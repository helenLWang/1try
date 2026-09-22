# Le Wang (lew2)'s M1 Candidate Model

Give this to teammates tomorrow. **This is my individual submission**,
not the team's final Milestone 1.

Two other teammates will each bring a different approach. We'll compare
all four numbers together and pick one to deploy.

## What this is

Name: **item–item CF + LLM cold-start**

Returning users: people who watched A also watched what? (collaborative
filtering).
New users with no history: read the likes/dislikes they wrote at
signup, extract structured JSON with Gemini, then score against the
real movie list.
Neither case: fall back to popular movies.

Code entry point (this is all teammates need to call):

```text
python -m src.m1_recommend 9375
```

Prints one line, no spaces, no JSON, up to 20 movie IDs separated by
commas. This is exactly the format the assignment expects for
`http://<machine>:8082/recommend/<userid>`.

Implementation: `src/m1_recommend.py`
Local test server: `python -m src.m1_server`, then
`curl http://127.0.0.1:8082/recommend/9375`

## Repo

https://github.com/cmu-seai/f26-model-lew2

Or this branch: https://github.com/helenLWang/1try/tree/cursor/i2-recommendation-model-f5a6

Key files:

- `src/models/collaborative.py` — collaborative filtering
- `src/models/cold_start.py` — new-user LLM path
- `src/evaluate.py` — how accuracy is measured
- `src/m1_recommend.py` — the team-facing entry point
- `evaluation.md` / `model.md` — assignment write-up

## The four numbers (for the comparison table)

Measured on the same dataset (~5e6 Kafka records, time-based split, 400
test users).

Accuracy (HitRate@20): **0.095**
Accuracy (NDCG@20): **0.035**
New-user HitRate@20 (self-description only): **0.05**

Training time: one `python -m src.train` run takes about **35.4
seconds** (`elapsed_s` in `artifacts/train_log.json`)

Inference time: 400 users took 0.12 seconds total in evaluation, about
**0.3 ms/user** on average. The assignment limit is 600 ms, so this is
well within budget.

Model file size: `artifacts/models/recommenders.joblib` is not
committed (over 5MB, can't go into git). After a teammate trains it
locally, run:

```text
python -m src.m1_measure
```

This writes `artifacts/m1_lew2_measures.json`, which includes the file
size in bytes.

I recommend the team deploy this one — not my content/TF-IDF variant,
which only scored 0.010 HitRate.

## How teammates run it

Needs the course VPN / Kafka tunnel, same as I2.

```text
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./scripts/start_kafka_tunnel.sh
python -m src.collect --max-events 5000000 --windows 12
python -m src.train
python -m src.m1_recommend 9375
```

Put the LLM key in `api.key` at the repo root — do not commit it.
Without a key, new users fall back to a simple rule-based path; the
output format is unchanged.

## Wiring it into the team's Flask app

```python
from src.m1_recommend import recommend_line

@app.get("/recommend/<int:user_id>")
def rec(user_id):
    return recommend_line(user_id)
```

For new users to keep working: the service checks whether the user is
in the CF matrix, and falls back to cold-start if not. Later, the team
should pull newly registered users' self-descriptions from
`http://128.2.220.123:8080/user/<id>` into `users.jsonl`, or pass the
likes text directly to `cold.recommend(..., likes=..., dislikes=...)`.

## Short message for the team chat (copy-paste)

My candidate for tomorrow is item-item CF, with new users routed to an
LLM. Call `python -m src.m1_recommend <userid>` — it returns one line of
movie IDs. HitRate@20 is 0.095, training takes about 35 seconds, and a
single recommendation takes about 0.3ms. Code is in the course repo
`f26-model-lew2`, entry point `src/m1_recommend.py`. My content-based
model isn't in the running — it was too weak.
