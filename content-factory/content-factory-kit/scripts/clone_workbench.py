#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clone_workbench.py —— 把「创作小屋 · 灵感营地」内容运营工作台复刻到当前用户的资料库。

设计要点（为什么不是一个普通的 clone）：
    工作台页面里的 11 张表属于**原作者**账号，复刻者对其没有任何读权限。
    所以复刻**不能**用「读旧表 → 导出 CSV → 建新表」的标准 clone-flow
    （那条路在别人的账号里第一步就会因无权限失败）。

    本脚本走的是「清单建表」：
      ① 模板产物里内嵌了一份复刻清单（JSON），含 11 张表的建表字段与虚构示例数据；
      ② 按清单在**当前用户自己账号**里建表、灌示例数据；
      ③ 把页面里写死的旧表 id 全部改写成新表 id；
      ④ 再把页面导入资料库并挂好父子关系。

    全程不读原作者的任何一张表，因此不需要任何跨账号权限。

用法：
    # 推荐：用内置模板产物（离线，不依赖任何线上页面）
    python3 scripts/clone_workbench.py --token-stdin --dry-run < token.txt

    # 真正执行
    printf '%s' "$TOKEN" | python3 scripts/clone_workbench.py --token-stdin

    # 从线上产物复刻（页面被更新过时用它拿最新版）
    python3 scripts/clone_workbench.py --token-stdin \\
        --source https://workbuddy-space-static.codebuddy.work/page/<id>/<ver>/index.html

    # 只建表灌数据，不导入页面
    python3 scripts/clone_workbench.py --token-stdin --skip-page

前置依赖：资料库（library）技能。脚本通过 --library-dir 定位它；
        不传时依次尝试 $CODEBUDDY_SKILL_DIR / $CODEBUDDY_PLUGIN_ROOT/skills/library / 自动探测。

安全约束：
    - 只做「新增」不做「删除」：不删表、不删记录、不删节点。
    - --dry-run 不发起任何写请求，只把将要执行的命令与产物写到工作目录。
    - 不复现 token；所有子进程输出经脱敏后再回显。
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCHEMA_ID = "aiws-template/1"
# 与资料库 database/_db_types.py 的 VALID_TYPE_KEYS 保持一致（建表脚本按这个白名单校验）
VALID_TYPES = {
    "text", "number", "currency", "select", "multi_select",
    "date", "checkbox", "url", "email", "phone_number",
    "image", "attachment", "person",
}
DEMO_MARK_START = "<!--AIWS-DEMO-BLOCK-START-->"
DEMO_MARK_END = "<!--AIWS-DEMO-BLOCK-END-->"
MANIFEST_MARK_START = "<!--AIWS-MANIFEST-START-->"
MANIFEST_MARK_END = "<!--AIWS-MANIFEST-END-->"
MANIFEST_SCRIPT_OPEN = '<script type="application/json" id="aiws-template-manifest">'
BATCH_LIMIT = 100

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
DEFAULT_SOURCE = SKILL_ROOT / "assets" / "ai-content-workspace-template.html"

OK: list[str] = []
WARN: list[str] = []
ERR: list[str] = []


def log(msg: str) -> None:
    print(msg, flush=True)


def ok(msg: str) -> None:
    OK.append(msg)
    log("  ok   " + msg)


def warn(msg: str) -> None:
    WARN.append(msg)
    log("  WARN " + msg)


def die(msg: str, code: int = 1):
    ERR.append(msg)
    log("  FAIL " + msg)
    log("")
    log("复刻中止。已完成的步骤不会回滚（资料库不支持删除表），")
    log("如已建出表，请到资料库界面手动清理后再重跑。")
    sys.exit(code)


# --------------------------------------------------------------------------
# token / 子进程
# --------------------------------------------------------------------------

