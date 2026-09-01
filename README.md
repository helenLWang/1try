# Machine Learning in Production — I1: LLM features for Zulip

Repository for Canvas submission: `https://github.com/cmu-seai/f26-zulip-lew2`

This is the course Zulip tree (`mlip-cmu/zulip-template`) plus two LLM-backed product features:

1. **Unread recap** — a dedicated page that summarizes a user's unread messages and links back to the originals.
2. **Topic title improver** — after you send a channel message, the server checks whether the topic has drifted and can suggest a better title.

The LLM calls go through **LiteLLM**, which is already a Zulip dependency, so you can switch providers without changing application code. API keys are never committed.

## 1. Get an LLM API key

Any LiteLLM-supported chat model works (OpenAI, Groq, OpenRouter, Azure, etc.). A few dollars of credit is enough.

Create a file named `api.key` in the **repository root** containing only the key:

```text
sk-...your-key...
```

`api.key` is gitignored. **Do not commit it.**

Optional environment variables (these override the file):

| Variable | Purpose |
| --- | --- |
| `LLM_API_KEY` or `OPENAI_API_KEY` | Secret |
| `LLM_MODEL` | Model id (default: Zulip's `TOPIC_SUMMARIZATION_MODEL`, e.g. Groq Llama, or `gpt-4o-mini`) |
| `LLM_API_BASE` | Base URL for OpenAI-compatible providers, e.g. `https://openrouter.ai/api/v1` |

You can instead put `topic_summarization_api_key = ...` in `zproject/dev-secrets.conf` (also gitignored).

## 2. Install and run Zulip (Vagrant — required by the course)

Follow Zulip's documented development setup: https://zulip.readthedocs.io/en/latest/development/setup-recommended.html

From a clone of **this** repository:

```bash
vagrant up
vagrant ssh
cd /srv/zulip
./tools/run-dev
```

The web app is at http://localhost:9991. Log in as `hamlet@zulip.com` / `abcd1234`.

Restart `./tools/run-dev` after backend changes. Reload the browser after frontend changes.

## 3. Check the APIs

```bash
API_KEY=$(curl -s -X POST 'http://localhost:9991/api/v1/dev_fetch_api_key' \
  --data-urlencode 'username=hamlet@zulip.com' | python3 -c "import sys,json; print(json.load(sys.stdin)['api_key'])")

curl -s -X GET 'http://localhost:9991/api/v1/messages/recap' -u :"$API_KEY"

curl -s -X POST 'http://localhost:9991/api/v1/messages/topic_title_suggest' \
  -u :"$API_KEY" \
  --data-urlencode 'stream_id=1' \
  --data-urlencode 'topic=Weekend plans'
```

## 4. Using the features in the UI

**Unread recap.** Left sidebar → **Unread recap**. Follow **Jump to message** links (`#narrow/channel/<id>-<name>/topic/<topic>/near/<message_id>`).

**Topic title improver.** Send a few channel messages that wander off the title (e.g. title `Weekend plans`, then talk about a database migration). A compose banner offers **Rename topic**.

## 5. Tests

Inside the Vagrant VM:

```bash
cd /srv/zulip
./tools/test-backend zerver.tests.test_llm_features
```

The tests mock LiteLLM; they do not need a live API key.

## 6. Canvas submission

Submit the commit URL:

`https://github.com/cmu-seai/f26-zulip-lew2/commit/<full-commit-sha>`

Record a short UI demo (both features, or one video) and paste the link into `implementation.md`.

## 7. What was added

| Area | Path |
| --- | --- |
| LLM helper (LiteLLM) | `zerver/lib/llm_client.py` |
| Recap backend | `zerver/lib/message_recap.py`, `zerver/views/llm_features.py` |
| Title improver | `zerver/lib/topic_title_improver.py` |
| Routes | `GET /messages/recap`, `POST /messages/topic_title_suggest` |
| Recap UI | `web/src/message_recap.ts`, overlay templates, left-sidebar view |
| Title UI | `web/src/topic_title_improver.ts`, compose banner, `web/src/compose.ts` |
| Tests | `zerver/tests/test_llm_features.py` |
| Design write-up | `implementation.md` |
