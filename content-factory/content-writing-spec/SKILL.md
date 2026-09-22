---
name: content-writing-spec
description: >-
  创作小屋内容工厂的写作绑定层。规定领取到写作类任务（大纲 / 初稿 / 续写 / 扩写 / 缩写 / 增强观点 /
  去 AI 味 / 口语化 / 优化开头结尾 / 起标题）时：先读套件里的通用写作规范，再按本层的个人判断标准
  （两套声道的具体长相、词库、签名式元素、标题实测区间）与写回契约落笔。
  当需要写正文、改稿、判断稿件是否达标时使用。
  关键词：写正文、改稿、去 AI 味、缩写、扩写、起标题、写作规范、声道、词库、签名式元素。
agent_created: true
---

# 内容写作 · 本机绑定层

创作小屋（AI 自媒体运营工作台）的写作类任务，由领取任务的 WorkBuddy 亲自写——页面只把任务卡写进队列。

> ## 通用规范在哪（先读它，再读本文）
>
> 写作的通用规则——声道模型、通用六拍、七体裁骨架卡、篇幅配比、段落与句子、标题公式与禁忌、
> 改稿细则（不可动清单 / 扩写 / 缩写 / 增强观点 / 口语化 / 开头结尾）、
> **去 AI 味 10 类黑名单与逐条改写对照**、交付自查、失败降级——**唯一真源是**：
>
> - **`~/.workbuddy/skills/content-factory-kit/references/writing.md`**
> - **`~/.workbuddy/skills/content-factory-kit/references/deai.md`**
>   （去 AI 味逐条对照；本技能原来的 `references/deai-examples.md` 与它逐句相同，已删除并入）
>
> 本文**不复述**上面那些，只写两样：**只对本账号生效的判断标准**、**本机写回契约**。
> 改通用口径就改套件那两份；改个人风格就改本文与风格指南。

## 何时使用

- 写作类动作：`outline` `gzhstruct` `draft` `cont` `expand` `shorten` `stronger` `deai`
  `spoken` `openhead` `openend` `titles10` `titlegzh` `titleviral` `titleknow` `titleab`，
  以及 `pipeline` 里的「正文」那一段
- 判断一份正文 / 标题 / 大纲能不能写回内容主表
- 调整写作阶段的产出标准

不适用：研究阶段（走 `content-research-spec`）、多平台改写（走 `content-platform-adapt`）、
封面与配图（走 `content-visual-spec`）、资产沉淀（走 `content-asset-loop`）。

## 一、两个真源的关系（别搞混）

| 层 | 真源 | 管什么 |
|---|---|---|
| **通用规则** | `kit/references/writing.md` + `kit/references/deai.md` | 格式约定：骨架、七体裁卡、篇幅配比、改稿步骤、AI 味清单 |
| **个人判断标准** | 本文 §二 + `ai-workspace/风格指南-颜颜yan.md` | 两套声道长什么样、词库、签名、标题实测区间 |

风格指南的 `DIGEST` 区块会随任务卡一起注入，写作前你手里已经有 8 条速用指令——
**那是摘要，不是全部规范**：体裁骨架、篇幅配比、改稿细则、AI 味黑名单在 kit 那两份里。

## 二、只对本账号生效的判断标准（kit 刻意不给，必须用这里的）

### 词库（可直接取用）

| 位置 | 备选 |
|---|---|
| 开场 | 逛到、刷到、发现、今天跟 AI 脑暴、前段时间、不知不觉、相信很多同学 |
| 过渡 | 说白了、其实、不过、注意、这就、那么、接下来、先说结论 |
| 强调 | 居然、竟然、真的、硬是、直接、完全 |
| 收尾 | 写在最后、总结、期待一下吧、咱们下期再见、一起学习一起加油、未来已来～ |
| 情绪 | 激动、惊艳、惊出一身冷汗、上头、好开心、没招儿了 |
| 系列感 | 本期、第一期、专栏系列、往期回顾、持续更新 |

### 签名式元素

- 格言「**生如芥子，心藏须弥**」（教程 / 正式稿收尾）
- 署名：颜颜yan_ / {颜颜YAN_}
- 连载意识：期数、系列名、下期预告
- 互动引导：欢迎 issue/commit、公众号关键词回复
- 配图习惯：真机截图为主，表情包梗图点缀，教程用 GIF 头图

