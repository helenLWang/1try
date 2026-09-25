"""Cold-start evaluation, per DATA_GUIDE.md section 5 / EVALUATION.md 3.3:
metrics.py cannot score users with no training history, so we simulate cold
start by holding out the *real* training history of warm test users and
scoring only from their users.csv self-description text, against the same
post-cutoff ground truth metrics.py uses for the other two models. Compared
against the popularity list for the *same* sampled users (not the full-set
baseline in baseline_popularity.json, since a subsample shifts the mean).
"""
from __future__ import annotations

import json
import os
import random
import sys
import time

import numpy as np
import psutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.cold_start import ColdStartRecommender  # noqa: E402

from adapters import load_interactions, load_movies, load_users  # noqa: E402
from metrics import load_eval_data, precision_at_k, recall_at_k, ndcg_at_k  # noqa: E402

PROC = psutil.Process(os.getpid())
SAMPLE_N = 2000
K = 20


def main():
    print("Loading data...")
    train = load_interactions("data/v2/train.csv")
    movies = load_movies("data/movies.csv")
    users = load_users("data/users.csv")
    data = load_eval_data("data/v2/train.csv", "data/v2/test.csv")

    # Only users with a real self-description are a fair cold-start test:
    # ~70% of users.csv rows have one (DATA_GUIDE.md section 3).
    has_desc = users[
        users["self_description_likes"].fillna("").str.len().gt(0)
        | users["self_description_dislikes"].fillna("").str.len().gt(0)
    ]
    eligible = set(data.truth) & set(has_desc["user_id"].astype(str))
    print(f"  eligible warm users with a self-description: {len(eligible)}")

    random.seed(0)
    sample = random.sample(sorted(eligible), min(SAMPLE_N, len(eligible)))
    print(f"  sampling {len(sample)} of them, pretending each is cold")

    rss0 = PROC.memory_info().rss / 1e6
    t0 = time.perf_counter()
    cold = ColdStartRecommender(prefer_llm=True).fit(train, movies, users)
    train_s = time.perf_counter() - t0
    rss1 = PROC.memory_info().rss / 1e6
    print(f"  fit() in {train_s:.2f}s, rss delta {rss1 - rss0:.1f} MB")

    popularity_order = (
        train.groupby("movie_id").size().sort_values(ascending=False).index.astype(str).tolist()
    )

    totals = {"precision": 0.0, "recall": 0.0, "ndcg": 0.0}
    pop_totals = {"precision": 0.0, "recall": 0.0, "ndcg": 0.0}
    hit = 0
    pop_hit = 0
    lat = []
    used_llm = 0
    all_recs = set()

    for uid in sample:
        row = has_desc[has_desc["user_id"].astype(str) == uid].iloc[0]
        likes = row.get("self_description_likes") or ""
        dislikes = row.get("self_description_dislikes") or ""
        relevant = data.truth[uid]

        t0 = time.perf_counter()
        ranked = cold.recommend_from_text(likes, dislikes, k=K)
        lat.append((time.perf_counter() - t0) * 1000)
        if cold.last_prefs and cold.last_prefs.get("source") == "llm":
            used_llm += 1
        all_recs.update(ranked)

        totals["precision"] += precision_at_k(ranked, relevant, K)
        totals["recall"] += recall_at_k(ranked, relevant, K)
        totals["ndcg"] += ndcg_at_k(ranked, relevant, K)
        if any(m in relevant for m in ranked[:K]):
            hit += 1

        pop_ranked = popularity_order[:K]
        pop_totals["precision"] += precision_at_k(pop_ranked, relevant, K)
        pop_totals["recall"] += recall_at_k(pop_ranked, relevant, K)
        pop_totals["ndcg"] += ndcg_at_k(pop_ranked, relevant, K)
        if any(m in relevant for m in pop_ranked):
            pop_hit += 1

    n = len(sample)
    result = {
        "sampled_users": n,
        "used_llm_path": used_llm,
        "used_heuristic_path": n - used_llm,
        "cold_start": {
            "precision@20": totals["precision"] / n,
            "recall@20": totals["recall"] / n,
            "ndcg@20": totals["ndcg"] / n,
            "hit_rate@20": hit / n,
        },
        "popularity_same_users": {
            "precision@20": pop_totals["precision"] / n,
            "recall@20": pop_totals["recall"] / n,
            "ndcg@20": pop_totals["ndcg"] / n,
            "hit_rate@20": pop_hit / n,
        },
        "latency_median_ms": float(np.median(lat)),
        "latency_p95_ms": float(np.percentile(lat, 95)),
        "distinct_films_recommended": len(all_recs),
        "distinct_films_pct": len(all_recs) / 20784,
        "fit_time_s": train_s,
    }
    print(json.dumps(result, indent=2))
    with open("results_cold_start.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nWrote results_cold_start.json")


if __name__ == "__main__":
    main()
