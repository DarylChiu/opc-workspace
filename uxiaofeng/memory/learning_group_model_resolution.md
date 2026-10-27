# learning · 群会话模型解析（2026-09-15）

## 机制（不变）

OpenClaw 模型解析的实际行为（本机 2026.4.29 实测）：

| 会话类型 | 解析来源 | 本机结果 |
|---|---|---|
| 飞书私聊 | `agents.list[].model`（per-agent） | main/xiaofeng = pro，balance/self = flash |
| 飞书群聊 | `agents.defaults.model` | 全部 = flash |
| heartbeat / cron | per-agent 或 defaults | main heartbeat = pro，其余 flash |

- per-agent 的 `model` 覆盖**不作用于群会话**：群会话回落到 `agents.defaults.model`。
- 会话级 `/model` 覆盖（`session_status model=...`）是**逐会话**的，改私聊不会顺带改群会话。
- 校验口径：以 **session 记录（`agents/<id>/sessions/sessions.json` 的 `model` 字段）** 与 **每轮 `systemPromptReport.model`** 为准；`session_status` 卡片读的是配置解析值，可能显示 pro 而实际跑 flash。

## 本机现状（Daryl 2026-09-15 决策）

- **OPC 群（oc_7d71d54d…）只跑 `deepseek/deepseek-v4-flash`**，四个 Agent 一致。
- 已对四个群会话显式钉 flash，避免后续配置变动时漂移。
- 私聊维持 per-agent 配置（main/xiaofeng = pro）。

## 参考物指针（可变，勿存快照）

- 配置：`~/.openclaw/openclaw.json` → `agents.defaults.model`、`agents.list[].model`
- 会话状态：`~/.openclaw/agents/<id>/sessions/sessions.json`（字段 `model`、`systemPromptReport.model`）
- 决策来源：`memory/2026-09-15.md`（11:13 私聊改 pro；11:50 群聊定 flash）

## 踩坑记录

1. 不要凭 `session_status` 卡片回答「我用什么模型」——它可能显示配置值而非实跑值。
2. 问 Agent 自报模型时，容易出现「配置 ≠ 实跑」的口径冲突，先查 session 记录再下结论。
3. 群会话新建时机（配置变更后新建）不会自动继承 per-agent 覆盖，别假设「改了配置就全局生效」。
