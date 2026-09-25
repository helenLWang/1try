# Data Guide — Team 04 Recommender

The training data is ready. Get on the VM, download the snapshot, point your
models at it, score them, and write them up in `EVALUATION.md`.

Each of us builds all three approaches: **collaborative filtering**,
**content-based**, and **cold start**. So you need the whole snapshot, not a
slice of it.

Snapshot **`v2`**, hash `a07a47ee48a2`. Quote that hash with any result you
report.

## If you were handed the `movielog-v2` folder

Everything is already in it. Skip sections 1 and 2 and go straight to section 3.

```
movielog-v2/
  DATA_GUIDE.md              this file
  EVALUATION.md              the template you fill in
  metrics.py                 the shared scorer
  baseline_popularity.json   the number to beat
  data/
    movies.csv               film metadata
    users.csv                user self-descriptions
    v2/
      train.csv              fit on this
      test.csv               score on this only
      ratings_train.csv      explicit ratings
      ratings_test.csv
      dataset_card.json      how it was built, plus the hash
```

Work inside this folder, or copy `data/`, `metrics.py` and
`baseline_popularity.json` next to your own code. Every path in this guide is
written relative to the folder root.

Run the check in "Verify" below once before you start. It takes a few seconds
and catches a bad copy before it costs you a training run.

Sections 1 and 2 are for rebuilding the folder from the VM if you ever need to.

## 1. Get on the VM

You should already have an account, named after your Andrew ID. Tell me if you
cannot get in and I will sort it out.

| | |
| --- | --- |
| Host | `128.2.220.245` |
| User | your Andrew ID |
| Password | the one from the course setup. Ask me if you never got it |

```
ssh <andrewid>@128.2.220.245
```

The snapshot lives at `/srv/movielog/snapshots/v2/`. It is world-readable, so
you do not need any special permission to copy it.

If you prefer a GUI over the terminal, any SSH client with an SFTP browser works
the same way: connect to the host above and drag the files across.

### Look around before you download

```bash
# what is available
ls -lh /srv/movielog/snapshots/v2/

# how it was built: window, cutoff, counts, hash
cat /srv/movielog/snapshots/v2/dataset_card.json

# what the rows look like
head -3 /srv/movielog/snapshots/v2/train.csv
head -3 /srv/movielog/snapshots/v2/ratings_train.csv
head -2 /srv/movielog/snapshots/v2/movies.csv
head -2 /srv/movielog/snapshots/v2/users.csv

# is the collector still running
/srv/movielog/status.sh
```

## 2. Download the data

Work on your own laptop. Do not train on the VM: 4 cores shared by five people
and a collector already using one.

### What you need

Since everyone builds all three approaches, you need all of it: about **330 MB**.

| Approach | Files it needs |
| --- | --- |
| Collaborative filtering | `train.csv`, `test.csv` |
| Content-based | above, plus `movies.csv` and `ratings_train.csv` |
| Cold start | above, plus `users.csv` |

`interactions.csv` is train and test concatenated. Useful for exploring the
data, never for training. Skip it.

### From the terminal

Run these on your laptop, not from inside an SSH session:

```
cd <your project folder>

# this guide, metrics.py and the baseline
scp -r <andrewid>@128.2.220.245:/srv/movielog/team .

# the interaction data, one file per line
mkdir -p data/v2
scp <andrewid>@128.2.220.245:/srv/movielog/snapshots/v2/train.csv data/v2/
scp <andrewid>@128.2.220.245:/srv/movielog/snapshots/v2/test.csv data/v2/
scp <andrewid>@128.2.220.245:/srv/movielog/snapshots/v2/dataset_card.json data/v2/
scp <andrewid>@128.2.220.245:/srv/movielog/snapshots/v2/ratings_train.csv data/v2/
scp <andrewid>@128.2.220.245:/srv/movielog/snapshots/v2/ratings_test.csv data/v2/

# metadata goes in data/, not data/v2/
scp <andrewid>@128.2.220.245:/srv/movielog/snapshots/v2/movies.csv data/
scp <andrewid>@128.2.220.245:/srv/movielog/snapshots/v2/users.csv data/
```

