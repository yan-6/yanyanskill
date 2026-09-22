#!/usr/bin/env python3
"""内容工厂套件 · 通用/本机两层链路自检。

架构约定（2026-09-22 合并后）：
    content-factory-kit/
      references/*.md         ← 通用规范（谁都能用），唯一真源
      references/local/*.md   ← 本机口径（只对这套工作台生效），指回真源 + 写本机命令/ID/判断标准
      SKILL.md                ← 入口，含「按动作 ID 取规范」路由表

所以最怕的四种事故：
    ① 真源改名 / 搬家 → 本机文档的指针集体失效而不报错（B）
    ② 加了新真源没人接线 → 变成没人读的孤儿文档（C）
    ③ 本机文档图省事把通用正文抄回来 → 从此改一处要改两处（D）
    ④ 合并后旧技能名还散在正文里 → 读者去加载一个已经不存在的 skill（E）

退役技能名清单与 tests/check_kit_integrity.py **共用** tests/retired-skills.txt
（两边各抄一份名单会漂移）；本文件里不写任何旧技能名字面量。

用法（本文件住在套件自己的 tests/ 下，默认检查它所在的那个套件）：
    python3 tests/check_spec_bindings.py [套件目录]
    python3 tests/check_spec_bindings.py --selftest     # 负对照：注入 4 类破坏，必须每次都报错
退出码：0 = 全绿；1 = 有 FAIL
"""
import difflib
import os
import re
import shutil
import sys
import tempfile

# 默认 = 本文件所在 tests/ 的上一级（也就是套件根）；
# 项目里那份 ai-workspace/tools/check_spec_bindings.py 是个转发壳。
DEFAULT_KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isfile(os.path.join(DEFAULT_KIT, "SKILL.md")):
    DEFAULT_KIT = os.path.expanduser("~/.workbuddy/skills/content-factory-kit")

# 本机口径文档 -> 它必须显式指到的通用真源
LOCAL_TO_SOURCE = {
    "research.md": ["research.md"],
    "writing.md": ["writing.md", "deai.md"],
    "platforms.md": ["platforms.md"],
    "visual.md": ["visual.md"],
    "assets.md": ["assets.md", "asset-examples.md"],
}
# 任何阶段都可能用到的本机速查（不指向单一阶段真源）
LOCAL_EXTRA = ["workbench-facts.md"]

# references/ 下**不归五阶段本机文档管**的文件（属套件的其它支路）
KNOWN_UNBOUND = {
    "style-guide.md": "怎么长出你自己的风格指南（方法论文档，由 SKILL.md 指）",
    "template-authoring.md": "支路 B：怎么把自己的应用做成模板源",
    "workbench-clone.md": "支路 C：怎么复刻工作台",
    "workbench-schema.md": "支路 C：清单结构 / 11 张表 / 149 字段",
}

# 「本技能原来的 X 已删除并入」这类**历史说明行**里会出现旧名，那是记录不是指针
HISTORICAL_MARKERS = ("已删除", "已并入", "原来的", "合并前", "曾叫")

# 退役技能名清单与「结构自检」共用同一份数据（tests/retired-skills.txt）。
# 两边各抄一份清单会漂移 —— 所以这里只读文件，不写字面量。
RETIRED_FILE = "tests/retired-skills.txt"


def load_retired(kit):
    p = os.path.join(kit, RETIRED_FILE)
    if not os.path.isfile(p):
        return []
    with open(p, encoding="utf-8", errors="replace") as f:
        return [ln.split("#", 1)[0].strip() for ln in f if ln.split("#", 1)[0].strip()]

PATH_RE = re.compile(r"(?<![\w/.-])(references/(?:local/)?[A-Za-z0-9_\-]+\.md)")
H1_RE = re.compile(r"^# .+", re.M)
POINTER_RE = re.compile(r"^> ## 通用规范在哪\s*$", re.M)


