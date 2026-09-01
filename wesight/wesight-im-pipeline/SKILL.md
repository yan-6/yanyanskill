---
name: wesight-im-pipeline
description: WeSight IM 桥全链路（微信/飞书 ↔ agent）手册与行为规范。两类场景使用：① 排查「微信发消息→agent 处理→回复回传」链路问题（收不到消息、回复丢失、处理超时截断、网关断连），或要了解/修改桥架构时；② 当前会话经由 IM 桥驱动时，约束 agent 的回合时长、汇报节奏、后台任务用法，保证手机端用户收到完整结果。源码位于 wesight-upstream/src/main/im/。
---

# WeSight IM 桥：全链路架构 + 排查 + 会话行为规范

## 链路全景

```
微信 ←→ NativeWeixinGateway ──→ IMGatewayManager ──→ IMCoworkHandler ──→ Claude Code 会话
         (收/发消息)              (路由/绑定/网关管理)    (会话映射/累加器)         (agent 处理)
                                                              ↓ 结果
微信 ←── sendConversationReply ←── imDeliveryRoute/imReplyGuard ←── 回复累加器
```

源码目录：`~/wesight/wesight-upstream/src/main/im/`。主日志：`~/Library/Logs/WeSight/main-YYYY-MM-DD.log`。

## 逐跳详解

行号基于 2026-09-01 源码快照，源码更新后可能漂移；失准时以函数名 grep 定位为准。

### 第 1 跳：NativeWeixinGateway（nativeWeixinGateway.ts, 452 行）

负责与微信的连接、收发消息（飞书对应 nativeFeishuGateway.ts）。

- `start(config)`:154 — 建立连接；`stop()`:194；
- `pollLoop(signal)`:305 — 轮询拉取新消息；
- `handleRawMessage()`:341 — 归一化原始消息，调 `messageCallback` 上报；
- `sendConversationReply(conversationId, text)`:286 — 把回复发回微信；
- `qrLoginStart/qrLoginWait`:228/249 — 扫码登录流程。

**常见故障**：断连后无自动重连（需 `IMGatewayManager.reconnectAllDisconnected()`:286 或重启）；扫码登录态过期。日志关键字：`NativeWeixinGateway`。

### 第 2 跳：IMGatewayManager（imGatewayManager.ts, 3214 行）

总编排：网关生命周期、平台↔agent 绑定、消息分流。

- 消息分流点 :340-357：**有 coworkHandler 一律走 Cowork 模式**（:340-346），否则退化到 `IMChatHandler`（直连 LLM、不经 agent，:357）；
- `startGateway/stopGateway`:950/1052；`startAllEnabled`:1133；
- `sendConversationReply(platform, conversationId, text)`:2598 — 所有回发最终走这里；
- `getStatus()`:531 — 网关连接状态；
- session 映射存 `imStore.ts`（`getSessionMapping`）。

**常见故障**：平台↔agent 绑定缺失导致消息走错模式或被丢弃。日志关键字：`IMGatewayManager`、`Using Cowork mode for message processing`。

### 第 3 跳：IMCoworkHandler（imCoworkHandler.ts, 1266 行）

把 IM 消息送进 Claude Code 会话并收集回复。**绝大多数"回复异常"都出在这一跳。**

- `ACCUMULATOR_TIMEOUT_MS = 5*60*1000` :64 — 回复累加器**固定 5 分钟死倒计时**，从收到用户消息起算，持续输出不重置；
- 超时处理 :793-795 — 截断现有部分，拼上 `[处理超时，以上为部分结果]` 发出；
- `handleMessage` :742 / `handleComplete` — 收集 agent 输出、回合收尾；
- `isReminderSystemTurn` 守卫 — 超时后回合若继续跑完，最终结果走 `sendAsyncReply`(:132) 后台补发，但守卫**只允许定时提醒类回合补发，普通对话的最终结果被静默丢弃**；
- session 映射过期自动重建 :279；可恢复 API 400 重建会话重试一次 :271；
- 权限确认弹窗 60 秒未响应自动拒绝，且确认后的后续结果同样被丢弃；
- 回合进行中用户再发新消息，会顶掉前一条的等待（前一条结果丢失）。

日志关键字：`IMCoworkHandler`、`completed IM cowork turn`、`skipping async reply`。

### 第 4 跳：回发（imDeliveryRoute.ts / imReplyGuard.ts）

- imDeliveryRoute — 按会话投递上下文（channel/to/accountId）路由回复；
- imReplyGuard — 空回复兜底文案（`DEFAULT_IM_EMPTY_REPLY`）、定时任务承诺校验（说了"会提醒"但没建任务时改发提示）。

## 排查套路

1. 先确定消息走到哪一跳：日志里顺次搜 `NativeWeixinGateway` → `Using Cowork mode` → `IMCoworkHandler` → `completed IM cowork turn`，断在哪跳查哪跳。
2. 「处理超时，以上为部分结果」→ 第 3 跳累加器超时，且后续结果多半被 `isReminderSystemTurn` 守卫丢弃（搜 `skipping async reply` 确认）。
3. 完全没回复 → 查网关连接状态（`getStatus`）与绑定；再查 `skipping async reply`。
4. 回复变成纯闲聊、没有工具调用 → 走到了 IMChatHandler 直连模式，查 coworkHandler 为何不可用。

## IM 桥会话行为规范（agent 侧）

当前会话经由 IM 桥驱动时的行为军规。识别信号：宿主日志 conversationId 形如 `weixin-native:...`，或用户消息为手机端短句风格且会话由 IM 桥（而非桌面 UI）驱动。

1. **每回合 ≤ 4 分钟**。从接单到结束回合回复控制在 4 分钟内，给 5 分钟死倒计时留 1 分钟余量。
2. **阶段化汇报**。接单先回一句"分几步做"；每完成一个阶段立即结束回合、回复阶段结果；等用户说"继续"再推进。不要连续闷头做多个阶段。
3. **禁用 harness 后台任务**（run_in_background / 后台 Agent）。它不阻塞回复，但回合保持打开直到任务完成，5 分钟定时器照样触发（2026-09-01 实测：后台任务跑 8 分钟 → 超时截断 → 完成时结果被守卫丢弃）。
4. **长任务脱离会话执行**：用 `nohup ... &` 彻底脱离（不追踪、完成不通知），后续回合再用快速命令查日志/结果文件；或拆成小步同步做。
5. **避免权限确认弹窗**。优先只读操作和已允许的工具；非触发不可时，提前一回合告知用户"马上会弹确认，请尽快回复允许"。
6. **提示用户别连发**。回合未回完时用户再发消息会顶掉前一条；回合短了用户自然等得住。
7. **回复自包含**。每回合的结束语应是完整的阶段结论——IM 用户看不到工具过程，只看最终文本。
