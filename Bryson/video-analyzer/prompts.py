"""
视频分析交互Workflow V3 — Prompt 模板
架构: Gemini 原生视频（转写+视觉）→ DeepSeek 文本分析
"""

# ═══════════════════════════════════════════
# V3 核心: Gemini 原生视频一站式分析
# ═══════════════════════════════════════════
GEMINI_VIDEO_ANALYSIS_V3 = """你是一个顶级的短视频分析师。请完整分析这段视频，返回精确的 JSON。

## 任务 1: 完整转写 (transcript)
结合画面和音频，逐句转写全部对白和旁白:
- 每句标注时间戳 MM:SS
- 标注说话者（男声/女声/旁白/画外音等）
- 听不清的标注 [听不清]
- 不要遗漏背景音中的对白

## 任务 2: 场景分解 (scenes)
将视频按叙事节奏拆为 3-6 个场景，每个:
- sceneId: 场景序号
- timeRange: 时间范围 "00:00-00:30"
- location: 地点和环境
- summary: 这个场景在讲什么（30字以内）
- characters: [{role, appearance, actions}] - 角色外貌特征、动作
- dialogue: [{ts, speaker, text}] - 本场景对白摘要
- narrativeRole: 场景的叙事功能（Hook建立/冲突升级/转折/高潮/收尾等）
- tension: 戏剧张力 1-10

## 任务 3: 故事内核 (story)
- synopsis: 完整故事梗概 100-200字
- genre: 类型标签列表（搞笑/悬疑/反转/生活/教程/情感/广告/讽刺/混剪 等）
- protagonist: {role, identity, goal, obstacle}
- conflict: 核心冲突是什么
- turningPoints: [{timeEstimate, description, why}] 2-4个关键转折点
- dramaticMechanism: 幽默/戏剧机制分析（如有）

## 任务 4: 视觉&制作 (visualStyle)
直接分析你看到的画面:
- shotTypes: 景别策略（特写/近景/中景/远景的使用规律）
- cameraWork: 摄影机运动特点
- lighting: 光线氛围
- colorPalette: 色彩策略
- editing: 剪辑节奏和转场方式
- bgm: 背景音乐风格和情绪
- soundDesign: 音效使用
- productionQuality: 制作水准评估（1-10）

## 输出 JSON 格式:
{
  "transcript": [{"ts": "00:00", "speaker": "男声", "text": "..."}],
  "scenes": [
    {"sceneId": 1, "timeRange": "00:00-00:30", "location": "...", "summary": "...",
     "characters": [{"role": "主角", "appearance": "...", "actions": "..."}],
     "dialogue": [{"ts": "00:00", "speaker": "...", "text": "..."}],
     "narrativeRole": "Hook建立", "tension": 3}
  ],
  "story": {
    "synopsis": "...", "genre": ["搞笑"],
    "protagonist": {"role": "...", "identity": "...", "goal": "...", "obstacle": "..."},
    "conflict": "...",
    "turningPoints": [{"timeEstimate": "00:15", "description": "...", "why": "..."}],
    "dramaticMechanism": "..."
  },
  "visualStyle": {
    "shotTypes": "...", "cameraWork": "...", "lighting": "...",
    "colorPalette": "...", "editing": "...", "bgm": "...",
    "soundDesign": "...", "productionQuality": 7
  }
}

只输出 JSON，不要 markdown 包裹，不要任何其他文字。"""


# ═══════════════════════════════════════════
# V3 DeepSeek 文本分析 Prompts
# 注意: {{ 和 }} 是 Python .format() 转义的花括号
# ═══════════════════════════════════════════

OVERVIEW_PROMPT = """你是一个专业的视频内容分析师。基于 Gemini 的多模态分析结果，提取关键信息。

## Gemini 故事分析
{story_json}

## 完整对白文本（含时间戳）
{transcript}

## 请用 JSON 格式输出:
{{
  "oneLiner": "一句话总结视频核心内容和价值主张（30字以内）",
  "audience": "目标受众画像",
  "painPoints": "视频试图解决的受众痛点",
  "viewpoint": "视频传达的核心观点或立场",
  "cognition": "看完视频后观众的认知变化——从什么变成了什么"
}}

只输出 JSON，不要其他内容。"""


SCRIPT_ANALYSIS_PROMPT = """你是一个专业的短视频脚本分析师。基于 Gemini 的场景分解和故事分析，进行深度脚本结构解析。

## Gemini 场景分析
{scenes_json}

## Gemini 故事分析
{story_json}

## 完整对白文本（最高优先级——以原文为准）
{transcript}

## ⚠️ 分析前必须完成推理验证（不输出，但必须执行）：

### 验证1: 角色关系核实
- 对照对白原文，确认每个场景中「谁对谁做了什么」
- 如果解读中出现不符合角色身份的行为（如喜剧短片里父亲挨揍），必须质疑并纠正
- 问自己：这个动作的施动者和承受者分别是谁？是否符合剧情逻辑？

### 验证2: 动机深度挖掘
- 角色的每个行为，问：是偶然失误还是有意为之？如果是故意的，更深层的动机是什么？
- 例：「忘带作业」可能是故意的（想用「写了但忘带」搪塞老师），而非简单的疏忽
- 从对白和画面细节中寻找动机线索

### 验证3: 逻辑连贯性
- 每场戏的叙事功能是否与前后场形成因果链？
- 如果某场戏的解释存在逻辑矛盾，回溯对白寻找正确答案

## 分析维度:

### 叙事结构 (acts): 3-5幕
- name: 给每幕一个有洞察力的标题（不是简单描述，是理解内核后的命名）
- timeRange, narrativeFunction
- characterDynamics: 描述人物关系和动态变化（必须验证角色关系的正确性）
- dramaticTension(1-10)
- keyMoments: 2-4个关键节点，每个含 ts, desc, 以及为什么这个时刻重要

### 情绪曲线 (emotionCurve): 描述观众情绪如何变化

### 叙事技巧 (techniques): 2-4个，每个含 name, usage, effect

输出 JSON:
{{
  "acts": [{{"act":1,"name":"...","timeRange":"...","narrativeFunction":"...","characterDynamics":"...","dramaticTension":5,"keyMoments":[{{"ts":"00:03","desc":"..."}}]}}],
  "emotionCurve": "...",
  "techniques": [{{"name":"...","usage":"...","effect":"..."}}]
}}

只输出 JSON。"""


