#!/usr/bin/env python3
"""content-factory-kit 结构自检：文档引用完整性 / 无孤儿文件 / 无旧技能名残留。

三个技能合并成一个后，最大的维护风险是「路径引用断链」和「旧名字残留」——
本脚本专门查这两类，外加 frontmatter 与关键资产的存在性。

用法：
    python3 tests/check_kit_integrity.py [技能根目录]

退出码：0 = 全绿；1 = 有 FAIL。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(HERE)

# 文档里出现的「技能根目录相对路径」形态
PATH_RE = re.compile(r"(?:references|scripts|tests|assets)/[A-Za-z0-9_./-]+")

# 合并前的三个技能名，不允许再出现在任何文档/脚本里（本脚本自己列清单，故排除自身）
STALE = ["clone-content-workbench", "html-app-template-source", "content-factory-spec"]

# 必须存在的文件（合并时最容易漏掉的那几个）
REQUIRED = [
    "SKILL.md",
    "references/research.md",
    "references/writing.md",
    "references/deai.md",
    "references/platforms.md",
    "references/visual.md",
    "references/assets.md",
    "references/asset-examples.md",
    "references/style-guide.md",
    "references/template-authoring.md",
    "references/workbench-clone.md",
    "references/workbench-schema.md",
    "scripts/measure_titles.py",
    "scripts/clone_workbench.py",
    "tests/check_measure_titles.py",
    "tests/check_clone_workbench.py",
    "assets/ai-content-workspace-template.html",
]

# 文档里允许提到但不必存在的路径（外部技能的文件、用户自己造的路径）
ALLOW_MISSING = {
    "references/",
}

results = []


def ok(name, cond, detail=""):
    results.append((bool(cond), name, detail))


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def walk_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            out.append(rel(os.path.join(dirpath, fn)))
    return sorted(out)


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


FILES = walk_files()
MD_FILES = [f for f in FILES if f.endswith(".md")]
PY_FILES = [f for f in FILES if f.endswith(".py")]

# ── A. frontmatter ────────────────────────────────────────────────────
skill_md = os.path.join(ROOT, "SKILL.md")
ok("A1 SKILL.md 存在", os.path.isfile(skill_md))
text = read(skill_md) if os.path.isfile(skill_md) else ""

m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
ok("A2 有 YAML frontmatter", bool(m))
fm = m.group(1) if m else ""
dirname = os.path.basename(ROOT)

ok("A3 name 与目录名一致", re.search(r"^name:\s*%s\s*$" % re.escape(dirname), fm, re.M) is not None,
   "目录名=%s" % dirname)
ok("A4 agent_created: true", re.search(r"^agent_created:\s*true\s*$", fm, re.M) is not None)
desc = fm.split("description:", 1)[1] if "description:" in fm else ""
ok("A5 description 够长（≥400 字）", len(desc.strip()) >= 400, "%d 字" % len(desc.strip()))

# 三条支路的关键词都要能被检索到
for kw in ["研究", "写作", "多平台", "配图", "资产沉淀", "模板源", "复刻", "风格指南"]:
    ok("A6 description 含关键词「%s」" % kw, kw in desc)

# ── B. 引用完整性 ─────────────────────────────────────────────────────
missing = []
skip_self = {"tests/check_kit_integrity.py"}
for f in MD_FILES + PY_FILES:
    if f in skip_self:
        continue
    for hit in set(PATH_RE.findall(read(os.path.join(ROOT, f)))):
        if hit in ALLOW_MISSING or hit.endswith("/"):
            continue
        if not os.path.exists(os.path.join(ROOT, hit)):
            missing.append("%s → %s" % (f, hit))

ok("B1 文档内路径引用全部命中", not missing, "; ".join(sorted(set(missing))[:6]))

# ── C. 必需文件 ───────────────────────────────────────────────────────
gone = [f for f in REQUIRED if not os.path.isfile(os.path.join(ROOT, f))]
ok("C1 必需文件齐全（%d 个）" % len(REQUIRED), not gone, "缺: %s" % ", ".join(gone))

# ── D. 孤儿文件 & 旧名残留 ────────────────────────────────────────────
corpus = "\n".join(read(os.path.join(ROOT, f)) for f in MD_FILES)
subdir = [f for f in FILES if f.split("/")[0] in ("references", "scripts", "tests")
          and not f.startswith("tests/fixtures") and f not in skip_self]
orphans = []
for f in subdir:
    base = os.path.basename(f)
    if base in corpus or f in corpus:
        continue
    orphans.append(f)
ok("D1 无孤儿文件（每个都被文档提到）", not orphans, ", ".join(orphans))

stale_hits = []
for f in MD_FILES + PY_FILES:
    if f in skip_self:
        continue
    body = read(os.path.join(ROOT, f))
    for name in STALE:
        if name in body:
            stale_hits.append("%s → %s" % (f, name))
ok("D2 无残留旧技能名", not stale_hits, ", ".join(sorted(set(stale_hits))))

# ── E. 支路 C 的脚本与产物 ────────────────────────────────────────────
clone_py = os.path.join(ROOT, "scripts", "clone_workbench.py")
if os.path.isfile(clone_py):
    src = read(clone_py)
    ok("E1 复刻脚本按 __file__ 定位技能根（搬家不失效）",
       'SKILL_ROOT = HERE.parent' in src)
    ok("E2 复刻脚本内置产物路径指向根目录 assets/",
       'SKILL_ROOT / "assets"' in src)

asset = os.path.join(ROOT, "assets", "ai-content-workspace-template.html")
if os.path.isfile(asset):
    size = os.path.getsize(asset)
    ok("E3 模板产物是完整产物（≥1MB）", size >= 1024 * 1024, "%.1f MB" % (size / 1048576))
    head = read(asset)
    ok("E4 模板产物含复刻清单标记", "aiws-template-manifest" in head)
    ok("E5 模板产物含演示块标记", "AIWS-DEMO-BLOCK-START" in head)

# ── 汇总 ──────────────────────────────────────────────────────────────
print("=== content-factory-kit 结构自检（根目录 %s）===" % ROOT)
print()
cur = ""
for passed, name, detail in results:
    sec = name.split()[0][0]
    if sec != cur:
        cur = sec
        print("[%s]" % {"A": "frontmatter", "B": "引用完整性", "C": "必需文件",
                        "D": "孤儿与旧名", "E": "支路 C 资产"}.get(sec, sec))
    tag = "PASS" if passed else "FAIL"
    line = "  %s  %s" % (tag, name)
    if detail and not passed:
        line += "   ← %s" % detail
    elif detail:
        line += "   (%s)" % detail
    print(line)
print()
n_fail = sum(1 for p, _, _ in results if not p)
print("=== 合计：PASS %d / FAIL %d ===" % (len(results) - n_fail, n_fail))
sys.exit(1 if n_fail else 0)
