# -*- coding: utf-8 -*-
"""measure_titles.py 的验收测试（纯本地，不联网、不写外部账号）。

跑法：
    python3 tests/check_measure_titles.py
全部通过退出码 0，否则 1。
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SCRIPT = os.path.join(SKILL, "scripts", "measure_titles.py")
FIX = os.path.join(HERE, "fixtures")

PASS = 0
FAIL = 0
MSGS = []


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        MSGS.append("  PASS  %s" % name)
    else:
        FAIL += 1
        MSGS.append("  FAIL  %s %s" % (name, extra))


def run(*args):
    """返回 (rc, stdout, stderr)。"""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, SCRIPT, *args],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env)
    return p.returncode, p.stdout or "", p.stderr or ""


def run_all(*args):
    """返回 (rc, stdout+stderr 合并)，用于断言报错文本。"""
    rc, out, err = run(*args)
    return rc, out + err


def jrun(*args):
    rc, out, err = run(*args, "--json")
    if rc != 0:
        return None, rc, out + err
    # 取最后一个 JSON 对象（防止前面有杂音）
    s = out[out.find("{"):]
    try:
        return json.loads(s), rc, ""
    except Exception as e:
        return None, rc, "JSON 解析失败: %s\n%s" % (e, out[:400])


print("=== measure_titles.py 验收 ===")

# ---- A. 四种语料形态都能解析 ----
print("\n[A] 语料形态")
csv_j, rc, err = jrun(os.path.join(FIX, "titles.csv"))
check("A1 CSV 解析成功", csv_j is not None, err)
check("A2 CSV 条数=6", csv_j and csv_j.get("n") == 6, str(csv_j and csv_j.get("n")))
check("A3 CSV 认出了日期列（有分期）", bool(csv_j and csv_j.get("by_year")), "无 by_year")
check("A4 CSV 冒号率=50%(6 条中 3 条带冒号)",
      csv_j and csv_j["features"]["冒号（两段式）"]["n"] == 3,
      str(csv_j and csv_j["features"]["冒号（两段式）"]))
check("A5 CSV 栏目前缀=1（【鸿蒙】）",
      csv_j and csv_j["features"]["栏目前缀【/（"]["n"] == 1,
      str(csv_j and csv_j["features"]["栏目前缀【/（"]))
check("A6 CSV 第一人称=1（我用三行脚本）",
      csv_j and csv_j["features"]["第一人称（我/咱）"]["n"] == 1,
      str(csv_j and csv_j["features"]["第一人称（我/咱）"]))

txt_j, rc, err = jrun(os.path.join(FIX, "titles.txt"))
check("A7 TXT 解析成功", txt_j is not None, err)
check("A8 TXT 剥掉 #、-、数字序号后条数=5", txt_j and txt_j.get("n") == 5,
      str(txt_j and txt_j.get("n")))
check("A9 TXT 栏目前缀=1（【鸿蒙】未被剥离）",
      txt_j and txt_j["features"]["栏目前缀【/（"]["n"] == 1,
      str(txt_j and txt_j["features"]["栏目前缀【/（"]))
# 用非 json 模式确认首行标题干净
rc2, out2, _ = run(os.path.join(FIX, "titles.txt"))
check("A10 TXT 输出不含残留 '1. 时序'", "1. 时序" not in out2, out2[:200])

lst_j, rc, err = jrun(os.path.join(FIX, "titles_list.json"))
check("A11 JSON 字符串数组解析成功", lst_j is not None, err)
check("A12 JSON 字符串数组条数=5", lst_j and lst_j.get("n") == 5,
      str(lst_j and lst_j.get("n")))
check("A13 JSON 字符串数组无分期（无日期字段）", lst_j and "by_year" not in lst_j,
      "不该有 by_year")

# 模拟 shelves 形态
shelves = {"shelves": [{"name": "x", "items": [
    {"t": "KES Operator：声明式部署", "d": "2025-09-09"},
    {"t": "让异构增量同步飞起来！", "d": "2025-03-02"},
    {"t": "【鸿蒙】ArkTS 入门笔记", "d": "2022-05-20"},
]}]}
tmp = os.path.join(HERE, "_tmp_shelves.json")
open(tmp, "w", encoding="utf-8").write(json.dumps(shelves, ensure_ascii=False))
shel_j, rc, err = jrun(tmp)
check("A14 shelves 嵌套形态解析成功", shel_j is not None, err)
check("A15 shelves 条数=3", shel_j and shel_j.get("n") == 3, str(shel_j and shel_j.get("n")))
check("A16 shelves 分期识别到 2022/2025",
      shel_j and set(shel_j.get("by_year", {}).keys()) == {"2022", "2025"},
      str(shel_j and shel_j.get("by_year", {}).keys()))
os.remove(tmp)

# ---- B. 列名指定与报错 ----
print("\n[B] 列名与报错")
rc3, out3, _ = run(os.path.join(FIX, "titles.csv"), "--title-field", "标题")
check("B1 显式指定存在的列名可跑通", rc3 == 0, "rc=%d %s" % (rc3, out3[:200]))

rc4, out4 = run_all(os.path.join(FIX, "titles.csv"), "--title-field", "不存在的列")
check("B2 指定不存在的列名 → 非零退出", rc4 != 0, "rc=%d" % rc4)
check("B3 报错信息给出可用列", "可用列" in out4, out4[:300])

rc5, out5 = run_all(os.path.join(HERE, "no_such_file_xyz.csv"))
check("B4 文件不存在 → 非零退出", rc5 != 0, "rc=%d" % rc5)
check("B5 文件不存在给明确提示", "找不到语料文件" in out5, out5[:200])

rc6, out6 = run_all("https://example.com/titles.csv")
check("B6 URL 输入 → 非零退出并说明不联网", rc6 != 0 and "不联网" in out6,
      "rc=%d %s" % (rc6, out6[:200]))

# ---- C. 词/正则统计 ----
print("\n[C] 词与正则")
w_j, rc, err = jrun(os.path.join(FIX, "titles_list.json"), "--words", "让.*飞起来,ArkTS,实战")
check("C1 正则 '让.*飞起来' 命中 1", w_j and w_j.get("words", {}).get("让.*飞起来", {}).get("n") == 1,
      str(w_j and w_j.get("words")))
check("C2 字面 'ArkTS' 命中 1", w_j and w_j["words"]["ArkTS"]["n"] == 1,
      str(w_j and w_j.get("words")))
check("C3 未命中词记 0（'实战'）", w_j and w_j["words"]["实战"]["n"] == 0,
      str(w_j and w_j.get("words")))
check("C4 编不成的 token 按字面处理不崩",
      run(os.path.join(FIX, "titles_list.json"), "--words", "KES[")[0] == 0, "")

# ---- D. 空语料负对照 ----
print("\n[D] 边界与负对照")
empty = os.path.join(HERE, "_tmp_empty.txt")
open(empty, "w", encoding="utf-8").write("# 只有注释\n\n   \n")
rc7, out7, _ = run(empty)
check("D1 空语料不崩（rc=0）", rc7 == 0, "rc=%d" % rc7)
check("D2 空语料给出提示", "没有解析到任何标题" in out7, out7[:200])
ej, rc, _ = jrun(empty)
check("D3 空语料 JSON 里 n=0", ej is not None and ej.get("n") == 0, str(ej))
os.remove(empty)

# 只读：脚本不得修改语料文件
before = open(os.path.join(FIX, "titles_list.json"), encoding="utf-8").read()
run(os.path.join(FIX, "titles_list.json"))
after = open(os.path.join(FIX, "titles_list.json"), encoding="utf-8").read()
check("D4 脚本不修改语料（只读）", before == after, "")

print("\n".join(MSGS))
print("\n=== 合计：PASS %d / FAIL %d ===" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
