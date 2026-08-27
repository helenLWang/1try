# 17-445 Lab 1 讲义：Kafka 为什么出现在这门课里

这不是操作备忘录，而是这节 recitation 的讲义。读完你应该能用自己的话向助教说明：生产环境里的数据流是什么、地址（offset）如何保证不丢不重、以及为什么「从头/从尾读」不够用。

---

## 一、这节课的目标

课程后半学期的组项目，是做一个电影推荐系统。系统的输入不是一份静态 CSV，而是用户正在发生的观看行为：谁在看哪部电影、看到第几分钟。这些事件从一台共享的 Kafka 服务器持续涌进来。Lab 1 的全部意义，就是让你在碰到组项目之前，先独立走通「连上这条流、往里写、从里读、从任意位置重放」这一件事。

学完这节课，你应当具备三层能力：

1. **能解释系统**：Kafka 不是聊天室，而是一本只能追加的日志。topic 是这本日志的名字，offset 是每一行的地址。消费者断线后，靠已提交的 offset 从断点继续，所以消息不会因为有人读过就消失。
2. **能操作这条流**：通过 SSH 隧道连上课程 broker，用 Python 写出一批消息再读回来，并用 `seek()` 从日志中间、而不是只从两端开始读。
3. **能用命令行核对**：用 `kcat` 列出 topic，并从某一个绝对 offset（例如 8）消费，证明命令行和 Python 看到的是同一本日志上的同一个地址。

考核方式是 recitation 当场演示并口头解释，不交书面报告。代码已经填好并在课程服务器上跑通过，证据在 `KafkaDemo.ipynb`、`kafka_lab.py`、`kafka_log.csv` 和 `outputs/`。

---

## 二、先建立一个正确的模型，再碰电脑

很多同学第一次听 Kafka，会把它想成「队列」：放进去，拿走，东西就没了。这个模型是错的，后面所有关于断线续读、重放、`auto_offset_reset` 的问题都会绕进去。

正确的模型是：**一本公共的、只能往后写的日志本**。

任何人都可以往这本本子的末尾追加一行（producer）。任何人都可以从某一行开始抄写（consumer）。抄写不会把原件撕掉。多个人可以同时抄，也可以故意从很早以前的某一行重新抄一遍。Kafka 要保证的是：每一行都有一个不会变的整数地址，抄写的人可以记住「我抄到第几行了」，明天接着抄下一行。

在这个模型里，几个词就有了位置：

课程把这本日志放在一台叫 broker 的机器上（`128.2.220.123`）。一本有名字的日志叫做 topic——你的实验 topic 是 `lab01-helenlwang`，组项目读的电影点击流是 `movielog1`。一本日志可以拆成几卷，每一卷叫 partition；本实验只有一卷，所以你暂时不必处理分区。每一卷里，每一行的行号叫做 offset。本次实验写入了 20 行，Kafka 给出的 offset 是 0 到 19。下一行将被写成 20，这个「下一行将要出现的位置」叫做 high watermark（水位线）。

Producer 只做一件事：在末尾追加。Consumer 只做一件事：从某个 offset 开始顺序读。若这个 consumer 属于某个 consumer group，它还可以定期告诉 Kafka「我已经处理到 offset X」，这叫做 commit。进程挂了再回来，group 从 X 的下一行继续。日志本身还在 broker 上，不会因为被读过而删除（只在课程设定的保留期之后才过期）。

这就是助教问「topic 和 offset 如何保证断线后消息连续」时，你要讲的整段话。不是三个孤立定义，而是一件事：有名字的日志、每行有地址、读者记住地址。

---

## 三、为什么必须先打 SSH 隧道

你不能直接访问 `128.2.220.123:9092`。课程故意把 Kafka 放在账号体系之外，再用一条 SSH 隧道把它「借」到你自己电脑的 9092 端口上。这样做有两层用意：安全上不把 broker 暴露给整网；学习上让你的 Python 和 kcat 都连 `localhost:9092`，看起来 Kafka 就像在本地跑。

