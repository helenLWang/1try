# I3 — Risks and mitigations (ChildFind dashcam search)

Individual assignment 3 for 17-445/17-645/17-745. Hazard analysis of a dashcam feature that searches recordings for missing children, plus LLM tooling for stakeholders → losses/REQs → ASM/SPEC.

## What to read in which order

| File | What it is |
| --- | --- |
| `goals.md` | Layered goals + 3-step measures |
| `analysis_results.md` | Full report (12 stakeholders, 64 losses/REQs, ASM/SPEC) |
| `key_results.md` | Four curated results (human-selected) |
| `fault_tree.md` | FTA for R-S02-1 and two system-level mitigations |
| `figures/` | SVG fault trees |
| `office_hours_notes.md` | Notes for the grading conversation |
| `workspace/` | Human-reviewed JSON checkpoints the report was rendered from |

## Setup

Python 3.10+ (stdlib plus optional `python-dotenv`).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**API keys — do not commit them.** Copy `.env.example` to `.env` and fill one provider:

```bash
cp .env.example .env
# edit .env
```

Alternatively export variables in the shell, or put a single key in `api.key` (gitignored) and `export OPENAI_API_KEY=$(cat api.key)`.

Supported `LLM_PROVIDER` values:

- `openai` (default) — OpenAI, Azure OpenAI, OpenRouter, Groq, or any OpenAI-compatible `/v1/chat/completions` endpoint via `OPENAI_BASE_URL`
- `anthropic` — `ANTHROPIC_API_KEY`
- `gemini` — `GEMINI_API_KEY`

The committed `analysis_results.md` does **not** require a key. It is rendered from the reviewed JSON in `workspace/`:

```bash
python3 -m hazard_tool seed     # rewrite workspace JSON + analysis_results.md from the reviewed catalog
python3 -m hazard_tool report   # re-render markdown from whatever is currently in workspace/
python3 -m hazard_tool status
```

## Human-in-the-loop LLM pipeline (steps 2–4)

Do not run this as one shot the first time. Each step writes a JSON file with `"approved": false`. You edit the file (delete hallucinations, rewrite REQs that mention models, add missing indirect stakeholders), then approve.

```bash
# 2. Stakeholders
python3 -m hazard_tool stakeholders
# open workspace/stakeholders.json, edit the list
python3 -m hazard_tool approve stakeholders.json

# 3. Values, goals, losses, world-level REQs
python3 -m hazard_tool hazards
# open workspace/hazards.json — rewrite any REQ that is not world-only
python3 -m hazard_tool approve hazards.json

# 4. ASM / SPEC per requirement
python3 -m hazard_tool requirements
# open workspace/requirements.json — ASM = world/shared, SPEC = interface only
python3 -m hazard_tool approve requirements.json

# Candidate ranking for humans (not the four key results)
python3 -m hazard_tool prioritize

# Render
python3 -m hazard_tool report
```

`python3 -m hazard_tool run-all` exists for a first draft. It auto-approves intermediate files so the next LLM call can proceed; you are still expected to edit the JSON and re-run `report`. The four items in `key_results.md` must be chosen by a human.

### Filtering / prioritizing

- **Manual filter:** delete items from `hazards.json` before approving (recommended). That is how generic "model inaccurate" rows were removed for this submission.
- **LLM ranker:** `prioritize` scores severity × plausibility × easy-to-miss and flags surprising assumption failures. Use it as a shortlist, not as the answer. See `key_results.md` for the actual selection rule.

## Regenerating the fault-tree figures

```bash
python3 scripts/make_fault_trees.py
```

## Secrets

`.env`, `api.key`, and `*.pem` are gitignored. If you paste a key into a prompt file, delete it before committing.

## Canvas submission (you must do this part)

1. In the course Slack: `/create-repo I3 helenLWang` (use your GitHub username).
2. Push this tree to the private `cmu-seai/...` repo that command creates.
3. Submit `https://github.com/cmu-seai/<repo>/commit/<full-commit-sha>` on Canvas.
