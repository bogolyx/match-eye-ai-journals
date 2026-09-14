#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search_similar.py — 在指定期刊内检索与论文主题相似的最新/高影响论文。

用途：期刊推荐之后做"落地性验证"——确认该刊是否真的收这类稿，以及同类稿件
在该刊的写法、体量、时间分布。

数据源：OpenAlex（主，免费无 key）+ Semantic Scholar（备，OpenAlex 无该刊时用）

用法示例
--------
# 1) 先在候选期刊里找同类论文
python search_similar.py \
  --query "optical coherence tomography" --query "myopia" --query "choroid" \
  --journal "IEEE Transactions on Medical Imaging" \
  --journal "Medical Image Analysis" \
  --journal "Information Fusion" \
  --years 3 --top 6

# 2) 从论文纯文本自动抽取主题词
python search_similar.py --paper draft.txt --journal "IEEE TMI" --years 3

# 3) 只解析期刊名，不检索（用于确认期刊是否被 OpenAlex 收录）
python search_similar.py --resolve-only --journal "CAAI Transactions on Intelligence Technology"

输出：默认打印 Markdown（便于直接贴进报告）；--json 输出 JSON；--out 写入文件。
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

OA = "https://api.openalex.org"
S2 = "https://api.semanticscholar.org/graph/v1"
MAILTO = "gaohebei@ojlab.ac.cn"  # OpenAlex polite pool
ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT / "data" / "journal_ids.json"
SEARCH_CACHE_PATH = ROOT / "data" / "search_cache.json"
CACHE_TTL_DAYS = 14

STOPWORDS = set("""
a an the and or but of in on at to for from with without by via using use used
is are was were be been being this that these those we our it its as such can
may show shows shown propose proposed present presented new novel based method
methods approach approaches results result paper study wehere however thus also
than then there their they have has had do does did not no only both all any
""".split())

# 泛词：作为短语成分没问题（"graph attention"），但单独作检索词太宽，
# 只在挑选"孤词查询"时排除
GENERIC_WORDS = set("""
framework model models network networks data dataset datasets feature features
prediction predictions task tasks experiment experiments performance comparison
compared improved improvement evaluate evaluated analysis aggregation attention
deep learning neural clinical medical image imaging application applications
proposed demonstrate demonstrates jointly structural risk factors improved
""".split())


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
class RateLimited(Exception):
    """OpenAlex 限流且重试耗尽。调用方应切换到 Semantic Scholar 兜底。"""


def http_json(url, tries=4, timeout=30, max_wait=50):
    """带 429 退避的 JSON 请求。

    OpenAlex 对未鉴权调用有速率限制。**限流绝不能静默变成"0 篇命中"**——
    那会被误读成"该刊不收这个方向"，是会误导投稿决策的严重错误。
    服务端有时返回 Retry-After=60000+ 秒（实测遇到过 60228s，约 17 小时），
    这种必须截断，否则脚本会静默挂死；截断后若仍失败则抛 RateLimited，
    由调用方切到 Semantic Scholar。
    """
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": f"journal-recommender (mailto:{MAILTO})"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429:
                wait = 0
                try:
                    wait = int(e.headers.get("Retry-After") or 0)
                except Exception:  # noqa: BLE001
                    wait = 0
                # 服务端给的 Retry-After 可能大得离谱，必须截断
                wait = min(max(wait, 2 * (i + 1)), max_wait)
                print(f"  [~] 限流 429，等待 {wait}s 后重试（{i + 1}/{tries}）", file=sys.stderr)
                time.sleep(wait)
                continue
            if 500 <= e.code < 600:
                time.sleep(2 * (i + 1))
                continue
            raise
        except Exception as e:  # noqa: BLE001
            last = e
            if i < tries - 1:
                time.sleep(1.5 * (i + 1))
    if isinstance(last, urllib.error.HTTPError) and last.code == 429:
        raise RateLimited("OpenAlex 限流，重试已耗尽")
    raise last


# --------------------------------------------------------------------------- #
# 期刊名 -> OpenAlex source id（带磁盘缓存）
# --------------------------------------------------------------------------- #
def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def load_cache():
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def save_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8"
    )


