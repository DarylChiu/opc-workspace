# IELTS 陪练助手 · GitHub 开源项目调研（2026-10-07）

> 目标：调研 GitHub 上「雅思陪练 / 英语口语·听读训练」相关开源项目，提炼可吸收内容。
> 约束（Daryl 指令）：不做 Duolingo 式重功能；做轻功能高粘性；场景仅限英语口语 + 听读训练；先调研不落地。

## 一、结论先行

1. **高粘性的引擎是「复习闭环 + 间隔重复 + streak」，不是题海和功能堆叠**。
   证据：最火的 IELTS-Speaking-Simulator（100K+ 对话）作者亲述——他自己练了半年只提升 0.5 分，因为「没有复习每一场练习」。练完不复盘≈白练。
2. **发音评估可以免费自托管**：OpenPronounce（MIT）本地 CPU 跑，音素级评分，直接替代 Azure/ELSA/SpeechAce 的按分钟付费 API——补上我们管线最大短板（发音不准）。
3. **听读训练最佳范式 = EchoLingo 的「兴趣素材 → 逐句听 → 复述 → AI 对比」闭环**，且无需登录/无需 API key 即可跑（降门槛、降成本）。
4. **「微功能」思路**（数字听写、分句听写）可作轻量切入，一上来不做大而全。

## 二、项目清单（按对标价值分四类）

### A. 雅思口语模拟（最直接对标）

#### 1. hubeiqiao/IELTS-Speaking-Simulator ⭐ 最重要
- 数据：100K+ 对话、4.4 分(500+)、5万学习者；后来演化为 JoeSpeaking.com 商业产品
- 本质：不是代码，是「提示词工程 + 结构化题库 + 工作流」，分 Part 1/2/3
- **可吸收点**：
  - 题库按季度更新（1-4月 / 5-8月 / 9-12月），随机抽题（需解决 GPT 不随机的问题）
  - Part2 有 1 分钟准备计时；每场结束自动评分 + 追问「要不要优化答案」
  - 题库 + 各版本 prompt 随 Release 公开，可直接复用/参考
- **警示/反证**：
  - 作者自评只提升 0.5 分 → 印证「不复盘就白练」，复习闭环才是粘性核心
  - 依赖 OpenAI GPT；语音转文字导致发音评估完全不准 → 我们自建管线反而有优势

#### 2. rahulsamant37/english-speaking-practice-app
- Groq（快/便宜 LLM）+ Notion 存题库，AI 老师提问 → 录音 → 转写 → 反馈
- 可吸收：Notion 当题库/内容管理，低成本内容运营

#### 3. 其他口语类（弱对标，仅列名）
- fflec/ielts-speaking、iamvickynguyen/IELTS-Speaking-simulator（Android）、LegendZDY/AI-IELTS-Speaking、5uru/Discute、lengvietcuong/examinai、Flutter_IeltsPrep（重功能，反例）

### B. 发音评估（技术基建，轻量自托管）

#### 4. Halleck45/OpenPronounce ⭐ 技术价值最高（MIT）
- 音素级发音评估：Wav2Vec2 + DTW，本地 CPU 跑，无 key、无账单、数据不出服务器
- 输出：score(0-100) + 每个发错词的 IPA（预期/实际）+ 音高/能量曲线（prosody）
- 评分公式：`0.3×声学距离 + 0.4×(1-音素错误率) + 0.3×(1-词错误率)`
- 接口：`/pronunciation` `/speech2text` `/phonemes` `/tts`（含参考发音），pip 可装，可 `pip install openpronounce` 直接嵌入我们管线
- 局限：英文校准最好；短词约 1/5 误报；重口音/儿童/噪声退化
- **结论：直接集成候选，补发音短板**

#### 5. jimbozhang/speechocean762
- 非母语英语发音评分语料（专家标注），可用于自校准/验证我们评分模型

### C. 听力/听读训练（最契合「轻功能高粘性·听读」）

#### 6. shine11224/EchoLingo ⭐ 听读训练最佳范本
- local-first，把用户自己的视频/播客/文章变成课：逐句听、复述、AI 对比、句型操练、词汇复习
- **可吸收点（方法论价值极高）**：
  - 「兴趣驱动素材」：导入自己想看的内容（YouTube/B站/本地音视频），比现成教材更易坚持
  - 学习闭环：理解 → 句中记词 → 复述输出 → 写作 → 语境复习
  - 5 设计原则：① 先理解后分析 ② 词在句中记 ③ 兴趣驱动 ④ 难度 i+1（可调字幕/词表控制支撑度）⑤ 以用促学（复述/写作）
  - **复述（retell）**：听 → 隐藏原文 → 凭记忆复述 → AI 对比漏听/误听部分 → 「听读训练」的核心高粘性交互
  - 无需 API key 也能用（内置 ECDICT 词典 + IELTS/TOEFL/GRE 词表）→ 降门槛
- 局限：PolyForm Noncommercial 协议（商用需单独授权）→ **只能学思路，不能直接搬代码商用**

#### 7. LoganLiu66/iListen
- 听力练习：yt-dlp 下载任意音频 → 分句 → 逐句听写（gradio 界面）
- 可吸收：任意音频切成句子做听写的工程手法

#### 8. Numblr（awesome-english 收录）
- 数字听力专项：日期/时间/电话/金额的听写
- 可吸收：「微功能」思路——轻到极致但解决真实痛点（IELTS 听力 Part1 常考数字/日期）

### D. 全栈平台（架构可借鉴，但偏「重」）

#### 9. atk0309/freelingo（AGPL-3.0）
- 自托管 AI 语言平台：CEFR 分级 + 个性化学习计划 + SM-2 间隔重复 + 语音对话 + streak/XP
- **可吸收的单点机制**：
  - 后端代理所有 LLM/TTS/STT 调用（前端不直连）→ 安全架构（我们已有类似）
  - SM-2 间隔重复 + streak（连续打卡）→ 高粘性两个成熟抓手
  - WebSocket `/ws/conversation` + 反向代理 TLS（实时对话的硬要求，与我们经验一致）
- 但这是「重」平台（PostgreSQL+Redis+Docker+GPU），**不符合我们轻定位，只吸收单点，不整搬**

## 三、给我们的落点建议（轻功能高粘性 · 口语听读）

1. **粘性引擎**：复习闭环 + 间隔重复(SM-2) + streak，而非功能堆叠
2. **补短板**：集成 OpenPronounce（MIT）做发音音素级反馈，替代/增强现有 LLM 评估
3. **听读范式**：借鉴 EchoLingo 的「兴趣素材 → 逐句 → 复述 → AI 对比」闭环；无需登录即可跑
4. **轻量切入**：微功能优先（数字/日期听写、分句听写、跟读复述），不做大而全
5. **内容运营**：题库按季度更新 + Notion/结构化题库低成本管理

## 四、License 提醒

| 项目 | License | 商用影响 |
|------|---------|---------|
| OpenPronounce | MIT | ✅ 可直接集成 |
| IELTS-Speaking-Simulator | 题库/prompt 公开，商业产品另立（JoeSpeaking） | 学思路/题库，注意不碰其商业品牌 |
| EchoLingo | PolyForm Noncommercial | 只能学思路，商用需授权 |
| FreeLingo | AGPL-3.0 | copyleft，可商用授权；改后分发需开源 |
| speechocean762 | 语料（研究用） | 用于自校准 |
