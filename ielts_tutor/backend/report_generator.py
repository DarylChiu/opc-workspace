"""
评估报告生成器
生成完整 HTML 报告，包含对话历史 + 四维评分 + 语法改进 + 优秀表达
"""
import os
import json
from datetime import datetime
from typing import Optional


def generate_report(session: dict, scores: Optional[dict] = None, output_dir: str = None) -> str:
    """
    生成 HTML 评估报告
    
    Args:
        session: 会话数据 {mode, transcripts, created}
        scores: 评分数据 {fluency, vocabulary, grammar, pronunciation, overall, summary, improvements, highlights}
        output_dir: 输出目录，默认 ielts_tutor/reports/
    
    Returns:
        报告文件路径
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    os.makedirs(output_dir, exist_ok=True)

    sid = session.get("session_id", "unknown")[:8]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ielts_report_{sid}_{ts}.html"
    filepath = os.path.join(output_dir, filename)

    mode_name = {
        "ielts_part1": "IELTS Speaking Part 1",
        "ielts_part2": "IELTS Speaking Part 2",
        "ielts_part3": "IELTS Speaking Part 3",
        "business_pitch": "Business English · Investor Pitch",
        "free_talk": "Free Conversation",
    }.get(session.get("mode", ""), session.get("mode", "IELTS"))

    transcripts = session.get("transcripts", [])
    s = scores or {}

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IELTS Practice Report</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f0f1a;color:#e0e0f0;padding:40px 20px;display:flex;justify-content:center}}
.report{{max-width:800px;width:100%}}
.header{{text-align:center;margin-bottom:30px}}
.header h1{{font-size:24px;color:#6c63ff}}
.header .meta{{color:#888;font-size:13px;margin-top:6px}}

/* Score card */
.score-card{{background:#1a1a2e;border-radius:12px;padding:24px;margin-bottom:20px;border:1px solid #2a2a4a}}
.score-card h2{{font-size:16px;color:#00d4aa;margin-bottom:16px}}
.overall{{text-align:center;margin-bottom:16px}}
.overall .num{{font-size:48px;font-weight:800;color:#ffd700}}
.overall .lbl{{font-size:13px;color:#888}}
.dims{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.dim{{display:flex;flex-direction:column;gap:4px}}
.dim .lbl{{font-size:12px;color:#888;display:flex;justify-content:space-between}}
.dim .lbl span.val{{color:#e0e0f0;font-weight:700}}
.dim .bar-bg{{height:6px;background:#2a2a4a;border-radius:3px;overflow:hidden}}
.dim .bar-fill{{height:100%;border-radius:3px}}
.bar-f.f{{background:#00d4aa}}.bar-f.v{{background:#4dc9f6}}
.bar-f.g{{background:#f39c12}}.bar-f.p{{background:#e74c8b}}

/* Summary */
.summary{{background:#0f0f1a;padding:14px;border-radius:8px;font-size:13px;line-height:1.7;margin-bottom:16px;color:#ccc}}

/* Section */
.section{{background:#1a1a2e;border-radius:12px;padding:20px;margin-bottom:20px;border:1px solid #2a2a4a}}
.section h2{{font-size:15px;margin-bottom:14px}}
.section.improve h2{{color:#ff6b6b}}
.section.highlight h2{{color:#00d4aa}}
.section.transcript h2{{color:#6c63ff}}

.item{{padding:8px 12px;background:#0f0f1a;border-radius:6px;margin-bottom:8px;font-size:13px;line-height:1.6}}
.item.improve{{border-left:3px solid #ff6b6b}}
.item.good{{border-left:3px solid #00d4aa}}
.correct{{color:#4caf50;font-weight:700}}
.wrong{{color:#ff5252;text-decoration:line-through;font-weight:700}}
.better{{color:#64b5f6;font-weight:700}}

/* Transcript */
.msg{{padding:8px 14px;border-radius:10px;margin-bottom:8px;font-size:13px;line-height:1.6}}
.msg.user{{background:#1e3a5f;text-align:right}}
.msg.tutor{{background:#2d1f4e}}
.msg .role{{font-size:10px;color:#888;display:block;margin-bottom:3px}}
.msg .ts{{font-size:9px;color:#888;margin-top:3px;text-align:right}}

.footer{{text-align:center;color:#555;font-size:11px;margin-top:30px}}
</style>
</head>
<body>
<div class="report">
<div class="header">
<h1>🎤 {mode_name} · Practice Report</h1>
<div class="meta">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | IELTS Tutor v2.0</div>
</div>
"""
    # Score section
    if s:
        overall = s.get("overall", 0)
        dims_html = ""
        dims_data = [
            ("Fluency", "f", s.get("fluency", 0)),
            ("Vocabulary", "v", s.get("vocabulary", 0)),
            ("Grammar", "g", s.get("grammar", 0)),
            ("Pronunciation", "p", s.get("pronunciation", 0)),
        ]
        for name, cls, val in dims_data:
            dims_html += f"""<div class="dim">
<div class="lbl"><span>{name}</span><span class="val">{val:.1f}</span></div>
<div class="bar-bg"><div class="bar-fill bar-f {cls}" style="width:{(val/9*100):.0f}%"></div></div>
</div>"""

        summary = s.get("summary", "")
        summary_html = f'<div class="summary">{summary}</div>' if summary else ""

        html += f"""<div class="score-card">
<h2>📊 Assessment</h2>
<div class="overall"><div class="num">{overall:.1f}</div><div class="lbl">Overall Band Score</div></div>
<div class="dims">{dims_html}</div>
{summary_html}
</div>"""

        # Improvements
        improvements = s.get("improvements", [])
        if improvements:
            items = ""
            for imp in improvements:
                imp = imp.replace("~~", '<span class="wrong">').replace("~~", '</span>')
                imp = imp.replace("**", '<span class="correct">').replace("**", '</span>')
                imp = imp.replace("→", '→ <span class="better">').replace("</span> —", '</span> —')
                items += f'<div class="item improve">{imp}</div>'
            html += f'<div class="section improve"><h2>🔧 Grammar & Phrasing to Improve</h2>{items}</div>'

        # Highlights
        highlights = s.get("highlights", [])
        if highlights:
            items = ""
            for h in highlights:
                h = h.replace("``", '<span class="correct">').replace("``", '</span>')
                h = h.replace("→", '→ <span class="better">').replace("</span> —", '</span> —')
                items += f'<div class="item good">{h}</div>'
            html += f'<div class="section highlight"><h2>⭐ Strong Points & Better Expressions</h2>{items}</div>'

    # Transcript
    if transcripts:
        msgs = ""
        for t in transcripts:
            role = t.get("speaker", "user")
            css = "user" if role == "user" else "tutor"
            label = "🧑 You" if role == "user" else "🎓 Examiner"
            text = t.get("text", "").replace("<", "&lt;")
            msgs += f'<div class="msg {css}"><span class="role">{label}</span>{text}<div class="ts">{t.get("time", "")}</div></div>'
        html += f'<div class="section transcript"><h2>💬 Conversation Transcript</h2>{msgs}</div>'

    html += '<div class="footer">IELTS Tutor v2.0 · Powered by DeepSeek + Google Cloud</div></div></body></html>'

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath
