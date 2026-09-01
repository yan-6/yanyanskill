# wesight-im-pipeline

WeSight IM 桥（微信/飞书 ↔ agent）全链路手册 + 会话行为规范，供 Claude Code 作为 Skill 使用。

## 功能

一个 Skill 覆盖两类场景：

1. **链路排障手册**：排查「微信发消息 → agent 处理 → 回复回传」全链路问题（收不到消息、回复丢失、处理超时截断、网关断连），或需要了解/修改桥架构时使用。提供逐跳架构图、关键函数与行号索引、日志关键字、典型症状的定位套路。
2. **IM 会话行为军规**：当前会话经由 IM 桥驱动时自动生效，约束 agent 的回合时长（≤4 分钟）、阶段化汇报、禁用后台任务、长任务 nohup 脱离等，保证手机端用户收到完整结果。

## 链路速览

```
微信 ←→ NativeWeixinGateway ──→ IMGatewayManager ──→ IMCoworkHandler ──→ Claude Code 会话
         (收/发消息)              (路由/绑定/网关管理)    (会话映射/累加器)         (agent 处理)
                                                              ↓ 结果
微信 ←── sendConversationReply ←── imDeliveryRoute/imReplyGuard ←── 回复累加器
```

涉及的 WeSight 源码位于 `wesight-upstream/src/main/im/`。

## 安装

```bash
mkdir -p ~/.claude/skills/wesight-im-pipeline
cp SKILL.md ~/.claude/skills/wesight-im-pipeline/SKILL.md
```

重启 Claude Code 会话后生效。会话中识别到 IM 桥消息（conversationId 形如 `weixin-native:...`）或用户要求排查 IM 链路时自动触发。

## 维护说明

- SKILL.md 中的函数行号基于 2026-09-01 的源码快照，WeSight 源码更新后可能漂移，失准时以函数名 grep 定位为准。
- 行为军规源自 2026-09-01 真实排障事故（5 分钟累加器死倒计时、`isReminderSystemTurn` 守卫丢弃最终结果、后台任务拖住回合），配套文章见公众号「颜颜yan的编程日记」。
