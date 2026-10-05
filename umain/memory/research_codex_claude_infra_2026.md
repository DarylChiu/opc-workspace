# 调研：Codex & Claude Code 基建（2026-10）· 供 OpenClaw 基建更新参考

> 日期: 2026-10-05 · Daryl 指派 · 主 Agent Kitty
> 交叉验证: OpenAI/Anthropic 官方文档 + VILA Lab 架构论文(arxiv 2604.14228) + mem0/vectorize/第三方剖析
> 结论一句话: 两大厂 2026 已收敛到同一套基建范式 —— AGENTS.md 指令层 + 自动记忆层(异步"睡眠式"巩固) + SKILL.md 技能 + 子代理 + Hooks/Plugins/MCP。自进化 ≠ 改自己代码，= 后台异步巩固记忆 + 按需加载技能。

---

## 一、脚手架（Scaffolding）

### Codex CLI (OpenAI)
- **AGENTS.md = 跨工具开放标准**：Codex/Cursor/Aider/Jules 等多工具收敛；开放格式规范已捐给 Linux Foundation 的 Agentic AI Foundation（agents.md）。
- **分层发现机制**（每次 run 构建一次指令链）：
  - Global: `~/.codex/AGENTS.md`（`AGENTS.override.md` 优先）
  - Project walk: 从 git root 走到 cwd，逐层 concat；同层 `AGENTS.override.md` 覆盖 `AGENTS.md`
  - Fallback 文件名: `project_doc_fallback_filenames`（可指向 CLAUDE.md/.cursorrules 等）
  - 上限 `project_doc_max_bytes` 默认 **32 KiB**（≈8000 token），超出静默截断
- 配置: `~/.codex/config.toml`

### Claude Code (Anthropic)
- **`/init` 脚手架**：自动分析 codebase 生成 CLAUDE.md（build/test/约定）；`CLAUDE_CODE_NEW_INIT=1` 时升级为多阶段流程 —— 询问要设哪些 artifacts（CLAUDE.md/skills/hooks）→ **子代理探索代码库** → 追问补缺 → **写文件前给出可审阅提案**。
- **`/doctor prompt-audit`**：审计指令文件的过期/冲突内容（为旧模型写的指令、不存在的文件引用、互相矛盾的规则），给出报告+建议修改，用户确认后才应用。

---

## 二、记忆系统（Memory）

### Codex：两层记忆
1. **AGENTS.md**（静态指令层，用户/团队写）
2. **Memories**（自动生成层，agent 自己写）：
   - **异步后台生成**：session 空闲 ≥6h 才纳入巩固；活动会话不触发
   - **双模型**：一个模型判定"什么值得记"，一个模型合并候选进存量记忆
   - **巩固子代理**：consolidation sub-agent 负责合并
   - 存储 `~/.codex/memories/`：`memory_summary.md`(先读) / `MEMORY.md`(长文合并) / `raw_memories.md` / `skills/<name>/SKILL.md` / `rollout_summaries/<slug>.md`
   - 上限: 256 rollouts 硬顶；30 天未召回的记忆 prune；**秘密脱敏**；rate-limit 感知(配额低时不跑)
   - 双开关：写开关 / 读开关 独立
- **召回方式 = 非向量**：session 启动读 `memory_summary.md` 全文 → token 截断；需要细节时 `grep` 过 `MEMORY.md`。
- 限制: 无跨机器同步、无团队共享；EEA/UK/瑞士 首发不支持。

### Claude Code：CLAUDE.md + Auto Memory + Dreams
- **CLAUDE.md 4 scopes**（宽→窄加载）：managed policy(组织) / user(`~/.claude/CLAUDE.md`) / project(`./CLAUDE.md`) / local(`./CLAUDE.local.md`)；另支持读 AGENTS.md。
  - `@path` 导入语法；`.claude/rules/` 路径级规则（paths frontmatter 只对匹配文件加载）
  - 建议单文件 <200 行
