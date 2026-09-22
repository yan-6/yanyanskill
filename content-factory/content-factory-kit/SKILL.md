---
name: content-factory-kit
description: >-
  内容工厂套件——「创作小屋」内容运营工作台的三件事一次装齐：
  （A）执行规范：研究 / 写作改稿 / 多平台改写 / 封面配图 / 资产沉淀五个阶段的可判定合格线。
  每个阶段是**通用规范 + 本机口径**两份文档：通用在 `references/`（研究 8 段结构、双声道模型、
  骨架六拍、去 AI 味黑名单、7 张平台卡片、封面尺寸与脱敏、合格资产 5 关），
  本机在 `references/local/`（queue.py 命令、表 ID 与落点字段、动作 ID 映射、个人判断标准与本机踩过的坑）；
  （B）模板源生产：把连着自己云端数据表的单文件 HTML 应用做成别人一句话可复刻的模板源
  （复刻清单内嵌、演示块标记化、双产物构建、免鉴权机读直链、复刻协议文本）；
  （C）模板复刻：把「创作小屋 · 灵感营地」工作台（11 张云表 / 149 字段 / 82 条示例）
  装进自己的资料库，一条命令跑完。
  当需要写稿改稿、执行 AI 任务队列、判断产出能不能写回、按自己的作品长出风格指南、
  把工作台分享给别人、或复刻这个工作台时使用。
  关键词：内容工厂、创作小屋、执行规范、研究规范、写作规范、双声道、骨架六拍、去 AI 味、
  多平台改写、平台卡片、封面配图、脱敏、资产沉淀、风格指南、模板源、复刻、clone、
  一键复刻、示例数据、嵌入式复刻清单、databaseId 重映射、资料库 page + database、
  本机口径、写回契约、queue.py、动作 ID、AI 任务队列、任务卡、落点字段。
agent_created: true
---

# 内容工厂套件

一句话：**「创作小屋」这套内容工厂——怎么干活（A）、怎么给别人（B）、怎么装进来（C）**。
三件事在同一个技能里，各有正文，**先认路，不要混读**。

## 三条支路（先认路，只读一条）

| 支路 | 你要干的事 | 读哪一份 | 触发标志 |
|---|---|---|---|
| **A 执行规范** | 写稿 / 改稿 / 研究 / 多平台改写 / 配图 / 沉淀资产，执行任务队列里的活 | `references/<阶段>.md` + `references/local/<阶段>.md`，见下面的动作表 | 「帮我写」「改一下」「研究一下」+ 动作 ID |
| **B 模板源生产** | 把自己的单文件应用 / 工作台分享出去，让别人也能复刻 | `references/template-authoring.md` | 「分享给别人」「做成模板」「让人也能用」 |
| **C 模板复刻** | 把「创作小屋」工作台装进**自己**的资料库 | `references/workbench-clone.md` + `scripts/clone_workbench.py` | 「复刻给我」「clone 这个工作台」 |

## 支路 A：按动作 ID 取规范（**通用 + 本机，两份一起读**）

队列里不同动作走不同规范。**先看清任务卡里的「动作ID」，再按下面这张表读那两份文档**——
只读命中的，不要一次全读。

| 页面阶段 | 动作 ID | 通用规范（`references/`） | 本机口径（`references/local/`） |
|---|---|---|---|
| **research** 研究 | `pipeline` `research` `searchres` `orgsources` `compete` `factcheck` `callresearch` `researchteam` | `research.md` | `research.md` |
| **topic** 选题 | `judge` `deepdig` `angles` `hitparse` `calltopic` `startresearch` | `research.md` | `research.md` |
| **write** 写作改稿 | `outline` `gzhstruct` `draft` `cont` `expand` `shorten` `stronger` `deai` `spoken` `openhead` `openend` `callwrite` `titles10` `titlegzh` `titleviral` `titleknow` `titleab` | `writing.md`（`deai` 另加 `deai.md`） | `writing.md` |
| **produce** 配图 | `cover` `illus` `infograph` | `visual.md` | `visual.md` |
| **produce** 多平台 | `juejin` `xhs` `sumsocial` `adapt` | `platforms.md` | `platforms.md` |
| **sediment** 沉淀资产 | `sed-method` `sed-topic` `sed-struct` `sed-prompt` `sed-skill` `sed-quote` `sed-case` | `assets.md`（另加 `asset-examples.md`） | `assets.md` |
| 其余 | `ppt` `vid60` `shortvideo` `pubsum` `tags` `typos` `linkcheck` `precheck` `review` `rvtitle` `rvtopic` `rvstruct` `rvdata` `rvbest` `rvworst` `rvnext` `nexttopics` | 无专门规范，按任务卡执行 | 无 |