def acquire_token(use_stdin: bool) -> str:
    if use_stdin:
        raw = sys.stdin.readline()
        tok = raw.strip()
        if not tok:
            die("--token-stdin 未从 stdin 首行读到 token")
        return tok
    tok = os.environ.get("LIBRARY_TOKEN", "").strip()
    if not tok:
        die("未提供 token：用 --token-stdin 或设 LIBRARY_TOKEN")
    return tok


def scrub(text: str) -> str:
    """回显前脱敏：token、长签名串。"""
    text = re.sub(r"(?i)(token[\"'=:\s]+)[A-Za-z0-9._\-]{12,}", r"\1***", text)
    text = re.sub(r"op_[A-Za-z0-9]{16,}", "op_***", text)
    return text


def run(cmd: list[str], stdin_text: str = "", timeout: int = 180) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, input=stdin_text, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, p.stdout or "", p.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s"
    except FileNotFoundError:
        return 127, "", "脚本不存在: " + cmd[0]


def extract_json(text: str) -> dict | None:
    """从子进程输出里抓出第一个可解析的 JSON 对象。"""
    for m in re.finditer(r"\{", text):
        depth, i = 0, m.start()
        for j in range(i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[i:j + 1])
                        if isinstance(obj, dict):
                            return obj
                    except json.JSONDecodeError:
                        pass
                    break
    return None


def find_library_dir(explicit: str) -> Path:
    cands = []
    if explicit:
        cands.append(Path(explicit))
    for env in ("CODEBUDDY_SKILL_DIR", "CODEBUDDY_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT"):
        v = os.environ.get(env, "").strip()
        if v:
            cands.append(Path(v))
            cands.append(Path(v) / "skills" / "library")
    roots = [
        Path(os.environ.get("APPDATA", "")) / ".." / "Local" / "Programs" / "WorkBuddy",
        Path("/Applications/WorkBuddy.app"),
    ]
    for r in roots:
        try:
            if r.exists():
                for hit in r.glob("**/skills/library/space_api.py"):
                    cands.append(hit.parent)
        except OSError:
            pass
    for c in cands:
        try:
            if (c / "space_api.py").is_file() and (c / "database" / "create_database.py").is_file():
                return c.resolve()
        except OSError:
            continue
    die("找不到资料库（library）技能。请用 --library-dir 指定其绝对路径。"
        "（该技能必须包含 space_api.py 与 database/create_database.py）")
    raise SystemExit(1)


# --------------------------------------------------------------------------
# 取产物
# --------------------------------------------------------------------------

def _http_get(url: str, timeout: float = 30.0) -> bytes:
    """直连优先、失败再走代理的双策略重试（本机代理会拦截静态产物域名）。"""
    req = urllib.request.Request(url, headers={"User-Agent": "content-factory-kit/1.0"})
    attempts = [
        urllib.request.build_opener(urllib.request.ProxyHandler({})),   # 直连
        urllib.request.build_opener(),                                  # 跟随系统代理
    ]
    last = None
    for i in range(3):
        for opener in attempts:
            try:
                with opener.open(req, timeout=timeout) as r:
                    return r.read()
            except Exception as e:      # noqa: BLE001 - 网络异常一律重试
                last = e
        time.sleep(1.2 * (i + 1))
    raise RuntimeError(f"下载失败（直连与代理都试过 3 轮）：{last}")


def resolve_source(source: str, work: Path) -> tuple[Path, str]:
    """返回 (本地入口 HTML 路径, 来源描述)。"""
    if source.startswith(("http://", "https://")):
        log(f"[1/7] 下载产物：{source}")
        data = _http_get(source)
        if len(data) < 100_000:
            die(f"下载到的内容只有 {len(data)} 字节，不像完整产物（可能拿到了 SPA 外壳或错误页）")
        out = work / "src" / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        ok(f"产物已下载到 {out}（{len(data)} 字节）")
        return out, source

    p = Path(source).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    if not p.is_file():
        die(f"产物文件不存在：{p}")
    log(f"[1/7] 使用本地产物：{p}")
    ok(f"本地产物 {p.name}（{p.stat().st_size} 字节）")
    return p, str(p)


