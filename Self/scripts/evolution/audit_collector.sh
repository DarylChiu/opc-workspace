#!/bin/bash
# Self L3自进化 · 一周审计数据采集器
# 由 cron (2026-07-22) 调用，输出结构化数据供审计报告分析
# 用法: bash audit_collector.sh [起始日期 YYYY-MM-DD]

SELF_WS="$HOME/.openclaw/workspace-self"
CHECKER_LOG="$SELF_WS/memory/evolution/checker-log.jsonl"
JOURNAL="$SELF_WS/memory/reflexion_journal.md"
SINCE="${1:-2026-07-15}"

echo "════════════════════════════════════════"
echo "  Self L3自进化 一周审计数据 (since $SINCE)"
echo "  采集时间: $(date '+%Y-%m-%d %H:%M %Z')"
echo "════════════════════════════════════════"

echo ""
echo "───── 1. Checker 使用情况 ─────"
if [ -f "$CHECKER_LOG" ]; then
  python3 << PYEOF
import json
from datetime import datetime
since = "$SINCE"
rows = []
with open("$CHECKER_LOG", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try:
            r = json.loads(line)
            if r.get("ts","")[:10] >= since:
                rows.append(r)
        except: pass

if not rows:
    print("⚠️ 审计期内 Checker 零调用 — Self 可能未执行协议！")
else:
    total = len(rows)
    passed = sum(1 for r in rows if r.get("verdict")=="PASS")
    failed = total - passed
    print(f"调用总次数: {total}")
    print(f"PASS: {passed} ({passed*100//total}%) | FAIL: {failed} ({failed*100//total}%)")
    # 三维平均分趋势(前半段 vs 后半段)
    def avg(rs, dim):
        vs=[r.get("scores",{}).get(dim) for r in rs if r.get("scores",{}).get(dim) is not None]
        return round(sum(vs)/len(vs),1) if vs else None
    half=len(rows)//2
    print(f"\n三维平均分(全期):")
    for d in ["traceability","structure","rigor"]:
        print(f"  {d}: {avg(rows,d)}")
    if half>=1:
        print(f"\n趋势(前{half}次 → 后{len(rows)-half}次):")
        for d in ["traceability","structure","rigor"]:
            a,b=avg(rows[:half],d),avg(rows[half:],d)
            arrow = "↑" if (a and b and b>a) else ("↓" if (a and b and b<a) else "→")
            print(f"  {d}: {a} → {b} {arrow}")
    # 逐日分布
    print(f"\n逐日调用:")
    days={}
    for r in rows:
        d=r.get("ts","")[:10]; days[d]=days.get(d,0)+1
    for d in sorted(days): print(f"  {d}: {days[d]}次")
PYEOF
else
  echo "⚠️ checker-log.jsonl 不存在 — Self 从未调用过 Checker！"
fi

echo ""
echo "───── 2. Reflexion 检讨情况 ─────"
if [ -f "$JOURNAL" ]; then
  TOTAL=$(grep -c '^## ' "$JOURNAL" 2>/dev/null || echo 0)
  SINCE_CNT=$(awk -v s="$SINCE" '/^## /{d=substr($2,1,10); if(d>=s) c++} END{print c+0}' "$JOURNAL")
  echo "检讨总条数: $TOTAL (审计期内新增: $SINCE_CNT)"
  echo ""
  echo "审计期内检讨明细:"
  awk -v s="$SINCE" '/^## /{show=(substr($2,1,10)>=s)} show' "$JOURNAL"
else
  echo "⚠️ reflexion_journal.md 不存在"
fi

echo ""
echo "───── 3. Self 实际执行痕迹 (git) ─────"
cd "$SELF_WS" 2>/dev/null && git log --oneline --since="$SINCE 00:00" 2>/dev/null | head -20 || echo "(无git记录)"

echo ""
echo "───── 4. 文件最后修改时间 ─────"
for f in "$CHECKER_LOG" "$JOURNAL"; do
  [ -f "$f" ] && echo "  $(basename $f): $(stat -f '%Sm' "$f" 2>/dev/null)"
done
echo "════════════════════════════════════════"