三点补充：

- **`pipeline` 是全链路任务**（研究 + 写作 + 制作方案一次做完）：研究那几段按 `research.md`，
  写正文那一段同时遵守 `writing.md` 的改稿铁律。
- **任何阶段都要动表时**，先把 `references/local/workbench-facts.md` 打开——
  表 ID、字段名、`queue.py` 全部命令、payload 格式、包装类型陷阱都在那一份里。
- **想按自己的作品定风格** → `references/style-guide.md`（支路 A 的配套方法论，配可跑的量化脚本）。

支路 B / C 的三个文件：`references/template-authoring.md`（生产侧方法论）、
`references/workbench-clone.md`（复刻执行说明）、
`references/workbench-schema.md`（11 张表 / 149 字段 / old id 完整清单）。

## 技能内的「通用 / 本机」两层（支路 A，先读这一段）

这个技能里每一个阶段都是**两份文档**，不要只读一份就动手：

| | 在哪 | 装什么 | 换个账号还能不能用 |
|---|---|---|---|
| **通用规范** | `references/<阶段>.md` | 结构、篇幅区间、平台卡片、AI 味清单、合格线、验收清单 | ✅ 谁都能用，是行业与平台层面的客观约束 |
| **本机口径** | `references/local/<阶段>.md` | `queue.py` 命令、表 ID 与落点字段、动作 ID 映射、个人词库与签名、标题实测区间、真实好例、本机踩过的坑 | ❌ 只对**这个**工作台账号生效 |

- **口径只有一份**：改阶段结构 / 篇幅 / 写回契约 → 改 `references/` 的通用那份；
  改本机命令 / 表 ID / 个人风格 → 只碰 `references/local/` 的那份。
- **别把通用正文抄进本机文档**——自检会以 35% 相似度上限拦下"又抄回来"的重复正文。
- 本机文档顶部都有一段「通用规范在哪」的指针块，**读完本机那份要顺着指针回去读通用那份**。

### 通用里的「方法」与本机的「结论」

| | 内容 | 能不能直接拿走用 |
|---|---|---|
| **格式约定** | 研究摘要几段、正文多长、封面多少字、标签几个、各平台各写什么、「注意：」标在哪 | ✅ **可以直接用** |
| **判断标准** | 什么话像 AI 写的、哪种标题配哪个平台、什么时候该缩小结论、哪句话不写 | ⚠️ **只能改造成你自己的** |

判断标准为什么不给：它是从**某个人的具体作品**里长出来的。别人量出来的「两段式标题占 68%」
对你没有意义——你得量你自己的那批。所以这里给的是**方法**，不是**结论**。

> 想知道怎么把自己的判断标准长出来 → 看 `references/style-guide.md`。
> 那一份是配套动作，不看完不完整的。它配了一个能真跑的量化脚本：
> `python3 scripts/measure_titles.py <你的标题语料>`（csv/json/txt 都行，
> 出长度中位、两段式冒号率、问句率、并按年份分期看拐点）。

## 全局铁律（三条支路都适用，越界即返工）

1. **改稿只动表达，不动事实。** 数字、时间、版本号、金额、链接、「（来源：xxx）」标注、
   「【待核实：xxx】」标记、证据（表格 / 代码 / 命令 / 截图占位）——一个字都不能改。
2. **「待核实」标记不许顺手删。** 它看着像瑕疵，实际是必要的诚实标记。
   缩写删到论证链断了就是删过头。
