# Model Evaluation — Le Wang (lew2)

**Copy this to `EVALUATION_<yourname>.md` and fill it in.** One file per person
so we do not collide in git.

Each of us builds all three approaches: **collaborative filtering**,
**content-based**, and **cold start**. So this file reports three models, not
one. Part 1 is how you measure. Part 2 is the summary. Part 3 is one block per
approach. Part 4 is your verdict.

| | |
| --- | --- |
| Author | Le Wang (lew2) |
| Date | 2026-09-25 |

Do not change the "Fixed protocol" section. Everything else is yours.

---

## Fixed protocol (do not change)

| | |
| --- | --- |
| Snapshot | `v2`, hash `a07a47ee48a2` |
| Train | `data/v2/train.csv`, 2,699,724 interactions, Aug 31 to Sep 20 |
| Test | `data/v2/test.csv`, 298,974 interactions, Sep 21 to 22 |
| Ratings, if you use them | `data/v2/ratings_train.csv`, 1,860,669 rows |
| Film metadata | `data/movies.csv`, 20,784 films, covers every film in the data |
| User self-descriptions | `data/users.csv`, 288,209 users |
| Scorer | `metrics.py`, unchanged, from the folder root |
| k | 20 |
| Metrics | Precision@20, Recall@20, NDCG@20 |
| Relevance | binary, any watch counts the same |
| Ground truth | films watched after the cutoff that the user had not watched before it |
| Eligible users | at least one training interaction and at least one ground-truth film |
| Zero-hit users | count as 0.0, never skipped |
| Already-watched films | must be excluded by the model |

Report on the **full user set**. Use `sample_users` only while developing.

**Baseline: popularity, measured on the full 137,694 users. Read it from
`baseline_popularity.json`, do not recompute it.**

| Metric | Popularity on v2 |
| --- | --- |
| Recall@20 | 0.1006 |
| Precision@20 | 0.0108 |
| NDCG@20 | 0.0502 |
| Hit rate@20 | 0.1952 |
| Mean held-out films per user | 2.16 |

---

# Part 1. How you measure

## 1.1 Accuracy

- **Measure:** Precision@20, Recall@20, and NDCG@20, binary relevance — whether
  a recommended film appears in the set of films the user watched after the
  Sep 21 cutoff that they had not already watched before it.
- **Data:** `data/v2/train.csv` to fit / build the candidate set, `data/v2/test.csv`
  as ground truth, via `metrics.py`'s `load_eval_data`. Every eligible user
  (>=1 train interaction, >=1 ground-truth film) is scored; zero-hit users
  count as 0.0, not skipped.
- **Operationalization:** `metrics.score_model(recommend, data, k=20)`, unmodified,
  on the full 137,694 eligible users for collaborative and content-based.
  Cold start cannot go through this path (see 3.3) — scored separately on a
  2,000-user simulated-cold sample using the same `precision_at_k` /
  `recall_at_k` / `ndcg_at_k` functions from the same file.

## 1.2 Training cost

- **Measure:** Wall-clock fit time in seconds, and resident memory delta during
  fit.
- **Data:** `data/v2/train.csv` (+ `data/movies.csv` for content, + `data/users.csv`
  for cold start).
- **Operationalization:** `time.perf_counter()` around each `.fit(...)` call
  for training time. Memory follows the team's standardized definition
  (proposed by Sarah, 2026-09-27): **maximum resident set size (RSS) for one
  full training process, including data loading + model fitting, but
  excluding serialization/pickling.** Measured via a background thread
  polling `psutil.Process().memory_info().rss` every 20ms from just before
  `load_interactions(...)` through the end of `.fit(...)`, keeping the
  running max — not `resource.getrusage`, which is POSIX-only and unavailable
  on Windows.

## 1.3 Inference cost and throughput

- **Measure:** Median and p95 latency per `recommend()` call, model-only (no
  HTTP layer — nothing has been deployed as a service yet).
- **Data:** 1,000 users from `data.truth` for collaborative/content; all 2,000
  simulated-cold users for cold start (every call was timed, not a subsample).
- **Operationalization:** `time.perf_counter()` around each call,
  `numpy.median` / `numpy.percentile(..., 95)` over the collected list. The
  graded limit is 600ms end-to-end including HTTP + VM contention, which none
  of this measures directly.