`movies.csv` and `users.csv` go in `data/`, not `data/v2/`, because they are not
version-specific and most code looks for them there. Run `ls -lh
/srv/movielog/snapshots/v2/` first to confirm the paths before you copy.

**Do not use brace expansion** like `{train.csv,test.csv}`. Modern scp speaks
SFTP and fails with "No such file or directory".

### From a GUI client

Open `/srv/movielog/snapshots/v2/` on the VM, select the files your candidate
needs, drag them into your project's `data/v2/` folder.

### Verify

**Check row counts, not file sizes.** A download that dies halfway leaves a
file that looks fine in `ls` and fails hours later. This is the single most
expensive mistake available to you here. I lost four training runs to a
`test.csv` that had stopped copying.

```
python3 -c "
import json,csv
csv.field_size_limit(10**9)
c=json.load(open('data/v2/dataset_card.json'))
for f,k in [('train','train_interactions'),('test','test_interactions'),('ratings_train','ratings_train'),('ratings_test','ratings_test')]:
    n=sum(1 for _ in open('data/v2/%s.csv'%f))-1
    print('%-16s %9d expected %9d %s'%(f,n,c[k],'OK' if n==c[k] else 'MISMATCH, re-copy'))
for f,e in [('movies',20784),('users',288209)]:
    n=sum(1 for _ in csv.reader(open('data/%s.csv'%f,newline='',encoding='utf-8',errors='replace')))-1
    print('%-16s %9d expected %9d %s'%(f,n,e,'OK' if n==e else 'MISMATCH, re-copy'))
print('hash', c['train_sha256'][:12], 'expected a07a47ee48a2')
"
```

`movies.csv` must be counted with a CSV reader, not by lines. It uses CRLF
endings and a few of the overview texts contain stray carriage returns, so a
plain line count reports five rows too many. Read it with `pd.read_csv`.

Every line must say `OK` and the hash must print `a07a47ee48a2`. If the hash
differs you are on a different snapshot and your numbers will not match anyone
else's.

### Keep it out of git

Add to `.gitignore` before your first commit:

```
data/
models/
```

485 MB will slow every clone, and GitHub rejects files over 100 MB. The hash
goes in the repo instead, so results stay traceable without the data being
versioned.

## 3. What the data is

| What you get | Use it for |
| --- | --- |
| `train.csv` / `test.csv` | collaborative filtering, anything interaction-based |
| `ratings_train.csv` / `ratings_test.csv` | explicit 1-to-10 signal, reranking or its own model |
| `movies.csv` | content-based models |
| `users.csv` | cold start |

### Why it is only 485 MB when we collected 3.3 GB of logs

**Watching one film writes about 110 log lines.** The stream sends a film one
minute at a time, and every minute is its own line. All 110 lines say the same
thing: this user watched this film. We keep it once.

That is the whole difference.

Here is one viewing of a 136-minute film as the collector recorded it:

```
timestamp,user_id,movie_id,minute,partition,offset
2026-09-01T10:00:03.204,123,the+matrix+1999,0,0,104829110
2026-09-01T10:01:04.118,123,the+matrix+1999,1,0,104829418
...
2026-09-01T12:15:44.661,123,the+matrix+1999,135,0,104871902
```

All 136 say the same thing: user 123 watched The Matrix. The snapshot stores it
once, keeping the latest timestamp and the highest minute:

```
user_id,movie_id,timestamp,minutes_watched
123,the+matrix+1999,2026-09-01T12:15:44.661,135
```

Exact figures for v2: 368,188,738 lines, 2,998,698 rows.

### Why we do not keep all the rows

A model needs exactly one number per (user, film) cell. If that number is the
row count, you have chosen runtime as your signal. Two examples of what that
does.

Across films:

