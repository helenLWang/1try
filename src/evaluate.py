"""Offline ranking evaluation for CF, content, popularity, and cold-start."""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict

import numpy as np
import pandas as pd

from src.config import (
    ARTIFACT_DIR,
    METRICS_PATH,
    MIN_INTERACTIONS_FOR_SPLIT,
    RANDOM_SEED,
    TEST_HOLD_FRACTION,
    TOP_K,
)
from src.dataset import build_interactions, load_movies, load_users, time_split
from src.models.cold_start import ColdStartRecommender, load_api_key
from src.models.collaborative import CollaborativeItemCF
from src.models.content import ContentTfidfRecommender
from src.models.popularity import PopularityRecommender


def _dcg(rels: list[int]) -> float:
    return float(sum((rel / np.log2(idx + 2)) for idx, rel in enumerate(rels)))


def ndcg_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    rec = recommended[:k]
    gains = [1 if item in relevant else 0 for item in rec]
    dcg = _dcg(gains)
    ideal = _dcg([1] * min(len(relevant), k))
    if ideal == 0:
        return 0.0
    return dcg / ideal


def metrics_for_ranking(recommended: list[str], relevant: set[str], k: int) -> dict:
    rec = recommended[:k]
    if not rec:
        return {"hit": 0.0, "precision": 0.0, "recall": 0.0, "ndcg": 0.0}
    hits = [item for item in rec if item in relevant]
    hit = 1.0 if hits else 0.0
    precision = len(hits) / len(rec)
    recall = len(hits) / len(relevant) if relevant else 0.0
    return {
        "hit": hit,
        "precision": precision,
        "recall": recall,
        "ndcg": ndcg_at_k(rec, relevant, k),
    }


def _mean_metrics(rows: list[dict]) -> dict:
    if not rows:
        return {"n_users": 0, "hit_rate": 0.0, "precision": 0.0, "recall": 0.0, "ndcg": 0.0}
    return {
        "n_users": len(rows),
        "hit_rate": float(np.mean([r["hit"] for r in rows])),
        "precision": float(np.mean([r["precision"] for r in rows])),
        "recall": float(np.mean([r["recall"] for r in rows])),
        "ndcg": float(np.mean([r["ndcg"] for r in rows])),
    }


def evaluate_recommenders(
    models: dict,
    test: pd.DataFrame,
    train: pd.DataFrame,
    k: int,
    max_users: int | None,
) -> dict:
    test_by_user: dict[int, set[str]] = defaultdict(set)
    for row in test.itertuples(index=False):
        test_by_user[int(row.user_id)].add(str(row.movie_id))

    train_seen: dict[int, set[str]] = defaultdict(set)
    for row in train.itertuples(index=False):
        train_seen[int(row.user_id)].add(str(row.movie_id))

    user_ids = sorted(test_by_user)
    if max_users is not None and len(user_ids) > max_users:
        rng = np.random.default_rng(RANDOM_SEED)
        user_ids = sorted(rng.choice(user_ids, size=max_users, replace=False).tolist())

    names = {
        "collaborative": models["collaborative"],
        "content": models["content"],
        "popularity": models["popularity"],
    }
    report: dict[str, dict] = {}
    for name, model in names.items():
        per_user = []
        t0 = time.time()
        for user_id in user_ids:
            relevant = test_by_user[user_id]
            recs = model.recommend(user_id, k=k, seen=train_seen[user_id])
            per_user.append(metrics_for_ranking(recs, relevant, k))
        summary = _mean_metrics(per_user)
        summary["elapsed_s"] = round(time.time() - t0, 2)
        summary["k"] = k
        report[name] = summary
    return report


