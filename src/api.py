"""Thin client for the course movie/user metadata API.

The API is rate-limited and accepts at most 200 comma-separated ids per
request. We retry on 429 / 5xx with exponential backoff and skip ids that
return 404 so a few missing movies do not abort collection.
"""

from __future__ import annotations

import time
from typing import Iterable

import requests

from src.config import API_BATCH_SIZE, API_MAX_RETRIES, API_SLEEP_S, METADATA_API


def _chunks(items: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _get_json(url: str) -> object | None:
    delay = 0.5
    for attempt in range(API_MAX_RETRIES):
        try:
            response = requests.get(url, timeout=20)
        except requests.RequestException:
            time.sleep(delay)
            delay *= 2
            continue
        if response.status_code == 429:
            time.sleep(delay)
            delay *= 2
            continue
        if response.status_code == 404:
            return None
        if response.status_code >= 500:
            time.sleep(delay)
            delay *= 2
            continue
        if not response.ok:
            return None
        try:
            return response.json()
        except ValueError:
            return None
    return None


def fetch_movies(movie_ids: Iterable[str]) -> list[dict]:
    """Fetch movie metadata. Unknown ids are omitted from the result."""
    unique = list(dict.fromkeys(str(mid) for mid in movie_ids if mid))
    results: list[dict] = []
    for batch in _chunks(unique, API_BATCH_SIZE):
        url = f"{METADATA_API}/movie/{','.join(batch)}"
        payload = _get_json(url)
        time.sleep(API_SLEEP_S)
        if payload is None:
            # Fall back to one-by-one so a single bad id does not drop the batch.
            for movie_id in batch:
                one = _get_json(f"{METADATA_API}/movie/{movie_id}")
                time.sleep(API_SLEEP_S)
                if isinstance(one, dict) and one.get("id"):
                    results.append(one)
                elif isinstance(one, list):
                    results.extend(x for x in one if isinstance(x, dict))
            continue
        if isinstance(payload, list):
            results.extend(x for x in payload if isinstance(x, dict))
        elif isinstance(payload, dict):
            results.append(payload)
    return results


def fetch_users(user_ids: Iterable[int | str]) -> list[dict]:
    """Fetch user metadata, including free-text likes/dislikes."""
    unique = list(dict.fromkeys(str(int(uid)) for uid in user_ids))
    results: list[dict] = []
    for batch in _chunks(unique, API_BATCH_SIZE):
        url = f"{METADATA_API}/user/{','.join(batch)}"
        payload = _get_json(url)
        time.sleep(API_SLEEP_S)
        if payload is None:
            for user_id in batch:
                one = _get_json(f"{METADATA_API}/user/{user_id}")
                time.sleep(API_SLEEP_S)
                if isinstance(one, dict) and "user_id" in one:
                    results.append(one)
                elif isinstance(one, list):
                    results.extend(x for x in one if isinstance(x, dict))
            continue
        if isinstance(payload, list):
            results.extend(x for x in payload if isinstance(x, dict))
        elif isinstance(payload, dict):
            results.append(payload)
    return results