- **Auto Memory**（v2.1.59+，默认开）：Claude 自己写笔记到 `~/.claude/projects/<project>/memory/`；`MEMORY.md` 作索引 + 主题文件（debugging.md / api-conventions.md...）；每会话加载前 200 行/25KB；同 repo 所有 worktree 共享。
- **Auto Dream（Dreams 原语）**：空闲期后台子代理，读记忆库 + 历史 transcripts → 产出**重组后的记忆库**（去重合并 / 替换过期矛盾 / 提炼新洞察）；**绝不改源码**，只动记忆层；四阶段：读库存→收集信号→巩固(相对日期转绝对时间戳、删矛盾事实、prune 过期、合并重复)→重建 MEMORY.md 索引。
  - Dreams 原语: 1 记忆库 + 1-100 会话 → 1 新记忆库（输入库不变，可审阅丢弃）；异步 job；Research Preview（模型限 opus-4-8/4-7、sonnet-4-6）
- **召回方式 = 非向量**：读 MEMORY.md + 主题文件，走标准文件工具，不用语义向量检索。

---

## 三、自进化系统（Self-Evolution）

两者都不做"改自己代码/改 system prompt"，而是：
1. **自动记忆巩固**（见上：Memories / Auto Dream）—— 唯一真正"自动进化"的闭环
2. **Skills**：SKILL.md(frontmatter) + 支持文件，按需加载；现为 16+ 工具的开放标准（Codex/Claude/Cursor/Gemini CLI/VS Code）
3. **子代理**：Codex 最多 8 并行子代理（各自 context + 云沙箱）；Claude Code 子代理可带**独立持久记忆**
4. **Hooks**（PreToolUse 等拦截）+ **Plugins** + **MCP** 四扩展机制

### Claude Code 架构（VILA 论文核心，直接对比 OpenClaw）
- 核心 = 简单 while 循环（调模型→跑工具→重复）；大部分代码在循环外圈：
  - **权限系统**: 7 模式 + ML 分类器（auto-mode），"定义边界让 agent 自由工作"而非逐动作审批
  - **5 层 compaction pipeline** 管上下文
  - **4 扩展机制**: MCP / plugins / skills / hooks
  - **子代理委派** + **append-only 会话存储**
- **5 价值**：人类决策权威 / 安全 / 可靠执行 / 能力放大 / 上下文适应性
- **vs OpenClaw 差异**（论文 §10，对我们最相关）：
  | 维度 | Claude Code | OpenClaw |
  |------|------------|----------|
  | 安全评估 | 逐动作安全评估 | 边界级访问控制(perimeter) |
  | 运行形态 | 单 CLI 循环 | 网关控制平面内嵌 runtime |
  | 能力注册 | 上下文窗口扩展 | 网关级能力注册 |
- **6 开放方向**：可观测性-评估缺口 / 跨会话持久化 / harness 边界演化 / 视野扩展 / 治理 / 评估透镜

---

## 四、对 OpenClaw 基建更新的启示（映射）

| # | 借鉴点 | 我们的现状 | 建议动作 |
|---|--------|-----------|---------|
| 1 | 记忆召回非向量（索引文件+主题文件+grep） | 已有 memory_search(向量) | 保留向量，补轻量 MEMORY.md 索引+主题文件模式作兜底/降本 |
| 2 | 异步"睡眠式"记忆巩固（Auto Dream） | 已有 23:59 cron 审计 + heartbeat | 升级为空闲期后台子代理：读近期日记+transcripts→去重/替换过期/提炼→写回 |
| 3 | /init 式脚手架（子代理扫描+可审阅提案） | startup.sh 只验证不生成 | 补"项目指令自动生成"：子代理扫描→提案→确认写入 |
| 4 | SKILL.md 开放标准 | 已有 skills/ + SKILL.md ✅ | 对齐 open spec frontmatter 规范 |
| 5 | AGENTS.md override/fallback 机制 | 已有 AGENTS.md | 可补 AGENTS.override.md + fallback 语义 |
| 6 | 子代理独立持久记忆 | 子代理默认 isolated，只有 trace | 升级 memory/subagent_runs/ 为持久主题记忆 |
| 7 | 安全模型（per-action vs perimeter） | Sentinel before_tool_call 已做 per-action 拦截 ✅ | 论文认可此方向；评估是否加 ML 分类器（成本红线内） |

**红线提醒**：借鉴范围限"记忆层+脚手架+技能"，不触碰"改 system prompt/safety 规则"（论文 L4 Self-Modification 正是我们红线）。GEPA 类严禁再开发（7/21 Daryl 指令仍有效）。
