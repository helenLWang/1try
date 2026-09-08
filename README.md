# I2: Learning a Recommendation Model

Individual Assignment 2 for 17-445/17-645/17-745 (Machine Learning in Production).
This repository collects the course Kafka `movielog1` stream plus the movie/user
metadata API, trains **two different recommenders**, and uses an **LLM** to
recommend movies for **cold-start** users from their signup self-description.

## What you get

| Approach | Idea | Code |
| --- | --- | --- |
| Collaborative filtering | Item–item cosine on the user–movie matrix | `src/models/collaborative.py` |
| Content-based filtering | TF-IDF over title/genres/overview; user = weighted average | `src/models/content.py` |
| Cold-start (LLM) | Parse likes/dislikes with an LLM, then score the catalog | `src/models/cold_start.py` |
| Popularity (baseline only) | Rank by `count × mean score` | `src/models/popularity.py` |

`recommend(user_id)` returns up to 20 movie IDs. We **do not** deploy an HTTP
service in this assignment.

## Prerequisites

- Python 3.10+
- Access to the course server `128.2.220.123` (on the **CMU network**, or
  **CMU VPN** from off campus)
- An SSH client (for the Kafka tunnel)
- An OpenAI-compatible API key for the LLM cold-start path (optional for
  collaborative/content training; required to exercise the real LLM)

### Campus network / VPN

You **do** need to be on campus or on the CMU VPN to reach Kafka and the
metadata API from a laptop. The collector talks to:

- Kafka via an SSH tunnel to `tunnel@128.2.220.123` (local `9092`)
- Metadata at `http://128.2.220.123:8080/movie/<id>` and `/user/<id>`

You cannot usefully open `128.2.220.123:9092` directly: Kafka advertises
`localhost:9092`, which is why the assignment requires

```bash
ssh -L 9092:localhost:9092 tunnel@128.2.220.123 -NT
```

The tunnel account is `tunnel`. Use the password from Canvas (`mlip-kafka` in
the published instructions) or the course SSH key. **Do not commit the
password, the key, or `api.key`.**

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x scripts/start_kafka_tunnel.sh
```

LLM key (pick one):

```bash
echo 'sk-...' > api.key          # gitignored
# or
export OPENAI_API_KEY='sk-...'
# OpenRouter / Groq / Azure-compatible:
export LLM_BASE_URL='https://openrouter.ai/api/v1'
export LLM_MODEL='gpt-4o-mini'
```

## 1. Start the Kafka tunnel

In a **separate terminal**, leave this running:

```bash
./scripts/start_kafka_tunnel.sh
```

Sanity check (if you have `kcat`): `kcat -b localhost -L`

## 2. Collect data

```bash
# Full homework-scale pull (several minutes): ~5M log lines from 12 slices
# spaced across the retained Kafka log, plus API metadata
python -m src.collect --max-events 5000000 --windows 12

# Small-batch laptop / CI smoke test (tail only)
python -m src.collect --max-events 20000 --windows 1
```

This writes (gitignored except tiny samples):

- `data/ratings.csv` — explicit 1–10 ratings
- `data/watches.csv` — aggregated watch progress per `(user, movie)`
- `data/movies.jsonl`, `data/users.jsonl` — metadata API
- `data/collection_meta.json` — how much was read, from which offsets
- `data/sample/` — a few dozen rows so parsers can be tested offline

Use `movielog1` until your team topic exists (`KAFKA_TOPIC=movielogN`).

## 3. Train

```bash
python -m src.train
```

Fits both personalized models on a **per-user chronological train split**
(last 20% of each user's interactions held out). Writes:

- `artifacts/models/recommenders.joblib` (gitignored, can exceed 5 MB)
- `artifacts/train_log.json` — every hyperparameter and data size

Train on all rows only if you want a “production” pickle:

```bash
python -m src.train --full-data
```

## 4. Evaluate

```bash
python -m src.evaluate --max-users 400 --cold-start-users 40
```

`--max-users 0` scores every test user (slower). `--no-llm` forces the
schema-compatible heuristic extractor (no API spend). With `api.key` present
the cold-start path calls the LLM.

Metrics land in `artifacts/metrics.json`. How they are defined is in
`evaluation.md`.

## 5. Recommend

```bash
python -m src.recommend --user-id 2 --model collaborative
python -m src.recommend --user-id 2 --model content
python -m src.recommend --user-id 2 --model coldstart
python -m src.recommend --user-id 2 --model auto
```

`auto` uses item–item CF when the user is in the interaction matrix, otherwise cold-start.

Override text for a brand-new user:

```bash
python -m src.recommend --user-id 0 --model coldstart \
  --likes "I like dry crime comedies and Star Wars" \
  --dislikes "No horror"
```

Prints JSON plus a comma-separated id list (the format the later team API will
need).

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
src/models/collaborative.py SVD
src/models/content.py       TF-IDF
src/models/cold_start.py    LLM extract + catalog scorer
src/train.py / evaluate.py / recommend.py
scripts/start_kafka_tunnel.sh
model.md                    data + modeling write-up
evaluation.md               metrics and numbers
```

## Design choices (short)

- **Why item–item CF and TF-IDF?** They are standard, CPU-friendly, and *actually
  different* (behavior vs. metadata). Two CF runs with different `k` would
  not satisfy the assignment. Item–item cosine fits this sparse Kafka window
  better than a 50-factor SVD.
- **Why mix watches with ratings?** Explicit ratings are sparse in this stream.
  Watch progress is a reasonable implicit like; we drop `< 3` minutes.
- **Why not deploy?** Out of scope for I2. The `recommend` CLI is the hook
  the team project can wrap in Flask later.
- **Secrets and large files:** `api.key`, Kafka credentials, CSV dumps, and
  pickled models are gitignored. Do not force-add them.

## Hyperparameters

All knobs live in `src/config.py` (`RANDOM_SEED = 42`, SVD components = 50,
TF-IDF 4000 features, `TOP_K = 20`, …). They are copied into
`artifacts/train_log.json` on every train run.
