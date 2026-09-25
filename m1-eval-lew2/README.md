# M1 evaluation — lew2

My candidate for the team's Milestone 1 model comparison. Results are in
[`EVALUATION_lew2.md`](./EVALUATION_lew2.md) — that's the file to read.

Ported from `../src/models/` (the I2 codebase on this branch) onto the
team's shared `v2` snapshot, scored with the team's shared `metrics.py`
(unchanged) against `baseline_popularity.json` per `DATA_GUIDE.md`.

## Reproduce

Needs the `v2` snapshot (`data/movies.csv`, `data/users.csv`, `data/v2/*.csv`)
downloaded per `DATA_GUIDE.md` — not committed here, gitignored, ~330MB.

```bash
python run_cf_content.py   # collaborative + content-based, full 137,694-user set
python run_cold_start.py   # cold start, 2,000-user simulated-cold sample
```

Raw output: `results_cf_content.json`, `results_cold_start.json`.
