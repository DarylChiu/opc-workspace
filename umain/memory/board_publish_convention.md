# OPC 看板「产物与预览」发布约定（2026-10-07 与 Self 核对确认）

> 权威源：`/Users/zhaoyuzhao/WorkBuddy/Claw/opc-dashboard/server.js` 的 `AGENT_ARTIFACT_RULES`

## 各 Agent 产物目录规则（server.js 硬编码）

| Agent | priority（+13分，首位再+5） | exclude（命中即 -10） |
|-------|---------------------------|----------------------|
| kitty | chord-gesture, console, opc-dashboard, **reports**, roundtable | dashboard, opc-dashboard |
| xiaofeng | ielts_tutor, video_editor_mvp, video-analyzer, voice-mvp, **reports**, opc-dashboard | investor-pitch-phrases, skills, compliance |
| balance | 贷款材料自动化, 越南税金循环, **reports**, docs, _root | memory, scripts |
| self | ACCA-Knowledge-Network, 方法轮卡片, knowledge-network, project-summary, knowledge, **reports** | compliance, memory-system, **memory** |

## 约定结论（已与 Self 确认）

1. **发布位置 = `reports/`**：所有 Agent 的 `reports/` 都在 priority 白名单；`memory/` 在多数 Agent 的 exclude 里。**交付物想上「产物与预览」看板，必须放 `reports/`，不能放 `memory/`**。
   - 子目录模式：`reports/<项目名>/`（Balance 已有 `reports/balance/`，Self 用 `reports/FOC-VN/`）。project 分组 = 第一个非 skip 容器目录 = `reports`。
   - **无 INDEX.md 强制要求**：代码只特殊处理 `memory/INDEX.md`（score 28），`reports/` 下不需要 INDEX。命名无硬性规范，自描述命名即可（如 `FOC-VN-01-业务流程图-v0.5.md`）。

2. **多版本策略 = 看板只放当前有效版**：被对抗审查推翻的旧版（v0.1–v0.4）不放看板，避免互相矛盾的旧结论噪音 + 旧文件靠 mtime 新鲜度掉分/30天自动排除。
   - **版本链留痕靠 git，不靠看板**（AGENTS.md T0「产物=版本追溯」）：完整版本链留在 `memory/projects/` 的 git 历史里，看板只发布当前有效版 + 配套稿。

## 备注
- 30 天新鲜度硬截止（v1.7.0, Daryl 8/5）：mtime 超 30 天的产物直接从看板排除。
