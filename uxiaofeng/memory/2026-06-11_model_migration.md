# 2026-06-11 模型迁移：统一DeepSeek直连

## 背景
- OpenRouter今天产生$20.86成本，远超预期
- Daryl指令：停止使用OpenRouter，统一使用DeepSeek V4 Pro直连

## 变更内容
- **旧规则**（四层分级）：
  - T1重型 → Opus 4.6 (OpenRouter)
  - T2中型 → Sonnet 4.5 (OpenRouter, 默认)
  - T3轻量 → DeepSeek V4 Pro (直连)
  - T4极轻量 → Gemini Flash (OpenRouter)

- **新规则**（统一模型）：
  - **所有任务** → DeepSeek V4 Pro (直连)

## 受影响的文件
- ✅ MEMORY.md (Model Routing章节)
- ✅ HEARTBEAT.md (任务分级判断)
- ✅ 当前session模型切换为deepseek/deepseek-v4-pro

## 生效时间
2026-06-11 21:40 起

## 预期成本变化
- OpenRouter → $0/天
- DeepSeek直连 → 按实际token消耗计费（价格远低于OpenRouter）

---
*记录者: Kitty | 最后使用OpenRouter模型: anthropic/claude-sonnet-4.5*
