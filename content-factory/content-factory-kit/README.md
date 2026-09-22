# content-factory-kit

「创作小屋」内容运营工作台套件 —— 怎么干活（支路 A）、怎么给别人（支路 B）、怎么装进来（支路 C）。

## 功能

一个 Skill 覆盖三件事：

1. **执行规范（支路 A）**：研究 / 写作改稿 / 多平台改写 / 封面配图 / 资产沉淀五个阶段的**可判定合格线**。
   含双声道模型、骨架六拍、去 AI 味黑名单、7 张平台卡片、封面尺寸与脱敏、合格资产 5 关，
   加全局铁律 6 条、阶段篇幅表、写回契约、交付前自查 7 项。
2. **模板源生产（支路 B）**：把连着自己云端数据表的单文件 HTML 应用，
   做成别人一句话能复刻的模板源（复刻清单内嵌、演示块标记化、双产物构建、免鉴权机读直链）。
3. **模板复刻（支路 C）**：把「创作小屋 · 灵感营地」工作台装进自己的资料库，一条命令跑完 ——
   11 张云表 / 149 字段 / 82 条示例数据 / 1 个能立刻打开的页面。

## 一条最重要的分界线

套件给的是**方法**，不是**结论**：

| | 内容 | 能不能直接拿走用 |
|---|---|---|
| **格式约定** | 研究摘要几段、正文多长、封面多少字、标签几个、「注意：」标在哪 | 可以直接用（平台与行业的客观约束） |
| **判断标准** | 什么话像 AI 写的、哪种标题配哪个平台、什么时候该缩小结论 | 只能改造成你自己的 |

判断标准是从**某个人的具体作品**里长出来的。别人量出来的「两段式标题占 68%」对你没有意义 ——
你得量你自己的那批。所以配了一个能真跑的量化脚本：

```bash
python3 scripts/measure_titles.py <你的标题语料>   # csv / json / txt 都行
```

出长度中位、两段式冒号率、问句率，并按年份分期看拐点。

## 与配套的 5 份绑定层的关系

本套件是**真源**，另外 5 个 Skill（`content-research-spec` / `content-writing-spec` /
`content-platform-adapt` / `content-visual-spec` / `content-asset-loop`）是**绑定层**：

- 真源装**通用格式约定**（谁都能用）；
- 绑定层装**本机命令 + 表 ID + 个人判断标准**（只能自己长）。

工作台里执行任务时按动作 ID 加载绑定层，读完再顺着它顶部的指引读回本套件的真源 ——
**两份合起来才是完整规范**。详见 `SKILL.md`。

## 安装

```bash
mkdir -p ~/.workbuddy/skills/content-factory-kit
cp -r SKILL.md references scripts tests assets ~/.workbuddy/skills/content-factory-kit/
```

Claude Code 用户同理，放 `~/.claude/skills/content-factory-kit/`。重启会话后生效。

## 复刻工作台

```bash
export PATH="/usr/bin:/bin:/mingw64/bin:$PATH"
SKILL="$HOME/.workbuddy/skills/content-factory-kit"

# 先干跑一遍（只做本地检查，不发任何写请求）
printf '%s' "$TOKEN" | python3 "$SKILL/scripts/clone_workbench.py" --token-stdin --dry-run

# 确认没问题再真跑
printf '%s' "$TOKEN" | python3 "$SKILL/scripts/clone_workbench.py" --token-stdin
```

跑完回执里那个 `/space/d/<nodeId>` 链接就是新的工作台。

> **动手前必须知道**：复刻会**新建 11 张表**，而资料库**没有删除表的接口** ——
> 建了只能在界面上手动删。所以一定先 `--dry-run`。

**别用资料库自带的 clone-flow 复刻本工作台**：产物里 `databaseId:` 字面量数量是 0
（表 id 写成 `var DB = { content : '…' }`），会被误判成「纯 HTML 页」跳过建表，
最后给出一个指向原作者表的空页面，而且全程不报错。本套件走的是「按内嵌清单建表」第三条路，
不读原作者任何一张表，所以不需要跨账号权限。

## 自检

```bash
python3 tests/check_kit_integrity.py     # 22 项：frontmatter / references 完整性 / 孤儿文件 / 旧名残留
python3 tests/check_measure_titles.py    # 30 项：标题量化脚本（含负对照）
python3 tests/check_clone_workbench.py   # 39 项：复刻全链路（用桩脚本替换资料库技能，不碰真账号）
```

三段验收里的第三段是**反向对照**（清单选项被删 / 标记缺失 / DB 绑定被篡改 / 非模板产物，
四种都必须被正确拒绝）—— 没有这一段，上面所有 ok 都可能是假绿。

## 关于示例

`references/` 里的示例（尤其 `deai.md`、`assets.md`、`asset-examples.md`）是**虚构的示范**，
只用来演示**结构**。不要把它们当素材直接引用，也不要把示例里的数字当事实。

唯一的例外：`references/style-guide.md` 里那张分期表，是一批真实公开语料的聚合统计（248 篇，2022–2026）。
它出现在那里只为演示**怎么读数据**（全期平均会掩盖拐点），不是给你对标的结论 ——
**你的数字必须自己跑 `scripts/measure_titles.py` 量出来**。

## 维护说明

- 内置模板产物 `assets/ai-content-workspace-template.html`（2.7MB，含复刻清单）是快照，可能落后。
  要拿最新版就从发布态静态地址复刻：`--source <发布态 index.html 的 URL>`。
- 产物里的 11 个旧表 id 在公开分发前已替换为**等长合成 id**（`DEMOOldTable*`）。
  它们只是重映射时用于搜索的锚点，与原作者的账号无关，也不影响复刻。
- 改过 `scripts/` 或产物，三个自检都要重跑。
