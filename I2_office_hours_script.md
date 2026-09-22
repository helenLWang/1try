# I2 Office Hours 口头部分 · 简单口语稿

作业：I2 Recommendation Model，口头 20 分  
仓库：https://github.com/cmu-seai/f26-model-lew2  
官方要求：https://github.com/mlip-cmu/f2026/blob/main/assignments/I2_model.md

对 TA **说英文**。中文只给你自己看。句子都很短，卡住就看第 7 节那 30 秒。

---

## 最重要（先看）

- **不用打开 Kafka 网站。** 作业没让你现场连数据。
- **不用把所有文件点开讲。** 口头分是：你讲得懂、能答局限和上线。
- 去之前开 3 个网页：仓库首页、`model.md`、`evaluation.md`。
- 不要打开 `api.key`。不要把 I1 的 Zulip 拿来讲。
- popularity **不是**作业要求的第二个模型，只是拿来对比。
- TMDB（有人听成 TMA）= 电影资料。你没有自己爬网站，用的是课上 `8080` 接口。

---

## 1. 去之前打开什么

| 标签 | 打开 | 干什么 |
| --- | --- | --- |
| A | https://github.com/cmu-seai/f26-model-lew2 | 给 TA 看仓库 |
| B | 点 `model.md` | 讲数据和两个模型 |
| C | 点 `evaluation.md` | 讲数字 |

TA 说 show me the code 再点 `src/` 里的文件。

---

## 2. 文件在哪（被问再点）

| 他们问 | 你点 |
| --- | --- |
| 怎么跑 | `README.md` |
| 数据 / 模型说明 | `model.md` |
| 数字 | `evaluation.md` |
| Kafka 采集 | `src/collect.py` |
| 怎么读每一行日志 | `src/parse.py` |
| 拉电影 / 用户资料 | `src/api.py` |
| 清洗、切训练测试 | `src/dataset.py` |
| 方法 1 | `src/models/collaborative.py` |
| 方法 2 | `src/models/content.py` |
| 新用户 + LLM | `src/models/cold_start.py`（搜 EXTRACT_PROMPT） |
| 给一个用户推荐 | `src/recommend.py` |

`src/models/popularity.py` 只是对比，不是第二个方法。

---

## 3. 数字（卡住就翻 evaluation.md）

大概 **494 万** 条日志，**12** 段，时间 2026-07-17 到 09-08。  
3 万多条评分，12 万对观看，1.7 万部电影，8 万多用户。

有历史的用户（400 人，推荐 20 部）：

| 模型 | HitRate@20 | NDCG@20 |
| --- | ---: | ---: |
| 方法1 CF | 0.095 | 0.035 |
| 方法2 内容 | 0.010 | 0.003 |
| 热门对比 | 0.115 | 0.043 |

新用户冷启动（40 人，不看历史，只看自我介绍）：

| 方法 | HitRate@20 | NDCG@20 |
| --- | ---: | ---: |
| LLM | 0.050 | 0.017 |
| 不用 LLM 的简单规则 | 0.075 | 0.013 |
| 热门（不用文字） | 0.275 | 0.068 |

**你选哪个上线：** 老用户用方法 1（CF）；新用户用 LLM。方法 2 不当主力。

HitRate@20 用白话说：推荐 20 部里，有没有至少一部是用户后来真看过/评过高的。

---

## 4. 整场对着读（8–12 分钟）

### 开场（30 秒）

这时点：仓库首页

**说：**  
Hi, I’m Le Wang. This is homework I2. I built a movie recommender. I got data from Kafka and from the class movie API. I made two different models. I also used an LLM for new users. I can talk about the data, the two models, cold start, and the numbers.

**中文：** 这是 I2。数据来自 Kafka 和课上电影接口。两个不同模型。新用户用 LLM。

---

### 步骤 1 · 仓库（1 分钟）

这时点：根目录，指 README、model.md、evaluation.md、src 文件夹

**说：**  
The three write-ups are in the root folder. README is how to run it. model.md is how it works. evaluation.md is the numbers. Code is in src. I did not put the API key or big data files on GitHub.

