# yanyanskill

颜颜yan 的 Claude Code Skill 合集。每个 Skill 是一个带 `SKILL.md` 的目录，复制到 `~/.claude/skills/` 即可使用。

## Skill 索引

| Skill | 说明 | 位置 |
|-------|------|------|
| wesight-im-pipeline | WeSight IM 桥（微信/飞书 ↔ agent）全链路排障手册 + IM 会话行为规范 | [wesight/wesight-im-pipeline](wesight/wesight-im-pipeline) |

## 目录约定

按所属项目/域分一级文件夹，每个 Skill 一个二级目录，内含 `SKILL.md`（必需）与 `README.md`（说明）。

```
yanyanskill/
└── wesight/                    # WeSight 项目相关
    └── wesight-im-pipeline/    # IM 桥全链路手册 + 行为规范
        ├── SKILL.md
        └── README.md
```

## 使用方法

```bash
# 以 wesight-im-pipeline 为例
mkdir -p ~/.claude/skills/wesight-im-pipeline
cp wesight/wesight-im-pipeline/SKILL.md ~/.claude/skills/wesight-im-pipeline/
```

重启 Claude Code 会话后生效。

## 作者

颜颜yan —— 内容创作者 & 独立开发者，公众号「颜颜yan的编程日记」。
