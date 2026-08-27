# Lab 1：Kafka 数据流实验（小白完整指南）

课程：[17-445/17-645 ML in Production, Fall 2026](https://github.com/mlip-cmu/f2026/blob/main/labs/lab01.md)

这个实验**不是交 PDF**，而是 recitation 当场给助教演示。下面按「你要做什么 → 电脑上点哪里 → 助教可能问什么」写。

已经替你填好 starter 里所有 TODO，并且真的连上课程 Kafka、写出 20 条消息、读回来、用 `seek()` 从三个 offset 重放、用 `kcat` 从中间 offset 消费。证据在 `kafka_log.csv`、`outputs/` 和 `KafkaDemo.ipynb` 里。

---

## 0. 这个实验到底在干什么？

Kafka 可以想成一台**永不覆盖的录像带 / 日志本**：

| 词 | 人话 |
| --- | --- |
| **Broker** | 存放日志的服务器。课程的 Kafka 在 `128.2.220.123`，你不能直接连 `:9092`，要先打 SSH 隧道。 |
| **Topic** | 一本有名字的日志。你的实验 topic 是 `lab01-helenlwang`。组项目读的是 `movielog1`（或你们组的 `movielogN`）。 |
| **Partition** | 一本日志可以拆成几卷。本实验只有 partition 0。 |
| **Offset** | 这一卷上的行号。第 1 条还在的消息是 offset 0，下一条是 1，再下一条是 2…… |
| **Producer** | 往日志末尾**写**新行。 |
| **Consumer** | 从某个 offset 开始**读**。读完可以记住「我读到哪了」（commit）。断线后从上次的 offset 继续，不会丢、也不会默认重读全部。 |

助教一定会问 topic 和 offset。把上面这张表讲出来就够。

---

## 1. 你要交 / 演示的三件事

1. **SSH 隧道连上 Kafka**，并讲清 topic、offset、断线后续读。
2. **改 starter 代码**：producer 写城市温度，consumer 读出来；讲 `auto_offset_reset`；用 `seek()` 从有效范围内**三个**起点重放（不能只演示头尾）。
3. **用 kcat** 看 topic / 消息，并且用**绝对 offset**（例如 `-o 8`）从日志中间消费。

---

## 2. 课上给的服务器信息（Canvas / 17445 Pages）

| 项 | 值 |
| --- | --- |
| 服务器 | `128.2.220.123`（在 CMU 网内；校外先连 **CMU VPN**） |
| SSH 隧道账号 | `tunnel` |
| 密码 | `mlip-kafka` |
| 隧道命令 | `ssh -L 9092:localhost:9092 tunnel@128.2.220.123 -NT` |
| 电影 API | `http://128.2.220.123:8080/movie/<movieid>` |
| 用户 API | `http://128.2.220.123:8080/user/<userid>` |
| 组项目数据流 | topic `movielog1`（组项目开始后改用你们组的 `movielogN`） |

规则：平时**只读** Kafka；**本 lab 允许写**自己的 `lab01-你的id` topic。想写别的 topic 要先问课程组。

---

## 3. 在你自己电脑上当场演示（recitation 用）

### 3.1 校外先开 VPN

CMU VPN 连上之后再做后面步骤。

### 3.2 打开隧道（第一个终端，一直挂着）

macOS / Linux / WSL：

```bash
ssh -L 9092:localhost:9092 tunnel@128.2.220.123 -NT
```

提示密码时输入 `mlip-kafka`（输入时屏幕不会显示字符，输完回车）。  
这个窗口**不会打印任何东西，也不要关**。它把远端 Kafka 的 9092 端口映射到你电脑的 9092。

测通：新开**第二个**终端：

```bash
kcat -b localhost:9092 -L
```

能看到 `lab01-helenlwang`、`movielog1` 等 topic 就成功了。

还没装 kcat：

- Mac：`brew install kcat`
- Ubuntu：`sudo apt-get install kcat`
- Windows：用 WSL，或和旁边用 Mac/Linux 的同学一起演示这一项

### 3.3 安装 Python 依赖（第二个终端）

```bash
cd lab01
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3.4 两种演示方式，选一种即可

**方式 A（推荐，一条命令跑完全部 Python 部分）：**

```bash
python kafka_lab.py
```

你会看到：写入 offset `0 .. 19` → 读回 20 条 → `seek` 到 0、10、18。

**方式 B（官方 notebook，助教可能更认这个）：**

```bash
pip install jupyter
jupyter notebook KafkaDemo.ipynb
```

从上到下 Run。Consumer 那个格子读完会自己停（加了 5 秒超时）。若某格报 `NoBrokersAvailable`，回去看隧道窗口是不是还活着。

### 3.5 演示 kcat（第三个交付项）

```bash
# 从头读 5 条，左边数字就是 offset
kcat -b localhost:9092 -t lab01-helenlwang -C -o beginning -c 5 -e -f "%o: %s\n"

# 从中间绝对 offset 8 再读 5 条（必须做这一条）
kcat -b localhost:9092 -t lab01-helenlwang -C -o 8 -c 5 -e -f "%o: %s\n"
```

`-e` 表示读到日志末尾就退出，否则 kcat 会一直等新消息，看起来像卡住。

可选（组项目预习）：

```bash
kcat -b localhost:9092 -t movielog1 -C -o beginning -c 5 -e -f "%o: %s\n"
curl "http://128.2.220.123:8080/movie/fight+club+1999"
curl "http://128.2.220.123:8080/user/118511"
```

---

## 4. 代码里每个 TODO 填了什么

官方 starter：https://github.com/AshrithaG/mlip-kafka-lab

| TODO | 填写 |
| --- | --- |
| `andrew_id` | `"helenlwang"`（和别的同学撞名就改成你的 Andrew ID） |
| producer `bootstrap_servers` | `["localhost:9092"]` |
| `value_serializer` | `lambda m: dumps(m).encode("utf-8")`（dict → JSON 文本 → 字节） |
| 城市 | Pittsburgh 64、Shanghai 82、San Francisco 68 |
| consumer topic / bootstrap | 和 producer 一样 |
| `auto_offset_reset` | `"earliest"` |
| `beginning_offsets` / `end_offsets` | 有效范围 `0 .. 19`（end 是下一条将要写入的位置，所以最后可读是 19） |
| 三个 seek 起点 | `0`（开头）、`10`（中间）、`18`（最后 2 条） |

本次真实运行结果：

- 写入 offset **0 到 19**
- Python 从中间 seek **10**，读到 Shanghai / Shanghai
- kcat `-o 8` 从 Pittsburgh 那条开始，和 Python consumer 的 offset 8 对得上

---

## 5. 助教爱问的概念（先背这几句）

完整口述稿见 [`助教讲解稿.md`](助教讲解稿.md)。

**Topic：** 一个有名字的消息流。写的人和读的人都认这个名字。我们的实验流是 `lab01-helenlwang`，电影点击流是 `movielog1`。

**Offset：** 分区日志里每条消息的整数地址。它保证顺序，也保证断线后续读：consumer group 会 commit「我读到了 offset X」，重连后从 X+1 继续。

**`auto_offset_reset`：** 只在「这个 group 还没有有效的已提交 offset」时生效，而且只能选两个**端点**：

- `earliest`：从日志还保留的最老一条开始（本实验是 0）
- `latest`：跳过历史，只等新消息（水位线 / high watermark，本实验是 20，现在读不到东西）
- `none`：没有已提交 offset 就报错

它**不能**把你放到 8 或 10。从中间重放必须 `consumer.seek(partition, offset)`，或 `kcat -o 8`。

三个起点里：

- offset **0** → `earliest` 自己就能到
- 水位线 **20**（下一条）→ `latest` 自己就能到（但那里还没有消息）
- offset **10**（以及 kcat 的 `-o 8`）→ **必须 seek**

---

## 6. 目录

```
lab01/
  KafkaDemo.ipynb     # 填好 TODO、带本次运行输出的 notebook
  kafka_lab.py        # 同一套逻辑的脚本，一条命令跑完
  kafka_log.csv       # consumer 写出的 20 条
  connect_tunnel.sh   # 开 SSH 隧道
  requirements.txt
  bug_list.md         # 官方常见错误
  助教讲解稿.md
  outputs/            # kcat 和 API 的原始输出
```

若你的 Andrew ID 不是 `helenlwang`，把 `kafka_lab.py` 和 notebook 第一格里的 `andrew_id` 改掉再跑 producer。
