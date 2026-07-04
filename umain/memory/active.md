# 当前活跃任务

> 最后更新: 2026-07-04 13:30 GMT+7

## 🟢 进行中
### 🔴 M2 Workflow可视化编辑器验收（当前）
- **状态**: Agent状态与任务模块 ✅，开始验收 Workflow 模块
- **版本**: v1.3.4（已 commit + tag）
- **隧道**: https://flood-villages-project-considerations.trycloudflare.com
- **本地**: localhost:8765

## 🔵 待办
### OPC看板v1.4
- 主次优先级视觉分层
- Bryson雅思陪练产物补全
- symlink重复清理

### Agent版本变更通知
- OPC看板Agent卡片增加「约定版本」字段
- 机制变更时自动通知对应Agent

### M2 剩余模块
- 成本仪表盘验收
- 沙箱任务验收

## ✅ 已完成
### 🔴 M2 Agent状态面板验收 (7/4)
- M2a WebSocket / M2b 飞书DM / M2c 实时推送全部完成 ✅
- Daryl 验收通过，commit v1.3.4

### OPC看板实时刷新功能
- 修复sidebar 5模块实时badge + 成本仪表盘session真实成本 ✅
- Agent状态面板任务自动同步（active.md→Dashboard） ✅

### Agent状态面板任务自动同步
- 解析各Agent的memory/active.md → Dashboard自动展示 ✅
- Xiaofeng active.md 已创建

### 隧道调试 & 验收准备 (7/2 晚)
- cloudflared临时隧道 + loca.lt双隧道就绪
- 问题根因: exec background进程在session切换时被SIGKILL
- 解决方案: nohup & disown完全脱离终端

### OPC看板Sidebar实时badge (7/2)
- 5模块各加实时摘要badge,每小时自动刷新

### OPC看板成本仪表盘实时化 (7/2)
- 数据源从agent_reports改为session estimatedCostUsd

### OPC看板v1.3.2产物模块 (6/29)
- 72条产物全部可预览,4 Agent workspace扫描正常