隧道命令的含义需要讲清楚，不要只会复制：

```bash
ssh -L 9092:localhost:9092 tunnel@128.2.220.123 -NT
```

`-L 9092:localhost:9092` 说的是：把我这台电脑的 9092，转到远端机器自己看到的 localhost:9092。账号是 `tunnel`，密码是 `mlip-kafka`。`-N` 表示不在远端执行任何命令（这个账号本来也没有 shell），`-T` 表示不分配交互终端。所以这个窗口会一直停着、什么都不打印，这是正常的。校外需要先连 CMU VPN，因为服务器在校园网内。

隧道活着，后面所有程序才看得到 broker。`kcat -b localhost:9092 -L` 能列出 topic，就说明第一层目标已经达成：你够到了那本日志。

---

## 四、实验为什么是「写 → 读 → 从中间再读」而不是三道互不相关的题

官方要求看起来像三条 checklist。它们其实是同一条学习路径上的三个检查点，顺序不能反。

**第一段：证明你写进去了。**  
Starter notebook 让你做一个 producer：把若干城市的温度写成 JSON，序列化成字节，发到自己的 topic。Kafka 只收字节，所以 `value_serializer` 必须是「Python 字典 → JSON 文本 → UTF-8 字节」。你加了 Pittsburgh、Shanghai、San Francisco 三个城市，发了 20 条。Broker 给这 20 条分配了 offset 0 到 19。记住这个范围，后面所有「从中间读」都是对着这 20 个地址说话。

**第二段：证明你能按地址读回来。**  
Consumer 连同一个 `localhost:9092`、同一个 topic。这里课程要你理解的不是「for 循环把消息 print 出来」，而是 `auto_offset_reset` 这个参数的真实含义。

它很容易被误解成「从哪里开始读」的旋钮。它不是。它只在一种情况下生效：这个 consumer group 对这个 partition **还没有**一份有效的已提交 offset（新 group，或者旧 offset 已经被日志清理掉了）。而且它只能在日志的**两个端点**里选一个：

- `earliest`：从还保留着的最老一行开始。本实验就是 0。适合要历史、要核对写入是否成功。代价是可能把很久以前的数据再处理一遍。
- `latest`：跳到水位线，只等新写入的行。适合在线服务，不在乎停机那几分钟漏掉的事件。代价是故障窗口内的数据你主动放弃了。
- `none`：没有已提交 offset 就报错。适合你希望「静默跳到某一端」这种事永远不要发生。

本实验用 `earliest`，所以 20 条全部读回，写进 `kafka_log.csv`。读到这里，你已经会写、会读，也知道「没有历史记录时，系统只会把你放到头或尾」。

**第三段：证明你会从中间开始。**  
真实系统几乎从不满足于头或尾。「重放最近 50 条来排查刚才的故障」「从崩溃前 200 条重新处理，以免漏掉未提交的」——这些起点都在日志中间。`auto_offset_reset` 到不了那里。到达那里的方法是 `seek(partition, offset)`。

所以 notebook 要求你先问 broker 有效范围（`beginning_offsets` 是 0，`end_offsets` 是 20，最后一条可读的是 19），再选三个**铺开**的起点，而不是只演示 0 和 19：

- 从 0 读 2 条：这是 `earliest` 自己就能到的地方，用来对照。
- 从 10 读 2 条：这是中点。`auto_offset_reset` 无论取哪个值都到不了，必须 `seek`。
- 从 18 读 2 条：这是「给我最后两条」。`latest` 会把你放到 20（现在是空的），不会放到 18，所以这也必须 `seek`。

助教若问「这三个里哪个 reset 能到、哪个必须 seek」，答案就是上面这一段。课程把这一点写进 2026 的 lab，就是怕学生只会 `earliest` / `latest`，到了组项目不会重放。

