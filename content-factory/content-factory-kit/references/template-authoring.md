# 支路 B（生产侧）· 单文件应用 → 可分发的模板源

> 本文是 `content-factory-kit` 的支路 B 正文。文中相对路径都相对**技能根目录**。

## 什么时候用

你有一个**单文件 HTML 应用**（页面 + 内联素材），但它读的是**你自己账号名下**的数据表。
现在要分享给别人，让 ta 也能拥有整套。核心矛盾：

> 数据表**没有公开分享通道**（只有 page 能 publish），别人读不到你的表；
> 而且协作成员只能在前端手动加。所以「让别人克隆」**不能依赖读你的表**。

**结论性做法**：把「建表 schema + 示例数据」打包成**复刻清单**内嵌进那张公开页，
清单跟着页面走，零权限依赖。

```
公开页（已 publish）  ──直链下载──▶  别人的 WorkBuddy
   ├─ 前端外壳（HTML/JS）
   ├─ 复刻清单（11 张表的字段 + 示例数据 + 原 databaseId）   ← 机读
   └─ 演示块（本地假数据层）                                 ← 复刻时整块删掉
```

## 前置判断（先做，别跳）

| 检查 | 命令/方法 | 不满足的后果 |
|---|---|---|
| 表结构能拿到 | 对每张表 `database/get_database_schema.py` | 清单里的建表字段就是猜的，复刻出来类型不对 |
| 有免鉴权直链 | `list-page-publish-artifacts` 取 `data.url` + `artifacts[].path`，然后 `curl --noproxy '*'` | 只能给 `workbuddy.link/p/...`，那是 SPA 外壳，抓不到清单 |
| publish 链接≠机读源 | 抓 `workbuddy.link/p/<id>` 只有几 KB | 别把外壳链接当模板源发给别人 |

## 做法（五步）

### 1. 生成复刻清单

写一个 `tools/gen_template_manifest.py`，合并三样东西：

- **每张表的真实 schema**（从线上接口拉，别手写）→ 转成 `create_database` 的
  `properties: [{name, config:{<类型>: ...}}]`
- **示例数据**（虚构、日期相对今天偏移，永不过期）→ 转成写入侧 `PropertyValue`
  （`{"text":"x"}` / `{"select":"进行中"}` / `{"multi_select":[...]}` / `{"date":"YYYY-MM-DD"}` / `{"url":{text,link}}`）
- **原 databaseId**（复刻方要靠它做重映射）

清单结构：

```json
{ "schema": "aiws-template/1", "version": "v47", "generatedAt": "2026-09-21",
  "page": {"title": "…", "fileName": "…html"},
  "demoBlock": {"start": "<!--XXX-DEMO-START-->", "end": "<!--XXX-DEMO-END-->"},
  "tables": [{ "key": "content", "title": "内容主表", "oldDatabaseId": "…",
               "properties": [...], "records": [...] }] }
```

**必做校验**（这一步回报最高，能抓出真实数据质量问题）：

- seed 里每个字段名都在表结构里（多的报错）
- **select / multi_select 的值必须在该字段的 options 里** —— 不在的话服务端会**静默丢弃**，
  复刻出来是残缺数据。实测一次就抓出 12 处这类问题。
- 清单表顺序 == 页面里 `var DB = {...}` 的键顺序（否则复刻方对不上第几张表）

### 2. 给演示块加切片标记，并内嵌清单

构建脚本里：

- 把「本地假数据层 + 示例数据」用 `<!--XXX-DEMO-BLOCK-START-->` / `-END-->` **夹住**。
  复刻方按标记整块删除即可，不依赖任何属性匹配（平台会重排标签属性）。
- 清单用 `<script type="application/json" id="xxx-template-manifest">` 内嵌，**外面再包一层注释标记**。
  JSON 里的 `<` 转义成 `\u003c`，防止内容里的尖括号提前闭合 script。
- 清单块要放在 **页面 DB 定义之前**，且**不要在演示块里面**（复刻后还要留着它）。

### 3. 双产物（关键，别只做一个）

| 产物 | 构建 | 平台注入脚本 | 用途 |
|---|---|---|---|
| 演示版 | `build.py --demo` | **剥掉** | 独立分发（静态托管/本地打开），零外部请求，打开即玩 |
| 模板页 | `build.py --demo --keep-inject` | **保留** | 挂进资料库、publish；复刻后靠它读云端表 |

为什么必须分：**复刻后的页面要读别人自己的云端表，就必须保留平台注入脚本**
（它提供 `__SMART_PAGE__` 这个数据库 SDK）；而独立分发的演示版留着它会 404 报
`Unexpected token '<'`。

### 4. 发布 + 拿机读直链

