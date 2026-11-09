# 事故报告 · M4c「OPC机制约定版本更新」刷屏（2026-11-09）

**等级** P2（扰民级，无数据损失） · **处理人** 忧郁小猫 · **结案** 2026-11-09 22:5x

## 现象
18:56–22:13，Daryl 私聊被「🔧 OPC机制约定版本更新：你的约定版本已从 — 变更为 v1.0」刷屏 2000+ 条。

## 根因（实证）
| # | 环节 | 证据 |
|---|---|---|
| 1 | **通知消费失败 → 永久重发**。server 处理通知的方式是 rename 到 `notifications/processed/`，而该目录不存在 → ENOENT → 文件留在原地 → 下一轮再发 | 日志 `Notify err: ENOENT ... rename ... processed/` |
| 2 | 实测发送量 9412 条 = 4 agent × 2353 | `grep -c "DM sent to" /tmp/opc-dashboard.log` |
| 3 | 18:56:40 生成 4 条通知，`oldVersion: null`（状态被重置） | `data/notifications/*.json` |
| 4 | M4c 设计缺陷：`null` 当变更 + 无去重 + 无单轮上限 | `memory/archive/2026-08-07.md:31`（commit 09e38ea） |
| 5 | 放大：源码被删但 server 进程存活，crontab watchdog 仍在跑 | xiaofeng session 39bd462c |

## 处置
- ✅ 建 `data/notifications/processed/`
- ✅ 4 条残留通知移出 → `backups/notif_drain_20261109/`
- ✅ 验证死循环停止（日志 delta=0）
- ⚠️ 遗留：crontab `*/5 watchdog.sh` 指向已删脚本，macOS `crontab` 写操作挂起，需 sudo/launchd 处理

## 修复清单（若看板重装）
1. `oldVersion == null` → 视为初始化，不推送
2. 发送前查 `processed/`，同名已处理即跳过
3. 单轮发送上限（如 ≤ 4 条），超限熔断并告警
4. 启动时先 `mkdir -p processed`，失败即拒绝启动通知模块