# --------------------------------------------------------------------------- #
# 检索结果缓存（避免重复请求触发限流）
# --------------------------------------------------------------------------- #
def load_search_cache():
    if SEARCH_CACHE_PATH.exists():
        try:
            return json.loads(SEARCH_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def save_search_cache(c):
    SEARCH_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEARCH_CACHE_PATH.write_text(
        json.dumps(c, ensure_ascii=False), encoding="utf-8"
    )


def cache_get(c, key):
    e = c.get(key)
    if not e:
        return None
    if time.time() - e.get("ts", 0) > CACHE_TTL_DAYS * 86400:
        return None
    return e.get("papers")


def cache_put(c, key, papers):
    c[key] = {"ts": time.time(), "papers": papers}


def resolve_source(name, cache):
    """返回 {'id','name','works','score'}；score 为名称相似度 0-1。"""
    key = norm(name)
    if key in cache:
        return cache[key]

    url = f"{OA}/sources?search={urllib.parse.quote(name)}&per-page=10&mailto={MAILTO}"
    try:
        data = http_json(url)
    except Exception:  # noqa: BLE001
        info = {"id": None, "name": None, "works": None, "score": 0.0}
        cache[key] = info
        save_cache(cache)
        return info

    a = set(norm(name).split())
    best, best_score = None, -1.0
    for s in data.get("results", []):
        b = set(norm(s.get("display_name")).split())
        if not a or not b:
            continue
        score = len(a & b) / len(a | b)
        if norm(s.get("display_name")) == norm(name):
            score = 1.0
        # 优先期刊型 source
        if s.get("type") == "journal":
            score += 0.05
        if score > best_score:
            best_score, best = score, s

    if best and best_score >= 0.45:
        info = {
            "id": best["id"].rsplit("/", 1)[-1],
            "name": best.get("display_name"),
            "works": best.get("works_count"),
            "score": round(min(1.0, best_score), 2),
        }
    else:
        info = {
            "id": None,
            "name": best.get("display_name") if best else None,
            "works": best.get("works_count") if best else None,
            "score": round(best_score, 2) if best_score > 0 else 0.0,
        }
    cache[key] = info
    save_cache(cache)
    return info


# --------------------------------------------------------------------------- #
# 检索
# --------------------------------------------------------------------------- #
def search_in_source(sid, queries, from_date, per_query=100, scache=None):
    """在给定 source 内按多个主题词检索，合并去重。

    关键：使用 OpenAlex 通用 `search=` 参数（相关度排序，词间为 OR 式宽松匹配），
    而不是 `title_and_abstract.search=`（多词为 AND，极易漏检）。
    实测同一组词：AND 语义命中 0 篇，通用 search 命中 9 篇且首位高度相关。

    返回 (papers, errors)。errors 非空说明有查询失败，结论不可信。
    命中 429 且重试耗尽时抛 RateLimited，由调用方切换 Semantic Scholar。
    """
    found = {}
    errors = []
    scache = scache if scache is not None else {}
    for q in queries:
        safe_q = q.replace(",", " ").strip()
        ckey = f"{sid}|{safe_q}|{from_date}|{per_query}"
        cached = cache_get(scache, ckey)
        if cached is not None:
            print(f"  [c] 「{q}」命中缓存 {len(cached)} 篇", file=sys.stderr)
            for w in cached:
                found.setdefault(w["_id"], w)
            continue

        enc = urllib.parse.quote(safe_q, safe="")
        flt = (
            f"primary_location.source.id:{sid},"
            f"from_publication_date:{from_date},"
            f"type:article"
        )
        url = (
            f"{OA}/works?filter={flt}&search={enc}"
            f"&per-page={per_query}"
            f"&select=id,title,publication_year,publication_date,doi,cited_by_count,"
            f"primary_location,type,relevance_score&mailto={MAILTO}"
        )
        try:
            data = http_json(url)
        except RateLimited:
            raise
        except Exception as e:  # noqa: BLE001
            errors.append(f"{q}: {e}")
            print(f"  [!] 检索失败 ({q}): {e}", file=sys.stderr)
            continue

        hits = data.get("results", [])
        print(f"  [·] 「{q}」命中 {data.get('meta', {}).get('count', '?')} 篇", file=sys.stderr)
        row_cache = []
        for w in hits:
            wid = w.get("id")
            if not wid:
                continue
            doi = (w.get("doi") or "").replace("https://doi.org/", "")
            item = {
                "_id": wid,
                "title": (w.get("title") or "").strip(),
                "year": w.get("publication_year"),
                "date": w.get("publication_date"),
                "doi": doi,
                "cites": w.get("cited_by_count") or 0,
                "score": round(w.get("relevance_score") or 0, 1),
                "url": w.get("doi") or wid,
            }
            row_cache.append(item)
            if wid in found:
                found[wid]["hits"].add(q)
            else:
                found[wid] = dict(item, hits={q})
        cache_put(scache, ckey, row_cache)
        time.sleep(1.0)  # 保持礼貌速率，避免触发 429

    for v in found.values():
        v["hits"] = sorted(v["hits"])
    return list(found.values()), errors


def search_s2(venue_name, queries, from_year, top):
    """OpenAlex 未收录或限流时的兜底（Semantic Scholar）。

    返回 (papers, errors)。**必须先记录 errors 再判断空结果**——
    两个数据源同时失败时若返回空列表，报告会错误地宣称"该刊不收这个方向"。
    """
    out = {}
    errors = []
    for q in queries:
        url = (
            f"{S2}/paper/search?query={urllib.parse.quote(q)}"
            f"&venue={urllib.parse.quote(venue_name)}"
            f"&year={from_year}-&limit={top * 3}"
            f"&fields=title,year,venue,externalIds,citationCount"
        )
        try:
            data = http_json(url, tries=2, max_wait=8)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{q}: {e}")
            print(f"  [!] S2 兜底也失败 ({q}): {e}", file=sys.stderr)
            continue
        for p in data.get("data", []) or []:
            doi = (p.get("externalIds") or {}).get("DOI", "")
            out[p.get("paperId")] = {
                "title": (p.get("title") or "").strip(),
                "year": p.get("year"),
                "date": None,
                "doi": doi,
                "cites": p.get("citationCount") or 0,
                "score": 0,
                "url": f"https://doi.org/{doi}" if doi else "",
                "hits": [q],
                "via": p.get("venue"),
            }
        time.sleep(1.2)
    return list(out.values()), errors


# --------------------------------------------------------------------------- #
# 从论文文本抽主题词
# --------------------------------------------------------------------------- #
def read_paper(path):
    """读取论文文件。支持 txt / md；docx 自动解包 word/document.xml 提取文本。"""
    p = Path(path)
    if p.suffix.lower() == ".docx":
        import zipfile

        with zipfile.ZipFile(p) as z:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
        # 段落边界还原为换行，其余标签剥掉
        xml = re.sub(r"</w:p>", "\n", xml)
        return re.sub(r"<[^>]+>", "", xml)
    return p.read_text(encoding="utf-8", errors="replace")


def keywords_from_text(text, limit=8):
    """从论文文本抽检索词：标题实词优先 + 高频双词短语 + 全文高频词。

    OpenAlex 的 search= 对 2-4 词短语的相关度最好，孤词太宽，
    所以这里除了高频孤词，还把标题里的相邻实词组成短语。
    """
    text = re.sub(r"\s+", " ", text)
    title = text.split("\n")[0] if "\n" in text else text[:300]

    # 标题相邻实词 → 双词短语（如 "pathologic myopia"、"graph attention"）
    def words(s):
        return [
            t.lower()
            for t in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", s)
            if t.lower() not in STOPWORDS and len(t.lower()) >= 4
        ]

    title_words = words(title)
    # 标题相邻实词 → 双词短语，按"该短语在全文出现次数"排序：
    # 出现 ≥2 次的是真实术语搭配（如 "pathologic myopia"、"graph attention"），
    # 只出现 1 次的往往是标题里的凑合词（如 "fusing genetic"）
    low_text = text.lower()
    cand = []
    for i, (a, b) in enumerate(zip(title_words, title_words[1:])):
        cnt = low_text.count(f"{a} {b}")
        cand.append((cnt, -i, f"{a} {b}"))
    cand.sort(reverse=True)
    phrases, used = [], set()
    for cnt, _, ph in cand:
        a, b = ph.split()
        if cnt < 1:
            continue
        if a in used or b in used:
            continue
        phrases.append(ph)
        used.update((a, b))
        if len(phrases) >= 3:
            break

    # 全文高频孤词（排除泛词：单独作查询太宽，如 "framework"、"attention"）
    freq = {}
    for t in words(text):
        freq[t] = freq.get(t, 0) + 1
    singles = [
        w
        for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
        if w not in GENERIC_WORDS
    ]

    # 组合：先标题短语（覆盖不同侧面），再补高频孤词
    out = phrases[:3]
    for w in singles:
        if w not in out and len(out) < limit:
            out.append(w)
        if len(out) >= limit:
            break
    return out


# --------------------------------------------------------------------------- #
# 输出
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# 命中率分析（Scope 命中指数）
# --------------------------------------------------------------------------- #
def compute_hit_rate(papers, queries, errors, today=None):
    """Scope 命中指数（0-100）：该刊近 N 年收不收这类稿的量化估计。

    四个维度：
      活跃度 40 分 —— 近 N 年同类论文总量
      时效性 20 分 —— 最新一篇距今多久（还在收 = 加分）
      覆盖面 20 分 —— 多少组主题词在该刊有命中（论文的多个侧面都被覆盖）
      相关度 20 分 —— top-3 命中的 OpenAlex relevance_score 归一

    ⚠️ 该指数衡量 scope 契合度，不等于录用概率：录用还取决于新颖性、
    实验充分性、写作质量与审稿运气。指数高只说明"这本刊收这类稿"。
    """
    today = today or date.today()
    if errors and not papers:
        return None  # 检索失败，数据无效，绝不能算成 0 分
    n = len(papers)

    # ① 活跃度 /40
    if n >= 30:
        act = 40
    elif n >= 20:
        act = 34
    elif n >= 10:
        act = 27
    elif n >= 5:
        act = 20
    elif n >= 3:
        act = 12
    elif n >= 1:
        act = 5
    else:
        act = 0

    # ② 时效性 /20
    rec = 0
    dates = [p.get("date") for p in papers if p.get("date")]
    if dates:
        try:
            nd = date.fromisoformat(max(dates)[:10])
            months = (today - nd).days / 30.4
            rec = 20 if months <= 12 else 14 if months <= 24 else 8 if months <= 36 else 3
        except ValueError:
            rec = 8

    # ③ 覆盖面 /20
    groups = {h for p in papers for h in (p.get("hits") or [])}
    bread = round(20 * len(groups) / max(1, len(queries)))

    # ④ 相关度 /20（S2 兜底无 relevance_score 时跳过并重新归一到 80 分制）
    scores = [p.get("score") or 0 for p in papers]
    top3 = sorted(scores, reverse=True)[:3]
    if top3 and max(scores) > 0:
        rel = round(20 * min(1.0, sum(top3) / len(top3) / 120))
        total = act + rec + bread + rel
        rel_txt = f"{rel}"
    else:
        rel = None
        total = round((act + rec + bread) / 80 * 100)
        rel_txt = "—"

    if total >= 75:
        grade, verdict = "高", "scope 活跃阵地，放心进入候选"
    elif total >= 50:
        grade, verdict = "中", "该刊收但非主场，叙事需向其主流方向靠拢"
    elif total >= 25:
        grade, verdict = "低", "偶发收录，投前精读那几篇先例再定"
    else:
        grade, verdict = "很低", "大概率 out-of-scope，建议换刊或重构叙事"

    return {
        "score": total,
        "grade": grade,
        "verdict": verdict,
        "activity": act,
        "recency": rec,
        "breadth": bread,
        "relevance": rel,
        "n": n,
        "groups": len(groups),
        "rel_txt": rel_txt,
    }


GRADE_COLOR = {"高": "#1a7f37", "中": "#b58900", "低": "#d97706", "很低": "#c0392b"}


def render_md(results, years, top, queries=None):
    queries = queries or []
    lines = []
    # ---- 命中率汇总表 ----
    rates = {}
    for journal, block in results.items():
        rates[journal] = compute_hit_rate(
            block["papers"], queries, block.get("errors") or []
        )
    if rates:
        lines.append("## 投稿命中率分析（Scope 命中指数）")
        lines.append("")
        lines.append(
            "> 指数衡量 **scope 契合度**（该刊近 "
            f"{years} 年收不收这类稿），**不等于录用概率**——录用还取决于新颖性、实验与写作。"
        )
        lines.append("")
        lines.append("| 期刊 | 命中指数 | 等级 | 活跃度/40 | 时效/20 | 覆盖/20 | 相关/20 | 解读 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for j, r in sorted(
            rates.items(), key=lambda kv: -(kv[1]["score"] if kv[1] else -1)
        ):
            if r is None:
                lines.append(f"| {j} | — | ⚠️ 无效 | — | — | — | — | 检索失败，不可用于决策 |")
            else:
                lines.append(
                    f"| {j} | **{r['score']}** | {r['grade']} | {r['activity']} | "
                    f"{r['recency']} | {r['breadth']} | {r['rel_txt']} | {r['verdict']} |"
                )
        lines.append("")
        lines.append("---")
        lines.append("")

    for journal, block in results.items():
        info = block["source"]
        lines.append(f"### {journal}")
        r = rates.get(journal)
        if r:
            lines.append(
                f"> **Scope 命中指数：{r['score']}/100（{r['grade']}）** —— {r['verdict']}"
            )
        if info.get("id"):
            lines.append(
                f"> OpenAlex 收录：{info['name']}（source id `{info['id']}`，"
                f"全刊累计 {info.get('works') or '—'} 篇，名称匹配度 {info.get('score')}）"
            )
        else:
            lines.append(
                f"> ⚠️ OpenAlex 未收录该刊（匹配到的最近似刊：{info.get('name') or '无'}）；"
                f"结果来自 Semantic Scholar 兜底"
            )
        papers = block["papers"]
        errors = block.get("errors") or []
        lines.append(f"> 近 {years} 年匹配到 **{len(papers)}** 篇同类论文")
        if errors:
            lines.append(
                f"> ❌ 有 {len(errors)} 个主题词检索失败，**本篇结论不可用于决策**，请重跑或换词"
            )
        lines.append("")

        if not papers:
            if errors:
                lines.append("_检索未成功完成（见上方警告），不要据此判断该刊范围。_")
            else:
                lines.append(
                    "**未检出同类论文** —— 该刊近 "
                    f"{years} 年几乎没有这个方向的稿件，投稿被以 out-of-scope 直接拒的风险偏高。"
                    "建议：换刊，或把叙事重心从「临床问题」移到「方法学问题」以匹配该刊 scope。"
                )
            lines.append("")
            continue

        # 按相关度排序（不用被引量排序：被引榜会被"高引但只是勉强相关"的
        # 大综述/立场文件污染，实测 Ophthalmology 的被引榜首是
        # "Disparities in Vision Health and Eye Care"，与主题几乎无关）
        by_rel = sorted(papers, key=lambda p: (-(p.get("score") or 0), -p["cites"]))[:top]
        by_new = sorted(
            papers, key=lambda p: (p["date"] or f"{p['year'] or 0}-00-00"), reverse=True
        )[:top]

        lines.append(f"**① 该刊最相关同类论文（近 {years} 年，按相关度）**")
        lines.append("")
        lines.append("| # | 年 | 被引 | 标题 | DOI |")
        lines.append("|---|---|---|---|---|")
        for i, p in enumerate(by_rel, 1):
            lines.append(
                f"| {i} | {p['year'] or '—'} | {p['cites']} | {p['title'][:120]} | "
                f"{('[' + p['doi'] + '](https://doi.org/' + p['doi'] + ')') if p['doi'] else '—'} |"
            )
        lines.append("")
        lines.append("**② 该刊最新同类论文（按发表日期，看当前写法与体量）**")
        lines.append("")
        lines.append("| # | 发表日期 | 年 | 标题 | DOI |")
        lines.append("|---|---|---|---|---|")
        for i, p in enumerate(by_new, 1):
            lines.append(
                f"| {i} | {p['date'] or '—'} | {p['year'] or '—'} | {p['title'][:120]} | "
                f"{('[' + p['doi'] + '](https://doi.org/' + p['doi'] + ')') if p['doi'] else '—'} |"
            )
        lines.append("")
    return "\n".join(lines)


def _esc(s):
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_html(results, years, top, queries, from_date):
    """浅色主题 HTML 报告（适配 IDE light theme）。"""
    CSS = """
:root{--bg:#f7f8fa;--card:#fff;--line:#e6e8ec;--tx:#1f2329;--tx2:#5f6673;--ac:#2563eb;
--ok:#0f9d58;--wn:#c77700;--er:#d93025;}
*{box-sizing:border-box}
body{margin:0;padding:28px 20px;background:var(--bg);color:var(--tx);
font:14px/1.65 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto}
h1{font-size:24px;margin:0 0 6px}
h2{font-size:18px;margin:30px 0 10px;padding-bottom:7px;border-bottom:2px solid var(--ac)}
.sub{color:var(--tx2);font-size:13px;margin:0 0 18px}
.meta{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:13px 17px;margin-bottom:8px}
.meta code{background:#eef1f5;padding:1px 5px;border-radius:4px;font-size:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:15px 17px;margin:14px 0}
.card h3{margin:0 0 4px;font-size:16px}
.stat{color:var(--tx2);font-size:12.5px;margin:0 0 11px}
.stat b{color:var(--ac);font-size:14px}
table{width:100%;border-collapse:collapse;margin:7px 0 13px;font-size:13px;background:var(--card)}
th{background:#f0f2f5;text-align:left;padding:7px 9px;border:1px solid var(--line);
font-weight:600;font-size:12.5px;color:#3d434d}
td{padding:6px 9px;border:1px solid var(--line);vertical-align:top}
tr:nth-child(even) td{background:#fafbfc}
td.n{text-align:center;color:var(--tx2);white-space:nowrap}
td.t{line-height:1.45}
a{color:var(--ac);text-decoration:none;word-break:break-all}
a:hover{text-decoration:underline}
.label{display:inline-block;font-size:12px;font-weight:600;padding:2px 8px;border-radius:5px;
background:#eef3ff;color:var(--ac);margin:12px 0 5px}
.none{background:#fff7f0;border:1px solid #ffd9b8;border-left:3px solid var(--wn);
border-radius:8px;padding:11px 14px;color:#8a4b00;font-size:13px}
.err{background:#fdf0ef;border:1px solid #f7c9c4;border-left:3px solid var(--er);
border-radius:8px;padding:11px 14px;color:#a01a10;font-size:13px;font-weight:600}
.foot{margin-top:30px;color:var(--tx2);font-size:12px;border-top:1px solid var(--line);padding-top:12px}
"""

    def tbl(rows, cols):
        h = "".join(f"<th>{c}</th>" for c in cols)
        b = ""
        for i, p in enumerate(rows, 1):
            doi = p.get("doi")
            link = (
                f'<a href="https://doi.org/{_esc(doi)}">{_esc(doi)}</a>' if doi else "—"
            )
            b += f'<tr><td class="n">{i}</td><td class="t">{_esc(p["title"])}</td><td class="n">{link}</td></tr>'
        return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"

    out = [
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
        "<title>投稿命中率分析与同类论文报告</title>",
        f"<style>{CSS}</style></head><body><div class='wrap'>",
        "<h1>投稿命中率分析与同类论文报告</h1>",
        f"<p class='sub'>用于验证候选期刊是否真的接收你这类稿件 —— 找该刊近 {years} 年的同类论文。</p>",
        "<div class='meta'>",
        f"<div><b>主题词</b>：{_esc('、'.join(queries))}</div>",
        f"<div><b>时间窗</b>：{from_date} 起（近 {years} 年）</div>",
        "<div><b>数据源</b>：OpenAlex（Semantic Scholar 兜底）</div>",
        "</div>",
    ]

    # ---- 命中率汇总表 ----
    rates = {
        j: compute_hit_rate(b["papers"], queries, b.get("errors") or [])
        for j, b in results.items()
    }
    if rates:
        out.append("<h2>投稿命中率分析（Scope 命中指数）</h2>")
        out.append(
            "<p class='sub'>指数衡量 <b>scope 契合度</b>（该刊近 "
            f"{years} 年收不收这类稿），<b>不等于录用概率</b>——录用还取决于新颖性、实验与写作。</p>"
        )
        out.append("<table><thead><tr><th>期刊</th><th>命中指数</th><th>等级</th>"
                   "<th>活跃度/40</th><th>时效/20</th><th>覆盖/20</th><th>相关/20</th><th>解读</th></tr></thead><tbody>")
        for j, r in sorted(
            rates.items(), key=lambda kv: -(kv[1]["score"] if kv[1] else -1)
        ):
            if r is None:
                out.append(f"<tr><td>{_esc(j)}</td><td class='n'>—</td><td class='n'>⚠️ 无效</td>"
                           "<td class='n'>—</td><td class='n'>—</td><td class='n'>—</td><td class='n'>—</td>"
                           "<td>检索失败，不可用于决策</td></tr>")
            else:
                color = GRADE_COLOR.get(r["grade"], "#5f6673")
                out.append(
                    f"<tr><td>{_esc(j)}</td><td class='n'><b style='color:{color};font-size:15px'>{r['score']}</b></td>"
                    f"<td class='n' style='color:{color};font-weight:600'>{r['grade']}</td>"
                    f"<td class='n'>{r['activity']}</td><td class='n'>{r['recency']}</td>"
                    f"<td class='n'>{r['breadth']}</td><td class='n'>{r['rel_txt']}</td>"
                    f"<td>{_esc(r['verdict'])}</td></tr>"
                )
        out.append("</tbody></table>")

    for journal, block in results.items():
        info = block["source"]
        papers = block["papers"]
        errors = block.get("errors") or []
        r = rates.get(journal)

        out.append("<div class='card'>")
        badge = ""
        if r:
            color = GRADE_COLOR.get(r["grade"], "#5f6673")
            badge = (f"<span style='float:right;font-size:13px;font-weight:700;"
                     f"color:{color}'>命中指数 {r['score']}/100 · {r['grade']}</span>")
        out.append(f"<h3>{_esc(journal)}{badge}</h3>")
        if info.get("id"):
            out.append(
                f"<p class='stat'>OpenAlex：{_esc(info['name'])} · <code>{info['id']}</code> · "
                f"全刊 {info.get('works') or '—'} 篇 · 名称匹配 {info.get('score')}</p>"
            )
        else:
            out.append(
                f"<p class='stat'>⚠️ OpenAlex 未收录，结果来自 Semantic Scholar 兜底"
                f"（最近似刊：{_esc(info.get('name') or '无')}）</p>"
            )
        if block.get("note"):
            out.append(f"<div class='none'>ℹ️ {_esc(block['note'])}</div>")

        if errors:
            out.append(
                f"<div class='err'>❌ {len(errors)} 个主题词检索失败，本篇结论不可用于决策</div>"
            )
        elif not papers:
            out.append(
                f"<div class='none'><b>未检出同类论文。</b>该刊近 {years} 年几乎没有这个方向的稿件，"
                "被以 out-of-scope 直接拒的风险偏高。建议换刊，或把叙事重心从「临床问题」"
                "移到「方法学问题」以匹配该刊 scope。</div>"
            )
        else:
            by_rel = sorted(papers, key=lambda p: (-(p.get("score") or 0), -p["cites"]))[:top]
            by_new = sorted(
                papers, key=lambda p: (p["date"] or f"{p['year'] or 0}-00-00"), reverse=True
            )[:top]
            out.append(f"<p class='stat'>近 {years} 年匹配到 <b>{len(papers)}</b> 篇同类论文</p>")
            out.append("<div class='label'>① 最相关（按相关度）</div>")
            out.append(tbl(by_rel, ["#", "论文标题", "DOI"]))
            out.append("<div class='label'>② 最新发表（看当前写法与体量）</div>")
            out.append(tbl(by_new, ["#", "论文标题", "DOI"]))
        out.append("</div>")

    out.append(
        "<div class='foot'>数据源 OpenAlex（CC0）／Semantic Scholar。"
        "相关度排序由检索引擎给出，宽泛主题词可能带入弱相关结果，建议人工筛一遍。</div>"
    )
    out.append("</div></body></html>")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="在指定期刊内检索与论文主题相似的论文（用于验证投稿 scope 可行性）"
    )
    ap.add_argument("--query", "-q", action="append", default=[], help="主题词，可重复")
    ap.add_argument("--paper", help="论文初稿文件（txt/md/docx），自动抽关键词")
    ap.add_argument("--journal", "-j", action="append", default=[], help="期刊名，可重复")
    ap.add_argument("--years", type=int, default=3, help="回溯年数（默认 3）")
    ap.add_argument("--top", type=int, default=6, help="每刊每个榜单条数（默认 6）")
    ap.add_argument("--resolve-only", action="store_true", help="只解析期刊 ID，不检索")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--html", action="store_true", help="输出浅色主题 HTML 报告")
    ap.add_argument("--out", "-o", help="写入文件")
    args = ap.parse_args()

    queries = [q.strip() for q in args.query if q.strip()]
    if args.paper:
        text = read_paper(args.paper)
        auto_kw = keywords_from_text(text, limit=5)
        print(f"[i] 自动抽取的检索词：{', '.join(auto_kw)}", file=sys.stderr)
        queries = auto_kw + queries
    if not queries:
        queries = ["deep learning", "retinal imaging", "optical coherence tomography"]

    if not args.journal:
        ap.error("至少需要一个 --journal")

    from_date = (date.today() - timedelta(days=365 * args.years + 30)).isoformat()
    from_year = int(from_date[:4])

    cache = load_cache()
    scache = load_search_cache()
    results = {}
    used_s2 = []

    for j in args.journal:
        info = resolve_source(j, cache)
        print(f"[*] {j}  ->  {info.get('name')} ({info.get('id')})", file=sys.stderr)
        if args.resolve_only:
            results[j] = {"source": info, "papers": []}
            continue
        if not info.get("id"):
            papers, s2err = search_s2(info.get("name") or j, queries, from_year, args.top)
            results[j] = {
                "source": info,
                "papers": papers,
                "fallback": "s2",
                "errors": s2err,
                "note": "OpenAlex 未收录该刊，已用 Semantic Scholar 兜底",
            }
            used_s2.append(j)
            continue
        try:
            papers, errors = search_in_source(
                info["id"], queries, from_date, scache=scache
            )
            results[j] = {"source": info, "papers": papers, "errors": errors}
        except RateLimited as e:
            print("  [→] OpenAlex 限流，切换到 Semantic Scholar 兜底", file=sys.stderr)
            papers, s2err = search_s2(info.get("name") or j, queries, from_year, args.top)
            results[j] = {
                "source": info,
                "papers": papers,
                "fallback": "s2",
                "errors": s2err,
                "note": f"⚠️ OpenAlex 限流（{e}），已切 Semantic Scholar 兜底"
                + ("；兜底同样失败，本刊结果无效" if s2err else ""),
            }
            used_s2.append(j)
        for p in results[j]["papers"]:
            p.pop("_id", None)

    save_search_cache(scache)

    # 全局失败保护：不能把"检索失败"当成"该刊不收这个方向"
    n_err = sum(len(b.get("errors") or []) for b in results.values())
    n_all_zero = sum(1 for b in results.values() if not b["papers"])
    if n_err and n_all_zero == len(results):
        print(
            "\n[!!] 严重警告：所有期刊都返回 0 篇，且存在检索失败 —— "
            "这几乎肯定是网络/限流问题，不是期刊范围问题。\n"
            "     请等待 1–2 分钟后重跑，不要据此判断投稿可行性。\n",
            file=sys.stderr,
        )
    if used_s2:
        print(f"[i] 以下期刊使用了 Semantic Scholar 兜底：{', '.join(used_s2)}", file=sys.stderr)

    if args.json:
        text = json.dumps(
            {"queries": queries, "from_date": from_date, "results": results},
            ensure_ascii=False,
            indent=2,
        )
    elif args.html:
        text = render_html(results, args.years, args.top, queries, from_date)
    else:
        header = (
            f"# 同类论文检索结果\n\n"
            f"- 主题词：{', '.join(queries)}\n"
            f"- 时间窗：{from_date} 起（近 {args.years} 年）\n"
            f"- 数据源：OpenAlex（Semantic Scholar 兜底）\n\n"
        )
        text = header + render_md(results, args.years, args.top, queries)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"[+] 已写入 {args.out}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
