"""Le Wang (lew2) M1 candidate: one line of movie ids.

Milestone 1 wants:

    GET /recommend/<userid>
    -> id1,id2,...,idN   (max 20, no spaces, no JSON)

This file is the only thing teammates need to call.

- User is in the CF matrix  -> item-item collaborative filtering
- User is new / not in CF   -> LLM cold-start if they have signup text
- No history and no text    -> popularity (until the team fetches /user/<id>)
"""

from __future__ import annotations

import argparse

from src.config import TOP_K
from src.recommend import recommend


def recommend_ids(user_id: int, k: int = TOP_K) -> list[str]:
    result = recommend(int(user_id), "auto", k)
    return [str(mid) for mid in result["movie_ids"][:k]]


def recommend_line(user_id: int, k: int = TOP_K) -> str:
    """Comma-separated ids. Empty string only if the model has nothing."""
    return ",".join(recommend_ids(user_id, k=k))


def main() -> int:
    parser = argparse.ArgumentParser(description="Print M1-format recommendations")
    parser.add_argument("user_id", type=int)
    parser.add_argument("--k", type=int, default=TOP_K)
    args = parser.parse_args()
    print(recommend_line(args.user_id, k=args.k), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
