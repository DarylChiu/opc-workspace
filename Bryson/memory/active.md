# 当前活跃任务 (中期记忆 — 每次session加载)

> 最后更新: 2026-06-16 23:59

## 🔴 明日重点
### 视频分析交互Workflow — MVP 工作流融合
- **目标**: 将「视频分析MVP」的完整 pipeline 融入 Workflow
- **关键缺失**: Vision API 逐帧分析、对白时间线增强、剪辑节奏可视化、导演风格6维度
- **参考**: video_analyzer_app/DESIGN_REFERENCE.md 
- **MVP 参考报告**: ~/Desktop/7597261902088021622_v3_20260610_211500.md
- **前置**: 需解决 Vision API 可用性（Gemini/DeepSeek VL2/OpenAI Vision）

## 🟢 已交付（运行观察期 → 6月13日周日验收）
### 1. 记忆系统重构 ✅
- **完成**: 2026-06-06 14:15
- **成果**: 分层架构(L0-L4)、MEMORY.md 273→24行、31个日记归档

### 2. Agent间通信方案 ✅
- **完成**: 2026-06-06 14:45
- **成果**: 通信协议v2 + 双轨制 + 双向联调通过

### 3. 模型分级调用 ✅
- **完成**: 2026-06-06 15:28
- **规则**: Sonnet分类 → Opus/Sonnet/Flash三级执行
- **详见**: memory/model-routing.md

### 4. 成本追踪方案 ✅
- **完成**: 2026-06-06 14:45
- **工具**: tracker.sh (task-start/task-end/daily/report)

### 5. API Key独立化 ✅
- **完成**: 2026-06-06 14:43
- **新Key**: ...37c7 (名称: "吹点小风")

### 6. 工作流规范落地 ✅
- **完成**: 2026-06-06 15:53
- **内容**: P0-P3决策矩阵 + 里程碑驱动 + 汇报机制
- **详见**: memory/workflow-rules.md

## 🟡 待启动（等Daryl确认M2）
### OPC总控看板 — M1已完成 ✅ M2待确认
- **M1成果**: /workspace/opc_dashboard/ (Kitty开发，819行index.html + server.py)
- **M1模块**: HTML骨架、任务看板(拖拽)、产物追踪、预览面板、项目进度+风险、Agent状态、沙箱占位、server.py
- **M2分工（已对齐）**:
  - 小风: Cloudflare Tunnel + 启动脚本优化(nohup) + 沙箱面板完善
  - Kitty: 代码review+bug修复 + 二期技术方案评估
- **暂缓**: 语音指令(STT)、公网预览完整版、MCP/Skills面板

## 🟡 进行中
### 7. 视频分析MVP 🎬
- **启动**: 2026-06-14
- **内容**: 抖音/B站短片深度影像分析（逐帧镜头语言、叙事结构、色彩光线）
- **产物**: 飞书云文档进度表（R7vTdTcZkoZLk0xxbDrcinTDnhb）+ 分幕分析文件（vision_batch_01~03.md）
- **已分析**: ①《安心便服出行》②《90后家长上门道歉》③《身份反转·迷途羔羊》
- **待分析**: ④庞大辉
- **Workflow**: vision_batch 分批次输出，每批覆盖一个叙事段落的完整帧

### 8. IELTS陪练重构 🔄
- **状态**: 深度诊断完成(2026-06-15)，方向确认偏了
- **根因**: 当前是STT→LLM→TTS链式批处理(7-17s延迟)，不是实时对话
- **推荐方案**: OpenAI Realtime API (语音→语音, <1s) + DeepSeek异步评估
- **成本预估**: ~$270/月(OpenAI) / ~¥60-90/月(Qwen备选) / 零成本(CF自建备选)
- **等Daryl确认**: ①质量vs成本 ②交付节奏 ③商业英语优先级 ④API Key
- **报告**: reports/ielts_diagnostic_2026-06-15.md

## 🔵 待办（非紧急）
- 硬件语音助手(MCU)开发 — Daryl后续需求
- 雅思口语水平评估（占比将下降）
- ngrok 备用隧道安装

## ✅ 已完成（本周）
- 模型升级 DeepSeek R1 → Claude Opus 4.6
- 记忆系统诊断报告

## 🟢 进行中
### 9. 视频分析交互Workflow 🎬
- **启动**: 2026-06-16
- **内容**: 视频深度分析交互式Web应用，融合 MVP 分析架构
- **成果**: 
  - 三栏布局（视频+对白/分析面板/标记管理）
  - DeepSeek V4 Pro × 5 并行分析管线（$0.0025/次）
  - MVP 风格分析面板：总览/脚本解析/复刻模板/镜头&声音/评分
  - 标记系统（hook/金句/转折点 + 保存/导出）
  - 素材库侧边栏（localStorage 持久化）
  - 竖屏/横屏自适应 + 视频↔对白双向联动
- **地址**: https://unwhispering-imani-digitately.ngrok-free.dev (端口8777)
- **待补**: Vision API 接入（逐帧镜头分析）、对白时间线视图
- **产物**: video_analyzer_app/ (index.html + server.py + prompts.py)
- **设计参考**: video_analyzer_app/DESIGN_REFERENCE.md（Daryl需求归档）
- **状态**: ✅ 基础功能完成，等待 Daryl 确定 MVP 优质板块迁移方向
