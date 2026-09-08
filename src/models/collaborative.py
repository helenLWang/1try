"""Collaborative filtering via item–item cosine similarity.

We build a user × movie matrix of (explicit + implicit) scores and rank unseen
movies by how similar they are (co-watched / co-rated) to movies the user
already consumed. This uses only the interaction matrix — no genres or plots —
so it is substantively different from content-based TF-IDF.

Item–item cosine is a better fit for this stream than a large SVD: most users
in a collected window have only one or two movies, so a 50-factor SVD mostly
reconstructs noise. Similarity of item columns still lets a user who watched
Star Wars get other movies that Star Wars viewers also watched.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.preprocessing import normalize

from src.config import CF_MIN_MOVIE_INTERACTIONS, CF_MIN_USER_INTERACTIONS, RANDOM_SEED


@dataclass
class _Maps:
    user_to_idx: dict[int, int]
    movie_to_idx: dict[str, int]
    idx_to_movie: list[str]


class CollaborativeSVD:
    """Item–item collaborative filter (class name kept for train.py imports)."""

    def __init__(
        self,
        n_components: int = 50,  # unused; kept so train logs stay stable
        min_user: int = CF_MIN_USER_INTERACTIONS,
        min_movie: int = CF_MIN_MOVIE_INTERACTIONS,
        random_state: int = RANDOM_SEED,
    ) -> None:
        self.n_components = n_components
        self.min_user = min_user
        self.min_movie = min_movie
        self.random_state = random_state
        self.maps: _Maps | None = None
        self.item_vectors = None  # (n_movies, n_users) L2-normalized columns as rows
        self.user_rows: dict[int, np.ndarray] = {}
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
            raise ValueError("Not enough interactions to fit collaborative filtering.")

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
        # Item vectors: L2-normalized movie columns, stored as rows for matmul.
        self.item_vectors = normalize(matrix.T.tocsr())

        for user_id, group in filtered.groupby("user_id"):
            vec = np.zeros(n_movies, dtype=np.float32)
            for movie_id, rating in zip(
                group["movie_id"].astype(str), group["rating"]
            ):
                vec[movie_to_idx[movie_id]] = float(rating)
            self.user_rows[int(user_id)] = vec

        self.seen = {
            int(user_id): set(group["movie_id"].astype(str))
            for user_id, group in interactions.groupby("user_id")
        }
        self.popularity_order = (
            interactions.groupby("movie_id")
            .size()
            .sort_values(ascending=False)
            .index.astype(str)
            .tolist()
        )
        self.n_components = min(self.n_components, n_movies, n_users)
        return self

    def _scores_for_user(self, user_id: int) -> np.ndarray | None:
        if self.maps is None or self.item_vectors is None:
            raise RuntimeError("Model is not fitted.")
        history = self.user_rows.get(int(user_id))
        if history is None:
            return None
        # scores_i = sum_j sim(i, j) * r_uj  with sim = cosine of item columns
        # item_vectors is (n_movies, n_users); G = item_vectors @ item_vectors.T
        # too big to store: compute (item_vectors @ (item_vectors.T @ history))
        projected = self.item_vectors.T.dot(history)  # (n_users,)
        scores = np.asarray(self.item_vectors.dot(projected)).ravel()
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
