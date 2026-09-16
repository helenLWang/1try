# I3 作业规格（之后改代码 / 回 PR 用这张表）

**官方原文（唯一标准）：**  
https://github.com/mlip-cmu/f2026/blob/main/assignments/I3_risk.md  
Raw: https://raw.githubusercontent.com/mlip-cmu/f2026/main/assignments/I3_risk.md

**学生提交仓库：** `https://github.com/cmu-seai/f26-risk-lew2`（必须保持 private）  
**已交 Canvas 的 commit（不要无故覆盖）：**  
https://github.com/cmu-seai/f26-risk-lew2/commit/d937c32f3405b6c5f785877c5d42e8587a9a12be

场景：行车记录仪厂商 + 非营利组织做 ChildFind（用 dashcam 录像搜失踪儿童）。人脸/行人识别外包。无直连互联网（USB/蓝牙/Wi-Fi）。法律未定。约 1 次/天 nationwide。用户担心隐私和流量费。管理层对加油站等 edge 感兴趣。

## 助教按 commit 快照评分（不是看最后一次 diff）

根目录必须有：`goals.md` `README.md` `analysis_results.md` `key_results.md` `fault_tree.md`，以及可运行的 LLM 自动化代码。禁止提交 API key。

## 评分表（100 分，多为 pass/fail）

| 分 | 检查什么 |
| ---: | --- |
| 10 | `goals.md`：组织目标（厂商）+ 系统目标（新功能）+ 用户目标（≥3 个利益相关者）+ 模型目标，并写清关系 |
| 10 | `goals.md`：每层至少一个度量，且按 **measure / data / operationalization** 三步写到别人能独立复测 |
| 10 | LLM 工具能跑；`README.md` 写安装、怎么填 key、怎么改利益相关者列表再往下分析；仓库无密钥 |
| 10 | `analysis_results.md`：≥10 个利益相关者及其目标；≥50 条损失/REQ；每条有 ASM/SPEC；追溯链清楚：人→目标→损失→REQ→ASM/SPEC |
| 10 | `key_results.md`：**正好四条**重要或意外的损失+REQ；追溯到 stakeholder 和 goal；列出 ASM 和 SPEC |
| 10 | Jackson 用词：REQ 只写 **world**；ASM 写 world 或 world↔接口映射；SPEC 只写 **接口**；三者合在一起能成立（ASM ∧ SPEC ⊨ REQ） |
| 10 | `fault_tree.md`：从 curated 里选一条依赖 ML 的 REQ；图语法清楚；覆盖该 REQ 的 ASM/SPEC 违规；必须有 **模型预测错误** 事件 |
| 10 | 至少两条 **系统级**缓解（不能只是「多采训练数据」）；说明如何降风险；第二张故障树要体现缓解 |
| 20 | 提交后 2 周内 office hours：能讲清实现；**四条是人选的不是模型顶四**；能答反思题 |

## 自动化范围

只要求自动化 **步骤 2–4**（利益相关者；values/goals/losses→REQ；ASM/SPEC）。要有人在回路（中间可改 JSON）。规模：10–20 个 stakeholder；每人 5–10 条损失/REQ；每条 REQ 3–10 个 ASM/SPEC。

## 之后若有 PR，优先核对

1. 有没有把 REQ 写成「模型准确率 99%」（那是 SPEC）。
2. 缓解是否仍在 ML 组件外。
3. 故障树是否仍包含 wrong prediction，且覆盖 `key_results.md` 里那条 REQ 的 ASM/SPEC。
4. 四条 curated 的「为什么选」是否还在、是否仍能口头讲。
5. 不要把新 commit 误推成 Canvas 要交的唯一 SHA，除非老师要求 resubmit。
