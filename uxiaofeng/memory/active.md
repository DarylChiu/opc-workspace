# 当前活跃任务 (中期记忆 — 每次session加载)

> 最后更新: 2026-07-15 09:50

## 🟢 进行中
### IELTS陪练助手v2.0 — M1 验收完成，剩余问题转入 M2
- **雅思** 口语/写作/听力/阅读全线陪练
- **管线1-IELST Part1**: ✅ 验收 70%
  - 已完成: 链式流式核心管线、Debug验收模块、评估报告系统、成本追踪、VAD音频采集修复
  - 待解决: **延时优化**（当前 7700-11787ms，需降到 3000-5000ms）
- **Debug 验收模块**: ✅ 验收 90%
  - 已完成: SQLite 持久化、实时监控、诊断引擎、管线1/管线2 双面板
  - 待解决: 管线2 debug 数据完整性
- **TTS 吞音/粘连**: ✅ 修复已部署（7/14）
  - 方案B（句尾300ms静音填充）已实现并部署
  - TTS 引擎翻转为 Piper high 主引擎 → Kokoro fallback
  - 待 Daryl 今晚验收测试
- **7/14晚测试三问题**: 问题2✅（Piper翻转，7/14晚） 问题1✅+问题3✅（7/15上午修复并部署）
  - 问题1 长句断句: buffer 30s硬切 → 软60s等停顿flush + 硬90s兜底
  - 问题3 评估不显示: score缓存 + `GET /api/session/{sid}/score` HTTP兜底 + 前端轮询
  - 三项均待 Daryl 实测验收；服务须用 venv/bin/python3 启动
- **管线2-Qwen Omni**: ❌ 未通过验收
  - 已知问题: Voice 不支持(Cherry)、buffer too small、WebSocket frame 超限(>256KB)
  - 决定: 暂停管线2开发，转入 M2 一起规划

### M2 开发计划（Daryl 7/5 指令）
- **P0**: 管线1 延时降至 3000ms 以下
  - ASR: batch→streaming API（预期 4617→300ms）
  - TTS: 串行→并行调用（预期 5595→2000ms）
- **P1**: 管线2 Qwen Omni 修复
  - 音频分片发送（解决 256KB frame 限制）
  - Voice 参数修正
- **P2**: Part 2 长独白 / Part 3 深度讨论模式
- **P2**: 评估面板 UI 优化

### Loop Engineering（基建 · P0 🔴 事故复盘完成，方向待定）
- **状态**: 🔴 Sentinel v1 事故复盘完成（7/11 Daryl 对话），方向待定
- **事故**: Sentinel v1 Plugin → $20 API 浪费 + Gateway 反复重启 + 开发效率下降
- **方案**: Sentinel v2（轻量 before_tool_call hook，只拦 write/edit/exec，零 Gateway 通信）已设计
- **阻塞**: Daryl 认为基建问题需要更强模型才能从根本上解决，7/12 讨论未发生
- **方向**: 决策矩阵延伸，短链→长链，P2/P3 自主执行（原计划 M1-M3 时间线已过期）
- **状态**: ⏸️ 等待 Daryl 发起讨论

## ✅ 已完成
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
| 管线2 Qwen Omni 对接 | ❌ | 30% |

### 视频分析交互Workflow 🎬
- **状态**: 🟡 拓展节点「内核洗稿MVP」启动中（7/15 Daryl 确认交叉开发模式）
- **交叉开发模式**（7/15 确立）: 雅思验收门控期间 → 开发洗稿MVP中午可验收小里程碑；两项目分session隔离防上下文污染
- **待输入**: Daryl 的洗稿构想+参考案例（未发）
- **里程碑**: v1.0 MVP → v1.1 商业数据+Tab → v1.2 Gemini V3 原生视频 ✅ (7/4)
- **成本**: ~$0.0025/次分析
- **地址**: https://unwhispering-imani-digitately.ngrok-free.dev (端口8777)
- **代码**: video_analyzer_app/

## 🔵 待办

### ngrok 备用隧道安装
- 备用隧道待部署

### 硬件语音助手(MCU)开发
- 规划阶段

### Agent自进化
- 待 Loop Engineering 框架就绪

### 内核驱动洗稿MVP
- 待视频分析下一阶段确认

## 📦 历史归档项目（看板忽略此段）
- 抖音视频分析MVP（B站/douyin 下载器+分析，2026年4月）→ 已归档
- 语音转录测试(STT) → 已归档
- 投资者路演短语库 → 已归档