# --------------------------------------------------------------------------
# 清单
# --------------------------------------------------------------------------

def extract_manifest(html: str) -> tuple[dict, str]:
    log("[2/7] 解析内嵌复刻清单")
    if html.count(MANIFEST_MARK_START) != 1 or html.count(MANIFEST_MARK_END) != 1:
        die("产物里找不到（或找到多份）MANIFEST 标记，不是有效的模板产物。"
            "请确认用的是 build.py --demo --keep-inject 产出的模板版，而不是演示版/正式版。")
    i = html.index(MANIFEST_SCRIPT_OPEN)
    j = html.index("</script>", i)
    raw = html[i + len(MANIFEST_SCRIPT_OPEN):j]
    try:
        man = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"清单 JSON 解析失败：{e}")
    if man.get("schema") != SCHEMA_ID:
        die(f"清单 schema 不匹配：期望 {SCHEMA_ID}，实际 {man.get('schema')!r}")
    ok(f"清单已解析（schema={SCHEMA_ID}）")
    return man, raw


def options_of(config_value) -> set | None:
    """从 select / multi_select 的 config 值里抽出选项文本集合。

    真实表结构里这个值可能是多种形状（建表脚本对它是原样透传给服务端的）：
        ["A", "B"]                                  —— 扁平字符串列表
        [{"text": "A", "id": "...", "style": n}]    —— 对象列表
        {"options": [ ... ]}                        —— 再包一层 options
    抽不出来就返回 None，表示「本次不做取值校验」，而不是当成空集合（那会误报）。
    """
    if isinstance(config_value, dict):
        return options_of(config_value.get("options"))
    if not isinstance(config_value, list):
        return None
    texts = set()
    for item in config_value:
        if isinstance(item, str):
            texts.add(item)
        elif isinstance(item, dict) and isinstance(item.get("text"), str):
            texts.add(item["text"])
        else:
            return None
    return texts


def validate_manifest(man: dict) -> None:
    log("[3/7] 校验清单内容")
    tables = man.get("tables")
    if not isinstance(tables, list) or not tables:
        die("清单 tables 为空")

    seen_keys, seen_old = set(), set()
    total_records = 0
    for t in tables:
        for f in ("key", "title", "oldDatabaseId", "properties"):
            if not t.get(f):
                die(f"清单表项缺字段 {f}：{json.dumps(t, ensure_ascii=False)[:120]}")
        if t["key"] in seen_keys:
            die(f"清单里表 key 重复：{t['key']}")
        if t["oldDatabaseId"] in seen_old:
            die(f"清单里 oldDatabaseId 重复：{t['oldDatabaseId']}")
        seen_keys.add(t["key"])
        seen_old.add(t["oldDatabaseId"])

        props = t["properties"]
        names = []
        opts: dict[str, set] = {}
        for p in props:
            name, cfg = p.get("name"), p.get("config")
            if not name or not isinstance(cfg, dict) or len(cfg) != 1:
                die(f"[{t['title']}] 字段定义非法：{json.dumps(p, ensure_ascii=False)[:120]}")
            if not (set(cfg) & VALID_TYPES) or len(set(cfg) & VALID_TYPES) != 1:
                die(f"[{t['title']}] 字段「{name}」的类型 {list(cfg)} 不是合法类型"
                    f"（建表脚本只认 {', '.join(sorted(VALID_TYPES))}）")
            ptype = next(iter(set(cfg) & VALID_TYPES))
            names.append(name)
            if ptype in ("select", "multi_select"):
                o = options_of(cfg[ptype])
                if o:
                    opts[name] = o
        if len(names) != len(set(names)):
            die(f"[{t['title']}] 字段名有重复")
        nameset = set(names)

        for r_i, rec in enumerate(t.get("records") or []):
            if not isinstance(rec, dict):
                die(f"[{t['title']}] 第 {r_i + 1} 条记录不是对象")
            for kname, kval in rec.items():
                if kname not in nameset:
                    die(f"[{t['title']}] 第 {r_i + 1} 条记录含表中不存在的字段「{kname}」")
                if kname in opts and isinstance(kval, dict):
                    raw = kval.get("select")
                    if raw is None:
                        raw = kval.get("multi_select")
                    vals = raw if isinstance(raw, list) else [raw]
                    bad = [v for v in vals if v and v not in opts[kname]]
                    if bad:
                        die(f"[{t['title']}·{kname}] 第 {r_i + 1} 条取值 {bad} 不在选项内"
                            f"（服务端会静默丢弃）")
        total_records += len(t.get("records") or [])

    ok(f"清单有效：{len(tables)} 张表、{total_records} 条示例记录、"
       f"{sum(len(t['properties']) for t in tables)} 个字段")