**第四段：用另一套工具再确认一次地址。**  
kcat 是同一套日志的命令行入口，不是另一种 Kafka。`-o beginning` 从 0 读，`-o 8` 从绝对地址 8 读。本次运行里，offset 8 是 Pittsburgh、64，和 Python consumer 打印的第 8 条一致。这就是「offset 是跨客户端稳定的地址」的证据。`-e` 表示读到末尾就退出；不加的话 kcat 会继续等新消息，看起来像死机。

到这里，三条官方 deliverable 被收成一句话：**你连上了公共日志，你能在末尾追加，你能用两种工具从任意地址重放。**

---

## 五、现场演示建议怎样讲（一条故事，不要三项报菜名）

校外先开 VPN。第一个终端挂上隧道，不要关。第二个终端进入 `lab01`，激活虚拟环境，运行：

```bash
python kafka_lab.py
```

或者打开 `KafkaDemo.ipynb` 从上到下执行。然后在终端跑：

```bash
kcat -b localhost:9092 -t lab01-helenlwang -C -o beginning -c 5 -e -f "%o: %s\n"
kcat -b localhost:9092 -t lab01-helenlwang -C -o 8 -c 5 -e -f "%o: %s\n"
```

对着屏幕，按这个顺序讲：先指着隧道说明为什么程序连的是 localhost；再指着 producer 的 `0 .. 19` 说明 offset 是 broker 分配的地址；再指着 consumer 说明 `earliest` 为什么能把历史全部拿回来；再指着 seek 的三个起点，明确说出「0 是 earliest 能到的，10 和 18 必须 seek」；最后指着 kcat 从 8 开始的那几行，说明命令行和 Python 认的是同一个地址。

若你的 Andrew ID 不是 `helenlwang`，改 notebook 和 `kafka_lab.py` 里的 `andrew_id` 再跑一次 producer，避免和别人的 topic 撞名。

更完整的口述稿见同目录的 `助教讲解稿.md`。连不上时看 `bug_list.md`：绝大多数错误的第一原因是隧道断了。

---

## 六、这节课怎样接到组项目

Lab 用城市温度当玩具数据，只是为了让 offset 好看、消息好读。组项目里同一套机制读的是 `movielog1`（组确定之后改成你们组的 `movielogN`）。一行长这样：

```text
2026-08-27T18:44:45.585,118511,GET /data/m/fight+club+1999/19.mpg
```

逗号分开的是时间、用户 ID、一次观看请求。用户 ID 是数字，电影 ID 是字符串。Kafka 只告诉你「发生了这件事」；电影片名、类型、用户年龄要再问 HTTP API：

```text
http://128.2.220.123:8080/user/118511
http://128.2.220.123:8080/movie/fight+club+1999
```

一次最多查 200 个 ID，有速率限制。课程规定：除了本 lab 往自己的 `lab01-...` 写，平时只读 Kafka。组项目里你要解析这些行、调用这两个 API、再做推荐——而「从哪一行开始解析」仍然是今天学的 offset 问题。

可选预习：

```bash
kcat -b localhost:9092 -t movielog1 -C -o beginning -c 5 -e -f "%o: %s\n"
```

---

## 七、代码里每个空填了什么（对照官方 TODO）

官方 starter 在 https://github.com/AshrithaG/mlip-kafka-lab 。填写如下，便于你打开 notebook 时知道每一格在完成上面哪一段目标。

- `andrew_id = "helenlwang"`，topic 因此是 `lab01-helenlwang`
- producer / consumer / explorer 的 `bootstrap_servers` 都是 `["localhost:9092"]`（隧道的这一头，不是公网 IP）
- `value_serializer=lambda m: dumps(m).encode("utf-8")`
- 城市：`("Pittsburgh", 64), ("Shanghai", 82), ("San Francisco", 68)`
- `auto_offset_reset="earliest"`
- `first_offset = explorer.beginning_offsets([tp])[tp]`
- `next_offset = explorer.end_offsets([tp])[tp]`
- 三个起点：`first_offset`、中点、`next_offset - 2`

本次真实结果：可读范围 0..19；seek 0 / 10 / 18 各读到两条；kcat `-o 8` 从 Pittsburgh 那条开始，与 Python 一致。
