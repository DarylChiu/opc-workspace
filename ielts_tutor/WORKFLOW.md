# 雅思陪练助手 v2.0 · 双管线架构工作流

> 版本: 0.1.0 | 创建: 2026-06-28 | 负责人: Bryson/吹点小风

---

## 一、架构总览

```
                              ┌─────────────────────┐
                              │      前端 SPA        │
                              │  · 模式选择          │
                              │  · 管线切换          │
                              │  · WebRTC 音频       │
                              │  · 实时字幕          │
                              │  · 纠错/评分         │
                              └──────────┬──────────┘
                                         │ WebRTC + WebSocket
                                         ▼
                              ┌─────────────────────┐
                              │    Server 路由层     │
                              │  POST /session/start │
                              │  WS   /ws/chat       │
                              │  POST /session/report│
                              │         │            │
                              │  管线选择逻辑        │
                              │   自由对话→管线2     │
                              │   IELTS模考→管线1    │
                              │   商业英语→管线1     │
                              │   发音练习→管线2     │
                              └────┬──────────┬─────┘
                                   │          │
                    ┌──────────────┘          └──────────────┐
                    ▼                                        ▼
         ┌─────────────────┐                    ┌─────────────────┐
         │   管线 1         │                    │   管线 2         │
         │ 链式流式         │                    │ Qwen-Omni        │
         │ (精度优先)      │                    │ (流畅优先)      │
         │                 │                    │                 │
         │ Google STT      │                    │ 端到端语音→语音  │
         │ DeepSeek V4 Pro │                    │ WebRTC           │
         │ Google TTS      │                    │ <2s 延迟         │
         │ 1-3s 延迟       │                    │                 │
         └────────┬────────┘                    └────────┬────────┘
                  │                                      │
                  └──────────────┬───────────────────────┘
                                 │ (会话结束)
                                 ▼
                        ┌─────────────────┐
                        │ 统一评估出口      │
                        │ DeepSeek V4 Pro  │
                        │ · 评分           │
                        │ · 逐句纠错        │
                        │ · 弱点追踪        │
                        │ · 学习报告        │
                        └─────────────────┘
```

---

## 二、管线 1 · 链式流式（精度优先）

```
用户 → 录音(WebM/Opus) → WebSocket → Server
                                         │
  ┌──────────────────────────────────────┘
  ▼
Step 1 · STT 流式转写 (Google Speech-to-Text)
  ├─ 流式 partial results（~100ms间隔）
  ├─ 学习者停顿检测（不因思考中断断句）
  └─ 输出: 实时部分文本 + 完整句子文本
                                                    │
  ▼
Step 2 · DeepSeek 对话引擎（流式）
  ├─ 考官角色扮演（IELTS / 商业英语）
  ├─ 流式 token 输出（~50ms间隔）
  ├─ 实时纠错标记（语法/词汇/发音建议）
  └─ 输出: 流式回复文本 + 纠错标记
                                                    │
  ▼
Step 3 · TTS 语音合成 (Google Cloud TTS)
  ├─ 流式音频合成
  ├─ 自然语调 + 合理停顿
  └─ 输出: 音频流 → WebSocket → 前端播放
                                                    │
  ▼
Step 4 · 异步评估（会话结束后）
  ├─ 完整对话→DeepSeek深度分析
  ├─ IELTS 四维评分（流利度/词汇/语法/发音）
  ├─ 逐句纠错建议
  └─ 生成学习报告

⏱ 延迟: 1-3s/轮 | 💰 成本: ~$0.01/min | 🎯 IELTS模考 / 商业英语 / 语法精练
```

---

## 三、管线 2 · 语音→语音（流畅优先）

```
用户 → 音频流(WebRTC) → Server → Qwen-Omni Realtime API
                                         │
  ┌──────────────────────────────────────┘
  ▼
Step 1 · 端到端语音对话
  ├─ 理解语调/情绪/停顿
  ├─ 自然打断/追问
  ├─ 上下文连贯记忆
  ├─ 考官角色扮演
  └─ 输出: 语音 → WebRTC → 前端播放
                                                    │
  ▼
Step 2 · 会话转录存档
  ├─ 全程录音 → 转写文本
  └─ 存入会话历史
                                                    │
  ▼
Step 3 · 异步评估（同管线1 Step 4）
  ├─ DeepSeek深度分析
  └─ 生成学习报告

⏱ 延迟: <2s/轮 | 💰 成本: ~$0.02-0.05/min | 🎯 自由对话 / 发音练习 / 语感训练
```

---

## 四、管线切换策略

```
┌──────────────┐
│ 用户选择模式  │
├──────────────┤
│ IELTS 模考   │──→ 管线 1（精度优先，需要详细评分）
│ 商业英语     │──→ 管线 1（措辞准确性要求高）
│ 发音练习     │──→ 管线 2（需要音频层信息）
│ 自由对话     │──→ 管线 2（流畅度优先）
│ 热身闲聊     │──→ 管线 2（轻松对话感）
└──────────────┘
         │
         ▼
   系统自动选择（用户可手动切换）
```

---

## 五、已有资产整合映射

### 🔵 可直接复用的核心资产

