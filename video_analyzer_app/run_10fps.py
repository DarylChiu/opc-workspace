"""
10fps Vision 分析管线 — 高密度帧采样，单次合成
MVP 策略：先不计成本验证上限，再降本
"""
import os, sys, json, time, base64, subprocess, shutil, tempfile, urllib.request
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent
sys.path.insert(0, str(WORKSPACE))
from prompts import format_transcript

# ═══ API 配置 ═══
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
DEEPSEEK_BASE = "https://api.deepseek.com/v1/chat/completions"
OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_VISION_MODEL = "google/gemini-2.5-flash"

if not DEEPSEEK_API_KEY:
    # try to read from server.py
    import re
    sp = (WORKSPACE / "server.py").read_text()
    m = re.search(r'DEEPSEEK_API_KEY\s*=\s*os\.environ\.get\("DEEPSEEK_API_KEY",\s*"([^"]*)"\)', sp)
    if m and m.group(1): DEEPSEEK_API_KEY = m.group(1)
    m = re.search(r'OPENROUTER_API_KEY\s*=\s*os\.environ\.get\("OPENROUTER_API_KEY",\s*"([^"]*)"\)', sp)
    if m and m.group(1): OPENROUTER_API_KEY = m.group(1)

# ═══ API 调用 ═══
def call_deepseek(prompt, system="你是专业的视频分析助手。严格按JSON格式输出。", max_tokens=4096):
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role":"system","content":system},{"role":"user","content":prompt}],
        "temperature": 0.3, "max_tokens": max_tokens
    }).encode()
    req = urllib.request.Request(DEEPSEEK_BASE, data=payload,
        headers={"Authorization":f"Bearer {DEEPSEEK_API_KEY}","Content-Type":"application/json"})
    resp = urllib.request.urlopen(req, timeout=180)
    data = json.loads(resp.read())
    content = data["choices"][0]["message"]["content"].strip()
    if content.startswith("```"): content = content.split("\n",1)[1]
    if content.endswith("```"): content = content[:-3]
    return content, data.get("usage", {})

def call_gemini_vision(frames_b64, prompt, max_tokens=4096):
    content = [{"type":"text","text":prompt}]
    for img in frames_b64:
        content.append({"type":"image_url","image_url":{"url":img,"detail":"low"}})
    payload = json.dumps({
        "model": GEMINI_VISION_MODEL,
        "messages": [{"role":"system","content":"你是专业的影视画面分析师。严格按JSON输出。"},
                     {"role":"user","content":content}],
        "temperature": 0.3, "max_tokens": max_tokens
    }).encode()
    req = urllib.request.Request(OPENROUTER_BASE, data=payload,
        headers={"Authorization":f"Bearer {OPENROUTER_API_KEY}","Content-Type":"application/json",
                 "HTTP-Referer":"http://localhost:8777","X-Title":"Video Analyzer 10fps"})
    resp = urllib.request.urlopen(req, timeout=300)
    data = json.loads(resp.read())
    cr = data["choices"][0]["message"]["content"].strip()
    if cr.startswith("```"): cr = cr.split("\n",1)[1]
    if cr.endswith("```"): cr = cr[:-3]
    return cr, data.get("usage", {})

# ═══ 帧提取 ═══
def extract_frames(video_path, output_dir, fps=10):
    fd = Path(output_dir) / "frames"
    fd.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg","-i",video_path,"-vf",f"fps={fps}","-q:v","2",
        str(fd/"frame_%04d.jpg")], capture_output=True, text=True, timeout=120)
    frames = sorted(fd.glob("frame_*.jpg"))
    print(f"[EXTRACT] {fps}fps → {len(frames)} 帧")
    return frames

def image_to_base64(path):
    with open(path, "rb") as f:
        return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"

