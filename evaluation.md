# Evaluation

Numbers come from `python -m src.evaluate --max-users 400 --cold-start-users 40 --no-llm` after `python -m src.collect --max-events 5000000 --windows 12`. That run scanned 4.94M Kafka lines from 12 slices spanning 2026-07-17 to 2026-09-08 (30,628 ratings, 123,780 watch pairs, 17,404 movies, 82,688 users). Details: `data/collection_meta.json`, `artifacts/metrics.json`, `artifacts/train_log.json`.

## Ranking (existing users)

**Protocol.** Merge explicit ratings with implicit watch-progress scores (`model.md`). Sort each user by time. Users with 2–4 interactions: leave-one-out. Users with ≥5: hold out the last 20%. Fit only on the prefix. Predict 20 ids, excluding train items.

- HitRate@20: 1 if any held-out movie is in the list
- Precision@20 / Recall@20 on that set
- NDCG@20 with binary relevance

We score 400 random test users (seed 42). Popularity (`count × mean score`) is a baseline, not one of the two required models. Users who never enter the CF matrix fall back to popularity, matching `recommend`.

| Model | HitRate@20 | Precision@20 | Recall@20 | NDCG@20 |
| --- | ---: | ---: | ---: | ---: |
| Item–item CF | 0.095 | 0.0048 | 0.088 | 0.035 |
| Content TF-IDF | 0.010 | 0.0005 | 0.008 | 0.003 |
| Popularity baseline | 0.115 | 0.0060 | 0.110 | 0.043 |

**Choice.** Popularity is slightly ahead on this window (many users still have short histories). We still pick **item–item CF for later deployment**: it already falls back to popularity, it can use co-watch structure as the team log grows, and `auto` sends true new users to the LLM. We would not ship content-based as the primary ranker.

## Cold-start (self-description)

**Protocol.** 40 users with non-empty `self_description_likes` and ≥2 items scored ≥7. Hide **all** history. Recommend 20 ids from the text. Ground truth = those ≥7 movies. Compare to popularity (ignores text). No API key was present, so the schema-compatible heuristic extractor ran (same scorer the LLM fills). With `api.key`, `used_llm_api` is true.

| Method | HitRate@20 | Recall@20 | NDCG@20 |
| --- | ---: | ---: | ---: |
| Cold-start (heuristic extractor + catalog scorer) | 0.075 | 0.029 | 0.013 |
| Popularity (no text) | 0.275 | 0.124 | 0.068 |

**Demonstration.** The scorer surfaces titles the user named: user 9375 → *The Godfather* / *The English Patient* / *Twelve Monkeys*; user 12502 → *Gone with the Wind* / *Close Encounters*; user 12943 → *Star Wars*, *Pulp Fiction*, *Forrest Gump* (and *Star Wars* was in that user’s held likes). Signup prose is not the same as later high ratings (e.g. Godfather fan whose held likes include *Happy Gilmore*), so popularity wins accidental overlap. Qualitative match to the text is the intended small-scale check.

**Repeat.** Start the tunnel, then:

```bash
python -m src.collect --max-events 5000000 --windows 12
python -m src.train
python -m src.evaluate --max-users 400 --cold-start-users 40
```

Put a key in `api.key` so cold-start uses the LLM; add `--no-llm` to force
the heuristic extractor.
