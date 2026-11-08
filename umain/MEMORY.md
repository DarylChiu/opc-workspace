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

## 汇报 & 通信 🔴（2026-11-08 Daryl 拍板「方案B」· 默认不报）

**核心：默认不报。只报决策点；交付物攒到日报，不即时打断。**

### 报（3类·即时）
1. **要花钱** — 任何采购/订阅，附年化成本+推荐方案+不回复时的默认行动
2. **不可逆风险** — 删数据/改核心配置/对外发布/触碰安全红线
3. **方向要走不通** — 原定方案被证伪需换路；或承诺交不出来（提前说，别到点才发现）

### 不报（默认·绝大多数情况）
- 任务启动、执行过程、里程碑内部推进
- 与其他 Agent 的讨论/对抗/互审过程（谁驳谁、认错几条、commit 号）
- 自己的技术选型、参数调整、代码实现细节
- 中途小问题（自己解决了就不说）
- **交付完成也不即时报** → 进日报清单

### 日报（方案B·唯一交付通道）
- **每天 20:00 一条**，格式：`✅ 今日交付 / ⏸ 卡住 / 💰 待批`
- 无交付则当天不发（不刷存在）
- 超 4h 任务中途只在**超过 6h 未完成**时报一句「还在跑」，防以为我挂了

### 例外
- Daryl 主动问 → 立即答，不攒
- 【紧急】级别故障（Agent 全挂/数据丢失）→ 立即报，不等日报

### 保留条款
- 标题→完成情况→问题→决策需求→下一步（日报内也守这个结构）
- 自主决策记理由（写进 memory，不报给 Daryl）
- 系统级操作前群内@all通知 → 等全部确认再执行

## 模型路由（2026-09-17 Daryl 拍板：私聊/群聊分档）
- **私聊 DM（Daryl 直连）**: main(Kitty) / xiaofeng(Bryson) = `deepseek/deepseek-v4-pro` · balance / self = `deepseek/deepseek-v4-flash`
- **群聊（OPC of DarylChiu）**: 四家统一 `deepseek/deepseek-v4-flash`
- **默认兜底** `agents.defaults.model` = `deepseek/deepseek-v4-flash`
- 已弃用 OpenRouter · pro 单价约 flash 3×（输入 $1.32/输出 $3.96 vs $0.44/$1.32）