## 1.4 Model size and memory

- **Measure:** Serialized artifact size on disk (`pickle`), and the same RSS
  delta as 1.2 (they are not independent — memory grows once, at fit time,
  and the pickle is a snapshot of what was built).
- **Data:** n/a — this is about the fitted object, not a dataset.
- **Operationalization:** `pickle.dump` to `models/<name>.pkl`,
  `os.path.getsize(...)` in bytes, converted to MB.

---

# Part 2. Summary

| | Collaborative | Content-based | Cold start |
| --- | --- | --- | --- |
| Recall@20 | 0.0999 | 0.0131 | 0.0313* |
| Precision@20 | 0.0108 | 0.0014 | 0.0033* |
| NDCG@20 | 0.0503 | 0.0074 | 0.0177* |
| Hit rate@20 | 0.1950 | 0.0282 | 0.0600* |
| Beats popularity? | essentially tied (-0.0007 recall) | no, by ~7x | no — see 3.3, popularity on the *same* 150 users scores 0.1004 recall |
| Train time | 93.3s (re-measured 9/28) | 68.4s | 2.5s (`fit()`, no LLM call yet — the LLM runs at request time) |
| p95 latency (ms) | 10.2 | 1.4 | **79,372** (that is 79 seconds, not a typo) |
| Artifact size (MB) | 133.3 | 115.6 | n/a (no serialized model — pure lookup + prompt) |
| Catalogue coverage | 2,191 films (10.5%) | 6,142 films (29.6%) | 1,265 films (6.1%) |

*Cold-start metrics are **not comparable** to the other two columns — different
protocol, a much smaller sampled user set (150, down from 2,000 — see 4.2 for
why), and these numbers are from the **real LLM path**, confirmed via
`used_llm_path: 150/150` in `results_cold_start_llm.json` (an earlier run on
the same code, before a working key was available, used the heuristic
fallback instead — see 4.2 for that comparison). Popularity is at 0.1006
recall on the full set, 0.1004 on this specific 150-user sample.

---

# Part 3. The three models

## 3.1 Collaborative filtering

**What it is:** Item-item collaborative filtering: builds a user x movie matrix
weighted by `minutes_watched`, L2-normalizes movie (item) vectors, and scores
unseen movies by cosine similarity to what the user has already watched, using
a matrix-projection trick that avoids ever materializing the full 20,784 x
20,784 item-item similarity matrix.

| Setting | Value |
| --- | --- |
| Libraries and versions | scipy 1.16.x (`sparse`), scikit-learn 1.9.1 (`normalize`), numpy 2.5.3 |
| Key hyperparameters | `min_user_interactions=2`, `min_movie_interactions=2` (no latent-factor count — item-item cosine has none) |
| What it reads | `data/v2/train.csv`: `user_id`, `movie_id`, `minutes_watched` (renamed to `rating` as the interaction weight) |
| Cold-start fallback | unseen user -> global popularity-by-training-count list |
| Command to reproduce | `python run_cf_content.py` (in `m1-team-eval/`, ported from `1try_repo/src/models/collaborative.py`) |

| Metric | Result | Popularity |
| --- | --- | --- |
| Recall@20 | 0.09996 | 0.1006 |
| Precision@20 | 0.01081 | 0.0108 |
| NDCG@20 | 0.05027 | 0.0502 |
| Hit rate@20 | 0.19500 | 0.1952 |
| Users scored | 137,694 | 137,694 |

