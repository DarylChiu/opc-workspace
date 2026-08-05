#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
error_budget.py — 周度错误预算（结果导向）

决策自主环 M1 · 决策自主层工具之三
规则源: docs/错误预算规则.md（修订#5 定稿，结果导向，替代信任档位）

后果分级（客观判级，无需主观打分）:
  0.1   可逆 + 低影响（代码可回滚、可重来、无对外影响）
  1     不可逆 + 小范围（发错一条消息、不可回退的局部操作）
  10    不可逆 + 大范围（删数据/对外承诺/大规模影响）→ P0 直接拦截：
        不进预算（cost=0, blocked），直接上报/人工接管

预算循环（周期制，周一开始）:
  周内累计消耗 < 预算       → 全自主 L3（默认档）
  周内累计消耗 ≥ 预算（耗尽）→ 降档 L3→L2（输出降档信号）
  下周开始自动重置回满额、回升 L3
  单个错误不降档 —— 只有「周总量超支」才刹车（给创造力留呼吸空间）

磨合期保护（新角色/新领域 2-4 周）:
  --grace <key> 标记期内错误只记账不耗预算（cost=0, grace 留痕），只入病理库

机制:
  · 每笔消耗逐条记入 error_budget_ledger.jsonl（ts/week/agent/task/desc/level/cost/blocked/grace/is_exception/tier）
  · 状态存 error_budget_state.json（week_id/budget/consumed/tier），跨周自动重置
  · 周度预算默认 2.0（占位常量，部署方可调；机制要求=固定总量）

用法:
  record: python3 error_budget.py record --level 0.1|1|10 --desc "..." [--agent A] [--task T] [--exception] [--grace <key>]
  status: python3 error_budget.py status
  list:   python3 error_budget.py list [--since YYYY-MM-DD] [--until YYYY-MM-DD]
  reset:  python3 error_budget.py reset    # 强制重置当前周（测试/人工）
  全局:   [--ledger <路径>] [--state <路径>] [--budget <数值>]

作为模块:
  from error_budget import record_error, get_status, list_entries
