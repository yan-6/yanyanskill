# content-research-spec

内容工厂的**研究绑定层**：队列里的研究 / 核查 / 竞品 / 一键成篇任务该怎么跑、结果怎么写回工作台。

## 它管什么

通用规范在套件里，本层只装**本机绑定**：

| 哪一边 | 内容 |
|---|---|
| 真源 → `content-factory-kit/references/research.md` | 8 段结构、篇幅预算、来源标注规则、写回前验收清单 |
| **本层** | `queue.py` 写回命令（`done` / `apply` / `sources`）、研究资料表的表 ID 与字段结构、检索工具映射、本机坑 |

**检索工具映射**：WebSearch → WebFetch（能直取原文就直取）→ anysearch → AIHOT。

**本机坑（都复现过）**：

- `--token-stdin` 会把**整个 stdin** 读成 token；批量写要用 `--stdin` 模式（token 第一行，其余为 JSON）。
- url 字段直接传字符串会被后端拒绝 → 必须 `{"url":{"text":…,"link":…}}`。
- select / date 字段包装写错会被**静默丢弃**，不报错。
- 队列 13 个字段全是 text；写库后必须重扫表核验（可能「返回成功但没写进去」）。

## 核心口径

研究摘要**固定 8 段**；第 1 行必须是 `信息截止：YYYY-MM-DD`；末段必须是「信息来源」清单；
核心事实逐条带 `（来源：xxx）`；第三方转述数据保留原文措辞并标 `待核实`；
正文**按 ≤2400 字起稿**（上限 1500–2500，超限会被打回重压）。
跑完把实际用到的来源（最多 8 条）回写研究资料表。

## 安装

```bash
mkdir -p ~/.workbuddy/skills/content-research-spec
cp -r SKILL.md references ~/.workbuddy/skills/content-research-spec/
```

**前置**：需要同时装 `content-factory-kit`（通用规范真源）。只装本层会拿到本机命令但没有结构规范。

## 适配到你自己的账号

`references/workbench-facts.md` 里的表 id、工作目录、python 解释器路径都是**占位符**
（形如 `<内容主表ID>`、`<你的工作目录>`）。换成你自己资料库的值即可 ——
先列一遍表拿到各表 id，按同样的表名对应填进去。

## 维护说明

- 本层的写回命令与 `tools/queue.py` 的 `TARGETS` / `T_FIELD` 是耦合的，改一边要同步另一边。
- 通用规范改了（结构 / 篇幅 / 写回契约），要回头检查本层是否也需要补口径 ——
  口径只有一份，在套件里。
