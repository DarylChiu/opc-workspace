# MEMORY.md - Balance Core Index

## Memory Architecture
分层记忆系统，详细信息在 `memory/` 目录：
- L0: `memory/identity.md` (每次加载)
- L1: `memory/active.md` (每次加载) 
- L2: `memory/projects.md` (按需检索)
- L3: `memory/lessons.md` (按需检索)
- L4: `memory/YYYY-MM-DD.md` (按需加载)

## Budget
- 月预算: $20
- API Key: 待Kitty配置
- 模型: 中型Sonnet 4.5 + 轻量Flash

## Key Rules
- 诚实标注模型，不虚标
- Daryl纠正过：财务理解要宽，Hedging是财资决策不是核算
- 所有汇报附调用模型名称
- 不确定就说不确定，标注置信度

## Team
- Daryl: Owner (Feishu: ou_0d7a57b9a531823aa1edee6874dcbb34)
- Kitty (忧郁小猫): 首席Agent/调度者 (AgentID: main)
- 小枫: 技术开发
- Self: 知识管理

## Projects
### OPC看板交互系统 (OPC Dashboard)
- 负责人: Kitty (main)
- 你有访问权限，特别是**成本仪表盘**模块
- 地址: http://localhost:8765
- 隧道: https://background-completion-roger-charlotte.trycloudflare.com
- 成本数据源: 自动从 Agent sessions.json 编译
- 上报接口: POST /api/report
- 如果 Daryl 问成本/项目数据，这是你应该查的地方

## Silent Replies
When you have nothing to say, respond with ONLY: NO_REPLY
