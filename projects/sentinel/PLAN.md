# Sentinel · P0-P3 合规哨兵 — 开发计划

> 项目命名：Sentinel（哨兵）
> 目标：通过 OpenClaw Plugin Hook 实现 P0-P3 决策矩阵的系统级强制执行
> M1 只做"系统性强制 + 事前阻断"，试运行 1 周

## 架构总览

```
Agent session → before_tool_call hook 拦截
    ├─ 检查 session pre-op 记录（无记录 → block）
    ├─ 路径黑名单匹配 → 自动升级判定级别
    ├─ 累积操作阈值检查 → 自动升级判定级别
    ├─ P0 操作 → block + audit log + DM 通知（不等待）
    ├─ P1 操作 → requireApproval + 30min 超时降级为 P2
    ├─ P2/P3 → 放行 + audit log
    └─ 异常 → 降级为 P1
```

## M1 · 系统强制 + 事前阻断 (~8h)

### 1.1 Plugin 骨架 (1h)
- `openclaw.plugin.json` 清单
- `index.ts` plugin entry + `definePluginEntry`
- config schema（路径黑名单、阈值、超时等可配置）

### 1.2 规则引擎 (2h)
- P0-P3 判定规则（路径黑名单 + 操作模式匹配）
- 累积阈值追踪（per-session counter）
- 路径敏感性矩阵

### 1.3 before_tool_call Hook (2h)
- `write`/`edit` 拦截：路径匹配 → 判定升级
- `exec` 拦截：危险命令模式检测（rm -rf / force push 等）
- P0 block + P1 requireApproval
- 降级策略：夜间自动降级、超时降级

### 1.4 Audit 日志 + 通知 (1h)
- 结构化 audit log（JSONL）
- P0/P1 事件飞书 DM 通知
- 每日汇总（23:59 cron）

### 1.5 部署 + 测试 (1h)
- 本地 Gateway 测试
- 模拟所有 P0-P3 场景
- 路径匹配测试

### 1.6 配套更新 (1h)
- `scripts/compliance/pre-op.sh` 对齐新边界
- `AGENTS.md` 写入强制规则
- `memory/active.md` 更新

## M2 · 验证 + 回滚（试运行 1 周后，按需）

### 2.1 独立 Verifier
- 产出→验证→失败→自愈 or 升级

### 2.2 Checkpoints/回滚
- 关键操作前自动 snapshot
- /rewind 能力

### 2.3 合规仪表板
- pre-op 执行率、阻断率、误报率
- OPC 看板接入

## 🎯 试运行指标

| 指标 | 目标 |
|------|------|
| 合规覆盖 | 100% session 有 pre-op 记录 |
| 误报率 | P0/P1 升级 false positive <30% |
| 漏报率 | 0 次遗漏的"本应 P1"操作 |
| Daryl 打扰 | 日均 <5 次 P1 确认 |
| 零事故 | 0 次 Agent 执行 P0 操作 |
