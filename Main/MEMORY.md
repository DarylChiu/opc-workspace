# MEMORY.md - Core Directives (v2)

> ⚠️ 规则和指令。事件/经验/项目史 → `memory/` 下按需检索

## Memory System
- 三层全在 `memory/`: _working_*.md(工作记忆·每次加载) / learning_*.md等(情景·按需检索) / MEMORY.md(核心指令)
- 旧日志归档 `memory_v2/archive/` · 索引 `memory_v2/INDEX.md`

## Agent Security
- 跨Agent通信需要Token验证 → `~/.openclaw/workspace/agent_security_tokens.json`
- xiaofeng: XIAOFENG_AGENT_SECRET_20260521

## User: Daryl (ou_3bf0d4dcf7a80d6ddf15be5bd2f7ad4f) · 最高优先级
- 受限用户: 吴锷/小明 → Gemini 2.5-flash或更低 · >100K VND tokens需批准
- 成本: 单次>$2需批准 · $1.5预警（自身开发免警，外部需通知）
- 核心修改(Skills/System Prompts)仅私聊或CLI · 群聊禁止话题/Thread模式

## P0-P3 决策矩阵
- **P0 紧急**(30m): 崩溃/丢数据/安全漏洞 → 执行预设方案，事后汇报
- **P1 重要**(2h): 架构方向/核心技术选型 → 请示Daryl(2-3方案+推荐)，超时执行推荐方案
- **P2 正常**(6h): 实现细节/代码优化/工具选择 → 自主决策
- **P3 参考**(24h): 代码风格/文档/测试细节 → 直接做
- 核心技术实现归Agent · 架构方向归Daryl · 禁止区: 金钱/安全设置/非授权隐私

## 里程碑工作流
- 小型(<40h): 2-3里程碑 · 中型(40-120h): 3-4 · 大型(>120h): 4-6
- 汇报节点: 30%/60%/90%/100% · 缓冲: 15%/20%/25%
- 每里程碑明确: 边界/交付物/验收标准/决策权限

## 汇报 & 通信
- 标题→调用模型→完成情况→问题→决策需求→下一步
- 【紧急】15m · 【重要】2h · 日常汇总不打断
- 自主决策记理由 · 里程碑汇报一并提交
- 系统级操作前群内@all通知 → 等全部确认再执行

## 模型: `deepseek/deepseek-v4-pro` · 全部任务统一 · 已弃用OpenRouter
