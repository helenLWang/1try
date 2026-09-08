"""Content-based filtering with TF-IDF movie documents.

Each movie is a bag of words from title, genres, tagline, and overview.
A user's profile is the score-weighted average of the movies they already
interacted with. Recommendations are nearest movies in that TF-IDF space.

This never uses other users' behavior, so it is substantively different from
collaborative filtering and can recommend long-tail titles that CF ignores.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from src.config import TFIDF_MAX_FEATURES, TFIDF_MIN_DF, TFIDF_NGRAM


def movie_document(row: pd.Series) -> str:
    genres = row.get("genres") or []
    if isinstance(genres, list):
        genre_text = " ".join(str(g) for g in genres)
    else:
        genre_text = str(genres)
    parts = [
        str(row.get("title") or ""),
        str(row.get("original_title") or ""),
        genre_text,
        genre_text,  # duplicate genres so they outweigh plot words a bit
        str(row.get("tagline") or ""),
        str(row.get("overview") or ""),
        str(row.get("original_language") or ""),
    ]
    return " ".join(parts)


class ContentTfidfRecommender:
    def __init__(
        self,
        max_features: int = TFIDF_MAX_FEATURES,
        ngram_range: tuple[int, int] = TFIDF_NGRAM,
        min_df: int = TFIDF_MIN_DF,
    ) -> None:
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=min_df,
            stop_words="english",
        )
        self.movie_ids: list[str] = []
        self.movie_matrix = None
        self.user_profiles: dict[int, np.ndarray] = {}
        self.seen: dict[int, set[str]] = {}
        self.popularity_order: list[str] = []
        self._id_to_row: dict[str, int] = {}

    def fit(
        self,
        interactions: pd.DataFrame,
        movies: pd.DataFrame,
    ) -> "ContentTfidfRecommender":
        movies = movies.copy()
        movies["id"] = movies["id"].astype(str)
        movies["document"] = movies.apply(movie_document, axis=1)
        # Keep movies that appear in interactions OR have text (so we can still
        # recommend catalog titles the stream has not mentioned yet).
        movies = movies[movies["document"].str.len() > 0].drop_duplicates("id")
        if movies.empty:
            raise ValueError("No movie documents to fit TF-IDF.")

        self.movie_ids = movies["id"].tolist()
        self._id_to_row = {mid: i for i, mid in enumerate(self.movie_ids)}
        self.movie_matrix = normalize(
            self.vectorizer.fit_transform(movies["document"])
        )

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

        # Weighted average of item vectors (sparse × weights → dense profile).
        for user_id, group in interactions.groupby("user_id"):
            idxs = []
            weights = []
            for movie_id, rating in zip(
                group["movie_id"].astype(str), group["rating"]
            ):
                row = self._id_to_row.get(movie_id)
                if row is None:
                    continue
                idxs.append(row)
                weights.append(float(rating))
            if not idxs:
                continue
            weight_arr = np.asarray(weights, dtype=np.float32)
            weight_arr = weight_arr / weight_arr.sum()
            profile = self.movie_matrix[idxs].T.dot(weight_arr)
            # movie_matrix is (n_movies, n_terms); [idxs] -> (n, n_terms)
            # .T.dot(weights) -> (n_terms,)
            self.user_profiles[int(user_id)] = np.asarray(profile).ravel()
        return self

    def recommend(
        self,
        user_id: int,
        k: int = 20,
        seen: set[str] | None = None,
    ) -> list[str]:
        banned = set(seen or self.seen.get(int(user_id), set()))
        profile = self.user_profiles.get(int(user_id))
        if profile is None or self.movie_matrix is None:
            return [m for m in self.popularity_order if m not in banned][:k]

        # Cosine similarity: catalog rows are L2-normalized; normalize profile.
        norm = np.linalg.norm(profile)
        if norm == 0:
            return [m for m in self.popularity_order if m not in banned][:k]
        profile = profile / norm
        sims = self.movie_matrix.dot(profile)
        sims = np.asarray(sims).ravel()

        extra = min(len(sims), max(k + len(banned) + 50, 1))
        if extra >= len(sims):
            cand = np.argsort(-sims)
        else:
            cand = np.argpartition(-sims, extra - 1)[:extra]
            cand = cand[np.argsort(-sims[cand])]
        out: list[str] = []
        for idx in cand:
            movie_id = self.movie_ids[int(idx)]
            if movie_id in banned:
                continue
            out.append(movie_id)
            if len(out) >= k:
                break
        return out
