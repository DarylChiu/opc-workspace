"""
视频分析交互Workflow — Prompt 模板
融合 MVP 深度分析架构：脚本解析 + 镜头语言&声音
"""
import json

# ═══════════════════════════════════════════
# Prompt 1: 内容总览（保持）
# ═══════════════════════════════════════════
OVERVIEW_PROMPT = """你是一个专业的视频内容分析师。请分析以下视频转写文本，提取关键信息。

## 输入：视频转写文本（含时间戳）
{transcript}

## 请用 JSON 格式输出以下字段：
{{
  "oneLiner": "一句话总结这个视频的核心内容和价值主张（30字以内）",
  "audience": "目标受众画像（谁会对这个内容感兴趣）",
  "painPoints": "视频试图解决的受众痛点（1-2句话）",
  "viewpoint": "视频传达的核心观点或立场",
  "cognition": "看完视频后观众的认知变化——从什么变成了什么"
}}

只输出 JSON，不要其他内容。"""

# ═══════════════════════════════════════════
# Prompt 2: 脚本解析（替换原"结构拆解"）—— MVP 风格四幕分析
# ═══════════════════════════════════════════
SCRIPT_ANALYSIS_PROMPT = """你是一个专业的短剧/短视频脚本分析师。请对以下视频转写文本进行深度的脚本结构解析，风格接近专业分镜头剧本分析。

## 输入：视频转写文本（含时间戳）
{transcript}

## 分析维度：

### 1. 叙事结构（acts）
将内容拆解为 3-5 个叙事段落（幕/act）。每个段落需包含：
- act: 幕序号
- name: 段落名称（如"第一幕：Hook建立"、"第二幕：冲突升级"）
- timeRange: 时间范围（如 "00:00-00:45"）
- narrativeFunction: 这个段落的叙事功能是什么（建立关系？制造冲突？身份反转？）
- characterDynamics: 人物关系或情绪动态变化
- dramaticTension: 戏剧张力等级（1-10，10最高）
- keyMoments: 这个段落中的 2-4 个关键对白/情节节点，每个包含 timestamp 和描述

### 2. 情绪曲线（emotionCurve）
描述全片的情绪走向，用文字描述从开头到结尾的情绪变化轨迹。

### 3. 叙事技巧（techniques）
列出这个视频用到的 2-3 个核心叙事技巧，每个说明在哪段使用、产生了什么效果。

## 输出 JSON：
{{
  "acts": [
    {{
      "act": 1,
      "name": "第一幕：...",
      "timeRange": "00:00-00:45",
      "narrativeFunction": "...",
      "characterDynamics": "...",
      "dramaticTension": 3,
      "keyMoments": [
        {{"ts": "00:03", "desc": "..."}},
        {{"ts": "00:15", "desc": "..."}}
      ]
    }}
  ],
  "emotionCurve": "...",
  "techniques": [
    {{"name": "技巧名", "usage": "使用位置和方式", "effect": "产生的效果"}}
  ]
}}

重要：
- 严格基于原文内容分析，不要编造不存在的对话
- 段落划分要合理，每个幕有明确的叙事功能
- 情绪曲线要具体，不要泛泛而谈

只输出 JSON，不要其他内容。"""

# ═══════════════════════════════════════════
# Prompt 3: 复刻模板（保持并增强）
# ═══════════════════════════════════════════
TEMPLATE_PROMPT = """你是一个专业的爆款内容模板提取专家。请分析以下视频转写文本，提取可复用的内容模板和创作者可复用元素。

## 输入：视频转写文本（含时间戳）
{transcript}

## 任务：

### 1. 复刻模板（templates，2-3个）
每个模板包含：
- name: 模板名称（如"开头公式：身份反转"）
- desc: 模板用途和适用场景
- formula: 模板公式，用【占位符】标记可替换部分

### 2. 可复用元素（reusableElements）
- scriptPattern: 脚本模式——这个视频的故事结构可以怎么套用？
- hookTechnique: Hook 技巧——开头是怎么抓住注意力的？
- topicAngle: 话题切入点——为什么这个话题能引起共鸣？
- viralFactors: 爆款因素（2-3条）——为什么这个内容容易传播？

## 输出 JSON：
{{
  "templates": [
    {{
      "name": "...",
      "desc": "...",
      "formula": "..."
    }}
  ],
  "reusableElements": {{
    "scriptPattern": "...",
    "hookTechnique": "...",
    "topicAngle": "...",
    "viralFactors": ["...", "..."]
  }}
}}

重要：
- 模板必须基于原文内容抽取
- 【占位符】用中文命名
- 可复用元素要具体，能指导创作

只输出 JSON，不要其他内容。"""

