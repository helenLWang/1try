# I2 Office Hours 口头部分 · 中英双语话术

作业：**I2: Recommendation Model (oral part) / 20 分**  
官方要求：https://github.com/mlip-cmu/f2026/blob/main/assignments/I2_model.md  
你的课仓库：https://github.com/cmu-seai/f26-model-lew2  
Canvas 提交的是 **某一次 commit 链接**，格式：

`https://github.com/cmu-seai/f26-model-lew2/commit/<长 SHA>`

本仓库当前 HEAD（若你之后又 push 了，以 GitHub 上最新那次为准）：

`https://github.com/cmu-seai/f26-model-lew2/commit/89b10a81da2714c8d559ce2ee7cd63d9ed2373e6`

---

## 0. GitHub 到底要你现场展示什么？

**不要求**把所有文件打开讲一遍。100 分里 80 分是仓库 + `README.md` + `model.md` + `evaluation.md`；**口头只有 20 分**。原文是：

> Within 2 weeks of submitting, meet staff during office hours to **explain your solution**. We may ask about **any part of your implementation** (including AI-written code), **discuss alternatives**, and **reflect on limitations** and **production challenges**.

所以 office hour 正确流程是：

1. 打开 GitHub 仓库首页（给 TA 看你交了什么）
2. 打开 `README.md` / `model.md` / `evaluation.md`（这三份才是作业要求的文档）
3. **口头讲懂**：数据、两个不同模型、冷启动 LLM、怎么评、为什么选 CF、局限、上线问题
4. TA 问到代码时，再点下面「文件地图」里那几个文件

**不要**演示 Kafka 现场采集（VPN/隧道很容易失败）。  
**不要**打开 `api.key`。  
数字记 `evaluation.md` 里那张表即可。

作业里的 **TMDB**（The Movie Database，有人会听成 TMA）= 电影元数据来源。你们用课上 API：`http://128.2.220.123:8080/movie/<id>`，数据大多来自 TMDB。

---

## 1. 去之前打开哪些页面（建议三个标签）

| 标签 | 打开什么 | 干什么 |
| --- | --- | --- |
| A | https://github.com/cmu-seai/f26-model-lew2 | 仓库总览 |
| B | 点进根目录 **`model.md`** | 数据 + 两个模型 + 冷启动 |
| C | 根目录 **`evaluation.md`** | 数字和选哪个模型 |

备用：根目录 **`README.md`**（怎么跑）。  
代码只在 TA 说 “show me the code” 时再点。

---

## 2. 文件地图（TA 问 “where is the code” 就用这个）

在 GitHub 仓库里按路径点，不要乱翻。

| 讲什么 | 点这个 |
| --- | --- |
| 怎么跑 | `README.md` |
| 数据与模型说明 | `model.md` |
| 评估数字 | `evaluation.md` |
| 采集 Kafka + 元数据 API | `src/collect.py` |
| 解析 watch / rate / create_account | `src/parse.py` |
| 批量拉 TMDB 风格电影/用户资料（≤200 个 id） | `src/api.py` |
| 清洗、隐式评分、时间划分 | `src/dataset.py` |
| **方法 1 协同过滤** | `src/models/collaborative.py` |
| **方法 2 内容过滤** | `src/models/content.py` |
| **冷启动 LLM**（prompt 在这里） | `src/models/cold_start.py`（搜 `EXTRACT_PROMPT`） |
| 训练 | `src/train.py` |
| 评估 | `src/evaluate.py` |
| 推荐入口 `recommend(user_id)` | `src/recommend.py` |
| 超参 | `src/config.py` |
| Kafka 隧道 | `scripts/start_kafka_tunnel.sh` |

流行度 `src/models/popularity.py` **只是 baseline，不算作业要求的两个方法。**

---

## 3. 必须记住的数字（卡住就看 `evaluation.md`）

采集：约 **494 万** 条 Kafka，**12 个时间片**，2026-07-17 到 2026-09-08；30,628 条评分，123,780 对观看，17,404 部电影，82,688 个用户。

现有用户（400 人，Top-20）：

