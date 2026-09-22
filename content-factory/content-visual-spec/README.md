# content-visual-spec

内容工厂的**封面与配图绑定层**：封面（cover）/ 插图（illus）/ 信息图（infograph）三类任务。

## 它管什么

| 哪一边 | 内容 |
|---|---|
| 真源 → `content-factory-kit/references/visual.md` | 四类配图的分工、各平台封面尺寸与安全区、截图脱敏、AI 插图风格统一、图上数字必须来自资料 |
| **本层** | 视频封面禁令、真实封面压缩示例、出图工具分工与提示词写法 |

**本机口径**：

- 视频封面**不含任何品牌元素**。
- AI 出图一律要「**无字底图 + 后期叠字**」的提示词 —— 不要让模型直接画正文文字（中文字形必崩）。
- 图上出现的任何数字都必须来自资料，不能编。

## 截图脱敏

配图里出现真机截图时，要处理掉：账号名 / 头像 / 侧栏历史条目 / 通知数 / 浏览器标签页标题 /
文件路径里的用户名。**脱敏不是可选项** —— 一张没脱干净的截图能泄露远超预期的信息。

## 安装

```bash
mkdir -p ~/.workbuddy/skills/content-visual-spec
cp SKILL.md ~/.workbuddy/skills/content-visual-spec/
```

**前置**：需要同时装 `content-factory-kit`。