def read(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def effective_lines(body):
    for i, ln in enumerate(body.splitlines(), 1):
        if any(m in ln for m in HISTORICAL_MARKERS):
            continue
        yield i, ln


def run_checks(kit):
    """返回 RESULTS: [(passed, name, detail)] 与 INFO: [str]"""
    res, info = [], []
    ref_dir = os.path.join(kit, "references")
    local_dir = os.path.join(ref_dir, "local")
    skill_md = os.path.join(kit, "SKILL.md")

    def ok(name, cond, detail=""):
        res.append((bool(cond), name, detail))

    # ── A. 技能完整性 ────────────────────────────────────────────────
    ok("A1 入口 SKILL.md 在", os.path.isfile(skill_md), skill_md)

    want_local = sorted(LOCAL_TO_SOURCE) + LOCAL_EXTRA
    miss_local = [f for f in want_local if not os.path.isfile(os.path.join(local_dir, f))]
    ok("A2 本机口径 %d 份都在" % len(want_local), not miss_local, "缺: %s" % ", ".join(miss_local))

    bad_head = []
    for f in sorted(LOCAL_TO_SOURCE):
        p = os.path.join(local_dir, f)
        if not os.path.isfile(p):
            continue
        t = read(p)
        if not H1_RE.search(t):
            bad_head.append("%s 缺 H1" % f)
        elif not POINTER_RE.search(t):
            bad_head.append("%s 缺「通用规范在哪」指针块" % f)
    ok("A3 本机文档都有 H1 + 指针块", not bad_head, " | ".join(bad_head))

    # ── B. 指针可达 ──────────────────────────────────────────────────
    scan = [skill_md] + [os.path.join(local_dir, f) for f in want_local]
    scan += [os.path.join(ref_dir, f) for f in sorted(os.listdir(ref_dir))
             if f.endswith(".md")] if os.path.isdir(ref_dir) else []
    broken, resolved = [], set()
    for p in scan:
        if not os.path.isfile(p):
            continue
        who = os.path.relpath(p, kit).replace("\\", "/")
        for lineno, line in effective_lines(read(p)):
            for rel in sorted(set(PATH_RE.findall(line))):
                if os.path.isfile(os.path.join(kit, rel.replace("/", os.sep))):
                    resolved.add(rel)
                else:
                    broken.append("%s:%d → %s（不存在）" % (who, lineno, rel))
    ok("B1 技能内所有 references 指针都能解析", not broken,
       " | ".join(sorted(set(broken))[:8]))

    not_linked = []
    for f, need in sorted(LOCAL_TO_SOURCE.items()):
        p = os.path.join(local_dir, f)
        if not os.path.isfile(p):
            continue
        body = "\n".join(ln for _, ln in effective_lines(read(p)))
        for src in need:
            if ("references/" + src) not in body:
                not_linked.append("local/%s 没指到 references/%s" % (f, src))
    ok("B2 每份本机文档都显式指到了它该读的通用真源", not not_linked, ", ".join(not_linked))

    # ── C. 真源齐全 + 无孤儿 ─────────────────────────────────────────
    all_refs = sorted(f for f in os.listdir(ref_dir) if f.endswith(".md")) if os.path.isdir(ref_dir) else []
    expected = set()
    for v in LOCAL_TO_SOURCE.values():
        expected.update(v)
    gone = [f for f in sorted(expected) if f not in all_refs]
    ok("C1 本机文档指到的通用真源都存在（%d 份）" % len(expected), not gone,
       "缺: %s" % ", ".join(gone))

    orphan = [f for f in all_refs if f not in expected and f not in KNOWN_UNBOUND]
    ok("C2 没有未接线的通用真源（白名单外）", not orphan,
       "新增了真源但没接上本机文档: %s" % ", ".join(orphan))
    unbound = [f for f in all_refs if f in KNOWN_UNBOUND]
    info.append("ℹ references/ 共 %d 份通用文档：%d 份已接线，%d 份属其它支路（%s）"
                % (len(all_refs), len(all_refs) - len(unbound), len(unbound), ", ".join(unbound)))

    # ── D. 无反向依赖（本机文档不许把通用抄回来）────────────────────
    dupe = []
    for f, need in sorted(LOCAL_TO_SOURCE.items()):
        lp = os.path.join(local_dir, f)
        if not os.path.isfile(lp):
            continue
        a = [l.strip() for l in read(lp).splitlines() if len(l.strip()) >= 16]
        for src in need:
            gp = os.path.join(ref_dir, src)
            if not os.path.isfile(gp):
                continue
            b = [l.strip() for l in read(gp).splitlines() if len(l.strip()) >= 16]
            if not a or not b:
                continue
            ratio = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
            if ratio > 0.35:
                dupe.append("local/%s ↔ references/%s 相似度 %.0f%%" % (f, src, ratio * 100))
    ok("D1 本机文档没有把通用正文抄回来（相似度 ≤35%）", not dupe, " | ".join(dupe))

    # ── E. 旧技能名已消失 ────────────────────────────────────────────
    retired = load_retired(kit)
    ghost = []
    if retired:
        for p in scan:
            if not os.path.isfile(p):
                continue
            who = os.path.relpath(p, kit).replace("\\", "/")
            for lineno, line in effective_lines(read(p)):
                for old in retired:
                    if old in line:
                        ghost.append("%s:%d → %s" % (who, lineno, old))
    ok("E1 技能内不再出现已合并的旧技能名（名单 %d 个）" % len(retired), retired and not ghost,
       ((" | ".join(sorted(set(ghost))[:6])) if ghost
        else ("名单读不到，E1 是空转" if not retired else "")))

    return res, info


def report(res, info, title):
    print("=== %s ===" % title)
    print()
    for ln in info:
        print("  " + ln)
    if info:
        print()
    n_fail = sum(1 for p, _, _ in res if not p)
    for passed, name, detail in res:
        line = "  %s  %s" % ("PASS" if passed else "FAIL", name)
        if detail:
            line += "   (%s)" % detail if passed else "   ← %s" % detail
        print(line)
    print()
    print("=== 合计：PASS %d / FAIL %d ===" % (len(res) - n_fail, n_fail))
    return n_fail


def selftest(kit):
    """负对照：4 类破坏各注入一次，每次都必须让自检报 FAIL。"""
    cases = []

    def case(name, mutate):
        cases.append((name, mutate))

    # 破坏方式都**从真实文件派生**，源码里不留假的路径字面量：
    # 留了就会被「结构自检」的路径扫描当成真引用，逼出一串假阳性（也逼出豁免名单）。
    def brk_pointer(d):
        """把某份本机文档里实际指的那个真源，改成一个不存在的名字。"""
        ld = os.path.join(d, "references", "local")
        p = os.path.join(ld, sorted(f for f in os.listdir(ld) if f.endswith(".md"))[0])
        t = read(p)
        m = PATH_RE.search(t)
        if not m:
            raise AssertionError("这份本机文档里没有可破坏的指针，负对照前提不成立")
        real = m.group(1)
        open(p, "w", encoding="utf-8").write(t.replace(real, real[:-3] + "-missing.md", 1))

    def brk_orphan(d):
        """新建一个没人接线的真源（名字从已有的真源派生）。"""
        rd = os.path.join(d, "references")
        seed = sorted(f for f in os.listdir(rd) if f.endswith(".md"))[0]
        open(os.path.join(rd, "orphan-" + seed), "w", encoding="utf-8").write("# probe\n")

    def brk_copyback(d):
        src = read(os.path.join(d, "references", "research.md"))
        open(os.path.join(d, "references", "local", "research.md"), "w", encoding="utf-8").write(
            "# 研究 · 本机口径\n\n> ## 通用规范在哪\n>\n> x\n\n" + src)

    def brk_ghost(d):
        """在 SKILL.md 里塞一个已退役的技能名（名字从名单里取，不写字面量）。"""
        names = load_retired(d)
        if not names:
            raise AssertionError("读不到退役名单，E1 无从验证")
        open(os.path.join(d, "SKILL.md"), "a", encoding="utf-8").write(
            "\n详见 `%s`。\n" % names[0])

    case("B 指针断裂（真源改名）", brk_pointer)
    case("C 出现未接线真源", brk_orphan)
    case("D 本机文档抄回通用正文", brk_copyback)
    case("E 残留旧技能名", brk_ghost)

    print("=== 负对照：注入破坏后自检必须报错 ===")
    print()
    bad = 0
    tmp = tempfile.mkdtemp(prefix="cfkit-selftest-")
    try:
        for name, mutate in cases:
            d = os.path.join(tmp, re.sub(r"[^\w]+", "_", name))
            shutil.copytree(kit, d)
            mutate(d)
            res, _ = run_checks(d)
            n_fail = sum(1 for p, _, _ in res if not p)
            fails = [nm for p, nm, _ in res if not p]
            got = "报错 ✓" if n_fail else "没报错 ✗（负对照失效！）"
            print("  %-26s → FAIL %d  %s" % (name, n_fail, got))
            if fails:
                print("       命中：%s" % "、".join(fails))
            if not n_fail:
                bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print()
    print("=== 负对照：%d/4 通过 ===" % (4 - bad))
    return bad


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    kit = os.path.abspath(args[0]) if args else os.path.abspath(DEFAULT_KIT)

    if not os.path.isdir(kit):
        print("套件目录不存在：%s" % kit)
        return 1

    res, info = run_checks(kit)
    n_fail = report(res, info, "内容工厂套件 · 通用/本机两层自检（%s）" % kit)

    if "--selftest" in flags:
        print()
        bad = selftest(kit)
        n_fail += bad

    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
