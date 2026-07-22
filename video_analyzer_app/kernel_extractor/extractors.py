#!/usr/bin/env python3
"""内核提取器 · DeepSeek V4 Pro 调用底座 + L0-L5 分层提取
Daryl决策: L2-L5 每层独立LLM调用, 暂统一 deepseek-v4-pro (=api.deepseek.com deepseek-chat)
"""
import os, json, re, urllib.request

DEEPSEEK_KEY = open(os.path.expanduser("~/.openclaw/auth/deepseek/api.key")).read().strip()
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"  # DeepSeek V4 Pro 线上模型

def ds_call(system_prompt: str, user_content: str, max_tokens=4096, temperature=0.3) -> dict:
    """调用 DeepSeek, 期望返回 JSON。自动剥 markdown code block。"""
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(DEEPSEEK_URL, data=body,
        headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
    usage = resp.get("usage", {})
    text = resp["choices"][0]["message"]["content"]
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {"_parse_error": True, "_raw": text[:500]}
    return {"data": data, "usage": usage}


# ══════════════════════════════════════════════════════════════
# 各层 system prompt
# ══════════════════════════════════════════════════════════════

SYS_L0_L1 = """你是资深影视结构分析师。基于给定的视频逐镜头分析材料，提取【L0源信息】和【L1叙事骨骼】。
只输出JSON:
{
 "L0_source": {"title","director","type","era","culture_context","genre","medium","duration","language"},
 "L1_narrative_skeleton": {
   "hero_journey_phase":"坎贝尔英雄之旅阶段(启程/启蒙/归来)",
   "plot_beats":[{"label":"引发事件/升级/危机/高潮/解决","timestamp":"","description":""}],
   "time_structure":"线性/倒叙/循环/闪回",
   "emotional_arc_shape":"6种情感曲线之一:上升/下降/落坑爬出/伊卡洛斯/灰姑娘/俄狄浦斯",
   "pov":"叙事视角"
 }
}
不确定的字段填"未知",不要编造。"""

SYS_L2 = """你是荣格分析心理学 + 影视人物学专家。提取【L2人物心理动力】。
关键: 人物原型不是性格标签,是心理动力模式;要挖出"表面欲望vs真正需求"的落差,以及原型间的冲突张力。
只输出JSON:
{
 "L2_characters": {
   "characters":[{
     "name","jung_archetype":"英雄/愚者/恋人/孤儿/探索者/智者/统治者/照顾者/破坏者/创造者...",
     "archetype_conflict":"如 愚者vs英雄——两个原型的张力如何驱动人物行为",
     "surface_want":"角色说ta想要什么",
     "deep_need":"角色实际需要什么(ta自己可能不自知)",
     "core_fear":"最深层恐惧",
     "arc":{"start":"起点状态","catalyst":"转变催化剂","end":"终点:改变了什么"}
   }],
   "inter_character_dynamic":"角色间力量关系(互补/对抗/镜像/救赎)及随情节变化"
 }
}
必须基于材料证据,深度要够,不要泛泛。"""

SYS_L3 = """你是电影学者 + 深层心理学家(融荣格/弗洛伊德/亚里士多德诗学/列维-斯特劳斯结构人类学)。
这是最核心的一层。你要回答: 这个故事究竟触动了人类的哪种深层心理? 为什么跨文化有效? 观众带走了什么?
铁律: 存在困境必须是"无解的悖论"(有解=说教肤浅,无解=有深度)。认知更新必须是"关于观众自己的真相",不是"学到的道理"。
只输出JSON:
{
 "L3_resonance_engine": {
   "tapped_needs_fears":["归属/认同/安全/自由/意义/死亡/自主/联结..."],
   "core_existential_dilemma":"无解悖论一句话",
   "mytheme_opposition":{"binary":"二元对立如 安定vs成长","mediation":"故事如何调解/反转这组对立"},
   "katharsis":{"aroused_emotions":["怜悯/恐惧/..."],"release_path":"角色牺牲→观众释放的机制","cognitive_update":"观众看清了____(关于自己的真相)"},
   "drive_tension":{"eros":"生本能/爱/联结如何表现","thanatos":"死本能/分离/消逝如何表现","dynamic":"两者拉锯如何构成叙事动力"}
 }
}
深度是这一层的生命线。用你最强的推理。"""

SYS_L4 = """你是电影语言学 + 视听语法专家。提取【L4电影语法编码】——共鸣是怎样被镜头/空间/时间/声音/身体语言编码出来的。
铁律: 每个判断必须落到具体证据(时间点),不许泛泛说"港式风情"。
只输出JSON:
{
 "L4_cinematic_grammar": {
   "visual_metaphors":[{"image":"反复意象","psychological_meaning":"心理符号含义","evidence_timestamps":[""]}],
   "spatial_coding":[{"space":"空间名","emotional_tag":"情绪标签","camera_style":"景别/运镜/光色"}],
   "temporal_coding":"节奏如何制造情绪",
   "sound_coding":{"bgm_logic":"BGM选择逻辑+切换点功能","ambient_sound_function":"环境音情绪功能"},
   "body_action_encoding":[{"action":"关键动作","symbolism":"象征意义"}]
 }
}"""

SYS_L5 = """你是叙事结构 + 戏剧构作(dramaturgy)专家。提取【L5桥段节拍库】——本项目最难的一层。
核心认知(必须贯彻): 桥段功能是【位置性】的,同一个母题在不同叙事位置=不同beat。例:"便利店买烟"(setup铺垫)和"地铁口点烟"(payoff结缘)不能对调,因为Setup必须先于Payoff(契诃夫之枪)。
你必须标出: ①每个beat的叙事位置槽和位置性功能 ②依赖关系(前置/使能beat) ③缝合耦合度(tight硬缝顺序锁定/loose软接可移动/medium) ④溯源级别。
只输出JSON:
{
 "L5_beat_library": {
   "beats":[{
     "id":"beat_000","name","motif":"母题/物件",
     "narrative_slot":"setup/develop/turn/payoff/coda",
     "positional_function":"该位置上做的叙事/心理工作(位置性,非静态标签)",
     "psychological_mechanism":"为什么这个位置有效",
     "dependencies":{"prerequisite_beats":["前置beat_id"],"enabling_beats":["被开启的beat_id"]},
     "coupling_degree":"tight/loose/medium",
     "emotion_target":"要制造的观众情绪",
     "provenance":{"level":"复刻/同构/联想","source_work":"出处","evidence":"本片对应证据+时间点"},
     "replaceable_params":{"character":"","setting":"","era":"","visual_style":""}
   }],
   "dependency_graph":{"chains":[{"name":"如 买烟→点烟","beats":["有序beat_id"],"invariant_reason":"顺序为何不可乱"}]}
 }
}
先给每个beat编id,再在dependency_graph里用id串依赖链。这一层的价值全在依赖拓扑和位置性功能上。"""


LAYER_SYS = {"L0_L1": SYS_L0_L1, "L2": SYS_L2, "L3": SYS_L3, "L4": SYS_L4, "L5": SYS_L5}
