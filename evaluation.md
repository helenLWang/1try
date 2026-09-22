# Evaluation

`python -m src.evaluate --max-users 400 --cold-start-users 40` after 4.94M Kafka lines from 12 slices (2026-07-17–2026-09-08; 30,628 ratings, 123,780 watch pairs, 17,404 movies, 82,688 users). Ranking matches the earlier hold-out. Cold-start used Gemini `gemini-3.5-flash-lite` (38/40 LLM extracts, 2 fallbacks) plus the catalog scorer; re-rank off (`I2_COLD_START_RERANK=0`).

## Ranking (existing users)

**Protocol.** Merge ratings with implicit watch-progress scores (`model.md`). Sort each user by time. 2–4 interactions: leave-one-out. ≥5: hold out the last 20%. Fit on the prefix. Predict 20 ids, excluding train items.

- HitRate@20: 1 if any held-out movie is in the list
- Precision@20 / Recall@20 on that set
- NDCG@20 with binary relevance

400 random test users (seed 42). Popularity (`count × mean score`) is a baseline, not one of the two required models. Users absent from the CF matrix fall back to popularity.

| Model | HitRate@20 | Precision@20 | Recall@20 | NDCG@20 |
| --- | ---: | ---: | ---: | ---: |
| Item–item CF | 0.095 | 0.0048 | 0.088 | 0.035 |
| Content TF-IDF | 0.010 | 0.0005 | 0.008 | 0.003 |
| Popularity baseline | 0.115 | 0.0060 | 0.110 | 0.043 |

**Choice.** Popularity is slightly ahead (short histories). We still pick **item–item CF for later deployment**: it already falls back to popularity, it can use co-watch structure as the log grows, and `auto` sends true new users to the LLM. We would not ship content-based as the primary ranker.

## Cold-start (self-description)

**Protocol.** 40 users with a likes blurb and ≥2 items scored ≥7. Hide **all** history; recommend 20 ids from the text. Ground truth = those ≥7 movies. Popularity ignores the text. `used_llm_api` is true.

| Method | HitRate@20 | Recall@20 | NDCG@20 |
| --- | ---: | ---: | ---: |
| Cold-start (LLM extract + catalog scorer) | 0.050 | 0.016 | 0.017 |
| Cold-start (heuristic extractor, previous table) | 0.075 | 0.029 | 0.013 |
| Popularity (no text) | 0.275 | 0.124 | 0.068 |

Ranking numbers are unchanged. Versus the heuristic, LLM NDCG rose (0.017 vs 0.013) while hit/recall fell: named titles pull the list away from accidental overlap with later ratings. Re-rank was skipped for latency; the LLM still filled the JSON the scorer consumes.

**Demonstration.** LLM `liked_titles` (heuristic left this empty): 9375 → *The Godfather* / *The English Patient* / *Twelve Monkeys*; 12502 → *Gone with the Wind* / *The Sound of Music* / *Close Encounters*; 12943 → *Star Wars*, *Pulp Fiction*, *Forrest Gump* (*Star Wars* was held); 13993 wrote “fugitive and t2” → *The Fugitive*, *Terminator 2*. Signup prose ≠ later ratings (Godfather fan whose held likes include *Happy Gilmore*), so popularity still wins overlap. Qualitative match to the text is the intended check.

**Repeat.** Start the tunnel, then:

```bash
python -m src.collect --max-events 5000000 --windows 12
python -m src.train
GEMINI_MODEL=gemini-3.5-flash-lite I2_COLD_START_RERANK=0 \
  python -m src.evaluate --max-users 400 --cold-start-users 40
```

Put a key in gitignored `api.key` for the LLM; `--no-llm` uses the heuristic.
