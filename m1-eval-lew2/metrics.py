"""Shared metric implementation. Every candidate is scored with THIS file.

Why one file
------------
Precision, Recall and NDCG all have defensible variants: whether to divide
NDCG by an ideal capped at k, whether a user with no hits counts as zero or is
skipped, whether already-seen items are excluded. Three people making three
reasonable choices produce three incomparable numbers. So nobody writes their
own: import from here.

Definitions used, state these in the report
-------------------------------------------
k                20
ground truth     films a user watched AFTER the split cutoff that they had NOT
                 watched before it. Excluding the already-seen ones matters:
                 every model is required to filter them out, so scoring a model
                 on an item it was structurally unable to return would
                 understate it.
eligible users   users with at least `min_history` interactions in train AND at
                 least one ground-truth item. Users with no training history
                 cannot be scored fairly by any of the three metrics.
relevance        binary. Any watch is relevance 1. NDCG therefore reduces to a
                 position-discounted hit measure; it does NOT express degrees
                 of liking. Pass graded=True to use minutes_watched instead.
zero hits        counts as 0.0, it is not skipped. Skipping them would inflate
                 every score and make the metrics incomparable to published
                 numbers.

Usage
-----
    from metrics import load_eval_data, score_model
    data = load_eval_data("data/v1/train.csv", "data/v1/test.csv")
    print(score_model(recommend, data, k=20))
"""

import csv
import math
from collections import defaultdict

K = 20
MIN_HISTORY = 1


class EvalData:
    """Train history, ground truth and the eligible user list, built once."""

    def __init__(self, seen, truth, grades):
        self.seen = seen        # user -> set(movie) watched before the cutoff
        self.truth = truth      # user -> set(movie) watched after, unseen before
        self.grades = grades    # (user, movie) -> minutes_watched, for graded NDCG

    @property
    def users(self):
        return list(self.truth)


def load_eval_data(train_csv, test_csv, min_history=MIN_HISTORY):
    seen = defaultdict(set)
    grades = {}
    with open(train_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            seen[row["user_id"]].add(row["movie_id"])

    held = defaultdict(set)
    with open(test_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            user, movie = row["user_id"], row["movie_id"]
            if movie in seen.get(user, ()):
                continue  # already watched before the cutoff, not a prediction target
            held[user].add(movie)
            grades[(user, movie)] = int(row.get("minutes_watched", 1) or 1)

    truth = {u: m for u, m in held.items()
             if len(seen.get(u, ())) >= min_history and m}
    return EvalData(dict(seen), truth, grades)


def precision_at_k(ranked, relevant, k=K):
    """Hits divided by k.

    Ceiling warning: with ~1-3 held-out items per user, a PERFECT model scores
    at most len(relevant)/k, often 0.05. Report it next to the value or the
    number reads as failure.
    """
    if k <= 0:
        return 0.0
    return sum(1 for m in ranked[:k] if m in relevant) / k


def recall_at_k(ranked, relevant, k=K):
    """Hits divided by the number of held-out items. The honest primary here."""
    if not relevant:
        return 0.0
    return sum(1 for m in ranked[:k] if m in relevant) / len(relevant)


def ndcg_at_k(ranked, relevant, k=K, grades=None, user=None):
    """Position-discounted gain over the ideal ranking.

    Binary by default. The ideal is capped at k, so a user with 50 held-out
    items is not punished for a top-20 list being short.
    """
    def gain(movie):
        if grades is None or user is None:
            return 1.0
        return float(grades.get((user, movie), 1))

    dcg = 0.0
    for i, movie in enumerate(ranked[:k]):
        if movie in relevant:
            dcg += gain(movie) / math.log2(i + 2)

    ideal = sorted((gain(m) for m in relevant), reverse=True)[:k]
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def score_model(recommend_fn, data, k=K, graded=False, sample_users=None, seed=0):
    """Average the three metrics over eligible users.

    recommend_fn(user_id, k) -> list of movie_id strings, best first.
    Users with zero hits contribute 0.0 rather than being dropped.
    """
    import random

    users = data.users
    if sample_users and sample_users < len(users):
        users = random.Random(seed).sample(users, sample_users)

    grades = data.grades if graded else None
    totals = {"precision": 0.0, "recall": 0.0, "ndcg": 0.0}
    hit_users = 0

    for user in users:
        relevant = data.truth[user]
        ranked = list(recommend_fn(int(user), k))
        # Caught here rather than silently scoring a broken model.
        already = data.seen.get(user, set())
        leaked = [m for m in ranked if m in already]
        if leaked:
            raise ValueError(
                f"user {user}: recommended {len(leaked)} already-watched films, "
                f"e.g. {leaked[0]}. Every candidate must exclude training history.")
        totals["precision"] += precision_at_k(ranked, relevant, k)
        totals["recall"] += recall_at_k(ranked, relevant, k)
        totals["ndcg"] += ndcg_at_k(ranked, relevant, k, grades, user)
        if any(m in relevant for m in ranked[:k]):
            hit_users += 1

    n = max(len(users), 1)
    return {
        "users_scored": len(users),
        "k": k,
        "relevance": "graded (minutes_watched)" if graded else "binary",
        f"precision@{k}": totals["precision"] / n,
        f"recall@{k}": totals["recall"] / n,
        f"ndcg@{k}": totals["ndcg"] / n,
        f"hit_rate@{k}": hit_users / n,
        "mean_truth_size": sum(len(v) for v in data.truth.values()) / max(len(data.truth), 1),
    }
