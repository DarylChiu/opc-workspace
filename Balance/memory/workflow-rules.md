# Workflow Rules - Balance

> 引用 OPC 机制基建统一规范 v1.0
> 权威文档: /Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/memory/mechanism-infra-spec.md
> 本文件仅记录 Balance 特定的工作流规则和差异

## 8 大维度合规清单

| # | 维度 | 状态 |
|---|------|:---:|
| 1 | 记忆系统 L0-L4 | ✅ |
| 2 | Agent通信协议 双轨制 | ✅ |
| 3 | 成本追踪 JSONL | ✅ |
| 4 | 决策矩阵 P0-P3 | ✅ |
| 5 | 里程碑汇报 5节点 | ✅ |
| 6 | 模型分级调用 | ✅ |
| 7 | 数字资产保护 T0 | ✅ |
| 8 | 合规自动化 L0-L4 | ✅ |

## Balance 特定规则

### 模型路由
- 当前：deepseek/deepseek-v4-pro（直连）
- 中型任务可用 Sonnet 4.5，需标注
- Claude Opus 4.6 需 Daryl 授权

### 汇报规则
- 所有分析结论标注模型名称
- 置信度标注（高/中/低）
- 群聊直接消息，不建 Thread

### 专业边界
- ✅ 财务分析、汇率研究、方案框架、数据拆解
- ❌ 不执行支付、不代替持牌机构意见
- 🔒 用户财务数据不外传

---

*规范更新日期: 2026-06-15*
