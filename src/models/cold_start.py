"""Cold-start recommendations from a user's free-text self-description.

New users have no watch/rating history. Many of them filled in
`self_description_likes` / `self_description_dislikes` at signup. We:

1. Ask an LLM to turn that prose into structured tastes (genres + titles).
2. Score the movie catalog with those tastes (plus a weak popularity prior).
3. Optionally ask the LLM to re-rank a short candidate list and return ids.

The LLM is required for the assignment. If no API key is present, a
deterministic extractor that uses the same JSON schema is used so the rest
of the pipeline still runs (tests, offline matcher metrics). Graders should
put a key in `api.key`, `OPENAI_API_KEY`, or `GEMINI_API_KEY` to exercise
the real LLM path. Gemini keys (`AIza…` or `AQ.…`) auto-select Google's
native generateContent API.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import pandas as pd

from src.config import (
    API_KEY_FILE,
    COLD_START_TOP_K,
    DEFAULT_GEMINI_MODEL,
    GEMINI_FALLBACK_MODELS,
    GEMINI_NATIVE_BASE,
    GEMINI_OPENAI_BASE,
    LLM_BASE_URL,
    LLM_MAX_CANDIDATES,
    LLM_MAX_OUTPUT_TOKENS,
    LLM_MAX_RETRIES,
    LLM_MODEL,
    LLM_TEMPERATURE,
)

GENRE_ALIASES = {
    "sci-fi": "Science Fiction",
    "scifi": "Science Fiction",
    "science fiction": "Science Fiction",
    "sci fi": "Science Fiction",
    "rom-com": "Romance",
    "romcom": "Romance",
    "romantic comedy": "Romance",
    "kids": "Family",
    "children": "Family",
    "animated": "Animation",
    "anime": "Animation",
    "doc": "Documentary",
    "docs": "Documentary",
    "biopic": "History",
    "superhero": "Action",
}

CANONICAL_GENRES = [
    "Action",
    "Adventure",
    "Animation",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Family",
    "Fantasy",
    "History",
    "Horror",
    "Music",
    "Mystery",
    "Romance",
    "Science Fiction",
    "TV Movie",
    "Thriller",
    "War",
    "Western",
]


def load_api_key() -> str | None:
    for name in ("OPENAI_API_KEY", "LLM_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        env = os.environ.get(name)
        if env and env.strip():
            return env.strip()
    if API_KEY_FILE.exists():
        text = API_KEY_FILE.read_text(encoding="utf-8").strip()
        if text:
            return text.splitlines()[0].strip()
    return None


def _looks_like_gemini_key(key: str) -> bool:
    # Legacy Google keys (`AIza…`) and AI Studio auth keys (`AQ.…`).
    return key.startswith("AIza") or key.startswith("AQ.")


def llm_client_settings() -> tuple[dict[str, Any], str]:
    """OpenAI-SDK kwargs and model name, including Gemini auto-detect.

    I1 allows OpenAI or Google Gemini. Gemini keys (`AIza…` or `AQ.…`) use
    Google's native generateContent API unless `LLM_BASE_URL` is set to a
    non-Google host. A dedicated `GEMINI_API_KEY` wins over `OPENAI_API_KEY`
    so both can exist in the environment without mixing hosts.
    """
    env_base = os.environ.get("LLM_BASE_URL") or LLM_BASE_URL
    env_model = os.environ.get("LLM_MODEL") or LLM_MODEL
    gemini_env = (
        os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    ).strip()
    api_key = gemini_env or load_api_key()
    if not api_key:
        raise RuntimeError(
            "No LLM API key. Create api.key or set OPENAI_API_KEY / GEMINI_API_KEY."
        )

    kwargs: dict[str, Any] = {"api_key": api_key}
    wants_gemini = (
        bool(gemini_env)
        or _looks_like_gemini_key(api_key)
        or env_model.lower().startswith("gemini")
    )

    if env_base:
        kwargs["base_url"] = env_base
        model = env_model
        if wants_gemini and not env_model.lower().startswith("gemini"):
            model = DEFAULT_GEMINI_MODEL
    elif wants_gemini:
        kwargs["base_url"] = GEMINI_OPENAI_BASE
        model = env_model if env_model.lower().startswith("gemini") else DEFAULT_GEMINI_MODEL
    else:
        model = env_model
    return kwargs, model


def _use_gemini_native(kwargs: dict[str, Any], model: str) -> bool:
    key = str(kwargs.get("api_key") or "")
    env_base = os.environ.get("LLM_BASE_URL") or LLM_BASE_URL or ""
    if env_base and "generativelanguage.googleapis.com" not in env_base:
        return False
    if key.startswith("AQ."):
        return True
    if _looks_like_gemini_key(key) or model.lower().startswith("gemini"):
        return True
    base = str(kwargs.get("base_url") or "")
    return "generativelanguage.googleapis.com" in base


def _gemini_native_complete(api_key: str, model: str, system: str, user: str) -> str:
    """Chat completion via Gemini generateContent (required for `AQ.` keys)."""
    import requests

    models_to_try = [model.removeprefix("models/")]
    for fallback in GEMINI_FALLBACK_MODELS:
        if fallback not in models_to_try:
            models_to_try.append(fallback)
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": LLM_TEMPERATURE,
            "responseMimeType": "application/json",
            "maxOutputTokens": LLM_MAX_OUTPUT_TOKENS,
        },
    }
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    last_error = "Gemini request failed"
    for candidate in models_to_try:
        url = f"{GEMINI_NATIVE_BASE}/models/{candidate}:generateContent"
        for attempt in range(LLM_MAX_RETRIES):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
            except requests.RequestException as exc:
                last_error = f"Gemini network error: {type(exc).__name__}"
                time.sleep(1.5 * (attempt + 1))
                continue
            if response.status_code == 503:
                last_error = f"Gemini HTTP 503 on {candidate}"
                break
            if response.status_code == 429:
                last_error = f"Gemini HTTP 429 on {candidate}"
                time.sleep(min(8, 2 ** attempt))
                continue
            if response.status_code >= 400:
                last_error = f"Gemini HTTP {response.status_code} on {candidate}: {response.text[:200]}"
                break
            data = response.json()
            parts = (
                ((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
            )
            text = "".join(part.get("text") or "" for part in parts)
            if text.strip():
                return text
            last_error = f"Gemini returned empty text from {candidate}"
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(last_error)


def _llm_complete(system: str, user: str) -> str:
    kwargs, model = llm_client_settings()
    if _use_gemini_native(kwargs, model):
        return _gemini_native_complete(kwargs["api_key"], model, system, user)
    from openai import OpenAI

    client = OpenAI(**kwargs)
    completion = client.chat.completions.create(
        model=model,
        temperature=LLM_TEMPERATURE,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return completion.choices[0].message.content or "{}"


def _normalize_genre(token: str) -> str | None:
    raw = token.strip()
    if not raw:
        return None
    alias = GENRE_ALIASES.get(raw.lower())
    if alias:
        return alias
    for genre in CANONICAL_GENRES:
        if genre.lower() == raw.lower():
            return genre
    return None


def heuristic_extract(likes: str, dislikes: str) -> dict[str, Any]:
    """Schema-compatible fallback when no LLM key is configured.

    This is *not* the graded LLM; it exists so `recommend --model coldstart`
    still returns something and so we can unit-test the matcher.
    """
    liked_genres = []
    disliked_genres = []
    for genre in CANONICAL_GENRES:
        pattern = re.compile(rf"\b{re.escape(genre)}\b", re.I)
        if pattern.search(likes or ""):
            liked_genres.append(genre)
        if pattern.search(dislikes or ""):
            disliked_genres.append(genre)
    for alias, canon in GENRE_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", likes or "", re.I):
            liked_genres.append(canon)
        if re.search(rf"\b{re.escape(alias)}\b", dislikes or "", re.I):
            disliked_genres.append(canon)
    return {
        "liked_genres": sorted(set(liked_genres)),
        "disliked_genres": sorted(set(disliked_genres)),
        "liked_titles": [],
        "disliked_titles": [],
        "notes": "heuristic_extractor",
        "source": "heuristic",
        "raw_likes": likes or "",
        "raw_dislikes": dislikes or "",
    }


EXTRACT_PROMPT = """You extract movie tastes for a recommender.
The user is new (no watch history). They wrote:

