# 当前活跃任务

> 最后更新: 2026-07-06 16:55 GMT+7

## 🟢 运维
### OPC Dashboard v1.5 — 运行中
- **地址**: http://localhost:8765
- **隧道**: https://background-completion-roger-charlotte.trycloudflare.com
- **管理**: `cd /Users/zhaoyuzhao/WorkBuddy/Claw/opc-dashboard && bash manage.sh {start|stop|restart|status|logs}`

## ✅ 已完成
### 记忆系统v3 — project文件开发 (7/6)
- 模板+API+Cron 全部完成 ✅
- project_main/xiaofeng/Balance/Self.md 创建 ✅
- GET /api/projects/milestones 上线 ✅
- Agent 群内通知已发送 ✅

### OPC看板持久化修复 (7/6)
- Agent 状态面板：30s→30min 刷新 + 磁盘持久化 ✅
- 成本仪表盘：启动加载快照 + 过期自动刷新 ✅
- 任务数据源：CLI→active.md ✅

### OPC看板 v1.4 (7/5)
- 主次优先级视觉分层 ✅
- Bryson 雅思陪练产物补全 ✅
- symlink 重复清理 ✅

### M2 成本仪表盘验收 (7/5)
- 柱状图+饼图布局、字体对比度 ✅
- DeepSeek V4 Pro 定价修正 ✅

### M2 Workflow可视化编辑器验收 (7/5)
- 交互协议 v1.0 ✅

### M2 Agent状态面板验收 (7/4)
- WebSocket + 飞书DM + 实时推送 ✅

## 🔵 待办
### Agent版本变更通知
- OPC看板Agent卡片增加「约定版本」字段
- 机制变更时自动通知对应Agent

### Crontab 手动安装
- 记忆系统v3 cron 被系统拦截，需 Daryl 手动执行:
  `(crontab -l; echo '0 7,13,19 * * * bash ~/.openclaw/workspace/scripts/projects/cron_notify_update.sh >> /tmp/project_cron.log 2>&1') | crontab -`
