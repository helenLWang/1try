"""Unread-message recap with permalinks back to the original messages."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import orjson

from zerver.lib.llm_client import chat_completion, llm_is_configured, parse_json_object
from zerver.lib.url_encoding import pm_message_url, stream_message_url
from zerver.models import Message, Stream, UserMessage, UserProfile
from zerver.models.recipients import Recipient

MAX_UNREAD_MESSAGES = 80


def _unread_user_messages(user_profile: UserProfile) -> list[UserMessage]:
    queryset = (
        UserMessage.objects.filter(user_profile=user_profile)
        .extra(where=[UserMessage.where_unread()])  # noqa: S610
        .select_related("message", "message__sender", "message__recipient")
        .order_by("-message_id")[:MAX_UNREAD_MESSAGES]
    )
    return list(reversed(list(queryset)))


def _stream_map(messages: list[Message]) -> dict[int, Stream]:
    stream_ids = {
        message.recipient.type_id
        for message in messages
        if message.recipient.type == Recipient.STREAM
    }
    if not stream_ids:
        return {}
    return {stream.id: stream for stream in Stream.objects.filter(id__in=stream_ids)}


def message_permalink(user_profile: UserProfile, message: Message, stream: Stream | None) -> str:
    """Build a hash URL that jumps to a message.

    Channel messages use ``#narrow/channel/<id>-<name>/topic/<topic>/near/<id>``.
    """
    if message.recipient.type == Recipient.STREAM and stream is not None:
        return stream_message_url(
            realm=user_profile.realm,
            message={
                "id": message.id,
                "stream_id": stream.id,
                "display_recipient": stream.name,
                "subject": message.topic_name(),
            },
            include_base_url=False,
        )
    display_recipient: list[dict[str, Any]]
    if message.recipient.type == Recipient.PERSONAL:
        display_recipient = [
            {"id": message.sender_id, "full_name": message.sender.full_name},
            {"id": user_profile.id, "full_name": user_profile.full_name},
        ]
    else:
        display_recipient = [{"id": user_profile.id, "full_name": user_profile.full_name}]
    return pm_message_url(
        user_profile.realm,
        {"id": message.id, "display_recipient": display_recipient},
    ).split(user_profile.realm.url, 1)[-1]


def _conversation_label(message: Message, stream: Stream | None) -> str:
    if message.recipient.type == Recipient.STREAM and stream is not None:
        return f"#{stream.name} > {message.topic_name()}"
    return "Direct message"


def _format_unread_for_prompt(
    messages: list[Message], streams: dict[int, Stream]
) -> tuple[str, dict[int, Message]]:
    by_id: dict[int, Message] = {}
    lines: list[str] = []
    for message in messages:
        stream = (
            streams.get(message.recipient.type_id)
            if message.recipient.type == Recipient.STREAM
            else None
        )
        by_id[message.id] = message
        content = " ".join(message.content.split())
        if len(content) > 400:
            content = content[:400] + "…"
        lines.append(
            f"[id={message.id}] ({_conversation_label(message, stream)}) "
            f"{message.sender.full_name}: {content}"
        )
    return "\n".join(lines), by_id


def _stream_for(message: Message, streams: dict[int, Stream]) -> Stream | None:
    if message.recipient.type != Recipient.STREAM:
        return None
    return streams.get(message.recipient.type_id)


def _fallback_recap(
    user_profile: UserProfile,
    messages: list[Message],
    streams: dict[int, Stream],
    overview: str,
) -> dict[str, Any]:
    grouped: dict[str, list[Message]] = defaultdict(list)
    for message in messages:
        grouped[_conversation_label(message, _stream_for(message, streams))].append(message)

    sections = []
    for label, group in grouped.items():
        cited = group[:3]
        sections.append(
            {
                "title": label,
                "summary": f"{len(group)} unread message(s).",
                "references": [
                    {
                        "message_id": message.id,
                        "sender": message.sender.full_name,
                        "permalink": message_permalink(
                            user_profile, message, _stream_for(message, streams)
                        ),
                    }
                    for message in cited
                ],
            }
        )
    return {
        "overview": overview,
        "unread_count": len(messages),
        "truncated": False,
        "sections": sections,
    }


def generate_unread_recap(user_profile: UserProfile) -> dict[str, Any]:
    user_messages = _unread_user_messages(user_profile)
    messages = [um.message for um in user_messages]
    if not messages:
        return {
            "overview": "You have no unread messages.",
            "unread_count": 0,
            "truncated": False,
            "sections": [],
        }

    streams = _stream_map(messages)
    formatted, by_id = _format_unread_for_prompt(messages, streams)
    truncated = len(user_messages) == MAX_UNREAD_MESSAGES

    if not llm_is_configured():
        labels = {
            _conversation_label(message, _stream_for(message, streams)) for message in messages
        }
        overview = (
            f"You have {len(messages)} unread message(s) across {len(labels)} "
            "conversation(s). Jump links go to the original messages."
        )
        recap = _fallback_recap(user_profile, messages, streams, overview)
        recap["truncated"] = truncated
        return recap

    prompt_messages = [
        {
            "role": "system",
            "content": (
                "You write recaps of unread Zulip messages for a teammate who was away. "
                "Respond with a JSON object only, no markdown fences. Schema:\n"
                "{\n"
                '  "overview": "2-4 sentence recap of the most important unread activity",\n'
                '  "sections": [\n'
                "    {\n"
                '      "title": "channel > topic or Direct message",\n'
                '      "summary": "one or two sentences",\n'
                '      "message_ids": [123, 456]\n'
                "    }\n"
                "  ]\n"
                "}\n"
                "message_ids MUST be copied from the [id=...] tags in the input. "
                "Cite the most useful 1-3 messages per section so the reader can jump to them."
            ),
        },
        {"role": "user", "content": formatted},
    ]

    raw = chat_completion(prompt_messages, max_tokens=700, temperature=0.2)
    try:
        parsed = parse_json_object(raw)
    except (ValueError, orjson.JSONDecodeError):
        return _fallback_recap(
            user_profile,
            messages,
            streams,
            overview=raw.strip()[:1500] or "Unread activity is listed below.",
        )

    sections = []
    raw_sections = parsed.get("sections")
    if isinstance(raw_sections, list):
        for raw_section in raw_sections:
            if not isinstance(raw_section, dict):
                continue
            cited_ids: list[int] = []
            for value in raw_section.get("message_ids") or []:
                try:
                    cited_ids.append(int(value))
                except (TypeError, ValueError):
                    continue
            references = []
            for message_id in cited_ids:
                message = by_id.get(message_id)
                if message is None:
                    continue
                references.append(
                    {
                        "message_id": message.id,
                        "sender": message.sender.full_name,
                        "permalink": message_permalink(
                            user_profile, message, _stream_for(message, streams)
                        ),
                    }
                )
            sections.append(
                {
                    "title": str(raw_section.get("title") or "Unread"),
                    "summary": str(raw_section.get("summary") or ""),
                    "references": references,
                }
            )

    overview = str(parsed.get("overview") or "").strip()
    if not overview:
        overview = "Here is a recap of your unread messages."
    if not sections:
        return _fallback_recap(user_profile, messages, streams, overview)

    return {
        "overview": overview,
        "unread_count": len(messages),
        "truncated": truncated,
        "sections": sections,
    }
