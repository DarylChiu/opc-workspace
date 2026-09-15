# 事故记录 · 2026-09-15 凌晨 DeepSeek 突发扣费（¥10+）

**级别**: P1（资金消耗，未定位来源）
**发现**: Daryl 08:17 私聊，DeepSeek 控制台显示今日 ¥15.30 / 145 请求 / 52.5M tokens，柱状图峰值落在 00:00-08:00，疑似凌晨 4 点烧了约 ¥10。

## 排查结论（本地证据）

**本机 OpenClaw 在 09-14 22:09 → 09-15 08:17 期间完全空闲，零 LLM 调用。** 证据：

| 检查项 | 结果 |
|--------|------|
| Gateway 进程 | PID 5894，21:27 启动，跨夜存活，日志无 4am 事件，无 agent dispatch |
| 4 个 Agent session 文件 | 无任何文件 mtime 落在 03:00-06:00（全盘 find 02:00-06:30 = 0 个写入） |
| gateway cron | `openclaw cron list` = No cron jobs |
| crontab / launchd | 最近定时任务：23:59 审计、周日 21:00 bench；**3-5 点无任何任务** |
| 心跳 | `agents.defaults.heartbeat.every = 0m`（已停） |
| 后台任务/子代理 | task_runs 仅 1 条历史记录，subagents/runs.json 无新条目 |
| 备用 profile | `~/.openclaw-deepseek_official` 今日零活动 |

→ 扣费**不是 OpenClaw 调度链**发出的，走的是直连 `api.deepseek.com`（继承 DEEPSEEK_API_KEY）的旁路，或本机以外的设备/第三方滥用。

## 08:30 Daryl 提供控制台导出 CSV（按小时+模型）→ 关键突破

CSV 时间戳为 +07:00（与本地一致，08:00 那一行的 flash ¥0.32 正好对应今早这次对话，可信）。

| 时段(本地) | 模型 | 费用 CNY |
|---|---|---|
| 01:00–02:00 | flash | 0.596 |
| 03:00–04:00 | **pro** | 1.866 |
| 04:00–05:00 | flash | 0.001 |
| **04:00–05:00** | **pro** | **10.352** ← 元凶 |
| 05:00–06:00 | flash | 0.576 |
| 05:00–06:00 | **pro** | 1.918 |
| 08:00–09:00 | flash | 0.315 ← 今早对话 |
| 合计 | | ≈15.62 |

**结论升级**：凌晨烧的钱几乎全是 **deepseek-v4-pro**（¥14.1 / 15.6）。而本机 4 个 Agent 在 openclaw.json 里**全部钉死 deepseek-v4-flash**。本机唯一引用 v4-pro 的是开发/自进化脚本（`scripts/evolution/distill_patterns.py`、`classify_task.py`，直连 api.deepseek.com），且它们夜里没有运行痕迹。

## 附带发现

1. **Sentinel 插件处于 disabled**（配置仍在）→ 夜间降档（23-8 点）、exec≤6/write≤10 阈值**均未生效**，护栏形同虚设。
2. **2 个 cron 指向的脚本已不存在**（静默失败）：
   - `xiaofeng_workspace/scripts/compliance/audit-cron.sh` → No such file
   - `workspace/scripts/ops_center/opc_ops_center.sh` → No such file
3. 余额实测（API）：**¥32.96 CNY**（截图 ¥33.22，差值为排查消耗）。
4. 控制台时区按 **UTC+8**（沿用 9/5 事故结论）→ 图中 04:00 = 西贡 03:00。

## 待 Daryl 提供才能定案

- 控制台 **API keys 页面**：有几把 key、名字、各自的「最近使用时间」→ 是否有一把非本机持有的 key 在 04:00 被用过
- 是否有其它设备/应用（手机 App、别的电脑、VPS）共用该 key

## 08:32 Daryl 提供第二份 CSV（含 api_key_name / request_count / token 明细）→ 关键证据

**key 比对：CSV 中的 `sk-b1715…c4be` == 本机 `~/.openclaw/.env` 的 DEEPSEEK_API_KEY（head=sk-b1715 / tail=c4be / len=35）**，key 名 "OPE of Daryl"。同一把 key 还存在于 `auth/deepseek/api.key`、`auth/agents/xiaofeng/deepseek_bryson.json`。

### 逐小时请求明细（本地时间）

| 时段 | 模型 | 请求数 | 平均上下文/请求 | 输出 | 费用 |
|---|---|---|---|---|---|
| 01–02 | flash | 48 | ~147K（cache_hit 7.05M） | 95.5K | ¥0.60 |
| 03–04 | pro | 2 | ~205K（无缓存，冷启动） | 1.8K | ¥1.87 |
| 04–05 | flash | 1 | — | 303 | ¥0.001 |
| **04–05** | **pro** | **73** | **~449K（cache_hit 32.8M）** | 71K | **¥10.35** |
| 05–06 | flash | 6 | ~420K | 5.7K | ¥0.58 |
| 05–06 | pro | 15 | ~528K | 32.6K | ¥1.92 |
| 08–09 | flash | 31 | ~45K | 22.6K | ¥0.32 ← 今早本机对话 |

