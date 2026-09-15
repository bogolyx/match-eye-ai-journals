# ScopeShot

**Paper in, journals out.** 输入论文初稿（或一个思路），输出目标期刊推荐、投稿命中率分析、以及该刊近三年同类论文对比。

> Scope + Shot：投稿是对一本期刊"开一枪"。开枪之前，先看清它的 scope。

## 📌 备注：我是哪个 skill / 怎么用我

| | |
|---|---|
| **Skill 名** | `scopeshot`（曾用名 `ophthalmology-journal-recommender`，是同一个东西） |
| **装到哪** | 全局：`~/.workbuddy/skills/scopeshot/`　单项目：`<项目>/.workbuddy/skills/scopeshot/` |
| **装什么** | 整个仓库 → 目标目录（`SKILL.md` + `scripts/` + `data/`，缺一不可） |
| **怎么触发** | 装好后**不用点名 skill**，直接说人话即可，例如：<br>「我写了篇文章想投，帮我选期刊」<br>「这篇稿子适合投哪？初稿在 xxx.docx」<br>「投稿期刊推荐」「帮我找同类论文」 |
| **要不要给东西** | 给**论文初稿**（txt / md / docx 都行）最省事；只给 2–4 组主题词（疾病词 + 模态词 + 方法词）也可以 |
| **要 API key 吗** | ❌ 不需要。数据源 OpenAlex（CC0）+ Semantic Scholar 兜底 |

**识别特征（在别处看到这个仓库时怎么确认是它）**：看产出物里有没有 **"Scope 命中指数（0–100）"** 这个四维打分表（活跃度/40 + 时效性/20 + 覆盖面/20 + 相关度/20）——这是 ScopeShot 的独有标志。

## What it does / 它做什么

给定一篇论文（txt / md / docx，或手动给主题词），ScopeShot 会对每本候选期刊给出：

1. **投稿命中率分析（Scope 命中指数，0–100）** —— 四个维度量化"这本刊近 N 年收不收你这类稿"：
   | 维度 | 分值 | 含义 |
   |---|---|---|
   | 活跃度 | /40 | 近 N 年同类论文总量 |
   | 时效性 | /20 | 最新一篇距今多久（还在收 = 加分） |
   | 覆盖面 | /20 | 你论文的多个主题侧面是否都被该刊覆盖 |
   | 相关度 | /20 | top 命中的检索相关度 |

   等级：≥75 高（scope 活跃阵地）· 50–74 中（收但非主场）· 25–49 低（偶发收录）· <25 很低（大概率 out-of-scope）

   ⚠️ 指数衡量 **scope 契合度**，不等于录用概率——录用还取决于新颖性、实验与写作。

2. **同类论文对比** —— 每本候选刊两个榜单：① 最相关（按相关度）② 最新发表（看当前写法与体量）。这些同时是：投刊可行性证据、可对标的写法、审稿人可能的参考文献池。

3. **期刊数据库（AI + 医学影像方向）** —— 内置眼科临床 / IEEE·CCF 顶刊 / 医学影像 AI / BMC / Elsevier / CAAI 各系列，含最新 JIF、中科院新锐分区、CCF 推荐目录等级、审稿周期、OA 费用、预警（Under Review）核查。见 `SKILL.md`。

## Quick start / 快速开始

无需任何 API key（数据源 OpenAlex，CC0；Semantic Scholar 自动兜底）：

```bash
# 方式一：直接给论文文件（自动抽检索词，支持 txt / md / docx）
python scripts/search_similar.py \
  --paper my-draft.docx \
  -j "IEEE Transactions on Medical Imaging" \
  -j "Medical Image Analysis" \
  -j "Eye and Vision" \
  --years 3 --top 5 --html -o report.html

# 方式二：手动给主题词（2–4 个英文词一组，覆盖论文不同侧面：疾病词 + 模态词 + 方法词）
python scripts/search_similar.py \
  -q "pathologic myopia OCT" \
  -q "heterogeneous graph attention" \
  -q "multi-modal fusion" \
  -j "IEEE Transactions on Medical Imaging" -j "Information Fusion" \
  --html -o report.html
```

输出：控制台 markdown，或 `--html` 浅色主题报告，或 `--json` 结构化数据。

