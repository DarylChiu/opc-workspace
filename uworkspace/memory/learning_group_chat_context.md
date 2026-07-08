# Learning: 群聊Context策略

**日期**: 2026-06-11
**来源**: Daryl指正

## 错误理解（已修正）
我曾认为：为了省token，被@时也应该尽量少加载context，直接回复。

## 正确策略
**被@时必须做**：
1. 读群聊session最近5-10条消息
2. 理解事件前因后果
3. 再执行任务或给出意见

**不被@时**：
- HEARTBEAT_OK保持沉默
- 避免无效旁听和token浪费

## 核心原则
- **有效参与 > 盲目参与 > 完全不参与**
- 成本优化不能以"答非所问"为代价
- Context理解是质量保证，不是可选项

## 实现方式
被@时的标准流程：
```
1. sessions_history(sessionKey=群聊key, limit=10, includeTools=false)
2. 快速阅读最近对话，提取关键信息
3. 理解当前任务/问题的背景
4. 给出informed reply
```

## 相关文档
- AGENTS.md § Know When to Speak (已更新)
