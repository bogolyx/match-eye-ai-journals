---
name: scopeshot
description: SCI 期刊投稿决策（AI + 医学影像/眼科方向）。输入论文初稿（txt/md/docx）或研究思路，输出目标期刊推荐（冲刺-主投两梯队，不收"保底水刊"）、投稿命中率分析（Scope 命中指数 0-100）、以及每本候选刊近 3 年同类论文对比。触发词：投稿期刊推荐、杂志推荐、选期刊、投稿去哪、CCF-A、找同类论文、journal recommendation、投稿SCI。内置期刊数据库（眼科临床、IEEE/CCF-A顶刊、医学影像AI、眼脑/AD交叉、BMC系列、Elsevier系列、CAAI系列），含最新JIF、中科院新锐分区、CCF推荐目录等级、审稿周期、OA费用、Under Review 预警核查；附 scripts/search_similar.py（OpenAlex 检索 + 命中率计算，无需 key）。
agent_created: true
---

# ScopeShot — 论文投稿决策

输入论文初稿（或思路），输出：目标期刊 + 投稿命中率分析 + 同类论文对比。面向 AI + 医学影像（眼科：OCT/OCTA/CFP、眼脑交叉、近视 biomarker）方向研究者。

## ⚠️ 数据版本声明（每次推荐必须先看这里）

本 skill 内置数据版本：
- **影响因子**：2026 年 6 月 17 日 Clarivate 发布的 JCR（统计 2025 年引用数据，学界俗称"2025 JIF"，但行文应称"2026 年最新 JIF"）
- **中科院分区**：2026 年 3 月 24 日发布的《新锐期刊分区表》（最新版）；括号内保留 2025 年 3 月升级版作对照
- **CCF 推荐目录**：第七版（2026-03-05 公示 / 2026-03-31 正式发布 / 2026-04-09 更新）；本次仅 IEEE TMM 与 Bioinformatics 两本期刊升入 A 类
- **JCR 分区**：2026 年 6 月 17 日发布版本
- **预警名单**：中科院自 2026 年起不再单独发布预警名单，改为在《新锐期刊分区表》中标注「under review」并动态更新（2026-03-24 首发 37 种）；**本 skill 的核查基准日期为 2026-09-14，超过 1 个月须重新检索**

**历史教训（务必记住）**：不要在数据版本上犯错。2026 年 6 月这一版相比上一版变化极大，多个期刊跳升 30%+（npj Digital Medicine 12.4→18.0、IEEE TMI 8.9→12.4、Translational Neurodegeneration 10→19.1、JAMA Ophthalmology 9.2→10.5）。引用数据前先确认"这是哪一版"。

**时效规则**：每年 6 月 JCR 更新、每年 3 月中科院分区更新。距上次更新超过 6 个月时，用 WebSearch 核对；用户明确说"帮我查最新的"时，必须实时检索，不要直接用内置数据。

**预警硬约束**：用户明确要求"不能是预警期刊"。推荐任何期刊前必须对照 Under Review 名单排除；Elsevier / MDPI / Frontiers / Springer 各出版方内部都有预警刊，不能按出版社整体判断安全性（Heliyon 就是 Elsevier 的预警刊）。

## 使用流程

### 1. 获取论文信息
用户说"根据我的论文推荐期刊"时，先找初稿文件：
- 询问文件路径，或搜索工作区常见位置（`*.docx`, `*.md`, `*.pdf`）
- 只需读：标题、摘要、方法核心、结论、图表质量描述。不用读全文
- 若没有初稿，问三个问题：①研究类型（临床研究/方法学AI/综述/影像组学）②疾病方向（眼病/AD眼脑/近视）③数据规模（样本量、队列数、是否多中心）

**读稿时要顺手抽出三组检索词**，供第 4 步使用：疾病词（如 `pathologic myopia`）、模态词（如 `OCT angiography`）、方法词（如 `graph attention network`）。

### 2. 稿件分类（决定主攻梯队）
| 稿件类型 | 特征 | 去向 |
|---|---|---|
| A. 临床影像研究 | OCT/OCTA/CFP + 疾病诊断/进展，方法常规（DL分割分类） | 眼科临床期刊为主 |
| B. 方法学AI创新 | 新模型架构、新算法，眼科只是应用场景 | 医学影像AI期刊为主 |
| C. 眼脑交叉/AD | 眼底/OCT biomarker 预测认知、AD 相关 | 神经/AD期刊为主 |
| D. 高度近视 | 病理性近视转变 biomarker | 眼科临床期刊（视网膜向） |

### 3. 输出两梯队推荐（**不要保底档**）

**设计原则：不推保底水刊**（2 分档综合刊、OA 灌水刊、"能发就行"型期刊一律不推）。只给两类：

- **冲刺档**：本方向天花板（IEEE TPAMI/TIP/TMI、MedIA、npj Digital Medicine、Ophthalmology、Alzheimer's & Dementia 等）
- **主投档**：与工作量/新颖度匹配的主力目标（CCF-B/C 的 AI 刊、医学影像 2 区 Top、眼科 1–2 区临床刊、眼脑交叉刊）

若用户稿件确实偏弱，不降档，而是**给出"补什么才能上主投档"的具体建议**（补外部验证集、补消融、补临床效用评估、把方法从应用级提升到方法学级）。

每梯队选 2-3 本，每本给出：
- 名称、最新 JIF、中科院分区（注明分区版本）/JCR分区、**CCF 推荐目录等级（有则必标）**
- **预警状态（必填）**：✅ 不在 Under Review 名单 / ⚠️ 历史预警 / ❌ 在名单
- Scope 契合点（必须具体到论文内容）
- 审稿周期、是否 OA（APC 大概）
- 注意事项（字数限制、报告规范 STARD/TRIPOD 等）

投稿策略：按 冲刺→主投 排列，明确指出"先投哪本、被拒后转投哪本"。

### 4. 同类论文检索 + 投稿命中率分析（**推荐期刊后必做的一步**）

