# Evaluation

Numbers come from `python -m src.evaluate --max-users 400 --cold-start-users 40 --no-llm` after collecting 5,000,000 recent `movielog1` events (32,400 ratings, 57,002 watch pairs, 14,583 movies, 8-hour window 2026-09-08). Full JSON: `artifacts/metrics.json`. Hyperparameters: `artifacts/train_log.json`.

## Ranking (existing users)

**Protocol.** Merge explicit ratings with implicit watch-progress scores (`model.md`). Per user, sort by time. Users with 2–4 interactions: leave-one-out. Users with ≥5: hold out the last 20%. Fit only on the prefix. Predict 20 ids, excluding train items.

- HitRate@20: 1 if any held-out movie is in the list
- Precision@20 / Recall@20 on that set
- NDCG@20 with binary relevance

We score 400 random test users (seed 42). Popularity (`count × mean score`) is a baseline, not one of the two required models. Most users in this window have a single movie, so collaborative filtering falls back to popularity for them — that is also how `recommend` behaves.

| Model | HitRate@20 | Precision@20 | Recall@20 | NDCG@20 |
| --- | ---: | ---: | ---: | ---: |
| Item–item CF | 0.0825 | 0.0041 | 0.0825 | 0.0329 |
| Content TF-IDF | 0.0050 | 0.0003 | 0.0050 | 0.0012 |
| Popularity baseline | 0.0950 | 0.0048 | 0.0950 | 0.0372 |

**Takeaway.** In an eight-hour slice, two watches from the same user are often unrelated, so metadata similarity almost never recovers the held-out title. Popularity is the strongest list. CF is close to popularity because of the fallback; it does not beat it yet. We still pick **item–item CF for later deployment**: with a longer history window it can use co-watch structure, and `auto` already mixes in popularity / LLM cold-start. We would not ship content-based as the primary ranker on this data.

## Cold-start (self-description)

**Protocol.** 40 users with a non-empty `self_description_likes` and ≥2 items scored ≥7. Hide **all** history. Recommend 20 ids from the text. Ground truth = those ≥7 movies. Compare to popularity (ignores text). No API key was present, so the schema-compatible heuristic extractor ran (same scorer the LLM fills). With `api.key`, `used_llm_api` becomes true.

| Method | HitRate@20 | Recall@20 | NDCG@20 |
| --- | ---: | ---: | ---: |
| Cold-start (heuristic extractor + catalog scorer) | 0.125 | 0.054 | 0.042 |
| Popularity (no text) | 0.200 | 0.121 | 0.073 |

**Takeaway.** The scorer **does** surface titles the user named (e.g. user 16904 → *Star Wars*, *Shawshank*, *Die Hard*, *The Wrong Trousers*; user 24121 → *Se7en*, *Trainspotting*, *Vertigo*). That is the right cold-start behavior. It loses the numeric comparison because signup prose is not the same as the two movies they happened to rate ≥7 in this window (e.g. “I like The Godfather” vs. held-out *Home Alone*). Qualitative match to the text is the demonstration the assignment asks for; popularity wins the accidental overlap with later watches.

**Repeat.** Tunnel, `python -m src.collect`, `python -m src.evaluate`. Add `api.key` for the LLM path; `--no-llm` forces the heuristic.
