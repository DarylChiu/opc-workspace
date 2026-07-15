#!/bin/bash
# Reflexion — Self(恨点小己) L3自进化基建 M2
# 结构化检讨: 失败→写检讨→下次先读检讨
#
# 写入:  reflect.sh add "任务" "哪错了" "根因" "下次规则"
# 查看:  reflect.sh recent [N]      最近N条(默认5)
# 检索:  reflect.sh search "关键词"
#
# 存储: memory/reflexion_journal.md (在memory/下, memory_search可语义检索)

JOURNAL="$HOME/.openclaw/workspace-self/memory/reflexion_journal.md"
mkdir -p "$(dirname "$JOURNAL")"

# 初始化
if [ ! -f "$JOURNAL" ]; then
cat > "$JOURNAL" << 'HEADER'
# Reflexion 检讨日志 — Self (恨点小己)

> L3自进化基建 · 每次被纠正/Checker两次FAIL/重复犯错时写入
> 动手前先读: `bash scripts/evolution/reflect.sh recent`
> 同类任务先检索: memory_search 本文件

---
HEADER
fi

case "$1" in
  add)
    TASK="$2"; WRONG="$3"; CAUSE="$4"; RULE="$5"
    if [ -z "$TASK" ] || [ -z "$WRONG" ] || [ -z "$CAUSE" ] || [ -z "$RULE" ]; then
      echo "用法: reflect.sh add \"任务\" \"哪错了\" \"根因\" \"下次规则\"" >&2
      exit 2
    fi
    {
      echo ""
      echo "## $(date '+%Y-%m-%d %H:%M') · ${TASK}"
      echo "- **哪错了**: ${WRONG}"
      echo "- **根因**: ${CAUSE}"
      echo "- **下次规则**: ⚡ ${RULE}"
    } >> "$JOURNAL"
    echo "✅ 检讨已写入 ($(grep -c '^## ' "$JOURNAL") 条累计)"
    ;;
  recent)
    N="${2:-5}"
    echo "═══ 最近 ${N} 条检讨 ═══"
    # 取最后N个 '## ' 段落
    awk '/^## /{n++} {lines[NR]=$0; if(/^## /) starts[n]=NR} END{
      from = (n>'"$N"') ? starts[n-'"$N"'+1] : starts[1];
      if (n==0) { print "(暂无检讨记录)"; exit }
      for(i=from;i<=NR;i++) print lines[i]
    }' "$JOURNAL"
    ;;
  search)
    KW="$2"
    [ -z "$KW" ] && { echo "用法: reflect.sh search \"关键词\"" >&2; exit 2; }
    grep -B1 -A4 -i "$KW" "$JOURNAL" || echo "(未找到含「${KW}」的检讨)"
    ;;
  count)
    grep -c '^## ' "$JOURNAL"
    ;;
  *)
    echo "用法: reflect.sh {add|recent|search|count}"
    echo "  add \"任务\" \"哪错了\" \"根因\" \"下次规则\"  — 写检讨"
    echo "  recent [N]                                — 最近N条(默认5)"
    echo "  search \"关键词\"                          — 检索检讨"
    exit 2
    ;;
esac
