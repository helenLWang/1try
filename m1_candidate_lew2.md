# Le Wang (lew2) 的 M1 候选模型

明天交给队友用这一份。**这是我一个人的方案**，不是整组的 Milestone 1。

组里还要另外两个人各出一套不一样的。最后一起比四个数，选一个上线。

## 这一套是什么

名字：**item–item CF + LLM 冷启动**

有历史的用户：看过 A 的人也看过什么（协同过滤）。  
没历史的新用户：读注册时写的 likes/dislikes，用 Gemini 抽 JSON，再在真电影列表里打分。  
两边都没有：先给热门电影。

代码入口（队友只要调这个）：

```text
python -m src.m1_recommend 9375
```

打印一行，没有空格，没有 JSON，最多 20 个电影 id，逗号隔开。这就是作业要的：

`http://机器:8082/recommend/<userid>` 的返回格式。

实现：`src/m1_recommend.py`  
本地试服务：`python -m src.m1_server` 然后 `curl http://127.0.0.1:8082/recommend/9375`

## 仓库

https://github.com/cmu-seai/f26-model-lew2

也可以看这个分支：https://github.com/helenLWang/1try/tree/cursor/i2-recommendation-model-f5a6

主要文件：

- `src/models/collaborative.py` 协同过滤
- `src/models/cold_start.py` 新用户 LLM
- `src/evaluate.py` 怎么测准确率
- `src/m1_recommend.py` 给组里接服务用
- `evaluation.md` / `model.md` 作业说明

## 四个数（先拿去填表）

在同一份数据上测的（约 5e6 条 Kafka，时间切分，400 个测试用户）。

准确率（HitRate@20）：**0.095**  
准确率（NDCG@20）：**0.035**  
新用户只看自我介绍的 HitRate@20：**0.05**

训练时间：一次 `python -m src.train` 大约 **35.4 秒**（`artifacts/train_log.json` 里的 elapsed_s）

推理时间：评估里 400 个用户一共 0.12 秒，平均大约 **0.3 毫秒 / 人**。作业限制是 600 毫秒，够用。

模型文件大小：`artifacts/models/recommenders.joblib` 没有提交（大于 5MB 不能进 git）。队友在自己电脑跑完 train 之后执行：

```text
python -m src.m1_measure
```

会写出 `artifacts/m1_lew2_measures.json`，里面有磁盘字节数。

我建议组里上线用这一套，不用我的 content TF-IDF（HitRate 只有 0.010）。

## 队友怎么跑

需要课上 VPN / Kafka 隧道，和 I2 一样。

```text
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./scripts/start_kafka_tunnel.sh
python -m src.collect --max-events 5000000 --windows 12
python -m src.train
python -m src.m1_recommend 9375
```

LLM key 放仓库根目录 `api.key`，不要提交。没有 key 时新用户会走简单规则，格式还是那一行 id。

## 接进组里的 Flask

```python
from src.m1_recommend import recommend_line

@app.get("/recommend/<int:user_id>")
def rec(user_id):
    return recommend_line(user_id)
```

新用户要持续能用：服务里如果发现这个 user 不在 CF 矩阵，就会走冷启动。组里之后要从 `http://128.2.220.123:8080/user/<id>` 把新注册用户的自我介绍补进 `users.jsonl`，或者直接把 likes 文本传给 `cold.recommend(..., likes=..., dislikes=...)`。

## 给队友的短消息（复制发群）

明天我出的方案是 item-item CF，新用户走 LLM。调用 `python -m src.m1_recommend <userid>`，返回一行电影 id。HitRate@20 是 0.095，训练大约 35 秒，单次推荐大约 0.3ms。代码在课仓库 f26-model-lew2，入口 src/m1_recommend.py。我的 content 模型不参赛，太弱了。