### 标题实测区间（**本账号实测，不是行业参照系**）

**长度 25–35 字**（对标 2025–2026 成熟期；2025 后冒号两段式率 **64–68%**、2026 问号率 **11%**）。
早期「【】栏目前缀 + 短教程体」已弃用，除非写的本来就是连载教程。

> kit 里那段「中位 28 字、两段式 60%」是**别人样本**的参照系；本账号用上面这组。
> 重跑口径：`python3 ~/.workbuddy/skills/content-factory-kit/scripts/measure_titles.py <你的语料>`

### 两套声道的具体长相（判定规则与表格见 kit；这里只写「本账号长什么样」）

- **A 声道**：少用「我」，多用「本次 / 本文 / 适配中」；分层表格 + 清点式小标题；
  **结尾的能力边界是必写项**（「只讲优点不讲代价」是反模式第 3 条）。
- **B 声道**：高频「我」；一句成段；允许自嘲（菜鸟 / 摆烂 / FOMO / 没招儿了）与表情梗图；
  结尾给互动或下期预告。
- **去 AI 味的本账号口径**：具体动作替代抽象名词、长短句不齐、**保留判断力度**、允许自嘲。
- **两者绝不混用**——A 里忽然卖萌，或 B 里忽然「综上所述」，会立刻失味。这是自查第一条。

## 三、本机写回契约

工具：`tools/queue.py`（**不要绕过它直连 batch_update**，包装类型写错会静默丢值）。

```bash
export PATH="/usr/bin:/bin:/mingw64/bin:$PATH"
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin show  <任务ID>            # 读任务卡全文
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin claim <任务ID>
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin done  <任务ID> --summary "一句话" --value "$(cat 结果文件)"
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin apply <任务ID> --json 结果.json
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin fail  <任务ID> --summary "失败原因"
```

- **写作类单字段动作**（draft / cont / expand / shorten / stronger / deai / spoken / openhead / openend）
  → 落点字段是内容主表的**正文**，走 `done --value`。
- **标题类动作**（titles10 / titlegzh / titleviral / titleknow / titleab）→ 落点是**备选标题**，走 `done --value`。
- **`pipeline`** → 走 `apply --json`，键名只用这 5 个：
  `研究摘要` `内容大纲` `正文` `制作方案` `状态`（值 `待发布`）。
- 长正文一律用 `--value "$(cat 文件)"` 传，避免命令行转义；写临时文件用带内容 ID 后缀的新文件名，
  **不要复用上轮文件名**。
- JSON 键名必须与表字段名完全一致；输出里出现「跳过未知字段」说明键名写错了，要改。

表 ID 与字段清单见 `content-research-spec/references/workbench-facts.md`。

## 四、本机自查增量（kit 那份 12 条之外）

- 标题是否落在**本账号的** 25–35 字、两段式或亲测式？
- 交付长正文前用 `wc -m` 核一下字数，别凭感觉估。
- 改稿任务：数字、来源标注、「待核实」标记、证据、声道，一个都没被动过？

## 五、本机踩过的坑

- **别把 DIGEST 当成全部规范**。任务卡里注入的是 8 条速用指令；七体裁骨架、篇幅配比、
  改稿细则、AI 味黑名单在 `kit/references/writing.md` / `kit/references/deai.md` 里，要去读。
- **改稿不是重写**。收到 expand / shorten / deai 时就地改，不要把整篇换成自己的写法——
  那会让改稿后风格断裂。
- **「待核实」不能顺手删**。它看着像瑕疵，实际是必要的诚实标记。
- **缩写时别删论证链**。删到「结论还在但不知道为什么」就是删过头了。

## 六、相关规范（同一套内容工厂，按阶段分工）

| skill | 管什么 | 通用规范（真源，都在套件里） |
|---|---|---|
| `content-research-spec` | 研究阶段 | `kit/references/research.md` |
| `content-writing-spec` | **本 skill**：写作与改稿 | `kit/references/writing.md` + `kit/references/deai.md` |
| `content-platform-adapt` | 多平台改写 | `kit/references/platforms.md` |
| `content-visual-spec` | 封面与配图、截图脱敏 | `kit/references/visual.md` |
| `content-asset-loop` | 沉淀回流、素材库写回 | `kit/references/assets.md` |