**为什么必做**：期刊的 Aims & Scope 是公关文案，真正能回答"这本刊收不收我这类稿"的，是**它近 3 年有没有发过同类论文**。这一步同时给用户三样东西：投刊可行性证据、可对标的写法/体量、以及审稿人可能的参考文献池。

**执行方式**：调用 `scripts/search_similar.py`（OpenAlex 主源 + Semantic Scholar 兜底，无需 API key）。

```bash
# 方式一：直接给论文文件（txt/md/docx 均可，自动抽检索词）
python scripts/search_similar.py \
  --paper my-draft.docx \
  -j "Ophthalmology Retina" -j "Eye and Vision" -j "IEEE Transactions on Medical Imaging" \
  --years 3 --top 5 --html -o report.html

# 方式二：手工给主题词（更可控，推荐）
python scripts/search_similar.py \
  -q "pathologic myopia OCT biomarker" \
  -q "choroidal thickness myopia progression" \
  -j "Ophthalmology Retina" -j "Eye and Vision" -j "IEEE Transactions on Medical Imaging" \
  --years 3 --top 5 --html -o similar-papers.html
```

**输出自带投稿命中率分析（Scope 命中指数，0–100）**，四个维度：活跃度 /40（近 N 年同类论文总量）、时效性 /20（最新一篇距今多久）、覆盖面 /20（论文的多个主题侧面是否都被该刊覆盖）、相关度 /20（top 命中的检索相关度）。等级：≥75 高（scope 活跃阵地）· 50–74 中（收但非主场）· 25–49 低（偶发收录）· <25 很低（大概率 out-of-scope）。

**必须向用户声明**：命中指数衡量 scope 契合度，**不等于录用概率**——录用还取决于新颖性、实验充分性与写作质量。指数高只说明"这本刊收这类稿"。

**主题词设计规则（决定成败）**：
- 每词 **2–4 个英文词**，别写整句。太长相关度会崩（实测长短语首位结果会漂到无关论文）。
- 给 **3–5 组词**，覆盖论文的不同侧面：疾病词 + 模态词 + 方法词。脚本会自动合并去重。
- **方法词和临床词要分开给**：`"high myopia deep learning"` 和 `"choroidal thickness myopia progression"` 命中的是完全不同的两批论文，前者看方法学空间，后者看临床空间。
- 脚本用的是 OpenAlex 通用 `search=`（相关度排序、宽松匹配）；**不要改成 `title_and_abstract.search=`**——那个是多词 AND 语义，实测同一组词会从 9 篇命中掉到 0 篇。

**结果怎么解读（这是重点，不要只贴表格）**：

| 观测 | 含义 | 建议 |
|---|---|---|
| 命中 20+ 篇 | 该刊是本方向的活跃阵地 | 放心投，但要在叙事上明确与已有工作的差异 |
| 命中 3–10 篇 | 该刊收，但不是主场 | 可投，需把 scope 往该刊主流方向靠 |
| 命中 1–2 篇 | 偶发收录 | 风险中等，投前先读那 1–2 篇，判断它是被当"方法学样例"还是"临床研究"收的 |
| 命中 0 篇 | 该刊近 3 年没发过 | **大概率 out-of-scope 秒拒**，换刊或重构叙事角度 |
| 同刊在"A 组词"命中多、"B 组词"命中 0 | 该刊只收你的某一个侧面 | 按命中的那个侧面写 introduction 和 story |

**必须人工筛一遍**：宽泛主题词（如 `"graph neural network"`）会带进弱相关结果——实测 Information Fusion 会混进股票组合优化、交通流预测；Ophthalmology 按被引排序时榜首会漂到"Disparities in Vision Health"这类大综述。**所以脚本按相关度而非被引量排序**，但输出仍需人工过一遍，只保留真正同类的。

**输出规范**：每刊给两个榜单——① 最相关（按相关度）② 最新（按发表日期，看当前写法与体量）。用 `--html` 生成浅色主题页面，在推荐报告里作为"可行性证据"章节附上。

**常用候选刊分组（直接复制进 `-j`）**：

```bash
# 方法学组（AI 创新为主）
-j "IEEE Transactions on Medical Imaging" -j "Medical Image Analysis" \
-j "IEEE Transactions on Image Processing" -j "Information Fusion" -j "Pattern Recognition"

# 眼科临床组（近视/视网膜）
-j "Ophthalmology" -j "Ophthalmology Retina" -j "Eye and Vision" \
-j "Asia-Pacific Journal of Ophthalmology" -j "British Journal of Ophthalmology"

# 眼脑/AD 组
-j "Alzheimer's & Dementia" -j "Alzheimer's & Dementia: Diagnosis, Assessment & Disease Monitoring" \
-j "Alzheimer's Research & Therapy" -j "BMC Geriatrics"
```

**期刊 ID 已缓存**在 `data/journal_ids.json`，检索结果缓存在 `data/search_cache.json`（TTL 14 天），重复检索不重复请求。

#### 429 限流处理（实战踩过的坑，必读）

OpenAlex 的 `search=` 端点有速率限制。实测被限流时服务端会返回 `Retry-After`，**可能是 30–50 秒，也可能夸张到 60228 秒（≈17 小时）**——必须截断，否则脚本静默挂死。脚本已处理：截断到 50s、最多重试 4 次，仍失败则抛 `RateLimited` 并自动切到 Semantic Scholar 兜底。

**最危险的失败模式（已修，不要改回去）**：限流失败如果被当成"检索成功但 0 篇命中"，报告会宣称"该刊近 3 年没发过这个方向 → 大概率 out-of-scope 秒拒"——**这是把网络故障伪装成投稿建议，会直接误导决策**。因此：
- 每个主题词的失败都会记入 `errors`，报告里显示红色错误块而不是"未检出"
- 全局兜底：若所有期刊都是 0 篇且有错误，脚本打印 `[!!] 严重警告`
- 两个数据源同时失败时，该刊结果标记为无效，不得用于判断 scope

**降低被限流的实用做法**：
- 一次跑 **≤5 本刊 × 2 组主题词**（约 10 次请求）
- 成功过的查询会进缓存，**重跑几乎零成本**；想换榜单直接复用缓存
- 命中 429 时先等 1 分钟再试；连续 429 就停手，隔一段时间再来
- 期刊名解析走 `journal_ids.json` 缓存，不消耗检索配额

