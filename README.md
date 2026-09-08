# I2: Learning a Recommendation Model

Individual Assignment 2 for 17-445/17-645/17-745 (Machine Learning in Production).
This repository collects the course Kafka `movielog1` stream plus the movie/user
metadata API, trains **two different recommenders**, and uses an **LLM** to
recommend movies for **cold-start** users from their signup self-description.

## What you get

| Approach | Idea | Code |
| --- | --- | --- |
| Collaborative filtering | Item–item cosine on the user–movie matrix | `src/models/collaborative.py` |
| Content-based filtering | TF-IDF over genres/tagline/overview | `src/models/content.py` |
| Cold-start (LLM) | Parse likes/dislikes with an LLM, then score the catalog | `src/models/cold_start.py` |
| Popularity (baseline only) | Rank by `count × mean score` | `src/models/popularity.py` |

`recommend(user_id)` returns up to 20 movie IDs. This assignment does **not**
deploy an HTTP service.

## Prerequisites

- Python 3.10+
- Access to the course server `128.2.220.123` (CMU network or CMU VPN)
- An SSH client for the Kafka tunnel
- An OpenAI **or Gemini** API key to run the LLM cold-start path (I1 allows
  both; course staff should use their own key). Collaborative/content
  training does not need a key.

### Kafka tunnel

You cannot usefully open `128.2.220.123:9092` directly. Kafka advertises
`localhost:9092`, so forward it:

```bash
./scripts/start_kafka_tunnel.sh
# equivalent: ssh -L 9092:localhost:9092 tunnel@128.2.220.123 -NT
```

Leave that process running. Account `tunnel`; password / SSH key are on
**Canvas** — do not commit them. Metadata API:
`http://128.2.220.123:8080/movie/<id>` and `/user/<id>`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x scripts/start_kafka_tunnel.sh
```

LLM key (gitignored). OpenAI and Google Gemini both work (same as I1):

```bash
echo 'YOUR_KEY' > api.key
# OpenAI:
#   export OPENAI_API_KEY='sk-...'
# Gemini (key usually starts with AIza or AQ.; auto-detected, uses native Gemini API):
#   export GEMINI_API_KEY='AQ....'
#   # or: echo 'AQ....' > api.key
# OpenRouter / Groq / Azure-compatible:
export LLM_BASE_URL='https://openrouter.ai/api/v1'
export LLM_MODEL='gpt-4o-mini'
```

## 1. Collect data

```bash
# Homework-scale: ~5M log lines from 12 slices across the retained log + API
python -m src.collect --max-events 5000000 --windows 12

# Small-batch smoke test (tail only)
python -m src.collect --max-events 20000 --windows 1
```

Writes (gitignored except tiny samples and `collection_meta.json`):

- `data/ratings.csv`, `data/watches.csv`
- `data/movies.jsonl`, `data/users.jsonl`
- `data/collection_meta.json` — offsets, event counts, timestamps
- `data/sample/` — a few dozen rows for offline inspection

Topic defaults to `movielog1` (`KAFKA_TOPIC=movielogN` later).

## 2. Train

```bash
python -m src.train
```

Fits both personalized models on a per-user chronological train split.
Writes `artifacts/models/recommenders.joblib` (gitignored, can exceed 5 MB)
and `artifacts/train_log.json` (hyperparameters). Optional:
`python -m src.train --full-data`.

## 3. Evaluate

```bash
python -m src.evaluate --max-users 400 --cold-start-users 40
```

`--max-users 0` scores every test user. Omit `--no-llm` when `api.key` is
present so cold-start calls the LLM. `--no-llm` uses the schema-compatible
heuristic extractor (same catalog scorer). Metrics: `artifacts/metrics.json`.
Definitions: `evaluation.md`.

## 4. Recommend

```bash
python -m src.recommend --user-id 9375 --model collaborative
python -m src.recommend --user-id 9375 --model content
python -m src.recommend --user-id 9375 --model coldstart
python -m src.recommend --user-id 9375 --model auto
```

`auto` uses item–item CF when the user is in the interaction matrix,
otherwise cold-start.

```bash
python -m src.recommend --user-id 0 --model coldstart \
  --likes "I like dry crime comedies and Star Wars" \
  --dislikes "No horror"
```

Prints JSON plus a comma-separated id list.

## Offline tests (no Kafka)

```bash
python -m pytest tests/test_offline.py -q
```

## Repository layout

```
src/collect.py              Kafka + API collection
src/parse.py                movielog line parser
src/api.py                  batched metadata client (≤200 ids)
src/dataset.py              implicit/explicit merge + time split
src/models/collaborative.py item–item CF
src/models/content.py       TF-IDF (genres / overview)
src/models/cold_start.py    LLM extract + catalog scorer
src/train.py / evaluate.py / recommend.py
scripts/start_kafka_tunnel.sh
model.md                    data + modeling write-up
evaluation.md               metrics and numbers
```

## Design choices

- **Why item–item CF and TF-IDF?** Standard, CPU-friendly, and *actually
  different* (behavior vs. metadata). Two CF runs with different `k` would
  not satisfy the assignment. Item–item cosine fits this sparse Kafka window
  better than a 50-factor SVD.
- **Why mix watches with ratings?** Explicit ratings are sparse. Watch
  progress is a reasonable implicit like; we drop `< 3` minutes.
- **Why not deploy?** Out of scope for I2.
- **Secrets and large files:** `api.key`, Kafka credentials, CSV dumps, and
  pickled models are gitignored.

## Hyperparameters

All knobs live in `src/config.py` (`RANDOM_SEED = 42`, TF-IDF 4000 features,
`TOP_K = 20`, CF min 2 interactions, …). Copied into
`artifacts/train_log.json` on every train run.
