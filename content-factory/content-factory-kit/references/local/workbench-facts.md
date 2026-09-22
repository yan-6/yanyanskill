# 创作小屋工作台 · 事实与命令速查

配套 `references/local/research.md` 使用。所有 ID 与字段名来自线上表，写错包装类型后端会静默丢值。

## 一、工作目录与环境

- 工作目录：`<你的工作目录>`
- Python：`<你的 python 解释器>`
- 每条 Bash 首行：`export PATH="/usr/bin:/bin:/mingw64/bin:$PATH"`（`dirname: command not found` 是无害噪音）
- 资料库脚本目录：`<资料库 skill 目录>`
- 取 token：`connect_open_platform(skill_id="library")` → `op_` 开头，约 30 分钟有效

## 二、表 ID 与字段

| 表 | ID | 关键字段 |
|---|---|---|
| 内容主表 | `<内容主表ID>` | 内容ID / 标题 / 状态(select) / 研究摘要 / 内容大纲 / 正文 / 制作方案 / 备选标题 / 更新时间(date) / 优先级(select) |
| 选题库 | `<选题库ID>` | 选题ID / 选题标题 / 状态 / 为什么值得写 / 切入角度 / 一句话大纲 / 目标读者 / 来源 / 来源类型(select) / 原始链接(url) |
| 研究资料表 | `<研究资料表ID>` | 内容ID / 资料名称 / 资料类型(select) / 链接(url) / 备注 / 创建时间(date) |
| AI 任务队列 | `<AI任务队列ID>` | 任务ID / 动作ID / 动作名称 / 目标类型 / 目标键 / 目标标题 / 落点表 / 落点字段 / 状态 / 任务卡 / 结果摘要 / 创建时间 / 完成时间（**13 个字段全是 text**） |
| 素材库 | `<素材库ID>` | 内容ID / 素材名称 / 内容 / 资产分类(select) / 关联内容标题 |
| 复盘数据表 | `<复盘数据表ID>` | 内容ID / 内容标题 / AI复盘 / 判定 / 复盘时间(date) |
| 账号管理 | `<账号管理表ID>` | 账号ID / 账号名称 / 平台(select) / 粉丝数(number) |

- 状态枚举（内容）：待研究 / 研究中 / 待大纲 / 写作中 / 待修改 / 待配图 / 待发布 / 已发布 / 待复盘 / 已完成
- 五段进度：研究 → 大纲 → 正文 → 配图 → 发布（`FLOW_STEPS`）
- 资料类型枚举：新闻链接 / 官网 / GitHub / 公众号文章 / 产品资料 / PDF / 图片 / 个人笔记 / 其他

## 三、queue.py 命令与大表字段清单

`tools/queue.py` 内部的 `TARGETS` / `T_FIELD` 已登记：内容主表、选题库、复盘数据表、素材库、账号管理、**研究资料表**。

写回命令：

```bash
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin done  <任务ID> --summary "一句话" --value "$(cat /path/out.txt)"
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin apply <任务ID> --json /path/pipeline.json
printf '%s' "$TOKEN" | python3 tools/queue.py --token-stdin sources <内容ID> --json /path/sources.json [--dry]   # 来源回流（去重/上限 8 条）
```

pipeline JSON 只用这 5 个键：`研究摘要` `内容大纲` `正文` `制作方案` `状态`（值 `待发布`）。

`sources` 的来源文件结构：`[{"名称":…, "类型":…, "链接":…, "备注":…}, …]`（也兼容 `{"sources":[…]}`）；
工具内部按「内容ID + 链接」去重、非法类型归「其他」、缺名称跳过、最多 8 条，`--dry` 只预览不写库。

## 四、来源回流：优先用 queue.py sources（底层 batch_add 仅用于批量补历史）

日常回流一律走 `queue.py sources`（已内置去重与上限）。需要在没有队列任务的情况下批量补历史来源时，才直接用底层脚本：

```bash
# token 与 body 同走 stdin：token 第一行，其余为 JSON
printf '%s\n%s' "$TOKEN" "$(cat payload.json)" | python3 \
  "$LS/database/batch_add_database_records.py" --token-stdin --stdin
# 其中 LS=资料库 skill 目录
```

payload 结构（数组，最多 100 个对象）：

```json
{"databaseId":"<研究资料表ID>","records":[
 {"properties":{
   "内容ID":{"text":"CT-2026-0017"},
   "资料名称":{"text":"GitHub Blog：Copilot runtime 迁移到 Rust"},
   "资料类型":{"select":"官网"},
   "链接":{"url":{"text":"GitHub Blog","link":"https://github.blog/..."}},
   "备注":{"text":"一手来源，含 832,378 行等原始数据"},
   "创建时间":{"date":"2026-09-18"}}}]}
```

踩坑（已复现）：

1. `--records` 传大 JSON 在 Git Bash 下静默失败 → 一律用 `--stdin`。
2. url 字段直接传字符串会被后端 11607 拒绝 → 必须 `{"url":{"text":..., "link":...}}`。
3. select / date 字段写错包装会被静默丢弃 → 值域必须与枚举一致。
4. 查询返回的 url 是 `[{link,text}]` 数组，复核脚本按数组判断。
5. 去重前的查询：`query_database_record.py --database-id <表> --page-size 200`，按「内容ID + 链接」比对。

## 五、复核方式

```bash
printf '%s' "$TOKEN" | python3 tools/scan.py --token-stdin --out .scan/check.json   # 全表 dump
```

- `--out` 必须带目录（写 `tmp.json` 会 WinError 3）。
- 复核要点：四段产出落库、状态推进到待发布、来源条数与去重结果。

## 六、页面与发布

- 页面节点：`<页面节点ID>`，发布链接 `https://workbuddy.link/p/<页面节点ID>`
- 产物：`dist/ai-content-workspace.html`（`python build.py` 重建；源在 `build/p*.html|js`）
- 研究与写作规范写在页面侧：`build/p29_aiexec.js`（`AI_HARD_RULES` / `aiBaseContent` / `aiPipelineCard`）、`build/p30_aiactions.js`（`AI_RESEARCH_SHAPE` / 各动作模板 / `AI_WRITE_CMD`）
- 改页面要重发版本：先 `list_page_publish_artifacts` 看线上版本，再以该版本为 base 建事务（并行会话常同时发版，base 过期会报 19901）
- 发布相关流程见 skill `library-live-page-update`