**期刊 ID 缓存**已包含：TMI `S58069681`、MedIA `S116571295`、Information Fusion `S7560371`、TIP `S4210173141`、JBHI `S2495854775`、Pattern Recognition `S414566`、Ophthalmology `S207341048`、Ophthalmology Retina `S2764728514`、Eye and Vision `S4210190797`、British Journal of Ophthalmology `S79587146`、CAAI TRIT `S2898415742`、Alzheimer's & Dementia `S108427512`、A&D: DADM `S2898482455`、Alzheimer's Research & Therapy `S140755874`。

### 5. 报告规范
医疗AI类稿件基本都会被要求 TRIPOD+AI / CLAIM / STARD 清单，推荐时主动提醒。

---

## 期刊数据库

### 一、眼科临床期刊（2026 年最新 JIF 全排名，全球 98 本中前 40）

| 期刊 | 2026 JIF | 较上年 | 中科院2026新锐 | JCR | 备注 |
|---|---|---|---|---|---|
| Progress in Retinal and Eye Research | 16.2 | — | — | Q1 | 综述型，约稿为主 |
| Ophthalmology | 10.9 | ↑1.4 | 医学1区 / 眼科学1区 | Q1 | 临床眼科顶刊，大样本 |
| JAMA Ophthalmology | 10.5 | ↑1.3 | 医学1区 / 眼科学1区 | Q1 | 竞争极激烈 |
| Asia-Pacific J Ophthalmology | 7.0 | ↑2.5 | 医学2区 / 眼科学2区 | Q1 | 亚太，上升快 |
| Survey of Ophthalmology | 6.8 | ↑0.9 | 医学1区 / 眼科学1区 | Q1 | 综述驱动 |
| Ocular Surface | 6.6 | — | — | Q1 | 眼表专向 |
| Ophthalmology Retina | 5.9 | ↑0.2 | 医学1区 / 眼科学1区 | Q1 | 视网膜影像临床 |
| **IOVS** | **5.5** | ↑0.8 | 医学3区 / 眼科学2区 | Q1 | ARVO会刊；大类3区是短板 |
| **Eye and Vision** | **5.2** | ↑1.2 | 医学1区 / 眼科学1区 | Q1 | **BMC出版，温医大主办；AI+近视方向极友好** |
| Clinical and Experimental Ophthalmology | 5.1 | ↓0.5 | 医学2区 / 眼科学2区 | Q1 | |
| Ophthalmology Science | 5.0 | ↑0.4 | 医学2区 / 眼科学2区 | Q1 | Ophthalmology 子刊 |
| American J Ophthalmology | 4.7 | ↑0.5 | 医学2区 / 眼科学1区 | Q1 | 老牌，非OA |
| British J Ophthalmology | 4.5 | ↑1.0 | 医学2区 / 眼科学2区 | Q1 | BMJ旗舰 |
| Advances in Ophthalmology Practice and Research | 4.5 | ↑1.1 | 医学2区 / 眼科学2区 | Q1 | 新刊上升快 |
| Eye | 4.4 | — | 医学2区 / 眼科学2区 | Q1 | Nature系，接受面广 |
| Contact Lens & Anterior Eye | 4.2 | — | — | Q1 | 接触镜专向 |
| Ophthalmology and Therapy | 4.2 | ↑1.0 | 医学3区 / 眼科学3区 | Q1 | |
| Eye and Brain | 3.9 | — | — | — | |
| International J of Retina and Vitreous | 3.8 | — | — | — | |
| J of Cataract and Refractive Surgery | 3.7 | — | — | — | 白内障屈光 |
| Ophthalmic and Physiological Optics | 3.4 | — | — | — | |
| Ophthalmology Glaucoma | 3.3 | ↑0.1 | 医学3区 / 眼科学2区 | Q1 | 青光眼专向 |
| Experimental Eye Research | 3.1 | — | — | Q2 | 眼基础 |
| Seminars in Ophthalmology | 3.1 | ↑0.8 | 医学3区 / 眼科学3区 | Q2 | |
| Current Opinion in Ophthalmology | 3.1 | ↑0.5 | 医学3区 / 眼科学3区 | Q2 | 综述 |
| Acta Ophthalmologica | 3.0 | — | — | — | 北欧老牌 |
| Journal of Refractive Surgery | 2.9 | — | — | — | |
| Graefe's Archive | 2.8 | ↑0.5 | 医学3区 / 眼科学3区 | Q2 | 视网膜/影像 |
| **TVST** | **2.7** | — | 医学3区 / 眼科学3区 | Q2 | 视觉科学转化，OA |
| Japanese J of Ophthalmology | 2.7 | ↑0.8 | 医学4区 / 眼科学3区 | Q2 | |
| BMJ Open Ophthalmology | 2.7 | ↑0.5 | 医学3区 / 眼科学3区 | Q2 | BJO姊妹刊，OA |
| Clinical Ophthalmology | 2.5 | ↑0.3 | 医学3区 / 眼科学3区 | Q2 | OA |
| Cornea | 2.3 | — | — | — | 角膜专向 |
| **Retina** | **2.1** | — | — | — | 注意：已从 3.4 档跌至 2.1 |
| BMC Ophthalmology | 2.1 | ↑0.4 | 医学4区 / 眼科学3区 | Q3 | 见 BMC 专区 |
| Journal of Neuro-Ophthalmology | 2.1 | — | — | — | 神经眼科 |
| International J of Ophthalmology | 2.0 | — | — | — | 国人主办 |

### 二、BMC 系列（Springer Nature / BioMed Central）医学期刊专区

**系列特点**：全部 Gold OA；编辑决策明确"不基于研究兴趣度或潜在影响力，只要求科学成立"→ 接收率相对高、审稿快（BMC Ophthalmology 中位首次决定 7 天）；代价是 IF 普遍偏低、部分单位不认可、APC 约 $2,000–3,000。

