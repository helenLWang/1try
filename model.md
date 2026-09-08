# Model description

This assignment builds movie recommenders from a live Kafka watch/rate log and
the course metadata API. Code pointers are relative to the repository root.

## Data we collect

`python -m src.collect` reads topic `movielog1` through the SSH tunnel
(`localhost:9092`). The retained log is huge (hundreds of millions of lines)
but a **single tail slice is only a few hours of traffic**, so almost every
user has one movie. By default we therefore read about 5 million messages
from **12 slices spaced across the retained offsets** (each slice also has a
45-second time budget so a cold Kafka segment cannot stall the job). The
evaluation run scanned 4.94M lines spanning 2026-07-17 through 2026-09-08
(counts and offsets: `data/collection_meta.json`).

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

## Approach 1: collaborative filtering (item–item cosine)

`src/models/collaborative.py`. We keep users/movies with ≥2 interactions,
build a sparse user × movie matrix, L2-normalize each movie's user vector, and
score unseen movies by cosine similarity to the movies that user already
consumed (`S @ r_u` without materializing `S`). Already-seen movies are
masked; users who never enter the matrix fall back to popularity.

We chose item–item CF rather than a large SVD because this stream is sparse
in any collected window (most users have one or two movies). Factorizing
residuals with 50 latent dimensions mostly reconstructs noise; co-watch
similarity still transfers “people who watched X also watched Y”. It cannot
recommend a movie nobody in the window has touched, and it fails for
brand-new users — that is the cold-start hole.

## Approach 2: content-based TF-IDF

`src/models/content.py`. Each movie is a document of **genres (repeated),
tagline, and overview** — titles are omitted so rare proper nouns do not
collapse neighbors to sequels that share a place name. A `TfidfVectorizer`
(4000 features, 1–2 grams, English stops) yields L2-normalized vectors. A
user profile is the rating-weighted average of movies they already consumed.
We rank by 85% cosine + 15% popularity so ties are not obscure catalog noise,
and mask seen ids.

This is substantively different from item–item CF: two users with disjoint
histories can still get similar lists if they watched the same genres, and a
long-tail title with a rich overview can surface with little collaborative
support. It cannot pick up “people like you also liked X” when X is unlike
the user’s text profile.

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
project can wrap. We recommend deploying **item–item CF (with a popularity
fallback) for users with history**, and the **LLM + catalog scorer for users
without history**. Content TF-IDF is useful when CF has too little overlap.
No service is deployed for I2.
