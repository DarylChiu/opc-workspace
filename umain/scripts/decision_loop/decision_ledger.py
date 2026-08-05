#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
decision_ledger.py — 决策账本（append-only JSONL）

决策自主环 M1 · 决策自主层工具之二
规则源: LOOP_ENGINEERING_PLAN.md「九·颠覆性修订#2 决策账本」+「三.3 批量审批」

每个自主决策记录（最小必要字段）:
  ts             时间戳 ISO8601（默认当前时间）
  agent          Agent ID
  task           任务
  decision_type  决策分类（方向型/规则型/执行型）
  chosen         选了什么
  alternatives   备选方案（list，可选）
  why            为什么
  rejected       放弃了什么（可选）
  is_exception   是否例外（bool，可选，默认 false）

机制（只加机制，不加细节限制）:
  · append-only JSONL 写入：只能追加，不覆盖不改写历史行
  · 查询: 按 agent 或按时间范围（--since/--until，含边界，按日期 YYYY-MM-DD）
  · 行损坏跳过并计数，不中断查询

用法:
  append: python3 decision_ledger.py append --record '<json>'
          [--ledger <路径>]   # 默认 scripts/decision_loop/decision_ledger.jsonl
  query:  python3 decision_ledger.py query [--agent A] [--since YYYY-MM-DD]
          [--until YYYY-MM-DD] [--json] [--ledger <路径>]

作为模块:
  from decision_ledger import append_record, query
  append_record({...})
  rows, skipped = query(agent="main", since="2026-08-03", until="2026-08-09")
"""
import argparse
import datetime
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LEDGER = os.path.join(SCRIPT_DIR, "decision_ledger.jsonl")

REQUIRED = ["agent", "task", "decision_type", "chosen", "why"]
ALLOWED = ["ts", "agent", "task", "decision_type", "chosen",
           "alternatives", "why", "rejected", "is_exception"]
VALID_TYPES = ("方向型", "规则型", "执行型")


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def append_record(record, ledger=DEFAULT_LEDGER):
    """追加一条决策记录（append-only）。返回补齐默认值后的完整记录。

    必填: agent / task / decision_type / chosen / why
    非法字段被忽略；损坏不覆盖历史。
    """
    missing = [k for k in REQUIRED if not record.get(k)]
    if missing:
        raise ValueError(f"缺少必填字段: {missing}")
    rec = {k: record[k] for k in ALLOWED if k in record}
    rec.setdefault("ts", now_iso())
    rec.setdefault("alternatives", [])
    rec.setdefault("rejected", "")
    rec.setdefault("is_exception", False)
    if rec["decision_type"] not in VALID_TYPES:
        raise ValueError(f"非法 decision_type: {rec['decision_type']} "
                         f"(合法: {'/'.join(VALID_TYPES)})")
    os.makedirs(os.path.dirname(os.path.abspath(ledger)), exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def query(agent=None, since=None, until=None, ledger=DEFAULT_LEDGER):
    """查询决策记录。since/until 为 'YYYY-MM-DD'，含边界。

    返回: (rows, skipped) — 匹配记录列表 + 跳过损坏行数
    """
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
            if agent and rec.get("agent") != agent:
                continue
            d = str(rec.get("ts", ""))[:10]
            if since and d < since:
                continue
            if until and d > until:
                continue
            rows.append(rec)
    return rows, skipped


def main():
    ap = argparse.ArgumentParser(description="决策账本（append-only JSONL）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_a = sub.add_parser("append", help="追加一条决策记录")
    p_a.add_argument("--record", required=True, help="JSON 字符串（必填字段见模块文档）")
    p_a.add_argument("--ledger", default=DEFAULT_LEDGER)

    p_q = sub.add_parser("query", help="查询决策记录")
    p_q.add_argument("--agent", default=None)
    p_q.add_argument("--since", default=None, help="起始日期 YYYY-MM-DD（含）")
    p_q.add_argument("--until", default=None, help="截止日期 YYYY-MM-DD（含）")
    p_q.add_argument("--json", action="store_true")
    p_q.add_argument("--ledger", default=DEFAULT_LEDGER)

    args = ap.parse_args()

    if args.cmd == "append":
        try:
            record = json.loads(args.record)
        except json.JSONDecodeError as e:
            print(f"❌ --record 不是合法 JSON: {e}", file=sys.stderr)
            sys.exit(2)
        if not isinstance(record, dict):
            print("❌ --record 必须是 JSON 对象", file=sys.stderr)
            sys.exit(2)
        try:
            rec = append_record(record, ledger=args.ledger)
        except ValueError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(2)
        print(json.dumps(rec, ensure_ascii=False))

    else:  # query
        rows, skipped = query(args.agent, args.since, args.until, ledger=args.ledger)
        if args.json:
            print(json.dumps(rows, ensure_ascii=False))
        else:
            print(f"共 {len(rows)} 条" + (f"（跳过损坏行 {skipped}）" if skipped else ""))
            for r in rows:
                print(f"- [{r.get('ts', '')}] {r.get('agent', '')} | "
                      f"{r.get('task', '')} | {r.get('decision_type', '')} | "
                      f"选了什么: {r.get('chosen', '')} | 放弃: {r.get('rejected', '')}")


if __name__ == "__main__":
    import sys
    main()