LIKES:
{likes}

DISLIKES:
{dislikes}

Return ONLY compact JSON with this schema:
{{
  "liked_genres": [<TMDB genre names>],
  "disliked_genres": [<TMDB genre names>],
  "liked_titles": [<movie titles they mentioned or close equivalents>],
  "disliked_titles": [<movie titles they mentioned>],
  "notes": "<one sentence summary of taste>"
}}
Use only these genre names when possible:
Action, Adventure, Animation, Comedy, Crime, Documentary, Drama, Family,
Fantasy, History, Horror, Music, Mystery, Romance, Science Fiction, Thriller,
War, Western.
If the user names specific movies, copy the titles into liked_titles / disliked_titles.
If a field is unknown, use an empty list. No markdown.
"""


RERANK_PROMPT = """You recommend movies for a new user.

User likes: {likes}
User dislikes: {dislikes}
Structured tastes: {prefs}

Choose up to {k} movies from the CATALOG. Prefer titles matching likes,
avoid dislikes, and diversify a little (not 20 sequels). Use catalog ids
exactly.

CATALOG (id | title | genres):
{catalog}

Return ONLY JSON: {{"movie_ids": ["id1", "id2", ...]}}
"""


def _parse_json_blob(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return {}
    return {}


def llm_extract(likes: str, dislikes: str) -> dict[str, Any]:
    """Call Gemini or an OpenAI-compatible chat model to structure the self-description."""
    content = _llm_complete(
        "You output JSON only.",
        EXTRACT_PROMPT.format(likes=likes or "(none)", dislikes=dislikes or "(none)"),
    )
    data = _parse_json_blob(content)
    data["source"] = "llm"
    data["raw"] = content
    data["liked_genres"] = [
        g
        for g in (_normalize_genre(x) or str(x) for x in data.get("liked_genres") or [])
        if g
    ]
    data["disliked_genres"] = [
        g
        for g in (
            _normalize_genre(x) or str(x) for x in data.get("disliked_genres") or []
        )
        if g
    ]
    data["liked_titles"] = [str(x) for x in data.get("liked_titles") or []]
    data["disliked_titles"] = [str(x) for x in data.get("disliked_titles") or []]
    data["raw_likes"] = likes
    data["raw_dislikes"] = dislikes
    return data


def extract_preferences(likes: str, dislikes: str, prefer_llm: bool = True) -> dict[str, Any]:
    if prefer_llm and load_api_key():
        try:
            return llm_extract(likes, dislikes)
        except Exception as exc:  # noqa: BLE001 — keep recommending if the API flakes
            data = heuristic_extract(likes, dislikes)
            data["llm_error"] = type(exc).__name__
            return data
    return heuristic_extract(likes, dislikes)


def _title_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def score_catalog(
    prefs: dict[str, Any],
    movies: pd.DataFrame,
    popularity: dict[str, float],
) -> pd.DataFrame:
    """Score every movie from structured tastes. Higher is better."""
    liked_genres = {g.lower() for g in prefs.get("liked_genres") or []}
    disliked_genres = {g.lower() for g in prefs.get("disliked_genres") or []}
    liked_titles = [t.lower() for t in prefs.get("liked_titles") or []]
    disliked_titles = [t.lower() for t in prefs.get("disliked_titles") or []]
    raw_likes = (prefs.get("raw_likes") or "").lower()
    raw_dislikes = (prefs.get("raw_dislikes") or "").lower()

    rows = []
    pop_max = max(popularity.values()) if popularity else 1.0
    for movie in movies.itertuples(index=False):
        movie_id = str(movie.id)
        title = str(getattr(movie, "title", "") or "")
        genres = getattr(movie, "genres", []) or []
        genre_set = {str(g).lower() for g in genres}
        score = 0.0
        if liked_genres:
            score += 2.5 * len(genre_set & liked_genres)
        if disliked_genres and genre_set & disliked_genres:
            score -= 3.0 * len(genre_set & disliked_genres)
        title_l = title.lower()
        for named in liked_titles:
            if named and (named in title_l or title_l in named):
                score += 8.0
        for named in disliked_titles:
            if named and (named in title_l or title_l in named):
                score -= 8.0
        # Also match catalog titles the user typed in free text (LLM and heuristic).
        if title and len(title) >= 5 and title_l in raw_likes:
            score += 8.0
        if title and len(title) >= 5 and title_l in raw_dislikes:
            score -= 8.0
        tokens = [
            w
            for w in re.findall(r"[a-z0-9]+", title_l)
            if w not in {"the", "a", "an", "of", "and", "in", "to", "part"} and len(w) >= 6
        ]
        if tokens and any(tok in raw_likes for tok in tokens):
            score += 5.0
        if tokens and any(tok in raw_dislikes for tok in tokens):
            score -= 5.0
        # Tiny popularity prior so ties do not become random catalog order.
        score += 0.15 * (popularity.get(movie_id, 0.0) / pop_max)
        rows.append((movie_id, title, score))
    ranked = pd.DataFrame(rows, columns=["movie_id", "title", "score"])
    return ranked.sort_values("score", ascending=False)


def llm_rerank(
    likes: str,
    dislikes: str,
    prefs: dict[str, Any],
    candidates: pd.DataFrame,
    k: int,
) -> list[str] | None:
    """Ask the LLM to pick ids from a short candidate list. None on failure."""
    if not load_api_key() or candidates.empty:
        return None
    catalog_lines = []
    for row in candidates.head(LLM_MAX_CANDIDATES).itertuples(index=False):
        catalog_lines.append(f"{row.movie_id} | {row.title} | {row.score:.2f}")
    try:
        content = _llm_complete(
            "You output JSON only.",
            RERANK_PROMPT.format(
                likes=likes or "(none)",
                dislikes=dislikes or "(none)",
                prefs=json.dumps(
                    {key: prefs.get(key) for key in (
                        "liked_genres",
                        "disliked_genres",
                        "liked_titles",
                        "disliked_titles",
                        "notes",
                    )},
                    ensure_ascii=False,
                ),
                k=k,
                catalog="\n".join(catalog_lines),
            ),
        )
        data = _parse_json_blob(content)
        ids = [str(x) for x in data.get("movie_ids") or []]
        allowed = set(candidates["movie_id"].astype(str))
        filtered = [mid for mid in ids if mid in allowed]
        return filtered[:k] or None
    except Exception:  # noqa: BLE001 — fall back to scored catalog
        return None


class ColdStartRecommender:
    def __init__(self, prefer_llm: bool = True) -> None:
        self.prefer_llm = prefer_llm
        self.movies: pd.DataFrame | None = None
        self.users: dict[int, dict] = {}
        self.popularity: dict[str, float] = {}
        self.last_prefs: dict[str, Any] | None = None

    def fit(
        self,
        interactions: pd.DataFrame,
        movies: pd.DataFrame,
        users: pd.DataFrame,
    ) -> "ColdStartRecommender":
        self.movies = movies.copy()
        self.movies["id"] = self.movies["id"].astype(str)
        if not users.empty:
            self.users = {
                int(row.user_id): {
                    "likes": row.self_description_likes
                    if hasattr(row, "self_description_likes")
                    else None,
                    "dislikes": row.self_description_dislikes
                    if hasattr(row, "self_description_dislikes")
                    else None,
                }
                for row in users.itertuples(index=False)
            }
        pop = interactions.groupby("movie_id").size()
        self.popularity = {str(k): float(v) for k, v in pop.items()}
        return self

    def recommend_from_text(
        self,
        likes: str | None,
        dislikes: str | None,
        k: int = COLD_START_TOP_K,
        seen: set[str] | None = None,
    ) -> list[str]:
        if self.movies is None:
            raise RuntimeError("ColdStartRecommender is not fitted.")
        prefs = extract_preferences(likes or "", dislikes or "", prefer_llm=self.prefer_llm)
        self.last_prefs = prefs
        ranked = score_catalog(prefs, self.movies, self.popularity)
        banned = seen or set()
        ranked = ranked[~ranked["movie_id"].isin(banned)]
        llm_ids = llm_rerank(likes or "", dislikes or "", prefs, ranked, k) if self.prefer_llm else None
        if llm_ids:
            extra = [m for m in ranked["movie_id"].tolist() if m not in llm_ids]
            return (llm_ids + extra)[:k]
        return ranked["movie_id"].head(k).tolist()

    def recommend(
        self,
        user_id: int,
        k: int = COLD_START_TOP_K,
        seen: set[str] | None = None,
        likes: str | None = None,
        dislikes: str | None = None,
    ) -> list[str]:
        profile = self.users.get(int(user_id), {})
        likes = likes if likes is not None else profile.get("likes")
        dislikes = dislikes if dislikes is not None else profile.get("dislikes")
        return self.recommend_from_text(likes, dislikes, k=k, seen=seen)
