#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_exception_report.py — 每日例外上报

决策自主环 M1 · 决策自主层工具之四
规则源: docs/错误预算规则.md「三、例外管理」（Taylor MBE，每日汇总上报一次）

只上报三类例外（不上报例行决策；例行决策全自主，不进账本）:
  超阈值风险   即将/已经触碰预算红线，或风险等级 ≥ 不可逆小范围
  首次情境     从未见过的任务类型/领域（无模式可查）
  用户明确不满 用户主动表达不满或纠正

机制（只加机制，不加细节限制）:
  · add: 例外事件追加到 exception_events.jsonl（append-only）
  · report: 按日期（默认今天）汇总生成 markdown 上报文档
            无例外输出「今日无例外」
  · report --since/--until: 时间范围汇总（供 review_batch.sh 周度聚合复用）

用法:
  add:    python3 daily_exception_report.py add --type <超阈值风险|首次情境|用户明确不满>
          --desc "..." [--agent A] [--task T] [--suggestion "..."] [--events <路径>]
  report: python3 daily_exception_report.py report [--date YYYY-MM-DD]
          [--since ...] [--until ...] [--json] [--events <路径>]

作为模块:
  from daily_exception_report import add_event, load_events, generate_report
"""
import argparse
import datetime
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EVENTS = os.path.join(SCRIPT_DIR, "exception_events.jsonl")

EXCEPTION_TYPES = ("超阈值风险", "首次情境", "用户明确不满")


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def add_event(ex_type, desc, agent="", task="", suggestion="",
              events=DEFAULT_EVENTS):
    """追加一条例外事件。返回写入的事件 dict。"""
    if ex_type not in EXCEPTION_TYPES:
        raise ValueError(f"非法 type: {ex_type}（合法: {'/'.join(EXCEPTION_TYPES)}）")
    if not desc:
        raise ValueError("缺少必填字段: desc")
    ev = {
        "ts": now_iso(), "agent": agent or "", "task": task or "",
        "type": ex_type, "desc": desc, "suggestion": suggestion or "",
    }
    os.makedirs(os.path.dirname(os.path.abspath(events)), exist_ok=True)
    with open(events, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def load_events(date=None, since=None, until=None, events=DEFAULT_EVENTS):
    """读取例外事件。date=单日；since/until=范围（含边界，YYYY-MM-DD）。
    返回 (rows, skipped)。"""
    rows, skipped = [], 0
    if not os.path.exists(events):
        return rows, skipped
    if date:
        since = until = date
    with open(events, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            d = str(ev.get("ts", ""))[:10]
            if since and d < since:
                continue
            if until and d > until:
                continue
            rows.append(ev)
    return rows, skipped


def generate_report(date=None, since=None, until=None, events=DEFAULT_EVENTS):
    """生成每日例外上报 markdown。返回 (markdown_text, events_list)。"""
    rows, skipped = load_events(date, since, until, events=events)
    title_date = date or (since + " ~ " + until) if (since and until) else \
        (date or datetime.date.today().isoformat())
    if not rows:
        md = f"# 每日例外上报 · {title_date}\n\n今日无例外 ✅"
        if skipped:
            md += f"（跳过损坏行 {skipped}）"
        return md, rows

    lines = [f"# 每日例外上报 · {title_date}", ""]
    lines.append(f"## 例外清单（{len(rows)} 条）")
    if skipped:
        lines.append(f"> ⚠️ 跳过损坏行 {skipped}")
    for t in EXCEPTION_TYPES:
        group = [r for r in rows if r.get("type") == t]
        if not group:
            continue
        lines.append("")
        lines.append(f"### {t}（{len(group)}）")
        for r in group:
            prefix = f"[{r.get('agent') or '?'}] " + (f"任务: {r.get('task')} — " if r.get("task") else "")
            line = f"- {prefix}{r.get('desc', '')}"
            if r.get("suggestion"):
                line += f"（建议: {r['suggestion']}）"
            lines.append(line)

    lines.append("")
    lines.append("## 建议动作")
    for r in rows:
        if r.get("suggestion"):
            lines.append(f"- {r.get('suggestion')}")
    if not any(r.get("suggestion") for r in rows):
        lines.append("- （无）")
    return "\n".join(lines), rows


def main():
    ap = argparse.ArgumentParser(description="每日例外上报")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_a = sub.add_parser("add", help="追加一条例外事件")
    p_a.add_argument("--events", default=DEFAULT_EVENTS)
    p_a.add_argument("--type", required=True, choices=EXCEPTION_TYPES)
    p_a.add_argument("--desc", required=True)
    p_a.add_argument("--agent", default="")
    p_a.add_argument("--task", default="")
    p_a.add_argument("--suggestion", default="")

    p_r = sub.add_parser("report", help="生成每日例外上报")
    p_r.add_argument("--events", default=DEFAULT_EVENTS)
    p_r.add_argument("--date", default=None, help="YYYY-MM-DD（默认今天）")
    p_r.add_argument("--since", default=None, help="范围起始（含）")
    p_r.add_argument("--until", default=None, help="范围截止（含）")
    p_r.add_argument("--json", action="store_true")

    args = ap.parse_args()

    if args.cmd == "add":
        try:
            ev = add_event(args.type, args.desc, args.agent, args.task,
                           args.suggestion, events=args.events)
        except ValueError as e:
            print(f"❌ {e}", file=sys.stderr)
            import sys
            sys.exit(2)
        print(json.dumps(ev, ensure_ascii=False))

    else:  # report
        md, rows = generate_report(args.date, args.since, args.until,
                                   events=args.events)
        if args.json:
            print(json.dumps({"title_date": args.date or (args.since and f"{args.since} ~ {args.until}") or datetime.date.today().isoformat(),
                              "count": len(rows), "events": rows},
                             ensure_ascii=False))
        else:
            print(md)


if __name__ == "__main__":
    main()
