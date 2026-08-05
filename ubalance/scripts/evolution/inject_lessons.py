#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_lessons.py — M2 教训注入器（全量/轻量）

配合 classify_task.py 使用:
  A. 🆕 新任务   → 全量注入（三层检索 top-5）
  C. 📤 产出升级 → 轻量注入（只注入交付物类模式 top-3）

输出: 注入的教训文本块（Agent 将其拼入上下文）+ 记录到 task_state

用法:
  python3 inject_lessons.py --msg "<任务>" [--project <项目>] [--mode full|light] [--session <id>] [--debug]
"""
import json
import os
import sys
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.environ.get("WORKSPACE") or os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
sys.path.insert(0, os.path.join(WORKSPACE, "scripts/evolution"))
from retrieve_patterns import retrieve, load as _load

STATE_DIR = os.path.join(WORKSPACE, "memory/evolution/state")
STATE_FILE = os.path.join(STATE_DIR, "task_state.json")

# 轻量注入只保留这些类别
LIGHT_CATEGORIES = ["data_provenance", "traceability", "documentation", "reporting"]

# 注入模板
FULL_TEMPLATE = """⚠️ 历史教训（自进化基建L1 · 任务开始注入）:
{items}
执行时请规避以上历史错误。"""

LIGHT_TEMPLATE = """⚠️ 产出物规范（自进化基建L1 · 交付物升级注入）:
{items}
产出物请遵守以上规范。"""


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"sessions": {}}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sessions": {}}


def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def inject(msg, project=None, mode="full", session_id="default", topk=5, debug=False):
    """mode=full: 全量三层检索; mode=light: 只交付物类"""
    patterns = retrieve(msg, project, topk=topk, debug=False)

    if mode == "light":
        patterns = [p for p in patterns if p.get("category") in LIGHT_CATEGORIES]
        if len(patterns) < 3:
            # 补足：放宽到全部里再取（但保持 ≤3）
            patterns = retrieve(msg, project, topk=5, debug=False)[:3]
        patterns = patterns[:3]
        template = LIGHT_TEMPLATE
    else:
        patterns = patterns[:topk]
        template = FULL_TEMPLATE

    if not patterns:
        if debug:
            print("ℹ️ 无相关教训，零注入")
        return {"injected": 0, "text": "", "patterns": []}

    items = "\n".join(
        f"- [{p.get('category')}] {p.get('text', '')[:120]}"
        for p in patterns
    )
    text = template.format(items=items)

    # 记录注入到 task_state
    state = load_state()
    sess = state["sessions"].get(session_id, {})
    injected_ids = [p.get("id") for p in patterns]
    prev = sess.get("injected_patterns", [])
    sess["injected_patterns"] = list(dict.fromkeys(prev + injected_ids))
    state["sessions"][session_id] = sess
    save_state(state)

    result = {
        "injected": len(patterns),
        "mode": mode,
        "text": text,
        "patterns": injected_ids,
        "token_estimate": len(text) // 2,
    }

    if debug:
        print(f"📥 注入模式: {mode} | 数量: {len(patterns)}")
        for p in patterns:
            print(f"  + [{p.get('id')}] {p.get('text', '')[:60]}")
        print(f"\n{text}")
        print(f"\n📊 token估算: ~{result['token_estimate']}")

    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--msg", required=True)
    ap.add_argument("--project", default=None)
    ap.add_argument("--mode", choices=["full", "light"], default="full")
    ap.add_argument("--session", default="default")
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    result = inject(args.msg, args.project, args.mode, args.session, args.topk, args.debug)
    if not args.debug:
        print(json.dumps(result, ensure_ascii=False, indent=2))
