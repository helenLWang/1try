"""Detect topic drift and suggest a better Zulip topic title."""

from __future__ import annotations

import re
import threading
import time
from typing import Any

import orjson

from zerver.lib.llm_client import chat_completion, llm_is_configured, parse_json_object
from zerver.lib.streams import access_stream_by_id
from zerver.lib.topic import messages_for_topic
from zerver.models import Message, Stream, UserProfile
from zerver.models.constants import MAX_TOPIC_NAME_LENGTH

MIN_MESSAGES_FOR_DRIFT = 3
MAX_TOPIC_MESSAGES = 20
CACHE_TTL_SECONDS = 45
GENERIC_TITLES = {
    "hi",
    "hello",
    "hey",
    "question",
    "questions",
    "help",
    "test",
    "testing",
    "misc",
    "stuff",
    "topic",
    "chat",
    "discussion",
    "fyi",
    "update",
    "updates",
}

_cache_lock = threading.Lock()
_suggestion_cache: dict[tuple[int, int, str], tuple[float, dict[str, Any]]] = {}


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()


def title_token_overlap(title: str, texts: list[str]) -> float:
    title_words = {word for word in re.findall(r"[a-z0-9]+", title.lower()) if len(word) > 2}
    if not title_words:
        return 0.0
    recent = " ".join(texts[-8:]).lower()
    hits = sum(1 for word in title_words if word in recent)
    return hits / len(title_words)


def should_call_llm(title: str, message_count: int, texts: list[str]) -> bool:
    if message_count < MIN_MESSAGES_FOR_DRIFT:
        return False
    lowered = title.strip().lower()
    if lowered in GENERIC_TITLES or len(lowered) <= 4:
        return True
    return title_token_overlap(title, texts) < 0.5


def _format_topic_messages(messages: list[Message]) -> str:
    lines = []
    for message in messages:
        content = " ".join(message.content.split())
        if len(content) > 280:
            content = content[:280] + "…"
        lines.append(f"{message.sender.full_name}: {content}")
    return "\n".join(lines)


def _cache_key(stream: Stream, topic_name: str, last_message_id: int) -> tuple[int, int, str]:
    return (stream.id, last_message_id, topic_name.casefold())


def _cache_get(key: tuple[int, int, str]) -> dict[str, Any] | None:
    now = time.monotonic()
    with _cache_lock:
        cached = _suggestion_cache.get(key)
        if cached is None:
            return None
        stored_at, payload = cached
        if now - stored_at > CACHE_TTL_SECONDS:
            _suggestion_cache.pop(key, None)
            return None
        return payload


def _cache_set(key: tuple[int, int, str], payload: dict[str, Any]) -> None:
    with _cache_lock:
        if len(_suggestion_cache) > 512:
            _suggestion_cache.clear()
        _suggestion_cache[key] = (time.monotonic(), payload)


def _heuristic_title(current_title: str, texts: list[str]) -> str:
    """Best-effort title from message bodies when no LLM key is configured."""
    best = ""
    for text in texts:
        cleaned = " ".join(text.split())
        if len(cleaned) > len(best):
            best = cleaned
    if not best:
        return current_title
    # Use the first clause, capped to Zulip's topic length.
    clause = re.split(r"[.!?]", best, maxsplit=1)[0].strip(" -–:")
    if len(clause) < 8:
        clause = best
    words = clause.split()
    if len(words) > 8:
        clause = " ".join(words[:8])
    return clause[:60].rstrip()


def suggest_topic_title(
    user_profile: UserProfile,
    *,
    stream_id: int,
    topic_name: str,
) -> dict[str, Any]:
    stream, _sub = access_stream_by_id(user_profile, stream_id)
    topic_name = _normalize_title(topic_name)
    if stream.recipient_id is None:
        return {
            "drifted": False,
            "suggested_title": topic_name,
            "reason": "Channel has no recipient.",
            "skipped_llm": True,
            "message_count": 0,
            "latest_message_id": None,
        }

    messages = list(
        messages_for_topic(user_profile.realm_id, stream.recipient_id, topic_name)
        .select_related("sender")
        .order_by("-id")[:MAX_TOPIC_MESSAGES]
    )
    messages.reverse()

    no_drift = {
        "drifted": False,
        "suggested_title": topic_name,
        "reason": "",
        "skipped_llm": True,
        "message_count": len(messages),
        "latest_message_id": messages[-1].id if messages else None,
    }

    if not messages:
        no_drift["reason"] = "No messages in this topic."
        return no_drift

    cache_key = _cache_key(stream, topic_name, messages[-1].id)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    texts = [message.content for message in messages]
    if not should_call_llm(topic_name, len(messages), texts):
        if len(messages) < MIN_MESSAGES_FOR_DRIFT:
            no_drift["reason"] = "Not enough messages yet to judge drift."
        else:
            no_drift["reason"] = "Recent messages still match the current title."
        _cache_set(cache_key, no_drift)
        return no_drift

    if not llm_is_configured():
        suggested = _heuristic_title(topic_name, texts)
        payload = {
            "drifted": bool(suggested) and suggested.casefold() != topic_name.casefold(),
            "suggested_title": suggested or topic_name,
            "reason": "Suggested from recent messages because no LLM API key is configured.",
            "skipped_llm": True,
            "message_count": len(messages),
            "latest_message_id": messages[-1].id,
        }
        _cache_set(cache_key, payload)
        return payload

    prompt_messages = [
        {
            "role": "system",
            "content": (
                "You detect whether a Zulip topic title has drifted from the actual "
                "discussion. Reply with JSON only:\n"
                "{\n"
                '  "drifted": true or false,\n'
                '  "suggested_title": "short title, max 60 characters",\n'
                '  "reason": "one sentence explaining the drift or why the title is still fine"\n'
                "}\n"
                "Set drifted=true for sustained off-title discussion or a new sub-thread. "
                "Keep suggested_title concise, specific, and without wrapping quotes."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Current topic title: {topic_name}\n"
                f"Channel: {stream.name}\n"
                f"Recent messages:\n{_format_topic_messages(messages)}"
            ),
        },
    ]

    raw = chat_completion(prompt_messages, max_tokens=180, temperature=0.1)
    try:
        parsed = parse_json_object(raw)
    except (ValueError, orjson.JSONDecodeError):
        payload = {
            "drifted": False,
            "suggested_title": topic_name,
            "reason": "Could not parse the language-model response.",
            "skipped_llm": False,
            "message_count": len(messages),
            "latest_message_id": messages[-1].id,
        }
        _cache_set(cache_key, payload)
        return payload

    suggested = _normalize_title(str(parsed.get("suggested_title") or topic_name))
    if not suggested or suggested.casefold() == topic_name.casefold():
        drifted = False
        suggested = topic_name
    else:
        drifted = bool(parsed.get("drifted"))
        suggested = suggested[:MAX_TOPIC_NAME_LENGTH]

    payload = {
        "drifted": drifted,
        "suggested_title": suggested,
        "reason": str(parsed.get("reason") or "").strip(),
        "skipped_llm": False,
        "message_count": len(messages),
        "latest_message_id": messages[-1].id,
    }
    _cache_set(cache_key, payload)
    return payload
