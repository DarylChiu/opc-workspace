# 长语音处理 — 业界主流方案调研报告

> 2026-07-08 | 调研人: Bryson

## 1. 问题定义

Voice Agent 中「用户长时间说话不停止」会导致：
- 音频缓冲区无限增长 → 内存溢出
- ASR 处理超时（大音频文件推理时间长）
- LLM 收到超大文本 → 上下文爆炸、推理变慢
- 对话体验差（用户说了很久，系统一直没反应）

## 2. 业界主流方案

### 2.1 LiveKit Agents（业界事实标准）

LiveKit 的 `TurnHandlingOptions` 提供了**最完整的四层保护**：

| 层级 | 参数 | 默认值 | 作用 |
|:---|:---|:---|:---|
| **Endpointing** | `max_delay` | 3.0s | 用户停止说话后最长等待时间，超时强制提交 |
| **Endpointing** | `min_delay` | 0.5s | 静音检测到的最短等待（防止抢话） |
| **UserTurnLimit** | `maxDuration` | 可配置 | **用户单次说话硬上限**，超时自动中断并触发响应 |
| **Interruption** | `min_duration` | 0.5s | 最短打断检测时长（防止误触发） |

**核心机制：**
- **VAD + Semantic Turn Detection 双路判定**：不只靠静音阈值，还用 AI 模型判断「这句话有没有说完」
- LiveKit 的 `TurnDetector` 模型只有 30M 参数，CPU 推理 10ms，准确率 95%+
- **Dynamic Endpointing**：根据对话节奏自适应调整静音阈值（说话快的人阈值短，说话慢的人阈值长）

### 2.2 OpenAI Realtime API

GPT-4o Realtime 的处理方式更「智能」：

| 机制 | 说明 |
|:---|:---|
| **Server VAD** | 内置 VAD，检测语音起止，自动提交音频片段 |
| `idle_timeout_ms` | 用户长时间不说话时，模型主动问 "Are you still there?" |
| `input_audio_buffer.speech_stopped` | VAD 检测到语音停止事件 |
| `max_response_output_tokens` | 限制模型响应长度，防止超长输出 |

**特点：** 端到端模型内部处理 turn detection，开发者不需要手动管理缓冲区。

### 2.3 Pipecat / 语义 Turn Detection

- 从纯静音阈值升级为 **语义 + 时长 + VAD 三路融合**
- 训练小型 BERT/Transformer 判断 partial ASR text 是否已结束
- 典型参数：110M 以下，CPU 上 < 20ms 推理

### 2.4 WhisperX（长音频 ASR 策略）

针对长音频的 ASR 处理，WhisperX 采用 **Cut & Merge 策略**：

1. **VAD 分段**：先用 VAD 检测语音段，切分成短片段
2. **最优分块**：根据 VAD 边界智能切分（不在句子中间切）
3. **上下文重叠**：相邻 chunk 间保持 1-2s 重叠，避免边界信息丢失
4. **合并去重**：合并重叠区域的重复文本

### 2.5 HuggingFace Chunking with Stride

经典的 CTC-based ASR 长音频方案：
- 音频切成 10s chunk，相邻 chunk 重叠 stride_length
- 丢弃 chunk 边缘的低质量推理结果（通常丢两边各 1/6）
- 中间高置信度部分拼接

## 3. 长语音保护的层次模型

业界共识是**多层防护，逐级兜底**：

```
Layer 1: VAD 实时检测            → 用户还在说吗？   [~30ms 延迟]
Layer 2: Turn Detection          → 用户说完了吗？   [语义模型判断]
Layer 3: Endpointing Max Delay   → 最长等 3s 静音   [兜底强制提交]
Layer 4: User Turn Limit         → 单次说话硬上限   [15-30s 绝对上限]
Layer 5: Audio Buffer Overflow   → 内存保护         [480KB ≈ 15s]
Layer 6: STT Output Truncation   → 上下文保护       [500 字符截断]
```

## 4. 对我们系统的建议

当前 IELTS Tutor 管线1 已有的保护：

| 层级 | 状态 | 说明 |
|:---|:---|:---|
| L1 VAD | ✅ | 前端 VAD 控制 flush 时机 |
| L2 Turn Detection | ⚠️ 基础 | 仅靠静音阈值，无语义判断 |
| L3 Max Delay | ❌ 缺失 | 无静音超时兜底 |
| L4 User Turn Limit | ⚠️ 基础 | 刚加了 15s 自动 flush（纯缓冲大小） |
| L5 Buffer Overflow | ✅ | 480KB 上限自动 flush |
| L6 STT Truncation | ✅ | 500 字符截断 |

**推荐改进（按优先级）：**

1. **P1 · Endpointing Max Delay**：添加可配置的静音超时（如 3s），超时自动 flush — 代码量小、收益高
2. **P2 · User Turn Limit**：将缓冲区自动 flush 升级为基于时间的限制（如 20s 语音硬上限），而非仅靠字节数
3. **P3 · Dynamic Endpointing**：根据对话节奏自适应调整静音阈值（快节奏对话阈值短、慢节奏阈值长）
4. **P3 · Semantic Turn Detection**：接入小型 turn detection 模型判断语义完整性（但引入额外依赖和延迟）

## 5. 关键参数对照表

| 框架 | Endpoint Min | Endpoint Max | User Turn Limit | Idle Timeout |
|:---|:---|:---|:---|:---|
| LiveKit | 0.5s | 3.0s | 可配置 | - |
| OpenAI Realtime | - | - | - | 可配置 |
| Pipecat | 0.5s | 2-5s | - | - |
| **IELTS Tutor (当前)** | VAD 阈值 | **无** | **15s (缓冲大小)** | **无** |
| **建议目标** | VAD 阈值 | **3s** | **20s (基于时间)** | **8s** |

## 6. 总结

- **LiveKit 的方案最完整**：四层递进保护，从语义到物理层层兜底
- **核心思路是「分层次、渐进式」**：从快速响应的 VAD → 语义判断 → 时间兜底 → 硬上限
- **我们当前缺的是中间层**：有底层保护（buffer limit）但没有「智能判断」和「时间兜底」
- **最快见效的是 Endpointing Max Delay**：在 VAD 检测到静音后加一个 3s 硬超时，就能解决大部分用户说了很久不停止的问题
