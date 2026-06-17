#!/usr/bin/env python3
"""
Gosh Console — Unified remote control center
Dashboard + Dispatch + Agent management, single Flask app on :8766
"""
import json, os, glob
from datetime import date, datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

APP = Flask(__name__, static_folder='.')
PORT = 8766

# === Paths ===
BASE = Path("/Users/zhaoyuzhao/WorkBuddy/Claw")
REPORTS_DIR = BASE / "reports"
DISPATCH_DIR = Path("/Users/zhaoyuzhao/WorkBuddy/Claw/dispatch/tasks")
PLUGINS_DIR = Path("/Users/zhaoyuzhao/.workbuddy/plugins/marketplaces/my-experts/plugins")
ROUNDTABLE_DIR = BASE / "roundtable"

AGENTS = {
    "balance": {"name": "算点小账", "role": "跨境财务分析师 | ACCA/CPA/CFA", "color": "#50a0ff",
                "plugin": "finance-analyst"},
    "self":    {"name": "恨点小己", "role": "知识管理专家 | 中大+港中文", "color": "#ffaa50",
                "plugin": "knowledge-curator"},
    "yueyu":   {"name": "乐语",     "role": "音乐创作人", "color": "#dc64b4",
                "plugin": "music-creator"},
    "gosh":    {"name": "搞点小事", "role": "调度中枢", "color": "#888",
                "plugin": None},
}

# Ensure dispatch dirs exist
for key in AGENTS:
    d = DISPATCH_DIR / key
    d.mkdir(parents=True, exist_ok=True)


# === Helpers ===
def check_configured(key):
    plugin = AGENTS[key].get("plugin")
    if not plugin:
        return True  # Gosh is always configured
    agents_sub = PLUGINS_DIR / plugin / "agents"
    return agents_sub.exists() and (agents_sub / "identity.md").exists() and (agents_sub / "soul.md").exists()


def read_report(key):
    report_dir = REPORTS_DIR / key
    if not report_dir.exists():
        return None
    today = date.today().isoformat()
    rfile = report_dir / f"{today}.json"
    if not rfile.exists():
        files = sorted(report_dir.glob("*.json"), reverse=True)
        if not files:
            return None
        rfile = files[0]
    try:
        data = json.loads(rfile.read_text())
        data["_file"] = rfile.name
        return data
    except:
        return None

def list_reports(key):
    report_dir = REPORTS_DIR / key
    if not report_dir.exists():
        return []
    files = sorted(report_dir.glob("*.json"), reverse=True)
    reports = []
    for f in files:
        try:
            data = json.loads(f.read_text())
            reports.append({
                "file": f.name,
                "date": f.stem,
                "task": data.get("current_task", "")[:60],
                "progress": data.get("progress", 0),
            })
        except:
            pass
    return reports

def read_specific_report(key, filename):
    f = REPORTS_DIR / key / filename
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text())
        data["_file"] = f.name
        return data
    except:
        return None


def scan_dispatch_tasks():
    tasks = []
    for key in AGENTS:
        d = DISPATCH_DIR / key
        if d.exists():
            for f in sorted(d.glob("*.json"), reverse=True):
                try:
                    t = json.loads(f.read_text())
                    t["agent_key"] = key
                    t["file"] = f.name
                    tasks.append(t)
                except:
                    pass
    tasks.sort(key=lambda t: t.get("dispatched_at", ""), reverse=True)
    return tasks


# === API Routes ===

@APP.route("/")
def index():
    return send_from_directory(".", "index.html")


