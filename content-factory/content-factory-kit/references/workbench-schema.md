# 支路 C · 模板源与复刻清单结构

> 本文是 `content-factory-kit` 的支路 C 参考（清单契约与 11 张表的字段清单）。
> 怎么执行复刻见 `references/workbench-clone.md`；怎么做模板源见 `references/template-authoring.md`。

页面标题：**创作小屋 · 灵感营地**｜产物文件名：`ai-content-workspace.html`
清单 schema：`aiws-template/1`｜**11 张表 / 149 个字段 / 82 条示例记录**

## 一、产物里的两处标记

模板产物（`assets/ai-content-workspace-template.html`）里有两段用注释包起来的区块，
复刻时**都整块删掉**：

| 标记 | 内容 | 为什么必须删 |
|---|---|---|
| `<!--AIWS-DEMO-BLOCK-START-->` … `<!--AIWS-DEMO-BLOCK-END-->` | 假 SDK 演示层 | 它接管了 localStorage 的数据读写。留着新页读的是浏览器里的假数据，读不到自己云端的表。 |
| `<!--AIWS-MANIFEST-START-->` … `<!--AIWS-MANIFEST-END-->` | 复刻清单本身 | 复刻产物是**工作页**不是模板页；清单留着会干扰表 id 的计数判据。 |

内嵌清单本体：

```html
<script type="application/json" id="aiws-template-manifest">
  { ... 复刻清单 JSON ... }
</script>
```

> 清单里所有 `<` 都写成 JSON 转义 `\u003c`，避免产物里出现裸 `</script>` 之类会截断解析的序列。
> 用 `json.loads` 读即可，会自动还原。

## 二、清单的字段结构

```jsonc
{
  "schema": "aiws-template/1",
  "page":   { "title": "…", "fileName": "…" },
  "demoBlock": { "start": "<!--AIWS-DEMO-BLOCK-START-->",
                 "end":   "<!--AIWS-DEMO-BLOCK-END-->" },
  "tables": [
    {
      "key":          "content",          // 表的主键名（页面的 var DB 用它做键）
      "title":        "内容主表",          // 建表用的表名
      "oldDatabaseId":"AMmQ…",            // 原表 id，复刻时被替换掉
      "properties":   [ { "name": "内容ID", "config": { "text": "" } }, … ],
      "records":      [ { "内容ID": { "text": "CT-2026-0003" }, … }, … ]
    }, …
  ]
}
```

- `properties` 的形状**与 create-database 接口一致**（`{name, config}` 数组），可原样透传。
  建表脚本对 `config` 的值只做类型白名单校验后**原样转发**，所以 select 的嵌套形状
  `{"select":{"options":[{"text":…,"id":…,"style":…}]}}` 是正确写法，不要拍平成字符串数组。
- `records` 是 PropertyValue 形状（`{"text": "…"}` / `{"select": "…"}` / `{"multi_select": [ … ]}` /
  `{"number": 1}` / `{"date": "2026-08-18"}`），与 batch-add-records 接口一致。

## 三、11 张表

| key | 表名 | 字段数 | 示例记录 | 管什么 |
|---|---|---|---|---|
| `content` | 内容主表 | 19 | 10 | 每篇稿子的主记录（标题/大纲/正文/状态/计划发布） |
| `topic` | 选题库表 | 18 | 12 | 选题雷达与状态流转 |
| `resource` | 研究资料表 | 6 | 8 | 研究产出与信息来源 |
| `task` | 今日任务表 | 8 | 8 | 今天该干什么 |
| `pub` | 内容排期记录 | 11 | 10 | 发布记录与发布链接 |
| `review` | 复盘数据表 | 17 | 14 | 各平台数据回流与互动率 |
| `asset` | 素材库表 | 9 | 10 | 沉淀的方法、金句、文章结构、案例 |
| `idea` | 灵感速记表 | 4 | 5 | 灵感速记 |
| `account` | 账号管理 | 20 | 5 | 平台账号与粉丝数 |
| `activity` | 活动管理表 | 24 | 0 | 活动、打卡、连更 |
| `queue` | AI任务队列 | 13 | 0 | 派活给 WorkBuddy 的任务队列 |
| | **合计** | **149** | **82** | |

