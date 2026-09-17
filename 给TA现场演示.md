# 给 TA 现场演示（真 Zulip，不是模拟页）

本仓库 **main** 是别的网站，没有 `Vagrantfile`。真 Zulip 在分支 `cursor/zulip-i1-331d`。先切分支，再按下面 1–6 步启动。

在 **你自己的 Windows** 上打开一个 PowerShell / CMD / Git Bash，窗口不要关。

```bat
cd C:\Users\13360\Documents\1try
git fetch origin
git checkout cursor/zulip-i1-331d
dir Vagrantfile
```

能看到 `Vagrantfile` 再继续。路径不对就用资源管理器点地址栏，复制真实路径替换 `cd` 那一行。

```bat
vagrant up
vagrant ssh
```

进虚拟机后提示符会变成 `vagrant@zulip-...`：

```bash
cd /srv/zulip
./tools/run-dev
```

这个窗口必须一直开着。然后在 **Windows 的 Chrome/Edge** 打开 http://localhost:9991 ，用 `hamlet@zulip.com` / `abcd1234` 登录。第二个账号 `iago@zulip.com` / `abcd1234` 用来制造未读。

代码在 Windows 里改、给 TA 看，用资源管理器 / Cursor 打开 `C:\Users\13360\Documents\1try\...`。虚拟机里同一份文件在 `/srv/zulip/...`（Vagrant 同步过来的）。

## 现场点什么

1. Iago 发一条 → Hamlet 点左侧 **Unread recap** → 先出框再出摘要 → 点 **Jump to message**。
2. 新话题标题 `Weekend plans`，连发 3 条数据库迁移 → 输入框上 **Rename topic** → 点确认（走 Zulip 已有的移动话题）。

## 文件在哪、干什么

Windows 路径前缀一律是 `C:\Users\13360\Documents\1try\`（若你 clone 不在这，只换前缀，后面相对路径不变）。

| 给 TA 看时打开 | 干什么 |
|---|---|
| `web\src\navigation_views.ts` | 左侧栏 **Unread recap**，hash=`#recap` |
| `web\src\hashchange.ts` | `#recap` → `message_recap.launch()` |
| `web\templates\message_recap_overlay.hbs` | 弹窗外壳，先显示 Generating recap… |
| `web\src\message_recap.ts` | 先骨架，再 `GET /json/messages/recap` |
| `web\templates\message_recap_body.hbs` | 摘要和 Jump to message（`href="{{permalink}}"`） |
| `web\styles\message_recap.css` | Recap 样式 |
| `zproject\urls.py` | `GET messages/recap`、`POST messages/topic_title_suggest` |
| `zerver\views\llm_features.py` | 两个接口的入口 |
| `zerver\lib\message_recap.py` | Recap 逻辑；**链接用真实 message id 生成，不信模型 URL** |
| `zerver\lib\llm_client.py` | 读 `api.key` / 环境变量，调 LiteLLM |
| `web\src\compose.ts` | 频道消息发送成功后立刻检查标题 |
| `web\src\topic_title_improver.ts` | 请求建议；点 Rename 调用已有 move topic |
| `web\templates\compose_banner\topic_title_suggestion.hbs` | Rename topic 那条提示 |
| `zerver\lib\topic_title_improver.py` | 跑题检测；没密钥走规则保底；不自动改名 |
| `web\src\ui_init.js` | 启动时 initialize 两个模块 |
| `zerver\tests\test_llm_features.py` | mock LLM；断言 permalink 含 `/near/<id>` |
| `implementation.md` | 书面说明，卡壳时对着念 |
| `api.key.example` | 密钥格式；真正的 `api.key` 在仓库根目录且不进 git |

老师最可能让你打开的两处：

- Jump 链接：`zerver\lib\message_recap.py` 里 `message_permalink()`
- Rename 不会自动改：`web\src\topic_title_improver.ts` 里 `move_topic_containing_message_to_stream(..., "change_all")`
