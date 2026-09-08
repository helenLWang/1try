"""Popularity baseline: rank movies by interaction count / mean rating."""

from __future__ import annotations

import pandas as pd


class PopularityRecommender:
    """Non-personalized ranking used as an evaluation baseline."""

    def __init__(self) -> None:
        self.ranked_ids: list[str] = []
        self.scores: dict[str, float] = {}

    def fit(self, interactions: pd.DataFrame) -> "PopularityRecommender":
        stats = (
            interactions.groupby("movie_id")
            .agg(n=("rating", "size"), mean=("rating", "mean"))
            .reset_index()
        )
        # Slightly prefer well-rated popular titles over one-off 10-star movies.
        stats["score"] = stats["n"] * stats["mean"]
        stats = stats.sort_values("score", ascending=False)
        self.ranked_ids = stats["movie_id"].astype(str).tolist()
        self.scores = dict(zip(stats["movie_id"].astype(str), stats["score"]))
        return self

    def recommend(
        self,
        user_id: int,
        k: int = 20,
        seen: set[str] | None = None,
    ) -> list[str]:
        del user_id  # unused: popularity is global
        banned = seen or set()
        out: list[str] = []
        for movie_id in self.ranked_ids:
            if movie_id in banned:
                continue
            out.append(movie_id)
            if len(out) >= k:
                break
        return out
