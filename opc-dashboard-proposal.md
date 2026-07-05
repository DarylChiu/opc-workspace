# OPC of Daryl Chiu — 总控看板HTML开发方案

> 作者：小风(Bryson) | 日期：2026-06-06
> 基于Kitty的Workbuddy调研 + 小风的语音交互能力

## 1. 产品定位

**对标 WorkBuddy**，但运行在 OpenClaw 生态内：
- WorkBuddy = 腾讯的桌面AI Agent（Electron GUI + 产物追踪 + 一键部署）
- OPC Dashboard = OpenClaw的Web版总控台（HTML + 语音指令 + 多Agent协调）

**核心差异化**：WorkBuddy是单机单Agent；我们是**多Agent + 多渠道 + 24/7守护**

## 2. 功能模块

### 2.1 📋 任务看板
- 看板视图（待办/进行中/完成）
- 每个任务卡片显示：负责Agent、预算、实际成本、进度
- Daryl可拖拽调整优先级
- **参考WorkBuddy**: artifact-index产物追踪思路 → 每个任务自动记录产出文件列表

### 2.2 🎤 语音指令入口（小风核心贡献）
- **已有能力**：Bryson语音交互MVP（录音→Google Cloud STT→处理→TTS反馈）
- **集成方式**：
  1. HTML看板上嵌入"语音指令"按钮
  2. 用户点击录音 → 浏览器MediaRecorder API捕获音频
  3. 音频发送到本地FastAPI后端 → Google Cloud STT转文字
  4. 文字指令通过OpenClaw Gateway API → 发送到飞书群 → Agent执行
  5. 执行结果回显到看板
- **技术栈**：MediaRecorder API + FastAPI + Google Cloud STT + OpenClaw Gateway
- **成本**：STT成本极低（之前测试$0.07-$0.19/7分钟，远低于免费额度）

### 2.3 💰 成本仪表盘（Daryl重点要求）
- **实时数据源**：OpenClaw的usage tracking（每条消息都有token/cost记录）
- **展示内容**：
  - 每个任务的预算 vs 实际API调用成本
  - Token使用量（input/output/cache）
  - 金额明细（按模型、按Agent、按任务）
  - 预算使用进度条 + 超预算预警
- **审计功能**：任务完成后自动生成成本报告，超预算时诊断原因

### 2.4 🤖 Agent状态面板
- **数据源**：OpenClaw `sessions_list` 真实数据（替代现有dashboard的模拟数据）
- **展示**：
  - Agent在线状态、最后活跃时间
  - 当前正在处理的任务
  - 模型信息、token使用量
  - 健康检查结果

### 2.5 📊 项目进度
- 里程碑时间线
- 进度百分比 + 燃尽图
- 风险评估面板
- **参考WorkBuddy**: preview_url即时预览 → 每个产物生成后可直接在看板内预览

## 3. 技术架构

```
┌────────────────────────────────────────────┐
│              OPC Dashboard (HTML)           │
│  ┌─────────┬──────────┬──────────┬───────┐ │
│  │ 任务看板 │ 语音指令 │ 成本仪表盘│Agent状态│ │
│  └────┬────┴────┬─────┴────┬─────┴───┬───┘ │
└───────┼─────────┼──────────┼─────────┼─────┘
        │         │          │         │
   ┌────▼────┐ ┌──▼───┐ ┌───▼──┐ ┌───▼────┐
   │本地JSON │ │STT   │ │Usage │ │Sessions│
   │文件     │ │Server│ │Track │ │API     │
   └─────────┘ └──────┘ └──────┘ └────────┘
        │         │          │         │
   ┌────▼─────────▼──────────▼─────────▼────┐
   │         OpenClaw Gateway (localhost)     │
   └────────────────────────────────────────┘
        │
   ┌────▼────┐
   │Cloudflare│  ← 外网访问（Tunnel/Pages）
   │Tunnel   │
   └─────────┘
```

### 部署方式
- **本地开发**：`localhost:8083`（与语音MVP共享端口方案）
- **外网访问**：Cloudflare Tunnel 或 ngrok（参考WorkBuddy的CloudStudio Deploy思路）
- **替代方案**：直接部署到 Cloudflare Pages（静态HTML + Workers API代理）

## 4. 小风特有贡献点

| 能力 | 来源 | 对看板的价值 |
|------|------|-------------|
| 语音转文字(STT) | Bryson MVP | 语音指令入口 |
| TTS语音反馈 | Google TTS | 执行结果语音播报 |
| FastAPI后端 | MVP架构 | 统一API服务层 |
| 单端口内嵌HTML | MVP经验 | 简化部署 |
| ngrok/Tunnel经验 | 4月踩坑 | 外网访问方案 |

## 5. 与Kitty分工建议

| 模块 | 建议负责 | 原因 |
|------|---------|------|
| 任务看板 | Kitty | 她有现成的看板模板和数据结构 |
| 语音指令 | 小风 | 已有STT/TTS全套能力 |
| 成本仪表盘 | Kitty（主）+ 小风（辅）| Daryl让Kitty重构成本方案 |
| Agent状态 | 小风 | 熟悉sessions API |
| 项目进度 | Kitty | 她有现成的看板方案文档 |
| 部署/Tunnel | 小风 | 有ngrok和Tunnel经验 |

## 6. 预算估算

| 阶段 | 内容 | 预估成本 |
|------|------|---------|
| 方案设计 | 本文档 + 技术调研 | ~$0.5 |
| HTML骨架 | 基础界面 + 路由 | ~$1.0 |
| 语音模块 | STT集成到看板 | ~$1.5 |
| 成本追踪 | 数据接入 + 可视化 | ~$1.0 |
| Agent面板 | sessions API接入 | ~$0.5 |
| 联调部署 | Tunnel + 测试 | ~$0.5 |
| **总计** | | **~$5.0** |

待Daryl确认后启动。