# ═══ 10fps Vision 批处理 ═══
def run_vision_10fps(frames, video_duration_s, cache_path=None, fps=10):
    """高密度帧 Vision 分析：密集帧 → 连续行为链。支持断点恢复
    fps: 采样帧率，用于计算帧间隔和 prompt 个性化
    """
    frames_b64 = [(image_to_base64(str(f)), i) for i, f in enumerate(frames)]
    total = len(frames_b64)
    BATCH = 12
    stats = {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0,"cost_usd":0.0}
    all_results = []
    last_completed_batch = -1
    
    # 尝试从缓存恢复
    if cache_path and os.path.exists(cache_path):
        try:
            cached = json.loads(open(cache_path).read())
            all_results = cached.get("frame_results", [])
            stats = cached.get("stats", stats)
            last_completed_batch = cached.get("last_batch", -1)
            print(f"[RESUME] 从缓存恢复 {len(all_results)} 帧结果 (已完成批次 {last_completed_batch+1}/{-(total//-BATCH)})")
        except Exception as e:
            print(f"[RESUME] 缓存读取失败: {e}，重新开始")

    frame_interval = video_duration_s / total if total > 0 else 0.1

    for bi in range(0, total, BATCH):
        bn = bi // BATCH + 1
        tb = (total + BATCH - 1) // BATCH
        
        # 跳过已完成的批次
        if bn <= last_completed_batch:
            continue
        
        batch_frames = frames_b64[bi:bi+BATCH]
        frame_start = bi
        frame_end = min(bi + BATCH, total) - 1
        time_start = frame_start * frame_interval
        time_end = (frame_end + 1) * frame_interval

        prompt = f"""分析以下视频帧序列（第{bn}/{tb}批，{len(batch_frames)}帧，时间 {time_start:.1f}s-{time_end:.1f}s，帧间隔 {frame_interval:.3f}s @ {fps}fps）。

⚠️ 关键指令：你不是在描述孤立图片，你是在观察一段连续视频的帧序列。请把帧与帧之间的变化理解为动作的连续过程。

⚠️ 特别注意：
- 微动作：角色手中的物品是否有错误？（如本该拿手机却拿了生蚝壳 → 醉酒导致的物品误认）
- 空间错位：角色从一个场景突然出现在另一个场景？（如从车外→冰箱内 → 误把冰箱当车门）
- 状态渐变：角色的醉酒程度如何逐帧变化？（清醒→微醺→醉酒→行为错乱）

每帧输出：
1. frameIndex: 帧序号（从{frame_start}开始）
2. timeEstimate: 估算时间（秒）
3. action: 具体动作描述（⚠️ 不只描述静态画面，要描述发生了什么——角色在做什么动作）
4. state: 角色状态（清醒/微醺/醉酒/困惑/愤怒/开心/正常）
5. anomaly: 行为是否反常？例如：角色对着错误物品做动作、走向错误方向、把烟灰缸当杯子等。如有反常，推断原因
6. perspective: 客观镜头/角色POV
7. keyObjects: 画面中的关键物品及其当前状态
8. expression: 表情与身体语言
9. shotType: 景别

## 输出JSON：
{{"frames":[
  {{"frameIndex":0,"timeEstimate":0.0,"action":"...","state":"...","anomaly":"...","perspective":"...","keyObjects":"...","expression":"...","shotType":"..."}}
]}}
只输出JSON，不要其他内容。"""

        try:
            raw, usage = call_gemini_vision([fb[0] for fb in batch_frames], prompt)
            r = json.loads(raw)
            if "frames" in r:
                # 修正 frameIndex
                for i, frm in enumerate(r["frames"]):
                    frm["frameIndex"] = frame_start + i
                    frm["timeEstimate"] = round((frame_start + i) * frame_interval, 1)
                all_results.extend(r["frames"])

            pt = usage.get("prompt_tokens", 0)
            ct = usage.get("completion_tokens", 0)
            tt = usage.get("total_tokens", 0)
            cost = (pt * 0.30 + ct * 2.50) / 1_000_000
            for k, v in [("prompt_tokens", pt), ("completion_tokens", ct), ("total_tokens", tt)]:
                stats[k] += v
            stats["cost_usd"] += cost
            print(f"  [Vision {bn}/{tb}] {len(batch_frames)}帧 → {tt}t, ${cost:.5f} | 累计 ${stats['cost_usd']:.5f}")
            # 每批完成后保存缓存
            if cache_path:
                try:
                    with open(cache_path, "w") as cf:
                        json.dump({"frame_results": all_results, "stats": stats, "last_batch": bn}, cf, ensure_ascii=False)
                except Exception as e:
                    print(f"  [CACHE WARN] 写入失败: {e}")
        except Exception as e:
            print(f"  [Vision {bn}/{tb} ERROR] {e}")
            import traceback; traceback.print_exc()

    print(f"\n[Vision 完成] {len(all_results)}/{total} 帧分析结果, ${stats['cost_usd']:.5f}")
    return all_results, stats