def evaluate_cold_start(
    interactions: pd.DataFrame,
    movies: pd.DataFrame,
    users: pd.DataFrame,
    k: int,
    max_users: int,
    prefer_llm: bool,
) -> dict:
    """Users with a self-description: hide ALL history, recommend from text.

    Ground truth = movies the user rated/watched with score >= 7 (liked).
    A popularity baseline that ignores the text is reported for comparison.
    """
    if users.empty or "self_description_likes" not in users.columns:
        return {"error": "No user self-descriptions in the collected data."}

    described = users[users["self_description_likes"].notna()].copy()
    described = described[described["self_description_likes"].astype(str).str.len() > 8]
    likes = interactions[interactions["rating"] >= 7]
    truth = likes.groupby("user_id")["movie_id"].apply(lambda s: set(s.astype(str)))
    described["user_id"] = described["user_id"].astype(int)
    eligible = [
        int(uid)
        for uid in described["user_id"]
        if uid in truth.index and len(truth.loc[uid]) >= 2
    ]
    rng = np.random.default_rng(RANDOM_SEED)
    if len(eligible) > max_users:
        eligible = sorted(rng.choice(eligible, size=max_users, replace=False).tolist())

    pop = PopularityRecommender().fit(interactions)
    cold = ColdStartRecommender(prefer_llm=prefer_llm).fit(interactions, movies, users)
    # Cold-start must not see the user's own history.
    empty_seen: set[str] = set()

    llm_rows = []
    pop_rows = []
    examples = []
    t0 = time.time()
    for user_id in eligible:
        relevant = truth.loc[user_id]
        recs = cold.recommend(user_id, k=k, seen=empty_seen)
        pop_recs = pop.recommend(user_id, k=k, seen=empty_seen)
        llm_rows.append(metrics_for_ranking(recs, relevant, k))
        pop_rows.append(metrics_for_ranking(pop_recs, relevant, k))
        if len(examples) < 5:
            profile = described[described["user_id"] == user_id].iloc[0]
            examples.append(
                {
                    "user_id": int(user_id),
                    "likes": str(profile["self_description_likes"])[:240],
                    "dislikes": str(profile.get("self_description_dislikes") or "")[:160],
                    "prefs": cold.last_prefs,
                    "recommended": recs[:8],
                    "held_liked": sorted(relevant)[:8],
                }
            )
    used_llm = bool(load_api_key()) and prefer_llm
    return {
        "k": k,
        "n_users": len(eligible),
        "used_llm_api": used_llm,
        "extractor": "llm" if used_llm else "heuristic_schema_compatible",
        "cold_start": _mean_metrics(llm_rows),
        "popularity_baseline": _mean_metrics(pop_rows),
        "elapsed_s": round(time.time() - t0, 2),
        "examples": examples,
        "note": (
            "Ground truth is movies this user actually scored >= 7. "
            "History is hidden; only the signup self-description is used."
        ),
    }


def run_evaluation(max_users: int, k: int, cold_start_users: int, prefer_llm: bool) -> dict:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    interactions = build_interactions(persist=True)
    movies = load_movies()
    users = load_users()
    train_df, test_df = time_split(
        interactions, TEST_HOLD_FRACTION, MIN_INTERACTIONS_FOR_SPLIT
    )

    models = {
        "collaborative": CollaborativeItemCF().fit(train_df),
        "content": ContentTfidfRecommender().fit(train_df, movies),
        "popularity": PopularityRecommender().fit(train_df),
    }
    ranking = evaluate_recommenders(models, test_df, train_df, k=k, max_users=max_users)
    cold = evaluate_cold_start(
        interactions,
        movies,
        users,
        k=k,
        max_users=cold_start_users,
        prefer_llm=prefer_llm,
    )

    # Pick a model for later team deployment: higher NDCG@K on the ranking task.
    best_name = max(
        ("collaborative", "content"),
        key=lambda name: ranking[name]["ndcg"],
    )
    report = {
        "k": k,
        "random_seed": RANDOM_SEED,
        "n_train_rows": int(len(train_df)),
        "n_test_rows": int(len(test_df)),
        "n_eval_users_cap": max_users,
        "ranking": ranking,
        "cold_start": cold,
        "recommended_for_deployment": best_name,
        "deployment_rationale": (
            f"{best_name} has the higher NDCG@{k} on the chronological hold-out "
            "among the two personalized approaches."
        ),
    }
    METRICS_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    print(f"Wrote {METRICS_PATH}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate I2 recommenders")
    parser.add_argument("--k", type=int, default=TOP_K)
    parser.add_argument(
        "--max-users",
        type=int,
        default=400,
        help="Cap ranking-eval users (speed). Use 0 for all.",
    )
    parser.add_argument("--cold-start-users", type=int, default=40)
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Force the schema-compatible heuristic extractor (no API calls)",
    )
    args = parser.parse_args()
    max_users = None if args.max_users == 0 else args.max_users
    run_evaluation(
        max_users=max_users or 10**9,
        k=args.k,
        cold_start_users=args.cold_start_users,
        prefer_llm=not args.no_llm,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
