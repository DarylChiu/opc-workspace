# 开发计划 · A 题库更新 + C 听读训练（2026-10-07）

> Daryl 拍板：只做 A + C，B（发音音素级评估）不做。
> 状态：计划已定稿（2026-10-07 三决策确认），未落地。
> 已拍板：① A1 搜公开题库、季度更新、更新前经 Daryl 授权 ② C1 复用视频分析 workflow 下载模式（贴链接→下载→转写→第一版字幕跟读）③ C2 默认原文、中文字幕需完成跟读+复述后「揭开」④ **先做 C，C 归入 Shadowing 模块（素材导入+听读+复述三能力）**

## 范围界定

**做**
- A1 题库按季度更新（内容 + 数据结构加「季度」字段）
- A2 Part2 的 1 分钟准备计时（交互增量）
- C1 素材导入：YouTube/B站/本地音视频 → 转写 → 分句 → 入库
- C2 素材听读页：逐句播放/调速/字幕 + 逐句跟读 + 收藏
- C3 复述（retell）闭环：听 → 隐藏原文 → 复述 → AI 对比漏听/误听

**不做**
- B 发音音素级评估（OpenPronounce 集成）
- free_talk 场景改造
- EchoLingo 代码直接搬用（PolyForm Noncommercial，商用需授权；且与现有系统难合并）

## 现状基础（已核实的可复用资产）

| 能力 | 位置 | 复用方式 |
|------|------|---------|
| STT（faster-whisper small.en） | `backend/stt_streaming.py` | C1 转写直接复用模型加载机制 |
| TTS（Piper 主 + Google 兜底） | `backend/server.py` tts_speak | 素材逐句朗读、跟读参考音 |
| LLM（DeepSeek 流式） | `backend/server.py` ds_stream/ds_chat | C3 复述对比、评估 |
| 跟读模块 | `frontend/shadow.html` + review 端点 | C2 逐句跟读、C3 复述交互 |
| 词汇/复习队列 | `backend` review_* 端点 + vocab | C2 收藏句子入复习队列 |
| 题库引擎（去重+槽位变体） | `backend/question_bank.py` | A1 直接升级内容 |
| SQLite 会话层 | `backend/session_manager.py` | C1 新增 materials/sentences 表 |

## 任务拆解

### A1 · 题库季度更新（0.5-1 天）
1. `data/question_bank.json` 加 `season` 字段（如 `"2026-09/12"`），part1/part2/part3 各条目可选挂 season
2. `question_bank.py` 支持按 season 过滤抽题（默认最新季度）
3. 更新 `version`/`updated`；导入当前季度真题内容
- **素材来源**：搜公开题库整理（已拍板）
- **更新频率**：季度更新（1-4/5-8/9-12 月），每次更新前经 Daryl 授权（已拍板）

### A2 · Part2 1 分钟准备计时（0.5 天）
1. `frontend/index.html` Part2 流程：显示话题卡 → 60s 倒计时（静默准备）→ 再开录音
2. 复用现有 Part2 抽题返回的 topic/title；计时器纯前端，无需后端改动

### C1 · 素材导入（3-4 天）
> 策略（2026-10-07 二次定稿）：**双路径自动分流**。有字幕（TED/学习/演讲类）秒级拿字幕；无字幕（vlog/生活类）Whisper 转写为主力。覆盖 Daryl 两类素材需求。

1. 新增 `backend/import_material.py`，分流逻辑：
   - **探测字幕**：YouTube 用 yt-dlp 拉英文字幕探测（拉到即用）；B站用官方 API probe（`x/player/v2` 字幕列表，借鉴 EchoLingo 思路）
   - **路径A（有字幕）**：直接解析字幕（YouTube .vtt / B站 JSON），B站同时匹配中文对照；秒级
   - **路径B（无字幕，vlog 主力）**：下载音频（YouTube yt-dlp / B站官方 playurl DASH 流）→ faster-whisper 转写（**离线用大模型 medium.en/large-v3 求准**，与实时 STT 的 small.en 分开）→ 分句
   - **分句三规则**：句末标点 / 与下句间隔≥0.8s / ≥18-40 词合并
   - **转写后轻过滤**：滤掉纯口头禅碎句（uh/you know/like...）、无意义短片段，只保留有跟读价值的完整句（vlog 关键）
   - **中文**：B站有中文直接匹配；否则 DeepSeek 逐句翻译
2. 新增 SQLite 表 `materials`、`sentences`（材料元信息 + 句子）
3. 新增 API：`POST /materials/import`、`GET /materials`、`GET /materials/{id}/sentences`
- **风险**：yt-dlp/官方 API 随平台政策变化；vlog 嘈杂场景（BGM/多人/口音）转写准确率下降，medium/large 可改善但更慢

### C2 · 素材库页（并入 Shadowing 模块，1-2 天）
> 已拍板（2026-10-07）：C 不另起新页，扩展 `frontend/shadow.html` 顶部加标签：📌 巩固队列（现有）/ 📚 素材库（新增）。两个标签共用一个跟读引擎（review_attempt 打分 + review_tts 范音），仅素材来源不同。

1. `frontend/shadow.html` 顶部加「巩固队列 / 素材库」双标签
2. 素材库页：选素材 → 逐句播放 / 连续播放 / 循环 / 0.5x-2x 调速
   - 字幕：**默认原文**；中文字幕需**完成跟读训练 + 复述后**才解锁「揭开」（已拍板）
   - 逐句跟读（复用 review_attempt/review_tts）+ 收藏句子入复习队列
3. 复用现有 review 打分闭环

### C3 · 复述（retell）闭环（1-2 天）
1. 后端 `POST /materials/{id}/retell`：
   - 取一句/一段 → 用户复述 → STT → LLM 对比漏听/误听/替换词
2. 前端交互：听 → 隐藏原文 → 凭记忆复述 → 看 AI 对比（逐句标漏听/误听）
3. 复用 STT + ds_chat 评估；提示词参考「复述对比」专用模板

## 成本汇总

| 模块 | 估算 |
|------|------|
| A1 题库季度更新 | 0.5-1 天 |
| A2 Part2 计时 | 0.5 天 |
| C1 素材导入 | 3-4 天 |
| C2 听读页 | 1-2 天 |
| C3 复述闭环 | 1-2 天 |
| **合计** | **约 6-8 天**（不含大规模内容整理） |

## 建议执行顺序（2026-10-07 调整：C 优先）

1. **C 先行**（新能力/增量价值最高）：C1 素材导入 → C2 素材库页（并入 Shadowing）→ C3 复述闭环
2. **A 后置**（题库内容更新，低风险）：A2 计时半天 → A1 题库更新（需搜公开题库 + 经 Daryl 授权）
3. 每块完成单独验收，不一次性大改

## 已拍板决策（2026-10-07）

1. **A1 真题素材**：搜公开题库整理；季度更新；每次更新前经 Daryl 授权。
2. **C1 素材导入模式**：复用视频分析 workflow——用户贴 YouTube/B站链接，后端 yt-dlp/you-get 下载 + ffmpeg 提音频切片 → whisper 转写 → 生成第一版字幕跟读。
3. **C2 中文字幕**：默认原文；中文字幕可选，但需完成跟读训练 + 复述后才解锁「揭开」。中文用 DeepSeek 逐句翻译。

## 风险与注意

- yt-dlp 下载受平台/地区政策影响，可能失效
- 版权：仅处理用户有权使用的内容
- 分句音频切片占用本地存储（TOSHIBA 硬盘现状见 active.md）
- EchoLingo 只能学思路，不可搬代码商用（PolyForm Noncommercial）