# ═══ 故事合成 ═══
def synthesize_story(frame_results, transcript_text, video_duration_s, fps=10):
    """基于高密度帧行为链，合成最终故事理解"""
    
    # 自适应分桶：越高fps，桶越小
    bucket_size = 0.5 if fps >= 30 else (1.0 if fps >= 20 else 2.0)
    
    # 压缩帧数据：按时间分桶
    buckets = {}
    for fr in frame_results:
        t = fr.get("timeEstimate", 0)
        bucket_key = int(t / bucket_size) * bucket_size
        if bucket_key not in buckets:
            buckets[bucket_key] = []
        buckets[bucket_key].append(fr)
    
    # 为每个桶生成摘要
    bucket_summaries = []
    for bk in sorted(buckets.keys()):
        frames = buckets[bk]
        actions = [f.get("action","") for f in frames]
        states = [f.get("state","") for f in frames]
        anomalies = [f.get("anomaly","") for f in frames if f.get("anomaly")]
        objects = set()
        for f in frames:
            ko = f.get("keyObjects","")
            if isinstance(ko, dict):
                ko = ", ".join(f"{k}:{v}" for k,v in ko.items())
            elif isinstance(ko, list):
                ko = ", ".join(str(x) for x in ko)
            elif not isinstance(ko, str):
                ko = str(ko)
            for o in ko.split(","):
                if o.strip(): objects.add(o.strip())
        
        state_counts = {}
        for s in states:
            for w in ["醉酒","微醺","困惑","清醒","正常","开心","愤怒"]:
                if w in s: state_counts[w] = state_counts.get(w, 0) + 1
        dominant_state = max(state_counts.items(), key=lambda x: x[1])[0] if state_counts else "正常"
        
        bucket_summaries.append({
            "timeRange": f"{bk}s-{bk+bucket_size}s",
            "actions": actions[:5],
            "anomalies": anomalies,
            "keyObjects": list(objects)[:5],
            "frameCount": len(frames)
        })
    
    timeline_text = json.dumps(bucket_summaries, ensure_ascii=False, indent=2)
    
    prompt = f"""你是一个专业的短视频故事分析师。以下是基于{fps}fps高密度采样的完整行为链分析。

## 视频时长
{video_duration_s:.0f}秒

## {bucket_size}秒分桶行为链（完整时间线）
{timeline_text[:30000]}

## 对白参考
{transcript_text[:2000]}

## 任务：基于完整视觉行为链，合成终极故事理解

⚠️ 关键要求：
1. 你拥有的是每{1/fps:.3f}秒一帧的完整行为数据。不要猜测空白——所有行为都在数据中
2. 因果链必须基于画面证据，不依赖对白（对白可能不准确）
3. ⚠️ 完整覆盖全部时间线，不要只分析前半段而忽略后半段
4. 特别注意角色状态变化——如果角色从清醒→微醺→醉酒→行为错乱，这是叙事核心
5. ⚠️ 不要漏掉任何喜剧节拍（comedy beat）——比如拿错物品、走错方向、说错话等醉酒导致的荒谬行为，每个都是独立笑点
6. ⚠️ 错误认知推理：如果角色拿着A物品但上下文暗示他应该拿着B（如拿生蚝壳但上下文是打电话场景），要推理出"角色以为在拿B，实际拿了A"
7. ⚠️ 场景过渡推理：如果上一帧角色在X场景，下一帧出现在Y场景，中间必须有因果解释（如"他以为打开了车门，实际打开了冰箱门"）

## 输出JSON：
{{
  "synopsis": "200字故事梗概：完整的因果链——角色因为什么→做了什么→导致了什么→最终如何",
  "narrativeType": "叙事类型：twist-only(纯转型)/emotional-contagion(情绪传播型)/classic-arc(经典叙事)/slice-of-life(生活切片)",
  "genre": ["主要类型", "次要类型"],
  "confidence": 0.85,
  "causalChain": [
    {{"step": 1, "cause": "初始状态/动机", "behavior": "角色做了什么（具体动作）", "effect": "导致的结果", "timeRange": "Xs-Ys", "evidence": "帧X-Y的画面证据",
     "comedyBeat": "如果这一步是笑点，说明笑点机制（预期违背？物品误认？行为荒谬？）"}}
  ],
  "comedyBeats": [
    {{"timeEstimate": "秒数", "beat": "具体笑点描述", "mechanism": "笑点机制（误认物品/行为错乱/说错话/预期违背）", "evidence": "画面证据"}}
  ],
  "characters": [
    {{"role": "角色A", "identity": "身份推断", "state": "状态描述", "emotionalArc": "从X状态→Y状态的弧线"}}
  ],
  "keyTurningPoints": [
    {{"timeEstimate": "秒数", "event": "转折事件", "whySignificant": "为什么这是关键转折", "visualEvidence": "画面证据"}}
  ],
  "comedyMechanism": "如果是喜剧，笑点机制是什么",
  "dramaticMechanism": "广义的戏剧机制",
  "realityLine": "客观现实线——完整描述画面上实际发生的所有关键事件",
  "subjectiveLine": "如果存在主观视角线（如角色错误认知），逐条列出：角色以为X但实际Y"
}}
只输出JSON。"""

    try:
        raw, usage = call_deepseek(prompt, max_tokens=4096)
        story = json.loads(raw)
        print(f"  [Story] 类型={story.get('narrativeType')} genre={story.get('genre')} confidence={story.get('confidence',0):.2f}")
        print(f"  [Story] {story.get('synopsis','?')[:80]}...")
        return story, usage
    except Exception as e:
        print(f"[Story ERROR] {e}")
        return {"synopsis": f"合成失败: {e}", "genre": [], "narrativeType": "unknown", "confidence": 0}, {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0}