```
import_html.py --file-name "<标题>.html" --space-id <sid> --parent-id <文件夹id>
publish_page.py --node-id <node_id>
list-page-publish-artifacts --node-id <node_id>
  → data.url = https://workbuddy-space-static.codebuddy.work/page/<node_id>/<版本>/
  → 机读直链 = data.url + artifacts[0].path      ← 免鉴权，curl 直接 200
```

坑：① 除 import 外都要**清代理变量**，否则 `文件上传到 COS 失败`（瞬时，重试可过）；
② 机读直链带**版本号**，每次重新发布都要同步更新指向它的说明文案；
③ 旧版本目录仍可访问，所以过期链接不会 404，只是钉在旧版。

### 5. 写「一页使用说明」+ 复刻协议

说明页要讲清四件事：**它是什么（三层结构，哪层能拷哪层不能）**、
**两条路（只想看 / 想拥有）**、**可整段复制的复刻指令**、**诚实的能力边界**。

复刻指令必须是可执行的机械步骤（这是「一句复刻」的真正内容）：

1. 命令行下载机读直链成本地 HTML（不要用网页阅读器，会丢 script 块）
2. 按注释标记切片 → 取 `<script id="...-template-manifest">` 里的 JSON
3. 按 `properties` 建 N 张表 → 记下新 id → 按 `records` 灌数据
4. 删掉 demo 标记之间的整块
5. 把 HTML 里所有 `databaseId` 字面量从 `oldDatabaseId` 换成新 id
   （**自查判据：原文里不应再出现任何 oldDatabaseId**）
6. 导入资料库、把 N 张表挂到页面下
7. 把清单里每个 table 的 `oldDatabaseId` 改成新 id（供下次再复刻）

说明页里举例写 `<script ...>` / `<!--...-->` 时**必须转义 `&lt;` `&gt;`**，
否则平台当标签解析，会吞掉后面的 JS。

## 端到端验证（必须做，且要在线上实物上做）

写一个 `check_template_clone.js`，做「复刻演练」，全程本地模拟不碰远端：

- **A 离线**：解析清单 → 校验 N 张表齐全、每个 old id 确实出现在页面里 →
  造新 id → 删演示块 → 全量重映射 → 断言无残留 + 出现次数一致
- **B 浏览器**：给复刻后的页面挂一个桩 `__SMART_PAGE__.database`（记录被问了哪些表），
  断言页面**只按新 id 取数、一次都没碰 old id**，且演示提示条已消失
- **C 对照组**：同一套桩跑**未复刻**的原页 → 应「不读任何真 id + 提示条在」，
  证明这套断言真能分辨成功与没复刻

再对**线上实物**（机读直链下载回来的 HTML）跑一遍同样的演练：
平台的属性重排/注入只在线上出现，本地 dist 全绿不代表线上能过。

## 能力边界（要主动告诉对方，别让人误会）

- 页面里的 AI 按钮**不会当场跑**：它只是把任务卡写进队列表，真正执行的是对方本机的
  WorkBuddy + 各自的执行规范 + 定时任务。这部分**拷不走**。
- 个人写作风格/知识库要换成虚构示例，别把自己的内容资产带出去。
- 复刻是**新建** N 张表，不碰对方已有数据；但资料库**没有删表接口**，建了要手动删，
  所以动手前先跟对方确认要不要真建表。

## 消费侧：别用资料库自带 clone-flow 复刻这类产物

**坑（实测）**：资料库 `page/clone-flow.md` §3 靠 grep `databaseId: "xxx"` 判分支。
如果产物把表 id 写成 `var DB = { content : 'AMx…' }` 这种**键值对象**（很常见，
尤其是自己构建的单文件应用），产物里 `databaseId:` 字面量就是 **0 个** →
clone-flow 会**误判成「纯 HTML 页」走分支 A、直接跳过建表**，
最后给出一个指向原作者表的空页面，**全程不报错**。

而且即便判对了分支 B 也没用：分支 B 要「读旧表导 CSV」，跨账号没有读权限。

所以「按内嵌清单建表」是这类产物唯一可行的复刻路径：
不读原作者任何一张表，靠清单里的 `properties` + `records` 在对方账号重建。

**已有实现可直接用**：`references/workbench-clone.md` + `scripts/clone_workbench.py`
（复刻「创作小屋」工作台）就是这个路径的完整落地——含七步流水线
（取产物 / 解析清单 / 校验 / 剥块 / 建表 / 灌数据 / 重映射 + 导入 + 挂载）、
token 计数的 id 判据、以及用桩脚本替换资料库技能的全链路验收（不碰真账号）。
要为自己做的应用写消费侧脚本时，照它的结构抄。

## 配套

- **消费侧**（别人拿到模板源后怎么复刻）→ 本技能 `references/workbench-clone.md`
- 具体清单实例（11 张表 / 149 字段 / old ids）→ `references/workbench-schema.md`
- 更新已上线的资料库页面 → 技能 `library-live-page-update`
- 资料库本身的建表 / 导数 / 导入页面 / 挂载 API → 技能 `library`
