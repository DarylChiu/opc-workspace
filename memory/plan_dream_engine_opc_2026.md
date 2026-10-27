# OPC 执行计划：Dream Engine（巩固引擎 + 封顶索引 + lesson→skill 三合一流水线）

> 2026-10-05 · Kitty · 承接 research_codex_claude_infra_deep_2026.md
> 状态: 已收敛为精简版（Daryl 拍板：不分工、不笨重、Kitty 一人做）
> P1 决策：①定时LLM放开全体Agent+四道闸token护栏 ②遗忘边界按建议锁死

## 核心认知：三样不是三个项目，是一条流水线的三段

```
原始记忆 (daily logs / transcripts / episodes / active_tasks)
        │
        ▼
  [巩固引擎 Gap1]  ── 有损压缩：去重 / 替换过期 / 提炼 / 遗忘
        │
        ├──► [封顶索引 Gap2]  始终加载的精炼索引 (≤200行)
        └──► [lesson→skill Gap3] 可加载的能力 (SKILL.md)
```

所以执行上要按依赖顺序推进，但用"手工 MVP"把价值前置。

## 执行顺序 + 理由

- **Phase 0（本周，零代码）**：手写封顶索引"形状"。理由：先确立"精炼索引长什么样"+验收标准，零成本证明可行性，避免引擎建完才发现格式不对。
- **Phase 1（核心建设）**：建巩固引擎。理由：Gap2/Gap3 都依赖引擎产出，必须先行。
- **Phase 2（封顶索引自动化）**：Phase 0 手工索引改由引擎产出。
- **Phase 3（lesson→skill 闭环）**：引擎开始产出"重复教训"后，接蒸馏步骤。

## 精简版（Daryl 拍板：不分工、不笨重、Kitty 一人做）

三样收敛成一个轻量闭环，不建"引擎"：
- **Gap2 封顶索引** = 一个文件 `memory/INDEX.md`(≤200行)，手写+巩固输出维护。零代码。
- **Gap1 巩固** = 一个脚本 `scripts/consolidate.sh`(~50行)，非触发/staging/apply 系统。
- **Gap3 lesson→skill** = 一个习惯：重复教训手动蒸馏成 SKILL.md，不建 pipeline。

## 里程碑（边界 / 交付物 / 验收标准 / 决策权限）

| 阶段 | 交付物 | 验收标准 | 决策权限 |
|------|--------|---------|---------|
| P0 手工 MVP | `memory/INDEX.md`(≤200行)样例 | Daryl 一眼认"这就是精炼索引" | P2格式 / P1结构方向 |
| P1 巩固引擎 | 触发+输入+巩固调用+staging+diff+apply | dry-run 产出 staging diff，Daryl 审阅通过 | P1(遗忘边界+成本) / P2(实现) |
| P2 索引自动化 | 引擎自动重建 INDEX.md + 去重 episodes | 索引反映最新态，源记录完整 | P2 |
| P3 lesson→skill | 蒸馏规则 + skill 生成 pipeline + 注册 | 一个真实 lesson 蒸馏成 skill 并被加载 | P2 |

## P1 决策结果（Daryl 2026-10-05 拍板）

1. **定时 LLM 放开全体 Agent** + 四道闸 token 护栏：
   - 触发闸：无新增记忆不跑（增量触发），每日 ≤1 次
   - 输入闸：只喂上次巩固后的新增，倒序截断，硬顶 **80K tokens**（10/5 Daryl 拍板：原 8K 提 10 倍）
   - 输出闸：max_tokens **20K**（10/5 提 10 倍）
   - 预算闸：周预算 **≤$0.5**（10/5 Daryl 确认：原 $0.05 提 10 倍）
   - 模型：deepseek-v4-flash（单次跑满 ≈ $0.062）
   - ⏸️ 沙箱测试暂缓（Daryl 指令：先清掉 Bryson/Balance 手中项目再上，防他们在沙箱操作丢进度）
   - 强制方式：一个 ~30 行 wrapper `scripts/llm_budget.sh`（截断输入+设max_tokens+记成本+超预算拒绝），全体 Agent 定时任务共用
2. **遗忘边界（按建议锁死）**：只碰衍生记忆(摘要/去重后 episodes)；源记录(日志/git/SOUL-USER-MEMORY 核心)永不删、只归档；"新增/去重"可自动生效，"删除/替换"永远强制人审阅。

## 红线自查
- 巩固输出全部进 staging，原文件不动，人审阅后 apply
- 遗忘只作用于可再生的衍生记忆，源记录只归档不删（对齐 SOUL.md T0 数字资产保护）
- 不碰 system prompt / safety 规则 / GEPA
