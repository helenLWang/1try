# Evaluation

We do **not** grade ourselves on a leaderboard number; the goal is a
reasonable, reproducible comparison. All figures below come from
`python -m src.evaluate` after `python -m src.collect` / `python -m src.train`.
Exact counts for the run are in `artifacts/metrics.json` and
`artifacts/train_log.json`.

## Ranking task (existing users)

**Metric.** For each user with ≥5 interactions we sort their rows by
timestamp and hold out the last 20% (at least one row). Models are fit only
on the prefix. We ask for 20 movie ids, excluding train items.

Let \(R_u\) be the held-out movie set and \(\hat{L}_u\) the top-20 list.

- HitRate@20: 1 if \(R_u \cap \hat{L}_u\) is non-empty
- Precision@20: \(|R_u \cap \hat{L}_u| / 20\)
- Recall@20: \(|R_u \cap \hat{L}_u| / |R_u|\)
- NDCG@20: binary relevance, DCG / IDCG

We cap evaluation at 400 randomly chosen test users (seed 42) so a laptop
run finishes quickly; `--max-users 0` uses everyone. Popularity
(`count × mean score`) is a non-personalized baseline, not one of the two
required approaches.

**Data.** Interactions are the merged explicit ratings and implicit
watch-progress scores described in `model.md`, built from the Kafka window
in `data/collection_meta.json`.

**Results.** *(filled after the training run; see `artifacts/metrics.json`)*

| Model | HitRate@20 | Precision@20 | Recall@20 | NDCG@20 |
| --- | ---: | ---: | ---: | ---: |
| Collaborative SVD | TBD | TBD | TBD | TBD |
| Content TF-IDF | TBD | TBD | TBD | TBD |
| Popularity baseline | TBD | TBD | TBD | TBD |

**Choice for later deployment.** We pick the personalized model with higher
NDCG@20 (named in `artifacts/metrics.json` as `recommended_for_deployment`).
SVD should win if co-watching structure is strong; TF-IDF should win if the
window is too sparse for factorization. Popularity is only a sanity check:
if SVD cannot beat it, we would not ship SVD.

## Cold-start (LLM / self-description)

**Protocol.** Take users who (a) have a non-empty `self_description_likes`
and (b) have at least two interactions scored ≥ 7. Hide **all** of their
history. Recommend 20 movies from the text alone. Ground truth is those
≥ 7 movies (a proxy for “this is what they actually liked”). Compare to
the same popularity list, which ignores the text. Up to 40 such users
(seed 42). This is a small demonstration, as allowed.

**Results.** *(filled after the run)*

| Method | HitRate@20 | Recall@20 | NDCG@20 |
| --- | ---: | ---: | ---: |
| Cold-start (LLM if `api.key` else heuristic extractor + same scorer) | TBD | TBD | TBD |
| Popularity (no text) | TBD | TBD | TBD |

If the LLM key is present, `used_llm_api` in `metrics.json` is true and the
extractor is the chat model; otherwise we still evaluate the catalog scorer
with the schema-compatible heuristic so the command is reproducible. A few
example users (description, parsed tastes, recommendations vs. held likes)
are stored under `cold_start.examples` in `metrics.json`.

**How to repeat.** Tunnel up, collect, `python -m src.evaluate`. For the
real LLM, add `api.key`. Use `--no-llm` to force the heuristic path.
