"""Minimal multi-provider LLM client. Keys are read from the environment only."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class LLMError(RuntimeError):
    pass


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name, default)
    return value.strip() if isinstance(value, str) and value.strip() else default


def provider_name() -> str:
    return (_env("LLM_PROVIDER", "openai") or "openai").lower()


def model_name() -> str:
    return _env("LLM_MODEL") or {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-sonnet-4-5",
        "gemini": "gemini-2.0-flash",
    }.get(provider_name(), "gpt-4o-mini")


def complete_json(system: str, user: str, *, temperature: float = 0.3) -> Any:
    """Ask the model to return a JSON value. Raises LLMError on failure."""
    provider = provider_name()
    if provider in {"openai", "openrouter", "azure"}:
        return _openai_compatible(system, user, temperature)
    if provider == "anthropic":
        return _anthropic(system, user, temperature)
    if provider in {"gemini", "google"}:
        return _gemini(system, user, temperature)
    raise LLMError(f"Unknown LLM_PROVIDER={provider!r}. Use openai, anthropic, or gemini.")


def _parse_json_content(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        start, end = text.find("["), text.rfind("]")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise LLMError(f"Model did not return JSON: {exc}: {text[:400]}") from exc


def _http_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int = 120) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise LLMError(f"HTTP {exc.code} from {url}: {body[:800]}") from exc


def _openai_compatible(system: str, user: str, temperature: float) -> Any:
    api_key = _env("OPENAI_API_KEY") or _env("OPENROUTER_API_KEY")
    if not api_key:
        raise LLMError("Set OPENAI_API_KEY (or OPENROUTER_API_KEY) in the environment or .env")
    base = (_env("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if "openrouter.ai" in base:
        headers["HTTP-Referer"] = "https://github.com/cmu-seai"
        headers["X-Title"] = "I3 hazard analysis"
    payload = {
        "model": model_name(),
        "temperature": temperature,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system + "\nAlways respond with a single JSON object."},
            {"role": "user", "content": user},
        ],
    }
    body = _http_json(f"{base}/chat/completions", payload, headers)
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"Unexpected OpenAI response: {body!r}") from exc
    return _parse_json_content(content)


def _anthropic(system: str, user: str, temperature: float) -> Any:
    api_key = _env("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMError("Set ANTHROPIC_API_KEY in the environment or .env")
    payload = {
        "model": model_name(),
        "max_tokens": 8000,
        "temperature": temperature,
        "system": system + "\nAlways respond with a single JSON object.",
        "messages": [{"role": "user", "content": user}],
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    body = _http_json("https://api.anthropic.com/v1/messages", payload, headers)
    try:
        content = "".join(part.get("text", "") for part in body["content"] if part.get("type") == "text")
    except (KeyError, TypeError) as exc:
        raise LLMError(f"Unexpected Anthropic response: {body!r}") from exc
    return _parse_json_content(content)


def _gemini(system: str, user: str, temperature: float) -> Any:
    api_key = _env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY")
    if not api_key:
        raise LLMError("Set GEMINI_API_KEY in the environment or .env")
    model = model_name()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system + "\nAlways respond with a single JSON object."}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
        },
    }
    body = _http_json(url, payload, {"Content-Type": "application/json"})
    try:
        content = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"Unexpected Gemini response: {body!r}") from exc
    return _parse_json_content(content)
