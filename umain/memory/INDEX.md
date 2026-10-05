# INDEX.md — 始终加载的精炼索引（封顶 ≤200 行）

> 维护：Kitty · 定位：新会话启动必读的「现在发生什么」快照 + 「细节去哪找」路标
> 不是 MEMORY.md 的重复（指令留在 MEMORY.md）· 不是日志（细节走 memory_search）· 不是 active.md 的复制（active 是全文，这里是蒸馏）

## 一、本周最要紧的 3 件事
1. **Dream Engine（记忆巩固）**：Daryl 已拍板精简版，Kitty 一人做。先出 INDEX.md 样例（本文件）→ 再写 consolidate.sh → 沙箱测试 → 挂 cron。
2. **OPC 看板入口**：serveo 隧道已死，正式入口改用 cloudflared `https://highways-colorado-impossible-dictionaries.trycloudflare.com`（待 Daryl 确认转正 + 杀 autossh）。
3. **成本护栏「方案A」已落地**（10/3）：exec 12/write 20，红线 $3 预警/$6 停。

## 二、活跃项目状态（一句话）
- **Dream Engine** 🟢 今天启动 · 计划 `memory/plan_dream_engine_opc_2026.md`
- **OPC 看板 v1.6** 🟢 运行中 localhost:8765 · M4(版本变更通知) 🟡 待开发
- **Decision Loop** 🟡 M2 剪辑MVP试点 · M0+M1 完成
- **OPC 自进化基建 L1** ⚪ Phase0 决策挂起（Balance 影子测试已结束）
- **Daryl 训练计划** 🟢 v1.1 全身版已交付
- **Agent 自进化(GEPA 类)** ⛔ 7/21 Daryl 叫停，严禁再开发

## 三、近期关键决策（近 30 天）
- 10/5 成本护栏方案A落地；10/3 exec/write 放宽；9/17 DeepSeek key 轮换定案（根因=旧 key 泄漏）

## 四、Agent 速查
| ID | 昵称 | 用户 | 模型(私聊) |
|----|------|------|-----------|
| main | 忧郁小猫 Kitty | Daryl | deepseek-v4-pro |
| xiaofeng | 吹点小风 | Bryson | deepseek-v4-pro |
| balance | 算点小账 | Balance | deepseek-v4-flash |
| self | 恨点小己 | Self | deepseek-v4-flash |
> 群聊统一 flash · 跨 Agent 通信需 Token 验证

## 五、红线提醒（易忘但致命）
- **T0 数字资产**：代码 git 强制管理 + 需求写日记，丢了直接删 Agent
- **成本**：$3 预警 / $6 停 · 单次 >$2 需批准 · 定时 LLM 走 llm_budget.sh 四道闸
- **GEPA 禁令**：提示自动进化/模型自我优化 严禁
- **不碰**：system prompt / safety 规则 / 核心文件(SOUL/USER/MEMORY 只读)

## 六、细节路标（去哪找）
- 完整活跃任务 → `memory/active.md`
- 核心指令/决策矩阵 → `MEMORY.md`
- 项目历史 → `memory/project_*.md`（memory_search）
- 教训 → `memory/learning_*.md` + `failure_patterns.json`
- 合规状态 → `memory/compliance-status.json`
