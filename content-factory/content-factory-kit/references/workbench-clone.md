# 支路 C（消费侧）· 复刻「创作小屋」内容运营工作台

> 本文是 `content-factory-kit` 的支路 C 正文。文中相对路径都相对**技能根目录**；
> 11 张表的字段清单与 old id 见 `references/workbench-schema.md`。

把一个自带 11 张云数据表的内容运营工作台，装进**当前用户自己**的资料库。
产出：11 张表 + 82 条虚构示例数据 + 1 个能立刻打开用的工作台页面，表挂在页面节点下。

## 一句话执行

```bash
export PATH="/usr/bin:/bin:/mingw64/bin:$PATH"
SKILL="$HOME/.workbuddy/skills/content-factory-kit"   # 或技能实际所在目录

# 先干跑一遍（不写任何东西，只做本地检查）
printf '%s' "$TOKEN" | python3 "$SKILL/scripts/clone_workbench.py" --token-stdin --dry-run

# 确认没问题再真跑
printf '%s' "$TOKEN" | python3 "$SKILL/scripts/clone_workbench.py" --token-stdin
```

跑完拿到回执里那个 `/space/d/<nodeId>` 链接就是新的工作台。

**token 怎么来**：和资料库技能一致——`ToolSearch` 查 `connect_open_platform`，
`DeferExecuteTool` 调它，`skill_id=library`，拿到的 token 经 stdin 传入。
**不要**把 token 写进命令行参数。

## 为什么不能用资料库自带的 clone-flow

资料库 `page/clone-flow.md` 的分支 B 是「读旧表 → 导出 CSV → 建新表」。
这条路对本工作台**必然失败**，两个原因，都必须知道：

1. **权限**：HTML 里硬编码的表属于原作者账号，复刻者没有任何读权限，
   第一步导出就挂。
2. **更隐蔽的**：clone-flow §3 靠 grep `databaseId: "xxx"` 判分支。
   本工作台的产物里 **`databaseId:` 字面量数量是 0** —— 表 id 的写法是
   `var DB = { content : 'AMmQ...', ... }`（单引号、键值对象）。
   所以 clone-flow 会把它**误判成「纯 HTML 页」走分支 A，直接跳过建表**，
   最后得到一个指向原作者表的空页面，全程不报错。

本技能走的是**第三条路：按内嵌清单建表**——不读原作者任何一张表，
因此不需要任何跨账号权限。

## 它到底怎么工作

模板产物里内嵌了一份 JSON 复刻清单（`<script id="aiws-template-manifest">`），含：

- 11 张表的表名、建表字段定义（properties，与真实表结构同形状）、原表 id（oldDatabaseId）
- 82 条虚构示例记录（按 PropertyValue 形状写好，可直接灌）

脚本按清单在**当前用户账号**里建表、灌数据，然后把页面里写死的旧表 id
全部改写成新表 id，再导入资料库并挂好父子关系。全程不读原作者的表。

七个步骤（脚本内部打日志，`[n/7]`）：

| 步 | 做什么 | 硬门 |
|---|---|---|
| 1 | 取产物（默认用技能内置的那份，离线） | 下载不足 100KB 判为错误页/SPA 外壳并中止 |
| 2 | 解析内嵌清单 | 缺 MANIFEST 标记即拒绝，并提示该用模板版而非演示版/正式版 |
| 3 | 校验清单 | 字段类型合法、字段名不重复、记录不越界、select 取值在选项内 |
| 4 | 剥掉演示块 + 清单块 | 剥完 11 个旧 id 各须**恰好出现 1 次**（按独立 token 计） |
| 5 | 建表（并新建，不碰已有表） | 服务端返回的字段数须与清单一致；新 id 须互不相同、且不与旧 id 撞 |
| 6 | 灌示例数据 | 每批 ≤100 条；写入条数须回执一致 |
| 7 | 重映射 id → 导入页面 → 挂表 | 重映射双重硬门；页面节点 id 必须拿到 |

## 复刻前必须告诉用户的三件事

1. **会新建 11 张表**，资料库**没有删除表的接口**，建了只能在界面上手动删。
   所以先 `--dry-run` 看一遍，确认了再跑。想少建表就先别跑。
2. **示例数据是虚构的**，可以随便改、随便清空。它不是真实战绩。
3. **执行层不在复刻范围内**。复刻得到的是外壳 + 数据层；
   真正干活的五套规范（研究 / 写作 / 多平台改写 / 配图 / 资产沉淀）、
   风格指南、定时自动化都在原作者本机，是跟着人走的，需要另外安装。
   复刻完的页面里那些 AI 按钮**点了不会自己跑**——它们只往云端队列写任务卡，
   得有人领。

## 常用参数