3. **只讲优点不讲代价 = 不合格。** 专业稿必须有「当前能力边界」；
   个人稿必须有情绪或自嘲。两边都没有的就是产品说明书。
4. **平台口味只能改「怎么说」，不能改「是什么」。**
   结论可以**缩小范围**（「我自己用下来是这样」），不能**放大程度**（「效果爆炸」）。
5. **查不到就不编。** 数字查不到写【待核实】，不要用形容词（「很快」「显著提升」）糊过去。
6. **不许虚构来源、引文、人物发言。** 链接必须真打开过。

## 五个阶段的产出篇幅（支路 A）

| 阶段 | 产出 | 篇幅 |
|---|---|---|
| 研究 | 研究摘要 | 800–1500 字，结构齐全优先，不灌水 |
| 研究 | 内容大纲 | 2500–3500 字为上限 |
| 写作 | 正文 | **起稿按 ≤2400 字**，交付区间 1500–2500 字 |
| 写作 | 备选标题 | 一次给足数量，每个标注适合哪类读者 / 哪个平台 |
| 多平台 | 各平台版本 | 见 `references/platforms.md` 的平台卡片 |
| 配图 | 配图方案 | 不限，但每张图要说明用途与平台尺寸 |
| 沉淀 | 单条资产 | ≤300 字，结论必须在前 60 字内自成一句 |

> 正文按 2400 字起稿是省返工的做法：超限被打回重压是高频问题，宁可起稿就压住。

## 写回契约（支路 A）

工作台的页面**不联网、不调模型**。它只做一件事：把任务卡写进云端队列。
真正干活的是领取任务的 agent（也就是你）。所以「执行规范」必须存在于**领取端**，也就是这里。

工作台页眉生成的任务卡里通常带：动作 ID、目标键、任务标题、落点表、落点字段、任务卡正文。
**任务卡与本规范冲突时以任务卡为准**，但要在结果摘要里注明你偏离了哪一条、为什么。

写回**一律走 `tools/queue.py`**（命令与 payload 格式见 `references/local/workbench-facts.md`），
**不要绕过它直连底层接口**——包装类型写错（比如该写 `{text: "…"}` 却写了裸字符串）
后端会**静默丢值**，你不会收到报错。写回前先只读试跑一遍（`--dry`）确认计划，再正式写。

| 动作类型 | 落点 | 注意 |
|---|---|---|
| 研究类单字段 | 内容主表的一个字段 | 用 `done --value` 单字段写回，然后**再做来源回流**（`sources`） |
| `pipeline`（一键成篇） | 一次写 4 个字段 + 状态 | 用 `apply`，只写**研究摘要 / 内容大纲 / 正文 / 制作方案 + 状态**，不要顺手改标题 |
| 多平台改写类 | **共享的「制作方案」字段** | 写回前先读现有内容，**追加**而不是覆盖，否则会把封面方案顶掉 |
| 沉淀类 `sed-*` | 素材库**新增记录** | 落点字段为空，`done --value` 对它无效，**只能**用 `asset` 子命令 |

> 支路 B / C 不涉及内容写回，走它们各自的脚本；复刻相关写回契约见
> `references/workbench-clone.md`，模板源清单契约见 `references/workbench-schema.md`。

## 交付前总自查

- [ ] **支路选对了吗？**（A 还要确认动作 ID 与阶段对得上）**通用 + 本机两份都读了吗？**
- [ ] 数字 / 来源 / 「待核实」/ 证据，一个都没被改掉？
- [ ] 形容词后面跟了量级（「几秒拿到结果」而不是「很快」）？
- [ ] 专业稿写了能力边界？个人稿有情绪锚点？两边都没串味？
- [ ] 篇幅落在区间内？（正文用字符数数一遍，别凭感觉估）
- [ ] 结论方向和原稿一致？有没有被平台口味放大？
- [ ] 落点字段在目标表里**真的存在**吗？（不存在就别硬写，记进结果摘要）
- [ ] 结果摘要写清了「做了什么 / 落到哪个字段 / 哪些没做成及原因」？

## 技能目录地图