# ═══ 文本分析（基于故事理解） ═══
def run_text_analysis(story_json, transcript_text):
    """基于10fps故事理解，运行所有文本分析"""
    from prompts import PROMPTS
    synopsis = story_json.get("synopsis", "")
    narrative_type = story_json.get("narrativeType", "classic-arc")
    genre = story_json.get("genre", [])
    causal_chain = story_json.get("causalChain", [])
    
    story_context = {
        "synopsis": synopsis,
        "narrativeType": narrative_type,
        "genre": genre,
        "causalChain": json.dumps(causal_chain, ensure_ascii=False)[:1000],
        "realityLine": story_json.get("realityLine", ""),
        "characters": json.dumps(story_json.get("characters", []), ensure_ascii=False)[:500],
        "keyTurningPoints": json.dumps(story_json.get("keyTurningPoints", []), ensure_ascii=False)[:1000],
    }
    story_str = json.dumps(story_context, ensure_ascii=False, indent=2)
    
    results = {}
    tstats = {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0,"cost_usd":0.0}
    
    tasks = [
        ("overview", PROMPTS["overview"], 2048),
        ("script_analysis", PROMPTS["script_analysis"], 4096),
        ("template", PROMPTS["template"], 3072),
        ("scoring", PROMPTS["scoring"], 2048),
    ]
    
    for name, ptpl, mt in tasks:
        try:
            prompt = ptpl.format(story=story_str, transcript=transcript_text)
            raw, usage = call_deepseek(prompt, max_tokens=mt)
            results[name] = json.loads(raw)
            pt = usage.get("prompt_tokens", 0)
            ct = usage.get("completion_tokens", 0)
            tt = usage.get("total_tokens", 0)
            cost = (pt * 0.27 + ct * 1.10) / 1_000_000
            for k, v in [("prompt_tokens", pt), ("completion_tokens", ct), ("total_tokens", tt)]:
                tstats[k] += v
            tstats["cost_usd"] += cost
            print(f"  [{name}] {tt}t, ${cost:.5f}")
        except Exception as e:
            print(f"[{name} ERROR] {e}")
            results[name] = None
    
    return results, tstats


