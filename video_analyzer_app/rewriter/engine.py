"""
M2 洗稿重构器 · 5步缝合工艺引擎
输入：内核卡 + 目标设定 → 输出：新定向短剧脚本
"""
import json, re, hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

WORKSPACE = Path(__file__).parent.parent
CARD_DIR = WORKSPACE / "kernel_output"
OUTPUT_DIR = WORKSPACE / "rewriter_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════
# 数据模型
# ══════════════════════════════════════════════

@dataclass
class TargetConfig:
    """目标设定：用户想把内核嫁接到什么新作品"""
    new_ip_name: str = "新短剧"
    new_style: str = "都市爱情"  # e.g. 王家卫/日系清新/韩系唯美/市井喜剧
    new_setting: str = "现代都市"
    new_era: str = "2020s"
    character_map: dict = field(default_factory=dict)  # {原角色名: 新角色名+身份}
    scene_map: dict = field(default_factory=dict)       # {原场景: 新场景}
    tone_shift: str = "保持原内核"  # 保持/强化/反转
    extra_notes: str = ""


@dataclass
class RewrittenBeat:
    """重构后的单个节拍"""
    beat_id: str
    original_name: str
    new_name: str
    narrative_slot: str
    coupling_degree: str
    provenance: dict
    # 替换后的内容
    new_characters: list = field(default_factory=list)
    new_setting: str = ""
    new_dialogue_hint: str = ""       # 对白方向
    new_action_hint: str = ""         # 动作/调度方向
    new_psychological_mechanism: str = ""  # 心理机制（保留或微调）


@dataclass
class TransitionNote:
    """场景间的接缝转调提示"""
    from_beat: str
    to_beat: str
    bgm_suggestion: str = ""
    pace_shift: str = ""      # 加速/减速/停顿
    visual_shift: str = ""    # 画面风格切换提示
    emotion_bridge: str = ""  # 情绪过渡


@dataclass
class RewrittenScript:
    """最终产出的新定向脚本"""
    target: TargetConfig
    source_card_name: str = ""
    motif_statement: str = ""           # M2b: 新母题声明
    structure_skeleton: list = field(default_factory=list)  # M2c: 结构骨架
    pivotal_scenes: list = field(default_factory=list)      # M2d: 枢纽场景
    transitions: list = field(default_factory=list)         # M2e: 接缝转调
    theme_closure: str = ""             # M2e: 主题闭环
    full_script: str = ""               # M2f: 完整脚本


# ══════════════════════════════════════════════
# 核心引擎
# ══════════════════════════════════════════════