| 期刊 | 2026 JIF | 较上年 | 中科院2026新锐 | JCR | 与你方向的契合度 |
|---|---|---|---|---|---|
| **Molecular Neurodegeneration** | **19.6** | — | 医学1区Top / 神经科学1区Top | Q1 | AD分子机制，门槛极高 |
| **Translational Neurodegeneration** | **19.1** | — | 医学1区 | Q1 | AD转化；**比旧数据(≈10)高近一倍，别低估门槛** |
| **Journal of Neuroinflammation** | **11.5** | ↑1.4 | 医学1区 | Q1 | 神经炎症机制 |
| **Alzheimer's Research & Therapy** | **8.9** | ↑1.3 | 医学1区Top / 临床神经病学1区+神经科学1区 | Q1 | AD转化研究，眼脑方向首选之一 |
| **BMC Medicine** | **8.7** | — | 医学1区Top / 医学内科1区 | Q1 | BMC旗舰，综合医学 |
| Acta Neuropathologica Communications | 6.5 | — | 医学1区Top / 神经科学2区 | Q1 | 病理机制 |
| J of NeuroEngineering and Rehabilitation | 6.0 | ↑0.8 | 医学2区Top / 康复医学1区 | Q1 | 神经工程/康复 |
| BMC Medical Informatics and Decision Making | 5.5 | ↑1.7 | 医学2区 / 医学:信息3区 | Q2 | 临床决策/信息学 |
| **BMC Geriatrics** | **4.5** | — | 医学2区Top | Q1 | 5年IF 5.2；老年认知+眼影像适配 |
| **BMC Medical Imaging** | **3.9** | ↑0.7 | 医学3区 / 核医学3区 | Q1(JCI) | 影像AI应用，审稿 27 周偏慢 |
| BMC Public Health | 3.6 | — | 医学2区Top | — | 流行病学方向 |
| BMC Neurology | 2.6 | ↑0.4 | 医学3区 / 临床神经病学3区 | Q3 | 临床神经，接受面广 |
| **BMC Ophthalmology** | **2.1** | ↑0.4 | 医学4区 / 眼科学3区 | Q3 | 中位首决 7 天；**设计原则不推此类低分区刊，仅作了解渠道** |

**重要**：BMC 系内真正值得投的是上半张表（Alzheimer's Research & Therapy 8.9、BMC Medicine 8.7、BMC Geriatrics 4.5、BMC Medical Informatics 5.5）；**BMC Ophthalmology / BMC Neurology 这一档按设计原则排除**，不要推。

BMC 投稿建议：Alzheimer's Research & Therapy 和 BMC Medicine 是真·主投档次（1区Top）；BMC Geriatrics 适合老年认知+眼影像。要注意 Springer Nature 的 Read & Publish 协议——国内不少三甲医院/医学院校已覆盖，可通过本单位图书馆确认，覆盖则 APC 为 0。

### 三、Elsevier（爱思唯尔）系列专区

**注意**：Elsevier 并非都安全——**Heliyon** 与 **Biomedicine & Pharmacotherapy** 目前在 Under Review 名单上。选刊不能只看出版社。
**下表每本刊均已逐刊核对 Under Review 名单，全部通过（✅）。**

#### 3.1 模式识别 / AI 方法学（计算机大类）

| 期刊 | 2026 JIF | 中科院2026新锐 | JCR | 预警 | 审稿周期 | 费用/适配 |
|---|---|---|---|---|---|---|
| **Information Fusion** | **15.5** | 计算机科学 **1区Top** | Q1 | ✅ 不在名单 | 6–12 周 | 非OA免版面费；多源/多模态融合。**OCT+gene 异构融合方向首选** |
| **Pattern Recognition (PR)** | **9.1** | 计算机科学 **1区Top**（小类人工智能2区/工程电子电气1区） | Q1 | ✅ 不在名单 | 初审 37 天，投稿→录用 206 天 | 订阅免费；OA 则 APC $3,120。**官网明确拒"常规应用"**，方法必须原创 |
| Engineering Applications of AI | 8.0 | 计算机科学 **1区Top** | Q1 | ✅ 不在名单 | 约 9 周 | 非OA免费；年发文近 2000，应用导向 |
| Knowledge-Based Systems | 8.0 | 计算机科学 **1区Top** | Q1 | ✅ 不在名单 | 约 7.8 个月 | 非OA免费；国人占比约 75%，录用率约 20% |
| Expert Systems with Applications | **9.4** | 计算机科学 **1区Top** | Q1 | ✅ 不在名单 | 约 13.8 个月（最慢） | 非OA免费；年发文 4000+ |
| Neurocomputing | 6.7 | 计算机科学 **2区Top** | Q1 | ✅ 不在名单（2020–2026 各版均不在） | 约 5.7 个月 | 非OA免费；发文量大、门槛适中，稳妥中转站 |
| Pattern Recognition Letters | 3.5 | 计算机科学 3区 | Q2 | ✅ 不在名单 | 约 7.2 个月 | 短文通道，不适合主线成果 |

#### 3.2 医学影像 / 医学信息（医学大类）

| 期刊 | 2026 JIF | 中科院2026新锐 | JCR | 预警 | 备注 |
|---|---|---|---|---|---|
| Medical Image Analysis | **14.0** | 医学 **1区Top**（计算机:AI 1区 / 工程生物医学1区 / 核医学1区） | Q1 (12/210) | ✅ 不在名单 | MICCAI 官方刊；非OA免费；审稿约 5 个月 |
| Artificial Intelligence in Medicine | 7.8 | 医学 **2区Top**（医学:信息2区） | Q1 | ✅ 不在名单（2020–2024 各版均不在） | 要求方法新颖 + 真实临床场景 + 临床效用评估；**审稿约 12 个月** |
| Computer Methods and Programs in Biomedicine | 6.4 | 医学 **2区Top**（小类计算机理论方法1区） | Q1 | ✅ 不在名单 | 方法+软件/工具实现导向，接受度宽 |
| Computers in Biology and Medicine | 6.3 | 医学 2区 | Q1 | ✅ 不在名单 | 审稿约 10 个月 |
| Biomedical Signal Processing and Control | 5.7 | 医学 **2区Top** | Q1 | ✅ 不在名单 | 初审约 10 天；年发文约 1370；国人约 37%，**速度+接受度均衡** |
| Computerized Medical Imaging and Graphics | 5.5 | 医学 2区（工程生物医学2区/核医学2区） | Q1（核医学25/217） | ✅ 不在名单（2020/2021/2023/2024 均不在） | CAD、影像组学、图像引导；审稿约 6 个月 |
| Journal of Biomedical Informatics | ≈5.7 | 医学 2区（医学信息） | Q1 | ✅ 不在名单 | 官方明确"纯信号/图像处理类另投"，注意 scope |

