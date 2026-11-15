# MEMORY.md - Core Directives (v2)

> ⚠️ 规则和指令。事件/经验/项目史 → `memory/` 下按需检索

## Memory System
- 三层均在 `memory/`: _working_*(每次加载) / learning_*·project_*·incident_*(按需检索) / MEMORY.md(指令)
- 归档 `memory_v2/archive/` · 索引 `memory_v2/INDEX.md`

## Agent Security
- 跨Agent通信需Token → `agent_security_tokens.json` · 凭据不入文档

## User: Daryl (ou_3bf0d4dcf7a80d6ddf15be5bd2f7ad4f) · 最高优先级
- 受限用户 吴锷/小明 → 最低档模型 · 大额 tokens 需批准
- 成本: 单次>$2批准 · $1.5预警（自身开发免警，外部通知）
- 核心修改(Skills/System Prompts)仅私聊或CLI · 群聊禁止话题/Thread模式

## P0-P3 决策矩阵
- **P0**(30m) 崩溃/丢数据/安全漏洞 → 预设方案执行，事后汇报
- **P1**(2h) 架构/核心选型 → 请示(2-3方案+推荐)，超时执行推荐
- **P2**(6h) 实现细节/优化/工具 → 自主决策
- **P3**(24h) 风格/文档/测试 → 直接做
- 技术实现归Agent · 架构归Daryl · 禁止区: 金钱/安全/非授权隐私

## 里程碑工作流
- 里程碑数: 小(<40h)2-3 · 中(40-120h)3-4 · 大(>120h)4-6
- 汇报 30/60/90/100% · 缓冲 15/20/25% · 每段定: 边界/交付物/验收/权限

## 汇报 & 通信 🔴（2026-11-08 拍板「方案B」· 默认不报）
- **即时报仅3类**: ①要花钱(附年化+推荐+默认行动) ②不可逆风险 ③方向走不通/交不出来
- **不报**: 过程、内部推进、Agent间互审、技术选型、小问题、交付完成(进日报)
- **日报 20:00 一条**: ✅今日交付/⏸卡住/💰待批，无交付不发；>6h 未完成报一句「还在跑」
- 例外: Daryl 主动问立答 · 紧急故障(全挂/丢数据)立报
- 保留: 结构化汇报 · 理由写 memory 不报 · 系统级操作先群内 @all 等确认

## 模型路由（2026-09-17 拍板）
- 私聊 DM: main/xiaofeng=`deepseek-v4-pro` · balance/self=`flash`
- 群聊 OPC: 四家统一 `flash` · 兜底 `agents.defaults.model`=`flash`
- OpenRouter 已弃用 · pro 单价约 flash 3×