| 已有文件 | 路径 | 整合到新架构的节点 |
|------|------|------|
| **FastAPI Server** (580行) | `Bryson/voice-mvp/backend/server_with_full_interaction_new.py` | → `ielts_tutor/backend/server.py` 重构为路由层 |
| **前端 SPA** (1887行) | `Bryson/voice-mvp/frontend/` (index.html + styles.css + app.js) | → `ielts_tutor/frontend/` 重构，增加管线切换UI |
| **STT 集成** | `direct_stt_test.py` / `test_stt_real.py` / `fix_stt_encoding.py` | → 管线1的 Step 1 流式 STT 模块 |
| **TTS 集成** | `Bryson/voice-mvp/backend/server_with_tts_fixed.py` | → 管线1的 Step 3 TTS 模块 |
| **音频处理** | `audio_to_base64.py` / fix_ielts_metadata.py | → 音频编解码工具 |
| **DeepSeek 测试** | `deepseek_direct_test.py` / `test_deepseek_key_v2.py` | → 管线1的 Step 2 对话引擎 |
| **雅思题库** | `references/practice_templates.md` | → `ielts_tutor/prompts/ielts_templates.py` |
| **商业英语模板** | `references/business_templates.md` | → `ielts_tutor/prompts/business_templates.py` |
| **投资者路演短语库** (8类 56短语) | `Bryson/investor-pitch-phrases/phrases/` | → `ielts_tutor/references/investor_phrases/` |
| **评估标准** | `references/practice_templates.md` (评分体系) | → 管线 1+2 的 Step 4 评估引擎 |
| **诊断报告** | `reports/ielts_diagnostic_2026-06-15.md` | → 架构设计参考，需求溯源 |

### 🟡 需要适配改造的资产

| 已有功能 | 改造内容 |
|------|------|
| **FastAPI Server** | 添加双管线路由逻辑，WebRTC 替代 WebSocket |
| **前端 UI** | 增加模式选择器 + 管线切换按钮 + 实时字幕面板 |
| **STT 流式** | 从录完整段→流式 partial results（Google StreamingRecognize） |
| **TTS** | 从完整合成→流式合成 + 自适应语速 |
| **WebSocket** | 改造为 WebRTC 双向音频通道 (LiveKit 或原生) |
| **评估** | 从单次评分→多维度报告（流利度/词汇/语法/发音四维） |

### 🟢 新增资产

| 新模块 | 用途 |
|------|------|
| **管线2 Qwen-Omni 对接** | WebRTC → Qwen-Omni Realtime API |
| **管线选择路由** | 基于 session 模式自动切换管线 |
| **学习记录数据库** | 会话历史、错误追踪、进度统计 |
| **ngrok 隧道** | 公网访问（复用视频分析项目隧道配置） |

---

## 六、文件结构

```
ielts_tutor/
├── WORKFLOW.md                    ← 本文件
├── VERSION
├── backend/
│   ├── server.py                   ← 主服务器（双管线路由）
│   ├── pipeline_cascade.py         ← 管线1：链式流式
│   ├── pipeline_qwen_omni.py       ← 管线2：语音→语音
│   ├── stt_streaming.py            ← Google STT 流式模块
│   ├── tts_streaming.py            ← Google TTS 流式模块
│   ├── conversation_engine.py      ← DeepSeek 对话引擎
│   ├── evaluation_engine.py        ← 统一评估出口
│   └── session_manager.py          ← 会话状态管理
├── frontend/
│   ├── index.html                  ← SPA 入口
│   ├── styles.css                  ← 样式
│   ├── app.js                      ← 主逻辑（WebRTC + UI）
│   └── components/
│       ├── mode_selector.js        ← 模式选择器
│       ├── pipeline_switcher.js    ← 管线切换
│       ├── subtitle_panel.js       ← 实时字幕
│       └── score_panel.js          ← 评分展示
├── prompts/
│   ├── ielts_examiner.py           ← 雅思考官角色 prompt
│   ├── business_english.py         ← 商业英语角色 prompt
│   └── evaluation.py               ← 评估报告 prompt
├── references/
│   ├── ielts_templates/            ← 雅思题库模板
│   ├── business_templates/         ← 商业英语场景模板
│   └── investor_phrases/           ← 投资者路演短语库（从Bryson/迁移）
├── reports/
│   └── ielts_diagnostic_2026-06-15.md  ← 诊断报告（参考）
└── docs/
    ├── ARCHITECTURE.md
    └── DEPLOYMENT.md
```

---

## 七、开发阶段

### Phase 0 · 基础骨架（当前）
- [x] 市场调研 & 架构决策
- [x] WORKFLOW.md 工作流文档
- [ ] 已有资产审计 & 迁移整合
- [ ] 项目目录初始化

### Phase 1 · 管线1 重构（链式流式）
- [ ] FastAPI Server 路由层重构
- [ ] Google STT 流式集成（StreamingRecognize）
- [ ] DeepSeek 对话引擎（考官角色 prompt + 流式输出）
- [ ] Google TTS 流式合成
- [ ] WebRTC 音频通道搭建
- [ ] 前端重构（模式选择 + 实时字幕 + 纠错显示）
- [ ] 异步评估报告生成

### Phase 2 · 管线2 接入（Qwen-Omni）
- [ ] Qwen-Omni Realtime API 对接
- [ ] WebRTC 分流逻辑
- [ ] 管线切换前端交互
- [ ] 会话转录存档

### Phase 3 · 打磨
- [ ] 学习记录数据库
- [ ] 薄弱点追踪
- [ ] 自适应难度
- [ ] 移动端适配
- [ ] ngrok 公网部署

---

## 八、版号

| 版号 | 日期 | 变更 |
|------|------|------|
| 0.1.0 | 06-28 | 双管线架构设计 + 已有资产整合 |