#### 3.3 眼科临床（Elsevier 旗下，与第一节同源）
Progress in Retinal and Eye Research 16.2（邀稿综述）· Ophthalmology 10.9（医学1区/眼科学1区）· Asia-Pacific J Ophthalmology 7.0（Elsevier，亚太友好）· Survey of Ophthalmology 6.8 · Ophthalmology Retina 5.9 · American J Ophthalmology 4.7 · Contact Lens & Anterior Eye 4.2 · Ophthalmology Glaucoma 3.3 · Experimental Eye Research 3.1

#### 3.4 眼脑 / 神经退行（Elsevier）
| 期刊 | 2026 JIF | 中科院2026新锐 | 备注 |
|---|---|---|---|
| Ageing Research Reviews | **15.5** | 医学 **1区Top** | 12.4→15.5；**论著占比仅约 19%，是综述刊，不收原创研究** |
| Progress in Neurobiology | 4.6 | 医学 2区（非Top） | 下跌明显：6.7→6.1→4.6，5年均 7.3 |

### 四、眼科影像 / AI / 信息学（非 Elsevier，作对照）

| 期刊 | 2026 JIF | 较上年 | 中科院2026新锐 | JCR | 备注 |
|---|---|---|---|---|---|
| npj Digital Medicine | **18.0** | ↑2.9 | 医学1区Top | Q1 (1/194) | 数字医疗天花板 |
| Medical Image Analysis | **14.0** | ↑2.2 | 医学1区Top | Q1 (12/210) | 纯方法学，非OA |
| IEEE TMI | **12.4** | ↑2.6 | 医学1区Top | Q1 | 方法新颖度要求极高 |
| IEEE JBHI | **7.7** | — | — | Q1 | 方法应用类可接受 |
| Computers in Biology and Medicine | 6.3 | ↓0.7 | 医学2区(2025版；2026新锐暂无) | Q1 | 审稿约 10 个月，注意周期 |
| **CAAI Transactions on Intelligence Technology** | **5.1** | ↓2.2 | 计算机科学1区 / 人工智能2区（**已退出Top**） | Q2 | APC $2,800；审稿 35 周 |

### 五、眼脑 / AD / 神经退行（非 BMC 系）

| 期刊 | 2026 JIF | 中科院2026新锐 | JCR | 备注 |
|---|---|---|---|---|
| Alzheimer's & Dementia | 12.8 | — | Q1 | 官网数据；眼脑方向天花板 |
| Alzheimer's & Dementia: DADM | 4.9 | 医学2区 / 临床神经病学2区 | Q1 | A&D子刊，**早期诊断/biomarker 极契合** |
| JNNP | — | — | — | BMJ系，神经眼科（投稿前核实最新IF） |
| Aging and Disease | — | — | — | 国人主办（投稿前核实） |
| Translational Neurodegeneration | 19.1 | 医学1区 | Q1 | 见 BMC 专区 |

### 六、IEEE 系列与 CCF-A 顶刊专区（用户核心战场：AI + 医学影像）

#### 6.0 先纠正一个常见误解：CCF-A 是"等级"，不是"范围"

用户常问"**CCF-A 类期刊是不是都可以投**"。答案：**不是。** 两个层面都要看：

1. **CCF-A 里没有几本收医学影像应用论文**。人工智能领域的 CCF-A **只有 4 本期刊**：**AIJ、TPAMI、IJCV、JMLR**（外加 Proc. IEEE，但只收综述）。这 4 本要么是纯视觉/机器学习理论刊（TPAMI/IJCV/JMLR），要么是 AI 综合理论刊（AIJ），**都不收"把网络换个数据集"的医学应用**。
2. **用户已有的主投目标其实不是 CCF-A**：**IEEE TMI 是 CCF-B；Medical Image Analysis 与 IEEE JBHI 是 CCF-C**。所以"投 TMI/MedIA 就是为了 CCF-A"这个前提是错的——它们是医学影像圈的顶刊，但 CCF 等级不高。**医学影像方向的 CCF-A 事实上只有 TPAMI、IJCV、TIP、TMM 这几本有现实可投性。**

**因此推荐逻辑应为：按"论文性质"选刊，而不是按"CCF 等级"选刊。**
- 方法学有普适性（新架构/新损失/新理论，图像只是验证载体）→ 可冲 **TIP / TPAMI / TMM**（CCF-A）
- 方法学只对医学影像成立、需要临床意义背书 → 投 **TMI（B）/ MedIA（C）/ JBHI（C）**，在领域内认可度远高于其 CCF 等级

#### 6.1 CCF 推荐目录（第七版）体系速览

版本：CCF《推荐国际学术会议和期刊目录》**第七版**，2026-03-05 公示、**2026-03-31 正式发布**、2026-04-09 更新。本次调整：新增 14 本期刊、6 本升级、1 本降级。**仅 2 本期刊升入 A 类：IEEE TMM（计算机图形学与多媒体）、Bioinformatics（交叉/综合/新兴）。**

人工智能领域期刊（第七版，完整）：

| 等级 | 期刊 |
|---|---|
| **A** | AIJ（Artificial Intelligence）· TPAMI · IJCV · JMLR |
| B | TAFFC · TASLP · TNNLS · TFS · 等 |
| C | TMI · TETCI · TCDS · Machine Learning · Neural Networks · PR（Pattern Recognition）· 等 |

（TMM 归在"计算机图形学与多媒体"类，不在人工智能类，见下表）