| Cost | Value |
| --- | --- |
| Train time / peak memory | **93.3s** / **1,894.0 MB peak** (both per the team's standard: data load + fit, excl. pickling; train time re-measured 9/28, two runs 93.1s/93.5s) |
| Median / p95 latency | 5.65ms / 10.20ms |
| Artifact on disk | 133.3 MB (pickled) |
| Machine | Laptop (Windows), not the VM — per DATA_GUIDE.md, training must not run on the shared VM |

**Coverage**

| | |
| --- | --- |
| Distinct films recommended | 2,191 (5,000-user sample) |
| As % of 20,784 | 10.5% |
| Identical list for every user? | No |

**What you tried**

| Variant | Recall@20 | Verdict |
| --- | --- | --- |
| `minutes_watched` as the interaction weight (used) | 0.0999 | kept |
| `min_user`/`min_movie` = 2 (I2 defaults, unchanged) | 0.0999 | not re-swept — out of time before this meeting, flagged in 4.3 |

**Raw output**

```
{'users_scored': 137694, 'k': 20, 'relevance': 'binary',
 'precision@20': 0.010807297340474606, 'recall@20': 0.09995827382859533,
 'ndcg@20': 0.05027247506311318, 'hit_rate@20': 0.19499760338141095,
 'mean_truth_size': 2.158946649817712}
```

## 3.2 Content-based

**What it is:** TF-IDF over each film's genres (upweighted 3x), tagline and
overview text (titles deliberately excluded — they were found in I2 to make
sequels look identical via shared proper nouns). A user's profile is the
rating-weighted average of the TF-IDF vectors of films they watched; ranking
is cosine similarity to that profile, blended 85/15 with a popularity prior.

| Setting | Value |
| --- | --- |
| Libraries and versions | scikit-learn 1.9.1 (`TfidfVectorizer`), numpy 2.5.3 |
| Key hyperparameters | `max_features=4000`, `ngram_range=(1,2)`, `min_df=2`, English stopwords |
| What it reads | `data/movies.csv`: `movie_id`, `genres` (`\|`-separated, split to a list), `tagline`, `overview`. `data/v2/train.csv` for the user's rating-weighted profile |
| Cold-start fallback | unseen user -> popularity-by-training-count list |
| Command to reproduce | `python run_cf_content.py` |

| Metric | Result | Popularity |
| --- | --- | --- |
| Recall@20 | 0.01314 | 0.1006 |
| Precision@20 | 0.00144 | 0.0108 |
| NDCG@20 | 0.00739 | 0.0502 |
| Hit rate@20 | 0.02822 | 0.1952 |
| Users scored | 137,694 | 137,694 |

| Cost | Value |
| --- | --- |
| Train time / peak memory | 68.4s / **1,525.7 MB peak** (Sarah's standardized definition: data load + fit, excl. pickling) |
| Median / p95 latency | 1.09ms / 1.39ms |
| Artifact on disk | 115.6 MB (pickled — mostly the TF-IDF sparse matrix over 20,784 films) |
| Machine | Laptop (Windows) |

**Coverage**

| | |
| --- | --- |
| Distinct films recommended | 6,142 (5,000-user sample) |
| As % of 20,784 | 29.6% |
| Identical list for every user? | No |

**What you tried**

| Variant | Recall@20 | Verdict |
| --- | --- | --- |
| genres x3, titles excluded (I2 default, used) | 0.0131 | kept — no time to re-sweep the genre weight before this meeting |

**Raw output**

```
{'users_scored': 137694, 'k': 20, 'relevance': 'binary',
 'precision@20': 0.001439786773570456, 'recall@20': 0.01313988217720406,
 'ndcg@20': 0.007387649619635203, 'hit_rate@20': 0.02822199950615132,
 'mean_truth_size': 2.158946649817712}
```

## 3.3 Cold start

**What it is:** The user's free-text `likes`/`dislikes` from `data/users.csv` is
sent to an LLM to extract structured genres/titles as JSON, which then scores
every film in the catalog (genre overlap + title mentions + a small popularity
prior); the LLM optionally re-ranks a short candidate list. If no LLM key
authenticates, a deterministic regex/keyword extractor with the same JSON
schema runs instead so the function still returns something.

| Setting | Value |
| --- | --- |
| Libraries and versions | `openai` SDK (OpenAI-compatible client, also used for Gemini's OpenAI-compat endpoint) |
| Key hyperparameters | `LLM_TEMPERATURE=0.2`, up to 80 candidates offered to the re-rank step |
| What it reads | `data/users.csv`: `user_id`, `likes`, `dislikes` (renamed to `self_description_likes`/`self_description_dislikes`); `data/movies.csv` for scoring the catalog |
| Command to reproduce | `python run_cold_start.py` |

**How you evaluated it.** `metrics.py` cannot score users with no training
history, so per DATA_GUIDE.md I held out the *real* training history of a
sample of warm test users who have a non-empty self-description (sampled from
the 96,936 eligible warm users who have one), and scored them purely from
that text against the same post-cutoff ground truth `metrics.py` uses — i.e.
pretending each one is a brand-new user. Compared against the popularity list
for that *same* user sample, not the full-set baseline (a subsample shifts
the mean). Ran twice: once on 2,000 users before a working LLM key was
available (heuristic fallback only), once on 150 users with a working Gemini
key (real LLM path, confirmed via `used_llm_path: 150/150`). The sample
shrank 2,000 -> 150 for the LLM run purely because of latency, see cost row
below.

| | |
| --- | --- |
| Method | held out real history of warm users, scored from self-description text only |
| Result (real LLM, 150 users) | Recall@20 0.0313, Precision@20 0.0033, NDCG@20 0.0177, Hit rate@20 0.0600 |
| Result (heuristic fallback, 2,000 users, no working key at the time) | Recall@20 0.0149, Precision@20 0.0017, NDCG@20 0.0100, Hit rate@20 0.0315 |
| Better than giving them the popularity list? | **No, either way.** Popularity on the same 150 users: Recall@20 0.1004, Hit rate@20 0.2067 — the real LLM path roughly **doubles** recall over the heuristic fallback, but still loses to popularity by ~3.2x |

| Cost | Value |
| --- | --- |
| Train time / peak memory | `fit()` (loads catalog + user table, no LLM call yet): 2.5s / RSS delta 149.5 MB |
| Median / p95 latency, heuristic | 438.1ms / 590.1ms — model-only, no HTTP. Already close to the 600ms end-to-end limit |
| Median / p95 latency, **real LLM** | **66,301ms / 79,372ms — that is 66 to 79 *seconds* per recommendation**, not milliseconds. Two sequential LLM calls per request (extract, then re-rank), plus retry/backoff on rate limits. This is roughly **130x over the 600ms budget** and is the actual finding here, not the accuracy numbers |
| Artifact on disk | n/a — no serialized model, this is a lookup + scoring function, not a fitted object |
| Machine | Laptop (Windows) |

**Coverage**

| | |
| --- | --- |
| Distinct films across unknown users | Heuristic: 4,398 of 2,000 sampled (21.2%). Real LLM: 1,265 of 150 sampled (6.1%) |
| Identical list for every unknown user? | No, either run — not the popularity-baseline-with-extra-steps failure mode, just a less accurate (and, with a real LLM, far too slow) one |

**What you tried**

| Variant | Result | Verdict |
| --- | --- | --- |
| LLM path, `OPENAI_API_KEY` env var present (not a key I generated) | 0/2,000 calls succeeded — `AuthenticationError` on every call | not usable |
| Heuristic fallback (regex/keyword genre extraction, same JSON schema) | Recall@20 0.0149 on 2,000 users | works, but the point of this block is the LLM path |
| LLM path, working `GEMINI_API_KEY` | Recall@20 0.0313 on 150 users, **p95 latency 79.4s** | accuracy roughly doubles over heuristic; latency makes this undeployable as-is, see 4.2 |

---

# Part 4. Your verdict

## 4.1 Which of your three is strongest, and why

Collaborative filtering. It is essentially tied with the popularity baseline on
every metric (within about 1% relative on recall) while still being genuinely
personalized — 10.5% catalog coverage and no two users get an identical list —
and its p95 latency (10ms) leaves enormous headroom under the 600ms budget. It
is also, as far as I can tell from the team's shared numbers, the best
personalized result reported so far: Balkan's ALS sweep never beat 0.0863
recall. Content-based is a legitimate second, structurally different
candidate for the required 4-dimension comparison, but its accuracy (about
1/7th of the popularity baseline) rules it out for deployment on its own.

## 4.2 Honest caveats

- **The real LLM path now runs (a working `GEMINI_API_KEY` was obtained after
  the first version of this report), and it is a much bigger problem than the
  earlier "no key" caveat.** Accuracy roughly doubles over the heuristic
  fallback (Recall@20 0.0313 vs 0.0149), but p95 latency is **79 seconds per
  request** — two sequential LLM calls (extract, then re-rank) plus
  rate-limit backoff, against a 600ms budget. This is not a "needs a key"
  problem anymore, it is a "needs a completely different request-time
  architecture" problem: precompute the extraction at signup instead of
  per-request, cut the second (re-rank) LLM call, and/or cache aggressively.
  As shipped today, this cannot go into the 600ms endpoint at all.
- Sample size dropped from 2,000 users (heuristic) to 150 (real LLM) purely
  because of that latency — 2,000 real Gemini calls at ~70s each was not
  practical to run before this report. 150 is small enough that the LLM
  recall number (0.0313) should be treated as a rough estimate, not a
  precise one.
- **Both `.pkl` artifacts are >100MB** (133.3 MB and 115.6 MB) — over GitHub's
  hard limit, consistent with DATA_GUIDE.md's warning to gitignore `models/`.
  Neither has been committed.
- **Both `.pkl` artifacts are >100MB** (133.3 MB and 115.6 MB) — over GitHub's
  hard limit, consistent with DATA_GUIDE.md's warning to gitignore `models/`.
  Neither has been committed.
- I scored the **full 137,694-user set** for collaborative and content-based
  (not a dev sample), per the "report on the full user set" instruction. Cold
  start used a 150-user (real LLM) / 2,000-user (heuristic) sample of *only*
  users with a non-empty self-description — the other ~30% of users.csv, and
  the un-sampled remainder of the 96,936 eligible users, are untested.
- I did not get to re-sweep any hyperparameters (CF's min-interaction
  thresholds, content's genre weighting) before this meeting — both models
  are running I2's original defaults unchanged.
- Peak memory was originally reported as a before/after RSS delta, which
  understates true peak. Updated to a proper running-max measurement (sampled
  every 20ms across data load + fit) once the team standardized the
  definition — see 1.2 and Part 3.1/3.2.
- **Training time for collaborative filtering was re-measured on
  2026-09-28** per Balkan's request (data load through end of fit, excl.
  pickling), and came out to **~93s** (two runs: 93.1s, 93.5s) — noticeably
  slower than the 53.6s first reported. The original 53.6s only timed
  `.fit()` itself, not data loading (which was done once, shared, before the
  timer started) — it undercounted relative to the team's standard, which is
  why this needed a redo. The gap isn't fully explained by that alone (data
  loading itself is only ~1.8s), so some of it may be this laptop being
  slower now than when the original number was measured days earlier; either
  way, 93s is the number that follows the agreed definition and is what's
  reported in 1.2, 3.1 and the summary table.

## 4.3 What you would build next

Redesign cold start around a 79-second-per-request LLM call being unusable
at request time: run the extraction step once at signup (or on a schedule)
and cache the structured preferences, so the `/recommend` path only does the
cheap catalog-scoring step, not a live LLM call. Drop the second (re-rank)
LLM call entirely — it roughly doubles latency for a step that `score_catalog`
already does reasonably on its own. Also vectorize `score_catalog` itself
(currently a per-film Python loop over 20,784 rows), and re-score on the
full 150+ user sample once the above lands, since 150 users is too few to
trust the recall number precisely.

---

# Appendix: what has been measured already

Balkan's ALS on the **v2** snapshot, 20,000-user sample. Context only.

| Factors | Recall@20 | Train time | Artifact |
| --- | --- | --- | --- |
| Popularity | **0.1006** | n/a | n/a |
| 4 | 0.0863 | 7s | 52.6 MB |
| 8 | 0.0769 | 8s | 57.5 MB |
| 16 | 0.0673 | 10s | 67.4 MB |
| 32 | 0.0556 | 17s | 87.1 MB |

The same sweep on v1, for reference: popularity 0.0978, then 0.0724, 0.0654,
0.0572, 0.0494, and 0.0438 at 64 factors.

Two things to take from this:

**Recall rises as ALS capacity falls, and the limit of that trend is popularity
itself.** Beating popularity on this data is hard. Losing to it by a little is a
normal result rather than a failure, and reporting it honestly is worth more
than tuning until the number wins.

**Tripling the data did not change the shape.** Every configuration improved by
roughly 0.012 to 0.014 recall, and fewer factors is still better. So more data
alone will not fix a model that is not finding personalized signal.

A co-occurrence check gives a median lift of 1.28 over chance, so collaborative
signal exists but is weak. This has not been confirmed with a second algorithm,
which is the open question on this approach.

**Known caveat in these numbers.** `data/movies.csv` was a broken symlink during
these runs, so `recommend_als.py` silently fell back to estimating film runtime
from watch minutes instead of reading real runtimes. The effect is unmeasured.
