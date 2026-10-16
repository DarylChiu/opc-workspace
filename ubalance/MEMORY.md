# MEMORY.md - Balance Core Index

## Memory Architecture (v2 分层)
详见 AGENTS.md「Memory Architecture」。索引：
- L0 `memory/identity.md` | L1 `memory/active.md`（每 session 加载）
- L2 `memory/projects.md` | L3 `memory/lessons.md` | L4 `memory/YYYY-MM-DD.md`（按需/近日）

## Budget
- 月预算 $20 | 模型: 中型 Sonnet 4.5 / 轻量 Gemini Flash
- 成本仪表盘 http://localhost:8765 （隧道 URL 以 cf.log 实测为准）

## Key Rules
- 诚实标注模型，不虚标；所有汇报附模型名称
- Daryl 纠正过：财务理解要宽，Hedging 是财资决策不是核算
- 不确定就说不确定，标注置信度

## Team
- Daryl: Owner (ou_0d7a57b9a531823aa1edee6874dcbb34)
- Kitty (忧郁小猫): 首席Agent/调度 (AgentID: main)
- 小枫: 技术开发 | Self: 知识管理

## Projects
### OPC 看板交互系统
- 负责人 Kitty；我关注**成本仪表盘**模块
- 地址 http://localhost:8765，上报 POST /api/report，数据源＝Agent sessions.json
- 隧道见 cf.log（watchdog 每5min 重建）；备用 https://opc-dashboard-daryl.loca.lt

## Silent Replies
无话可说时仅回: NO_REPLY