TEMPLATE_PROMPT = """你是一个专业的爆款内容模板提取专家。

## Gemini 故事分析
{story_json}

## Gemini 场景分析
{scenes_json}

## 完整对白文本
{transcript}

## 任务:

### 复刻模板 (templates): 2-3个
- name, desc, formula（用【占位符】标记可替换部分）

### 可复用元素 (reusableElements):
- scriptPattern, hookTechnique, topicAngle
- viralFactors: 2-3条爆款因素

输出 JSON:
{{
  "templates": [{{"name":"...","desc":"...","formula":"..."}}],
  "reusableElements": {{"scriptPattern":"...","hookTechnique":"...","topicAngle":"...","viralFactors":["...","..."]}}
}}

只输出 JSON。"""


CINEMATOGRAPHY_PROMPT = """你是一个专业的影视制作分析师。基于 Gemini 的视觉分析结果进行深度解读。

## Gemini 视觉分析
{visual_style_json}

## Gemini 故事分析
{story_json}

## 对白文本
{transcript}

## ⚠️ 分析原则：详略得当，不要平均用力

### 第一步：判断内容类型和视觉策略
- 微电影/广告片：通常镜头语言丰富，色彩/光线/构图都有设计
- 情景剧/口播/vlog：镜头语言被刻意简化以服务叙事，集中在少数几个维度发力
- 动作/特效类：剪辑节奏和摄影机运动是核心

### 第二步：识别「有分析价值的维度」
- 对当前视频，哪些维度被导演刻意运用来增强效果？→ 深挖 (150-200字)
- 哪些维度被刻意简化不分散观众注意力？→ 一句话说明即可 (30字)
- **剪辑节奏 (visualRhythm / editing)** 是通用维度，任何类型都值得分析（影响留存率）

### 第三步：逐维度输出（标注深度级别）
在输出的每个字段中，对重点维度给出充分分析，对非重点维度给出简洁判断。

## 分析维度:

### 镜头语言 (cinematography)
- shotTypes, composition, cameraMovement

### 光线与色彩 (lightingColor)
- lightingMood, colorPalette, visualRhythm

### 声音设计 (soundDesign)
- bgm, ambient, dialogueStyle, subtitleDesign

### 导演风格 (directorStyle)
- aesthetic, narrativeSignature, culturalEncoding

输出 JSON:
{{
  "_contentType": "情景剧/微电影/口播/vlog/广告/...",
  "_visualComplexity": "高/中/低",
  "_deepDims": ["剪辑节奏","BGM"],
  "_shallowDims": ["灯光","构图"],
  "cinematography": {{"shotTypes":"...","composition":"...","cameraMovement":"..."}},
  "lightingColor": {{"lightingMood":"...","colorPalette":"...","visualRhythm":"..."}},
  "soundDesign": {{"bgm":"...","ambient":"...","dialogueStyle":"...","subtitleDesign":"..."}},
  "directorStyle": {{"aesthetic":"...","narrativeSignature":"...","culturalEncoding":"..."}}
}}

只输出 JSON。"""


SCORING_PROMPT = """你是一个专业的视频内容质量评审。

## Gemini 故事分析
{story_json}

## Gemini 场景分析
{scenes_json}

## 完整对白文本
{transcript}

## 评分维度（每项 0-100 分）:
1. hook: Hook设计得分（开场是否抓人）
2. structure: 结构设计得分（叙事是否流畅）
3. expression: 表达效果得分（台词/表演/信息传递）

输出 JSON:
{{
  "hook": {{"value":85,"reason":"..."}},
  "structure": {{"value":82,"reason":"..."}},
  "expression": {{"value":78,"reason":"..."}}
}}

只输出 JSON。"""


def format_transcript(transcript_data: list) -> str:
    """将 transcript 列表格式化为对白文本"""
    lines = []
    for item in transcript_data:
        ts = item.get("ts", "")
        speaker = item.get("speaker", "")
        tag = item.get("tag", "")
        text = item.get("text", "")
        parts = []
        if speaker:
            parts.append(speaker)
        if tag:
            parts.append(f"[{tag}]")
        parts.append(text)
        lines.append(f"[{ts}] {'：'.join(p for p in parts if p) if speaker else ''.join(parts)}")
    return "\n".join(lines)


PROMPTS = {
    "overview": OVERVIEW_PROMPT,
    "script_analysis": SCRIPT_ANALYSIS_PROMPT,
    "template": TEMPLATE_PROMPT,
    "cinematography": CINEMATOGRAPHY_PROMPT,
    "scoring": SCORING_PROMPT,
}
