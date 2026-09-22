# yanyanskill

颜颜yan 的 Claude Code Skill 合集。每个 Skill 是一个带 `SKILL.md` 的目录，复制到 `~/.claude/skills/` 即可使用。

## Skill 索引

| Skill | 说明 | 位置 |
|-------|------|------|
| wesight-im-pipeline | WeSight IM 桥（微信/飞书 ↔ agent）全链路排障手册 + IM 会话行为规范 | [wesight/wesight-im-pipeline](wesight/wesight-im-pipeline) |
| **content-factory-kit** | 「创作小屋」内容运营工作台套件：① 执行规范（研究 / 写作改稿 / 多平台改写 / 封面配图 / 资产沉淀，每阶段**通用规范 + 本机口径**两份文档）② 模板源生产 ③ 一条命令复刻工作台（11 张云表 / 149 字段 / 82 条示例） | [content-factory/content-factory-kit](content-factory/content-factory-kit) |

> `content-factory-kit` 一个技能装齐三件事。原来分出去的研究 / 写作 / 多平台 / 配图 / 资产五份
> **绑定层**技能已在 2026-09-22 全部下沉，收成技能里的 `references/local/` 目录 ——
> 通用规范在 `references/`，本机口径（命令 / 表 ID / 个人判断标准）在 `references/local/`，
> **两份合起来才是完整规范**。对外只需要装这一个技能。

## 目录约定

按所属项目/域分一级文件夹，每个 Skill 一个二级目录，内含 `SKILL.md`（必需）与 `README.md`（说明）。

```
yanyanskill/
├── wesight/                    # WeSight 项目相关
│   └── wesight-im-pipeline/    # IM 桥全链路手册 + 行为规范
│       ├── SKILL.md
│       └── README.md
└── content-factory/            # 内容工厂（创作小屋工作台）
    └── content-factory-kit/    # 执行规范 + 模板源生产 + 复刻脚本
        ├── SKILL.md
        ├── README.md
        ├── references/         # 通用规范：五阶段 8 份 + 模板/复刻 3 份
        │   └── local/          # 本机口径：五阶段各 1 份 + 表/命令速查
        ├── scripts/            # clone_workbench.py / measure_titles.py
        ├── tests/              # 25 + 9 + 30 + 39 项自检
        └── assets/             # 内置模板产物（2.7MB，含复刻清单）
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
