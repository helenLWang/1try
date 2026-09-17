# 给 TA 现场演示（真 Zulip）

先找齐项目文件夹，**不要在 `C:\WINDOWS\system32` 里跑任何命令**。  
一次只敲一条，回车，等它结束再敲下一条。不要把两行粘成一行。

`/srv/zulip` 和 `./tools/run-dev` 只存在于 **vagrant ssh 进去之后** 的虚拟机里。你现在还在 Windows 上时，这两条一定会报错。

## 0. 项目实际在哪

这台电脑上真 Zulip（有 `Vagrantfile`）是：

`C:\Users\13360\f26-zulip-lew2`

不要用 `C:\Users\13360\1try`（没有 Vagrantfile）。不要在 `C:\WINDOWS\system32` 里跑命令。
`Desktop\claude\f26-zulip-lew2` 是另一份拷贝，演示用上面这个即可。

## 1–6. 启动真 Zulip

```powershell
cd C:\Users\13360\f26-zulip-lew2
dir Vagrantfile
```

必须能列出 `Vagrantfile`，然后：

```powershell
vagrant up
```

第一次要等很久。结束后：

```powershell
vagrant ssh
```

提示符变成 `vagrant@zulip-...` 之后（这时才在虚拟机里）：

```bash
cd /srv/zulip
./tools/run-dev
```

这个窗口一直开着。Windows 浏览器打开 http://localhost:9991  
登录：`hamlet@zulip.com` / `abcd1234`  
第二个账号：`iago@zulip.com` / `abcd1234`

## 给 TA 看的文件（相对仓库根目录）

用 Cursor 打开 `C:\Users\13360\f26-zulip-lew2`。虚拟机里同一份在 `/srv/zulip/...`。

| 文件 | 干什么 |
|---|---|
| `web\src\navigation_views.ts` | 左侧栏 Unread recap |
| `web\src\hashchange.ts` | `#recap` 打开弹窗 |
| `web\templates\message_recap_overlay.hbs` | 先出现的框，Generating recap… |
| `web\src\message_recap.ts` | 先骨架，再请求后端 |
| `web\templates\message_recap_body.hbs` | 摘要 + Jump to message |
| `zproject\urls.py` | 两条 API |
| `zerver\views\llm_features.py` | 接口入口 |
| `zerver\lib\message_recap.py` | Recap；Jump 链接用真实 message id 生成 |
| `zerver\lib\llm_client.py` | 读密钥、调 LLM |
| `web\src\compose.ts` | 发送成功后检查标题 |
| `web\src\topic_title_improver.ts` | Rename 提示；点了才改名 |
| `web\templates\compose_banner\topic_title_suggestion.hbs` | Rename topic 条 |
| `zerver\lib\topic_title_improver.py` | 跑题检测 |
| `web\src\ui_init.js` | 启动时挂上两个功能 |
| `zerver\tests\test_llm_features.py` | 测试 |
| `implementation.md` | 书面说明 |