# --------------------------------------------------------------------------
# 剥块 + 重映射
# --------------------------------------------------------------------------

def count_token(html: str, tok: str) -> int:
    """按「独立 token」计数，而不是子串计数。

    表 id 是裸串，页面里可能出现 `TAMPERED<id>` 这种粘连形式；
    用子串计数会把粘连的也算进来，于是「一个 id 只被绑定一次」这条判据会失真。
    """
    return len(re.findall(r"(?<![A-Za-z0-9_-])" + re.escape(tok) + r"(?![A-Za-z0-9_-])", html))


def strip_template_blocks(html: str, man: dict) -> str:
    log("[4/7] 剥掉演示块与清单块，产出可工作的页面")
    db = man.get("demoBlock") or {}
    starts = [db.get("start") or DEMO_MARK_START]
    ends = [db.get("end") or DEMO_MARK_END]

    for s, e in zip(starts, ends):
        if html.count(s) != 1 or html.count(e) != 1:
            die(f"演示块标记缺失或重复（{s} ×{html.count(s)} / {e} ×{html.count(e)}）")
        i, j = html.index(s), html.index(e) + len(e)
        html = html[:i] + html[j:]
    ok("演示块已整块删除（假 SDK 不再接管数据读写）")

    i, j = html.index(MANIFEST_MARK_START), html.index(MANIFEST_MARK_END) + len(MANIFEST_MARK_END)
    html = html[:i] + html[j:]
    ok("清单块已删除（复刻产物是工作页，不是模板页）")

    for bad in (DEMO_MARK_START, MANIFEST_MARK_START, "aiws_demo_data", "window.__DEMO_DB__ = buildApi()"):
        if bad in html:
            die(f"剥块不干净，仍残留：{bad}")
    ok("剥块自检通过：无残留标记、无假 SDK 痕迹")

    old_ids = [t["oldDatabaseId"] for t in man["tables"]]
    if "var DB = {" not in html:
        die("剥块后找不到 `var DB = {`，产物结构不符合预期")
    for oid in old_ids:
        n = count_token(html, oid)
        if n != 1:
            die(f"旧表 id {oid} 在剥块后应恰好出现 1 次，实际 {n} 次（复刻会漏改或多改）")
    ok(f"11 张旧表 id 各恰好出现 1 次，重映射判据成立")
    return html


def remap_ids(html: str, mapping: dict[str, str]) -> str:
    """把旧表 id 换成新表 id，并跑双重硬门校验。"""
    old_set, new_set = set(mapping), set(mapping.values())
    if old_set & new_set:
        die("新旧 id 集合有交集，重映射会产生链式替换")
    before = {o: count_token(html, o) for o in mapping}
    out = html
    for o, n in mapping.items():
        out = re.sub(r"(?<![A-Za-z0-9_-])" + re.escape(o) + r"(?![A-Za-z0-9_-])", n, out)
    after = {n: count_token(out, n) for n in mapping.values()}

    left = [o for o in mapping if count_token(out, o)]
    if left:
        die(f"重映射后仍残留旧 id：{left}")
    for o, n in mapping.items():
        if after[n] != before[o]:
            die(f"重映射计数不符：{o}({before[o]}) → {n}({after[n]})")
    ok(f"重映射完成并通过双重硬门：无残留旧 id；{len(mapping)} 张表新旧出现次数逐一相等")
    return out


