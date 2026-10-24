# 成本管线修复复盘 — 2026-09-16

## A. 版本对照表（判定"最新版本"）

| 路径 | mtime | 是否权威 | 理由 |
|---|---|---|---|
| `~/.openclaw/workspace-balance/scripts/full_cost_scan.py` | 07-14 15:37 | ✅ 权威 | 唯一在用的扫描器，append-only 台账模式 |
| `~/.openclaw/workspace-balance/scripts/generate_cost_daily.py` | 07-19 23:52 | ✅ 权威 | 唯一在用的格式化器 |
| `~/WorkBuddy/Claw/opc-dashboard/data/cost_daily.json` | 08-22 23:45（刷新后 09-16） | ✅ 权威输出 | 看板 server.js 读此路径 |
| `~/opc-workspace/Kitty/opc-dashboard/data/cost_daily.json` | 08-04（符号链接） | ❌ 非独立 | 指向上面那个，是软链 |
| `~/opc-workspace/Kitty/.../cost_daily.json.bak_20260801` | 08-01 23:47 | ❌ 旧备份 | 历史快照，不用 |
| `~/.openclaw/xiaofeng_workspace/ubalance/scripts/*.py` | 07-22 09:59 | ❌ 快照副本 | 与 Balance 版内容完全一致（主 Agent 已逐字节核实） |

**结论：不存在比 Balance 版更新的管线。** Balance 版（07-14/07-19）就是最新权威版本。

## B. 根因确认

**无任何 launchd/cron 调度成本管线** → 这就是 cost_daily.json 停在 8/22 的根因。
- `crontab -l`：只有 watchdog.sh(5min)、audit-cron.sh(23:59)、ops_center(08:00)、生活提醒，均不跑成本扫描。
- `~/Library/LaunchAgents/`：无 cost 相关 plist。
- 台账 cost_ledger.jsonl 日期止于 08-26（此前由 Balance 每日 13:00 的 proj-update 会话手工触发，该会话 8/26 后停跑）。

## C. Token 单价调整（before/after）

| 字段 | flash 旧值 | flash 新值（官方 peak） | pro（未动） |
|---|---|---|---|
| input | 0.44 | **0.30** | 1.32 |
| output | 1.32 | **1.20** | 3.96 |
| cacheRead | 0.014 | **0.006** | 0.044 |
| cacheWrite | 0 | 0 | 0 |

- pro 档（1.32/3.96/0.044）已等于官方 peak 价，**未改动**。
- 已备份 `openclaw.json.bak_20260916-090331`，JSON 校验通过，check_workspaces.py = 0 FAIL。
- **未重启 Gateway**，未动其他 agent 配置。
- 其他硬编码单价（仅列出，未改）：
  - `~/.openclaw/workspace/model_selection/sync_tracker.py:17` — `deepseek-v4-flash: {input 0.14, cache_hit 0.0028, output 0.28}`（更老的旧价，属 model_selection 独立系统，不喂成本管线）
  - xiaofeng_workspace 的 openclaw.json / Bryson/openclaw.json — 无 deepseek cost 字段，无需同步。

## D. 刷新前后数字对比

| 指标 | 刷新前(8/22) | 刷新后(9/16) |
|---|---|---|
| 累计成本 | $175.0404 | **$177.0179** |
| 本月 | $49.2538 | **$0.5317** |
| 今日 | $9.8972 | **$0.1787** |
| 总调用 | 27,658 | **27,988**（新增134） |

刷新后 by_agent：Bryson $93.98 / Balance $45.81 / Kitty $21.40 / Self $15.82（累计）。
本月 by_agent：Kitty $0.305 / Bryson $0.116 / Balance $0.075 / Self $0.035。

**日成本近 7 天（有数据的天）**：08-23 $0.47 → 08-24 $0.009 → 08-25 $0.04 → 08-26 $0.63 →（空窗）→ 09-05 $0.07 → 09-15 $0.28 → 09-16 $0.18。

## E. ¥5.39 归因结论

**¥5.39（≈$0.75）余额下降不是本机 DeepSeek LLM 用量造成的。**
- 本机 9 月整月记录成本仅 **$0.53**（≈¥3.8），昨天 9-15 记录 **$0.28**（≈¥2）。
- 台账显示机器 9 月近乎闲置：仅 09-05(15次)/09-15(75次)/09-16(43次) 有调用，8-27~9-14 基本空窗。
- 单日 ¥5.39 降幅是昨日记录成本的 ~2.7 倍，是本机整月成本的 ~1.4 倍，量级对不上。
- 可能来源：同一 DeepSeek key 被其他设备/账号共用、DeepSeek 非 LLM 计费项、或其他服务。建议 Daryl 到 DeepSeek 控制台查 9-15 的账单明细（按模型/时间拆解）核对。

> 数据完整性 caveat：因管线长期未调度 + 会话文件 ~30 天轮转删除，8-27~9-14 若有被删前未扫描的用量会永久丢失；但活体 session 文件佐证机器确实大多时间闲置，量级差距仍过大，不足以解释 ¥5.39。

## F. 剩余风险与建议

1. **（强烈建议）把管线挂进 launchd 定时**，推荐 **每日 23:50**（赶在 23:59 audit cron 之前），跑 `full_cost_scan.py` + `generate_cost_daily.py` 两连。理由：append-only 台账的价值就在于"即使 session 被删成本仍在账"，间隔越短越不易漏；每日一次成本可忽略（纯本地扫描，无 LLM 调用）。
2. 看板侧 `refreshCostFromJsonl()` 每 30min 活扫 session 文件（只扫活文件、无台账持久化），与 Balance 台账口径不一致、会低估被删会话的成本；确认 `/api/costs` 已把 `loadBalanceCostDaily()`(server.js L1990) 当作权威源优先于活扫，否则需对齐。
3. flash 单价下调后，历史 flash 成本（$17.28 累计）是按旧高价(0.44/1.32)记账的，属于**高估**；但按"Daryl 07-14 指令：历史成本就是历史成本"，不予追溯调整。
4. 本次只改价格 + 跑管线，未删任何历史文件、未改台账数据、未动 cost_ledger.jsonl。