| Film | Runtime | People who watched it | Raw rows |
| --- | --- | --- | --- |
| The Godfather | 175 min | 100 | 17,500 |
| The Hangover | 100 min | 150 | 15,000 |

The Hangover is watched by 50% more people. The Godfather has more rows. A model
counting rows ranks The Godfather higher and recommends it to more users,
forever.

Inside one user:

| What user 123 did | Raw rows |
| --- | --- |
| Finished The Matrix, 136 min | 136 |
| Finished a 90-minute comedy | 90 |

They finished both, so they liked both equally as far as we can tell. Row counts
say they preferred The Matrix by 1.5 times. They did not. The film is just
longer.

**Always train from the snapshot, never from the raw logs**, even on the VM. The
collapse has to happen before training either way, and doing it from raw costs
15 to 30 minutes and several GB of RAM on every run.

### What is lost

1. `minutes_watched` is the furthest minute reached, not total time watched.
2. Rewatches merge. Watching the same film twice becomes one row.
3. Per-minute pacing is gone. Only matters for sequential models.

Nothing is deleted. The raw events are still in `/srv/movielog/data/`, and
`build_dataset.py` rebuilds in about 30 minutes if we want a different shape.

### The files

| File | Size | What it is |
| --- | --- | --- |
| `train.csv` | 139 MB | 2,699,724 interactions, Aug 31 to Sep 20. Fit on this |
| `test.csv` | 16 MB | 298,974 interactions, Sep 21 to 22. Score on this only |
| `ratings_train.csv` | 93 MB | 1,860,669 explicit ratings, same window as train |
| `ratings_test.csv` | 11 MB | 209,595 ratings after the cutoff |
| `movies.csv` | 7.9 MB | 20,784 films: title, genres, overview text, runtime. Covers every film in the data |
| `users.csv` | 66 MB | 288,209 users: age, occupation, gender, free-text likes and dislikes |
| `interactions.csv` | 155 MB | Train and test combined, for exploring. Never train on it |
| `dataset_card.json` | 1.5 KB | How it was built, plus the hash |

### Metadata for content and cold start

`movies.csv` and `users.csv` do not come from the Kafka stream. They were
fetched from the course's read-only API and cached into the snapshot, so you get
them with the same download and never need API access yourself. That matters:
the API is reachable from the VM, not from a laptop off campus.

`users.csv` carries `age`, `occupation`, `gender`, `likes` and `dislikes`. The
last two are free text, and **201,280 of 288,209 users have it**, about 70%. It
reads like this:

> "Yeah, so I'm into the big movies, you know? Like 'The Godfather' and
> 'Schindler's List' are definitely my jam... Think classic dramas, epics, maybe
> some good rom-coms."

That is the cold-start signal: a new user with no watch history still arrives
with a written description of their taste.

### The columns

`train.csv` and `test.csv`, one row per interaction:

| Column | Meaning |
| --- | --- |
| `user_id` | int |
| `movie_id` | opaque string like `the+matrix+1999`. Never split the year off, ids like `1984+1956` exist |
| `timestamp` | last event for this pair |
| `minutes_watched` | furthest minute reached, a rough engagement signal |

`ratings_train.csv` and `ratings_test.csv` are the same shape with `rating`, an
integer 1 to 10, in place of `minutes_watched`.

### What it looks like

| | v2 |
| --- | --- |
| Window | Aug 31 to Sep 22, 2026 |
| Interactions | 2,998,698 |
| Users in train | 287,063 |
| Films | 20,784 |
| Films per user | 9.4 |
| Users with 2 or more films | 259,105 (90.3%) |
| Users scorable in test | 137,694 |
| Matrix density | 0.045% |
| Ratings | 2,070,264, from 274,611 users, 86.8% with 2 or more |

Two things to know going in. Histories are short, so no model will know a user
deeply. And popularity is concentrated enough that a plain most-watched list is
a strong baseline. Beating it by a little is a normal result here, not a
failure.

### Known data quality issue

**Sep 14 and Sep 16 are missing, and Sep 15 has only 1,451 rows.** The stream or
the broker had an outage. The data was never in Kafka and is not recoverable.

