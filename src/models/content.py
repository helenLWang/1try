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
    """Build a metadata document. Titles are omitted on purpose.

    Rare title tokens (place names, character names) otherwise dominate TF-IDF
    and the model recommends sequels that share a proper noun instead of
    similar genres/plots.
    """
    genres = row.get("genres") or []
    if isinstance(genres, list):
        genre_text = " ".join(str(g) for g in genres)
    else:
        genre_text = str(genres)
    parts = [
        genre_text,
        genre_text,
        genre_text,
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
        self.user_items: dict[int, list[tuple[int, float]]] = {}
        self.seen: dict[int, set[str]] = {}
        self.popularity_order: list[str] = []
        self._id_to_row: dict[str, int] = {}
        self.pop_scores: np.ndarray | None = None

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
        counts = interactions.groupby("movie_id").size()
        pop = np.array(
            [np.log1p(float(counts.get(mid, 0))) for mid in self.movie_ids],
            dtype=np.float32,
        )
        pop_max = float(pop.max()) if len(pop) else 1.0
        self.pop_scores = pop / pop_max if pop_max else pop

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
            self.user_items[int(user_id)] = [
                (int(i), float(w)) for i, w in zip(idxs, weight_arr)
            ]
        return self

    def recommend(
        self,
        user_id: int,
        k: int = 20,
        seen: set[str] | None = None,
    ) -> list[str]:
        banned = set(seen or self.seen.get(int(user_id), set()))
        items = self.user_items.get(int(user_id))
        if not items or self.movie_matrix is None:
            return [m for m in self.popularity_order if m not in banned][:k]

        idxs, weights = zip(*items)
        profile = np.asarray(
            self.movie_matrix[list(idxs)].T.dot(np.asarray(weights, dtype=np.float32))
        ).ravel()

        # Cosine similarity: catalog rows are L2-normalized; normalize profile.
        norm = np.linalg.norm(profile)
        if norm == 0:
            return [m for m in self.popularity_order if m not in banned][:k]
        profile = profile / norm
        sims = np.asarray(self.movie_matrix.dot(profile)).ravel()
        if self.pop_scores is not None and len(self.pop_scores) == len(sims):
            # 85% metadata similarity, 15% popularity so ties are not obscure
            # catalog noise. Still a content model: other users' *pairs* are unused.
            sims = 0.85 * sims + 0.15 * self.pop_scores

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
