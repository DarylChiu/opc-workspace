# Active Tasks
Last updated: 2026-06-24 21:15 GMT+7

## 🔴 P0 紧急

### OPC看板 M2 Agent状态面板 — 等待合入8765生产环境
- **状态**: ⏸️ 等待 Daryl 提供 8765 server.js 路径
- **产出**: M2 改动已实现于 sandbox (`/Users/zhaoyuzhao/WorkBuddy/Claw/opc-dashboard/`, commit de52bd2)
- **待做**: 找到 8765 server → 合入 M2 改动 → 更新前端 → 给 Daryl 隧道验收
- **阻塞**: Daryl 身体不适，明天继续

### OPC看板 Workflow编辑器 - 渲染问题
- **状态**: ⏸️ 等待Daryl实测普通script方案
- **问题**: Workflow模块在Daryl浏览器中白屏不渲染
- **当前部署**: 普通script标签版（UMD React + 动态import ReactFlow）

## 🟡 基建合规

### 隧道状态
- 8765(OPC) → pdas-highways-stud-observer.trycloudflare.com ✅
- 8777(视频分析) → clinic-fellow-heavy-ancient.trycloudflare.com ✅

## 🟡 开发中

### OPC看板交互系统
- **Daryl 2026-06-24 决策**：核心项目，不用沙箱，直接在 8765 上迭代
- 大版本做好 git commit
- 沙箱留给后续 Agent 执行类项目

## 🟡 待规划

### GLM 5.2 测试 & 独立Agent部署
- **状态**: ⏳ Daryl 自行安排测试时间

## 🟢 Recently Completed
- 基建合规审计汇报 (2026-06-14)
- 生活助手Cron验证通过 (2026-06-16)
- OPC看板M2基础开发 (2026-06-17)
- M2 Agent四态模型方案 (2026-06-24)