```
content-factory-kit/
  SKILL.md                                    本文（入口 + 三条支路 + 动作表 + 全局铁律 + 写回契约）
  references/                                 ── 通用规范（谁都能用）
    research.md  writing.md  deai.md           支路 A · 五阶段通用规范
    platforms.md visual.md   assets.md
    asset-examples.md style-guide.md
    template-authoring.md                      支路 B · 怎么做可分发的模板源
    workbench-clone.md                         支路 C · 怎么复刻这个工作台
    workbench-schema.md                        支路 C · 清单结构 / 11 张表 / 149 字段
    local/                                     ── 本机口径（只对这套工作台生效）
      research.md writing.md platforms.md     对应通用那五份，各一份
      visual.md   assets.md
      workbench-facts.md                      表 ID / 字段 / queue.py 命令速查（任何阶段都要）
  scripts/
    measure_titles.py        标题量化（支路 A · 风格指南配套，纯 stdlib）
    clone_workbench.py       七步复刻脚本（支路 C 唯一入口）
  tests/
    check_kit_integrity.py   24 项 · 结构：frontmatter / 路径引用 / 孤儿文件 / 旧名残留
    check_spec_bindings.py    9 项 · 通用/本机两层接线（含 --selftest 负对照）
    retired-skills.txt       退役技能名清单（上面两个自检共用，避免名单漂移）
    check_measure_titles.py  30 项 · 标题量化脚本
    check_clone_workbench.py 39 项 · 复刻全链路（桩脚本替换资料库技能，不碰真账号）
    fixtures/                语料样例（txt / csv / json）
  assets/
    ai-content-workspace-template.html   内置模板产物 2.7MB（含复刻清单，离线可用）
```

## 验证（改过任何脚本或文档都要跑）

```bash
python3 tests/check_kit_integrity.py      # 结构 · 24 项：frontmatter / 路径引用 / 孤儿文件 / 旧名残留
python3 tests/check_measure_titles.py     # 支路 A · 30 项
python3 tests/check_clone_workbench.py    # 支路 C · 39 项，用桩替换资料库技能，不会真建表
python3 tests/check_spec_bindings.py      # 通用/本机两层 · 9 项
```

**改过 `references/`（通用或本机）后，`check_spec_bindings.py` 必跑**：它查「本机文档完整性 /
指针可达 / 通用真源无孤儿 / 通用与本机没有互相抄 / 旧技能名已不存在」。
它带负对照，一次跑完：

```bash
python3 tests/check_spec_bindings.py --selftest   # 另注入 4 类破坏（指针断裂 / 出现孤儿真源 /
                                                  # 本机文档抄回通用正文 / 残留旧技能名），
                                                  # 每类都必须让自检报错，否则说明自检本身失效了
```

## 分享给别人 / 能力边界

- 想把这个工作台给别人用：**别只丢本目录**。两条路——① 给「演示版」公开链接（只看不改）；
  ② 给「模板源」+ 一句话复刻（真拥有，会在对方账号里新建 11 张表）。做法见
  `references/template-authoring.md`。
- **执行层拷不走**：页面里的 AI 按钮点了不会自己跑，它们只往云端队列写任务卡；
  真正干活的是对方本机的 WorkBuddy + 本技能支路 A 的那些执行规范 + 各自的定时任务。
  **所以把本技能一并给对方装，对方才算真的能用起来。**
  注意 `references/local/` 那几份是**本机口径**（含表 ID、个人判断标准），换账号要重写。
- 复刻是**新建** 11 张表，资料库**没有删表接口**，建了只能在界面上手动删
  → 先 `--dry-run` 看一遍再决定跑不跑。

## 关于示例

本技能里的示例（尤其 `references/deai.md`、`references/assets.md`
与 `references/asset-examples.md`）**是虚构的示范**，
只用来演示**结构**。不要把它们当素材直接引用，也不要把示例里的数字当事实。

唯一的例外：`references/style-guide.md` 里那张分期表，是**一批真实公开语料的聚合统计**
（248 篇，2022–2026）。它出现在那里只为演示**怎么读数据**（全期平均会掩盖拐点），
不是给你对标的结论——**你的数字必须自己跑 `scripts/measure_titles.py` 量出来**。
