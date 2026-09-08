# Model description

This assignment builds movie recommenders from a live Kafka watch/rate log and
the course metadata API. Code pointers are relative to the repository root.

## Data we collect

`python -m src.collect` reads topic `movielog1` through the SSH tunnel
(`localhost:9092`). By default it consumes about 5 million **recent** messages
rather than the full retained log (hundreds of millions of lines). That is
enough ratings and watch pairs for a laptop SVD, and it matches how a
production job would train on a sliding window. Offsets, event counts, and
timestamps are written to `data/collection_meta.json`.

We parse three record types in `src/parse.py`:

- watch: `GET /data/m/<movie_id>/<minute>.mpg` — one line per minute streamed
- rate: `GET /rate/<movie_id>=<rating>` with ratings outside 1–10 dropped
- `GET /create_account` — kept only so those user ids are fetched

Watches are **aggregated** in memory to one row per `(user_id, movie_id)`
(`max_minute`, event count, first/last timestamp). We never store a CSV of
every minute. Unique ids are then batched (≤200) against
`http://128.2.220.123:8080/movie/...` and `/user/...` (`src/api.py`). Movie
records keep title, genres, overview, tagline, runtime, language, imdb id.
User records keep age/occupation/gender plus `self_description_likes` /
`self_description_dislikes`.

**Cleaning / representation** (`src/dataset.py`): if the user rated a movie,
that 1–10 score is the label. Otherwise a watch of at least 3 minutes becomes
an implicit score `5 + 4 * min(max_minute / runtime, 1)` (runtime defaults to
90). Shorter watches are treated as accidental clicks. Duplicate ratings keep
the last timestamp. The learning matrix is this merged `interactions` table,
not raw Kafka lines.

## Approach 1: collaborative filtering (Truncated SVD)

`src/models/collaborative.py`. We keep users/movies with ≥5 interactions,
build a sparse user × movie matrix, subtract a bias model (global mean + user
mean + item mean), and factorize the **residuals** with sklearn
`TruncatedSVD` (50 components, seed 42). A recommendation is the reconstructed
score vector with already-seen movies masked, top 20. Users who never appear
in the factorized matrix fall back to popularity inside this class; the CLI
`auto` mode sends them to the LLM cold-start instead.

We chose SVD because it is the standard collaborative baseline for explicit
plus implicit scores, trains in seconds on CPU, and uses **only** who
interacted with what. It cannot recommend a movie nobody in the window has
touched, and it fails for brand-new users — that is the cold-start hole.

## Approach 2: content-based TF-IDF

`src/models/content.py`. Each movie is a document: title, genres (repeated so
they outweigh plot words), tagline, overview, language. A `TfidfVectorizer`
(4000 features, 1–2 grams, English stops) yields L2-normalized vectors. A
user profile is the rating-weighted average of movies they already consumed.
We rank by cosine similarity and again mask seen ids.

This is substantively different from SVD: two users with disjoint histories
can still get similar lists if they watched the same genres, and a long-tail
title with a rich overview can surface even with little collaborative support.
It cannot pick up “people like you also liked X” when X is unlike the user’s
text profile.

## Cold-start with an LLM

`src/models/cold_start.py`. New users often typed what they like and dislike
at signup. We prompt an OpenAI-compatible chat model (`gpt-4o-mini` by
default; override with `LLM_MODEL` / `LLM_BASE_URL`) to emit JSON:
`liked_genres`, `disliked_genres`, `liked_titles`, `disliked_titles`, `notes`.
A deterministic scorer then marks the catalog (+genre overlap, −disliked
genres, large bonus/penalty for named titles, weak popularity prior). We
optionally send the top candidates back to the LLM to pick ids **from that
list only**, so it cannot invent movie ids.

The same JSON schema is produced by a heuristic extractor if no `api.key` /
`OPENAI_API_KEY` is set, so training and tests still run. The graded path is
the LLM: put a key in `api.key` (gitignored) as in I1.

## What we would serve later

`python -m src.recommend --user-id <id> --model auto` is the function the team
project can wrap. We recommend deploying **collaborative SVD for users with
history**, and the **LLM + catalog scorer for users without history**. Content
TF-IDF is the fallback if SVD quality drops on niche users. No service is
deployed for I2.