> `活动管理表` 与 `AI 任务队列` 示例记录为 0 条，所以灌数据只发 9 个批次（不是 11 个）。
> 字段数合计 149 = 19+18+6+8+11+17+9+4+20+24+13。

## 四、每张表的字段

### 内容主表（`content`，19 字段）

`内容ID`(text)、`标题`(text)、`备选标题`(text)、`内容类型`(select：深度文章 / 产品评测 / 实战教程 / 行业分析 / 热点评论 / 项目案例 / 视频 / PPT / 短内容)、`所属栏目`(text)、`目标平台`(multi_select：微信公众号 / 掘金 / 小红书 / 视频号 / 抖音 / B站 / 其他)、`状态`(select：待研究 / 研究中 / 待大纲 / 写作中 / 待修改 / 待配图 / 待发布 / 已发布 / 待复盘 / 已完成)、`优先级`(select：P0 / P1 / P2)、`来源选题ID`(text)、`来源选题标题`(text)、`研究摘要`(text)、`内容大纲`(text)、`正文`(text)、`制作方案`(text)、`创作进度`(number)、`创建时间`(date)、`更新时间`(date)、`计划发布时间`(date)、`备注`(text)

### 选题库表（`topic`，18 字段）

`选题标题`(text)、`类型`(text)、`一句话大纲`(text)、`状态`(text)、`创建日期`(text)、`选题ID`(text)、`来源`(text)、`原始链接`(url)、`来源类型`(select：AI新闻 / 产品发布 / GitHub项目 / 个人灵感 / 公众号文章 / 社交媒体 / 读书/播客 / 品牌合作 / 用户反馈 / 其他)、`发现时间`(date)、`事件发生时间`(date)、`选题方向`(text)、`为什么值得写`(text)、`切入角度`(text)、`目标读者`(text)、`优先级`(select：P0 / P1 / P2)、`内容ID`(text)、`备注`(text)

### 研究资料表（`resource`，6 字段）

`内容ID`(text)、`资料名称`(text)、`资料类型`(select：新闻链接 / 官网 / GitHub / 公众号文章 / 产品资料 / PDF / 图片 / 个人笔记 / 其他)、`链接`(url)、`备注`(text)、`创建时间`(date)

### 今日任务表（`task`，8 字段）

`内容ID`(text)、`关联内容标题`(text)、`任务标题`(text)、`任务类型`(select：判断选题 / 深度研究 / 写大纲 / 写初稿 / 修改润色 / 配图制作 / 发布 / 数据复盘 / 资产沉淀 / 其他)、`计划日期`(date)、`状态`(select：待办 / 已完成 / 已延期)、`优先级`(select：P0 / P1 / P2)、`创建时间`(date)

### 内容排期记录（`pub`，11 字段）

`标题`(text)、`形式`(text)、`状态`(text)、`平台`(text)、`时段`(text)、`发布日期`(text)、`浏览量`(number)、`内容ID`(text)、`实际发布时间`(date)、`发布链接`(url)、`发布状态`(select：待发布 / 已发布)

### 复盘数据表（`review`，17 字段）

`内容标题`(text)、`完播率`(number)、`互动率`(number)、`关注率`(number)、`转化率`(number)、`判定`(text)、`日期`(text)、`内容ID`(text)、`阅读量`(number)、`点赞`(number)、`收藏`(number)、`转发`(number)、`评论`(number)、`新增关注`(number)、`发布平台`(text)、`AI复盘`(text)、`复盘时间`(date)

### 素材库表（`asset`，9 字段）

`素材名称`(text)、`类型`(text)、`内容`(text)、`星级`(number)、`备注`(text)、`内容ID`(text)、`资产分类`(select：历史文章 / 方法论 / Skills / Prompts / 案例库 / 素材库 / 金句 / 文章结构 / 选题方法)、`关联内容标题`(text)、`创建时间`(date)