## How it works / 工作原理

```
论文初稿 (.txt/.md/.docx)
   │  自动抽词：标题双词短语（按全文出现次数筛真实术语搭配）+ 高频实词（排除泛词）
   ▼
检索词 × 候选期刊列表
   │  OpenAlex 通用 search=（相关度排序、宽松匹配）
   │  ⚠️ 不用 title_and_abstract.search=（多词 AND 语义，同一组词实测 9 篇 → 0 篇）
   ▼
每刊：同类论文集合（去重合并）
   │  compute_hit_rate(): 活跃度 + 时效性 + 覆盖面 + 相关度 → 0–100
   ▼
报告：命中指数汇总表 + 每刊最相关/最新两个榜单
```

### 可靠性设计（实战踩坑换来的）

- **限流 ≠ 不收稿**：OpenAlex 对 `search=` 端点限流时返回 `Retry-After`（实测从 30 秒到 16 小时都出现过）。脚本截断等待、重试 4 次，仍失败自动切 Semantic Scholar 兜底；**两个源都失败时该刊结果标记为"无效"而不是"0 命中"**——把网络故障伪装成"out-of-scope 拒稿建议"是最危险的失败模式。
- **结果缓存**：期刊 ID 缓存在 `data/journal_ids.json`（已内置 30+ 本常用刊），检索结果缓存 14 天（`data/search_cache.json`，已 gitignore），重跑几乎零成本。
- **礼貌速率**：请求间隔 ≥1 秒，一次建议 ≤5 刊 × 3 词。

## 与 AI 助手配合使用

`SKILL.md` 是一份完整的 agent skill（WorkBuddy / Claude Code 等可读取）：内置期刊数据库、稿件分类逻辑、CCF-A 误区澄清、中科院预警名单核查清单、以及"推荐 → 检索同类论文 → 命中率解读"的完整流程。

### 安装（换台机器/换个助手时）

```bash
# 在 skill 根目录（含 SKILL.md 的目录）执行
git clone https://github.com/bogolyx/scopeshot.git ~/.workbuddy/skills/scopeshot
```

装完确认 `~/.workbuddy/skills/scopeshot/SKILL.md` 存在即可，助手下次启动会自动加载，**不需要手动点名 skill**。

### 日常使用：直接在对话里说

有稿子想投时，不需要记命令，把意图和文件丢给助手就行：

| 场景 | 你直接说 | 助手会做 |
|---|---|---|
| 有新稿子，不知道投哪 | 「我写了篇文章，帮我看看投哪个刊」+ 附初稿 | 分类稿件 → 出冲刺/主投两梯队 + 每刊 Scope 命中指数 |
| 已锁定几本刊，想知道哪本更稳 | 「我打算投 TMI / MedIA / Eye and Vision，帮我比一比」 | 三刊并行检索同类论文 → 命中指数横向对比 |
| 想知道这本刊最近收什么 | 「帮我看看 Information Fusion 近 3 年收不收多模态融合的稿」 | 该刊同类论文两个榜单（最相关 + 最新） |
| 被拒了想转投 | 「TMI 拒了，下一步投哪」 | 依据拒稿理由调整梯队，给转投路径 |
| 稿件偏弱 | 「审稿人说创新性不够，怎么办」 | 给**提升方案**（不给降档到水刊的方案） |

更底层的用法（不经助手、自己跑脚本）见上面 Quick start。

## 期刊数据版本（重要）

- JIF：2026-06-17 Clarivate JCR
- 中科院分区：2026-03-24《新锐期刊分区表》
- CCF 目录：第七版（2026-03-31 发布）
- 预警核查基准：2026-09-14（中科院自 2026 年起不再单独发布预警名单，改为在分区表内标注 "under review"，2026-03-24 首发 37 种）

每年 6 月 JCR 更新、3 月分区更新，引用前请核对最新版本。

## Limitations / 局限

- 命中指数只测 scope 契合度，不预测审稿人对新颖性的判断
- 自动抽词是启发式的，关键投稿决策请人工复核检索词（尤其确认疾病词/方法词都覆盖了）
- 宽泛主题词会带入弱相关结果，榜单需人工筛一遍

## License

MIT