class RewriterEngine:
    def __init__(self, target: TargetConfig):
        self.target = target
        self.card = None
        self.script = RewrittenScript(target=target)

    def load_kernel_card(self) -> dict:
        """加载最新内核卡"""
        cards = sorted(CARD_DIR.glob("*.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        if not cards:
            raise FileNotFoundError("无内核卡，先跑 M1 内核提取器")
        self.card = json.loads(cards[0].read_text())
        self.script.source_card_name = cards[0].name
        return self.card

    # ─── M2b: 母题锚定 ───
    def anchor_motif(self) -> str:
        """
        从内核卡 L3 提取核心母题 → 匹配到目标设定 → 生成新母题声明
        """
        L3 = self.card.get("L3_resonance_engine", {})
        dilemma = L3.get("core_existential_dilemma", "")
        needs = L3.get("tapped_needs_fears", [])
        L0 = self.card.get("L0_source", {})

        # 构造新母题声明
        original = f"原母题：{dilemma}"
        triggered = f"触及需求：{', '.join(needs[:3])}" if needs else ""
        transplant = f"嫁接目标：{self.target.new_ip_name} · {self.target.new_style} · {self.target.new_setting}"

        tone = self.target.tone_shift
        if tone == "保持原内核":
            adaptation = f"母题不变，表层参数替换为{self.target.new_setting}背景"
        elif tone == "强化":
            adaptation = f"强化{dilemma[:20]}...的情感张力，在新设定中放大冲突"
        else:
            adaptation = f"反转母题方向，从{dilemma[:20]}...转向反向表达"

        statement = f"""## 新母题声明

{original}
{triggered}
{transplant}

**适配策略**：{adaptation}

**核心母题**：在{self.target.new_setting}的背景下，{dilemma}
"""
        self.script.motif_statement = statement
        return statement

    # ─── M2c: 结构嫁接 ───
    def graft_structure(self) -> list:
        """
        取 L5 节拍依赖链 → 保持依赖拓扑不变 → 替换节点内容
        """
        L5 = self.card.get("L5_beat_library", {})
        beats = L5.get("beats", [])
        chains = (L5.get("dependency_graph", {}) or {}).get("chains", [])

        grafted = []
        for b in beats:
            rw = RewrittenBeat(
                beat_id=b.get("id", ""),
                original_name=b.get("name", ""),
                new_name=self._rename_beat(b),
                narrative_slot=b.get("narrative_slot", ""),
                coupling_degree=b.get("coupling_degree", ""),
                provenance=b.get("provenance", {}),
            )
            # 替换角色
            if b.get("replaceable_params"):
                rp = b["replaceable_params"]
                old_char = rp.get("character", "")
                new_char = self.target.character_map.get(old_char, self._gen_new_character(old_char))
                rw.new_characters = [new_char]
                rw.new_setting = self.target.scene_map.get(
                    rp.get("setting", ""),
                    self._gen_new_setting(rp.get("setting", ""))
                )
            else:
                rw.new_setting = self.target.new_setting

            # 保留心理机制
            rw.new_psychological_mechanism = b.get("psychological_mechanism", "")

            # 对白/动作方向
            rw.new_dialogue_hint = self._gen_dialogue_hint(b)
            rw.new_action_hint = self._gen_action_hint(b)

            grafted.append(rw)

        self.script.structure_skeleton = [asdict(g) for g in grafted]

        # 依赖链不变，但节点名更新
        updated_chains = []
        for c in chains:
            new_beats = []
            for bid in c.get("beats", []):
                gb = next((g for g in grafted if g.beat_id == bid), None)
                new_beats.append(gb.new_name if gb else bid)
            updated_chains.append({
                "name": c.get("name", ""),
                "beats": new_beats,
                "invariant_reason": c.get("invariant_reason", ""),
            })
        self.script.structure_skeleton.append({"dependency_chains": updated_chains})

        return grafted

    # ─── M2d: 枢纽场景复刻 ───
    def recreate_pivotal_scenes(self, grafted_beats: list) -> list:
        """
        选 2-3 个关键节拍（setup → turn → payoff）
        保留叙事功能和心理机制 → 替换表层 → 生成对白草稿
        """
        pivotal = []
        # 按 narrative_slot 优先级选
        priority = {"setup": 1, "turn": 2, "payoff": 3, "develop": 4, "coda": 5}
        candidates = sorted(
            [b for b in grafted_beats if b.narrative_slot in priority],
            key=lambda x: priority.get(x.narrative_slot, 99)
        )

        selected = candidates[:min(3, len(candidates))]

        for beat in selected:
            scene = self._build_pivotal_scene(beat)
            pivotal.append(scene)

        self.script.pivotal_scenes = pivotal
        return pivotal

    # ─── M2e: 接缝转调 + 主题闭环 ───
    def modulate_transitions(self, grafted_beats: list) -> list:
        """相邻场景间生成转调提示"""
        transitions = []
        for i in range(len(grafted_beats) - 1):
            curr = grafted_beats[i]
            nxt = grafted_beats[i + 1]

            # 根据 slot 变化决定节奏
            pace = "加速"
            if curr.narrative_slot == "turn" and nxt.narrative_slot == "payoff":
                pace = "减速 · 给情绪沉淀空间"
            elif curr.narrative_slot == "develop" and nxt.narrative_slot == "turn":
                pace = "停顿 · 转折前蓄力"
            elif curr.coupling_degree == "tight" and nxt.coupling_degree == "tight":
                pace = "平稳过渡 · 紧密衔接"

            transitions.append(asdict(TransitionNote(
                from_beat=curr.new_name,
                to_beat=nxt.new_name,
                bgm_suggestion=self._gen_bgm_hint(curr, nxt),
                pace_shift=pace,
                visual_shift=f"从{self._slot_visual(curr.narrative_slot)}过渡到{self._slot_visual(nxt.narrative_slot)}",
                emotion_bridge=f"{curr.new_psychological_mechanism[:20]}... → {nxt.new_psychological_mechanism[:20]}...",
            )))

        self.script.transitions = transitions

        # 主题闭环：开头→结尾的回声
        if grafted_beats:
            first = grafted_beats[0]
            last = grafted_beats[-1]
            self.script.theme_closure = self._build_theme_closure(first, last)

        return transitions

    # ─── M2f: 端到端串联 → 完整脚本 ───
    def assemble_full_script(self):
        """把所有部分缝合成完整的新定向脚本 Markdown"""
        parts = []
        parts.append(f"# {self.target.new_ip_name}")
        parts.append(f"**风格**: {self.target.new_style} | **设定**: {self.target.new_setting} | **年代**: {self.target.new_era}")
        parts.append(f"**内核来源**: {self.script.source_card_name}")
        parts.append(f"\n---\n")

        # 母题声明
        parts.append(self.script.motif_statement)
        parts.append("\n---\n")

        # 结构骨架
        parts.append("## 叙事结构骨架（依赖拓扑保持不变）")
        grafted = self._get_grafted_beats()
        for b in grafted:
            prov = b.get("provenance", {})
            src = prov.get("source_work", "") if prov else ""
            parts.append(
                f"### {b['new_name']} [{b['narrative_slot']} · {b['coupling_degree']}]\n"
                f"- 原参考: {b['original_name']} ← {src}\n"
                f"- 新角色: {', '.join(b.get('new_characters',[]))}\n"
                f"- 新场景: {b.get('new_setting','')}\n"
                f"- 心理机制: {b.get('new_psychological_mechanism','')}\n"
                f"- 对白方向: {b.get('new_dialogue_hint','')}\n"
                f"- 动作方向: {b.get('new_action_hint','')}\n"
            )

        parts.append("\n---\n")

        # 依赖链
        for item in self.script.structure_skeleton:
            if "dependency_chains" in item:
                parts.append("## 🔗 依赖链（锁死顺序不变）")
                for chain in item["dependency_chains"]:
                    chain_str = " → ".join(chain["beats"])
                    parts.append(f"- **{chain['name']}**: {chain_str}\n  _{chain['invariant_reason']}_\n")

        parts.append("\n---\n")

        # 枢纽场景
        if self.script.pivotal_scenes:
            parts.append("## 🎬 枢纽场景（对白草稿）")
            for i, scene in enumerate(self.script.pivotal_scenes, 1):
                parts.append(f"### 场景{i}: {scene.get('scene_title','')}")
                parts.append(f"- 角色: {scene.get('characters','')}")
                parts.append(f"- 地点: {scene.get('setting','')}")
                parts.append(f"- 叙事功能: {scene.get('narrative_function','')}")
                parts.append(f"\n{scene.get('dialogue_draft','')}\n")

        parts.append("\n---\n")

        # 接缝转调
        if self.script.transitions:
            parts.append("## 🎵 场景间转调提示")
            for t in self.script.transitions:
                t_src = t.get("transition") or f"{t.get('from_beat','')} → {t.get('to_beat','')}"
                parts.append(
                    f"### {t_src}\n"
                    f"- BGM: {t.get('bgm_suggestion','')}\n"
                    f"- 节奏: {t.get('pace_shift','')}\n"
                    f"- 画面: {t.get('visual_shift','')}\n"
                    f"- 情绪桥: {t.get('emotion_bridge','')}\n"
                )

        parts.append("\n---\n")

        # 主题闭环
        if self.script.theme_closure:
            parts.append("## 🔄 主题闭环")
            parts.append(self.script.theme_closure)

        full = "\n".join(parts)
        self.script.full_script = full
        return full

    def run_full_pipeline(self):
        """执行完整 M2 管线"""
        self.load_kernel_card()
        self.anchor_motif()
        grafted = self.graft_structure()
        self.recreate_pivotal_scenes(grafted)
        self.modulate_transitions(grafted)
        script = self.assemble_full_script()

        # 保存
        slug = re.sub(r'[^\w]', '_', self.target.new_ip_name)[:30]
        out_path = OUTPUT_DIR / f"rewritten_{slug}.md"
        out_path.write_text(script)
        print(f"✅ 脚本已保存: {out_path}")

        return {
            "motif_statement": self.script.motif_statement,
            "beats_rewritten": len(grafted),
            "pivotal_scenes": len(self.script.pivotal_scenes),
            "transitions": len(self.script.transitions),
            "output_path": str(out_path),
            "script": script,
            # 结构化数据供 UI 分段渲染
            "structure_skeleton": self.script.structure_skeleton,
            "pivotal_scenes_data": self.script.pivotal_scenes,
            "transitions_data": self.script.transitions,
            "theme_closure": self.script.theme_closure,
        }

    # ══════════════════════════════════════
    # 内部工具方法
    # ══════════════════════════════════════

    def _get_grafted_beats(self):
        for item in self.script.structure_skeleton:
            if isinstance(item, dict) and "beat_id" in item:
                yield item
        # from list of RewrittenBeat-like dicts
        for item in self.script.structure_skeleton:
            if isinstance(item, dict) and "beat_id" in item:
                yield item
            elif isinstance(item, list):
                for sub in item:
                    if isinstance(sub, dict) and "beat_id" in sub:
                        yield sub

    def _rename_beat(self, beat: dict) -> str:
        """给节拍取新名字：原功能不变，替换场景/角色元素"""
        name = beat.get("name", "")
        rp = beat.get("replaceable_params", {})
        if rp:
            old_setting = rp.get("setting", "")
            new_setting = self.target.scene_map.get(old_setting, self._gen_new_setting(old_setting))
            # 尝试替换场景词
            if old_setting and new_setting and old_setting in name:
                name = name.replace(old_setting, new_setting)
            else:
                name = f"{new_setting}·{name}"
        return f"[{self.target.new_setting}] {name}"

    def _gen_new_character(self, old: str) -> str:
        """根据目标风格生成新角色名"""
        style = self.target.new_style
        if "日系" in style:
            return f"{self.target.new_ip_name}の{old}" if old else f"角色A"
        elif "韩系" in style:
            return f"{self.target.new_ip_name}·{old}" if old else f"角色A"
        return old if old else "角色A"

    def _gen_new_setting(self, old: str) -> str:
        s = self.target.new_setting
        if "茶餐厅" in old:
            return "咖啡馆" if "日系" in self.target.new_style else s
        elif "街头" in old:
            return "街道" if "日系" in self.target.new_style else s
        elif "便利店" in old:
            return "便利店"  # 便利店是通用的
        return s if s else old

    def _gen_dialogue_hint(self, beat: dict) -> str:
        style = self.target.new_style
        if "日系" in style:
            return "含蓄留白·少说多暗示·用环境音代替直接表达"
        elif "韩系" in style:
            return "情绪外露·对话中穿插回忆杀·停顿+眼神"
        elif "王家卫" in style:
            return "碎片化独白·市井口语·重复变奏"
        return "保留原对白节奏·替换表层词汇"

    def _gen_action_hint(self, beat: dict) -> str:
        return f"保留原调度逻辑，替换为{self.target.new_setting}语境下的等价动作"

    def _build_pivotal_scene(self, beat) -> dict:
        """为一个枢纽节拍生成对白草稿"""
        prov = beat.provenance or {}
        src = prov.get("source_work", "")
        chars = beat.new_characters or ["角色A", "角色B"]
        setting = beat.new_setting or self.target.new_setting
        slot = beat.narrative_slot
        mech = beat.new_psychological_mechanism or ""

        # 根据 narrative_slot 生成对白骨架
        dialogue_templates = {
            "setup": (
                f"[{setting} · 日/夜]\n"
                f"{chars[0]}正在做一件事，{chars[1] if len(chars)>1 else '另一角色'}出现。\n\n"
                f"**{chars[0]}**: （{mech[:30]}...）\n\n_——此处保留原节拍的情绪节奏，替换具体台词。_\n"
                f"参考: {beat.original_name} ← {src}"
            ),
            "turn": (
                f"[{setting} · 关键时刻]\n"
                f"气氛骤变。{chars[0]}和{chars[1] if len(chars)>1 else '对方'}之间的张力达到顶点。\n\n"
                f"**{chars[0]}**: （打破沉默/爆发的台词）\n"
                f"**{chars[1] if len(chars)>1 else '对方'}**: （回应·对视·停顿）\n\n"
                f"_——此处是叙事转折点，需保留原节拍的 coupling_degree=({beat.coupling_degree})。_\n"
                f"心理机制: {mech}\n参考: {beat.original_name} ← {src}"
            ),
            "payoff": (
                f"[{setting} · 尾声]\n"
                f"情绪释放。{chars[0]}做出了选择。\n\n"
                f"**{chars[0]}**: （收束的台词·呼应开头）\n\n"
                f"_——此处形成情绪收束。_\n"
                f"参考: {beat.original_name} ← {src}"
            ),
        }

        return {
            "scene_title": f"{beat.new_name} [{slot}]",
            "characters": ", ".join(chars),
            "setting": setting,
            "narrative_function": f"{slot} · {beat.coupling_degree}",
            "dialogue_draft": dialogue_templates.get(slot, dialogue_templates["setup"]),
        }

    def _gen_bgm_hint(self, curr, nxt) -> str:
        style = self.target.new_style
        return f"从{curr.narrative_slot}节奏 → {nxt.narrative_slot}节奏 · {style}风格配乐"

    def _slot_visual(self, slot: str) -> str:
        return {"setup": "建立基调", "develop": "推进叙事", "turn": "转折高潮",
                "payoff": "情感释放", "coda": "余韵收尾"}.get(slot, "叙事推进")

    def _build_theme_closure(self, first, last) -> str:
        return (
            f"**开场**: {first.new_name} — 将观众引入{self.target.new_setting}的世界\n"
            f"**收尾**: {last.new_name} — 回应开场的母题，形成闭环\n"
            f"**回声手法**: 重复开场的第一句台词或第一个画面元素，但在新语境中赋予不同含义\n"
        )


# ══════════════════════════════════════════════
# 便捷入口
# ══════════════════════════════════════════════

def run_rewrite(target: TargetConfig) -> dict:
    engine = RewriterEngine(target)
    return engine.run_full_pipeline()


# ── 预设模板 ──
PRESET_TARGETS = {
    "日系纯爱": TargetConfig(
        new_ip_name="东京恋爱物语",
        new_style="日系清新",
        new_setting="东京·下北泽",
        new_era="2020s",
        character_map={"失恋男子": "山田健太", "茶餐厅老板": "咖啡馆マスター"},
        scene_map={"港式茶餐厅": "昭和风纯喫茶", "香港街头": "下北泽商店街", "便利店": "コンビニ"},
        tone_shift="保持原内核",
        extra_notes="保留志明与春娇的市井感，转化为日式纯爱语境",
    ),
    "韩系唯美": TargetConfig(
        new_ip_name="首尔恋爱日记",
        new_style="韩系唯美",
        new_setting="首尔·弘大",
        new_era="2020s",
        character_map={"失恋男子": "朴志浩", "茶餐厅老板": "路边摊阿姨"},
        scene_map={"港式茶餐厅": "路边포장마차", "香港街头": "弘大街头", "便利店": "GS25便利店"},
        tone_shift="强化",
        extra_notes="放大情绪冲突，加重回忆闪回",
    ),
    "王家卫续作": TargetConfig(
        new_ip_name="重庆森林·续",
        new_style="王家卫",
        new_setting="香港·2026",
        new_era="2026",
        character_map={},
        scene_map={"港式茶餐厅": "茶餐厅", "香港街头": "弥敦道", "便利店": "7-Eleven"},
        tone_shift="保持原内核",
        extra_notes="保持王家卫风格，市井对白+独白+跟拍",
    ),
}
