# yanyanskill

颜颜yan 的 Claude Code Skill 合集。每个 Skill 是一个带 `SKILL.md` 的目录，复制到 `~/.claude/skills/` 即可使用。

## Skill 索引

| Skill | 说明 | 位置 |
|-------|------|------|
| wesight-im-pipeline | WeSight IM 桥（微信/飞书 ↔ agent）全链路排障手册 + IM 会话行为规范 | [wesight/wesight-im-pipeline](wesight/wesight-im-pipeline) |
| **content-factory-kit** | 「创作小屋」内容运营工作台套件：执行规范（研究/写作/多平台/配图/资产）+ 模板源生产 + 一条命令复刻工作台（11 张云表 / 149 字段 / 82 条示例） | [content-factory/content-factory-kit](content-factory/content-factory-kit) |
| content-research-spec | 研究**绑定层**：队列里研究/核查/竞品任务的执行与写回（本机命令 + 表 ID + 本机坑） | [content-factory/content-research-spec](content-factory/content-research-spec) |
| content-writing-spec | 写作**绑定层**：大纲/初稿/扩写/去 AI 味/起标题（个人词库 + 标题实测区间 + 改稿禁区） | [content-factory/content-writing-spec](content-factory/content-writing-spec) |
| content-platform-adapt | 多平台改写**绑定层**：公众号/掘金/CSDN/小红书/视频号/B站/抖音的字数口径与铁律 | [content-factory/content-platform-adapt](content-factory/content-platform-adapt) |
| content-visual-spec | 封面配图**绑定层**：封面/插图/信息图的尺寸安全区、截图脱敏、出图分工 | [content-factory/content-visual-spec](content-factory/content-visual-spec) |
| content-asset-loop | 资产沉淀**绑定层**：7 个 `sed-*` 动作的落地方式、合格资产 5 关、命名与注入排序 | [content-factory/content-asset-loop](content-factory/content-asset-loop) |

> `content-factory/` 下的 6 个 Skill 是一套：`content-factory-kit` 是**通用规范真源**，
> 另外 5 个是**绑定层**（装本机命令与个人判断标准）。工作台里执行任务时按动作 ID 加载绑定层，
> 再顺着它顶部的指引读回真源 —— **两份合起来才是完整规范**。
> 只用 `content-factory-kit` 也能跑通支路 B（做模板源）和支路 C（复刻工作台）。

## 目录约定

按所属项目/域分一级文件夹，每个 Skill 一个二级目录，内含 `SKILL.md`（必需）与 `README.md`（说明）。

```
yanyanskill/
├── wesight/                    # WeSight 项目相关
│   └── wesight-im-pipeline/    # IM 桥全链路手册 + 行为规范
│       ├── SKILL.md
│       └── README.md
└── content-factory/            # 内容工厂（创作小屋工作台）
    ├── content-factory-kit/    # 通用规范真源 + 模板源生产 + 复刻脚本
    │   ├── SKILL.md
    │   ├── README.md
    │   ├── references/         # 8 份执行规范 + 3 份模板/复刻文档
    │   ├── scripts/            # clone_workbench.py / measure_titles.py
    │   ├── tests/              # 22 + 30 + 39 项自检
    │   └── assets/             # 内置模板产物（2.7MB，含复刻清单）
    ├── content-research-spec/  # 研究绑定层
    ├── content-writing-spec/   # 写作绑定层
    ├── content-platform-adapt/ # 多平台改写绑定层
    ├── content-visual-spec/    # 封面配图绑定层
    └── content-asset-loop/     # 资产沉淀绑定层
```

## 使用方法

```bash
# 单文件 Skill（以 wesight-im-pipeline 为例）
mkdir -p ~/.claude/skills/wesight-im-pipeline
cp wesight/wesight-im-pipeline/SKILL.md ~/.claude/skills/wesight-im-pipeline/
```

```bash
# 多目录 Skill（以 content-factory-kit 为例，它有 references/scripts/tests/assets）
mkdir -p ~/.claude/skills/content-factory-kit
cp -r content-factory/content-factory-kit/{SKILL.md,references,scripts,tests,assets} \
      ~/.claude/skills/content-factory-kit/
```

WorkBuddy 用户把上文的 `~/.claude/skills/` 换成 `~/.workbuddy/skills/` 即可。
重启会话后生效。

## 作者

颜颜yan —— 内容创作者 & 独立开发者，公众号「颜颜yan的编程日记」。