"""
import argparse
import datetime
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LEDGER = os.path.join(SCRIPT_DIR, "error_budget_ledger.jsonl")
DEFAULT_STATE = os.path.join(SCRIPT_DIR, "error_budget_state.json")
DEFAULT_BUDGET = 2.0  # 周度预算默认值（占位常量，部署方可调）

LEVELS = {
    0.1: "可逆+低影响",
    1.0: "不可逆+小范围",
    10.0: "不可逆+大范围(P0拦截)",
}
TIER_L3, TIER_L2 = "L3", "L2"


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def monday_of(d):
    return d - datetime.timedelta(days=d.weekday())


def current_week_id():
    return monday_of(datetime.date.today()).isoformat()


def load_state(state_path, budget):
    if os.path.exists(state_path):
        try:
            with open(state_path, encoding="utf-8") as f:
                st = json.load(f)
            st.setdefault("budget", float(budget))
            return st
        except Exception:
            pass
    return {"week_id": current_week_id(), "budget": float(budget),
            "consumed": 0.0, "tier": TIER_L3}


def save_state(state, state_path):
    os.makedirs(os.path.dirname(os.path.abspath(state_path)), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _ensure_current_week(state, budget):
    """跨周自动重置：周内累计归零、档位回升 L3。返回是否发生重置。"""
    week = current_week_id()
    if state.get("week_id") != week:
        state["week_id"] = week
        state["consumed"] = 0.0
        state["tier"] = TIER_L3
        state["budget"] = float(budget)
        return True
    return False


def _append_ledger(rec, ledger):
    os.makedirs(os.path.dirname(os.path.abspath(ledger)), exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def record_error(level, desc, agent="", task="", is_exception=False, grace=None,
                 ledger=DEFAULT_LEDGER, state_path=DEFAULT_STATE, budget=None):
    """记录一笔错误消耗。返回结果 dict。

    level: 0.1 / 1 / 10
    grace: 磨合期标记（新角色/新领域 key），期内不耗预算
    返回: {action, level, cost, blocked, grace, consumed, budget, tier,
          downgraded, message, record}
    """
    budget = budget if budget is not None else float(
        os.environ.get("ERROR_BUDGET_WEEKLY", DEFAULT_BUDGET))
    level = float(level)
    if level not in LEVELS:
        raise ValueError(f"非法 level: {level}（合法: 0.1/1/10）")

    st = load_state(state_path, budget)
    reset = _ensure_current_week(st, budget)

    week = st["week_id"]
    base = {
        "ts": now_iso(), "week": week, "agent": agent or "", "task": task or "",
        "desc": desc, "level": level,
    }
    downgraded = False

    if level >= 10.0:
        # P0 拦截：不进预算，直接上报/人工接管
        rec = {**base, "cost": 0.0, "blocked": True, "grace": grace or "",
               "is_exception": True, "tier": st["tier"]}
        _append_ledger(rec, ledger)
        result = {"action": "P0_BLOCK", "message":
                  "⛔ P0 拦截：不可逆+大范围错误，不进预算，直接上报/人工接管"}
    elif grace:
        # 磨合期：只记账不耗预算（只入病理库）
        rec = {**base, "cost": 0.0, "blocked": False, "grace": grace,
               "is_exception": bool(is_exception), "tier": st["tier"]}
        _append_ledger(rec, ledger)
        result = {"action": "grace",
                  "message": f"🛡️ 磨合期({grace})：错误只记账不耗预算（cost=0），只入病理库"}
    else:
        cost = level
        st["consumed"] = round(st["consumed"] + cost, 2)
        if st["tier"] == TIER_L3 and st["consumed"] >= st["budget"]:
            st["tier"] = TIER_L2
            downgraded = True
        rec = {**base, "cost": cost, "blocked": False, "grace": "",
               "is_exception": bool(is_exception), "tier": st["tier"]}
        _append_ledger(rec, ledger)
        if downgraded:
            result = {"action": "recorded",
                      "message": "⚠️ 周预算耗尽：L3→L2 降档（下周自动重置回升）"}
        else:
            result = {"action": "recorded", "message": "已记账"}

    save_state(st, state_path)
    result.update({
        "level": level, "cost": rec["cost"], "blocked": rec["blocked"],
        "grace": rec["grace"], "consumed": st["consumed"], "budget": st["budget"],
        "tier": st["tier"], "downgraded": downgraded,
        "week_reset": reset, "record": rec,
    })
    return result


def get_status(ledger=DEFAULT_LEDGER, state_path=DEFAULT_STATE, budget=None):
    """当前周预算状态（跨周自动重置）。"""
    budget = budget if budget is not None else float(
        os.environ.get("ERROR_BUDGET_WEEKLY", DEFAULT_BUDGET))
    st = load_state(state_path, budget)
    reset = _ensure_current_week(st, budget)
    if reset:
        save_state(st, state_path)
    return {
        "week_id": st["week_id"], "budget": st["budget"],
        "consumed": st["consumed"], "remaining": round(st["budget"] - st["consumed"], 2),
        "tier": st["tier"],
        "exhausted": st["consumed"] >= st["budget"],
        "downgraded": st["tier"] == TIER_L2,
    }


def list_entries(since=None, until=None, ledger=DEFAULT_LEDGER):
    """列出预算账本条目（可按日期范围过滤，含边界）。返回 (rows, skipped)。"""
    rows, skipped = [], 0
    if not os.path.exists(ledger):
        return rows, skipped
    with open(ledger, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            d = str(rec.get("ts", ""))[:10]
            if since and d < since:
                continue
            if until and d > until:
                continue
            rows.append(rec)
    return rows, skipped


def reset_week(state_path=DEFAULT_STATE, budget=None):
    """强制重置当前周（测试/人工）。"""
    budget = budget if budget is not None else float(
        os.environ.get("ERROR_BUDGET_WEEKLY", DEFAULT_BUDGET))
    st = {"week_id": current_week_id(), "budget": float(budget),
          "consumed": 0.0, "tier": TIER_L3}
    save_state(st, state_path)
    return st


def main():
    ap = argparse.ArgumentParser(description="周度错误预算（结果导向）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_common(p):
        p.add_argument("--ledger", default=DEFAULT_LEDGER)
        p.add_argument("--state", default=DEFAULT_STATE)
        p.add_argument("--budget", type=float, default=None)

    p_r = sub.add_parser("record", help="记录一笔错误消耗")
    add_common(p_r)
    p_r.add_argument("--level", required=True, help="0.1 | 1 | 10")
    p_r.add_argument("--desc", required=True)
    p_r.add_argument("--agent", default="")
    p_r.add_argument("--task", default="")
    p_r.add_argument("--exception", action="store_true")
    p_r.add_argument("--grace", default=None, help="磨合期标记 key（期内不耗预算）")

    p_s = sub.add_parser("status", help="查看当前周预算状态")
    add_common(p_s)
    p_l = sub.add_parser("list", help="列出预算账本条目")
    add_common(p_l)
    p_l.add_argument("--since", default=None)
    p_l.add_argument("--until", default=None)

    p_x = sub.add_parser("reset", help="强制重置当前周（测试/人工）")
    add_common(p_x)

    args = ap.parse_args()

    if args.cmd == "record":
        try:
            r = record_error(args.level, args.desc, args.agent, args.task,
                             args.exception, args.grace,
                             ledger=args.ledger, state_path=args.state,
                             budget=args.budget)
        except ValueError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(2)
        print(r["message"])
        print(json.dumps({k: v for k, v in r.items() if k != "record"},
                         ensure_ascii=False, indent=2))
        if r["blocked"]:
            sys.exit(3)  # P0 拦截退出码
    elif args.cmd == "status":
        st = get_status(ledger=args.ledger, state_path=args.state, budget=args.budget)
        print(f"周: {st['week_id']} | 消耗: {st['consumed']} / {st['budget']} "
              f"| 剩余: {st['remaining']} | 档位: {st['tier']}"
              + (" | ⚠️ 已降档 L3→L2" if st["downgraded"] else ""))
    elif args.cmd == "list":
        rows, skipped = list_entries(args.since, args.until, ledger=args.ledger)
        print(f"共 {len(rows)} 条" + (f"（跳过损坏行 {skipped}）" if skipped else ""))
        for r in rows:
            print(f"- [{r.get('ts', '')}] {r.get('agent', '')} | "
                  f"{r.get('task', '')} | level={r.get('level')} cost={r.get('cost')} "
                  f"| {r.get('desc', '')}"
                  + (" | ⛔BLOCKED" if r.get("blocked") else "")
                  + (f" | 🛡️grace:{r.get('grace')}" if r.get("grace") else ""))
    else:  # reset
        st = reset_week(state_path=args.state, budget=args.budget)
        print(f"✅ 已重置第 {st['week_id']} 周：消耗 0，档位 {st['tier']}")


if __name__ == "__main__":
    main()