**请求数校验：48+2+1+73+6+15 = 145**，正好等于控制台截图里的「今日 145 请求」→ CSV 时间戳与归属可信（08:00 那 31 次是本机今早对话，在截图之后）。

### 指纹判定

- 单请求上下文 **400–530K tokens** → 与 **2026-07-05 僵尸 session 事故（385K 上下文反复心跳）** 同构：不是人类聊天，而是**超长会话被反复调用**。
- 同一小时内 **flash 与 pro 混用** → 多个 Agent 并行，且并非本机配置（本机 4 个 Agent 全钉死 flash）。
- 04–05 点 pro 档 73 次/小时 ≈ 1.2 次/分钟，持续一小时 → 稳定的 Agent 循环。

### 本机排除（再确认）

- 全 4 个 Agent 的 `sessions.json`：**自 09-14 以来只有今早 08:32 更新的那一条 Feishu 会话**，夜间零 session 活动。
- 无 1–6 点 cron/launchd；心跳 `every=0m`；无容器；paired 设备仅为 CLI/control-ui 客户端。

→ **扣费调用确实使用的是我们这把 key，但不是本机发出的。** 头号嫌疑：**另一台机器/另一个部署上用同一把 key 的 OpenClaw（旧配置：pro 默认 + 心跳开启）**；其次是 key 泄漏被外部使用。

## 处置结果（2026-09-15 08:43–09:00 完成）

Daryl 提供第二把既有 key `sk-9638…35cf`（非新建）。Kitty 全量切换完毕：

| 动作 | 结果 |
|---|---|
| 新 key 真实推理调用 | HTTP 200 ✓ |
| 本机 7 个文件 12 处替换（.env / auth.deepseek.api.key / xiaofeng deepseek_bryson.json / balance+self auth-profiles.json / WorkBuddy+opc-workspace 两份 Bryson/openclaw.json） | 全部带备份 `.bak_20260915-084341`，JSON 校验通过 ✓ |
| Gateway 重启 | 08:44:34 → 08:59:30（两次，第二次吃进 auth-profiles）✓ |
| 旧 key 删后复测 | balance 401 / chat 401 ✓ 已失效 |
| 新 key 复测 | chat 200 ✓ |
| 重启后日志鉴权错误 | 0 ✓ |

**Daryl 决策（2026-09-15 09:00）**：**Sentinel 与余额告警均不启用**（明确拒绝）。已按决定执行，未开启。风险已知并在案：凌晨 3 小时烧钱无人知晓，依赖人工看图发现。

**遗留观察点**：旧 key 已废 → 若凌晨那条旁路来源仍在跑，应开始报 401；若 Daryl 某设备/服务出现鉴权错误，即为泄漏源。备份文件仍含旧 key（已失效，无风险）。

## ⚠️ Kitty 操作失误（9/15 09:00-09:07）——已修复

- **现象**: Daryl 被重复的「✅ 热重启完成」消息骚扰 + Gateway 每 ~90 秒重启一次（共 31 轮）。
- **原因**: 为「重启后验证」使用 `launchctl submit -l com.opc.keyrotate2` 提交验证脚本 → 该 job 被 launchd 反复拉起（脚本尾部含 `openclaw gateway restart` + 发送 Feishu 消息）→ 形成重启循环。
- **修复**: `launchctl remove com.opc.keyrotate2` + pkill + 删除脚本；45 秒后复测：同一 PID（26336，09:05:42 起）、无新重启、无残留 job。
- **影响**: 仅通道瞬时断连 + 消息骚扰；**零 API 成本**（重启不发 LLM 调用）。
- **教训（机制）**: 一次性延迟动作**禁止用 `launchctl submit`**（不可控常驻语义）。正确做法：直接在当前对话下一轮做前置检查，或用带明确退出的一次性脚本 + 事后确认已移除；任何自建的延迟/常驻任务，交付前必须验证「运行后是否自动退出」。



## 重复模式（三次事故同一指纹）

| 日期 | 金额 | 当时本机 OpenClaw 状态 |
|---|---|---|
| 08-27 | ¥115+ | 停机（402 后充值被回放） |
| 09-05 事故（9/3 夜） | ¥36 | Gateway 停机（9/1 02:13 停 → 9/4 18:29 启） |
| 09-15 本次 | ¥15.6（pro ¥14） | Gateway 存活但零调用 |

→ 三次都发生在**本机 OpenClaw 静默时段**，且用我们默认不用的 pro 档/直连通道。凌晨 04:00 西贡 = 18:00-22:00 UTC（美区白天）→ 更像**账户 key 在外部被使用/滥用**，而非本机任务。

## 建议动作

- [ ] 控制台锁定后**立即轮换 key**，并为旁路脚本分配独立 key（历史教训 #3）
- [ ] 重新启用 Sentinel（或至少恢复夜间降档 + 阈值拦截）
- [ ] 恢复余额告警（余额 <10 元 DM），该建议在 7/5、8/25 两次事故中提出，至今未落地

*记录：忧郁小猫 | 2026-09-15*
