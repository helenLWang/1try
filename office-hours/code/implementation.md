# Implementation notes (I1)

This assignment adds two LLM features to the course Zulip tree (`mlip-cmu/zulip-template`). Each section stays within the 500-word limit.

## Feature 1: Unread message recap

**Backend.** `GET /api/v1/messages/recap` (`zerver/views/llm_features.py`) authenticates like every other Zulip REST endpoint, then calls `generate_unread_recap` in `zerver/lib/message_recap.py`.

Unread rows come from `UserMessage` with `UserMessage.where_unread()`, newest 80 messages only. That cap keeps prompt size (and cost) bounded. Each message is formatted as `[id=<message_id>] (#channel > topic) Sender: content` so the model can cite real IDs instead of inventing URLs.

The LLM is asked for JSON `{overview, sections: [{title, summary, message_ids}]}`. After the response, the server **does not trust model-built links**. For every cited `message_id` that is actually unread, it builds a permalink with Zulip's encoder (`zerver/lib/url_encoding.py`):

- Channel: `#narrow/channel/<stream_id>-<stream_name>/topic/<topic>/near/<message_id>`
- Direct message: `#narrow/dm/<user-slug>/near/<message_id>`

That is the same fragment the web app uses (`web/src/hash_util.ts`). If the model returns non-JSON, a fallback still lists conversations and attaches those permalinks.

Secrets are read by `zerver/lib/llm_client.py` from `LLM_API_KEY` / `api.key` / `topic_summarization_api_key`. Calls go through **LiteLLM** (`litellm.completion`, pinned in `pyproject.toml`).

**Frontend.** A left-sidebar view `recap` (`web/src/navigation_views.ts`) hashes to `#recap`. `web/src/hashchange.ts` opens `web/src/message_recap.ts`, which `GET`s `/json/messages/recap` and renders `web/templates/message_recap_body.hbs`. **Jump to message** follows the fragment so the main view narrows to that message.

## Feature 2: Topic title improver

**Backend.** `POST /api/v1/messages/topic_title_suggest` takes `stream_id` and `topic`. `suggest_topic_title` in `zerver/lib/topic_title_improver.py` loads at most the last 20 messages in that topic.

Latency, cost, and scalability:

- **Skip the LLM when possible.** Fewer than 3 messages, or a title whose tokens still appear in recent bodies, return `skipped_llm: true`. Generic titles (`hi`, `question`, …) always call the model when a key is configured.
- **Small prompts.** 20 messages × ~280 characters, `max_tokens=180`, temperature 0.1.
- **Cache.** Keyed by `(stream_id, last_message_id, topic)` for 45 seconds so retries are not double-billed.
- **Sender-only.** The frontend calls the endpoint after *that user* sends. No fan-out to subscribers, no extra Tornado event. At large scale this would still need a worker and a monthly budget (Zulip already tracks `ai_credit_usage::day`); this assignment uses the cheap synchronous path.
- **Failure isolation.** Parse/API errors return `drifted: false` rather than blocking compose.

**Frontend.** `web/src/compose.ts` `send_message_success` calls `topic_title_improver.check_after_send` immediately after a channel send, while the author still has context. A compose banner offers **Rename topic**, which reuses `message_edit.move_topic_containing_message_to_stream(..., propagate_mode="change_all")`.

## Risks, UI, and production gaps

The recap can hallucinate; every claim is paired with a jump link. A title rename is a realm-visible edit, so we require an explicit click and never auto-rename. Prompt injection is possible; production would sandbox the prompt and rate-limit. Unread bodies leave the server for a third-party LLM. At scale, recap should be async and title checks should be queued.

## Demo video

Both recordings are from the **running Zulip UI** (`./tools/run-dev` at http://localhost:9991), logged in as Hamlet. Files are in this repository (private classroom repo; graders already have access):

1. **Unread recap:** [docs/demo/unread_recap.mp4](docs/demo/unread_recap.mp4)  
   Left sidebar **Unread recap** → overlay with grouped unreads and **Jump to message** → `#Denmark > Release Friday`.
2. **Topic title improver:** [docs/demo/topic_title_improver.mp4](docs/demo/topic_title_improver.mp4)  
   Topic `question`, three off-title messages, compose banner **Rename topic**.

Same files on GitHub after this commit is on `main`:

- https://github.com/cmu-seai/f26-zulip-lew2/blob/main/docs/demo/unread_recap.mp4
- https://github.com/cmu-seai/f26-zulip-lew2/blob/main/docs/demo/topic_title_improver.mp4