**中文：** 三份说明在根目录。密钥和大文件没上传。

如果问 Canvas：  
The Canvas link is this repo plus /commit/ and the long commit id.

---

### 步骤 2 · 数据（2 分钟）——仍然不用打开 Kafka

这时点：`model.md` 或 `src/collect.py`

**说：**  
The data comes from Kafka. The topic name is movielog1. I connect with SSH. I do **not** open a Kafka website. The full log is huge. If I only read the newest part, most users only watched one movie. So I took about 5 million lines from 12 different parts of the log.

There are three kinds of lines. One: the user watched one minute of a movie. Two: the user rated a movie 1 to 10. Three: a new user signed up.

I do not save every minute. I keep one row per user and movie. Then I ask the class API for movie info and user info. Max 200 ids at a time. Movie info is like TMDB: title, genres, plot. Users can also write what they like and don’t like when they sign up.

If they rated it, I use that score. If they only watched it, I keep it only if they watched at least 3 minutes. Less than 3 minutes I treat as a click by mistake.

**中文：** 数据从 Kafka 来，但别打开 Kafka 网页。三种日志：看、评、注册。看不够 3 分钟丢掉。电影资料来自课上 8080 接口。

如果问 why not all data：  
The stream never stops. 5 million lines was enough to train and test.

如果问 TMDB / TMA：  
I did not scrape TMDB. The class movie API already has that info.

如果问为什么不打开 Kafka：  
The homework does not ask for a live Kafka demo. I can show collect.py. Live Kafka needs VPN and a password, and it often fails.

---

### 步骤 3 · 方法 1（1.5 分钟）

这时点：`src/models/collaborative.py`

**说：**  
Model one is collaborative filtering. Simple idea: if you watched movie A, I look at other people who also watched A, and I recommend what they watched next. I do not use the plot text. I only use who watched what.

If a user has almost no history, I just give them popular movies.

I did not use a big SVD model, because in my data most people only watched one or two movies. That fancy model would mostly learn noise.

**中文：** 方法一：看过这部的人也看过那部。不用简介。

---

### 步骤 4 · 方法 2（1.5 分钟）

这时点：`src/models/content.py`

**说：**  
Model two is content-based. Simple idea: I read the movie genres and the short plot. I turn that into numbers with TF-IDF. Then I recommend movies that look like the ones you already liked.

I do not put the movie title into that text, because titles make it recommend sequels with the same name.

These two models are different on purpose. One uses other users’ behavior. One uses movie text. The homework says two models with the same method but different settings do **not** count.

**中文：** 方法二：看类型和简介像不像。作业要两个方法真的不一样。

---

### 步骤 5 · 新用户 LLM（2 分钟）

这时点：`src/models/cold_start.py`，搜 EXTRACT_PROMPT

**说：**  
New users have no watch history. But many of them typed what they like when they signed up. I send that text to an LLM. I used Gemini. I ask it to return JSON: liked genres, disliked genres, movie names they said.

Then **my code** scores the real movie list. Plus points if the genre matches. Big plus if they named a movie. The LLM is not allowed to make up movie ids.

If there is no API key, I have a simple backup that looks for genre words. The real homework path is the LLM. The key is in api.key. I did not commit the key.

**中文：** 新用户：把自我介绍给 LLM，再在真电影列表里打分。不能瞎编电影编号。

如果他们想看命令（不必跑）：  
python -m src.recommend --user-id 0 --model coldstart --likes "I like Star Wars" --dislikes "No horror"

例子：有人写了 fugitive and t2，模型找出 The Fugitive 和 Terminator 2。

---

### 步骤 6 · 数字和你选谁（2 分钟）

这时点：`evaluation.md` 两张表

**说：**  
For old users, I split by time. I hide their later movies, ask the model for 20 movies, and see if the hidden ones show up. I tested 400 users.

HitRate at 20: CF is 0.095. Content is 0.010. Popular movies is 0.115. Popular is a little higher because people don’t have much history, so hot movies often appear in the test set.

I still want to **ship CF** for users with history. It can already fall back to popular movies. When we have more data, “people also watched” can get better. I would **not** ship the content model as the main one. 0.01 is too low.

