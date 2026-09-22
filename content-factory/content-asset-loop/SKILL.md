---
name: content-asset-loop
description: 创作小屋内容工厂的资产循环绑定层。规定沉淀类动作（sed-*：提炼方法/选题方法/文章结构/Prompt/Skill 思路/金句/案例）该怎么落地：先读套件里的通用沉淀规范（5 条硬门槛、七类合格线、命名去重、写回契约），再按本层写回：页面入口、queue.py asset 命令、注入与排序的本机事实、真实好例。当需要执行队列里的沉淀类任务、给素材库补资产、判断一份「提炼产出」该不该入库、或调整「每次生成自动带上的历史资产」时使用。
agent_created: true
---

# 资产循环 · 本机绑定层

沉淀不是给这篇文章写结语，是给**下一篇**备料。

> ## 通用规范在哪（先读它，再读本文）
>
> 沉淀的通用规则——为什么要这个闭环、**合格资产 5 条硬门槛**、**七类资产各自的合格线**、
> 命名规范、去重与淘汰、写回契约、写回前验收清单、常见坑、以及
> **每类资产的「合格 / 不合格」完整对照分析**——**唯一真源是**：
>
> - **`~/.workbuddy/skills/content-factory-kit/references/assets.md`**
> - **`~/.workbuddy/skills/content-factory-kit/references/asset-examples.md`**
>   （本技能原来的 `references/asset-examples.md` 是它的**未脱敏版**，已删除并入这里）
>
> 本文只写**本机落地**：怎么触发、`queue.py asset` 命令、注入与排序的本机事实、真实好例。

## 何时使用

- 沉淀类动作：`sed-method` / `sed-topic` / `sed-struct` / `sed-prompt` / `sed-skill` / `sed-quote` / `sed-case`
- 判断一份提炼产出该不该写进素材库表
- 批量补历史资产、清理低质资产、调整注入规则

不适用：研究类（走 `content-research-spec`）；正文写作与改稿（走 `content-writing-spec`）；
多平台改写（走 `content-platform-adapt`）。

## 一、怎么触发（本机入口）

页面上：内容详情 → 「AI 执行详情 · 高级信息」折叠区 → 「沉淀为素材（N 条）」块里的 7 个按钮
（提炼写作方法 / 提炼选题方法 / 提炼文章结构 / 保存 Prompt / 生成 Skill 思路 / 提炼金句 / 加入案例库）。

**没有正文的内容不出按钮**——没东西可提炼时不要硬跑，产出的会是空资产。

点一下即派发：页面把任务卡写进队列，每小时自动化领取执行，执行端按本规范提炼并用
`queue.py asset` 写回。

## 二、本机写回契约（`sed-*` 不能走 `done --value`）

沉淀类动作的 `save` 只有 `{store:'asset', kind:'xx'}`，**没有 `field` / `label`**，
所以队列表的「落点字段」是空的——`done --value` 那套单字段回写**对 `sed-*` 完全不生效**；
而素材库又是「新增记录」而非「更新已有记录」。为此 `tools/queue.py` 提供了专门的 `asset` 子命令：

```bash
export PATH="/usr/bin:/bin:/mingw64/bin:$PATH"
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin show  <任务ID>
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin claim <任务ID>
# 资产文件：assets-<内容ID>.json
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin asset <任务ID> --json assets-<内容ID>.json --dry
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin asset <任务ID> --json assets-<内容ID>.json
```

工具已实现的能力不要自己重写：按「同内容ID + 素材名称」去重、非法分类退回该动作默认分类、
缺名称 / 缺内容跳过、**单次最多 5 条**、写完自动把任务标记「已完成」并写结果摘要。

- `--dry` 输出形如 `素材库表：CT-2026-0015 已有资产 0 条，本次待写 5 条（动作 sed-method，默认分类 方法论）`，
  下面逐条列 `名称 | 分类 | N★ | N 字`；出现「跳过：…」就是被过滤的条目。
  「已有资产」只统计**同内容ID**的已沉淀条数——历史批量导入的 33 条资产内容ID 为空，所以不会计入。
