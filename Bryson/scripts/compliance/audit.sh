#!/bin/bash
# L4: 完整审计 — 每日 23:59 Cron 兜底检查
# 用法: bash scripts/compliance/audit.sh [--report]
# --report: 输出简洁汇报摘要

WORKSPACE="${OPENCLAW_WORKSPACE:-/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace}"
cd "$WORKSPACE" || exit 1

TODAY=$(date +%Y-%m-%d)
TIMESTAMP=$(date +"%Y-%m-%dT%H:%M:%S%z")
REPORT_MODE=false
[ "$1" = "--report" ] && REPORT_MODE=true

FIXES=0
ISSUES=0

log_fix() { FIXES=$((FIXES + 1)); echo "  🔧 $1"; }
log_issue() { ISSUES=$((ISSUES + 1)); echo "  ❌ $1"; }
log_ok() { echo "  ✅ $1"; }

echo "📋 L4 每日审计 | $TODAY $TIMESTAMP"
echo "================================"

# --- 1. 日记完整性 ---
echo "1/5 日记检查"
TODAY_FILE="memory/$TODAY.md"
if [ -f "$TODAY_FILE" ] && [ -s "$TODAY_FILE" ]; then
    LINES=$(wc -l < "$TODAY_FILE" | tr -d ' ')
    SECTIONS=$(grep -c "^##" "$TODAY_FILE" || echo 0)
    log_ok "日记存在 ($LINES 行, $SECTIONS 段落)"
else
    log_issue "今日日记缺失"
fi

# 检查昨天日记
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
if [ -f "memory/${YESTERDAY}.md" ]; then
    log_ok "昨天日记存在"
else
    log_issue "昨天日记缺失 ($YESTERDAY)"
fi

# --- 2. active.md 新鲜度 ---
echo ""
echo "2/5 active.md 检查"
if [ -f "memory/active.md" ]; then
    LAST_MOD=$(stat -f "%m" "memory/active.md" 2>/dev/null || stat -c "%Y" "memory/active.md" 2>/dev/null)
    NOW=$(date +%s)
    AGE=$(( (NOW - LAST_MOD) / 3600 ))
    if [ "$AGE" -gt 24 ]; then
        log_issue "active.md ${AGE}h 未更新"
    else
        log_ok "active.md 新鲜 (${AGE}h)"
    fi
fi

# --- 3. lessons.md 覆盖 ---
echo ""
echo "3/5 lessons.md 检查"
if [ -f "memory/lessons.md" ]; then
    LESSON_LINES=$(wc -l < "memory/lessons.md" | tr -d ' ')
    # 检查是否有今天的新条目
    if grep -q "$TODAY" "memory/lessons.md" 2>/dev/null; then
        log_ok "lessons.md 有今日记录"
    else
        echo "  ℹ️ lessons.md 无需今日更新"
    fi
else
    log_issue "lessons.md 缺失"
fi

# --- 4. 清理过期日记 ---
echo ""
echo "4/5 归档检查"
ARCHIVE_COUNT=0
for f in memory/202[0-9]-[01][0-9]-[0-3][0-9].md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .md)
    # 解析日期
    FILE_DATE_EPOCH=$(date -j -f "%Y-%m-%d" "$BASENAME" +%s 2>/dev/null || date -d "$BASENAME" +%s 2>/dev/null)
    if [ -n "$FILE_DATE_EPOCH" ]; then
        NOW=$(date +%s)
        DAYS_OLD=$(( (NOW - FILE_DATE_EPOCH) / 86400 ))
        if [ "$DAYS_OLD" -gt 30 ]; then
            ARCHIVE_COUNT=$((ARCHIVE_COUNT + 1))
        fi
    fi
done

if [ "$ARCHIVE_COUNT" -gt 0 ]; then
    echo "  📦 $ARCHIVE_COUNT 个日记文件超30天，建议归档"
    # 自动归档
    mkdir -p memory/archive
    for f in memory/202[0-9]-[01][0-9]-[0-3][0-9].md; do
        [ -f "$f" ] || continue
        BASENAME=$(basename "$f" .md)
        FILE_DATE_EPOCH=$(date -j -f "%Y-%m-%d" "$BASENAME" +%s 2>/dev/null || date -d "$BASENAME" +%s 2>/dev/null)
        NOW=$(date +%s)
        DAYS_OLD=$(( (NOW - FILE_DATE_EPOCH) / 86400 ))
        if [ "$DAYS_OLD" -gt 30 ]; then
            mv "$f" memory/archive/ 2>/dev/null && log_fix "归档 $BASENAME.md"
        fi
    done
else
    log_ok "无需归档"
fi

# --- 5. MEMORY.md 大小 ---
echo ""
echo "5/5 MEMORY.md 检查"
if [ -f "MEMORY.md" ]; then
    MEM_LINES=$(wc -l < "MEMORY.md" | tr -d ' ')
    if [ "$MEM_LINES" -gt 40 ]; then
        log_issue "MEMORY.md 过大 (${MEM_LINES}行, 建议<30)"
    else
        log_ok "MEMORY.md ${MEM_LINES}行, 符合规范"
    fi
fi

# --- 总结 ---
echo ""
echo "================================"
echo "📊 审计完成 | 修复: $FIXES | 问题遗留: $ISSUES"

AUDIT_LOG="memory/compliance-audit.jsonl"
mkdir -p memory
cat >> "$AUDIT_LOG" << EOF
{"timestamp":"$TIMESTAMP","check":"L4-audit","fixes":$FIXES,"issues":$ISSUES}
EOF

if [ "$REPORT_MODE" = true ]; then
    if [ "$ISSUES" -eq 0 ]; then
        echo "✅ 记忆系统健康，所有检查通过"
    else
        echo "⚠️ 有 $ISSUES 个问题需要关注，$FIXES 项已自动修复"
    fi
fi

exit $ISSUES
