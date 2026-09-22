---
name: content-research-spec
description: 创作小屋内容工厂的研究绑定层。规定派发给 WorkBuddy 的研究/成篇任务（AI 任务队列）该怎么跑：先读套件里的通用研究规范，再按本机写回契约（queue.py 命令、落点字段、来源回流表 ID）写回工作台。当需要执行队列里的研究或一键成篇任务、判断研究产出是否达标、或要调整研究口径时使用。
agent_created: true
---

# 内容研究 · 本机绑定层

创作小屋（AI 自媒体运营工作台）里的研究，是 WorkBuddy 亲自联网做的：页面只生成一张任务卡写进队列，
真正的检索、核查、成文都由领取任务的 WorkBuddy 完成。

> ## 通用规范在哪（先读它，再读本文）
>
> 研究的通用规则——执行前三件确认、检索策略、**8 段产出结构**、篇幅预算、
> 写回前验收清单、失败与降级处置——**唯一真源是**：
>
> **`~/.workbuddy/skills/content-factory-kit/references/research.md`**
> （技能 `content-factory-kit` 支路 A；若套件装在别处，用技能名找到它）
>
> **本 skill 不重复那份内容**，只写两样：**本机怎么写回**（命令、表 ID、落点字段）、
> **本机踩过的坑**。改通用口径请改套件那份，别改这里——这里是绑定层，不是第二份规范。

## 何时使用

- 队列里的研究类动作：`research` `searchres` `orgsources` `compete` `factcheck`
  `callresearch` `researchteam` `judge` `pipeline`
- 判断一份研究摘要 / 大纲 / 正文能不能写回工作台
- 调整研究阶段的产出标准、验收口径

不适用：页面视觉与交互改动（走 `library-live-page-update`）；纯粹的选题推荐（走每日选题流水线）；
写作与改稿（走 `content-writing-spec`）。

## 一、本机工具映射

通用规范里只写「搜索找线索 → 抓取取原文 → 事实核查工具 → 资讯聚合」，本机对应：

**`WebSearch` 找线索 → `WebFetch` 取原文 → `anysearch` 做事实核实 → `AIHOT` 看是否已有中文报道与热度。**

## 二、本机写回契约

工具：`tools/queue.py`（**不要绕过它直连 batch_update**，包装类型写错会静默丢值）。
工作目录 = 工作台项目根（`ai-workspace/` 所在的仓库根）。

```bash
export PATH="/usr/bin:/bin:/mingw64/bin:$PATH"
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin list
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin claim <任务ID>
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin show <任务ID>
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin done <任务ID> --summary "一句话结论" [--value "$(cat 结果文件)"]
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin apply <任务ID> --json 结果.json
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin fail <任务ID> --summary "失败原因"
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin sources <内容ID> --json 来源.json [--dry]
```

- 单字段动作（`judge` / `research` / `factcheck` …）→ `done --value`，落到「落点表.落点字段」。
- `pipeline` → `apply --json`，一次写回 **研究摘要 / 内容大纲 / 正文 / 制作方案 + 状态=待发布**，
  只写这 5 个字段，不要顺手改标题。
- JSON 键名必须与目标表字段名完全一致；出现「跳过未知字段」说明键名写错。
- 队列表 **13 个字段全是 text**，写队列一律 `{"text": "…"}`。

字段与表 ID 对照、payload 格式见 `references/workbench-facts.md`。

## 三、来源回流（本机参数）

工具已实现的能力不要自己重写：**按「内容ID + 链接」去重 → 跳过缺名称的 → 按原顺序截取前 8 条**，
第 9 条起不写并提示「超过 8 条上限，其余未写」。**能写几条 = 跳过之后还剩几条**，
所以 10 条里若有 2 条被跳过，仍会写满 8 条。

```bash
# 来源文件：sources-<内容ID>.json
# [{"名称":"来源标题","类型":"官网","链接":"https://…","备注":"支撑了哪条结论"}, …]
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin sources <内容ID> --json sources-<内容ID>.json --dry
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin sources <内容ID> --json sources-<内容ID>.json
```

- **表 ID**：`<研究资料表ID>`（字段：内容ID / 资料名称 / 资料类型 / 链接 / 备注 / 创建时间）
- 资料类型只能取：新闻链接 / 官网 / GitHub / 公众号文章 / 产品资料 / PDF / 图片 / 个人笔记 / 其他
- `--dry` 输出形如 `研究资料表：<内容ID> 现有来源 0 条，本次待写 8 条`，下面逐条列出将写入的记录；
  看到「跳过：…」就是被过滤的条目。
- 需要**批量补写历史来源**时才用底层 `batch_add_database_records.py`
  （payload 与踩坑见 `references/workbench-facts.md`）。

## 四、本机踩过的坑

- 上一轮的临时产物文件名（如 `tmp_pipeline_build.py`）不要复用——Write 前要求先 Read，
  用带日期后缀的新名字。
- 长文本用 `--value "$(cat 文件)"` 传，避免命令行转义；`--records` 传大 JSON 在 Git Bash 下会静默失败。
- 队列 `list` 的「共 N 条待处理」含 待执行 / 执行中 / 失败，**N > 0 不等于有活干**，必须逐条看状态。
- 复核用 `tools/scan.py --token-stdin --out .scan/xxx.json` 全表 dump；`--out` **必须带目录**。
- `queue.py` **没有 query 子命令**；字段是否存在用 `get_database_schema` 核实后再决定是否补 `T_FIELD`。

## 五、本机记录（实证）

- 正文超限返工是高频问题：曾首稿 3414 字（超 2500）被压到 2487 才写回——按 ≤2400 字起稿可省一轮。

## 六、相关规范（同一套内容工厂，按阶段分工）

| skill | 管什么 | 通用规范（真源，都在套件里） |
|---|---|---|
| `content-research-spec` | **本 skill**：研究阶段 | `kit/references/research.md` |
| `content-writing-spec` | 写作与改稿：声道、骨架六拍、标题、去 AI 味 | `kit/references/writing.md` + `kit/references/deai.md` |
| `content-platform-adapt` | 多平台改写 | `kit/references/platforms.md` |
| `content-visual-spec` | 封面与配图、截图脱敏 | `kit/references/visual.md` |
| `content-asset-loop` | 沉淀回流、素材库写回 | `kit/references/assets.md` |

研究做完 → 写作改稿 → 多平台改写 → 封面配图 → 沉淀资产，各由对应规范接管；
本 skill 只管**研究阶段的本机落地**。