| 模型 | HitRate@20 | NDCG@20 |
| --- | ---: | ---: |
| Item–item CF | 0.095 | 0.035 |
| Content TF-IDF | 0.010 | 0.003 |
| Popularity baseline | 0.115 | 0.043 |

冷启动（40 人，只用自我介绍、藏掉全部历史）：

| 方法 | HitRate@20 | NDCG@20 |
| --- | ---: | ---: |
| LLM + catalog scorer | 0.050 | 0.017 |
| Heuristic（无 LLM） | 0.075 | 0.013 |
| Popularity（不用文本） | 0.275 | 0.068 |

**部署选择：** 有历史 → **item–item CF**（内部已能回退到 popularity）；新用户 → **LLM 冷启动**。Content **不**做主模型。

---

## 4. 整场流程（约 8–12 分钟）· 逐字稿

对 TA 说 **英文**。中文是给你自己看的。方括号是你要点的东西。

### 开场（30 秒）

**You say:**  
Hi, I’m Le Wang. This is I2, the recommendation model. I collected the Kafka movielog and the movie/user metadata API, trained two different recommenders, and used an LLM for cold-start. I can walk through GitHub, then data, the two models, cold-start, evaluation, and production limits.

**中文：** 我是 Le Wang。I2 做了 Kafka 采集、两个不同推荐模型、以及用 LLM 做新用户冷启动。我按仓库 → 数据 → 两个模型 → 冷启动 → 评估 → 上线局限来讲。

[打开标签 A：`cmu-seai/f26-model-lew2`]

---

### 步骤 1 · 仓库 / deliverables（1 分钟）

[停留在 GitHub 根目录，指 `README.md`、`model.md`、`evaluation.md`、`src/`]

**You say:**  
The graded files are in the repo root: README for how to run, model.md for data and the two approaches plus the LLM prompt, evaluation.md for metrics. Code is under src/. I did not commit api.key, Kafka passwords, or large CSVs and model pickles — those are gitignored.

**中文：** 作业要的三份文档都在根目录。密钥和大文件没有提交。

If they ask Canvas:  
The Canvas link is the commit URL of this repo, `https://github.com/cmu-seai/f26-model-lew2/commit/` plus the full SHA.

---

### 步骤 2 · 数据（2 分钟）

[打开 `model.md` 第一段 “Data we collect”，或点 `src/collect.py`]

**You say:**  
I consume Kafka topic movielog1 through an SSH tunnel to localhost:9092. The retained log is huge, but one tail slice is only a few hours, so almost every user would have one movie. So I read about 5 million messages from 12 slices across the log.

Three event types, parsed in parse.py:  
watch — GET /data/m/movie/minute.mpg, one line per minute;  
rate — GET /rate/movie=score, I drop ratings outside 1 to 10;  
create_account — I keep the user id so I can fetch their profile.

I aggregate watches in memory to one row per user-movie. I never save every minute to disk. Then I batch movie ids and user ids, at most 200 per request, against http://128.2.220.123:8080 — that is the course metadata API. Movie fields come mostly from TMDB: title, genres, overview, tagline. User fields include free-text likes and dislikes from signup.

For labels, in dataset.py: if the user rated the movie, I use that 1–10 score. If they only watched, I keep watches of at least 3 minutes and turn progress into an implicit score. Shorter watches I treat as accidental clicks.

**中文：** 数据来自 Kafka 观看/评分流 + 课上元数据 API（电影侧基本是 TMDB）。看不够 3 分钟丢掉。用 12 个切片是因为只读尾巴几乎每人只有一部电影。

**If they ask “why not all data?”**  
The stream is continuous. Five million lines across 12 windows was enough to train and evaluate. I logged offsets in collection_meta.json.

**If they ask “TMDB / TMA?”**  
I did not scrape TMDB myself. The course movie API is TMDB-backed. I also keep imdb id if we want extra metadata later.

---

### 步骤 3 · 方法 1 协同过滤（1.5 分钟）

[打开 `src/models/collaborative.py`]

**You say:**  
Approach one is item–item collaborative filtering. I build a user-by-movie matrix of those scores, L2-normalize each movie, and score unseen movies by cosine similarity to movies the user already consumed. I mask movies they already saw. Users with fewer than two interactions fall back to popularity.

