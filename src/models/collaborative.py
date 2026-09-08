"""Collaborative filtering via biased Truncated SVD.

We build a user × movie matrix of (explicit + implicit) scores, subtract a
simple bias model (global + user + item means), then factorize the residual
matrix. Recommendations are the reconstructed scores, excluding movies the
user already interacted with.

This is substantively different from content-based filtering: it never looks
at genres or overviews, only at who interacted with what.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import TruncatedSVD

from src.config import CF_MIN_MOVIE_INTERACTIONS, CF_MIN_USER_INTERACTIONS, CF_N_COMPONENTS, RANDOM_SEED


@dataclass
class _Maps:
    user_to_idx: dict[int, int]
    movie_to_idx: dict[str, int]
    idx_to_movie: list[str]


class CollaborativeSVD:
    """Matrix-factorization recommender (Truncated SVD on biased residuals)."""

    def __init__(
        self,
        n_components: int = CF_N_COMPONENTS,
        min_user: int = CF_MIN_USER_INTERACTIONS,
        min_movie: int = CF_MIN_MOVIE_INTERACTIONS,
        random_state: int = RANDOM_SEED,
    ) -> None:
        self.n_components = n_components
        self.min_user = min_user
        self.min_movie = min_movie
        self.random_state = random_state
        self.maps: _Maps | None = None
        self.global_mean: float = 0.0
        self.user_bias: np.ndarray | None = None
        self.item_bias: np.ndarray | None = None
        self.user_factors: np.ndarray | None = None
        self.item_factors: np.ndarray | None = None  # (n_movies, n_components)
        self.seen: dict[int, set[str]] = {}
        self.popularity_order: list[str] = []

    def fit(self, interactions: pd.DataFrame) -> "CollaborativeSVD":
        user_counts = interactions.groupby("user_id").size()
        movie_counts = interactions.groupby("movie_id").size()
        keep_users = set(user_counts[user_counts >= self.min_user].index)
        keep_movies = set(movie_counts[movie_counts >= self.min_movie].index)
        filtered = interactions[
            interactions["user_id"].isin(keep_users)
            & interactions["movie_id"].isin(keep_movies)
        ]
        if filtered.empty:
            raise ValueError("Not enough interactions to fit collaborative SVD.")

        users = sorted(filtered["user_id"].unique().tolist())
        movies = sorted(filtered["movie_id"].astype(str).unique().tolist())
        user_to_idx = {u: i for i, u in enumerate(users)}
        movie_to_idx = {m: i for i, m in enumerate(movies)}
        self.maps = _Maps(user_to_idx, movie_to_idx, movies)

        n_users, n_movies = len(users), len(movies)
        rows = filtered["user_id"].map(user_to_idx).to_numpy()
        cols = filtered["movie_id"].astype(str).map(movie_to_idx).to_numpy()
        values = filtered["rating"].to_numpy(dtype=np.float32)

        matrix = sparse.csr_matrix(
            (values, (rows, cols)), shape=(n_users, n_movies), dtype=np.float32
        )
        self.global_mean = float(values.mean())

        # Means over observed entries only.
        user_sum = np.array(matrix.sum(axis=1)).ravel()
        user_n = np.diff(matrix.indptr)
        item_sum = np.array(matrix.sum(axis=0)).ravel()
        item_n = np.diff(matrix.tocsc().indptr)
        self.user_bias = user_sum / np.maximum(user_n, 1) - self.global_mean
        self.item_bias = item_sum / np.maximum(item_n, 1) - self.global_mean

        # Residual = rating - global - user_bias - item_bias
        residual_values = (
            values
            - self.global_mean
            - self.user_bias[rows]
            - self.item_bias[cols]
        )
        residual = sparse.csr_matrix(
            (residual_values.astype(np.float32), (rows, cols)),
            shape=(n_users, n_movies),
        )

        n_comp = min(self.n_components, n_users - 1, n_movies - 1)
        n_comp = max(n_comp, 1)
        svd = TruncatedSVD(n_components=n_comp, random_state=self.random_state)
        # user_factors: (n_users, k), item_factors: (n_movies, k)
        self.user_factors = svd.fit_transform(residual).astype(np.float32)
        self.item_factors = svd.components_.T.astype(np.float32)

        self.seen = {
            int(user_id): set(group["movie_id"].astype(str))
            for user_id, group in interactions.groupby("user_id")
        }
        pop = (
            interactions.groupby("movie_id")
            .size()
            .sort_values(ascending=False)
            .index.astype(str)
            .tolist()
        )
        self.popularity_order = pop
        self.n_components = n_comp
        return self

    def _scores_for_user(self, user_id: int) -> np.ndarray | None:
        if self.maps is None or self.user_factors is None or self.item_factors is None:
            raise RuntimeError("Model is not fitted.")
        idx = self.maps.user_to_idx.get(int(user_id))
        if idx is None:
            return None
        latent = self.user_factors[idx]
        scores = self.item_factors @ latent
        scores = scores + self.global_mean + self.user_bias[idx] + self.item_bias
        return scores

    def recommend(
        self,
        user_id: int,
        k: int = 20,
        seen: set[str] | None = None,
    ) -> list[str]:
        banned = set(seen or self.seen.get(int(user_id), set()))
        scores = self._scores_for_user(user_id)
        if scores is None:
            # Cold-ish user for CF: fall back to popularity (caller may swap in LLM).
            return [m for m in self.popularity_order if m not in banned][:k]

        n_take = min(len(scores), k + len(banned) + 50)
        if n_take >= len(scores):
            cand = np.argsort(-scores)
        else:
            cand = np.argpartition(-scores, n_take - 1)[:n_take]
            cand = cand[np.argsort(-scores[cand])]
        out: list[str] = []
        for idx in cand:
            movie_id = self.maps.idx_to_movie[int(idx)]
            if movie_id in banned:
                continue
            out.append(movie_id)
            if len(out) >= k:
                break
        if len(out) < k:
            for movie_id in self.popularity_order:
                if movie_id in banned or movie_id in out:
                    continue
                out.append(movie_id)
                if len(out) >= k:
                    break
        return out
