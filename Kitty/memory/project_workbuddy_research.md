# Project: WorkBuddy深度调研

## 日期: 2026-06-05

### 核心发现
- WorkBuddy = 腾讯CodeBuddy的桌面AI Agent
- 架构: Electron + CodeBuddy CLI (类Claude Code)
- 默认模型: DeepSeek-V4-Pro
- 本地数据库: SQLite (workbuddy.db)

### WorkBuddy优势
1. 可视化Electron GUI
2. artifact-index自动追踪产物
3. CloudStudio Deploy一键预览
4. 60+官方plugins生态
5. sandbox-cli沙箱隔离
6. connector-proxy统一MCP管理

### OpenClaw优势
1. 多渠道通信（飞书/Telegram/Signal/Discord）
2. 24/7后台守护进程
3. 心跳机制主动检查
4. 跨Agent通信 sessions_spawn/sessions_send
5. Cloudflare生态深度集成

### Daryl的真实需求
把WorkBuddy的"快速落地单项目"能力移植到OpenClaw：
- 界面交互（HTML/localhost + Cloudflare Tunnel）
- 产物交付预览
- 技能快速调用