- `资产分类` 只能取：方法论 / 文章结构 / Prompts / 选题方法 / 金句 / Skills / 案例库 / 素材库。
- 动作卡要求 5–8 条时（`sed-quote`），**只取自己判断最值得复用的 5 条**，其余在结果摘要里列名称。
- 写库失败不影响任务结论：在结果摘要注明「资产未沉淀」+ 原因。

## 三、本机口径与现状

**单条上限口径 ≤300 字**（套件里写成「不超长」，具体数字在本层）：注入只取前 200 字，
**结论必须在前 60 字内自成一句**。库里有条 423 字（Prompts）被截断后只剩开头——不要模仿。
**星级缺省 4**，最该被复用的给 5。

**注入端事实（2026-09-18 核对）**：注入函数是 `build/p29_aiexec.js` 的 `assetsMethodText()`——
过滤 `ASSET_METHOD_KINDS` 后 `slice(0, 10)`，每条 `clip(内容, 200)`。
**素材库 33 条（方法论 7 / 金句 8 / 文章结构 6 / 选题方法 6 / 案例库 4 / Prompts 2）的 `内容ID` 全部为空**
——它们是批量导入的历史资产，不走 `sed-*` 写回。注入只按「资产分类」过滤，所以这 33 条都参与注入，
只是被截到前 10 条。

**所以排序就是生死线**：前 60 字必须是能独立成立的方法句。
**页面侧待办**：`assetsMethodText()` 目前按表返回顺序取前 10，**未按星级排序**——
在补齐之前星级只是给人看的标记；要真正生效需改 `p29_aiexec.js` + 重发版本
（走 skill `library-live-page-update`）。

> **核对存量资产时按「关联内容标题」筛，不要按内容ID**——历史资产的内容ID 是空的，
> 按内容ID筛会得出「一条都没有」的错误结论。

## 四、本账号真实好例（命名规范的可信样本）

套件里的好例是脱敏版（「某监控面板 + 消息调度」这种）。本账号的真实样本：

| 分类 | 真实好例 |
|---|---|
| 案例库 | `WeSight + 微信调度，5 个 Agent 把活干完`；`公众号爆款文章研究台（Qwen3.8-Max + FastAPI + React 全栈 Demo）` |
| 选题方法 | `「X 全记录」系列化选题法（一个平台缺口 = 一个系列）`——已跑通：Git Cola / Geany / Firebird / ESP-IDF / Eclipse Theia 五连发 |
| 方法论 | `结构化输出不能只靠 Prompt（四层兜底）` |
| 文章结构 | `全记录式｜为什么做 → 技术路线 → 分步实现 → 踩坑 → 能力边界` |
| Prompts | `主开发 Agent 五角色提示词（可直接复用）` |
| 金句 | `「语法兼容不等于性能一致。」`（观点）、`「真正拉开差距的是『开满之后稳不稳』。」`（结论，可做封面文案）、`「焦虑没让我干得更好。」`（自曝，只用于 B 声道） |

判断标准始终是同一条：**换个选题还能不能直接用。**

## 五、相关规范（同一套内容工厂，按阶段分工）

| skill | 管什么 | 通用规范（真源，都在套件里） |
|---|---|---|
| `content-research-spec` | 研究阶段 | `kit/references/research.md` |
| `content-writing-spec` | 写作与改稿 | `kit/references/writing.md` + `kit/references/deai.md` |
| `content-platform-adapt` | 多平台改写 | `kit/references/platforms.md` |
| `content-visual-spec` | 封面与配图 | `kit/references/visual.md` |
| `content-asset-loop` | **本 skill**：沉淀回流 | `kit/references/assets.md` + `kit/references/asset-examples.md` |
