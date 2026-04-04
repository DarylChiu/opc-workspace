# OpenAI TTS集成技术调研
> 为阶段2语音输出集成做准备

## 时间点
- **开始时间**: 2026-03-24 21:56 (GMT+7)
- **目标完成**: 2026-03-28 (周六前)
- **预算约束**: 每月$0.5 (约33,333字符)

## 技术方案对比

### A: OpenAI原生TTS API
**优点**:
- 官方支持，文档完善
- 价格透明: $0.015/千字符
- 语音质量可接受（原型级别）
- 三种语音选择：alloy, echo, fable, onyx, nova, shimmer

**缺点**:
- 需要通过OpenAI API密钥（需要检查OpenRouter支持情况）

### B: 通过OpenRouter中转
**优点**:
- 使用现有密钥架构（`ielts_tts_2026.key`）
- 统一成本计算
- 与当前系统兼容

**缺点**:
- 需要验证OpenRouter是否支持OpenAI TTS
- 可能存在额外路由延迟

## API端点分析

### OpenRouter模型列表检查
```bash
# 已执行：未发现TTS专用模型
# 但可能有音频相关的通用模型
```

### OpenAI直接调用
```bash
curl https://api.openai.com/v1/audio/speech \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello world! This is a test of OpenAI TTS.",
    "voice": "nova"
  }' \
  --output speech.mp3
```

## 关键验证步骤

### 1. 检查现有密钥能力
```bash
# 测试OpenRouter API密钥是否能访问OpenAI TTS
curl -s -H "Authorization: Bearer $(cat ~/.openclaw/auth/openrouter/ielts_tts_2026.key)" \
  "https://openrouter.ai/api/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "test",
    "voice": "nova"
  }'
```

### 2. 测试OpenAI直接API（需要独立API密钥）
```bash
# 如果要绕过OpenRouter使用原生OpenAI
export OPENAI_API_KEY="sk-..."
curl -s https://api.openai.com/v1/audio/speech \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d @audio_request.json -o test.mp3
```

## 集成架构设计

### 方案1: 直接调用OpenAI API
```
user_text → TTS Service → OpenAI API → audio.mp3 → player
                      ↓
                 cost tracking ($0.015/千字符)
```

### 方案2: OpenRouter中转
```
user_text → OpenRouter Gateway → OpenAI backend → audio → player
```

## 成本计算模型

基于预算约束：
```
每月$0.5预算 = 33,333字符
每日平均 = 1,111字符

按场景估算：
- 雅思Part 1答案: 100-150字符 × 3题 = 450字符
- Part 2演讲: 500字符 × 1题 = 500字符
- Part 3讨论: 200字符 × 2题 = 400字符
总计: 约1,350字符/次练习

每月可支持: 33,333 ÷ 1,350 ≈ 24.7次完整练习
```

## 音频处理技术要点

### 1. 格式选择
- **MP3**: 通用性好，压缩率高
- **WAV**: 无压缩，音质最好，文件大
- **OGG**: 开源格式，适合网络流

### 2. 本地环境播放方案
```python
# Python播放示例
import os
import subprocess

def play_audio(filepath):
    if os.name == 'nt':  # Windows
        os.startfile(filepath)
    elif os.name == 'posix':  # macOS/Linux
        # macOS
        subprocess.call(['afplay', filepath])
        # Linux (需要安装play/pulseaudio)
        # subprocess.call(['play', filepath])
```

### 3. 音频缓存策略
- 本地缓存已生成的语音（避免API重复调用）
- 按用户ID + 文本哈希进行缓存
- 缓存清理策略（最大文件数/最大存储空间）

## 实现步骤分解

### 阶段2A: 基础TTS功能（周三前）
- [ ] API端点验证
- [ ] 音频生成测试
- [ ] 本地播放测试
- [ ] 基础成本追踪

### 阶段2B: 雅思场景适配（周四前）
- [ ] Part 1-3语音模板
- [ ] 语音切换界面
- [ ] 缓存策略实施
- [ ] 错误处理机制

### 阶段2C: 优化与测试（周五前）
- [ ] 性能测试
- [ ] 成本验证
- [ ] 用户体验优化
- [ ] 系统稳定性测试

## 关键技术依赖

### 确定可用的：
1. ✅ API密钥架构（`ielts_tts_2026.key`）
2. ✅ 成本计算框架（纯API模式）
3. ✅ 本地存储（workspace目录）

### 待确认的：
1. ⚠️ OpenAI TTS通过OpenRouter的可访问性
2. ⚠️ 本地音频播放环境配置
3. ⚠️ 用户设备音频输出能力

## 风险评估

### 高风险项目：
1. **API访问问题** - OpenAI TTS可能无法通过OpenRouter访问
2. **音频播放兼容性** - 不同操作系统需要不同的播放方案
3. **成本控制** - 每月$0.5预算需要精细管理

### 缓解措施：
1. **备选方案准备**：探索其他TTS服务（Google TTS免费额度）
2. **兼容性测试**：在多环境下测试音频播放
3. **用量监控**：实时显示字符计数和预计费用

## 今晚可立即开展的工作

1. **API验证实验**：测试OpenRouter对OpenAI TTS的支持
2. **备用方案研究**：Google TTS免费额度和API
3. **音频播放原型**：创建基本的音频播放测试脚本
4. **成本计算原型**：设计字符计数和费用计算模块

## 下一步行动项

1. [ ] 使用现有密钥测试OpenAI TTS API端点
2. [ ] 如果不行，申请OpenAI独立API密钥
3. [ ] 创建音频播放的Python脚本原型
4. [ ] 设计字符计数算法
5. [ ] 验证不同操作系统的音频兼容性

## 决策点

**是否需要OpenAI独立API密钥？**
- 如果OpenRouter支持OpenAI TTS：使用现有密钥
- 如果不支持：需要申请独立的OpenAI API密钥

**音频播放策略？**
- 简单方案：下载为文件，让用户手动播放
- 自动方案：根据OS自动选择合适的播放器
- 高级方案：集成流媒体播放控件

**成本控制策略？**
- 实时显示字符计数
- 月度用量预警（当达到80%预算时）
- 低成本备选方案自动切换

---
**更新日志**
- 2026-03-24 21:56: 创建技术调研文档
- 2026-03-24 21:42: Daryl决策 - 选用OpenAI TTS，预算$0.5/月，周六前完成