# ═══════════════════════════════════════════
# Prompt 4: 镜头语言&声音分析（替换原"知识卡"）—— MVP 风格
# ═══════════════════════════════════════════
CINEMATOGRAPHY_PROMPT = """你是一个专业的影视制作分析师。请基于以下视频转写文本，推断可能的镜头语言、声音设计和导演风格。

## 输入：视频转写文本（含时间戳）
{transcript}

## ⚠️ 重要提示
你的分析基于对白文本推断，而非实际画面。请在分析中体现推理过程（"从对话节奏推断..."），不要断言画面细节。

## 分析维度：

### 1. 镜头语言推断（cinematography）
基于对白内容、节奏和情绪，推断可能的：
- shotTypes: 各段落可能使用的景别及其叙事功能（如"高潮段落的密集短句→推测使用近景/特写增强压迫感"）
- composition: 可能的构图策略（如"对话中身份对等→推测使用平衡双人构图"）
- cameraMovement: 可能的摄影机运动（如"情绪爆发段→推测手持晃动增强紧张感"）

### 2. 光线与色彩推断（lightingColor）
- lightingMood: 基于内容基调推断光线风格
- colorPalette: 基于情绪走向推断色彩策略
- visualRhythm: 基于对白节奏推断视觉节奏

### 3. 声音设计分析（soundDesign）
- bgm: 基于内容推断是否需要BGM、可能风格
- ambient: 环境音推断
- dialogueStyle: 对白风格分析（口语化程度、节奏、语气变化）
- subtitleDesign: 字幕设计推断

### 4. 导演风格推断（directorStyle）
- aesthetic: 美学取向（纪实/唯美/实验等）
- narrativeSignature: 叙事签名——这个创作者可能有什么标志性手法
- culturalEncoding: 文化编码——文本中隐含的文化符号和语境

## 输出 JSON：
{{
  "cinematography": {{
    "shotTypes": "...",
    "composition": "...",
    "cameraMovement": "..."
  }},
  "lightingColor": {{
    "lightingMood": "...",
    "colorPalette": "...",
    "visualRhythm": "..."
  }},
  "soundDesign": {{
    "bgm": "...",
    "ambient": "...",
    "dialogueStyle": "...",
    "subtitleDesign": "..."
  }},
  "directorStyle": {{
    "aesthetic": "...",
    "narrativeSignature": "...",
    "culturalEncoding": "..."
  }},
  "disclaimer": "⚠️ 本分析基于对白文本推断，未使用实际画面帧。如需精确的镜头语言分析，请提供视频文件。"
}}

只输出 JSON，不要其他内容。"""

# ═══════════════════════════════════════════
# Prompt 5: 三项评分（保持）
# ═══════════════════════════════════════════
SCORING_PROMPT = """你是一个专业的视频内容质量评审。请对以下视频转写文本进行三项评分。

## 输入：视频转写文本（含时间戳）
{transcript}

## 评分维度（每项 0-100 分）：
1. hook: Hook 设计得分——开场是否足够吸引人？是否建立期待？
2. structure: 结构设计得分——叙事逻辑是否清晰？段落过渡是否自然？
3. expression: 表达效果得分——语言是否口语化？是否有记忆点？

## 输出 JSON：
{{
  "hook": {{ "value": 85, "reason": "评分理由（1句话）" }},
  "structure": {{ "value": 82, "reason": "评分理由（1句话）" }},
  "expression": {{ "value": 78, "reason": "评分理由（1句话）" }}
}}

只输出 JSON，不要其他内容。"""


def format_transcript(transcript_data: list) -> str:
    """将转写数据格式化为 Prompt 输入文本"""
    lines = []
    for item in transcript_data:
        tag = item.get("tag", "")
        tag_str = f" [{tag}]" if tag else ""
        lines.append(f"[{item['ts']}]{tag_str} {item['text']}")
    return "\n".join(lines)


# 所有 Prompt 注册表
PROMPTS = {
    "overview": OVERVIEW_PROMPT,
    "script_analysis": SCRIPT_ANALYSIS_PROMPT,
    "template": TEMPLATE_PROMPT,
    "cinematography": CINEMATOGRAPHY_PROMPT,
    "scoring": SCORING_PROMPT,
}
