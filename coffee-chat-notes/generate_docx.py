#!/usr/bin/env python3
"""Generate Chinese coffee-chat study notes as a Word document."""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FONT = "Droid Sans Fallback"
OUT = Path(__file__).resolve().parent / "Coffee_Chat整理与横向对照.docx"


def set_run(run, size=11, bold=False, color=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    if color:
        run.font.color.rgb = RGBColor(*color)


def add_p(doc, text, size=11, bold=False, space_after=6, space_before=0, color=None, align=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.line_spacing = 1.15
    if align:
        p.alignment = align
    run = p.add_run(text)
    set_run(run, size=size, bold=bold, color=color)
    return p


def add_h(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        set_run(run, size={1: 18, 2: 14, 3: 12}.get(level, 12), bold=True)
    p.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    p.paragraph_format.space_after = Pt(8)
    return p


def add_bullets(doc, items, size=11):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(item)
        set_run(run, size=size)


def add_qa(doc, q, a_items):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("问：" + q)
    set_run(r, size=11, bold=True, color=(0x1F, 0x4E, 0x79))
    add_bullets(doc, a_items)


def configure_styles(doc):
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(11)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    for i in range(1, 4):
        h = styles[f"Heading {i}"]
        h.font.name = FONT
        h.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
        h._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    for name in ("List Bullet", "List Number"):
        try:
            st = styles[name]
            st.font.name = FONT
            st._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        except KeyError:
            pass


def main():
    doc = Document()
    configure_styles(doc)
    sec = doc.sections[0]
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.2)
    sec.left_margin = Cm(2.2)
    sec.right_margin = Cm(2.2)

    add_p(
        doc,
        "Coffee Chat 文字记录整理",
        size=22,
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=4,
        color=(0x1F, 0x4E, 0x79),
    )
    add_p(
        doc,
        "只保留事实要点 · 去掉寒暄口水和告别闲聊 · 供对照学习",
        size=11,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
        color=(0x66, 0x66, 0x66),
    )
    add_p(
        doc,
        "整理日期：2026-09-08　　来源：飞书妙记文字记录（浏览器打开后抓取转写）",
        size=10,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=12,
        color=(0x88, 0x88, 0x88),
    )

    add_h(doc, "一、读取情况（先说清楚范围）", 1)
    add_bullets(
        doc,
        [
            "共收到 3 条飞书妙记链接。浏览器实际打开后：第 1 条可匿名查看完整文字记录；第 2、第 3 条跳转飞书登录页，接口返回「object permission request error」，本环境无法登录你的飞书账号，因此这两场没有进入正文。",
            "第 1 场时长 1 小时 34 分 51 秒，转写共 437 段。下文按发言内容还原事实，不补充录音里没说的信息。明显口误/转写错词会在括号里标注最可能的原词，不把猜测写成事实。",
            "说话人未实名。结合标题「aipm 字节火山引擎coffee」和内容：说话人 1 更像 CMU AIPM、正在大量 coffee chat；说话人 2 是火山引擎创作者工具方向的暑期实习同学。下文用「AIPM」和「火山同学」区分。",
            "横向对照一章，只能填上已打开的这一场。第 2、第 3 场待你提供可访问权限（把妙记改成「获得链接的人可查看」，或导出文字记录）后再补差异。",
        ],
    )

    add_h(doc, "二、第 1 场　aipm × 字节火山引擎", 1)
    add_p(doc, "链接：https://bcnir6j13z0f.feishu.cn/minutes/obcnvkh42jj7kv94osb6b37j", size=10, color=(0x66, 0x66, 0x66))
    add_bullets(
        doc,
        [
            "时间：2026-09-06 22:04（页面显示）",
            "时长：1 小时 34 分 51 秒",
            "地点转写：5250 Liberty Ave（公寓公共区域；AIPM 说那边还有温泉）",
            "火山同学：春季入学，这是在当地读的第二个学期，本学期新买了 scooter；此前离开过，AIPM 印象里对方像是 2024 年的人，火山同学解释自己回来美国后已待了快小半年。",
        ],
    )

    add_h(doc, "1. 双方背景（只记自述）", 2)
    add_p(doc, "火山同学", size=12, bold=True, space_before=6, color=(0x1F, 0x4E, 0x79))
    add_bullets(
        doc,
        [
            "03 年出生；日本出生，7 岁回国学中文；18 岁选中国籍，自称北京人。",
            "本科 CS，做过后端开发；现在 CMU，专业侧很 technical（提到 ECE 也很 technical）。项目可选 1.5 年或 2 年，毕业要求是修满学分，没有强制实习，CPT 不受「必须实习才能毕业」那条影响。",
            "2023 年 ChatGPT 出来后判断「coding 再卷不过 AI」，想转到更难被替代、要跟人接触的岗位；认为 2025 年下半年大公司才开始大力招「AI 产品经理」。",
            "路径：大三/大四在百度做传统产品经理 → 一家做了近 20–30 年、有日韩渠道的贸易向小公司实习 → 2026 年暑假在火山引擎实习。",
            "百度体验：大厂实习偏螺丝钉；也说「可能跟组有关，那个组其实能学到很多」。",
            "暑假实习必须回国有具体牵挂；暑假分手后，现在一心想留美国，并补北美实习经历。F1 须连续读满两个学期才能在美合法工作，所以第一年暑假不能在美国实习。",
            "MBTI：AIPM 猜 ENTJ，本人确认。自称符合 CMU 校训 my heart is in the work。",
        ],
    )
    add_p(doc, "AIPM", size=12, bold=True, space_before=8, color=(0x1F, 0x4E, 0x79))
    add_bullets(
        doc,
        [
            "02 年出生；本科学工商管理；大三拿到安永全职 offer，后面一段时间「纯玩」。",
            "安永全职约一年：先在深圳沃尔玛项目（驻点客户总部，审计 / due diligence / 并购报告；那年沃尔玛要并购好又多），干得好会被调到更复杂项目；后做人工心脏医疗项目，约 6 个月换了 3 批人，加班很多，因此临时决定离职留学。",
            "离职后 gap 申请：雅思 19 天、GRE 约一个月；拿到 offer 后去 DeepWisdom 实习。另提过在 Alo 全职一年做 3D 打印牙医相关，以及金融咨询、访谈外国人的经历。",
            "DeepWisdom：中国公司、打北美市场；产品 Atoms，对标 Lovable 一类 vibe coding / 套壳平台；客户全在北美，订阅制；本人做竞品调研和平台优化。实习在深圳。",
            "专业可走 AIE / MLE / SWE，但多数同学口语一般、更想做工程因为更赚钱；真正找 PM 的人很少。",
            "没有「只去大厂」的执念；观察能达到自己想要生活状态的人多是做生意；找工被自己当成跳板，以后想创业。",
            "MBTI：自认比较 F，说自己是 ENTJ，有时是 ENFJ，比例偏中间。做小红书，有 professor 私信，但觉得这类连接怪、不敢发 coffee chat 帖。",
        ],
    )

    add_h(doc, "2. 北美 PM 市场与面试形态", 2)
    add_qa(
        doc,
        "现在找 PM 难不难？Meta 经历有没有用？",
        [
            "AIPM 刚结束一场和 Meta 相关同学的聊：对方讲到深处一直在讲 Meta；结论是就算有 Meta 经历，也没带来明显加成，「job market 就这样」。AIPM 听完「特别心碎」。",
            "两边同意：美国 PM 岗位本身少；国际生语言有劣势。",
            "AIPM 专业交叉（数据分析 + AI tech + business），画像看起来很贴产品，但实际找 PM 的人仍很少。",
        ],
    )
    add_qa(
        doc,
        "PM 要不要技术面 / 算法题？",
        [
            "AIPM 原理解：PM 全是 soft skill，没有 technical 面试。",
            "火山同学：看细分。业务向 PM 不需要很多 technical；技术型 PM 一般不刷力扣、不做算法题，但会问 AI 知识和 vibe coding。",
            "「要跟算法团队对口、所以要做算法题」——火山同学认为应该不需要。",
        ],
    )
    add_qa(
        doc,
        "春季入学为什么不早点铺北美实习？",
        [
            "当时不急：还有两年应届窗口，春季在适应；必须回国，所以暑假回国实习。",
            "上半年完全不了解北美招聘，信息来自暑假和最近的 coffee chat。",
            "现在目标改为全力找北美工作；认为北美实习无论留美还是回国都有用。",
        ],
    )

    add_h(doc, "3. DeepWisdom / vibe coding 产品事实（AIPM 自述，火山同学追问）", 2)
    add_bullets(
        doc,
        [
            "公司名 DeepWisdom；产品 Atoms；竞品包括 Lovable；也会看 Novo 一类 Web coding 做前端的站点。AIPM 认为 Novo 前端实现漂亮，简单后端和 AI integrated 也能做；两边业务「完全一样」。",
            "没有自研模型，被双方说成「套壳」。原定 target 是北美爱 tech 的圈层，后来发现这群人能直接用到更先进的 ChatGPT / 编程工具，不会用第三方套壳。",
            "规模转写为「一百多个人」。刚融完 2.2 亿（轮次：A 轮），正在洽谈下一轮；商业化「也做得不错」。",
            "CEO 无人制衡，处在融资风口，想加视频功能吸引投资。AIPM 查 post call / 数据库：用户没有明确视频意愿；prompt 研究里更多是 Excel、PPT 等多产物需求，再外推到视频。",
            "主要客户是美国 small business。故事线：印刷店先做网站，再想在网站上放 15–30 秒宣传片。火山同学把这概括成「网站 + 宣传片的一站式」；AIPM 同意。",
            "为何不打国内：AIPM 说「不赚钱」；火山同学补充国内太卷、能白嫖就白嫖，北美/日韩支付意愿高、订阅制走得通；国内优势是体量大，但创新点一出现就恶性竞争。",
            "付费结构：AIPM 说约 95% 免费用户、5% 付费且只是小订阅。增长/收入数字转写先后出现「700 美元 ARR」和「700 亿」；火山同学当场质疑「那 OpenAI 都不用做了」。此处只记录原话，未核实。",
            "公司全栈负责人「明哲」反对接视频生成，认为不会带来收入；CEO 坚持。结果「什么都没有阐述出来」（转写如此）。明哲离开创业，产品名转写为 LIBTV / LITV；最近在招实习生、问合同怎么写。AIPM 还说公司很多人最后离职去创业。",
        ],
    )

    add_h(doc, "4. 火山引擎实习：做什么、为什么做", 2)
    add_qa(
        doc,
        "火山这段具体做什么？",
        [
            "不是纯增长。大方向是技术出海 / 日韩；细致领域是创作者工具。",
            "对象：日本漫画家等。把剧本 → 脚本 → 角色/场景/服装 → 关键帧视频 → 配音渲染，收成一个网站，做成服务化矩阵卖给日本客户。",
            "本人做从 0 到 1 的创作者工具 MVP，不是在成熟产品上修功能。组是新赛道。这段实习让他确定以后要走视频生成 / 视频创作 / 创作者工具。",
            "客户对接：以火山名义和日本、韩国企业推合作。",
        ],
    )
    add_qa(
        doc,
        "视频模型格局怎么判断的？",
        [
            "字节 Seedance（转写多次为 C-DAWS / C-DAWS 2.0 / 2.5）：2026 年初 2.0 被称为全球 sota；暑假出 2.5，能力再升一截。国内市占转写为 80% 或 90% 以上，「垄断 / number one」。国内竞品提到 Vidu、海螺、快手；海外提到以前的 Sora（称 OpenAI 已关停该业务）和谷歌 Veo3。",
            "国内纵向做透后要横向出国。日韩还没有自己的生成模型，所以把中国视频生成能力往日韩落地——和他第二段中日韩贸易经历匹配。",
            "约三周前 MiniMax 推出视频模型，转写为 H3：效果约字节的 80%–90%，成本便宜约 40%–50%。格局从一家独大变成 MiniMax 与字节的二元竞争。",
            "技术叙事：2023 文字 → 图（Stable Diffusion，难关已攻克）→ 现在视频（更难、场景更多）。应用：电商宣传片、AI 短剧/漫剧，未来指向影视、电影、动漫。短剧对照横店真人拍摄：演员档期、场地道具；AI 把演员做成数字资产后不需要实体同时在场。",
            "当前 AI 进影视/动漫仍有技术难关没过；「一旦有公司解决，就会大量 AI 生成」。",
        ],
    )
    add_qa(
        doc,
        "为什么锁这个赛道，而不是芯片/机器人？",
        [
            "产品经理要垂直：像行业专家一样懂市场和用户；后端技能可跨电商/娱乐/芯片，产品不行。先用视频创作切入，以后还能转。",
            "三点理由：① 相对少受地缘政治硬对抗（对比芯片卡脖子）；文艺跨文化壁垒小。② 用户面大（手机里已经全是视频），教育素材也需要。③ 个人爱好日本动漫（提到《从零开始的异世界生活》第四季后半、《无职转生》、进击的巨人、鬼灭之刃、咒术回战）；自己没艺术细胞，想给有才能的人做工具，形成「我帮他做工具、他做出我爱看的作品」。",
            "看行业先看赚钱能力。对比自己做的外包/套壳平台：付费用户比例低。",
        ],
    )
    add_qa(
        doc,
        "视频生成的成本、门槛、ToB 还是 ToC？",
        [
            "按生成秒数计费。字节最强也最贵的模型：Seedance 2.0 约「一秒一块钱」人民币；2.5 变成「一秒三块钱」。一集 24 分钟动画粗算：2.0 约 1200 元，2.5 约 3600 元。",
            "对照日本动漫：分 S/A/B/C 档；B 档一集成本「上万级」。3600 对 3 万是数量级下降。对创作者/B 端不算贵，对 C 端可能贵，但已比以前便宜。",
            "火山引擎：把字节内部能力打包卖给中小公司，ToB。即梦：同一技术能力的 ToC 产品。B 端和 C 端 PM 工作内容不一样。",
            "自训视频模型：数据维度文字 < 图 < 视频（24 帧/秒），一般人烧不起。举例：约 1 万刀可能两小时烧完。只有大厂训模型；中小企业用 API 嵌入产品——正是 DeepWisdom 这类公司在做的。",
            "「从 0 到 1」的实话：先 copy 竞品，再结合自身能力找创新点。大厂往往等小公司验证商业模式再进场收割，所以字节启动并不早。国内小公司转写提到「酱友」「点众」「九州文化」，都有创作者平台。字节相对它们的核心差异被他说成「日韩本地化」：国内那套交互/审美不一定适合日韩，而日韩「AI 化程度」被转写成很高。",
        ],
    )
    add_qa(
        doc,
        "北美谁在做？要不要以 TikTok 为北美起点？",
        [
            "谷歌/YouTube：已有 short、中视频、长视频分发，还想做制作，让工作流留在平台。判断视频生成仍在发展、前景大。",
            "TikTok 想拿国内视频生成能力和美国竞争。TikTok 与抖音是独立团队、不同市场、汇报线不同（TikTok 的 VP 不向抖音总裁汇报）。招 TikTok 岗要去 TikTok 招聘站，字节官网没有 TikTok 岗位；字节官网出现的是「国内内部支持 TikTok」的岗。",
            "TikTok 北美已在部署创作者工具。火山同学 10 月要去洛杉矶参加剪映团队的全球创作者活动。招聘站也能看到创作者工具岗位。这也是他来北美的原因之一。",
            "若有更好机会，更想去其他公司，不是绑定回 TikTok。",
            "AIPM 反馈：聊过的 TikTok 人都不想回去。直系学姐在 TikTok 做 AI 相关 AIPM，每天工作到两点左右，在「3 号 c」办公室，不想回日常也不想回。火山同学认识的同专业学姐 Narry 做直播，暑期实习后也说 TT 太痛苦；另一个朋友走 TT 12 周项目则说「非常开心、好幸福」。火山同学认为关键是是否在做自己喜欢的事。",
        ],
    )

    add_h(doc, "5. 大厂文化、创业、职业选择", 2)
    add_bullets(
        doc,
        [
            "互联网「围城」：没进来的想进，进来的想出；光环在淡。",
            "AIPM：受不了只 stable、创造价值少、不 fulfilling 的工作。咨询乙方做报告/方案，不清楚有没有帮到客户，也深不进行业（不是甲方）。找工是跳板。",
            "字节内部口号被概括为「内部创业」；流动快，来去自由，和腾讯/阿里「养老、完善培养、希望你待很久」、华为「体系化、希望后半生贡献给公司」对照。所以字节候选人筛选本身就偏有冲劲、想创业的人；面试字节和其他公司不一样。CMU 被拿来类比：想改变世界的人来，partyschool / 水硕取向的不来。",
            "国内培养：应试下单体执行强、自己想法少，「有人派活就能高效完成」。北美更鼓励探索，想法多、单体能力不一定更强。双方都觉得身边缺少「发自内心要的东西」。",
            "为何转产品（火山同学）：产品细分很多，不是单一工种；下限低、上限高；技术线顶多到技术总裁，仍是高阶打工人；产品能力要素更靠近 CEO / 创业。AIPM 也是「因为产品好创业才做」；本科工商、刷题受不了，不走 SDE/MLE。",
            "创业动机（火山同学）：没想成单一来源，是综合结果；人生观是「来到世界上总得留下痕迹」，要提高影响力。",
        ],
    )

    add_h(doc, "6. 找工动作、CPT/OPT、国内备线", 2)
    add_qa(
        doc,
        "网申够不够？中国学生和美国学生差在哪？",
        [
            "AIPM 同专业同学刚开学，很多人简历还没改，唯一想到的方式是网站 cold apply，命中率低。对中小公司「只点 apply 不够，一定要 outreach、认识内部的人」。",
            "观察：美国学生对找工的重视程度远大于他接触的中国学生。例：Python 课旁边美国人整节课在 Handshake 投岗位，环境都没装；三个创业的美国人会打印简历去 career fair，大胆介绍自己、讲 story；大四刚毕业的美国人简历早就准备好并已投递。中国学生这边基本还没投、简历还没好。",
        ],
    )
    add_qa(
        doc,
        "CPT / 强制实习 / OPT？",
        [
            "火山同学项目无强制实习，毕业看学分；来年可能申请 CPT 去实习。关注 CPT 新政，认为对 AIPM 影响小，因为 AIPM 发邮件确认「还有 CPT」。",
            "AIPM 项目有强制实习，口碑上被火山同学列为北美找工较好的项目之一；另外提到 SCS 下 DS、CV。CMU 很少专业强制实习，AIPM 算例外。硅谷校区 MSSM 也强制实习、学校对接企业，但报更高。",
            "AIPM 还交过 Cornell 留位费，那个项目没有带薪实习。",
            "OPT 风险例：本科室友北卡读生统、找统计师，毕业后提前约四个月申 OPT 被卡住；花 1000 多刀走加急通道仍未审完，已有 offer 无法确认。加急整体约 1000–2000 刀，宣传是 30 天内出结果。校内 CPT 审核相对不经过「到美国那边审」。",
        ],
    )
    add_qa(
        doc,
        "国内还面吗？微信支付怎么样？",
        [
            "火山同学在面国内，「面着玩」：练面试 + 了解业务。第一次面试紧张到喝威士忌微醺，面阿里或腾讯时把女朋友在北京等私事讲出来。他认为面试次数够了会像吃饭喝水。",
            "AIPM 不喜欢连续面试，更靠微信了解；家在深圳，觉得学历不用很好也能进腾讯（地理位置），但听体验后不确定那是想要的生活，还没试过大厂。",
            "AIPM 对微信支付实习的判断：没有留用 HC；团队偏养老；任何 feature 影响用户面太大，创造性工作少；人清北背景、很卷想留用；去年留用的人「特别会舔 mentor」。交大背景、投行一年后转 agent PM 的同事被描述为 ESTJ、加班哭也要算时间。火山同学结论：不去也罢，但国内可当备线，「万一北美不好找」。",
        ],
    )

    add_h(doc, "7. 怎么找人、怎么 coffee chat（可操作方法）", 2)
    add_bullets(
        doc,
        [
            "找工功利是一面；更重要的是搞清自己喜欢什么、擅长什么、将来要做什么，不要被焦虑带跑偏。确定「不喜欢什么」也是收获。喜欢什么只能试错：有好感先冲，做着不喜欢再换。",
            "AIPM 多数 coffee chat 对象是外国人、尤其在北美做 PM 的印度人；中国人里在美做 PM 的太少。英文：跟火山同学一样以听为主也能聊；来美四五天后可以和三个美国人就创业项目畅聊约半小时，状态才打开。火山同学自评 small talk 可以，deep talk 还弱。",
            "认识中国同学的三条路（火山同学）：① 从自己微信列表找方向相关的人，直接约；试错成本低，多数会被拒，面子不值钱。② 朋友的朋友二次引荐（这场就是例子；也可要同专业去了 TT 的学姐联系方式）。③ 自己做小红书，发方向和 coffee chat 信息，让同方向的人来找你。判断私信：先看主页是否像生意号/离谱号；对方应先说自己做什么、想聊什么。",
            "课内：先小组浅层互动，方向贴再约深度 chat。火山同学选那门课，知识其次，目的是找到那波 PM；「几乎都是 PM，纯 tech 不会选」。还用「帮字节朋友在群里问 AIPM」反向吸引 CMU PM，再把 HR/朋友邮件发出去，感兴趣再 call。字节 title 本身就很能吸引人来找。",
            "年轻时在人才密度高的地方多连接「大佬幼龄体」：现在跟 40–50 岁大佬连接成本高、十年后价值不一定匹配；同龄先建立信任，十年后各行各业再合作成本低。AIPM 觉得自己 connect 的中国人不够；火山同学要反过来多 connect 外国人练英语。",
        ],
    )

    add_h(doc, "三、第 2、第 3 场（未能读取）", 1)
    add_p(doc, "第 2 场", size=12, bold=True, color=(0x1F, 0x4E, 0x79))
    add_bullets(
        doc,
        [
            "链接：https://bcnir6j13z0f.feishu.cn/minutes/obcnvjfkno9c12991d991e69",
            "浏览器结果：跳转「飞书 - 登录」（手机号/验证码或 App 扫码）。接口：object permission request error。",
            "正文：无。无法写入任何问答。",
        ],
    )
    add_p(doc, "第 3 场", size=12, bold=True, color=(0x1F, 0x4E, 0x79), space_before=8)
    add_bullets(
        doc,
        [
            "链接：https://bcnir6j13z0f.feishu.cn/minutes/obcnuwblriyykvvn31z44134",
            "浏览器结果：同上，必须登录且当前账号对该妙记无权限。",
            "正文：无。无法写入任何问答。",
        ],
    )
    add_p(
        doc,
        "若要补全：在飞书把这两条妙记的分享权限改成与第 1 条相同（获得链接即可看），或直接导出「文字记录」txt/docx 发过来。补齐后可以把同一张问题表填上另外两列。",
        size=11,
        space_before=6,
    )

    add_h(doc, "四、横向对照：同一类问题，这轮实际听到什么", 1)
    add_p(
        doc,
        "这一张表只反映「你在第 1 场里问过、或双方讨论过的同类问题」。第 2、第 3 列为空，不是没问，是记录打不开。不要把空格脑补成「别人也这么说」。",
        size=11,
        space_after=8,
    )

    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    headers = ["问题（按你这场实际问法归类）", "第 1 场：火山引擎同学", "第 2 场", "第 3 场"]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            for run in p.runs:
                set_run(run, size=10, bold=True, color=(0x1F, 0x4E, 0x79))

    rows = [
        (
            "PM / AI PM 还要不要技术面？",
            "看细分。业务 PM 可以不 technical；技术型 PM 不问算法题，问 AI 知识和 vibe coding。",
            "未能读取",
            "未能读取",
        ),
        (
            "北美 PM 岗位和竞争",
            "岗位少；国际生语言劣势。AIPM 另从 Meta 场听到：大厂经历也无明显加成。",
            "未能读取",
            "未能读取",
        ),
        (
            "为什么转产品 / 为什么选 AI PM",
            "2023 判断 coding 会被 AI 替代；2025 下半年大厂才加码 AI PM；要懂把 AI 能力嵌进真实场景；产品上限更高、更靠近创业。",
            "未能读取",
            "未能读取",
        ),
        (
            "这段实习具体产出",
            "火山创作者工具，日韩漫画家一站式生产管线，本人从 0 到 1 做 MVP，不是修旧功能。",
            "未能读取",
            "未能读取",
        ),
        (
            "赛道怎么选（视频 / 模型 / 应用）",
            "不自训模型（只有大厂烧得起）；做能力落地和本地化。锁视频创作是因为政治摩擦相对小、用户面大、和个人爱好闭环。",
            "未能读取",
            "未能读取",
        ),
        (
            "视频生成贵不贵、卖给谁",
            "按秒计费，2.5 约一秒三块人民币；对动漫 B 端仍远低于传统一集上万。火山 ToB，即梦 ToC。",
            "未能读取",
            "未能读取",
        ),
        (
            "要不要回 TikTok / 大厂",
            "北美创作者工具 TikTok 已在做，10 月有洛杉矶剪映活动；有更好机会想去别的公司。周围 TT 评价两极：有人做到两点不想回，有人 12 周项目很幸福。",
            "未能读取",
            "未能读取",
        ),
        (
            "大厂文化差在哪",
            "字节内部创业、流动快；腾讯阿里培养体系、希望你待久；华为体系化绑定。字节面试本身在筛创业取向。",
            "未能读取",
            "未能读取",
        ),
        (
            "网申 vs 内推 / coffee chat",
            "cold apply 对中小公司不够。美国同学 Handshake / career fair / 讲故事更早动手；中国同学简历和投递普遍更晚。",
            "未能读取",
            "未能读取",
        ),
        (
            "CPT/OPT 和项目结构",
            "无强制实习 → 靠 CPT；有强制实习的项目（如 AIPM、MSSM）找工口碑更好。OPT 加急仍可能卡住 offer。",
            "未能读取",
            "未能读取",
        ),
        (
            "国内是否当备线",
            "火山同学在面（含微信支付）当练习和了解业务；AIPM 认为微信支付无 HC、难创新。共识：北美优先，国内可双线。",
            "未能读取",
            "未能读取",
        ),
        (
            "人怎么找、connection 怎么做",
            "微信列表硬约、朋友引荐、小红书反向获客、PM 课小组深挖。年轻时连同龄高潜，而不是先连 40+ 大佬。",
            "未能读取",
            "未能读取",
        ),
        (
            "产品 vs 技术，和创业的关系",
            "两边都认为产品更适合以后创业。技术线再高也是螺丝钉。创业动机：留下痕迹 / 咨询乙方看不到结果所以要自己做生意。",
            "未能读取",
            "未能读取",
        ),
    ]
    for q, a1, a2, a3 in rows:
        row = table.add_row().cells
        for i, val in enumerate((q, a1, a2, a3)):
            row[i].text = val
            for p in row[i].paragraphs:
                for run in p.runs:
                    set_run(run, size=9)

    add_h(doc, "五、对你的启发（严格从已还原事实里抽，不把空场次写成差异）", 1)
    add_p(
        doc,
        "目前无法比较「同一个问题，三个不同的人怎么答」。能比较的是：你自己在这场里的假设，和火山同学当场给出的不同答案。这些差异已经够用，不必等另外两场才开始改动作。",
        size=11,
        space_after=8,
    )
    add_p(doc, "1. 先改你原先说错的判断", size=12, bold=True, color=(0x1F, 0x4E, 0x79))
    add_bullets(
        doc,
        [
            "「PM 没有技术面」不成立。至少要按业务 PM / 技术型 PM 分开准备：算法题可以不做，AI 概念和 vibe coding 要能讲。",
            "「交叉专业 = 产品人才供给多」不成立。供给画像贴，不代表有人真正在找 PM；口语和薪酬预期会把人推向 AIE/MLE。",
            "「大厂 title（Meta）能显著加分」被你刚结束的另一场直接打脸；本场火山同学也没把字节当成必须回去的终点。Title 能吸引来 coffee chat，不能保证市场。",
        ],
    )
    add_p(doc, "2. 赛道选择：对方给了一套可检验的标准，不是情怀", size=12, bold=True, color=(0x1F, 0x4E, 0x79), space_before=8)
    add_bullets(
        doc,
        [
            "三条同时成立才锁方向：地缘摩擦是否相对小、用户是否已经在用、是否能和自己长期兴趣闭环。芯片/机器人被明确排除在「现在切入」之外。",
            "「从 0 到 1」在大厂语境里 = 晚进入 + copy 竞品 + 找本地化差异，不是从零发明模型。你若讲 DeepWisdom 故事，重点应是用户 prompt 里没有视频需求、CEO 仍因融资去接视频——这是产品判断被资本节奏带跑的实例，和火山同学「先看用户再结合能力」正好相反。",
            "模型层只有大厂；应用层中小公司都能做。你实习的套壳平台属于后者。要问自己的不是「要不要做视频」，而是：5% 付费、95% 白嫖的结构，是不是你愿意再花一年证明的生意。",
        ],
    )
    add_p(doc, "3. 公司选择：同名公司内部的评价已经分裂，不要用一个学姐当结论", size=12, bold=True, color=(0x1F, 0x4E, 0x79), space_before=8)
    add_bullets(
        doc,
        [
            "TikTok：有人做到凌晨两点不想回，有人 12 周项目很幸福，有人只把 TT 当北美创作者工具的入口。差异来自是否在做自己要的赛道，而不是「TT 好或不好」。",
            "字节文化（内部创业、流动快）对想创业的人是筛选器，不是福利。微信支付被你自己判断为无 HC、难创新、清北内卷——如果国内只是备线，面可以面，不要把备线当成主叙事。",
        ],
    )
    add_p(doc, "4. 找工方法：你已经比多数中国同学早，但渠道仍偏单边", size=12, bold=True, color=(0x1F, 0x4E, 0x79), space_before=8)
    add_bullets(
        doc,
        [
            "美国同学的动作更早、更公开（Handshake、career fair、讲 story）。中国同学还停在改简历。你在做 coffee chat，这是对的；缺的是：中国 PM 同学、小红书反向获客、课内 PM 密度更高的课。",
            "对方给的三条获客可以马上用，且都是低成本：微信列表硬约、要二次引荐、发方向帖让人来找你。你卡在「不知道交换点」「不敢发帖」——对方的解法是让对方先报方向，而不是你先深聊。",
            "强制实习/CPT 是你的结构优势，ECE 同学没有。不要把优势睡过去；OPT 加急失败的例子说明 offer 到了签证仍可能掉，时间表要往前排。",
        ],
    )
    add_p(doc, "5. 对你自己这条路径的直接含义", size=12, bold=True, color=(0x1F, 0x4E, 0x79), space_before=8)
    add_bullets(
        doc,
        [
            "你已经能说出不喜欢什么：咨询乙方看不到结果、套壳平台价值没有想象大、纯刷题走不进去、微信支付那种难创新的大厂组不想去。对方认为「知道不喜欢」本身就是进展；下一步不是再找一个 title，而是用同一套问题去问下一场：这个组的用户是谁、付费是否成立、你能不能从 0 到 1 碰到决策，而不是只做竞品调研。",
            "你和对方都把产品当创业训练。差别是：对方已经用日韩创作者工具把「垂直行业专家」做实；你还在用 DeepWisdom 证明「这不是我想做的」。下一场 coffee chat 可以固定问：你现在做的事，一年后会不会变成我可以写进创业假设的行业知识？如果对方答不上来，这场的信息密度会低于本场。",
            "英文 deep talk、中国同学连接、PM 课人选，是本场唯一一组「对方弱、你强 / 你弱、对方强」的互补。可以互换资源：你带外国 PM 聊法，对方带 PM 课和字节侧引荐。这是记录里已经发生的互惠，不是建议你去攀关系。",
        ],
    )

    add_h(doc, "六、本场删掉了什么（避免你复习到噪音）", 1)
    add_bullets(
        doc,
        [
            "开场停车、scooter、公寓公共区域和温泉。",
            "落水、漂流、拍鸭子、不会游泳、德州扑克和深夜回家——只保留与身份相关的一句：日本出生、7 岁回国、18 岁选中国籍、北京人。",
            "重复确认（「对对对」「哦这样」）、互相吹捧、MBTI 闲聊中无信息增量的部分。",
            "未核实的公司财务数字（700 美元 / 700 亿 ARR）不写成结论，只在 DeepWisdom 一节标明转写冲突。",
        ],
    )

    add_p(
        doc,
        "第 2、第 3 场补齐后，把第四节表格的空列填上即可继续对照；不要根据一场的答案推测另外两场。",
        size=10,
        space_before=16,
        color=(0x88, 0x88, 0x88),
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )

    doc.save(OUT)
    print("wrote", OUT, "size", OUT.stat().st_size)


if __name__ == "__main__":
    main()
