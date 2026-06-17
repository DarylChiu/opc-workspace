# 模型路由策略 v3 (2026-06-09 更新)

> Daryl策略调整：2026-06-09 08:50  
> 本周有效，后续可能继续调整

## 当前策略

| Agent | 路由通道 | 模型 | 策略类型 |
|-------|---------|------|---------|
| **Kitty** (main) | OpenRouter | 三级调用 | Sonnet分类 → Opus/Sonnet/Flash 三级执行 |
| **Bryson** (xiaofeng) | DeepSeek直连 | deepseek-v4-pro | 单模型 |
| **Balance** | DeepSeek直连 | deepseek-v4-pro | 单模型 |
| **Self** | DeepSeek直连 | deepseek-v4-pro | 单模型 |

## 变化说明

- Bryson/Balance/Self 从 OpenRouter Claude Sonnet 4.5 切换回 DeepSeek V4 Pro 直连
- Kitty 保留 OpenRouter 三级调用策略（重任务需要 Opus）
- 目的：降低成本，集中重型任务到 Kitty