So v2 is 20 days of data across a 23-day window. The train/test boundary at
Sep 21 is clean, so the split is still valid, but this belongs in the report
under data quality.

## 4. Point your model at it

Expect a bug or two: most of our I2 code was written but never actually run
against real data. I hit a genuine crash in `bm25_weight` on the first try.

### a. Delete your collection and parsing code

In I2 you collected from Kafka and parsed raw events. Skip all of it. Read
`train.csv` directly.

### b. Do not collapse events again

I2 code usually has `groupby(['user_id','movie_id'])`. **Already done.** Harmless
to repeat, but if your version aggregates counts you will get 1 for everything.

### c. Rename the columns

I2's `watches.csv` used `ts` and `minute`. The snapshot uses `timestamp` and
`minutes_watched`. This is the most common way the port fails.

```python
df = pd.read_csv("data/v2/train.csv")
if "minutes_watched" in df.columns:
    df = df.rename(columns={"minutes_watched": "minute"})
```

### d. Do not split the data yourself

Remove any `temporal_split` or `quantile` call. The split is already applied and
is fixed, not a quantile. Re-splitting makes your numbers incomparable.

### Loading it

Every model starts the same way:

```python
import pandas as pd
train   = pd.read_csv("data/v2/train.csv")
movies  = pd.read_csv("data/movies.csv")
users   = pd.read_csv("data/users.csv")
ratings = pd.read_csv("data/v2/ratings_train.csv")
```

Note that `movies.csv` and `users.csv` sit in `data/`, not `data/v2/`. They are
not version-specific.

If your candidate is content-based, rule-based, or anything that works from rows
rather than a matrix, that is all you need.

If it needs a user-by-film matrix:

```python
import numpy as np, scipy.sparse as sp

users  = {u: i for i, u in enumerate(train.user_id.unique())}
movies = {m: i for i, m in enumerate(train.movie_id.unique())}

matrix = sp.csr_matrix(
    (np.ones(len(train)), (train.user_id.map(users), train.movie_id.map(movies))),
    shape=(len(users), len(movies)))
```

`np.ones` for a binary signal, `train.minutes_watched` to weight by engagement.
Either is fine, say which you used.

### What your model must expose

```python
def recommend(user_id: int, k: int = 20) -> list[str]:
    """Up to k movie_id strings, best first."""
```

Three hard rules:

1. **Return k items for any user**, including unseen ones. Fall back to
   popularity rather than returning an empty list.
2. **Never return a film the user already watched in training.** The scorer
   raises an error if you do.
3. **Never read `test.csv`** while fitting or tuning. Hold out a slice of
   `train.csv` by timestamp if you need to tune.

### Gotchas that cost me time

**If you copied your I2 folder, your venv is broken.** The `bin/python` symlink
points at a Python that moved. Rebuild it:

```
rm -rf venv
python3 -m venv venv
./venv/bin/pip install -q -U pip numpy pandas scipy scikit-learn implicit
```

**Check that the file you expected to load actually loaded.** Code that does
`if os.path.exists(path):` before reading will skip the file silently and take a
worse path without telling you. This bit me: `movies.csv` was a broken symlink,
so my model estimated film runtimes from watch minutes for every run I did, and
nothing in the output said so. Print what you loaded and how many rows.

**Do not suppress output on a first run.** I had `>/dev/null 2>&1` on a sweep and
watched the same error fail silently four times. Add the redirect once the run
works, never before.

**Check your fallback path before you rely on it.** Many I2 models degrade to
something simpler when a library is missing. Those fallbacks were written for
I2's 14,611 films and may not survive 20,784. Mine falls back to item-item
cosine, which builds a 20,784 by 20,784 similarity matrix and can exhaust RAM.

**If your model filters users during training, keep the full seen-set.** A
k-core filter that drops single-film users will leave them out of your "already
watched" lookup. Your model then recommends a film they have seen and the scorer
rejects it with a `ValueError`.

