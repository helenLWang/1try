"""Train + score collaborative filtering and content-based models on the v2
snapshot, using the team's shared metrics.py exactly as required by
DATA_GUIDE.md section 5. Run from inside m1-team-eval/.
"""
from __future__ import annotations

import json
import os
import pickle
import sys
import time

import numpy as np
import pandas as pd
import psutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.collaborative import CollaborativeItemCF  # noqa: E402
from src.models.content import ContentTfidfRecommender  # noqa: E402

from adapters import load_interactions, load_movies  # noqa: E402
from metrics import load_eval_data, score_model  # noqa: E402

PROC = psutil.Process(os.getpid())


def peak_rss_mb() -> float:
    return PROC.memory_info().rss / 1e6


def measure_latency(recommend_fn, user_ids, k=20):
    lat = []
    for u in user_ids[:1000]:
        t0 = time.perf_counter()
        recommend_fn(int(u), k)
        lat.append((time.perf_counter() - t0) * 1000)
    return float(np.median(lat)), float(np.percentile(lat, 95))


def coverage(recommend_fn, user_ids, k=20, n_catalog=20784, sample=5000):
    films = set()
    for u in user_ids[:sample]:
        films.update(recommend_fn(int(u), k))
    return len(films), len(films) / n_catalog


def main():
    print("Loading data...")
    train = load_interactions("data/v2/train.csv")
    movies = load_movies("data/movies.csv")
    print(f"  train interactions: {len(train)}, movies: {len(movies)}")

    print("Loading eval harness (metrics.py)...")
    data = load_eval_data("data/v2/train.csv", "data/v2/test.csv")
    users = data.users
    print(f"  eligible/scorable users: {len(users)}")

    results = {}

    # ---------------- Collaborative filtering ----------------
    print("\n=== Collaborative filtering ===")
    rss0 = peak_rss_mb()
    t0 = time.perf_counter()
    cf = CollaborativeItemCF().fit(train)
    train_s = time.perf_counter() - t0
    rss1 = peak_rss_mb()
    print(f"  trained in {train_s:.1f}s, rss delta {rss1 - rss0:.1f} MB (proc total {rss1:.1f} MB)")

    cf_recommend = lambda u, k=20: cf.recommend(u, k)
    score = score_model(cf_recommend, data, k=20)
    print("  score:", score)
    med, p95 = measure_latency(cf_recommend, users)
    print(f"  latency median {med:.2f}ms p95 {p95:.2f}ms")
    n_films, pct = coverage(cf_recommend, users)
    print(f"  coverage: {n_films} distinct films ({pct*100:.1f}%)")

    os.makedirs("models", exist_ok=True)
    with open("models/collaborative.pkl", "wb") as f:
        pickle.dump(cf, f)
    artifact_mb = os.path.getsize("models/collaborative.pkl") / 1e6
    print(f"  artifact size: {artifact_mb:.2f} MB")

    results["collaborative"] = {
        "train_time_s": train_s,
        "rss_after_mb": rss1,
        **score,
        "latency_median_ms": med,
        "latency_p95_ms": p95,
        "coverage_films": n_films,
        "coverage_pct": pct,
        "artifact_mb": artifact_mb,
    }

    # ---------------- Content-based ----------------
    print("\n=== Content-based (TF-IDF) ===")
    rss0 = peak_rss_mb()
    t0 = time.perf_counter()
    content = ContentTfidfRecommender().fit(train, movies)
    train_s = time.perf_counter() - t0
    rss1 = peak_rss_mb()
    print(f"  trained in {train_s:.1f}s, rss delta {rss1 - rss0:.1f} MB (proc total {rss1:.1f} MB)")

    content_recommend = lambda u, k=20: content.recommend(u, k)
    score = score_model(content_recommend, data, k=20)
    print("  score:", score)
    med, p95 = measure_latency(content_recommend, users)
    print(f"  latency median {med:.2f}ms p95 {p95:.2f}ms")
    n_films, pct = coverage(content_recommend, users)
    print(f"  coverage: {n_films} distinct films ({pct*100:.1f}%)")

    with open("models/content.pkl", "wb") as f:
        pickle.dump(content, f)
    artifact_mb = os.path.getsize("models/content.pkl") / 1e6
    print(f"  artifact size: {artifact_mb:.2f} MB")

    results["content"] = {
        "train_time_s": train_s,
        "rss_after_mb": rss1,
        **score,
        "latency_median_ms": med,
        "latency_p95_ms": p95,
        "coverage_films": n_films,
        "coverage_pct": pct,
        "artifact_mb": artifact_mb,
    }

    with open("results_cf_content.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nWrote results_cf_content.json")


if __name__ == "__main__":
    main()
