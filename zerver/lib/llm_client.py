"""Shared LLM client used by the unread recap and topic-title features.

Uses LiteLLM (already a Zulip dependency) so graders can switch providers
without code changes. Credentials are resolved in this order:

1. ``LLM_API_KEY`` / ``OPENAI_API_KEY`` / ``OPENROUTER_API_KEY``
2. An ``api.key`` file in the repository root (gitignored)
3. Zulip's ``topic_summarization_api_key`` secret
"""

from __future__ import annotations

import os
import re
from typing import Any

import orjson
from django.conf import settings

from zproject.config import DEPLOY_ROOT

# Avoid LiteLLM fetching a remote cost map during tests/import.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
import litellm

GENERIC_MODEL_FALLBACK = "gpt-4o-mini"


def get_llm_api_key() -> str | None:
    for env_name in ("LLM_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY"):
        value = os.environ.get(env_name)
        if value:
            return value.strip()

    api_key_path = os.path.join(DEPLOY_ROOT, "api.key")
    if os.path.isfile(api_key_path):
        with open(api_key_path) as key_file:
            value = key_file.read().strip()
        if value:
            return value

    return settings.TOPIC_SUMMARIZATION_API_KEY


def get_llm_model() -> str | None:
    env_model = os.environ.get("LLM_MODEL")
    if env_model:
        return env_model
    if settings.TOPIC_SUMMARIZATION_MODEL:
        return settings.TOPIC_SUMMARIZATION_MODEL
    if get_llm_api_key():
        return GENERIC_MODEL_FALLBACK
    return None


def get_llm_api_base() -> str | None:
    return os.environ.get("LLM_API_BASE") or getattr(
        settings, "TOPIC_SUMMARIZATION_API_BASE", None
    )


def llm_is_configured() -> bool:
    return get_llm_model() is not None and get_llm_api_key() is not None


def chat_completion(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 600,
    temperature: float = 0.2,
) -> str:
    model = get_llm_model()
    api_key = get_llm_api_key()
    if model is None or api_key is None:
        raise RuntimeError("LLM is not configured")

    extra_params: dict[str, Any] = dict(settings.TOPIC_SUMMARIZATION_PARAMETERS)
    extra_params.setdefault("max_tokens", max_tokens)
    extra_params.setdefault("temperature", temperature)
    api_base = get_llm_api_base()
    if api_base:
        extra_params.setdefault("api_base", api_base)

    response = litellm.completion(
        model=model,
        messages=messages,
        api_key=api_key,
        **extra_params,
    )
    content = response["choices"][0]["message"]["content"]
    if not content:
        raise RuntimeError("LLM returned an empty response")
    return str(content)


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object out of a model response, including fenced blocks."""
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, flags=re.DOTALL)
    if fenced:
        stripped = fenced.group(1)
    else:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            stripped = stripped[start : end + 1]
    parsed: object = orjson.loads(stripped)
    if not isinstance(parsed, dict):
        raise ValueError("LLM JSON was not an object")
    return parsed
