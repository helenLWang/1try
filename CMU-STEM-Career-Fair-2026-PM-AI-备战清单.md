# CMU STEM Career Fair 2026｜实测清单（AI / Product / Digital intern + 历史上能 sponsor）

> **求职目标：** PM / APM / TPM、AI Product/Strategy、Digital Transformation **实习生**  
> **活动：** STEM Career Fair 2026（Handshake 公开 163 家）  
> **实测日期：** 2026-09-13  
> **数据源：** Handshake 展商 JSON、Greenhouse / Ashby / Lever / BambooHR 职位 API、官网 JD HTTP 状态、DOL H-1B LCA 公开记录（MyVisaJobs / Ellis / bluedoor）

---

## 这次怎么测的（比 Handshake 严）

同时满足才进 **A 表**：

1. **现在真有** 美国站 **AI / Product / Digital** 实习帖（不是纯 SWE intern，不是 2025 旧帖）。
2. **公司历史上有 H-1B LCA**（实习本身走 CPT；这是转正后 sponsor 的证据）。
3. **这条实习 JD 没有写死** 不招 F-1 / 不支持 CPT·OPT / 现在或将来都不赞助签证。

优先级：**官网 JD > 职位 API > Handshake 岗位栏。**  
Handshake 的 `job_titles` 经常是 `None/TBD`，或把全职职称当成实习在招。OPT 开关也不是 JD。

上一版主表约 28 家，**高估了**。实测后，能同时打勾的只有下面这几家。

---

## A. 现在就能投（过测）