**Reset any global model cache between runs.** If your loader caches, scoring
two models in one process silently re-scores the first.

### Cost

No GPU, 4 cores, 15 GB RAM. At 2.7M interactions expect training in minutes
rather than hours. For scale, ALS at 64 factors on v1's 823k interactions took
about 20 seconds; v2 is roughly 3x that data.

If yours takes an hour, the problem is almost certainly in how you are loading
or reshaping the data, not in the model itself.

## 5. Score it

We report Precision@20, Recall@20 and NDCG@20, using `metrics.py` unchanged. Do
not write your own scorer: three reasonable implementations give three
incomparable numbers.

`metrics.py` is in the folder root. If your code lives elsewhere, copy it next
to your model. It calls one function, whatever your model is built from:

```python
def recommend(user_id: int, k: int = 20) -> list[str]:
    """Up to k movie_id strings, best first."""
```

Wrap your own code to match, then score:

```python
from metrics import load_eval_data, score_model

# adapt these two lines to your model
import my_model
recommend = lambda u, k=20: my_model.recommend(u, k)

data = load_eval_data("data/v2/train.csv", "data/v2/test.csv")
print(score_model(recommend, data, k=20))
```

Add `sample_users=20000` while developing. Drop it for anything you report.

### The number to beat

**Popularity is the baseline every candidate is compared against.** It is the
simplest possible recommender: rank films by how often they appear in
`train.csv`, give everyone the top 20, minus anything they already watched. No
personalization at all. A model that cannot beat it is not earning its
complexity.

**Do not compute it yourself.** It is measured once on the full user set and
lives in `baseline_popularity.json`. Read your comparison numbers from that
file. Three people each writing their own popularity function produces three
slightly different baselines, and then none of the candidate comparisons mean
anything.

| Metric | Popularity on v2 |
| --- | --- |
| Recall@20 | 0.1006 |
| Precision@20 | 0.0108 |
| NDCG@20 | 0.0502 |
| Hit rate@20 | 0.1952 |
| Users scored | 137,694 |

```python
import json
baseline = json.load(open("baseline_popularity.json"))
print(baseline["recall@20"])
```

For scale, ALS on v2 scored 0.0556 at 32 factors and got better the fewer
factors it had, reaching 0.0863 at 4 factors. All of those lose to popularity at
0.1006. Beating popularity on this data is hard, and beating it by a little is a
normal result rather than a failure. Do not spend three days assuming your code
is broken because you cannot beat it.

### Cold start cannot be scored this way

`metrics.py` only scores users who have history in `train.csv`, because a user
with no history has nothing to personalize from. So your cold-start model will
not produce a recall number comparable to the other two.

Evaluate it on its own terms and say which method you used: hold out the history
of warm users and treat them as cold, compare against the popularity list for
the same users, or inspect what a handful of unknown users get. `EVALUATION.md`
asks for this explicitly. Do not force a recall number that does not mean
anything.

Precision@20 is capped near 0.11 by arithmetic, since users hold about 2.2
held-out films and precision divides by 20. Expect roughly a tenth of your
recall. Do not panic at 0.01.

## 6. Write it up

When your models run and score, fill in **`EVALUATION.md`**. Copy it to
`EVALUATION_<yourname>.md` so we do not collide in git.

It has four parts:

| Part | What it asks for |
| --- | --- |
| 1. How you measure | the four graded measures, defined once: what each is, what data it uses, how you operationalized it |
| 2. Summary | one table, your three models side by side. Fill this in last |
| 3. The three models | one block each: what it is, config, metrics, cost, coverage, what you tried |
| 4. Your verdict | which of your three is strongest, your caveats, what you would do next |

Coverage decides whether we can deploy a model at all. One that returns the same
20 films to everyone scores 0% personalized and costs the team 10 points, however
good its recall.

Part 4 asks what you tried that failed and what you are unsure about. Fill those
in honestly. They are what make the final selection look reasoned, and the mentor
debriefing asks about them directly.
