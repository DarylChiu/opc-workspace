# 当前活跃任务 (中期记忆 — 每次session加载)

> 最后更新: 2026-08-15 17:30（8/15 四个交付：费率更新/FT记忆/题库/用户系统 P1）

## 🟢 进行中
### M2 剪辑MVP 试点（8/6 开工 · Kitty 下发）🟢
- **8/6**: Daryl 拍板 M2 试点 = 剪辑MVP（决策自主环），wf01-wf05 冻结为 v4.0 基线（2 必改已核验落实）
- 30% 节点完成：交互方案定稿 + 账本记录；进行中：前端 v4.0 交互版开发（60% 节点预估 8-12h 后）


### 视频自动化剪辑 MVP（video-editor-mvp）🟢 v3.0 重构完成（7/25）
- **v3.0 重构**: 🟡 M0-M5 全模块完成，Daryl 已开始交互（7/28）
  - ✅ BGM 结构: Hooktheory 方案（Birds of a Feather · 8乐句 + 12个8bar单元）
  - ✅ 数据层: SQLite song_lib + phrase_lib + 8bar_units
  - ✅ API: 模块化（api/bgm scan asr emotion match）+ server.py v3.0
  - ✅ 前端: 5节点 pipeline 全可视化 · OPC Design System
  - ✅ 输出: ffmpeg 渲染 → Toshiba HDD → Syncthing → Tab S8 验收
  - ✅ 服务: localhost:8768 / frontend/index.html ~400行
  - ✅ **7/28 修复**: 前端 API 路径从 localhost:8768 改为相对路径，隧道可正常访问
  - 🔗 旧隧道: `coral-katie-senator-urw` (可能已掉线)
  - 🚇 **最新隧道 (8/3)**: `https://freebsd-present-rome-modes.trycloudflare.com/frontend/index.html`（旧地址 synthesis-ent-hawaii-booth 已过期）
  - ✅ **BGM节点v2 完成** (7/30): 歌曲卡片/音频播放器/乐句播放+和弦弹窗/ffmpeg乐句连接
  - ⏳ 待验证: Gemini 场景检测 + Emotion 三层漏斗 + ffmpeg 渲染（需素材+API Key）
  - ⏳ Daryl 7/30指令：先不动，等他把剩余模块需求全部写出再一次性迭代
  - ✅ **8/9**: ngrok 隧道已切回 8768（launchd plist 修复，KeepAlive 常驻），公网 https://unwhispering-imani-digitately.ngrok-free.dev 可达
  - ⏳ 剩余3模块（ASR/情感/匹配）交互需求 Daryl 即将澄清（8/5 线框 wf02/wf03/wf04 为基线）
  - 🆕 **7/31**: Daryl 飞书发送 01-素材扫描 模块改造需求（4项），小风已回复可行性评估（~3.5h，全部可行），等待Daryl确认2个前置问题
  - 🆕 **8/4**: Daryl 度假回来要求恢复开发；服务已持久化（LaunchAgent: videoeditor/ielts/ngrok，Gateway重启不掉）；隧道 `https://unwhispering-imani-digitately.ngrok-free.dev` ✅
  - ⚠️ **8/4 阻塞**: TOSHIBA EXT 1TB 硬盘文件系统层卡死（ls 卡 EINTR），需 Daryl 物理重插；watchdog LaunchAgent 每10分钟探测，恢复后自动挂载+前端可用


## ⏸️ 挂起
### 洗稿MVP — v1.2.0 已交付 · 需求收集模式（7/18 起，20+ 天无输入）
- **状态**: ⏸️ standby · 等待 Daryl 发送新需求（v1.2.0 内核卡 M1-M3 已完整交付）
- **恢复条件**: Daryl 提供具体需求后一次性动工

### IELTS陪练助手 — v1.3.0 开发完毕，⏸️ 等待Daryl晚间验收（7/25更新 · 8/4服务持久化）
- **7/25晚**: Daryl 调试中发现两个Bug，已修复：
  - DeepSeek API 模型名废弃 deepseek-chat → deepseek-v4-pro（旧名导致LLM乱码）
  - 跟读模块 JS null safe 兜底（deviceInfo DOM不存在时报错）
- Daryl 刷新后继续测试中
- **v1.3.0 变更**: free_talk深度对话优化 + 词汇学习模块 + 训练库Dashboard重构
  - free_talk: VAD思考窗口 / STT碎片过滤 / 提示词重写 / LLM max_tokens 500→700
  - 词汇: 对话气泡长按选词→同义表达卡片→收录 / B2+词表预高亮 / 复习页
  - Dashboard: 14天趋势+6周日历双栏 / To Improve Sentence+Vocab分拆 / 模式总结
  - 自动评估: ≥10轮对话断开时自动触发LLM评估→入trend+review队列
