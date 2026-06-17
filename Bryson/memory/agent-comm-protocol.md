# Agent间通信协议 v2.0 (飞书群聊)

> 设计：小风(Bryson) | 2026-06-06 | 基于OpenClaw原生工具

## 1. 基本原则
- **只用原生工具**: sessions_send / sessions_list / sessions_history
- **不搞额外基础设施**: 不要Python daemon、安全令牌、自定义API
- **轻量实用**: 能用文件共享的用文件，能用群聊的用群聊

## 2. 通信方式

### 方式A: 群聊内自然对话
- 两个Agent都在同一个飞书群里
- 通过@提及触发对方
- 适合: 日常协作、任务交接、状态同步

### 方式B: sessions_send 直接通信
- Agent直接向对方的session发送消息
- 适合: 需要对方执行具体任务、获取信息

```
# 小风 → Kitty (群聊session)
sessions_send(
  sessionKey="agent:main:feishu:group:oc_7d71d54d87cbd265d9c3811bc59840b2",
  message="Kitty，请确认你的记忆重构完成情况",
  timeoutSeconds=30
)

# Kitty → 小风 (群聊session)
sessions_send(
  sessionKey="agent:xiaofeng:feishu:group:oc_7d71d54d87cbd265d9c3811bc59840b2",
  message="小风，我的重构已完成，准备联调",
  timeoutSeconds=30
)
```

### 方式C: 共享文件空间
- 路径: ~/.openclaw/kitty_collab/
- 适合: 共享配置、任务板、协作文档

## 3. 群聊协作规则

### 谁回复什么
- **@吹点小风/@小风** → 小风处理
- **@忧郁小猫/@Kitty** → Kitty处理
- **@所有人/@_all** → 都需要响应
- **无@** → 根据上下文判断，避免同时回复同一个问题

### 避免冲突
- 看到对方已经在回复（输入中/已回复），不要重复回答
- 如果不确定谁该回，等3秒看对方是否回复
- 技术问题优先小风，日常管理优先Kitty

### 任务交接格式
```
[任务交接] 
- 任务: XXX
- 当前状态: XXX  
- 需要对方做的: XXX
- 相关文件: XXX
```

## 4. 共享任务板

位置: ~/.openclaw/kitty_collab/tasks.md

格式:
```markdown
# 共享任务板
## 进行中
- [小风] 任务名称 — 状态描述
- [Kitty] 任务名称 — 状态描述

## 完成
- [✅ 小风] 任务名称 — 完成时间
```

## 5. 应急协议
- 如果一个Agent的session出错，另一个通过群聊通知Daryl
- 重大决策必须等Daryl确认，不能两个Agent自己拍板
