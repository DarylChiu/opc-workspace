#!/usr/bin/env python3
"""Gosh Dashboard Backend — scans agent reports and serves dynamic status API."""
import json, os, re, glob
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

APP = Flask(__name__, static_folder=".")
REPORTS_DIR = Path("/Users/zhaoyuzhao/WorkBuddy/Claw/reports")
PLUGINS_DIR = Path("/Users/zhaoyuzhao/.workbuddy/plugins/marketplaces/my-experts/plugins")

AGENTS = {
    "balance": {"name": "算点小账", "role": "跨境财务分析师", "color": "blue"},
    "self":    {"name": "恨点小己", "role": "知识管理专家", "color": "amber"},
    "yueyu":   {"name": "乐语",     "role": "音乐创作人",   "color": "pink"},
}


def check_agent_configured(agent_key):
    """Check if agent has identity.md and soul.md files."""
    agent_dir = PLUGINS_DIR / {
        "balance": "finance-analyst",
        "self": "knowledge-curator",
        "yueyu": "music-creator",
    }.get(agent_key, "")
    agents_sub = agent_dir / "agents"
    if not agents_sub.exists():
        return False
    return (agents_sub / "identity.md").exists() and (agents_sub / "soul.md").exists()


def read_agent_report(agent_key):
    """Read the latest report file for a given agent."""
    report_dir = REPORTS_DIR / agent_key
    if not report_dir.exists():
        return None
    today = date.today().isoformat()
    report_file = report_dir / f"{today}.json"
    if not report_file.exists():
        json_files = sorted(report_dir.glob("*.json"), reverse=True)
        if not json_files:
            return None
        report_file = json_files[0]
    try:
        return json.loads(report_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def get_gosh_tasks():
    """Scan dispatch tasks and roundtable for active task indicators."""
    tasks = []

    # Scan dispatch task queue
    dispatch_dir = Path("/Users/zhaoyuzhao/WorkBuddy/Claw/dispatch/tasks")
    if dispatch_dir.exists():
        for agent_key in ["balance", "self", "yueyu", "gosh"]:
            agent_dir = dispatch_dir / agent_key
            if agent_dir.exists():
                for tf in sorted(agent_dir.glob("*.json"), reverse=True):
                    try:
                        data = json.loads(tf.read_text())
                        tasks.append({
                            "task": data.get("content", tf.stem)[:80],
                            "agent": data.get("agent_name", agent_key),
                            "milestone": f"待执行 (下发于 {data.get('dispatched_at', '?')})",
                            "status": "pending",
                        })
                    except:
                        pass

    # Also scan roundtable
    rt_dir = Path("/Users/zhaoyuzhao/WorkBuddy/Claw/roundtable")
    if rt_dir.exists():
        for d in sorted(rt_dir.iterdir(), reverse=True):
            if d.is_dir():
                tasks.append({
                    "task": d.name,
                    "agent": "Gosh",
                    "milestone": "讨论完成" if (d / "05-execution-plan.md").exists() else "进行中",
                    "status": "done" if (d / "05-execution-plan.md").exists() else "in_progress",
                })

    if not tasks:
        tasks.append({"task": "无活跃任务", "agent": "—", "milestone": "—", "status": "idle"})
    return tasks[:5]


@APP.route("/api/status")
def api_status():
    agents_list = []
    alerts = []

    for key, info in AGENTS.items():
        configured = check_agent_configured(key)
        report = read_agent_report(key)

        agent_data = {
            "key": key,
            "name": info["name"],
            "role": info["role"],
            "color": info["color"],
            "configured": configured,
            "status": "ready" if configured else "pending",
            "report": report,
        }

        if report:
            agent_data["status"] = report.get("status", "working")
            agent_data["progress"] = report.get("progress", 0)
            agent_data["current_task"] = report.get("current_task", "")
            agent_data["tasks_completed"] = report.get("tasks_completed", [])
            agent_data["blockers"] = report.get("blockers", [])
            agent_data["decisions_needed"] = report.get("decisions_needed", [])
            agent_data["notes"] = report.get("notes", "")
            agent_data["last_updated"] = report.get("timestamp", "")

            for d in report.get("decisions_needed", []):
                alerts.append({
                    "agent": info["name"],
                    "type": "decision",
                    "message": d,
                    "urgency": "medium",
                })
            for b in report.get("blockers", []):
                alerts.append({
                    "agent": info["name"],
                    "type": "blocked",
                    "message": b,
                    "urgency": "high",
                })
            if report.get("status") == "blocked":
                alerts.append({
                    "agent": info["name"],
                    "type": "status",
                    "message": f"{info['name']} 被阻塞，等待外部输入",
                    "urgency": "high",
                })

        agents_list.append(agent_data)

    tasks = get_gosh_tasks()

    return jsonify({
        "agents": agents_list,
        "tasks": tasks,
        "alerts": alerts,
        "gosh_status": {
            "model": "MiniMax M2.5",
            "active": True,
            "last_refresh": date.today().isoformat(),
        },
    })


@APP.route("/")
def index():
    return send_from_directory(".", "index.html")


if __name__ == "__main__":
    APP.run(host="127.0.0.1", port=8765, debug=False)
