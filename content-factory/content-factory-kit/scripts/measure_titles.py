# -*- coding: utf-8 -*-
"""量自己的标题画像 —— 内容工厂风格的「第一步：量」。

把你自己写过的一批标题喂进来，输出可直接抄进风格指南 DIGEST 区块的指标：
长度中位/分布、两段式冒号率、问句率、数字率、栏目前缀率、人称率，并按年分期对比。

用法：
    python3 measure_titles.py <语料文件> [选项]

语料文件支持四种形态（自动识别，按后缀）：
    .json  — ① [{"t":"标题","d":"2025-01-01"}, ...]  ② ["标题", ...]
             ③ {"shelves":[{"items":[{"t":..,"d":..}]}]}  ④ {"items":[...]}
    .csv / .tsv — 带表头；自动认「t/title/标题」列与「d/date/日期」列
                  用 --title-field / --date-field 可手动指定列名
    .txt / .md  — 一行一个标题；行首的列表记号 - * + 与数字序号 1. 会剥掉；
                  以 # 开头的行按 Markdown 标题处理【默认跳过】（那是文档结构，不是文章标题）
    亦可直接给一个 URL（会提示你先落地成文件，本脚本不联网）

选项：
    --title-field NAME    指定标题字段/列名
    --date-field NAME     指定日期字段/列名（给了才会输出分期对比）
    --words a,b,c         额外统计这些词/短语的出现率。按【正则】匹配（忽略大小写），
                          所以「让.*飞起来」这类句式也能量；编不成的 token 自动按字面处理
    --json                输出机器可读 JSON（方便再喂给别的脚本）

无第三方依赖，Python 3.8+。
"""

import argparse
import csv
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

# ---------- 读取 ----------


def _norm_item(obj):
    """把一条记录归一成 (标题, 日期)。标题取不到返回 None。"""
    if isinstance(obj, str):
        return obj.strip(), ""
    if not isinstance(obj, dict):
        return None
    for k in ("t", "title", "标题", "name", "text"):
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            for dk in ("d", "date", "日期", "publish_date", "pub_date", "time"):
                dv = obj.get(dk)
                if isinstance(dv, str) and dv.strip():
                    return v.strip(), dv.strip()
            return v.strip(), ""
    return None


def _walk(obj, out):
    if isinstance(obj, list):
        for it in obj:
            if isinstance(it, dict) and any(k in it for k in ("items", "list", "articles", "list_data")):
                for ik in ("items", "list", "articles", "list_data"):
                    if isinstance(it.get(ik), list):
                        _walk(it[ik], out)
                        break
                else:
                    r = _norm_item(it)
                    if r:
                        out.append(r)
            else:
                r = _norm_item(it)
                if r:
                    out.append(r)
    elif isinstance(obj, dict):
        nested = False
        for nk in ("shelves", "items", "list", "articles", "data", "list_data"):
            if isinstance(obj.get(nk), list):
                _walk(obj[nk], out)
                nested = True
                break
        if not nested:
            r = _norm_item(obj)
            if r:
                out.append(r)


def load_corpus(path, title_field=None, date_field=None):
    if re.match(r"^https?://", path, re.I):
        sys.exit("本脚本不联网。请先把语料落地成文件（json/csv/txt）再跑。\n"
                 "  提示：平台导出的表格存成 .csv 最省事。")
    if not os.path.exists(path):
        sys.exit("找不到语料文件：%s" % path)
    ext = os.path.splitext(path)[1].lower()

    if ext == ".json":
        try:
            obj = json.loads(open(path, encoding="utf-8").read())
        except Exception as e:
            sys.exit("JSON 解析失败：%s" % e)
        out = []
        _walk(obj, out)
        return out

    if ext in (".csv", ".tsv"):
        delim = "\t" if ext == ".tsv" else ","
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f, delimiter=delim))
        if not rows:
            sys.exit("表格里没有数据行。")
        cols = list(rows[0].keys())

        def pick(cands, explicit):
            if explicit:
                if explicit not in cols:
                    sys.exit("指定的列名 %r 不存在。可用列：%s" % (explicit, cols))
                return explicit
            for c in cols:
                if str(c).strip().lower() in cands:
                    return c
            for c in cols:
                for cand in cands:
                    if cand in str(c).strip().lower():
                        return c
            return None

        tc = pick({"t", "title", "标题", "name", "文章标题"}, title_field)
        dc = pick({"d", "date", "日期", "时间", "publish", "pub_date"}, date_field)
        if not tc:
            sys.exit("认不出标题列。请用 --title-field 指定。可用列：%s" % cols)
        out = []
        for r in rows:
            t = (r.get(tc) or "").strip()
            if t:
                out.append((t, (r.get(dc) or "").strip() if dc else ""))
        return out

    # txt / md：一行一个标题
    # - 以 # 开头的按 Markdown 标题处理，默认跳过（那是文档/分节结构，不是文章标题）
    # - 行首的列表记号 - * + 与数字序号 1. 1、 1) 会剥掉，剩下的当标题
    out = []
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if not s:
            continue
        if re.match(r"^#{1,6}(\s|$)", s):
            continue
        s = re.sub(r"^\s*(?:[-*+]\s+|\d+[.、)]\s*)", "", s).strip()
        if s:
            out.append((s, ""))
    return out


