"""
HTML 报告导出模块 v1.0
生成自包含的完整分析报告 HTML
"""
import json, os, shutil, time
from datetime import datetime, timezone
from pathlib import Path

REPORTS_DIR = Path(__file__).parent / "reports"
VERSION_FILE = Path(__file__).parent / "VERSION"

def get_version():
    try:
        return VERSION_FILE.read_text().strip()
    except:
        return "0.0.0"


def generate_report(
    video_meta: dict,
    transcript: list,
    analysis: dict,
    token_stats: dict,
    marks: list = None,
    run_id: str = "",
    video_url: str = "",
) -> str:
    """生成完整 HTML 报告，返回 HTML 字符串"""
    ver = get_version()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    filename = video_meta.get("filename", "未知")
    duration_s = video_meta.get("duration", 0)
    duration_str = f"{int(duration_s//60)}:{int(duration_s%60):02d}" if duration_s else "—"
    source = video_meta.get("source", "local")
    platform = video_meta.get("platform", source)
    video_path = video_meta.get("path", "")
    
    # 提取各模块数据
    story = analysis.get("story", {})
    overview = analysis.get("overview", {})
    script = analysis.get("script_analysis") or analysis.get("scriptAnalysis", {})
    template = analysis.get("template", {})
    cine = analysis.get("cinematography", {})
    scores = analysis.get("scoring") or analysis.get("scores", {})
    commerce = analysis.get("commerce", {})
    gemini = analysis.get("gemini_analysis", {})
    
    genre = story.get("genre", []) or overview.get("genre", [])
    synopsis = story.get("synopsis", "") or overview.get("oneLiner", "")
    narrative_core = story.get("narrativeCore", "")
    
    # 镜头数据
    c = cine.get("cinematography", {}) if isinstance(cine.get("cinematography"), dict) else {}
    lc = cine.get("lightingColor", {}) if isinstance(cine.get("lightingColor"), dict) else {}
    sd = cine.get("soundDesign", {}) if isinstance(cine.get("soundDesign"), dict) else {}
    ds = cine.get("directorStyle", {}) if isinstance(cine.get("directorStyle"), dict) else {}
    
    marks = marks or []
    tstats = token_stats or {}
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>视频分析报告 — {filename}</title>
<style>
:root {{
  --bg: #0f0f0f; --card: #1a1a1a; --border: #2a2a2a;
  --text: #e0e0e0; --dim: #888; --accent: #4da6ff;
  --green: #4caf50; --yellow: #f0c040; --red: #f06060;
  --purple: #a855f7; --orange: #f09040;
}}
* {{ margin:0; padding:0; box-sizing:border-box }}
body {{ background:var(--bg); color:var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height:1.7; max-width:900px; margin:0 auto; padding:24px 16px 60px }}
h1 {{ font-size:1.5em; margin-bottom:4px }}
h2 {{ font-size:1.2em; border-bottom:1px solid var(--border); padding-bottom:8px; margin:32px 0 16px; display:flex; align-items:center; gap:8px }}
h3 {{ font-size:1em; margin:16px 0 8px; color:var(--accent) }}
.meta {{ color:var(--dim); font-size:0.85em; margin-bottom:24px }}
.header-card {{ background:var(--card); border:1px solid var(--border); border-radius:8px; padding:20px; margin-bottom:24px }}
.header-card .row {{ display:flex; flex-wrap:wrap; gap:16px; margin-bottom:12px }}
.header-card .item {{ min-width:120px }}
.header-card .item-label {{ font-size:0.75em; color:var(--dim); text-transform:uppercase; letter-spacing:0.5px }}
.header-card .item-value {{ font-size:1.05em }}
.genre-tag {{ display:inline-block; background:var(--accent); color:#000; padding:2px 10px; border-radius:12px; font-size:0.8em; margin:2px 4px }}
.synopsis {{ font-size:1.05em; line-height:1.8; margin:12px 0; padding:12px 16px; border-left:3px solid var(--accent); background:rgba(77,166,255,0.05) }}
.narrative-core {{ font-size:0.95em; line-height:1.8; margin:12px 0; padding:12px 16px; border-left:3px solid var(--purple); background:rgba(168,85,247,0.05) }}
.score-row {{ display:flex; gap:12px; flex-wrap:wrap; margin:12px 0 }}
.score-card {{ flex:1; min-width:140px; background:var(--card); border:1px solid var(--border); border-radius:8px; padding:16px; text-align:center }}
.score-card .label {{ font-size:0.8em; color:var(--dim); margin-bottom:4px }}
.score-card .value {{ font-size:2em; font-weight:700 }}
.score-card .value.high {{ color:var(--green) }}
.score-card .value.mid {{ color:var(--yellow) }}
.score-card .value.low {{ color:var(--red) }}
.score-card .reason {{ font-size:0.8em; color:var(--dim); margin-top:4px }}
.act-card {{ background:var(--card); border:1px solid var(--border); border-radius:8px; padding:16px; margin-bottom:12px }}
.act-card .act-header {{ font-weight:600; margin-bottom:4px }}
.act-card .act-header span {{ color:var(--accent) }}
.act-card .act-time {{ color:var(--dim); font-size:0.8em }}
.act-card .tension {{ display:inline-block; margin-left:8px; font-size:0.8em }}
.moment-item {{ padding:3px 0 3px 16px; font-size:0.9em; border-left:2px solid var(--border); margin:4px 0 }}
.moment-ts {{ color:var(--accent); font-size:0.8em; margin-right:6px }}
.transcript-line {{ display:flex; gap:8px; padding:4px 0; font-size:0.9em; border-bottom:1px solid rgba(255,255,255,0.04) }}
.transcript-ts {{ color:var(--accent); min-width:48px; font-size:0.8em; font-family:monospace }}
.transcript-tag {{ color:var(--orange); min-width:56px; font-size:0.75em; text-align:center }}
.transcript-text {{ flex:1 }}
.technique-card {{ background:var(--card); border:1px solid var(--border); border-radius:6px; padding:12px; margin-bottom:8px }}
.technique-name {{ font-weight:600; color:var(--accent) }}
.technique-usage {{ font-size:0.8em; color:var(--orange); margin-top:2px }}
.technique-effect {{ font-size:0.9em; margin-top:4px; color:var(--dim) }}
.field-row {{ display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:12px }}
@media (max-width:600px) {{ .field-row {{ grid-template-columns:1fr }} }}
.field-item {{ background:var(--card); border:1px solid var(--border); border-radius:6px; padding:10px 14px }}
.field-label {{ font-size:0.75em; color:var(--dim); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:2px }}
.template-card {{ background:var(--card); border:1px solid var(--border); border-radius:6px; padding:14px; margin-bottom:10px }}
.template-card .tpl-name {{ font-weight:600; color:var(--green) }}
.template-card .tpl-desc {{ font-size:0.85em; color:var(--dim); margin:4px 0 8px }}
.template-card .tpl-formula {{ background:rgba(255,255,255,0.05); padding:10px 14px; border-radius:4px; font-size:0.85em; white-space:pre-line; line-height:1.6 }}
.emotion-curve {{ background:var(--card); border:1px solid var(--border); border-radius:6px; padding:14px; margin:12px 0 }}
.disclaimer {{ color:var(--yellow); font-size:0.8em; font-style:italic; margin-bottom:12px }}
.mark-item {{ padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.04); font-size:0.9em }}
.mark-ts {{ color:var(--accent); font-size:0.8em; font-family:monospace }}
.mark-type {{ display:inline-block; padding:1px 6px; border-radius:4px; font-size:0.75em; margin:0 6px }}
.mark-type.hook {{ background:rgba(240,192,64,0.2); color:var(--yellow) }}
.mark-type.gold {{ background:rgba(76,175,80,0.2); color:var(--green) }}
.mark-type.turn {{ background:rgba(240,144,64,0.2); color:var(--orange) }}
.stats-box {{ display:flex; gap:12px; flex-wrap:wrap; margin:12px 0 }}
.stat-item {{ flex:1; min-width:100px; background:var(--card); border:1px solid var(--border); border-radius:6px; padding:12px; text-align:center }}
.stat-value {{ font-size:1.3em; font-weight:600 }}
.stat-label {{ font-size:0.75em; color:var(--dim); margin-top:2px }}
.footer {{ margin-top:40px; padding-top:16px; border-top:1px solid var(--border); font-size:0.75em; color:var(--dim); display:flex; justify-content:space-between; flex-wrap:wrap }}
</style>
</head>
<body>

<h1>🎬 视频分析报告</h1>
<div class="meta">生成时间: {now} · 版本: v{ver} · Run ID: {run_id}</div>

<!-- 视频信息 -->
<div class="header-card">
  <div class="row">
    <div class="item"><div class="item-label">视频</div><div class="item-value">{filename}</div></div>
    <div class="item"><div class="item-label">时长</div><div class="item-value">{duration_str}</div></div>
    <div class="item"><div class="item-label">平台</div><div class="item-value">{platform}</div></div>
    <div class="item"><div class="item-label">来源</div><div class="item-value">{"URL" if source=="url" else "本地"}</div></div>
  </div>
  {_commerce_section(commerce)}
</div>

<!-- 类型 & 概要 -->
<h2>📋 类型与概要</h2>
<div style="margin-bottom:12px">
{''.join(f'<span class="genre-tag">{g}</span>' for g in genre) if genre else '<span style="color:var(--dim)">—</span>'}
</div>
<div class="synopsis">{synopsis or '—'}</div>
{f'<div class="narrative-core"><strong>🧠 叙事核心:</strong> {narrative_core}</div>' if narrative_core else ''}

<!-- 三项评分 -->
<h2>⭐ 三项评分</h2>
<div class="score-row">
{_score_card("🪝 Hook", scores.get("hook"))}
{_score_card("🏗️ 结构", scores.get("structure"))}
{_score_card("💬 表达", scores.get("expression"))}
</div>

<!-- 对白 -->
<h2>💬 对白时间线</h2>
{_transcript_section(transcript)}

<!-- 脚本解析 -->
<h2>🎬 脚本解析</h2>
{_script_section(script)}

<!-- 复刻模板 -->
<h2>📋 复刻模板</h2>
{_template_section(template, analysis.get("templates"))}

<!-- 镜头 & 声音 -->
<h2>🎥 镜头 & 声音</h2>
{_cinematography_section(c, lc, sd, ds, cine.get("disclaimer"))}

<!-- 标记 -->
<h2>🏷️ 标记</h2>
{_marks_section(marks)}

<!-- 成本 -->
<h2>📊 性能 & 成本</h2>
<div class="stats-box">
  <div class="stat-item"><div class="stat-value">{tstats.get("total_tokens",0):,}</div><div class="stat-label">总 Tokens</div></div>
  <div class="stat-item"><div class="stat-value">${tstats.get("cost_usd",0):.4f}</div><div class="stat-label">成本 USD</div></div>
  <div class="stat-item"><div class="stat-value">{tstats.get("elapsed", tstats.get("elapsed_ms",0)//1000):.1f}s</div><div class="stat-label">耗时</div></div>
  <div class="stat-item"><div class="stat-value">{len(transcript)}</div><div class="stat-label">对白条数</div></div>
</div>

{_per_call_section(tstats.get("per_call", []))}

<div class="footer">
  <span>视频分析交互 Workflow v{ver}</span>
  <span>Generated by Bryson · {now}</span>
</div>

</body>
</html>'''
    return html


def _commerce_section(commerce: dict) -> str:
    if not commerce:
        return ""
    views = commerce.get("views", "")
    likes = commerce.get("likes", "")
    saves = commerce.get("saves", "")
    shares = commerce.get("shares", "")
    if not any([views, likes, saves, shares]):
        return ""
    items = []
    if views: items.append(f'<div class="item"><div class="item-label">👁 播放</div><div class="item-value">{views}</div></div>')
    if likes: items.append(f'<div class="item"><div class="item-label">👍 点赞</div><div class="item-value">{likes}</div></div>')
    if saves: items.append(f'<div class="item"><div class="item-label">⭐ 收藏</div><div class="item-value">{saves}</div></div>')
    if shares: items.append(f'<div class="item"><div class="item-label">↗ 转发</div><div class="item-value">{shares}</div></div>')
    return '<div class="row">' + ''.join(items) + '</div>'


def _score_card(label: str, score: dict) -> str:
    if not score:
        return '<div class="score-card"><div class="label">' + label + '</div><div class="value">—</div></div>'
    v = score.get("value", 0)
    cls = "high" if v >= 80 else ("mid" if v >= 60 else "low")
    return f'<div class="score-card"><div class="label">{label}</div><div class="value {cls}">{v}</div><div class="reason">{score.get("reason","")}</div></div>'


def _transcript_section(transcript: list) -> str:
    if not transcript:
        return '<p style="color:var(--dim)">—</p>'
    lines = []
    for item in transcript:
        ts = item.get("ts", "")
        tag = item.get("tag", "")
        text = item.get("text", "")
        lines.append(f'<div class="transcript-line"><span class="transcript-ts">{ts}</span><span class="transcript-tag">{tag}</span><span class="transcript-text">{text}</span></div>')
    return '\n'.join(lines)


def _script_section(script: dict) -> str:
    if not script:
        return '<p style="color:var(--dim)">—</p>'
    parts = []
    acts = script.get("acts", [])
    if acts:
        for a in acts:
            name = a.get("name", "")
            time_range = a.get("timeRange", "")
            func = a.get("narrativeFunction", "")
            dynamics = a.get("characterDynamics", "")
            tension = a.get("dramaticTension", 0)
            key_moments = a.get("keyMoments", [])
            parts.append(f'''<div class="act-card">
<div class="act-header"><span>{name}</span> <span class="act-time">{time_range}</span> <span class="tension">张力: {'█'*tension}{'░'*(10-tension)} {tension}/10</span></div>
<div style="font-size:0.9em;margin:6px 0">📌 {func}</div>
{f'<div style="font-size:0.85em;color:var(--dim)">👤 {dynamics}</div>' if dynamics else ''}
{''.join(f'<div class="moment-item"><span class="moment-ts">[{m.get("ts","")}]</span>{m.get("desc","")}</div>' for m in key_moments)}
</div>''')
    
    emotion = script.get("emotionCurve", "")
    if emotion:
        parts.append(f'<div class="emotion-curve"><strong>📈 情绪曲线:</strong> {emotion}</div>')
    
    techniques = script.get("techniques", [])
    if techniques:
        parts.append('<div style="margin-top:16px">')
        for t in techniques:
            parts.append(f'''<div class="technique-card">
<div class="technique-name">{t.get("name","")}</div>
<div class="technique-usage">用法: {t.get("usage","")}</div>
<div class="technique-effect">效果: {t.get("effect","")}</div>
</div>''')
        parts.append('</div>')
    
    return '\n'.join(parts) if parts else '<p style="color:var(--dim)">—</p>'


def _template_section(template: dict, templates: list) -> str:
    tpls = (template.get("templates") or templates or [])
    if not tpls:
        return '<p style="color:var(--dim)">—</p>'
    parts = []
    for t in tpls:
        if isinstance(t, str):
            parts.append(f'<div class="template-card"><div class="tpl-name">{t}</div></div>')
        else:
            name = t.get("name", "")
            desc = t.get("desc", "")
            formula = t.get("formula", "")
            parts.append(f'''<div class="template-card">
<div class="tpl-name">📐 {name}</div>
<div class="tpl-desc">{desc}</div>
{f'<div class="tpl-formula">{formula}</div>' if formula else ''}
</div>''')
    return '\n'.join(parts)


def _cinematography_section(c: dict, lc: dict, sd: dict, ds: dict, disclaimer: str = "") -> str:
    parts = []
    if disclaimer:
        parts.append(f'<div class="disclaimer">{disclaimer}</div>')
    
    if c or lc:
        parts.append('<div class="field-row">')
        for label, val in [("景别策略", c.get("shotTypes","")), ("构图策略", c.get("composition","")),
                           ("摄影机运动", c.get("cameraMovement","")), ("光线风格", lc.get("lightingMood","")),
                           ("色彩策略", lc.get("colorPalette","")), ("视觉节奏", lc.get("visualRhythm",""))]:
            if val:
                parts.append(f'<div class="field-item"><div class="field-label">{label}</div>{val}</div>')
        parts.append('</div>')
    
    if sd:
        parts.append('<div class="field-row">')
        for label, val in [("BGM", sd.get("bgm","")), ("环境音", sd.get("ambient","")), ("对白风格", sd.get("dialogueStyle",""))]:
            if val:
                parts.append(f'<div class="field-item"><div class="field-label">{label}</div>{val}</div>')
        parts.append('</div>')
    
    if ds:
        parts.append('<div class="field-row">')
        for label, val in [("美学取向", ds.get("aesthetic","")), ("叙事签名", ds.get("narrativeSignature","")), ("文化编码", ds.get("culturalEncoding",""))]:
            if val:
                parts.append(f'<div class="field-item"><div class="field-label">{label}</div>{val}</div>')
        parts.append('</div>')
    
    return '\n'.join(parts) if parts else '<p style="color:var(--dim)">—</p>'


def _marks_section(marks: list) -> str:
    if not marks:
        return '<p style="color:var(--dim)">暂无标记</p>'
    parts = []
    for m in marks:
        mtype = m.get("type", "")
        type_cls = {"hook":"hook", "gold":"gold", "turn":"turn"}.get(mtype, "")
        ts = m.get("timestamp", "")
        text = m.get("text", "")
        note = m.get("note", "")
        parts.append(f'<div class="mark-item"><span class="mark-ts">{ts}</span><span class="mark-type {type_cls}">{mtype}</span>{text}{" · 📝 "+note if note else ""}</div>')
    return '\n'.join(parts)


def _per_call_section(per_call: list) -> str:
    if not per_call:
        return ""
    rows = []
    for item in per_call:
        name = item.get("name", "")
        pt = item.get("prompt_tokens", 0)
        ct = item.get("completion_tokens", 0)
        cost = item.get("cost_usd", 0)
        rows.append(f'<tr><td style="padding:3px 8px;font-size:0.85em">{name}</td><td style="padding:3px 8px;text-align:right;font-size:0.85em">{pt:,}</td><td style="padding:3px 8px;text-align:right;font-size:0.85em">{ct:,}</td><td style="padding:3px 8px;text-align:right;font-size:0.85em">{pt+ct:,}</td><td style="padding:3px 8px;text-align:right;font-size:0.85em">${cost:.6f}</td></tr>')
    
    return f'''<div style="margin-top:16px">
<h3 style="margin-bottom:8px">调用明细</h3>
<table style="width:100%;border-collapse:collapse">
<tr style="border-bottom:1px solid var(--border);color:var(--dim);font-size:0.8em;text-align:right">
  <th style="text-align:left;padding:4px 8px">任务</th><th style="padding:4px 8px">Prompt</th><th style="padding:4px 8px">Completion</th><th style="padding:4px 8px">Total</th><th style="padding:4px 8px">Cost</th></tr>
{''.join(rows)}
</table></div>'''


def save_report(html: str, video_meta: dict, run_id: str = "") -> str:
    """保存报告到 reports/ 目录，返回保存路径"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    video_id = video_meta.get("filename", "unknown").rsplit(".", 1)[0]
    folder = REPORTS_DIR / f"{date_str}_{video_id}"
    folder.mkdir(parents=True, exist_ok=True)
    
    report_path = folder / "report.html"
    report_path.write_text(html)
    
    # 同时保存 source data
    meta_path = folder / "meta.json"
    meta_path.write_text(json.dumps({
        "run_id": run_id,
        "video": video_meta,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "version": get_version(),
    }, ensure_ascii=False, indent=2))
    
    print(f"[EXPORT] 报告已保存 → {report_path}")
    return str(report_path)
