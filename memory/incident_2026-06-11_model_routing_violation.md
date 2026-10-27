# Incident: 模型分级调用策略执行失败

**日期**: 2026-06-11 11:57 GMT+7
**发现者**: Daryl
**严重级别**: P2 - 成本浪费

## 问题描述
今早08:00-11:00期间，main agent在处理以下任务时未执行模型分级策略：
- Heartbeat检查
- 生活提醒消息发送
- NO_REPLY场景
- 简单配置测试

**实际消耗**: $3.59 (Claude Sonnet 4.5, 49次调用)
**应该消耗**: ~$0.3-0.5 (Gemini 2.5 Flash)
**浪费比例**: 7-12倍

## 根本原因
1. **Session级别未配置模型override** - 虽然MEMORY.md有分级策略，但没有在实际session启动时强制执行
2. **缺少任务分类判断** - 没有在接到任务时先判断T1/T2/T3/T4级别
3. **默认模型过重** - main agent默认模型是Sonnet 4.5，未根据任务动态切换

## 影响范围
- 今日main agent所有轻量任务（heartbeat、生活提醒、简单确认）
- 预计月度多花费 ~$60-100

## 已采取行动
- ✅ HEARTBEAT.md增加Step 0强制任务分级判断
- ✅ 明确T4任务强制使用Gemini 2.5 Flash
- ✅ 创建learning_cost_optimization.md记录教训
- 🔄 待验证：下次heartbeat实际调用模型

## 预防措施
- **规则**: 每次回复前，先自问"这是T几任务？应该用什么模型？"
- **自检**: 汇报时必须标注调用模型，便于Daryl审计
- **技术**: 考虑在OpenClaw层面实现自动模型路由（由分类器判断）

## 相关文档
- MEMORY.md § Model Routing (2026-06-08 v2)
- 决策矩阵 P0-P3
