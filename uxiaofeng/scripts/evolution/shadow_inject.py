#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shadow_inject.py — L1 Phase 0 影子模式注入器（Balance 试点专用）

影子模式 = 完整跑「分类 + 检索」流水线，但【零注入】到 Agent 上下文。
所有"本应注入什么"追加写入 shadow_log.jsonl，供测试期结束评估精度。

设计要点:
  1. 独立 shadow 状态机（task_state_shadow.json）— 不污染线上 task_state
  2. Fail-open: 任何异常 → exit 0 + SHADOW-ERROR 标记，绝不阻塞 Agent 任务
  3. stdout 只输出 SHADOW 标记行，提醒 Agent「本次无注入，正常执行任务」
  4. 与线上 inject_lessons.py 逻辑一致: new_task→full top5 / deliverable→light top3 / 其余→零注入

用法:
  python3 shadow_inject.py --msg "<任务描述>" [--project <项目>] [--session <id>] [--agent balance] [--debug]

输出: stdout 一行标记 + 追加 shadow_log.jsonl 一条记录

周五评估: python3 shadow_report.py   (统计命中/噪音/误判 + 生成评估摘要)
"""
import json
import os
import sys
import datetime
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.environ.get("WORKSPACE") or os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
SHADOW_DIR = os.path.join(WORKSPACE, "memory/evolution/shadow")
SHADOW_LOG = os.path.join(SHADOW_DIR, "shadow_log.jsonl")
SHADOW_STATE = os.path.join(WORKSPACE, "memory/evolution/state/task_state_shadow.json")

# 与 inject_lessons.py 保持一致的轻量注入类别
LIGHT_CATEGORIES = ["data_provenance", "traceability", "documentation", "reporting"]

sys.path.insert(0, os.path.join(WORKSPACE, "scripts/evolution"))
import classify_task
import retrieve_patterns


def load_shadow_state():
    if not os.path.exists(SHADOW_STATE):
        return {"sessions": {}}
    try:
        with open(SHADOW_STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sessions": {}}


def save_shadow_state(state):
    os.makedirs(os.path.dirname(SHADOW_STATE), exist_ok=True)
    with open(SHADOW_STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def append_log(rec):
    os.makedirs(SHADOW_DIR, exist_ok=True)
    with open(SHADOW_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def simulate_inject(decision, task, project):
    """模拟 inject_lessons.py 的注入选择（不写入任何 state）"""
    if decision == "new_task":
        mode, topk = "full", 5
    elif decision == "deliverable_upgrade":
        mode, topk = "light", 3
    else:
        return {"mode": "none", "patterns": [], "token_estimate": 0}

    patterns = retrieve_patterns.retrieve(task, project, topk=5)
    if mode == "light":
        light = [p for p in patterns if p.get("category") in LIGHT_CATEGORIES]
        patterns = (light if len(light) >= 3 else patterns)[:3]
    else:
        patterns = patterns[:topk]

    text = "\n".join(f"- [{p.get('category')}] {p.get('text', '')[:120]}" for p in patterns)
    return {
        "mode": mode,
        "patterns": [{
            "id": p.get("id"),
            "category": p.get("category"),
            "text": p.get("text", "")[:200],
            "severity": p.get("severity"),
            "rule_hit": p.get("_rule_hit", False),
        } for p in patterns],
        "token_estimate": len(text) // 2 if text else 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--msg", required=True, help="任务消息原文")
    ap.add_argument("--project", default=None)
    ap.add_argument("--session", default="default")
    ap.add_argument("--agent", default="balance")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    try:
        # 1) 分类（影子状态机：运行期替换 STATE_FILE，不污染线上）
        classify_task.STATE_FILE = SHADOW_STATE
        result = classify_task.classify(args.msg, args.session, args.project, debug=False)
        decision = result["decision"]

        # 2) 模拟注入
        sim = simulate_inject(decision, args.msg, args.project)

        # 3) 记录
        rec = {
            "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "agent": args.agent,
            "session": args.session,
            "project": args.project,
            "msg": args.msg[:200],
            "msg_hash": classify_task.subject_hash(args.msg),
            "decision": decision,
            "reason": result.get("reason", ""),
            "task_id": result.get("task_id"),
            "task_type": result.get("type"),
            "simulated_injection": sim,
            "injected": 0,  # 影子模式铁律：实际注入恒为0
            "verdict": None,  # 周五评估时回填: hit|noise|misjudge
        }
        append_log(rec)

        if args.debug:
            print(json.dumps(rec, ensure_ascii=False, indent=2))
        else:
            print(f"🔒 SHADOW-LOGGED: 判定={decision}, 本应注入({sim['mode']}) {len(sim['patterns'])}条 → 已记录, 实际注入0")
        # 影子模式：不输出任何教训文本
        return 0
    except Exception as e:
        print(f"🔒 SHADOW-ERROR: {e} → 本次不注入, 任务继续 (fail-open)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
