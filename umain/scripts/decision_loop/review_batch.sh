#!/bin/bash
# ============================================================
# review_batch.sh — 周度批量审批（每周一次，Daryl 批量确认/纠正）
#
# 规则源: LOOP_ENGINEERING_PLAN.md「三.3 批量审批」+ docs/错误预算规则.md「七、周度记账」
# 汇总本周（周一 ~ 周日）:
#   ① decision_ledger.jsonl      决策账本（按类型统计 + 明细）
#   ② error_budget_ledger.jsonl  错误预算（消耗/剩余/档位/是否降档 + 明细）
#   ③ exception_events.jsonl     例外事件（超阈值风险/首次情境/用户明确不满）
# 生成: scripts/decision_loop/reviews/review_<周一日期>.md（供 Daryl 批量确认/纠正）
#
# 纠正入口（数据闭环）:
#   纠正 → capture_correction.sh --type correction 写入 corrections_inbox
#        → 周度蒸馏(distill_patterns.py) → 模式库 → 全 Agent 规避
#
# 用法: bash scripts/decision_loop/review_batch.sh [--week YYYY-MM-DD]
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${WORKSPACE:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
DL_DIR="$SCRIPT_DIR"
REVIEWS_DIR="$DL_DIR/reviews"
mkdir -p "$REVIEWS_DIR"

WEEK_ARG=""
if [[ $# -gt 0 ]]; then
  case "$1" in
    --week) WEEK_ARG="${2:-}"; shift 2 ;;
    --week=*) WEEK_ARG="${1#--week=}"; shift ;;
    *) echo "❌ 未知参数: $1（用法: review_batch.sh [--week YYYY-MM-DD]）" >&2; exit 2 ;;
  esac
fi

# ---- 计算本周周一 / 周日 ----
WEEK_START=$(python3 - "$WEEK_ARG" <<'PYEOF'
import sys, datetime
d = datetime.date.today()
if sys.argv[1]:
    d = datetime.date.fromisoformat(sys.argv[1])
m = d - datetime.timedelta(days=d.weekday())
print(m.isoformat())
PYEOF
)
WEEK_END=$(python3 - "$WEEK_START" <<'PYEOF'
import sys, datetime
m = datetime.date.fromisoformat(sys.argv[1])
print((m + datetime.timedelta(days=6)).isoformat())
PYEOF
)

OUT="$REVIEWS_DIR/review_${WEEK_START}.md"

# ---- 聚合生成 review 文档 ----
python3 - "$WEEK_START" "$WEEK_END" "$OUT" "$DL_DIR" <<'PYEOF'
import json
import sys

week_start, week_end, out, dl_dir = sys.argv[1:5]
sys.path.insert(0, dl_dir)

import decision_ledger as dl
import error_budget as eb
import daily_exception_report as der

lines = []
lines.append(f"# 周度批量审批 · {week_start} ~ {week_end}")
lines.append("")
lines.append("> 生成: 决策自主环 review_batch.sh | 供 Daryl 批量确认/纠正（约 15 分钟）")
lines.append("")

# ---- ① 决策账本 ----
decisions, d_skipped = dl.query(since=week_start, until=week_end)
lines.append("## 一、决策账本摘要")
lines.append("")
if not decisions:
    lines.append("本周无自主决策记录。")
else:
    from collections import Counter
    cnt = Counter(r.get("decision_type", "?") for r in decisions)
    parts = " / ".join(f"{t} {n}" for t, n in cnt.items())
    lines.append(f"共 **{len(decisions)}** 条：{parts}。")
    lines.append("")
    lines.append("| 时间 | Agent | 任务 | 分类 | 选了什么 | 放弃了什么 |")
    lines.append("|------|-------|------|------|---------|-----------|")
    for r in decisions:
        lines.append(f"| {r.get('ts', '')[:16]} | {r.get('agent', '')} | "
                     f"{r.get('task', '')} | {r.get('decision_type', '')} | "
                     f"{r.get('chosen', '')} | {r.get('rejected', '')} |")
    if d_skipped:
        lines.append("")
        lines.append(f"> ⚠️ 跳过损坏行 {d_skipped}")