# ═══ HTML 报告生成 ═══
def generate_html_report(story, text_analysis, transcript, frame_results, stats, video_label):
    """生成完整 HTML 分析报告"""
    
    all_stats = {"total_tokens": 0, "cost_usd": 0.0}
    for s in stats:
        all_stats["total_tokens"] += s.get("total_tokens", 0)
        all_stats["cost_usd"] += s.get("cost_usd", 0)
    
    # Helper to safely get values
    def s(j, key, default=""):
        return j.get(key, default) if j else default
    
    ov = text_analysis.get("overview", {}) or {}
    sa = text_analysis.get("script_analysis", {}) or {}
    tp = text_analysis.get("template", {}) or {}
    sc = text_analysis.get("scoring", {}) or {}
    
    genre_tags = " ".join([f'<span class="tag">{g}</span>' for g in story.get("genre", [])])
    nt = story.get("narrativeType", "unknown")
    nt_label = {"twist-only":"纯转型","emotional-contagion":"情绪传播型","classic-arc":"经典叙事型","slice-of-life":"生活切片"}.get(nt, nt)
    
    # Causal chain HTML
    causal_html = ""
    for step in story.get("causalChain", []):
        causal_html += f"""
        <div class="causal-step">
            <span class="step-num">Step {step.get('step','?')}</span>
            <div class="step-body">
                <span class="cause">起因：{step.get('cause','')}</span> →
                <span class="behavior">行为：{step.get('behavior','')}</span> →
                <span class="effect">结果：{step.get('effect','')}</span>
                <div class="evidence">📷 画面证据：{step.get('evidence','')} | ⏱ {step.get('timeRange','')}</div>
            </div>
        </div>"""
    
    # Turning points
    tp_html = ""
    for tp_item in story.get("keyTurningPoints", []):
        tp_html += f"""
        <div class="turning-point">
            <span class="tp-time">⏱ {tp_item.get('timeEstimate','')}s</span>
            <strong>{tp_item.get('event','')}</strong>
            <p>{tp_item.get('whySignificant','')}</p>
            <p class="evidence">📷 {tp_item.get('visualEvidence','')}</p>
        </div>"""
    
    # Characters
    char_html = ""
    for c in story.get("characters", []):
        char_html += f"""
        <div class="character-card">
            <h4>{c.get('role','?')}</h4>
            <p>身份：{c.get('identity','')}</p>
            <p>状态：{c.get('state','')}</p>
            <p>情绪弧线：{c.get('emotionalArc','')}</p>
        </div>"""
    
    # Acts
    acts_html = ""
    for act in sa.get("acts", []):
        acts_html += f"""
        <div class="act-card">
            <h4>{act.get('name','')} <span class="act-time">⏱ {act.get('timeRange','')}</span></h4>
            <p>叙事功能：{act.get('narrativeFunction','')}</p>
            <p>人物动态：{act.get('characterDynamics','')}</p>
            <p>戏剧张力：{'★'*act.get('dramaticTension',0)}{'☆'*(10-act.get('dramaticTension',0))} {act.get('dramaticTension',0)}/10</p>
            <ul>{''.join([f'<li>[{km.get("ts","?")}] {km.get("desc","")}</li>' for km in act.get("keyMoments",[])])}</ul>
        </div>"""
    
    # Scoring
    hook_sc = sc.get("hook", {}) or {}
    struct_sc = sc.get("structure", {}) or {}
    expr_sc = sc.get("expression", {}) or {}
    
    # Frame density stats
    state_dist = {}
    for fr in frame_results:
        st = fr.get("state", "未知")
        state_dist[st] = state_dist.get(st, 0) + 1
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>10fps 深度分析 — {video_label}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#0f0f0f; color:#e0e0e0; line-height:1.6; }}
.container {{ max-width:900px; margin:0 auto; padding:20px; }}
.header {{ text-align:center; padding:40px 20px; background:linear-gradient(135deg,#1a1a2e,#16213e); border-radius:16px; margin-bottom:24px; }}
.header h1 {{ font-size:2em; color:#fff; margin-bottom:8px; }}
.header .badge {{ display:inline-block; background:#e94560; color:#fff; padding:4px 12px; border-radius:20px; font-size:0.85em; margin:4px; }}
.header .subtitle {{ color:#888; font-size:0.9em; margin-top:8px; }}
.section {{ background:#1a1a1a; border-radius:12px; padding:24px; margin-bottom:20px; border:1px solid #2a2a2a; }}
.section h2 {{ color:#e94560; font-size:1.3em; margin-bottom:16px; padding-bottom:8px; border-bottom:1px solid #2a2a2a; }}
.tag {{ display:inline-block; background:#2a2a4a; color:#a0a0ff; padding:2px 10px; border-radius:12px; font-size:0.85em; margin:2px; }}
.stat-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }}
.stat-card {{ background:#0d0d0d; padding:16px; border-radius:8px; text-align:center; }}
.stat-card .value {{ font-size:1.5em; font-weight:bold; color:#e94560; }}
.stat-card .label {{ font-size:0.8em; color:#888; }}
.causal-step {{ background:#0d0d0d; padding:12px; border-radius:8px; margin-bottom:8px; border-left:3px solid #e94560; }}
.step-num {{ font-weight:bold; color:#e94560; }}
.step-body {{ margin-top:4px; }}
.step-body .cause {{ color:#ff6b6b; }}
.step-body .behavior {{ color:#ffd93d; }}
.step-body .effect {{ color:#6bff6b; }}
.evidence {{ font-size:0.8em; color:#666; margin-top:4px; }}
.turning-point {{ background:#0d0d0d; padding:12px; border-radius:8px; margin-bottom:8px; border-left:3px solid #ffd93d; }}
.tp-time {{ color:#ffd93d; font-size:0.85em; }}
.character-card {{ background:#0d0d0d; padding:12px; border-radius:8px; margin-bottom:8px; }}
.character-card h4 {{ color:#a0a0ff; }}
.act-card {{ background:#0d0d0d; padding:12px; border-radius:8px; margin-bottom:8px; }}
.act-time {{ color:#888; font-size:0.85em; }}
.score-bar {{ display:flex; align-items:center; margin:12px 0; }}
.score-label {{ width:100px; font-size:0.9em; }}
.score-fill {{ height:24px; border-radius:12px; background:linear-gradient(90deg,#e94560,#ffd93d); transition:width 0.5s; }}
.score-value {{ margin-left:12px; font-weight:bold; }}
.template-card {{ background:#0d0d0d; padding:12px; border-radius:8px; margin-bottom:8px; }}
.template-card h4 {{ color:#ffd93d; }}
.formula {{ background:#000; padding:8px 12px; border-radius:6px; font-family:monospace; margin:8px 0; color:#6bff6b; }}
.transcript {{ max-height:300px; overflow-y:auto; background:#0d0d0d; padding:12px; border-radius:8px; font-family:monospace; font-size:0.85em; }}
.transcript .ts {{ color:#e94560; }}
.frame-stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:8px; margin-top:8px; }}
.frame-stat-card {{ background:#0d0d0d; padding:8px; border-radius:6px; text-align:center; }}
.frame-stat-card .count {{ font-size:1.2em; font-weight:bold; color:#a0a0ff; }}
.frame-stat-card .name {{ font-size:0.75em; color:#888; }}
@media (max-width:600px) {{ .score-bar {{ flex-direction:column; align-items:flex-start; }} }}
</style>
</head>
<body>
<div class="container">

<div class="header">
    <h1>🎬 10fps 深度影像分析报告</h1>
    <div class="badge">⚡ 10fps Vision Pipeline</div>
    <div class="badge">🔬 不修补 · 纯上限验证</div>
    <p class="subtitle">{video_label} | {datetime.now().strftime('%Y-%m-%d %H:%M')} | 帧密度：每0.1秒/帧</p>
</div>

<!-- 技术指标 -->
<div class="section">
    <h2>📊 技术指标</h2>
    <div class="stat-grid">
        <div class="stat-card"><div class="value">{len(frame_results)}帧</div><div class="label">Vision 分析帧</div></div>
        <div class="stat-card"><div class="value">10fps</div><div class="label">采样密度</div></div>
        <div class="stat-card"><div class="value">{all_stats['total_tokens']:,}</div><div class="label">总 Token</div></div>
        <div class="stat-card"><div class="value">${all_stats['cost_usd']:.4f}</div><div class="label">总成本</div></div>
    </div>
    <div class="frame-stats">
        {''.join([f'<div class="frame-stat-card"><div class="count">{v}</div><div class="name">{k}</div></div>' for k,v in sorted(state_dist.items(), key=lambda x:-x[1])[:8]])}
    </div>
</div>

<!-- 故事理解 -->
<div class="section">
    <h2>📖 故事理解（Vision + 因果推理一体）</h2>
    <p style="margin-bottom:12px;">
        <span class="tag">{nt_label}</span>
        {genre_tags}
        <span style="margin-left:8px;color:#888;">信心：{story.get('confidence',0)*100:.0f}%</span>
    </p>
    <p style="font-size:1.1em;line-height:1.8;background:#0d0d0d;padding:16px;border-radius:8px;">
        {story.get('synopsis','')}
    </p>
</div>

<!-- 因果链 -->
<div class="section">
    <h2>🔗 完整因果链</h2>
    {causal_html}
</div>

<!-- 戏剧机制 -->
<div class="section">
    <h2>🎭 戏剧机制</h2>
    <p><strong>喜剧机制：</strong>{story.get('comedyMechanism','')}</p>
    <p style="margin-top:8px;"><strong>广义戏剧机制：</strong>{story.get('dramaticMechanism','')}</p>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px;">
        <div style="background:#0d0d0d;padding:12px;border-radius:8px;">
            <h4 style="color:#ff6b6b;">📐 客观现实线</h4>
            <p>{story.get('realityLine','')}</p>
        </div>
        <div style="background:#0d0d0d;padding:12px;border-radius:8px;">
            <h4 style="color:#a0a0ff;">🎭 主观视角线</h4>
            <p>{story.get('subjectiveLine','')}</p>
        </div>
    </div>
</div>

<!-- 关键转折点 -->
<div class="section">
    <h2>⚡ 关键转折点</h2>
    {tp_html}
</div>

<!-- 角色分析 -->
<div class="section">
    <h2>👤 角色分析</h2>
    {char_html}
</div>

<!-- 内容总览 -->
<div class="section">
    <h2>📌 内容总览</h2>
    <p><strong>一句话总结：</strong>{s(ov,'oneLiner','')}</p>
    <p><strong>目标受众：</strong>{s(ov,'audience','')}</p>
    <p><strong>核心观点：</strong>{s(ov,'viewpoint','')}</p>
    <p><strong>认知转化：</strong>{s(ov,'cognition','')}</p>
</div>

<!-- 叙事结构 -->
<div class="section">
    <h2>🎬 叙事结构分离</h2>
    <p style="margin-bottom:12px;color:#888;">情绪曲线：{s(sa,'emotionCurve','')}</p>
    {acts_html}
    <h3 style="margin-top:16px;color:#ffd93d;">叙事技巧</h3>
    {''.join([f'<div class="causal-step"><strong>{t.get("name","")}</strong>：{t.get("usage","")} → {t.get("effect","")}</div>' for t in sa.get("techniques",[])])}
</div>

<!-- 评分 -->
<div class="section">
    <h2>⭐ 三项评分</h2>
    <div class="score-bar">
        <span class="score-label">Hook 设计</span>
        <div class="score-fill" style="width:{hook_sc.get('value',0)}%"></div>
        <span class="score-value">{hook_sc.get('value',0)}</span>
    </div>
    <p style="font-size:0.85em;color:#888;margin-bottom:12px;">{hook_sc.get('reason','')}</p>
    <div class="score-bar">
        <span class="score-label">结构设计</span>
        <div class="score-fill" style="width:{struct_sc.get('value',0)}%"></div>
        <span class="score-value">{struct_sc.get('value',0)}</span>
    </div>
    <p style="font-size:0.85em;color:#888;margin-bottom:12px;">{struct_sc.get('reason','')}</p>
    <div class="score-bar">
        <span class="score-label">表达效果</span>
        <div class="score-fill" style="width:{expr_sc.get('value',0)}%"></div>
        <span class="score-value">{expr_sc.get('value',0)}</span>
    </div>
    <p style="font-size:0.85em;color:#888;">{expr_sc.get('reason','')}</p>
</div>

<!-- 复刻模板 -->
<div class="section">
    <h2>📋 复刻模板</h2>
    {''.join([f'<div class="template-card"><h4>{t.get("name","")}</h4><p>{t.get("desc","")}</p><div class="formula">{t.get("formula","")}</div></div>' for t in tp.get("templates",[])])}
    <h3 style="margin-top:12px;color:#ffd93d;">可复用元素</h3>
    <p><strong>脚本模式：</strong>{s(tp.get('reusableElements',{}),'scriptPattern','')}</p>
    <p><strong>Hook技巧：</strong>{s(tp.get('reusableElements',{}),'hookTechnique','')}</p>
    <p><strong>话题切入：</strong>{s(tp.get('reusableElements',{}),'topicAngle','')}</p>
    <p><strong>爆款因素：</strong>{', '.join(tp.get('reusableElements',{}).get('viralFactors',[]) if tp.get('reusableElements') else '')}</p>
</div>

<!-- 对白转录 -->
<div class="section">
    <h2>🎙️ 对白转录（仅供参考）</h2>
    <div class="transcript">
        {''.join([f'<div><span class="ts">[{t.get("ts","?")}]</span> {t.get("text","")}</div>' for t in transcript])}
    </div>
</div>

<div style="text-align:center;padding:40px;color:#444;font-size:0.85em;">
    <p>🔬 10fps Vision Pipeline · 不修补 · 上限验证</p>
    <p>分析引擎：Gemini 2.5 Flash Vision (逐帧) + DeepSeek V4 Pro (故事合成+文本分析)</p>
</div>

</div>
</body>
</html>"""
    return html


# ═══ 主流程 ═══
def main():
    import argparse
    parser = argparse.ArgumentParser(description="10fps Vision 分析管线")
    parser.add_argument("video", help="视频文件路径")
    parser.add_argument("--label", default="", help="视频标签")
    parser.add_argument("--output", default="", help="输出HTML路径")
    parser.add_argument("--transcript-only", action="store_true", help="仅转写")
    parser.add_argument("--cache", default="", help="帧缓存JSON路径（支持断点恢复）")
    parser.add_argument("--skip-vision", action="store_true", help="跳过Vision分析，直接从缓存加载")
    parser.add_argument("--fps", type=int, default=10, help="采样帧率 (默认10, 建议10/20/30)")
    args = parser.parse_args()
    
    video_path = args.video
    if not os.path.exists(video_path):
        print(f"[ERROR] 视频不存在: {video_path}")
        sys.exit(1)
    
    # 获取视频时长
    probe = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",video_path],
        capture_output=True, text=True, timeout=10)
    duration = 0
    try:
        duration = float(json.loads(probe.stdout)["format"]["duration"])
    except: pass
    print(f"[VIDEO] {os.path.basename(video_path)} | {duration:.1f}s")
    
    # 转写
    print("[TRANSCRIBE] Whisper STT...")
    tmp = tempfile.mkdtemp(prefix="whisper_")
    transcript = []
    try:
        subprocess.run(["whisper", video_path, "--model", "tiny", "--language", "zh",
            "--output_format", "vtt", "--output_dir", tmp],
            capture_output=True, text=True, timeout=300)
        for vf in Path(tmp).glob("*.vtt"):
            from server import parse_vtt
            transcript = parse_vtt(vf.read_text())
            print(f"[TRANSCRIBE] {len(transcript)} 条")
            break
    except Exception as e:
        print(f"[TRANSCRIBE] 失败: {e}")
    finally:
        try: shutil.rmtree(tmp)
        except: pass
    
    ttext = format_transcript(transcript) if transcript else "（无对白）"
    print(f"[TRANSCRIBE] 文本:\n{ttext[:300]}")
    
    if args.transcript_only:
        print(json.dumps(transcript, ensure_ascii=False, indent=2))
        return
    
    fps = args.fps
    
    # ═══ 10fps Vision 分析 ═══
    cache_path = args.cache or str(WORKSPACE / "reports" / f"{os.path.splitext(os.path.basename(video_path))[0]}_{fps}fps_cache.json")
    
    all_stats = []
    
    if args.skip_vision:
        print(f"[SKIP-VISION] 从缓存加载: {cache_path}")
        if not os.path.exists(cache_path):
            print(f"[ERROR] 缓存文件不存在: {cache_path}")
            sys.exit(1)
        cached = json.loads(open(cache_path).read())
        frame_results = cached.get("frame_results", [])
        vision_stats = cached.get("stats", {})
        print(f"[SKIP-VISION] 加载 {len(frame_results)} 帧结果")
        t0 = time.time()
    else:
        print(f"\n{'='*60}")
        print(f"[PIPELINE] {fps}fps Vision 分析开始 (预计 {duration*fps:.0f} 帧)")
        print(f"{'='*60}")
        
        tmp = tempfile.mkdtemp(prefix=f"v{fps}_")
        try:
            frames = extract_frames(video_path, tmp, fps=fps)
            if not frames:
                print("[ERROR] 帧提取失败")
                sys.exit(1)
            
            t0 = time.time()
            frame_results, vision_stats = run_vision_10fps(frames, duration, cache_path=cache_path, fps=fps)
        finally:
            try: shutil.rmtree(tmp)
            except: pass
    
    all_stats.append(vision_stats)
    
    print(f"\n[SYNTHESIS] 故事合成...")
    story, story_stats = synthesize_story(frame_results, ttext, duration, fps=fps)
    all_stats.append(story_stats)
    
    print(f"\n[TEXT] 文本分析...")
    text_results, text_stats = run_text_analysis(story, ttext)
    all_stats.append(text_stats)
    
    elapsed = time.time() - t0
    
    # 总统计
    total_tokens = sum(s.get("total_tokens", 0) for s in all_stats)
    total_cost = sum(s.get("cost_usd", 0) for s in all_stats)
    print(f"\n{'='*60}")
    print(f"[DONE] {elapsed:.1f}s | {total_tokens:,} tokens | ${total_cost:.5f}")
    print(f"{'='*60}")
    
    # 生成 HTML 报告
    label = args.label or os.path.basename(video_path)
    html = generate_html_report(story, text_results, transcript, frame_results, all_stats, label)
    
    # 保存
    output_path = args.output or str(WORKSPACE / "reports" / f"{os.path.splitext(os.path.basename(video_path))[0]}_{fps}fps.html")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)
    print(f"[REPORT] {output_path}")
    print(f"[ACCESS] https://unwhispering-imani-digitately.ngrok-free.dev/reports/{os.path.basename(output_path)}")
    
    # 同时保存原始 JSON
    json_path = output_path.replace(".html", ".json")
    with open(json_path, "w") as f:
        json.dump({
            "story": story,
            "text_analysis": text_results,
            "transcript": transcript,
            "frame_count": len(frame_results),
            "fps": 10,
            "duration_s": duration,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "elapsed_s": elapsed,
        }, f, ensure_ascii=False, indent=2)
    print(f"[JSON] {json_path}")


if __name__ == "__main__":
    main()