@APP.route("/api/status")
def api_status():
    agents_list = []
    alerts = []

    for key, info in AGENTS.items():
        if key == "gosh":
            agents_list.append({
                "key": "gosh", "name": info["name"], "role": info["role"],
                "color": info["color"], "configured": True, "status": "active",
                "progress": 100, "current_task": "调度中",
                "last_updated": datetime.now().isoformat(),
            })
            continue

        configured = check_configured(key)
        report = read_report(key)
        ad = {"key": key, "name": info["name"], "role": info["role"],
              "color": info["color"], "configured": configured,
              "status": "ready" if configured else "pending",
              "progress": 100 if configured else 0,
              "current_task": "等待指令" if configured else "待配置",
              "last_updated": "N/A"}

        if report:
            ad["status"] = report.get("status", "working")
            ad["progress"] = report.get("progress", 0)
            ad["current_task"] = report.get("current_task", "")
            ad["last_updated"] = report.get("timestamp", "")
            ad["notes"] = report.get("notes", "")
            ad["report_file"] = report.get("_file", "")

        # Report history for this agent (allow viewing older reports)
        ad["report_history"] = list_reports(key)

        agents_list.append(ad)

    # Alerts — managed client-side via localStorage.
    # Server sends the current decisions_needed; frontend filters resolved ones.
    alerts_from_reports = []
    for key, info in AGENTS.items():
        if key == "gosh":
            continue
        report = read_report(key)
        if report:
            for d in report.get("decisions_needed", []):
                alerts_from_reports.append({
                    "id": f"{key}:{hash(d) % 100000}",
                    "agent": info["name"], "agent_key": key,
                    "type": "decision", "message": d, "urgency": "medium"
                })
            for b in report.get("blockers", []):
                alerts_from_reports.append({
                    "id": f"{key}:{hash(b) % 100000}",
                    "agent": info["name"], "agent_key": key,
                    "type": "blocked", "message": b, "urgency": "high"
                })
    alerts = alerts_from_reports

    # Tasks: dispatch + roundtable
    tasks = []
    for t in scan_dispatch_tasks():
        tasks.append({
            "task": t.get("content", "")[:80],
            "agent": t.get("agent_name", ""),
            "milestone": f"待执行 · {t.get('dispatched_at', '')[:16]}",
            "status": "pending",
        })

    if ROUNDTABLE_DIR.exists():
        for d in sorted(ROUNDTABLE_DIR.iterdir(), reverse=True):
            if d.is_dir():
                tasks.append({
                    "task": d.name, "agent": "Gosh",
                    "milestone": "完成" if (d / "05-execution-plan.md").exists() else "进行中",
                    "status": "done" if (d / "05-execution-plan.md").exists() else "in_progress",
                })

    if not tasks:
        tasks.append({"task": "无活跃任务", "agent": "—", "milestone": "—", "status": "idle"})

    return jsonify({
        "agents": agents_list,
        "tasks": tasks[:6],
        "alerts": alerts,
        "dispatch_queue": len(scan_dispatch_tasks()),
        "gosh_status": {
            "model": "MiniMax M2.5",
            "active": True,
            "last_refresh": datetime.now().isoformat(),
        },
    })


@APP.route("/api/report/<agent>")
def api_report(agent):
    """Return the full report for a specific agent (latest)."""
    if agent not in AGENTS:
        return jsonify({"ok": False, "error": f"Unknown agent: {agent}"}), 400
    report = read_report(agent)
    if not report:
        return jsonify({"ok": False, "error": "No report found"}), 404
    return jsonify({"ok": True, "agent": agent, "agent_name": AGENTS[agent]["name"], "report": report, "history": list_reports(agent)})


@APP.route("/api/reports/<agent>")
def api_reports_list(agent):
    """List all reports for an agent."""
    if agent not in AGENTS:
        return jsonify({"ok": False, "error": f"Unknown agent: {agent}"}), 400
    return jsonify({"ok": True, "agent": agent, "agent_name": AGENTS[agent]["name"], "reports": list_reports(agent)})


@APP.route("/api/report/<agent>/<filename>")
def api_report_specific(agent, filename):
    """Return a specific report by filename."""
    if agent not in AGENTS:
        return jsonify({"ok": False, "error": f"Unknown agent: {agent}"}), 400
    report = read_specific_report(agent, filename)
    if not report:
        return jsonify({"ok": False, "error": "Report not found"}), 404
    return jsonify({"ok": True, "agent": agent, "agent_name": AGENTS[agent]["name"], "report": report, "history": list_reports(agent)})


@APP.route("/api/dispatch", methods=["POST"])
def api_dispatch():
    data = request.get_json()
    agent = data.get("agent", "").strip()
    content = data.get("content", "").strip()

    if not agent or agent not in AGENTS:
        return jsonify({"ok": False, "error": f"Unknown agent: {agent}"}), 400
    if not content:
        return jsonify({"ok": False, "error": "Content required"}), 400

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"{ts}.json"
    filepath = DISPATCH_DIR / agent / filename

    task = {
        "agent": agent,
        "agent_name": AGENTS[agent]["name"],
        "dispatched_at": datetime.now().isoformat(),
        "content": content,
        "status": "pending",
        "dispatched_by": "Gosh Console",
    }
    filepath.write_text(json.dumps(task, ensure_ascii=False, indent=2))

    return jsonify({"ok": True, "task_id": ts, "sent_to": AGENTS[agent]["name"]})


@APP.route("/api/queue")
def api_queue():
    tasks = scan_dispatch_tasks()
    return jsonify({"tasks": tasks})


@APP.route("/api/queue/<agent>")
def api_queue_agent(agent):
    if agent not in AGENTS:
        return jsonify({"ok": False, "error": f"Unknown agent: {agent}"}), 400
    tasks = []
    d = DISPATCH_DIR / agent
    if d.exists():
        for f in sorted(d.glob("*.json"), reverse=True):
            try:
                t = json.loads(f.read_text())
                t["file"] = f.name
                tasks.append(t)
            except:
                pass
    return jsonify({"agent": agent, "agent_name": AGENTS[agent]["name"], "tasks": tasks})


@APP.route("/api/task/<agent>/<task_id>", methods=["DELETE"])
def api_delete_task(agent, task_id):
    if agent not in AGENTS:
        return jsonify({"ok": False}), 400
    f = DISPATCH_DIR / agent / f"{task_id}.json"
    if f.exists():
        f.unlink()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Not found"}), 404


if __name__ == "__main__":
    print(f"Gosh Console starting on http://0.0.0.0:{PORT}")
    APP.run(host="0.0.0.0", port=PORT, debug=False)