For new users, I took 40 people who wrote a like-text and later rated some movies 7 or higher. I hide all their history. I only use the text. LLM hit rate is 0.05. Popular is 0.275. That’s okay. What they wrote at signup is not always what they rated later. The homework does not grade accuracy. I mainly check that the LLM understands the text.

**中文：** 按时间切开来测。热门分更高，但老用户仍选 CF，新用户选 LLM。作业不看你模型有多准。

---

### 步骤 7 · 问题和上线（必问，1.5 分钟）

**说：**  
Problems: the data is still thin, so popular movies can beat CF. Watch minutes are noisy. The content model is weak. Cold start is only as good as the signup text. The LLM can make up titles, so I score the real catalog.

For production: I would **not** call Gemini on every page load. I would run the LLM once when they sign up, save the result, and reuse it. I would limit how often we call the LLM. I would keep reading Kafka in the background, not as a one-time 5 million dump. I need to hide movies they already watched. CF needs to be retrained later. I did not deploy a website. I2 does not ask for that.

Other ideas I did not pick: SVD — too little data. User-user CF — too many users, too slow. Let the LLM output movie ids — it invents fake ids. Two CF models with different k — the homework would say that’s not two different methods.

**中文：** 数据少、分数吵。上线不要每次刷新都打 LLM。没做网站，作业不要求。

---

## 5. 他们可能问 · 用短句答

**Did you use AI to write the code?**  
Yes. I still understand the pipeline: collect data, clean it, two models, LLM for new users, then test. The numbers in evaluation.md are mine to explain.

**Show me recommend().**  
点 `src/recommend.py`。  
This function takes a user id and returns up to 20 movie ids. auto means: if they have history, use CF; if they are new, use cold start.

**How do I run the eval?**  
See README. Tunnel, collect, train, evaluate. You need api.key for the LLM. I don’t need to run it live.

**Why is popularity better? Did you fail?**  
No. People have short history, so hot movies show up in the test set. The homework does not grade accuracy. I still pick CF for later, because it can grow with more data.

**Are the two models different enough?**  
Yes. One uses who watched what. One uses movie text. Same method with two settings would not count.

**Do I need to see Kafka?**  
No. I can show collect.py. I don’t open a Kafka UI. Live Kafka needs VPN and often fails.

**Where is the password?**  
On Canvas. Not on GitHub. I won’t type it here.

**What if the new user wrote nothing?**  
Give them popular movies until they watch two movies. Then use CF.

**Did test data leak into training?**  
No. I split each user by time. Later movies are hidden.

**Why 3 minutes?**  
Shorter is often just a preview or a misclick.

**Why 12 parts?**  
The newest slice is only a few hours. 12 parts give people more than one movie.

---

## 6. 现场你就按这个点

1. 打开 GitHub 仓库 → 说三份 md  
2. 打开 `model.md` → 数据、方法1、方法2、LLM  
3. 打开 `evaluation.md` → 两张表、说选 CF  
4. 被问代码才点：collaborative → content → cold_start 的 EXTRACT_PROMPT → recommend.py  
5. 被问上线：背步骤 7

不要：打开 Kafka、打开 api.key、把 Zulip 当 I2、说 popularity 是第二个模型。

---

## 7. 时间不够就只说这 30 秒

I got about 5 million Kafka events and movie info from the class API.  
Two different models: one is “people also watched this”, one is “movies with similar plot and genres”.  
For new users, an LLM reads what they typed, then my code picks real movie ids.  
I test by hiding later movies. Popular is a bit higher, but I would use CF for old users and the LLM for new users.  
I would not call the LLM on every click. I did not deploy a service.

---

## 8. 上台前看 1 分钟

- 不用开 Kafka  
- 口头 = 讲懂，不是炫文件  
- 方法1：别人也看过  
- 方法2：类型和简介像  
- 新用户：LLM 读自我介绍，再在真列表里挑  
- 老用户上线用方法1，新用户用 LLM  
- popularity 只是对比  
- 数字在 evaluation.md  
- 密钥别给 TA 看