I chose item–item instead of a big SVD because in this window most users have one or two movies. A 50-factor SVD mostly fits noise. Co-watch similarity still says: people who watched X also watched Y.

**中文：** 方法一是物品-物品协同过滤：只看谁和谁一起被看过，不用剧情文本。

---

### 步骤 4 · 方法 2 内容过滤（1.5 分钟）

[打开 `src/models/content.py`]

**You say:**  
Approach two is content-based TF-IDF. Each movie is a document of genres — I repeat genres — plus tagline and overview. I do **not** put titles in the document, so rare names don’t collapse neighbors into sequels. A user profile is the rating-weighted average of movies they watched. I rank by 85% cosine plus 15% popularity.

This is substantively different: CF uses other users’ behavior; content uses metadata. Two CF runs with different k would not count. Two users with no overlapping history can still get similar lists if they watched the same genres.

**中文：** 方法二用电影简介/类型做 TF-IDF，不靠别人的观看记录。作业要求两个方法必须本质不同。

---

### 步骤 5 · 冷启动 LLM（2 分钟）

[打开 `src/models/cold_start.py`，滚到 `EXTRACT_PROMPT`]

**You say:**  
New users have no history. Many typed what they like and dislike at signup. I send that text to an LLM — I used Gemini — and ask for JSON only: liked_genres, disliked_genres, liked_titles, disliked_titles, notes. I constrain genres to TMDB names like Action, Comedy, Science Fiction.

Then a **deterministic scorer** marks the catalog: plus for liked genres, minus for disliked, a large bonus if they named a title. The LLM is not allowed to invent movie ids. Optionally I can send top candidates back for re-rank, but in evaluation I turned re-rank off for latency.

If there is no API key, a heuristic extractor fills the same JSON so tests still run. The graded path is the LLM. The key is in gitignored api.key.

**Demo sentence if they want a command (don’t have to run it):**  
I would run: python -m src.recommend --user-id 0 --model coldstart --likes "I like Star Wars" --dislikes "No horror"

Qualitative check: user 13993 wrote “fugitive and t2” and the LLM extracted The Fugitive and Terminator 2. User 12943 mentioned Star Wars and it was in the held-out likes.

**中文：** 冷启动 = LLM 把自我介绍变成 JSON，再用目录打分。模型不能瞎编电影 id。

---

### 步骤 6 · 评估 + 选哪个（2 分钟）

[打开 `evaluation.md` 的表]

**You say:**  
For existing users I split each user by time: leave-one-out if they have 2 to 4 interactions, last 20% if they have 5 or more. I hide the test movies, predict 20 ids, and compute HitRate, Precision, Recall, and NDCG at 20. 400 random test users, seed 42.

HitRate@20: item–item CF 0.095, content 0.010, popularity 0.115. Popularity is slightly higher because histories are short. I still recommend **deploying item–item CF**: it already falls back to popularity, and as the log grows, co-watch structure can beat a static top list. I would **not** ship content as the primary ranker — 0.01 hit rate is too weak.

For cold-start I took 40 users who wrote a likes blurb and had at least two movies rated 7 or higher. I hide **all** history and recommend from text only. LLM hit rate is 0.05 versus popularity 0.275. Popularity wins overlap because signup text is not the same as later ratings — a Godfather fan whose held likes include Happy Gilmore. The intended check is qualitative match to the text, not beating popularity on later ratings. LLM NDCG is a bit higher than the no-key heuristic because it extracts real titles.

The assignment says they do not grade accuracy, so I am not claiming a SOTA model. The protocol is reasonable.

**中文：** 现有用户用时间划分评估。冷启动把历史藏掉、只看自我介绍。数字上 popularity 更高，但我们仍选 CF 给有历史的人、LLM 给新用户。作业不按准确率打分。

---

### 步骤 7 · 反思 / 上线（作业明确会问）（1.5 分钟）

**You say:**  
Limitations: the Kafka window is still sparse, so popularity can beat CF on HitRate. Implicit scores from watch minutes are noisy. Content TF-IDF is weak. Cold-start is only as good as the signup text; many users leave it empty. The LLM can hallucinate titles, which is why we score the catalog instead of trusting generated ids. Movie metadata can be incomplete.

