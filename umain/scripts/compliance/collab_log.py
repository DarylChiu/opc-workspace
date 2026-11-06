#!/usr/bin/env python3
"""
collab_log.py — Agent 协作记录器
2026-11-06 建立。Daryl 要求：Agent 之间沟通要可视化，在看板上呈现。

职责：
  1. 记录每次跨 Agent 沟通（谁问、谁答、几轮、有无分歧）
  2. 记录辩论过程（分歧点、双方观点、结论）
  3. 写入看板可读的 JSON 数据源

Daryl 的角色定位（2026-11-06 确认）：
  - Kitty = B(呈现者) + C(问假设者)，不做 A(拍板者)
  - 完整呈现辩论过程，关键假设问 Daryl

用法：
  collab_log.py start --topic "微风是否更换" --agents kitty,bryson
  collab_log.py add-turn --topic-id X --from kitty --to bryson --content "..."
  collab_log.py add-dispute --topic-id X --point "自动切节点能否救故障" --a "kitty:能" --b "bryson:不能" --verdict "bryson对"
  collab_log.py finish --topic-id X --conclusion "..." --pending "Bryson建议关系统代理"
  collab_log.py list
  collab_log.py show --topic-id X
"""
import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime

BASE = os.path.expanduser("~/.openclaw/workspace")
OUT_DIR = os.path.join(BASE, "memory", "collab")
OUT_FILE = os.path.join(OUT_DIR, "topics.json")
BOARD_FILE = os.path.join(BASE, "opc_dashboard", "data", "collab_records.json")

# 看板上真正在跑的那份
DASHBOARD_CANDIDATES = [
    "/Users/zhaoyuzhao/WorkBuddy/Claw/opc-dashboard/data/collab_records.json",
]


def _load():
    if not os.path.exists(OUT_FILE):
        return {"topics": []}
    try:
        with open(OUT_FILE) as f:
            return json.load(f)
    except Exception:
        return {"topics": []}


def _save(data):
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = OUT_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, OUT_FILE)
    _sync_to_board(data)


def _sync_to_board(data):
    """同步到看板数据目录（多个候选路径都写，保证看板能读到）"""
    payload = {
        "ok": True,
        "generatedAt": datetime.now().isoformat(),
        "topics": data.get("topics", []),
    }
    targets = [BOARD_FILE] + DASHBOARD_CANDIDATES
    for p in targets:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[warn] 写入 {p} 失败: {e}", file=sys.stderr)


def _find(data, topic_id):
    for t in data.get("topics", []):
        if t.get("id") == topic_id or t.get("slug") == topic_id:
            return t
    return None


def cmd_start(args):
    data = _load()
    tid = "ct_" + uuid.uuid4().hex[:8]
    topic = {
        "id": tid,
        "title": args.topic,
        "agents": [a.strip() for a in args.agents.split(",") if a.strip()],
        "status": "进行中",
        "startedAt": datetime.now().isoformat(timespec="seconds"),
        "endedAt": None,
        "turns": [],
        "disputes": [],
        "conclusion": "",
        "pendingForDaryl": [],
        "rounds": 0,
    }
    data.setdefault("topics", []).insert(0, topic)
    _save(data)
    print(tid)


def cmd_add_turn(args):
    data = _load()
    t = _find(data, args.topic_id)
    if not t:
        print(f"找不到话题 {args.topic_id}", file=sys.stderr)
        return 1
    t["turns"].append({
        "n": len(t["turns"]) + 1,
        "from": args.sender,
        "to": args.to or "",
        "content": args.content,
        "at": datetime.now().isoformat(timespec="seconds"),
    })
    t["rounds"] = len(t["turns"])
    _save(data)
    print(f"{t['id']} turn#{len(t['turns'])}")


def cmd_add_dispute(args):
    data = _load()
    t = _find(data, args.topic_id)
    if not t:
        print(f"找不到话题 {args.topic_id}", file=sys.stderr)
        return 1
    t["disputes"].append({
        "point": args.point,
        "a": args.a,
        "b": args.b,
        "verdict": args.verdict or "",
        "at": datetime.now().isoformat(timespec="seconds"),
    })
    _save(data)
    print(f"{t['id']} dispute#{len(t['disputes'])}")


def cmd_finish(args):
    data = _load()
    t = _find(data, args.topic_id)
    if not t:
        print(f"找不到话题 {args.topic_id}", file=sys.stderr)
        return 1
    t["status"] = args.status or "已结束"
    t["conclusion"] = args.conclusion or ""
    t["endedAt"] = datetime.now().isoformat(timespec="seconds")
    if args.pending:
        t["pendingForDaryl"] = [p.strip() for p in args.pending.split("|") if p.strip()]
    _save(data)
    print(f"{t['id']} finished")


def cmd_list(args):
    data = _load()
    topics = data.get("topics", [])
    if not topics:
        print("暂无协作记录")
        return
    for t in topics[:20]:
        disputes = len(t.get("disputes", []))
        print(f"{t['id']}  [{t['status']}]  {t['title']}")
        print(f"    参与: {', '.join(t.get('agents', []))} | 轮次: {t.get('rounds', 0)} | 分歧: {disputes}")
        if t.get("startedAt"):
            print(f"    时间: {t['startedAt'][:16].replace('T', ' ')}")
        if t.get("conclusion"):
            print(f"    结论: {t['conclusion'][:80]}")
        print()


def cmd_show(args):
    data = _load()
    t = _find(data, args.topic_id)
    if not t:
        print(f"找不到话题 {args.topic_id}", file=sys.stderr)
        return 1
    print(json.dumps(t, ensure_ascii=False, indent=2))


def main():
    p = argparse.ArgumentParser(description="Agent 协作记录器")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("start", help="开一个新话题")
    s.add_argument("--topic", required=True)
    s.add_argument("--agents", required=True, help="逗号分隔，如 kitty,bryson")
    s.set_defaults(func=cmd_start)

    s = sub.add_parser("add-turn", help="记录一轮发言")
    s.add_argument("--topic-id", required=True)
    s.add_argument("--from", dest="sender", required=True)
    s.add_argument("--to", default="")
    s.add_argument("--content", required=True)
    s.set_defaults(func=cmd_add_turn)

    s = sub.add_parser("add-dispute", help="记录一个分歧点")
    s.add_argument("--topic-id", required=True)
    s.add_argument("--point", required=True)
    s.add_argument("--a", required=True)
    s.add_argument("--b", required=True)
    s.add_argument("--verdict", default="")
    s.set_defaults(func=cmd_add_dispute)

    s = sub.add_parser("finish", help="结束话题")
    s.add_argument("--topic-id", required=True)
    s.add_argument("--conclusion", default="")
    s.add_argument("--pending", default="", help="待Daryl决策项，用 | 分隔")
    s.add_argument("--status", default="已结束")
    s.set_defaults(func=cmd_finish)

    s = sub.add_parser("list", help="列出全部话题")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("show", help="查看某话题详情")
    s.add_argument("--topic-id", required=True)
    s.set_defaults(func=cmd_show)

    args = p.parse_args()
    rc = args.func(args)
    sys.exit(rc or 0)


if __name__ == "__main__":
    main()
