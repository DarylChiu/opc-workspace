# 模型分级调用规则 v3 (2026-06-14 废弃)

> ⚠️ **已废弃** — OpenRouter 余额不足，所有 Agent 统一改用 DeepSeek 直连 `deepseek/deepseek-v4-pro`。
> 
> 本文件保留作为历史记录，不再生效。
> 
> 废弃原因：Kitty (main agent) 调用 OpenRouter API 时报 billing error，余额耗尽。
> 新策略：全量使用 DeepSeek v4 Pro 直连，取消分级调用。

## ~~原四层分级（已废弃）~~

| 级别 | 模型全称 | 通道 | 适用场景 |
|------|---------|------|---------|
| ~~T1 重型~~ | ~~`openrouter/anthropic/claude-opus-4.6`~~ | ~~OpenRouter~~ | ~~知识库架构规划~~ |
| ~~T2 中型~~ | ~~`openrouter/anthropic/claude-sonnet-4.5`~~ | ~~OpenRouter~~ | ~~深度研究、跨领域分析~~ |
| **T3 标准** | `deepseek/deepseek-v4-pro` | DeepSeek直连 | **全部场景（当前唯一）** |
| ~~T4 极轻量~~ | ~~`openrouter/google/gemini-2.5-flash`~~ | ~~OpenRouter~~ | ~~心跳、确认回复~~ |

## 新规则
- **唯一模型**: `deepseek/deepseek-v4-pro` (DeepSeek 直连)
- **分类器**: 废弃，无需分级
- **汇报格式**: 不再标注模型和成本
- **月预算**: 无限制（DeepSeek 直连成本极低）