计算机图形学与多媒体领域（第七版）：

| 等级 | 期刊 |
|---|---|
| A | **ACM TOG · IEEE TIP · IEEE TMM（2026 新升 A）· IEEE TVCG** |
| B | CGF · CAD · CAGD · SIIMS · 等 |
| C | CVM · GM · TVC · 等 |

**注意：TMI、MedIA、JBHI 不在"人工智能"或"图形学与多媒体"这两个 A 类主战场上**——TMI/JBHI 在**交叉/综合/新兴**类且是 B/C，MedIA 属 C（且非 CCF 目录中的"人工智能"类）。这是本方向最容易被误解的一点。

#### 6.2 IEEE 期刊逐个点评（含 CCF 等级 + 2026 JIF + 新锐分区 + 预警）

| 期刊 | CCF | 2026 JIF | 中科院2026新锐 | 自引率 | 预警 | 费用/周期 | 适配性 |
|---|---|---|---|---|---|---|---|
| **IEEE TPAMI** | **A** | **20.4** | 计算机科学 1区Top | 3.4% | ✅ | 非OA免费；审稿极慢（半年+） | 纯方法学天花板；异构 GAT / 异构 GAN 若有理论突破可冲 |
| **IEEE TIP** | **A** | **15.3** | 计算机科学 1区Top | ~7% | ✅ | 非OA免费 | **明确包含 biomedical imaging**；图像方法学主战场，本方向最现实的 CCF-A |
| **IEEE TMM** | **A**（2026 新升） | **9.9** | 计算机科学 1区Top | — | ✅ | 非OA免费 | 多媒体；医学影像可投但需多模态/媒体属性；国人占比 90%+ |
| **IEEE TMI** | **B** | **12.4** | 医学 1区Top | 5.6% | ✅ | 非OA免费；审稿约 4–6 月 | **医学影像第一目标**；方法新颖度要求极高，不接受纯应用 |
| **IEEE JBHI** | **C** | **7.7** | — | — | ✅ | 非OA免费 | 方法+应用类可接受，是 TMI 被拒后的主力中转站 |
| **IEEE TNNLS** | **B** | ~10 | 计算机科学 1区 | — | ✅ | 非OA免费 | 神经网络/学习理论；要求普适性 |
| **IEEE TCSVT** | B | ~8.4 | 计算机科学 1区 | — | ✅ | 非OA免费 | 视频技术；OCT 时序（巩膜镜配适）可对口 |
| **IEEE TCYB** | B | ~9 | 计算机科学 1区 | — | ✅ | 非OA免费 | 控制论/仿生；医学 AI 可投但需 cybernetics 视角 |
| **IEEE TKDE** | **A** | ~8.5 | **计算机科学 2区**（2026 新锐） | — | ✅ | 非OA免费 | CCF-A 但分区仅 2 区；知识/数据工程，图学习可对口 |
| **IEEE TVCG / ACM TOG** | **A** | — | 计算机科学 1区 | — | ✅ | 非OA免费 | 可视化/图形；**3D OCT 体积渲染方向若做成可视化方法学可考虑** |
| **IJCV** | **A** | **10.3** | **计算机科学 2区** | — | ✅ | 非OA免费 | CCF-A 但新锐 2 区；计算机视觉，纯方法 |
| **AIJ** | **A** | 4.7 | 计算机科学 2区 | — | ✅ | 非OA免费 | CCF-A 但 2 区；AI 综合理论 |
| **JMLR** | **A** | 6.8 | **计算机科学 3区** | — | ✅ | 免费（Gold OA 无需 APC） | CCF-A 但 3 区；纯机器学习理论，仅适合方法论文章 |
| **Proc. IEEE** | **A** | 30.9 | 综合 1区 | — | ✅ | 非OA免费 | **只收约稿综述**，不适合投原创研究 |

**关键错位结论（推荐时必须点明）**：CCF 等级 ≠ 中科院分区 ≠ 影响因子。TKDE、IJCV、AIJ、JMLR 都是 CCF-A，但中科院新锐分别为 2/2/2/3 区；反过来 TMI 只是 CCF-B，却是医学 1 区 Top、IF 12.4。**国内多数单位职称/毕业认定以中科院分区为准，CCF 等级在计算机学院另算**——给用户推荐时必须两个口径都给，让用户按自己单位的认定标准选。

#### 6.3 与非 IEEE 顶刊的对照（本方向常用）

| 期刊 | 出版方 | CCF | 2026 JIF | 中科院2026新锐 | 预警 |
|---|---|---|---|---|---|
| Medical Image Analysis | Elsevier | C | 14.0 | 医学1区Top | ✅ |
| npj Digital Medicine | Nature 系 | — | 18.0 | 医学1区Top | ✅ |
| Information Fusion | Elsevier | **不在 CCF 目录** | 15.5 | 计算机1区Top | ✅ |
| Pattern Recognition | Elsevier | B | 9.1 | 计算机1区Top | ✅ |
| Alzheimer's & Dementia | Wiley | — | 12.8 | — | ✅ |

**Information Fusion 值得单列**：不在 CCF 目录内（所以既不是 A 也不是 B），但中科院计算机 1 区 Top、IF 15.5、免版面费、审稿 6–12 周——**对"异构 OCT+gene 融合"这类多模态方法学，实际性价比高于多数 CCF-A**。选刊时不要因为"不是 CCF-A"就排除它。

### 七、⚠️ 预警名单核查与避雷清单（必读，每次推荐必须过关）

**机制已变（重要）**：中科院自 2026 年起**不再单独发布《国际期刊预警名单》**，改为把预警机制嵌入《新锐期刊分区表》，对存在学术诚信风险或质量异常的期刊标注「under review」并持续动态更新。**2026-03-24 首发共 37 种**（部分渠道把这 37 种直接称作"2026 版预警名单"）。**不要再去找"单独的预警名单文件"，要查 Under Review 标注。**

**历年预警名单规模（趋势参考）**：2020 版 65 种 → 2021 版 35 种 → 2023 版 28 种 → 2024 版 24 种 → 2025 版 5 种（全部为"论文工厂"问题刊）→ **2026 版 37 种**（嵌入新锐分区表）。2025 年大幅收缩后 2026 年再度扩张，说明核查必要性上升。

