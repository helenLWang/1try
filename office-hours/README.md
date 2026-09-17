# Office hours 投屏讲稿（Unread Recap + Topic Title Improver）

这是给老师看的 **5–10 分钟讲解页**：先走用户能看到的界面，再按「流程图 → 逐文件」对代码。

作业仓库（真正给 Canvas 的 Zulip 树）：

https://github.com/cmu-seai/f26-zulip-lew2

本页是从该提交抽出的演示/讲稿，方便投屏。真机 Zulip 需要本机 Vagrant：`./tools/run-dev` → http://localhost:9991 。

## 怎么开

```bash
cd office-hours
python3 -m http.server 9991
```

浏览器打开 http://localhost:9991 ，用 `hamlet@zulip.com` / `abcd1234` 进入。

## 投屏时怎么切

1. **先演示**：顶部「现场演示」。按页面左侧步骤条点完 Recap 和改标题。
2. **老师要看代码**：顶部「流程图 → 代码」，或右侧「投屏切文件」。GitHub 也可以直接打开对应 path。
3. **老师要看真机录像**：顶部「真机录像」（`./tools/run-dev` 里录的）。

不要说「这是 AI 写的我不懂」。可以说用了 coding tools，但设计决策是你的：不信任模型 URL、不自动改名、没 key 也能跑。