- **⚠️ 数据**: 昨晚session 987e4762丢失（重启后启动错误版本导致），已修复版本指向
- **待验收**: Daryl晚上到家练习口语时一并验收
- **8/4**: 服务已由 LaunchAgent 持久化（localhost:8767，v1.3.0 ACTIVE，health + dashboard 均 200 ✅）
- **v1.0.1**: 手机移动端自适应优化，Daryl 全部验收通过 ✅
- **v1.1.0 挂起原因**: iPhone 语音输入问题 + 交互逻辑拖沓，Daryl 要求暂停转其他任务
  - M1-M3 已完成 ✅（数据层/Dashboard/跟读闭环），M4 串联验收搁置
  - Debug 模式已确认正常（7/17 ~21:17-21:43）
  - iOS 回退完成，平板测试正面反馈（7/17 ~21:43 Daryl 👍）
  - 恢复条件：Daryl 进入 Debug 迭代模式逐一核对
- **管线1-IELST Part1**: ✅ v1.0.1 验收通过（e2e 3-4.5s）
- **管线2-Qwen Omni**: ❄️ 冻结
- **注意**: ngrok 已切给洗稿MVP（8777），IELTS 本地 8767 继续可用

## ✅ 已完成
### 8/6 工作区指针事故（✅ 已闭环 8/7）
- 根因: 8/4 openclaw.json 重写删 workspace 字段 → 会话回退空壳工作区失忆
- 修复: Kitty 写死 4 agent workspace + 空壳合并 + gateway 重启；8/7 验证新会话正确读取真工作区 ✅
- 教训: 启动必核对记忆完整性；单 Agent 单工作区；openclaw.json 变更后验证指针（已入 lessons.md）

### M2 开发计划（Daryl 7/5 指令 → 7/16 Daryl 看板验收认定完成 ✅）
- **P0 延时优化** ✅(7/15): ASR 4-8s→0.3-1.5s，e2e ~10s→3-4.5s，达标
- **P1 管线2 Qwen Omni**: 按决策冻结（重启触发条件存档 DEV_PLAN 附录A），随 M2 关闭
- **P2 评估面板 UI** ✅: 7/15 布局调整 + 7/16 v1.0.1 移动端自适应
- **P2 Part 2/3**: 基础模式已上线，深度模式归入后续里程碑（看板 M3）
- **7/14晚测试三问题** ✅ 全部修复并验收: TTS引擎翻转Piper主、长句软60s/硬90s断句、评估HTTP兜底+轮询
- **TTS 吞音/粘连** ✅: 方案B（句尾300ms静音填充），随 v1.0.0 验收

### IELTS陪练助手v2.0 M1 交付清单
| 模块 | 状态 | 完成度 |
|------|------|--------|
| 管线1 链式流式核心 | ✅ | 100% |
| 配置管理 + API Key | ✅ | 100% |
| SQLite 会话持久化 | ✅ | 100% |
| HTML 评估报告 | ✅ | 100% |
| Debug 验收模块 | ✅ | 90% |
| VAD + 音频采集修复 | ✅ | 100% |
| 成本追踪 Dashboard | ✅ | 100% |
| OPC 看板接入 | ✅ | 100% |
| 管线2 Qwen Omni 对接 | ❌ 冻结 | 30% |

## 🔵 待办
### IELTS陪练助手 — v1.4.1 题库改造 + v1.5.0 用户系统P1（🟢 开发完成，待 Daryl 验收）
- 服务 LaunchAgent 持久化：localhost:8767 ACTIVE（v1.5.0）
- **8/15**: ① 成本模型费率更新 ② Free Talk 持久记忆 v1.4.0 ③ 题库改造 A+B v1.4.1（120题+变体）④ 用户系统 P1 v1.5.0（登录页 /login，AUTH_REQUIRED=0 guest 模式，详见 2026-08-15.md）
- ⏸️ 待 Daryl 验收：v1.3.0 IELTS 1/2/3（对定式题型麻木，优先级让位）+ 今晚四个成果；Daryl 商业化方向：每月免费额度+按量收费
- 下一步：P2 数据隔离（全表挂 user_id + 强制登录开关）


### ~/opc-workspace 本地仓库卡死 rebase（7/16发现）
- 卡在 6/24 interactive rebase 中间态，每日 auto-backup 在 detached HEAD 上提交
- 推送暂用临时 sparse clone 绕过；待与 Daryl/Kitty 确认修复方式

### 硬件语音助手(MCU)开发
- 规划阶段


## 📦 历史归档项目（看板忽略此段）
- 抖音视频分析MVP（B站/douyin 下载器+分析，2026年4月）→ 已归档
- 语音转录测试(STT) → 已归档
- 投资者路演短语库 → 已归档
- ngrok 备用隧道 / Agent自进化 → 7/16 Daryl 看板验收确认非现存任务，已从待办移除
