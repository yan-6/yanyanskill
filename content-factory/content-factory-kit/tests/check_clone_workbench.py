#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_clone_workbench.py —— clone_workbench.py 的全链路验收。

思路：把资料库（library）技能换成一整套**桩脚本**（记录每次调用后返回标准成功回执），
      于是整条写库链路（建表 → 灌数据 → 重映射 → 导入 → 挂载）都能跑完并逐项断言，
      **不会在真实账号里建出任何东西**（资料库不支持删表，所以这是必须的）。

覆盖：
  A 段 本地正确性：清单校验、剥块、重映射硬门、新旧 id 计数
  B 段 调用契约：建表载荷 / 灌数据落点 / import 的 --databases / move-node 目标
  C 段 反向对照：故意破坏映射与清单，断言脚本**会报错**（证明测试有效）

用法：python3 tests/check_clone_workbench.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
SCRIPT = SKILL / "scripts" / "clone_workbench.py"
ASSET = SKILL / "assets" / "ai-content-workspace-template.html"

PASS: list[str] = []
FAIL: list[str] = []


def chk(cond: bool, msg: str) -> bool:
    (PASS if cond else FAIL).append(msg)
    print(("  ok   " if cond else "  FAIL ") + msg, flush=True)
    return bool(cond)


# --------------------------------------------------------------------------
# 桩：记录调用 + 返回标准回执
# --------------------------------------------------------------------------
STUB_CREATE = r'''
import json, os, sys
args = sys.argv[1:]
lines = sys.stdin.read().split("\n", 1)
body = json.loads(lines[1]) if len(lines) > 1 and lines[1].strip() else {}
log = os.environ["STUB_LOG"]
# 用 pid 保证并行调用下的唯一性（真服务端返回的 id 天然唯一，这里只是模拟）
new_id = "NEWID%08dZZZZ" % os.getpid()
with open(os.path.join(log, "create%08d.json" % os.getpid()), "w", encoding="utf-8") as f:
    f.write(json.dumps({"kind": "create_database", "argv": args,
                        "title": body.get("title"),
                        "nprops": len(body.get("properties") or []),
                        "space_id": body.get("space_id", ""),
                        "properties": body.get("properties"),
                        "new_id": new_id}, ensure_ascii=False) + "\n")
print(json.dumps({"database_id": new_id, "space_id": "STUBSPACE",
                  "property_count": len(body.get("properties") or []),
                  "properties": body.get("properties")}, ensure_ascii=False))
'''

STUB_BATCH = r'''
import json, os, sys
lines = sys.stdin.read().split("\n", 1)
body = json.loads(lines[1]) if len(lines) > 1 and lines[1].strip() else {}
log = os.environ["STUB_LOG"]
with open(os.path.join(log, "batch%08d.json" % os.getpid()), "w", encoding="utf-8") as f:
    f.write(json.dumps({"kind": "batch_add", "dbid": body.get("database_id"),
                        "n": len(body.get("records") or []),
                        "records": body.get("records")}, ensure_ascii=False) + "\n")
print(json.dumps({"count": len(body.get("records") or []),
                  "records": [{"id": "STUBREC"} for _ in (body.get("records") or [])]},
                 ensure_ascii=False))
'''

STUB_IMPORT = r'''
import json, os, sys
args = sys.argv[1:]
log = os.environ["STUB_LOG"]
def opt(name):
    return args[args.index(name) + 1] if name in args else ""
payload_path = [a for a in args if a.endswith(".html")]
html = open(payload_path[0], encoding="utf-8").read() if payload_path else ""
with open(os.path.join(log, "import%08d.json" % os.getpid()), "w", encoding="utf-8") as f:
    f.write(json.dumps({"kind": "import_html", "argv": args,
                        "file_name": opt("--file-name"),
                        "databases": opt("--databases"),
                        "path": payload_path[0] if payload_path else "",
                        "html_len": len(html)}, ensure_ascii=False) + "\n")
print("KS_IMPORT_OK " + json.dumps({"node_block_id": "NEWPAGE0001ZZZZ",
                                    "file_name": opt("--file-name"),
                                    "url": "/space/d/NEWPAGE0001ZZZZ"}, ensure_ascii=False))
'''

STUB_SPACE = r'''
import json, os, sys
args = sys.argv[1:]
log = os.environ["STUB_LOG"]
def opt(name):
    return args[args.index(name) + 1] if name in args else ""
with open(os.path.join(log, "space%08d.json" % os.getpid()), "w", encoding="utf-8") as f:
    f.write(json.dumps({"kind": "space_api", "api": args[0] if args else "",
                        "node_id": opt("--node-id"),
                        "target": opt("--target-parent-id")}, ensure_ascii=False) + "\n")
print(json.dumps({"api": "space.workspace.move-node", "data": {"ok": True}}, ensure_ascii=False))
'''


