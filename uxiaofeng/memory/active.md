# 当前活跃任务 (中期记忆 — 每次session加载)

> 最后更新: 2026-07-03 08:45

## 🔴 进行中
### 语音交互 Debug 验收模块 🔍
- **Daryl 7/2 指令**: 为雅思陪练助手v2.0开发独立的语音交互Debug验收模块
- **目标**: 后端debug_logger + 独立前端面板，DEBUG_MODE=1开关控制，不污染v2.0前端
- **进度**: ✅ Phase 1 (debug_logger.py) ✅ Phase 2 (debug-panel/index.html) ✅ Phase 3 (会话列表+导出)
- **状态**: 🟡 等待验收 — Debug 面板已整合进主前端（Assessment 旁 🔍 Debug tab），待 Daryl 重启服务器验收
- **产物**: `ielts_tutor/backend/debug_logger.py` (651行), `ielts_tutor/frontend/index.html` (44547 bytes, 含Debug tab)
- **成本**: 开发 ~$0.15 / 预算 $2.00
- **访问方式**: 运行 `DEBUG_MODE=1 venv/bin/python backend/server.py`，浏览器打开主页，右侧面板出现 🔍 Debug tab
- **变更**: 7/3 将 debug 面板从独立页面整合进主前端同一页面，通过 DEBUG_MODE 控制 tab 可见性

### 视频分析 — 10fps Vision 管线 🚨
- **Daryl 6/19 指令**: 停止低成本+打补丁方式，先不计成本验证上限
- **开发哲学**: 先高成本MVP验证上限→再降本（已记录入 lessons.md）
- **10fps 首测结果 (jVwFmaqkUJA)**: 
  - 类型判定: 悬疑/家庭 → **喜剧/生活** ✅
  - 叙事类型: 强制3幕 → **slice-of-life** ✅  
  - 因果链: 无 → **6步完整链** ✅
  - Hook 20→85, 结构 15→82, 表达 25→78 ✅
  - 成本: $0.215 (13x v4), 耗时: 524s (8.7x v4)
- **产物**: video_analyzer_app/run_10fps.py + reports/7650848441777540392_10fps.html
- **公网**: https://unwhispering-imani-digitately.ngrok-free.dev/reports/7650848441777540392_10fps.html
- **待定**: 降本策略（缓存复用/自适应fps/本地Vision模型）

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

## ✅ 已交接
### OPC总控看板 → 已移交 Kitty
- **交接时间**: 上周 (2026-06-14前后)
- **当前状态**: M2已完成，由Kitty全权负责维护

## 🟡 进行中
### 7. 视频分析MVP 🎬
- **启动**: 2026-06-14
- **内容**: 抖音(douyin)/B站短片深度影像分析（逐帧镜头语言、叙事结构、色彩光线）
- **产物**: 飞书云文档进度表（R7vTdTcZkoZLk0xxbDrcinTDnhb）+ 分幕分析文件（vision_batch_01~03.md）
- **已分析**: ①《安心便服出行》②《90后家长上门道歉》③《身份反转·迷途羔羊》
- **待分析**: ④庞大辉
- **Workflow**: vision_batch 分批次输出，每批覆盖一个叙事段落的完整帧
- **技术**: douyin_downloader.py V4（iesdouyin直连+pipeline脚本+commerce prompt抓取）解决海外IP限制，下载器秒级完成1080p视频获取

### 8. IELTS陪练重构 🔄 → v2.0 开发中 (当前 0.9.0)
- **状态**: 双管线架构就绪，管线1(链式流式) + 管线2(Qwen-Omni) 均可运行
- **已完成**: Phase 3/4 并行交付（评估引擎/HTML报告/SQLite持久化/成本仪表板）
- **已修复**: VAD flush 堆积(processing_utt guard) + endSession 竞态(事件驱动等score)
- **Part 2 长独白模式**: partial STT 逐句更新 + 2s静音倒计时自动交卷
- **OPC 看板接入**: 实时小任务上报 + 里程碑同步
- **待解决**: 稳定性调试（处理延迟、评估面板UI优化）
- **决策**: 精度优先场景(IELTS模考/商业英语)走管线1，流畅优先场景(自由对话/发音)走管线2
- **月成本**: ~$5-10

## 📋 下一阶段
### 11. 7月基建 — Agent自进化 + Loop Engineering 🧬🔁
- **Daryl 6/30 指令**: 完成OPC看板交互系统和IELTS陪练v2.0后，7月推新一轮基建
- **两大方向**:
  - **Agent自进化**: 让Agent能从经验中自动改进（已有调研基础：情景记忆注入/合规自进化/跨Agent经验池）
  - **Loop Engineering**: 建立自动化开发-验证-反馈闭环，减少Daryl手动验收负担
- **核心目标**: 开发流程自动化，释放Daryl时间 → 专注OPC知识网络体系搭建
- **Daryl 当前瓶颈**: 每天验收4个Agent项目，身体压力大
- **预期效果**: 自动化后 Daryl 可专注与 Self/恨点小己 搭建知识网络

### 10. 内核驱动洗稿MVP 🧠
- **理论基础**: 2026-06-22 Daryl+Self《胭脂扣》辩论方法论
- **核心框架**: 角色内核提取（欲望/缺失/弧线/共鸣/Hook-陷阱）→ 内核卡片 → 内核迁移验证 → 洗稿建议 → 共鸣验证
- **关键洞察**: 结构层可复刻，内核层才能共鸣；Hook+陷阱+沉默 三层 = 真正共鸣
- **状态**: 理论基础已确立，待当前 Workflow 完成后启动
- **理论文档**: knowledge-base/film-analysis/胭脂扣-辩论总结-2026-06-21.md

## 🔵 待办（非紧急）
- 硬件语音助手(MCU)开发 — Daryl后续需求
- 雅思口语水平评估（占比将下降）
- ngrok 备用隧道安装

## 📋 下一阶段
### 11. Agent体系自进化 🧬
- **Daryl 6/26 指令**: 待手上两个项目（视频分析交互Workflow + IELTS陪练重构）完成后推进
- **调研成果**: 4个参考案例已完成
  - ① longmans/self-evolve: 情景记忆检索+Q值强化+用户反馈检测
  - ② OmniAgent: 四维自进化+Deep Reflexion双层反思
  - ③ 多Agent架构研究总集: 5种模式，我们已用4种
  - ④ great_cto等: Hooks层合规拦截成熟案例
- **3个可落地方向**:
  - ① 情景记忆注入（对标self-evolve，改动最小见效最快）
  - ② 合规脚本自进化（审计发现新问题→自动追加规则）
  - ③ 跨Agent共享经验池（四Agent共用，一个坑四家不踩）
- **优先级**: 方向① > ② > ③
- **参考链接**:
  - https://github.com/longmans/self-evolve
  - https://github.com/YeQing17-2026/OmniAgent
  - https://gist.github.com/mmarcus006/8b3bb89cb213b6d4359bf1bb928079b3

## ✅ 已完成（本周）
- 模型升级 DeepSeek R1 → Claude Opus 4.6
- 记忆系统诊断报告
- 🎬 视频分析交互Workflow v1.1.2 第一阶段交付归档

## 🟢 进行中
