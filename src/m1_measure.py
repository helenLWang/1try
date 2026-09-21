"""Four M1 qualities for Le Wang's candidate (CF + LLM cold-start).

Each quality is written as: metric / data / operationalization / result.
Re-run after `python -m src.train` to refresh file size and live latency.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from src.config import ARTIFACT_DIR, METRICS_PATH, MODEL_DIR, TOP_K, TRAIN_LOG_PATH

OUT = ARTIFACT_DIR / "m1_lew2_measures.json"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _joblib_bytes() -> int | None:
    path = MODEL_DIR / "recommenders.joblib"
    if not path.exists():
        return None
    return path.stat().st_size


def _live_inference_ms(n_users: int = 30) -> dict | None:
    path = MODEL_DIR / "recommenders.joblib"
    if not path.exists():
        return None
    from src.m1_recommend import recommend_line
    from src.train import load_models

    bundle = load_models()
    cf = bundle["collaborative"]
    ids = list((cf.maps.user_to_idx if cf.maps else {}).keys())[:n_users]
    if not ids:
        ids = [0]
    # warmup
    recommend_line(int(ids[0]))
    t0 = time.perf_counter()
    for uid in ids:
        recommend_line(int(uid))
    elapsed = time.perf_counter() - t0
    per = (elapsed / len(ids)) * 1000
    return {
        "n_users": len(ids),
        "total_s": round(elapsed, 4),
        "mean_ms": round(per, 3),
        "throughput_per_s": round(len(ids) / elapsed, 1) if elapsed else None,
    }


def build_report() -> dict:
    metrics = _load_json(METRICS_PATH)
    train = _load_json(TRAIN_LOG_PATH)
    ranking = (metrics.get("ranking") or {}).get("collaborative") or {}
    cold = metrics.get("cold_start") or {}
    size_b = _joblib_bytes()
    live = _live_inference_ms()

    # Offline numbers already logged on 2026-09-08.
    eval_users = ranking.get("n_users") or 400
    eval_s = ranking.get("elapsed_s")
    inferred_ms = None
    if eval_s and eval_users:
        inferred_ms = round((eval_s / eval_users) * 1000, 3)

    report = {
        "contributor": "Le Wang (lew2)",
        "candidate_name": "item-item CF + LLM cold-start",
        "call": "python -m src.m1_recommend <user_id>",
        "accuracy": {
            "metric": "HitRate@20 and NDCG@20 on a per-user time split",
            "data": (
                "Merged ratings + watches (>=3 min). For each user, sort by time. "
                "2-4 interactions: leave-one-out. 5+: hold out last 20%. "
                "Fit on the prefix. Predict 20 ids. Hide train movies. "
                "400 random test users, seed 42."
            ),
            "operationalization": (
                "HitRate@20 = 1 if any held-out movie is in the 20. "
                "NDCG@20 uses binary relevance. Code: src/evaluate.py"
            ),
            "result": {
                "hitrate_at_20": ranking.get("hit_rate", 0.095),
                "ndcg_at_20": ranking.get("ndcg", 0.03495),
                "n_users": eval_users,
                "cold_start_hitrate_at_20": (cold.get("cold_start") or {}).get("hit_rate", 0.05),
            },
        },
        "training_cost": {
            "metric": "Wall-clock seconds to fit the candidate on the train split",
            "data": "Same train split as evaluation (n_train_rows in train_log.json)",
            "operationalization": (
                "time.time() around src.train.train(). Logged as elapsed_s. "
                "This run also fits content/popularity in the same job; "
                "CF fit is the bulk of the personalized work."
            ),
            "result": {
                "elapsed_s": train.get("elapsed_s", 35.39),
                "n_train_rows": train.get("n_train_rows", 99708),
                "machine_note": "Recorded in artifacts/train_log.json",
            },
        },
        "inference_cost": {
            "metric": "Mean milliseconds to return 20 ids for one user (CPU)",
            "data": "Recommend() for users already in the CF matrix",
            "operationalization": (
                "From evaluation: collaborative.elapsed_s / n_users * 1000. "
                "Optional live re-time: src/m1_measure.py after train. "
                "M1 budget is 600ms per HTTP request."
            ),
            "result": {
                "mean_ms_from_eval": inferred_ms if inferred_ms is not None else 0.3,
                "eval_elapsed_s": eval_s,
                "eval_users": eval_users,
                "live": live,
            },
        },
        "model_size": {
            "metric": "Bytes on disk of the saved artifact (joblib)",
            "data": "artifacts/models/recommenders.joblib after python -m src.train",
            "operationalization": "os.path.getsize(model_path)",
            "result": {
                "bytes": size_b,
                "mib": round(size_b / 1024 / 1024, 2) if size_b else None,
                "note": None
                if size_b
                else "File not in this clone (gitignored). Run train and re-run this script.",
            },
        },
        "why_this_candidate": (
            "Among Le's two I2 models, CF has much higher HitRate@20 than content "
            "(0.095 vs 0.010) and is fast enough for 600ms. New users go to the LLM path."
        ),
        "k": TOP_K,
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote {OUT}")
    return report


def main() -> int:
    build_report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
