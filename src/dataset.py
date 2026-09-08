"""Turn raw ratings + watches into a single user-movie interaction table."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    IMPLICIT_BASE,
    IMPLICIT_SCALE,
    INTERACTIONS_PATH,
    MAX_RATING,
    MIN_RATING,
    MIN_WATCH_MINUTES,
    MOVIES_PATH,
    RATINGS_PATH,
    USERS_PATH,
    WATCHES_PATH,
)


def load_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return pd.DataFrame(rows)


def _implicit_score(max_minute: float, runtime: float | None) -> float:
    length = runtime if runtime and runtime > 0 else 90.0
    progress = min(float(max_minute) / length, 1.0)
    score = IMPLICIT_BASE + IMPLICIT_SCALE * progress
    return float(np.clip(score, MIN_RATING, MAX_RATING))


def build_interactions(persist: bool = True) -> pd.DataFrame:
    """Merge explicit ratings with implicit watch-progress scores.

    Explicit ratings win when both exist for the same (user, movie). Watch-only
    pairs shorter than MIN_WATCH_MINUTES are dropped as accidental clicks.
    """
    ratings = pd.read_csv(RATINGS_PATH)
    watches = pd.read_csv(WATCHES_PATH)
    movies = load_jsonl(MOVIES_PATH)

    ratings["user_id"] = ratings["user_id"].astype(int)
    ratings["movie_id"] = ratings["movie_id"].astype(str)
    ratings["rating"] = pd.to_numeric(ratings["rating"], errors="coerce")
    ratings = ratings.dropna(subset=["rating"])
    ratings = ratings[
        (ratings["rating"] >= MIN_RATING) & (ratings["rating"] <= MAX_RATING)
    ]
    # Keep the last rating if a user rated the same movie twice.
    ratings = ratings.sort_values("timestamp")
    ratings = ratings.drop_duplicates(["user_id", "movie_id"], keep="last")
    ratings["source"] = "explicit"
    ratings["timestamp"] = ratings["timestamp"].astype(str)

    watches["user_id"] = watches["user_id"].astype(int)
    watches["movie_id"] = watches["movie_id"].astype(str)
    watches = watches[watches["max_minute"] >= MIN_WATCH_MINUTES]

    runtime_map: dict[str, float] = {}
    if not movies.empty and "runtime" in movies.columns:
        runtime_map = {
            str(row["id"]): row["runtime"]
            for _, row in movies.iterrows()
            if pd.notna(row.get("id"))
        }

    rated_pairs = set(zip(ratings["user_id"], ratings["movie_id"]))
    implicit_rows = []
    for row in watches.itertuples(index=False):
        pair = (int(row.user_id), str(row.movie_id))
        if pair in rated_pairs:
            continue
        score = _implicit_score(row.max_minute, runtime_map.get(str(row.movie_id)))
        implicit_rows.append(
            {
                "user_id": pair[0],
                "movie_id": pair[1],
                "rating": score,
                "timestamp": str(row.last_ts),
                "source": "implicit",
            }
        )

    implicit = pd.DataFrame(implicit_rows)
    frames = [ratings[["user_id", "movie_id", "rating", "timestamp", "source"]]]
    if not implicit.empty:
        frames.append(implicit)
    interactions = pd.concat(frames, ignore_index=True)
    interactions = interactions.sort_values(["user_id", "timestamp"])
    if persist:
        interactions.to_csv(INTERACTIONS_PATH, index=False)
    return interactions


def load_interactions() -> pd.DataFrame:
    if INTERACTIONS_PATH.exists():
        df = pd.read_csv(INTERACTIONS_PATH)
    else:
        df = build_interactions(persist=True)
    df["user_id"] = df["user_id"].astype(int)
    df["movie_id"] = df["movie_id"].astype(str)
    df["rating"] = df["rating"].astype(float)
    df["timestamp"] = df["timestamp"].astype(str)
    return df


def load_movies() -> pd.DataFrame:
    movies = load_jsonl(MOVIES_PATH)
    if movies.empty:
        return movies
    movies["id"] = movies["id"].astype(str)
    if "genres" in movies.columns:
        def _genres(value: object) -> list[str]:
            if isinstance(value, list):
                return [str(x) for x in value]
            if isinstance(value, str) and value.startswith("["):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return [str(x) for x in parsed]
                except json.JSONDecodeError:
                    return []
            return []

        movies["genres"] = movies["genres"].apply(_genres)
    else:
        movies["genres"] = [[] for _ in range(len(movies))]
    movies["overview"] = movies.get("overview", pd.Series([""] * len(movies))).fillna("")
    movies["title"] = movies.get("title", pd.Series([""] * len(movies))).fillna("")
    movies["tagline"] = movies.get("tagline", pd.Series([""] * len(movies))).fillna("")
    return movies


def load_users() -> pd.DataFrame:
    users = load_jsonl(USERS_PATH)
    if users.empty:
        return users
    users["user_id"] = users["user_id"].astype(int)
    return users


def time_split(
    interactions: pd.DataFrame,
    hold_fraction: float,
    min_interactions: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-user chronological split: last `hold_fraction` of each user's rows."""
    train_parts = []
    test_parts = []
    for _user_id, group in interactions.groupby("user_id", sort=False):
        group = group.sort_values("timestamp")
        n = len(group)
        if n < min_interactions:
            train_parts.append(group)
            continue
        n_test = max(1, int(round(n * hold_fraction)))
        n_test = min(n_test, n - 1)  # keep at least one train row
        train_parts.append(group.iloc[:-n_test])
        test_parts.append(group.iloc[-n_test:])
    train = pd.concat(train_parts, ignore_index=True)
    test = (
        pd.concat(test_parts, ignore_index=True)
        if test_parts
        else interactions.iloc[0:0].copy()
    )
    return train, test
