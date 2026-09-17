# 给 TA 现场演示（真 Zulip）

先找齐项目文件夹，**不要在 `C:\WINDOWS\system32` 里跑任何命令**。  
一次只敲一条，回车，等它结束再敲下一条。不要把两行粘成一行。

`/srv/zulip` 和 `./tools/run-dev` 只存在于 **vagrant ssh 进去之后** 的虚拟机里。你现在还在 Windows 上时，这两条一定会报错。

## 0. 先找到（或重新 clone）仓库

在 PowerShell 里先回用户目录：

```powershell
cd $HOME
dir
```

然后搜有没有现成的 Zulip / 1try / Vagrantfile（可能要等十几秒）：

```powershell
Get-ChildItem $HOME -Recurse -Depth 4 -ErrorAction SilentlyContinue | Where-Object { $_.Name -in @('1try','f26-zulip-lew2','Vagrantfile') } | Select-Object FullName
```

- 若出现某个文件夹里有 `Vagrantfile`：`cd` 进**含有 Vagrantfile 的那个目录**（不要 cd 进 system32）。
- 若搜不到：仓库还不在这台电脑上，在用户目录新建一份（会比较大，要等）：

```powershell
cd $HOME
git clone https://github.com/helenLWang/1try.git
cd 1try
git fetch origin
git checkout cursor/zulip-i1-331d
dir Vagrantfile
```

`main` 分支没有 `Vagrantfile`，必须 checkout `cursor/zulip-i1-331d`。看到 `Vagrantfile` 才算路径对了。

## 1–6. 启动真 Zulip

确认当前目录不是 system32，且 `dir Vagrantfile` 能列出文件之后：

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

用 Cursor 打开你刚才 `cd` 进去、能看到 `Vagrantfile` 的那个文件夹。虚拟机里同一份在 `/srv/zulip/...`。

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