```
--source <路径|URL>   模板产物来源。默认用技能内置产物（推荐，离线且不会失效）。
                      给 URL 时走「直连优先、失败再走代理」的重试（本机代理会拦静态产物域名）。
--work-dir <目录>     中间产物目录，默认 ./clone_work（含 schemas/ records/ page/ mapping.tsv）
--library-dir <路径>  资料库技能目录。默认从 $CODEBUDDY_SKILL_DIR / $CODEBUDDY_PLUGIN_ROOT
                      自动探测，探不到会明确报错让你手动指定。
--space-id <id>       目标空间，不传走默认空间
--parent-id <id>      新表的父节点，不传落空间根（导入页面后会挂到页面下）
--page-name <名>      新页面展示名，默认取清单里的 ai-content-workspace.html
--dry-run             只做本地部分 + 打印将要执行的写操作，不发任何写请求
--skip-page           只建表灌数据，不导入页面
--keep-work-dir       跑完保留中间产物（默认跑完自动清理）
--concurrency N       并发度，默认 6
```

## 线上产物被更新过时

内置产物是快照，可能落后。要拿最新版就从发布态静态地址复刻：

```bash
python3 "$SKILL/scripts/clone_workbench.py" --token-stdin \
  --source "https://workbuddy-space-static.codebuddy.work/page/<nodeId>/<版本号>/index.html"
```

`<版本号>` **每次发布都会 +1**，别写死。正确拿法：调资料库的
`page/list_page_publish_artifacts.py`（或 `space.page.list-page-publish-artifacts`），
取 `data.url` 拼上 `artifacts[].path`。

## 验证

技能自带全链路验收，**用桩脚本替换资料库技能**，因此不会在真账号里建出任何东西
（资料库不支持删表，这是必须的）：

```bash
python3 "$SKILL/tests/check_clone_workbench.py"
```

覆盖三段，共 39 项：

- **A 段（13 项）本地正确性**：清单校验报告、剥块彻底性、旧 id token 计数、
  干跑重映射后零残留旧 id、建表/灌数据载荷与清单逐表相符、记录无越界字段。
- **B 段（22 项）调用契约**：建表 11 次且表名与字段数逐张正确；灌数据落点
  **全是新建表 id、全不落旧 id**、总条数 82、批次不超 100、只覆盖有记录的 9 张表；
  `import_html` 的 `--databases` 恰好是那 11 个新 id；`move-node` 11 次且目标都是新页面节点；
  实际送进去的 HTML 零残留旧 id、无 AIWS 标记。
- **C 段（4 项）反向对照**：清单选项被删、标记缺失、DB 绑定被篡改、非模板产物——
  四种都被脚本正确拒绝并中止。**没有这一段，上面所有 ok 都可能是假绿。**

## 已知边界与坑

- **不要用资料库自带 clone-flow 复刻本工作台**（见上文两个原因，尤其 `databaseId:` 为 0 的误判）。
- **不要用网页阅读器/抓取工具取产物**：会把 `<script>` 块丢掉，清单也就没了。必须原始 HTML。
- **平台会改写发布产物**：给标签补属性、重排属性顺序、注入 `data-page-node-id`。
  所以复刻产物比原始 dist 略大是正常的；脚本只依赖标记与 id 字面量，不受影响。
- **剥块是必须的**：演示块（`AIWS-DEMO-BLOCK`）挂了假 SDK 接管 localStorage，
  留着会让新页读不到自己的云表；清单块留着没意义还干扰 id 计数。
- **空表不灌数据**：活动管理表 / AI 任务队列 示例记录为 0 条，脚本不会为空表发写请求，
  所以灌数据是 9 批 82 条，不是 11 批。
- **挂载失败不算致命**：表和数据都已经建好写好了，只是没挂到页面节点下，
  脚本只给 WARN，用户可在资料库里手动拖。
- **11 张表都在，字段数 149**：19+18+6+8+11+17+9+4+20+24+13。改过清单要同步这个数。

## 分享给别人的方式

这个技能目录是自包含的（含内置产物 2.7MB，离线可用）：

```
content-factory-kit/
  SKILL.md
  scripts/clone_workbench.py      复刻脚本（唯一入口）
  tests/check_clone_workbench.py  全链路验收（桩脚本，不碰真账号）
  assets/ai-content-workspace-template.html   内置模板产物（含清单）
  references/workbench-clone.md   本文（怎么复刻）
  references/workbench-schema.md  清单结构 / 11 张表 / 149 字段清单
```

把整个目录给对方放进 `~/.workbuddy/skills/` 即可；或告诉对方用资料库的
**模板源页面**（一句话「复刻给我」+ 模板源链接），由对方自己的 WorkBuddy 执行。

## 配套

- 把**自己的**应用做成这种模板源（生产侧）→ 本技能 `references/template-authoring.md`
- 执行层规范（复刻完的工作台怎么干活）→ 本技能 `references/` 下那 8 份执行规范
- 更新已上线的资料库页面 → 技能 `library-live-page-update`
- 资料库本身的建表/导数/导入页面 API → 技能 `library`（`database/`、`page/`、`space_api.py`）
