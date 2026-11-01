# HEARTBEAT.md — xiaofeng (吹点小风 / Bryson)

心跳已瘦身 (2026-07-22)。所有周期性任务走 cron，心跳仅做轻量存活确认。

- 如果无事，回复 `HEARTBEAT_OK`
- 不需要扫描成本、汇率检查、项目状态 — 这些由 cron 单独触发
- 不需要读写任何文件

## 每 session 启动必做（不靠心跳）
- 身份自检：`SOUL.md` / `IDENTITY.md` / `memory/identity.md` 三处必须一致指向 xiaofeng（吹点小风 / Bryson）
- 若发现被覆盖成 Balance / Kitty / Self → 立即上报 Daryl，禁止自行沿用