### 灵感速记表（`idea`，4 字段）

`日期`(text)、`灵感内容`(text)、`是否转选题`(text)、`备注`(text)

### 账号管理（`account`，20 字段）

`账号ID`(text)、`账号名称`(text)、`平台`(select：微信公众号 / CSDN / 小红书 / 知乎 / 掘金 / 视频号 / 抖音 / B站 / 微博 / 今日头条 / 百家号 / InfoQ / ModelScope / 个人博客 / X(Twitter) / YouTube / 其他)、`平台账号`(text)、`主页链接`(url)、`账号定位`(text)、`内容方向`(text)、`粉丝数`(number)、`累计发文`(number)、`账号状态`(select：运营中 / 筹备中 / 暂停更新 / 已停用)、`运营角色`(select：主阵地 / 同步分发 / 引流试水 / 变现承接 / 资料备份)、`优先级`(select：P0 / P1 / P2)、`更新频率`(text)、`账号权益`(text)、`变现方式`(text)、`起号时间`(date)、`数据更新日期`(date)、`登录方式`(text)、`AI诊断`(text)、`备注`(text)

### 活动管理表（`activity`，24 字段）

`活动名称`(text)、`活动状态`(select：待确认 / 报名中 / 已报名 / 未开始 / 进行中 / 已结束 / 已获奖)、`当前阶段`(select：未开始 / 报名中 / 进行中 / 已提交 / 已结束)、`活动形式`(select：内容征稿 / 话题挑战 / 直播活动 / 抽奖互动 / 系列专题 / 线下活动 / 其他)、`活动来源`(select：自己策划 / 平台官方 / 社区话题 / 博主联动 / 品牌合作 / 行业活动 / 其他)、`目标平台`(select：小红书 / B站 / 抖音 / 公众号 / 知乎 / CSDN / InfoQ / ModelScope / 多平台 / 脉脉 / 其他)、`重要程度`(select：高 / 中 / 低)、`活动进度`(number)、`投入成本(元)`(currency)、`实际曝光`(number)、`实际互动`(number)、`实际转化`(number)、`效果评分`(number)、`开始时间`(date)、`结束时间`(date)、`报名截止`(date)、`进度更新时间`(date)、`活动链接`(url)、`活动描述`(text)、`活动规则/要求`(text)、`预期目标`(text)、`进度备注`(text)、`复盘总结`(text)、`备注`(text)

### AI任务队列（`queue`，13 字段）

`任务ID`(text)、`动作ID`(text)、`动作名称`(text)、`目标类型`(text)、`目标键`(text)、`目标标题`(text)、`落点表`(text)、`落点字段`(text)、`状态`(text)、`任务卡`(text)、`结果摘要`(text)、`创建时间`(text)、`完成时间`(text)

## 五、原表 id（复刻时会被替换）

| key | oldDatabaseId | 在产物里出现次数 |
|---|---|---|
| `content` | `DEMOOldTablecontent000` | 1 |
| `topic` | `DEMOOldTabletopic00000` | 1 |
| `resource` | `DEMOOldTableresource00` | 1 |
| `task` | `DEMOOldTabletask000000` | 1 |
| `pub` | `DEMOOldTablepub0000000` | 1 |
| `review` | `DEMOOldTablereview0000` | 1 |
| `asset` | `DEMOOldTableasset00000` | 1 |
| `idea` | `DEMOOldTableidea000000` | 1 |
| `account` | `DEMOOldTableaccount000` | 1 |
| `activity` | `DEMOOldTableactivity00` | 1 |
| `queue` | `DEMOOldTablequeue00000` | 1 |

这些 id 属于**原作者账号**。复刻者对其没有任何读权限——这正是不能用
「读旧表导 CSV」那条路的原因。产物里每个 id 恰好出现 1 次（在 `var DB` 绑定里），
这是重映射的计数判据。