| 公司 | 实测岗位 | 直链（2026-09-13 打开） | H-1B 历史 | 备注 |
|---|---|---|---|---|
| **Databricks** | **Product Management Intern (Summer 2027)** | [岗位页 HTTP 200](https://www.databricks.com/company/careers/product/product-management-intern-summer-2027-6883068002) · Greenhouse `6883068002` | 大规模 sponsor（千级 LCA） | Handshake：OPT=True，*willing to sponsor*。JD 未见禁 F-1 条款。**本场最硬的 PM intern。** |
| **Eudia**（Cicero Technologies dba Eudia） | **Product Intern**（Palo Alto） | [Greenhouse HTTP 200](https://job-boards.greenhouse.io/eudia/jobs/4379570009) | FY25 约 16 份 LCA；累计约 17–28；含 Technical Product Manager / AI Engineer | Handshake：OPT=True，*willing to sponsor*。另有 [AI Engineer Intern](https://job-boards.greenhouse.io/eudia/jobs/4020078009)（HTTP 200）。 |
| **C3 AI** | **Data Science Intern (Summer 2027)** | [c3.ai HTTP 200](https://c3.ai/job-description/8738918002?gh_jid=8738918002) | FY25 约 99–106 份 LCA；累计约 340 | 这是 **AI/DS intern**，**不是 PM intern**。同批还有 [SWE Intern](https://c3.ai/job-description/8739037002?gh_jid=8739037002)。展台可问有没有 Product intern，但官网此刻没有。 |
| **Mujin** | **Intern - Product Development (Spring 2027)** | [BambooHR HTTP 200](https://mujin.bamboohr.com/careers/168) | FY23–26 约 25 份 LCA；累计约 35 | 内容偏 **视觉/PLC/硬件 POC**，不是典型软件 PM intern。同期还有 Software Development / Software Integration intern。地点 Suwanee, GA，学期是 **2027 春季**（1/12–4/24），不是暑假。 |
| **Formlabs** | **AI Software Intern (Winter/Spring 2027)** | [Greenhouse HTTP 200](https://careers.formlabs.com/job/8174874/apply/?gh_jid=8174874) | FY25 约 20 份 LCA；含 Senior Product Manager LCA | **AI 软件 intern**，不是 PM intern。Somerville, MA；学期 2027 冬春。 |
| **Phonic** | **Machine Learning Research Intern 2027** | [Ashby HTTP 200](https://jobs.ashbyhq.com/phonic/a6c8c3d2-250a-4c2f-8a20-e4667ca38e41) | 公开 LCA **很薄**（约 1–2 份旧记录，近年几乎没交） | Handshake 勾了 *willing to sponsor*，但历史 sponsor **弱**。这是研究 intern，不是产品 intern。 |
| **Simbe Robotics** | **Computer Vision Intern（Spring & Summer 2027）** | MIT CAPD 仍在招（招到 **2026-09-21**）：[校园帖](https://capd.mit.edu/jobs/simbe-robotics-computer-vision-intern/)；Handshake 挂了 6 个 job_id | FY25 约 4 份 LCA；累计约 13 | **官网 Lever 公开板 16 个岗位里没有 intern**（只有全职 Applied AI）。置信度：校园/Handshake 在招，不是 Greenhouse 那种可直接 HTTP 200 的对外帖。 |

**A 表里真正的 Product intern：Databricks、Eudia、Mujin（偏研发 POC）。**  
AI intern：C3 DS、Eudia AI Eng、Formlabs AI Software、Phonic ML Research、Simbe CV。

---

## B. Handshake 看起来像，但今天打不开对应实习帖

这些公司 **历史上会 sponsor**，Handshake 也标了 Internship / OPT，**不要当成「现在有岗」。**

| 公司 | Handshake 现状 | 实测 |
|---|---|---|
| **Google University Programs** | OPT=True，*willing to sponsor*；岗位栏 `None` | **2027 APM intern 尚未上板**。往年约 10 月初开、窗口约两周。全职 APM 对 F-1 历来更严；实习走 CPT。展台要问开放日，不要假装已经能投。 |
| **Brain Co.** | Job+Internship；职称 AI Product Engineer / AI-ML Engineer | Ashby **34 个岗位全是全职**（含 AI Product Engineer、Product Manager、Early Career ML）。Summer 2026 intern 帖已于 2026-02-27 下架。Handshake 把全职职称标成实习在招，**不准**。H-1B：BrainCo Technologies 在 SF 有少量 FY25–26 LCA。 |
| **BCG X** | FDE AI Scientist/Engineer；OPT=True，*willing to sponsor* | 能搜到的 FDE intern 公开页多为 **欧洲且已 filled**。未能打开美国 2027 intern 直链。BCG 历史上大量 H-1B；实习通常 CPT。展台确认美国循环是否还开。 |
| **Plaid** | Internship，`TBD` | Ashby **110 个岗位，intern = 0**。有一堆全职 PM（含 AI Foundations）。PM intern **历史上有，2027 帖未开**。 |
| **Glean** | Job+Internship，Software Engineer | Greenhouse **118 个岗位，intern = 0**。2026 Admin Console PM intern 是旧循环。 |
| **Klaviyo** | SWE / AI Engineer / ML Engineer | Greenhouse **137 个岗位，intern = 0**。有全职 PM（含 AI Analytics / ML Platform）。Handshake 职称 ≠ 在招 intern。 |
| **Intuit** | 现在只写 **Software Engineering Intern** | 上一版 TPM Intern 链接 **HTTP 404**。官网 internship 搜索此刻只剩 Software Engineer 1，**没有 TPM/PM intern**。Intuit 本身是 H-1B 大户，帖没了就不能算。 |
| **T-Mobile** | Internship，`None` | 实习枢纽页写明：**当前没有开放 intern 角色，季节性发布**。2026 eComm PM intern 是旧帖。 |
| **Rocket** | Job+Internship，`None` | internships 页本次抓取失败/不稳定。2026 Product Development intern 已关；**2027 未证实**。 |
| **Expedia Group** | Job+Internship，`None` | 官网 careers 返回 403，无法点开 2027 PM intern。公开聚合帖是 **2024 已关闭**。PM intern 管道历史上存在，**今天不能投**。 |
| **Gecko Robotics** | Internship；FDE / SWE / Mech / EE | 能找到的 intern 帖是 **Summer 2025 已关闭**。Lever slug 未扫到在招 intern。公司有 H-1B（含 FDE、ML、PM）。 |
| **Instalily** | 未标 intern 类型；职称含 Strategic AI Partner | 在招 intern 是 **GTM-Operations Intern, Events**（活动运营）+ Toronto Co-op。Strategic Partner / Associate 是全职。不算 AI/Product intern。 |
| **Persona / SingleStore** | 标了 Internship | Ashby/Greenhouse **intern = 0**。Handshake 空职称或只写 SWE intern，官网对不上。 |
| **GM / Merck** | 标了 intern；Merck 收 OPT | 岗位栏 `None`。未能打开 Digital Product intern 直链。不要凭 Handshake 类型去排队。 |

---

## C. 美国工程实习是真的，但不是 AI / Product / Digital intern

| 公司 | 实测 | 为什么不进 A |
|---|---|---|
| **Stripe** | [SWE Intern US（SF/Seattle/NYC）HTTP 200](https://stripe.com/jobs/listing/software-engineer-intern-summer-or-winter/8128745) | 工程实习。Greenhouse 未见 Product intern。H-1B 大户。 |
| **The Trade Desk** | Greenhouse intern 帖 [HTTP 200](https://job-boards.greenhouse.io/thetradedesk/jobs/5187605007)（careers 子域那条 404） | **2027 NA Software Engineering Internship**，不是 PM intern。 |
| **Whatnot** | Handshake：SWE Intern / New Grad | 未在公开职位 API 扫到 PM intern。 |
| **AppLovin** | 2027 Backend/Mobile intern **仅新加坡** | 不是美国岗。 |
| **Toast** | SWE Intern **仅都柏林** | 不是美国岗。Handshake 仍写 SWE Intern，容易误判。 |

---

## D. 有匹配实习，但 JD 明确不走 F-1 转正 / 不赞助 —— 已剔除

这些**不是没有岗**。按「要能 sponsor」直接删出队列。

| 公司 | 其实在招 | 实测依据 |
|---|---|---|
| **ZS** | BTS Associate Intern 等（Handshake 挂了一串 Digital/Analytics intern） | 聚合 JD：**This position is not eligible for visa sponsorship** + 须具备现在或将来都不需要雇主赞助的工作许可。Handshake OPT=False。公司历史上有 H-1B，**这条校园实习不算**。 |
| **PwC Advisory** | Summer 2027 Advisory intern 多条（含 Accelerated Solutions Consulting） | 校园政策：**不招现在或将来需要 H-1B lottery 的 entry-level**。Handshake 虽标 OPT=True / willing to sponsor，**以 JD 为准**。 |
| **Capital One** | Product / APM intern | JD：不支持 CPT/OPT/H-1B |
| **Red Ventures** | 2027 APM, AI | JD：不含 F-1 / OPT |
| **P&G** | IT Project & Product Manager intern | JD：Immigration Sponsorship is not available |
| **IBM** | PM Intern 2027 | Handshake 不收 OPT；多条 intern JD 现在或将来不赞助 |
| **Accenture / Cisco / Epic / TCS / MathWorks / Honeywell / GE Vernova** 等 | 见原剔除表 | Handshake 不收 OPT，或 JD 要求 unrestricted work auth |

---

## 优先网申（按实测，不是按品牌）

| # | 岗位 | 直链 |
|---|---|---|
| 1 | Databricks — Product Management Intern (Summer 2027) | https://www.databricks.com/company/careers/product/product-management-intern-summer-2027-6883068002 |
| 2 | Eudia — Product Intern | https://job-boards.greenhouse.io/eudia/jobs/4379570009 |
| 3 | Eudia — AI Engineer Intern | https://job-boards.greenhouse.io/eudia/jobs/4020078009 |
| 4 | C3 AI — Data Science Intern (Summer 2027) | https://c3.ai/job-description/8738918002?gh_jid=8738918002 |
| 5 | Mujin — Product Development Intern (Spring 2027) | https://mujin.bamboohr.com/careers/168 |

紧接着：Formlabs AI Software Intern、Simbe CV intern（走 Handshake/校园帖，9/21 前）、Phonic ML Research Intern（sponsor 弱）。

盯紧但今天不能投：Google APM intern（约 10 月初）、Plaid / Glean / Klaviyo / Expedia / T-Mobile / Rocket 的 2027 PM intern、Brain Co intern 是否重开、BCG X 美国 FDE intern。

---

## 展台怎么走（按证据，不是按 28 家主表）

- **必排队（能投 + 对口）：** Databricks、Eudia。C3 问 DS intern 转 Product/FDE 的路径。  
- **对口但学期/地点要自己接受：** Mujin（春季、佐治亚）、Formlabs（冬春、波士顿）、Simbe（CV intern，9/21 前投 Handshake）。  
- **问「2027 帖哪天开」，不要假装已开：** Google、Plaid、Glean、Klaviyo、Expedia、T-Mobile、Rocket、Brain Co、BCG X。  
- **不要为 PM intern 排长队：** Stripe / Trade Desk / Whatnot / AppLovin / Toast（只有工程实习或海外实习）。  
- **签证口头练一下即可、不要投：** Capital One、ZS、PwC、P&G、IBM、Red Ventures。

---

## 现场 3 个问题

1. 把 agent 嵌进生产时，**哪条评测/治理约束**最先卡住发布？intern 第一个月该建评测集、权限模型，还是客户工作流地图？  
2. Forward Deployed / Consultant / PM **谁拥有 backlog、谁对客户 KPI 签字**？CMU 同学怎样跨到产品决策？  
3. 展台简历是进 **PM intern 队列还是通用工程池**？你希望我圈出用户问题、实验指标，还是系统约束？

---

## 上一版错在哪（方便你对照）

| 上一版说法 | 实测 |
|---|---|
| Intuit 2027 TPM Intern 已开 | **404**；intern 搜索无 TPM/PM intern |
| 主表约 28 家都有匹配实习 | 多数是 Handshake 类型/历史管道，**官网没有对应 intern 帖** |
| ZS / PwC 可走 F-1 | 校园 JD：**这条实习不赞助 / 不招需要 H-1B lottery 的人** |
| Brain Co、Klaviyo、Glean、Plaid 在招 intern | Brain Co / Klaviyo / Glean / Plaid 公开板 **intern = 0** |
| Stripe / Toast / AppLovin / Trade Desk 算 Product intern | 只有 **SWE intern**，Toast/AppLovin 还不是美国岗 |
| T-Mobile / Rocket / Expedia 可投 PM intern | 实习枢纽无开放角色，或 careers 无法打开 2027 帖 |

实习几乎从不直接 sponsor H-1B。上表「能 sponsor」= **公司历史上交过 LCA，且这条实习 JD 没把 F-1 转正路堵死。**