# ---------- 度量 ----------


def has_colon(t):
    return ("：" in t) or (":" in t)


def has_question(t):
    return ("？" in t) or ("?" in t)


def has_bang(t):
    return ("！" in t) or ("!" in t)


def has_number(t):
    return bool(re.search(r"\d", t))


def has_prefix(t):
    return t.startswith("【") or bool(re.match(r"^[\[\(（【]", t))


def has_first_person(t):
    return any(w in t for w in ("我", "咱", "俺"))


def has_second_person(t):
    return any(w in t for w in ("你", "大家", "各位"))


def has_separator(t):
    return any(ch in t for ch in "—|｜丨-")


def pct(num, den):
    return (num * 100.0 / den) if den else 0.0


def year_of(d):
    m = re.search(r"(19|20)\d{2}", d or "")
    return m.group(0) if m else ""


def analyze(rows, words=None):
    titles = [t for t, _ in rows]
    n = len(titles)
    lens = [len(t) for t in titles]
    res = {"n": n}
    if not n:
        return res
    res["len_min"] = min(lens)
    res["len_median"] = statistics.median(lens)
    res["len_mean"] = round(statistics.mean(lens), 1)
    res["len_max"] = max(lens)
    b = Counter()
    for L in lens:
        b["<15" if L < 15 else "15-24" if L < 25 else "25-34" if L < 35 else "35+"] += 1
    res["len_buckets"] = {k: {"n": b[k], "pct": round(pct(b[k], n), 1)}
                          for k in ("<15", "15-24", "25-34", "35+")}
    feats = {
        "冒号（两段式）": has_colon,
        "问号（悬念/设问）": has_question,
        "感叹号": has_bang,
        "具体数字": has_number,
        "栏目前缀【/（": has_prefix,
        "第一人称（我/咱）": has_first_person,
        "第二人称（你/大家）": has_second_person,
        "破折号/竖线分隔": has_separator,
    }
    res["features"] = {name: {"n": sum(1 for t in titles if fn(t)),
                              "pct": round(pct(sum(1 for t in titles if fn(t)), n), 1)}
                       for name, fn in feats.items()}

    # 分期
    dated = [(year_of(d), t) for t, d in rows if year_of(d)]
    if dated and len(dated) >= 0.5 * n:
        g = defaultdict(list)
        for y, t in dated:
            g[y].append(t)
        per = {}
        for y in sorted(g):
            ts = g[y]
            per[y] = {
                "n": len(ts),
                "len_median": statistics.median([len(t) for t in ts]),
                "colon_pct": round(pct(sum(1 for t in ts if has_colon(t)), len(ts)), 1),
                "question_pct": round(pct(sum(1 for t in ts if has_question(t)), len(ts)), 1),
                "number_pct": round(pct(sum(1 for t in ts if has_number(t)), len(ts)), 1),
                "prefix_pct": round(pct(sum(1 for t in ts if has_prefix(t)), len(ts)), 1),
            }
        res["by_year"] = per
        if len(per) >= 2:
            ys = sorted(per)
            early = [y for y in ys if int(y) <= int(ys[len(ys) // 2])]
            late = [y for y in ys if y not in early]
            if early and late:
                def agg(gys):
                    tot = sum(per[y]["n"] for y in gys)
                    return {
                        "n": tot,
                        "colon_pct": round(sum(per[y]["colon_pct"] * per[y]["n"] for y in gys) / tot, 1),
                        "len_median": statistics.median(
                            [len(t) for y in gys for t in g[y]]),
                    }
                res["early_period"] = agg(early)
                res["late_period"] = agg(late)
    if words:
        def _hit(w, titles):
            try:
                rx = re.compile(w, re.I)
            except re.error:
                return sum(1 for t in titles if w.lower() in t.lower())
            return sum(1 for t in titles if rx.search(t))

        res["words"] = {w: {"n": _hit(w, titles), "pct": round(pct(_hit(w, titles), n), 1)}
                        for w in words}
    return res


# ---------- 打印 ----------


def render(res, source):
    L = []
    L.append("语料：%s" % source)
    if not res.get("n"):
        L.append("没有解析到任何标题 —— 检查文件格式，或用 --title-field 指定列名。")
        return "\n".join(L)
    n = res["n"]
    L.append("标题条数：%d" % n)
    L.append("")
    L.append("【标题长度（字符）】")
    L.append("  最短 / 中位 / 均 / 最长：%d / %g / %g / %d"
             % (res["len_min"], res["len_median"], res["len_mean"], res["len_max"]))
    for k in ("<15", "15-24", "25-34", "35+"):
        v = res["len_buckets"][k]
        L.append("  %-6s %4d 条 (%g%%)" % (k, v["n"], v["pct"]))
    L.append("")
    L.append("【结构特征】")
    for name, v in res["features"].items():
        L.append("  %-20s %4d 条 (%g%%)" % (name, v["n"], v["pct"]))
    if "by_year" in res:
        L.append("")
        L.append("【分期演变】")
        L.append("  %-6s %5s %8s %8s %8s %8s %8s"
                 % ("年份", "篇数", "长度中位", "冒号率", "问句率", "数字率", "前缀率"))
        for y, v in res["by_year"].items():
            L.append("  %-6s %5d %8g %7g%% %7g%% %7g%% %7g%%"
                     % (y, v["n"], v["len_median"], v["colon_pct"],
                        v["question_pct"], v["number_pct"], v["prefix_pct"]))
        if "early_period" in res and "late_period" in res:
            e, l = res["early_period"], res["late_period"]
            L.append("")
            L.append("  早期合计 n=%d：长度中位 %g，冒号率 %g%%"
                     % (e["n"], e["len_median"], e["colon_pct"]))
            L.append("  近期合计 n=%d：长度中位 %g，冒号率 %g%%"
                     % (l["n"], l["len_median"], l["colon_pct"]))
            if e["colon_pct"] and l["colon_pct"] / max(e["colon_pct"], 1) >= 2:
                L.append("  → 两段式冒号率近期是早期的 %g 倍，说明你改过招牌写法。"
                         % round(l["colon_pct"] / max(e["colon_pct"], 1), 1))
                L.append("    写新内容请对标【近期】，不要拿全期平均当基准。")
    if "words" in res:
        L.append("")
        L.append("【自定义词出现率】")
        for w, v in sorted(res["words"].items(), key=lambda x: -x[1]["n"]):
            L.append("  %-12s %4d 条 (%g%%)" % (w, v["n"], v["pct"]))
    L.append("")
    L.append("提示：以上是「你自己」的数。把它抄进风格指南的量化区块——")
    L.append("     但结论要下在【近期】那一行，不要用全期平均。")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(add_help=True, description="量自己的标题画像")
    ap.add_argument("corpus", help="语料文件（json/csv/tsv/txt/md）")
    ap.add_argument("--title-field", default=None)
    ap.add_argument("--date-field", default=None)
    ap.add_argument("--words", default="", help="逗号分隔的额外统计词")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()

    rows = load_corpus(a.corpus, a.title_field, a.date_field)
    words = [w.strip() for w in a.words.split(",") if w.strip()] or None
    res = analyze(rows, words)
    if a.json:
        print(json.dumps({"source": a.corpus, **res}, ensure_ascii=False, indent=2))
    else:
        print(render(res, a.corpus))


if __name__ == "__main__":
    main()