For production: I would not call Gemini on every page view. Extract tastes once at signup, cache them, and refresh on a worker. Rate-limit the LLM. Keep collecting Kafka with a consumer group instead of one-off 5 million slices. Filter already-watched and maybe already-recommended. Watch cost and latency. CF needs periodic retraining. Cold-start plus popularity is safer for true new users until they have two interactions. I did not deploy a service — I2 does not require that.

Alternatives I considered: matrix factorization SVD — too sparse. User–user CF — more expensive with 80k users. Pure LLM-generated ids — they invent ids. Two CF variants with different k — not substantively different, would fail the rubric.

**中文：** 局限是数据稀疏、观看分钟当分数很吵、自我介绍不等于后来评分。上线不要每次请求都打 LLM，要缓存、限流、定期重训。没部署服务，作业不要求。

---

## 5. TA 可能问什么 · 短答

**Q: Did you write this with AI?**  
Yes, I used a coding agent, but I can explain the pipeline: collect, clean, two models, LLM extract then catalog score, time-based eval. I am responsible for the numbers in evaluation.md.

**Q: Show me recommend().**  
[打开 `src/recommend.py`]  
recommend(user_id) returns up to 20 movie ids. auto uses CF if the user is in the matrix, otherwise cold-start.

**Q: How do I rerun evaluation?**  
README: tunnel, then collect, train, evaluate. Need api.key for the LLM path; --no-llm uses the heuristic.

**Q: Why is popularity better? Did you fail?**  
No. Short histories make popular movies likely to appear in the hold-out. The spec does not grade accuracy. I still pick CF for deployment because of the fallback and because it can improve as data grows.

**Q: Are the two approaches different enough?**  
Yes. CF uses only the interaction matrix. Content uses TMDB-style text. Same algorithm with different hyperparameters would not count.

**Q: Kafka credentials?**  
On Canvas, not in git. Tunnel script: scripts/start_kafka_tunnel.sh. I will not type the password here.

**Q: Cold-start without text?**  
Fall back to popularity until they watch two movies, then CF.

**Q: Leakage?**  
Split is per-user chronological. Test movies are masked from training for that user.

**Q: Why 3 minutes?**  
Shorter watches are often previews or accidental clicks.

**Q: Why 12 windows?**  
One tail is only a few hours. Slices spread the retained offsets so users have more than one movie.

---

## 6. 现场操作顺序（你就按这个点）

1. 打开 GitHub `f26-model-lew2` 根目录 → 说三份 md + src  
2. 打开 `model.md` → 讲数据、CF、content、LLM  
3. 打开 `evaluation.md` → 指两张表、说选 CF  
4. 只有被问到代码时：`collaborative.py` → `content.py` → `cold_start.py` 里的 `EXTRACT_PROMPT` → `recommend.py`  
5. 被问上线：背步骤 7 那段，不要临场编

**不要：** 现场跑 Kafka、打开 api.key、把 I1 Zulip 当 I2、把 popularity 说成作业要求的第二个模型。

---

## 7. 30 秒应急版（时间不够就只说这个）

I collected about 5 million Kafka events plus the TMDB-backed movie/user API.  
Two different models: item–item CF on watches and ratings, and TF-IDF on genres and overviews.  
Cold-start: LLM turns signup likes/dislikes into JSON, then I score the real catalog so ids cannot be invented.  
I evaluate with a per-user time split. Popularity is a bit higher on HitRate, but I would deploy CF for users with history and the LLM path for new users.  
Limits: sparse data, noisy implicit labels, LLM cost in production — extract once and cache. I did not deploy a service.

---

## 8. 中文速记（上台前看 1 分钟）

- 口头 20 分 = 讲懂 + 备选方案 + 局限 + 上线，不是点开所有文件  
- 两个模型：协同过滤 vs TF-IDF，本质不同  
- 冷启动：LLM → JSON → 目录打分，不编 id  
- 评估：按时间切；数字在 evaluation.md  
- 上线选 CF + 新用户走 LLM；content 当备胎  
- popularity 只是对照，不是第二个方法  
- TMDB = 电影元数据；我们打的是课上 8080 API  
- 密钥不要给 TA 看