lines.append("")

# ---- ② 错误预算 ----
lines.append("## 二、错误预算")
lines.append("")
st = eb.get_status()
lines.append(f"- 当前周（{st['week_id']}）：消耗 **{st['consumed']}** / {st['budget']}"
             f"，剩余 {st['remaining']}，档位 **{st['tier']}**"
             + ("，⚠️ 已降档 L3→L2" if st.get("downgraded") else "（未降档）"))
budget_rows, b_skipped = eb.list_entries(since=week_start, until=week_end)
if budget_rows:
    lines.append("")
    lines.append("本周预算账本明细：")
    for r in budget_rows:
        flags = ""
        if r.get("blocked"):
            flags += " ⛔P0拦截"
        if r.get("grace"):
            flags += f" 🛡️磨合期({r['grace']})"
        lines.append(f"- [{r.get('ts', '')[:16]}] {r.get('agent', '')} | "
                     f"level={r.get('level')} cost={r.get('cost')} | "
                     f"{r.get('desc', '')}{flags}")
    if b_skipped:
        lines.append(f"> ⚠️ 跳过损坏行 {b_skipped}")
else:
    lines.append("本周无预算消耗记录。")
lines.append("")

# ---- ③ 例外事件 ----
events, e_skipped = der.load_events(since=week_start, until=week_end)
lines.append("## 三、例外汇总")
lines.append("")
if not events:
    lines.append("本周无例外事件。")
else:
    for t in der.EXCEPTION_TYPES:
        group = [e for e in events if e.get("type") == t]
        if not group:
            continue
        lines.append(f"### {t}（{len(group)}）")
        for e in group:
            lines.append(f"- [{e.get('ts', '')[:16]}] {e.get('agent', '')} | "
                         f"{e.get('desc', '')}"
                         + (f"（建议: {e['suggestion']}）" if e.get("suggestion") else ""))
        lines.append("")
    if e_skipped:
        lines.append(f"> ⚠️ 跳过损坏行 {e_skipped}")
lines.append("")

# ---- ④ 待确认 / 纠正 ----
lines.append("## 四、待 Daryl 确认 / 纠正")
lines.append("")
review_items = [r for r in decisions if r.get("decision_type") == "方向型"]
if review_items:
    lines.append("方向型决策（已上报项，请确认或纠正）：")
    for r in review_items:
        lines.append(f"- [{r.get('ts', '')[:16]}] {r.get('agent', '')} | "
                     f"{r.get('task', '')} — {r.get('chosen', '')}")
    lines.append("")
else:
    lines.append("本周无方向型决策待确认。")
if events:
    lines.append("例外事件请一并审阅（第三节）。")
    lines.append("")
lines.append("---")
lines.append("")
lines.append("## 纠正入口（数据闭环）")
lines.append("")
lines.append("对以上任何条目的纠正，请写入纠正池：")
lines.append("")
lines.append("```bash")
lines.append("bash scripts/evolution/capture_correction.sh \\")
lines.append("  --agent <AgentID> --type correction \\")
lines.append("  --text '<上下文 + 错误 + 正确做法>' --source review_batch")
lines.append("```")
lines.append("")
lines.append("纠正自动进 `memory/evolution/corrections_inbox.jsonl` → 周度蒸馏 → 模式库 → 全 Agent 规避。")

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(out)
PYEOF

echo "✅ 周度 review 已生成: $OUT"
echo "纠正入口: bash scripts/evolution/capture_correction.sh --agent <AgentID> --type correction --text '<上下文+错误+正确做法>' --source review_batch"
echo "          → corrections_inbox → 周度蒸馏 → 模式库"
