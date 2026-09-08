"""CLI: recommend movies for a user id.

    python -m src.recommend --user-id 2 --model collaborative
    python -m src.recommend --user-id 2 --model content
    python -m src.recommend --user-id 2 --model coldstart
    python -m src.recommend --user-id 2 --model auto
"""

from __future__ import annotations

import argparse
import json

from src.config import TOP_K
from src.models.cold_start import load_api_key
from src.train import load_models


def recommend(
    user_id: int,
    model_name: str,
    k: int,
    likes: str | None = None,
    dislikes: str | None = None,
) -> dict:
    bundle = load_models()
    cf = bundle["collaborative"]
    content = bundle["content"]
    cold = bundle["cold_start"]
    pop = bundle["popularity"]

    name = model_name.lower()
    if name == "auto":
        # Existing users with a CF latent vector use SVD; everyone else uses
        # the LLM cold-start (or popularity if they also have no description).
        if cf.maps and int(user_id) in cf.maps.user_to_idx:
            name = "collaborative"
        else:
            name = "coldstart"

    if name in {"collaborative", "cf", "svd"}:
        recs = cf.recommend(user_id, k=k)
        used = "collaborative"
    elif name in {"content", "tfidf"}:
        recs = content.recommend(user_id, k=k)
        used = "content"
    elif name in {"popularity", "pop"}:
        recs = pop.recommend(user_id, k=k)
        used = "popularity"
    elif name in {"coldstart", "cold", "llm"}:
        recs = cold.recommend(user_id, k=k, likes=likes, dislikes=dislikes)
        used = "coldstart"
    else:
        raise ValueError(f"Unknown model {model_name!r}")

    return {
        "user_id": int(user_id),
        "model": used,
        "k": k,
        "movie_ids": recs,
        "llm_key_present": bool(load_api_key()),
        "cold_start_prefs": cold.last_prefs if used == "coldstart" else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Recommend movies for a user")
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument(
        "--model",
        default="auto",
        help="collaborative | content | coldstart | popularity | auto",
    )
    parser.add_argument("--k", type=int, default=TOP_K)
    parser.add_argument("--likes", default=None, help="Override self-description likes")
    parser.add_argument("--dislikes", default=None)
    args = parser.parse_args()
    result = recommend(args.user_id, args.model, args.k, args.likes, args.dislikes)
    print(json.dumps(result, indent=2, default=str))
    print(",".join(result["movie_ids"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