**三个查询入口，缺一不可**：
1. 新锐分区 **https://www.xr-scholar.com**（查 under review 标记；免费免登录）
2. 科睿唯安 **https://mjl.clarivate.com**（查 On Hold 状态——与 under review 是两套独立体系）
3. 旧版分区表 **https://fenqubiao.com**（查 2020–2025 历年预警记录）

**名单是动态的。** 本 skill 内的核查基准日期为 **2026-09-14**；距该日期超过 1 个月时，必须重新检索确认，不要直接引用。

**本方向相关、当前在 Under Review 名单上、必须避开（2026-03-24 版 37 种中与本方向有关的部分）**：
- **Heliyon**（Elsevier 旗下综合刊——最容易被当保底刊，实际在名单上）
- **Biomedicine & Pharmacotherapy**（Elsevier，医学类）
- **IEEE Transactions on Intelligent Vehicles**（常被误当"AI 好刊"）
- **Soft Computing / Journal of Intelligent & Fuzzy Systems / Optical and Quantum Electronics**
- **International Journal of Surgery** 全系列（5 本：正刊 / Case Reports / Open / Protocols / Oncology）
- **Annals of Medicine and Surgery**
- **Journal of the Pancreas / Clinical Hemorheology and Microcirculation / Environmental Toxicology**
- **Journal of Computational Methods in Sciences and Engineering / International Journal of Intelligent Engineering Informatics**

**注意**：该 37 种名单中**没有眼科专刊、没有 IEEE TMI/TIP/TPAMI 系、没有 BMC 系、没有 MedIA/PR/Information Fusion**——本方向主流目标期刊目前全部安全。但名单动态更新，引用前需复核日期。

**已核查为安全的期刊组（可放心推）**：
- Elsevier 计算机/AI 组：PR、Information Fusion、Neurocomputing、KBS、ESWA、EAAI、PRL —— 全部无预警记录
- Elsevier 医学影像组：MedIA、AIIM、CMPB、CBM、BSPC、CMIG、JBI —— 均不在名单（CMIG、AIIM 可查 2020/2021/2023/2024 四版均不在）
- Elsevier 眼科组：Ophthalmology、AJO、Survey、Ophthalmology Retina、Asia-Pacific JO、Ophthalmology Glaucoma、Experimental Eye Research 等
- BMC 全系列（含 Eye and Vision）—— 2020–2026 各版均不在名单
- CAAI TRIT —— 无预警记录

**投稿前 5 项自查**：① 是否在最新 Under Review 名单 ② 是否被科睿唯安标记 On Hold ③ 自引率是否超 20% ④ 近 3 年发文量是否暴增 ⑤ 是否仍在 Web of Science Master List

**硬性要求**：用户说"不能是预警刊"时，输出推荐报告里**每本刊都必须带预警状态栏**（✅ 不在名单 / ⚠️ 历史预警 / ❌ 在名单），不允许省略。

### 八、中国人工智能学会（CAAI）系列

| 期刊 | 出版方 | 2026 JIF | 分区 | 定位 |
|---|---|---|---|---|
| CAAI Transactions on Intelligence Technology（TRIT） | Wiley + IET | 5.1（较上年 7.3 明显回落） | 中科院2026新锐：计算机科学1区、小类人工智能2区、**非Top**（2025升级版曾是1区Top） | Gold OA，APC $2,800；审稿 35 周；国人占比 68.8%。医学影像AI应用类可投，但分区优势已不如从前 |
| CAAI Artificial Intelligence Research（AIR） | CAAI + 清华大学出版社 | 暂无 JCR IF（ESCI） | 未入分区 | 高起点新刊，年发文极少，不适合需 IF 的用途 |
| 智能系统学报 | CAAI + 哈工程 | 中文核心 | — | 中文投稿选项 |
| 中国人工智能学会通讯 | CAAI | — | — | 内部刊物 |

### 九、本方向已核实的同类论文先例（实战检索积累，可直接引用为"该刊收这类稿"的证据）

这些是用 `scripts/search_similar.py` 实检得到的结果，可作为投稿时的对标锚点。**每次做新检索后，把有价值的先例追加到这里。**

**异构图表征 / 图注意力方向**
- **IEEE TIP**：*NSB-H2GAN: "Negative Sample"-Boosted Hierarchical **Heterogeneous Graph Attention Network** for Interpretable Classification*（2025，DOI `10.1109/tip.2025.3583127`）—— **异构图注意力网络在 TIP 的直接先例**，且是 GAN + 异构图注意力组合。这条证据说明 heterogeneous GAT 方向在 TIP 有明确收稿路径。
- **Information Fusion**：*Learnable graph convolutional network and feature fusion for multi-view learning*（2023，被引 217，DOI `10.1016/j.inffus.2023.02.013`）—— 图网络 + 特征融合的方法学先例，该刊 TOP 相关命中。
- **Medical Image Analysis**：脑网络方向的图神经网络论文密集（fMRI/DTI/sMRI 多模态 + 可解释 GNN）—— **眼脑/AD 方向走"多模态脑网络图学习"叙事时 MedIA 是活跃阵地**。

**异构 GAN / OCT 生成与分类方向**
- **Medical Image Analysis**：*DTG: Dual transformers-based **generative adversarial networks** for retinal 2D/3D **OCT** image classification*（2025，DOI `10.1016/j.media.2025.103915`）—— GAN + 视网膜 2D/3D OCT 的直接先例。
- **IEEE TMI**：*FIT-Net: Feature Interaction Transformer Network for **Pathologic Myopia** Diagnosis*（2023，DOI `10.1109/tmi.2023.3260990`）—— 病理性近视诊断在 TMI 的先例，说明 TMI 收 PM 的 AI 方法工作。

**眼脑 / AD 方向**
- **IEEE TMI**：*Multi-Modal Diagnosis of Alzheimer's Disease Using Interpretable Graph Convolutional Networks*（2024，DOI `10.1109/tmi.2024.3432531`）—— AD + 多模态 + 可解释图卷积，TMI 直接先例。

