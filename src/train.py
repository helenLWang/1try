"""Train collaborative + content models and write artifacts + a train log."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np

from src.config import (
    ARTIFACT_DIR,
    CF_MIN_MOVIE_INTERACTIONS,
    CF_MIN_USER_INTERACTIONS,
    CF_N_COMPONENTS,
    IMPLICIT_BASE,
    IMPLICIT_SCALE,
    MIN_INTERACTIONS_FOR_SPLIT,
    MIN_WATCH_MINUTES,
    MODEL_DIR,
    RANDOM_SEED,
    TEST_HOLD_FRACTION,
    TFIDF_MAX_FEATURES,
    TOP_K,
    TRAIN_LOG_PATH,
)
from src.dataset import build_interactions, load_movies, load_users, time_split
from src.models.collaborative import CollaborativeItemCF
from src.models.content import ContentTfidfRecommender
from src.models.popularity import PopularityRecommender
from src.models.cold_start import ColdStartRecommender


def set_seed(seed: int = RANDOM_SEED) -> None:
    np.random.seed(seed)


def train(full_data: bool = False) -> dict:
    """Fit models on the train split (or all data) and persist them.

    Evaluation must not leak test rows, so the default is to fit on the
    chronological train split. Pass --full-data when you want a production
    artifact trained on everything.
    """
    set_seed()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    interactions = build_interactions(persist=True)
    movies = load_movies()
    users = load_users()
    if full_data:
        train_df = interactions
        test_df = interactions.iloc[0:0].copy()
    else:
        train_df, test_df = time_split(
            interactions, TEST_HOLD_FRACTION, MIN_INTERACTIONS_FOR_SPLIT
        )

    cf = CollaborativeItemCF().fit(train_df)
    content = ContentTfidfRecommender().fit(train_df, movies)
    popularity = PopularityRecommender().fit(train_df)
    cold = ColdStartRecommender(prefer_llm=True).fit(train_df, movies, users)

    payload = {
        "collaborative": cf,
        "content": content,
        "popularity": popularity,
        "cold_start": cold,
        "train_user_ids": sorted(train_df["user_id"].unique().tolist()),
        "hyperparams": _hyperparams(),
        "fitted_at": datetime.now(timezone.utc).isoformat(),
        "n_train": int(len(train_df)),
        "n_test": int(len(test_df)),
        "n_users": int(train_df["user_id"].nunique()),
        "n_movies": int(train_df["movie_id"].nunique()),
    }
    model_path = MODEL_DIR / "recommenders.joblib"
    joblib.dump(payload, model_path)

    log = {
        **payload["hyperparams"],
        "fitted_at": payload["fitted_at"],
        "model_path": str(model_path),
        "n_train_rows": payload["n_train"],
        "n_test_rows": payload["n_test"],
        "n_train_users": payload["n_users"],
        "n_train_movies": payload["n_movies"],
        "n_cf_users": len(cf.maps.user_to_idx) if cf.maps else 0,
        "n_cf_movies": len(cf.maps.movie_to_idx) if cf.maps else 0,
        "n_content_movies": len(content.movie_ids),
        "n_users_with_self_desc": int(
            users["self_description_likes"].notna().sum()
        )
        if not users.empty and "self_description_likes" in users.columns
        else 0,
        "elapsed_s": round(time.time() - t0, 2),
        "full_data": full_data,
    }
    TRAIN_LOG_PATH.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(json.dumps(log, indent=2))
    print(f"Saved models to {model_path}")
    return log


def _hyperparams() -> dict:
    return {
        "random_seed": RANDOM_SEED,
        "cf_n_components": CF_N_COMPONENTS,
        "cf_min_user_interactions": CF_MIN_USER_INTERACTIONS,
        "cf_min_movie_interactions": CF_MIN_MOVIE_INTERACTIONS,
        "tfidf_max_features": TFIDF_MAX_FEATURES,
        "min_watch_minutes": MIN_WATCH_MINUTES,
        "implicit_base": IMPLICIT_BASE,
        "implicit_scale": IMPLICIT_SCALE,
        "test_hold_fraction": TEST_HOLD_FRACTION,
        "min_interactions_for_split": MIN_INTERACTIONS_FOR_SPLIT,
        "top_k": TOP_K,
    }


def load_models(path: Path | None = None) -> dict:
    model_path = path or (MODEL_DIR / "recommenders.joblib")
    if not model_path.exists():
        raise FileNotFoundError(
            f"No trained models at {model_path}. Run: python -m src.train"
        )
    return joblib.load(model_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Train I2 recommenders")
    parser.add_argument(
        "--full-data",
        action="store_true",
        help="Fit on all interactions instead of the train split",
    )
    args = parser.parse_args()
    train(full_data=args.full_data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