# --------------------------------------------------------------------------
# 写库
# --------------------------------------------------------------------------

def make_tables(lib: Path, token: str, tables: list[dict], space_id: str,
                parent_id: str, work: Path, conc: int, dry: bool) -> dict[str, str]:
    log("[5/7] 建表（只新建，不动任何已有表）")
    script = lib / "database" / "create_database.py"

    def one(t: dict) -> tuple[str, str]:
        schema = {"title": t["title"], "properties": t["properties"]}
        if space_id:
            schema["space_id"] = space_id
        if parent_id:
            schema["parent_id"] = parent_id
        body = json.dumps(schema, ensure_ascii=False)
        (work / "schemas" / f"{t['key']}.json").write_text(
            json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
        if dry:
            return t["key"], ""
        code, out, err = run([sys.executable, str(script), "--token-stdin", "--stdin"],
                             stdin_text=token + "\n" + body)
        res = extract_json(out)
        if code != 0 or not res or res.get("error") or not res.get("database_id"):
            return t["key"], "ERR:" + scrub((res or {}).get("error") or err or out)[:200]
        if res.get("property_count") not in (None, len(t["properties"])):
            return t["key"], (f"ERR:建表字段数不符 期望 {len(t['properties'])} "
                              f"实际 {res.get('property_count')}")
        return t["key"], str(res["database_id"])

    mapping: dict[str, str] = {}
    seen_new: set[str] = set()
    with futures.ThreadPoolExecutor(max_workers=conc) as ex:
        for key, val in ex.map(one, tables):
            t = next(x for x in tables if x["key"] == key)
            if dry:
                # dry-run 也用「形状合法的合成新 id」把重映射真跑一遍，
                # 这样本地演练覆盖的是真实代码路径，而不是跳过它。
                mapping[t["oldDatabaseId"]] = f"DRY{key.upper()}{'0' * 16}"
                continue
            if val.startswith("ERR:"):
                die(f"建表失败 [{t['title']}]：{val[4:]}")
            if val in seen_new:
                die(f"服务端返回了重复的新表 id {val}（两张表会指向同一张表），已中止")
            if val in {x["oldDatabaseId"] for x in tables}:
                die(f"新表 id {val} 与旧表 id 撞了，重映射会出错，已中止")
            seen_new.add(val)
            mapping[t["oldDatabaseId"]] = val
            ok(f"建表成功 {t['title']} → {val}（{len(t['properties'])} 字段）")
    if dry:
        ok(f"dry-run：{len(tables)} 张表的建表载荷已写到 {work / 'schemas'}")
    return mapping


def seed_records(lib: Path, token: str, tables: list[dict], mapping: dict[str, str],
                 work: Path, conc: int, dry: bool) -> None:
    log("[6/7] 灌示例数据")
    script = lib / "database" / "batch_add_database_records.py"
    jobs = []
    for t in tables:
        recs = t.get("records") or []
        (work / "records" / f"{t['key']}.json").write_text(
            json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")
        new_id = mapping[t["oldDatabaseId"]]
        for i in range(0, len(recs), BATCH_LIMIT):
            jobs.append((t, new_id, recs[i:i + BATCH_LIMIT], i))
    if not jobs:
        ok("清单里没有示例记录，跳过")
        return

    def one(job) -> tuple[str, int, str]:
        t, new_id, chunk, off = job
        if dry:
            return t["title"], len(chunk), ""
        body = json.dumps({"database_id": new_id, "records": chunk}, ensure_ascii=False)
        code, out, err = run([sys.executable, str(script), "--token-stdin", "--stdin"],
                             stdin_text=token + "\n" + body)
        res = extract_json(out)
        if code != 0 or not res or res.get("error"):
            return t["title"], 0, "ERR:" + scrub((res or {}).get("error") or err or out)[:200]
        n = None
        for k in ("count", "added", "total", "success_count", "successCount"):
            if isinstance(res.get(k), int):
                n = res[k]
                break
        if n is None and isinstance(res.get("records"), list):
            n = len(res["records"])
        if n is not None and n != len(chunk):
            return t["title"], 0, f"ERR:写入条数不符 期望 {len(chunk)} 实际 {n}"
        return t["title"], len(chunk), ""

    written, failed = 0, 0
    with futures.ThreadPoolExecutor(max_workers=conc) as ex:
        for title, n, err in ex.map(one, jobs):
            if err:
                failed += 1
                log(f"  FAIL 灌数据失败 [{title}]：{err[4:]}")
            else:
                written += n
    if failed:
        die(f"{failed} 个批次灌数据失败，页面未导入（避免产出半空的工作台）")
    if dry:
        ok(f"dry-run：{len(jobs)} 个批次的灌数据载荷已写到 {work / 'records'}")
    else:
        ok(f"示例数据已写入 {written} 条（{len(jobs)} 个批次）")


def import_page(lib: Path, token: str, html_path: Path, page_name: str,
                mapping: dict[str, str], space_id: str, dry: bool) -> str:
    log("[7/7] 导入页面并挂载数据表")
    script = lib / "page" / "import_html.py"
    dbs = json.dumps([{"id": v} for v in mapping.values()], ensure_ascii=False)
    cmd = [sys.executable, str(script), "--token-stdin", str(html_path),
           "--file-name", page_name, "--databases", dbs]
    if space_id:
        cmd += ["--space-id", space_id]
    if dry:
        ok(f"dry-run：将执行 import_html.py --file-name {page_name!r} --databases "
           f"[{len(mapping)} 张表]")
        return ""
    code, out, err = run(cmd, stdin_text=token + "\n", timeout=300)
    res = extract_json(out)
    if code != 0 or not res or res.get("error") or not res.get("node_block_id"):
        die("页面导入失败：" + scrub((res or {}).get("error") or err or out)[:300])
    node = str(res["node_block_id"])
    ok(f"页面已导入 → {node}")

    move_script = lib / "space_api.py"

    def move(new_id: str) -> tuple[str, str]:
        code2, out2, err2 = run(
            [sys.executable, str(move_script), "space.workspace.move-node",
             "--token-stdin", "--node-id", new_id, "--target-parent-id", node],
            stdin_text=token + "\n")
        if '"error"' in out2 or '"api"' not in out2:
            return new_id, scrub(out2 or err2)[:200]
        return new_id, ""

    bad = 0
    with futures.ThreadPoolExecutor(max_workers=min(6, len(mapping))) as ex:
        for new_id, err2 in ex.map(move, list(mapping.values())):
            if err2:
                bad += 1
                log(f"  FAIL 挂载失败 {new_id}：{err2}")
    if bad:
        warn(f"{bad} 张表没能挂到页面下（表已建好、数据已写入，可在资料库里手动拖进去）")
    else:
        ok(f"{len(mapping)} 张表已挂到页面节点下")
    return node


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="复刻「创作小屋」内容运营工作台到资料库")
    ap.add_argument("--source", default=str(DEFAULT_SOURCE),
                    help="模板产物路径或发布态静态地址；默认用技能内置产物")
    ap.add_argument("--work-dir", default="", help="中间产物目录，默认 ./clone_work")
    ap.add_argument("--token-stdin", action="store_true", help="从 stdin 首行读 token")
    ap.add_argument("--library-dir", default="", help="资料库技能目录的绝对路径")
    ap.add_argument("--space-id", default="", help="目标空间 id，不传走默认空间")
    ap.add_argument("--parent-id", default="", help="新表的父节点 id，不传落空间根")
    ap.add_argument("--page-name", default="", help="新页面展示名，默认取清单里的 page.title")
    ap.add_argument("--keep-work-dir", action="store_true", help="跑完保留中间产物")
    ap.add_argument("--dry-run", action="store_true", help="只做本地部分并打印将要执行的写操作")
    ap.add_argument("--skip-page", action="store_true", help="只建表灌数据，不导入页面")
    ap.add_argument("--concurrency", type=int, default=6)
    a = ap.parse_args()

    work = Path(a.work_dir).expanduser() if a.work_dir else (Path.cwd() / "clone_work")
    if not work.is_absolute():
        work = (Path.cwd() / work).resolve()
    for sub in ("schemas", "records"):
        (work / sub).mkdir(parents=True, exist_ok=True)

    log("=" * 68)
    log("复刻「创作小屋 · 灵感营地」内容运营工作台")
    log("=" * 68)
    if a.dry_run:
        log("模式：dry-run（不发起任何写请求）")
    log("")

    token = acquire_token(a.token_stdin)
    lib = find_library_dir(a.library_dir)
    ok(f"资料库技能已定位：{lib}")

    src_path, src_desc = resolve_source(a.source, work)
    html = src_path.read_text(encoding="utf-8", errors="replace")
    man, _ = extract_manifest(html)
    validate_manifest(man)

    stripped = strip_template_blocks(html, man)
    page_name = a.page_name or ((man.get("page") or {}).get("fileName")
                                or (man.get("page") or {}).get("title") or "index.html")
    if not page_name.endswith(".html"):
        page_name += ".html"
    pre_path = work / "page" / "index.html"
    pre_path.parent.mkdir(parents=True, exist_ok=True)
    pre_path.write_text(stripped, encoding="utf-8")
    ok(f"剥块后的页面写到 {pre_path}")

    tables = man["tables"]
    mapping = make_tables(lib, token, tables, a.space_id, a.parent_id, work,
                          max(1, a.concurrency), a.dry_run)

    if not a.dry_run:
        (work / "mapping.tsv").write_text(
            "".join(f"{o}\t{n}\n" for o, n in mapping.items()), encoding="utf-8")

    seed_records(lib, token, tables, mapping, work, max(1, a.concurrency), a.dry_run)

    final = remap_ids(stripped, mapping)
    final_path = work / "page" / "final.html"
    final_path.write_text(final, encoding="utf-8")
    ok(f"重映射后的页面写到 {final_path}")

    node = ""
    if a.skip_page:
        warn("--skip-page：未导入页面。之后可手动跑："
             f"import_html.py --token-stdin {final_path} --file-name {page_name} --databases ...")
    else:
        node = import_page(lib, token, final_path, page_name, mapping,
                           a.space_id, a.dry_run)

    log("")
    log("=" * 68)
    if a.dry_run:
        log(f"dry-run 结束｜本地检查 {len(OK)} 项通过、{len(WARN)} 项提醒、0 失败")
        log(f"中间产物：{work}")
        log("去掉 --dry-run 即可真正执行（会在你账号里新建 11 张表、82 条记录、1 个页面）")
    else:
        log(f"复刻完成｜{len(OK)} 项通过、{len(WARN)} 项提醒")
        log(f"新页面节点：{node}")
        log(f"打开：https://www.workbuddy.cn/space/d/{node}")
        log(f"新建 {len(mapping)} 张表，共 "
            f"{sum(len(t.get('records') or []) for t in tables)} 条示例记录")
        log("示例数据是虚构的，可直接改可清空；工作台页面读的是你自己的表。")
        log("执行层（研究/写作/多平台/配图/沉淀五套规范、风格指南、自动化）不在复刻范围内，"
            "需要另外安装对应技能。")
    log("=" * 68)

    if not a.dry_run and not a.keep_work_dir:
        import shutil
        shutil.rmtree(work, ignore_errors=True)
        log(f"中间产物已清理（用 --keep-work-dir 可保留）")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("\n已中断。")
        sys.exit(130)