def build_fake_library(root: Path) -> Path:
    lib = root / "library"
    (lib / "database").mkdir(parents=True)
    (lib / "page").mkdir(parents=True)
    (lib / "space_api.py").write_text(STUB_SPACE, encoding="utf-8")
    (lib / "database" / "create_database.py").write_text(STUB_CREATE, encoding="utf-8")
    (lib / "database" / "batch_add_database_records.py").write_text(STUB_BATCH, encoding="utf-8")
    (lib / "page" / "import_html.py").write_text(STUB_IMPORT, encoding="utf-8")
    return lib


def run_clone(work: Path, lib: Path, log: Path, extra: list[str], token: str = "stub-token"):
    log.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["STUB_LOG"] = str(log)
    cmd = [sys.executable, str(SCRIPT), "--token-stdin", "--library-dir", str(lib),
           "--work-dir", str(work)] + extra
    return subprocess.run(cmd, input=token + "\n", capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env, timeout=600)


def read_log(log: Path) -> list[dict]:
    """桩每次调用写一个独立文件，避免并行 append 交错。"""
    if not log.is_dir():
        return []
    out = []
    for f in sorted(log.glob("*.json")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def rewrite_manifest(html: str, mutate) -> str:
    """就地把内嵌清单改掉再写回去（用于反向对照造错）。"""
    open_m = '<script type="application/json" id="aiws-template-manifest">'
    i = html.index(open_m)
    j = html.index("</script>", i)
    man = json.loads(html[i + len(open_m):j])
    mutate(man)
    txt = json.dumps(man, ensure_ascii=False).replace("<", "\\u003c")
    return html[:i + len(open_m)] + txt + html[j:]


def manifest_of(html: str) -> dict:
    i = html.index('<script type="application/json" id="aiws-template-manifest">')
    j = html.index("</script>", i)
    return json.loads(html[i + len('<script type="application/json" id="aiws-template-manifest">'):j])


# --------------------------------------------------------------------------
def main() -> int:
    print("=" * 68)
    print("clone_workbench.py 全链路验收（资料库用桩脚本，不碰真账号）")
    print("=" * 68)

    if not ASSET.is_file():
        print("内置产物缺失：" + str(ASSET))
        return 1
    src_html = ASSET.read_text(encoding="utf-8", errors="replace")
    man = manifest_of(src_html)
    old_ids = [t["oldDatabaseId"] for t in man["tables"]]
    n_tables = len(man["tables"])
    n_recs = sum(len(t.get("records") or []) for t in man["tables"])

    tmp = Path(tempfile.mkdtemp(prefix="clonecheck_"))
    try:
        # ---------------- A 段：dry-run（纯本地） ----------------
        print("\n[A] dry-run：本地链路")
        w1 = tmp / "w1"
        r1 = run_clone(w1, build_fake_library(tmp / "lib_dry"), tmp / "dry.log", ["--dry-run"])
        chk(r1.returncode == 0, f"dry-run 退出码 0（实际 {r1.returncode}）")
        chk(f"11 张表、{n_recs} 条示例记录、149 个字段" in r1.stdout,
            f"清单校验报告 {n_tables} 张表 / {n_recs} 条记录 / 149 字段")
        chk("dry-run 结束｜本地检查" in r1.stdout and "0 失败" in r1.stdout, "dry-run 0 失败")

        pre = (w1 / "page" / "index.html").read_text(encoding="utf-8")
        fin = (w1 / "page" / "final.html").read_text(encoding="utf-8")
        chk("<!--AIWS-DEMO-BLOCK-START-->" not in pre and "<!--AIWS-MANIFEST-START-->" not in pre,
            "剥块后页面无演示块/清单块标记")
        chk("aiws_demo_data" not in pre, "剥块后无假 SDK 的本地存储键")
        chk(all(len(re.findall(r"(?<![A-Za-z0-9_-])" + re.escape(o) + r"(?![A-Za-z0-9_-])", pre)) == 1
                for o in old_ids),
            "剥块后 11 个旧表 id 各恰好出现 1 次（按独立 token 计）")
        chk(all(o not in fin for o in old_ids), "重映射后页面里零残留旧表 id")
        dry_ids = [f"DRY{t['key'].upper()}{'0' * 16}" for t in man["tables"]]
        chk(all(len(re.findall(r"(?<![A-Za-z0-9])" + re.escape(d) + r"(?![A-Za-z0-9])", fin)) == 1
                for d in dry_ids),
            f"重映射后页面含 {n_tables} 个新表 id，且每个恰好出现 1 次")
        chk("var DB = {" in fin, "重映射后 var DB 绑定表仍在")
        chk(len(list((w1 / "schemas").glob("*.json"))) == n_tables,
            f"产出 {n_tables} 份建表载荷")
        chk(len(list((w1 / "records").glob("*.json"))) == n_tables,
            f"产出 {n_tables} 份灌数据载荷")

        # 建表载荷的字段数必须与清单一致（字段丢了就会静默丢列）
        want = {t["key"]: len(t["properties"]) for t in man["tables"]}
        got = {p.stem: len(json.loads(p.read_text(encoding="utf-8"))["properties"])
               for p in (w1 / "schemas").glob("*.json")}
        chk(want == got, f"每张表的建表字段数与清单逐一相符（{len(want)} 张）")
        # 灌数据载荷的字段名必须都在该表字段里
        recfiles = {p.stem: json.loads(p.read_text(encoding="utf-8"))
                    for p in (w1 / "records").glob("*.json")}
        names = {t["key"]: {p["name"] for p in t["properties"]} for t in man["tables"]}
        badf = [k for k, rs in recfiles.items() for r in rs for f in r if f not in names[k]]
        chk(not badf, f"灌数据载荷无越界字段（越界：{badf[:3]}）")

        # ---------------- B 段：真跑（对着桩） ----------------
        print("\n[B] 全链路：建表 → 灌数据 → 重映射 → 导入 → 挂载")
        w2 = tmp / "w2"
        log2 = tmp / "run.log"
        r2 = run_clone(w2, build_fake_library(tmp / "lib_run"), log2, ["--keep-work-dir"])
        chk(r2.returncode == 0, f"全链路退出码 0（实际 {r2.returncode}）")
        if r2.returncode != 0:
            print(r2.stdout[-3000:])
        calls = read_log(log2)
        creates = [c for c in calls if c["kind"] == "create_database"]
        batches = [c for c in calls if c["kind"] == "batch_add"]
        imports = [c for c in calls if c["kind"] == "import_html"]
        moves = [c for c in calls if c["kind"] == "space_api"]

        chk(len(creates) == n_tables, f"建表调用 {len(creates)} 次（期望 {n_tables}）")
        chk({c["title"] for c in creates} == {t["title"] for t in man["tables"]},
            "建表调用逐张用了清单里的表名")
        chk(all(c["nprops"] == want[t["key"]] for c in creates
                for t in man["tables"] if t["title"] == c["title"]),
            "建表调用逐张传了正确字段数")
        new_ids = [c["new_id"] for c in creates]
        chk(len(set(new_ids)) == n_tables, f"{n_tables} 个新表 id 互不相同")
        chk(not set(new_ids) & set(old_ids), "新表 id 与旧表 id 无交集（重映射安全）")

        # 清单里有 2 张表（活动管理表 / AI 任务队列）示例记录为 0 条，
        # 空表不该产生灌数据调用 —— 期望批次只覆盖「有记录的表」。
        withrec = [t for t in man["tables"] if t.get("records")]
        n_withrec = len(withrec)
        db_new = [c["dbid"] for c in batches]
        chk(set(db_new) <= set(new_ids), "灌数据的落点全都在新建表里")
        chk(len(set(db_new)) == n_withrec,
            f"灌数据覆盖 {len(set(db_new))} 张表 == 有记录的 {n_withrec} 张")
        chk(not set(db_new) & set(old_ids), "灌数据没有落到任何旧表 id 上")
        chk(sum(c["n"] for c in batches) == n_recs,
            f"灌数据总条数 {sum(c['n'] for c in batches)}（期望 {n_recs}）")
        chk(len(batches) == n_withrec,
            f"每张有记录的表恰好 1 个灌数据批次（实际 {len(batches)}，期望 {n_withrec}）")
        chk(all(c["n"] <= 100 for c in batches), "每个批次都不超过 100 条上限")

        chk(len(imports) == 1, f"import_html 调用 1 次（实际 {len(imports)}）")
        if imports:
            dbs = json.loads(imports[0]["databases"])
            chk(len(dbs) == n_tables and {d["id"] for d in dbs} == set(new_ids),
                f"import 的 --databases 恰好是那 {n_tables} 个新表 id")
            chk(imports[0]["file_name"].endswith(".html"),
                f"import 传了 --file-name（{imports[0]['file_name']}）")

        chk(len(moves) == n_tables, f"move-node 调用 {len(moves)} 次（期望 {n_tables}）")
        chk(all(m["target"] == "NEWPAGE0001ZZZZ" for m in moves),
            "所有表都挂到同一个新页面节点下")
        chk({m["node_id"] for m in moves} == set(new_ids), "挂载对象是新表，不是旧表")

        # 导入的 HTML 必须是重映射后的那一份
        if imports:
            sent = Path(imports[0]["path"]).read_text(encoding="utf-8")
            chk(all(o not in sent for o in old_ids), "导入的 HTML 里零残留旧表 id")
            chk(all(sent.count(n) == 1 for n in new_ids),
                f"导入的 HTML 引用了那 {n_tables} 个新表 id，各 1 次")
            chk("<!--AIWS-DEMO-BLOCK-START-->" not in sent and
                'id="aiws-template-manifest"' not in sent,
                "导入的 HTML 已剥掉演示块与清单块")
            chk(sent.count("<!--AIWS-") == 0, "导入的 HTML 里无任何 AIWS 标记残留")

        print("\n[C] 反向对照（证明上面这些断言真的会失败）")
        # C1：清单里 内容类型 的选项被删掉一个，而记录还在用那个值 → 应报错中止
        def drop_option(m):
            for t in m["tables"]:
                for prop in t["properties"]:
                    for cfg in prop["config"].values():
                        if isinstance(cfg, dict) and isinstance(cfg.get("options"), list):
                            keep = [o for o in cfg["options"] if o.get("text") != "深度文章"]
                            if len(keep) != len(cfg["options"]):
                                cfg["options"] = keep
                                return
            raise AssertionError("测试自身失效：清单里找不到 深度文章 这个选项")
        broken = rewrite_manifest(src_html, drop_option)
        p = tmp / "broken_option.html"
        p.write_text(broken, encoding="utf-8")
        w3 = tmp / "w3"
        r3 = run_clone(w3, build_fake_library(tmp / "lib_c"), tmp / "c1.log",
                       ["--dry-run", "--source", str(p)])
        chk(r3.returncode != 0 and "不在选项内" in r3.stdout,
            "C1 清单里出现非法选项值时脚本报错并中止")

        # C2：删掉演示块标记 → 剥块应报错（不能产出半成品）
        broken2 = src_html.replace("<!--AIWS-DEMO-BLOCK-START-->", "")
        p2 = tmp / "broken_mark.html"
        p2.write_text(broken2, encoding="utf-8")
        r4 = run_clone(tmp / "w4", build_fake_library(tmp / "lib_c2"), tmp / "c2.log",
                       ["--dry-run", "--source", str(p2)])
        chk(r4.returncode != 0 and "演示块标记" in r4.stdout,
            "C2 标记缺失时剥块报错（不会静默产出残缺页）")

        # C3：把 page 的 DB 绑定删掉一行 → 旧 id 计数不成立，应报错
        # 只改 var DB 里那一处（清单里仍是原值）→ 剥块后该旧 id 出现 0 次，应报错
        _i = src_html.index("var DB = {")
        broken3 = src_html[:_i] + src_html[_i:].replace(old_ids[0], "TAMPERED" + old_ids[0], 1)
        p3 = tmp / "broken_db.html"
        p3.write_text(broken3, encoding="utf-8")
        r5 = run_clone(tmp / "w5", build_fake_library(tmp / "lib_c3"), tmp / "c3.log",
                       ["--dry-run", "--source", str(p3)])
        chk(r5.returncode != 0 and "旧表 id" in r5.stdout,
            "C3 DB 绑定缺一张表时重映射判据报错")

        # C4：伪装成「演示版」（无清单块）→ 应被识别并拒绝
        p4 = tmp / "fake_demo.html"
        p4.write_text("<html><body>demo</body></html>", encoding="utf-8")
        r6 = run_clone(tmp / "w6", build_fake_library(tmp / "lib_c4"), tmp / "c4.log",
                       ["--dry-run", "--source", str(p4)])
        chk(r6.returncode != 0 and "MANIFEST 标记" in r6.stdout,
            "C4 非模板产物（无清单）被拒绝，并提示该用哪个产物")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 68)
    print(f"PASS {len(PASS)} / FAIL {len(FAIL)}")
    for m in FAIL:
        print("  FAIL " + m)
    print("=" * 68)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