**检索得出的 scope 风险结论（重要）**
- **IEEE TMI 对纯临床近视研究基本不收**：`"pathologic myopia OCT biomarker"`、`"choroidal thickness myopia progression"` 在 TMI 近 3 年命中 0 篇。→ 近视临床研究投 TMI 大概率 out-of-scope；若要在 TMI 发，必须把叙事完全转成方法学创新（新架构/新损失/新理论）。
- **Eye and Vision 是近视 + AI 方向的活跃阵地**：同一组词命中 6/20/15 篇，远高于 Asia-Pacific JO（1/5/4）和 TMI（0/0/4）。→ 高度近视方向 Eye and Vision 的 scope 契合度实测最高。
- **Information Fusion 不限定医学**：检索会混入股票组合优化、交通流预测、航空故障诊断等。它是"融合方法学"刊，**投它必须把医学内容降为验证载体、把融合机制升为贡献主体**，否则会被视为应用文而退。

---

## 特殊说明

- **不收保底刊（设计原则）**：Scientific Reports / Diagnostics / Frontiers / BMC Ophthalmology / BMJ Open Ophthalmology / Pattern Recognition Letters 这类"能发就行"型期刊不作为推荐项。稿件偏弱时给"提升方案"而不是"降档方案"。
- **CCF-A 的真相（必答项）**：用户问"CCF-A 类是不是都可以投"时，直接回答：**不是**。AI 领域 CCF-A 只有 AIJ/TPAMI/IJCV/JMLR 四本期刊，都是理论/视觉综合刊，不收医学应用；**TMI 是 CCF-B，MedIA 和 JBHI 是 CCF-C**。医学影像方向真正可投的 CCF-A 是 **TIP（含 biomedical imaging）/ TMM（2026 新升 A）/ TPAMI**。
- **两个口径都要给**：推荐时同时标注"中科院新锐分区"和"CCF 等级"。国内多数单位职称/毕业按中科院分区认定，计算机学院可能另按 CCF 认定；两者常错位（TKDE/IJCV 是 CCF-A 但仅新锐 2 区；TMI 是 CCF-B 但新锐医学 1 区 Top）。
- **眼脑/AD 方向**首选交叉期刊（DADM、Alzheimer's Research & Therapy、BMC Geriatrics），比投纯眼科刊更容易讲出增量故事
- **方法学论文投 TMI/MedIA 失败后**，转 AIIM / CMPB / BSPC / CMIG / IEEE JBHI / TIP，不要投回眼科期刊（会被质疑方法创新不足）
- **多模态融合是 Elsevier 侧的独门路径**：若核心贡献是"异构模态如何融合"（OCT+基因、影像+组学），首选 **Information Fusion**（15.5，计算机1区Top，免版面费，审稿 6–12 周）——与 heterogeneous GAN / UOT 聚合机制类方向高度对口；被拒转 PR / KBS；实用导向转 EAAI。注意它**不在 CCF 目录**，别因为"不是 CCF-A"就排除。
- **3D OCT 体积渲染方向**：若做成可视化方法学，CCF-A 的 **IEEE TVCG / ACM TOG** 是少见的对口正刊；若只是渲染效果展示，应投 TMI/MedIA 而非可视化刊。
- **PR 的隐性门槛**：官网明确声明"常规应用已有方法的论文请另投"，也就是"把 ResNet 换个数据集"必拒，必须在模式识别方法论层面有原创贡献
- **高度近视→病理性近视 biomarker**：Eye、Graefe's Archive、Ophthalmology Retina 匹配好；若样本量充足可冲 Asia-Pacific J Ophthalmology / Ophthalmology
- **APC 友好路径**：① Springer Nature 系（BMC 全系列 + Eye and Vision）多在国内 Read & Publish 协议内，可能 0 费用；② **Elsevier / IEEE 订阅制期刊（PR、Information Fusion、KBS、ESWA、EAAI、Neurocomputing、MedIA、BSPC、CMIG、AJO、Ophthalmology、TPAMI、TIP、TMM、TMI、JBHI）全部免版面费**——这是比 CAAI TRIT（$2,800）和 MDPI（约 $2,600）明显省钱的一条路
- **避雷（务必每次查）**：中科院已改为在《新锐期刊分区表》中标注「under review」，不再单独发预警名单，2026-03-24 首发 37 种。重点避开 Heliyon（Elsevier）、IEEE T-IV、Soft Computing、JIFS、Biomedicine & Pharmacotherapy、Int J Surgery 全系列。眼科/IEEE 影像系目前无一在名单上。
- **数据波动警示**：眼科期刊整体在涨，但 Retina（3.4→2.1）、International J of Ophthalmology（3.5→2.0）、TVST（3.0→2.7）在跌；Progress in Neurobiology（6.7→4.6）也在跌；引用时以当版为准
- **预警状态不明时不要含糊**：若某刊的预警状态无法确认，明确告诉用户"该刊预警状态未核实，投稿前请自行查分区表 Under Review 标注"，不要默认安全

## 输出格式

推荐报告用表格呈现（期刊/JIF/中科院分区/**CCF 等级**/契合理由/审稿周期/APC/预警状态），按 **冲刺→主投** 两梯队分组，最后给一段"投稿路线建议"。**不设保底档。** 报告存为 HTML 或直接在对话中展示。报告中必须标注数据版本与来源日期，并单列一栏预警核查结论。

**报告固定包含三大块**：
1. **期刊推荐表**（冲刺 / 主投，含预警栏）
2. **投稿命中率分析**（Scope 命中指数汇总表 + 各维度分项，由脚本自动生成并置顶）
3. **同类论文可行性证据**（对每本候选刊，给"最相关"与"最新"两个榜单 + 命中数解读），由 `scripts/search_similar.py --html` 生成。命中数为 0 的刊要明确写出"out-of-scope 风险高"。

若用户只给了初步想法（尚无稿件），先问三件事：研究类型、疾病方向、数据规模，再给推荐；同类论文检索可同步做，用来反推用户该往哪个角度写。
