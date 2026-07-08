#!/bin/bash
# L4: 完整审计 — 每日 23:59 Cron 兜底检查 (Kitty workspace)
# 用法: bash scripts/compliance/audit.sh [--report]
# --report: 输出简洁汇报摘要

WORKSPACE="$HOME/.openclaw/workspace"
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

echo "📋 L4 每日审计 | $TODAY $TIMESTAMP (Kitty)"
echo "================================"

# --- 1. 日记完整性 ---
echo "1/6 日记检查"
TODAY_FILE="memory/$TODAY.md"
if [ -f "$TODAY_FILE" ] && [ -s "$TODAY_FILE" ]; then
    LINES=$(wc -l < "$TODAY_FILE" | tr -d ' ')
    log_ok "今日日记存在 ($LINES 行)"
else
    log_issue "今日日记缺失"
fi

YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
if [ -f "memory/${YESTERDAY}.md" ]; then
    log_ok "昨天日记存在"
else
    log_issue "昨天日记缺失 ($YESTERDAY)"
fi

# --- 2. active_tasks 新鲜度 ---
echo ""
echo "2/6 active_tasks 检查"
if [ -f "memory/_working_active_tasks.md" ]; then
    LAST_MOD=$(stat -f "%m" "memory/_working_active_tasks.md" 2>/dev/null || stat -c "%Y" "memory/_working_active_tasks.md" 2>/dev/null)
    NOW=$(date +%s)
    AGE=$(( (NOW - LAST_MOD) / 3600 ))
    if [ "$AGE" -gt 24 ]; then
        log_issue "active_tasks ${AGE}h 未更新"
    else
        log_ok "active_tasks 新鲜 (${AGE}h)"
    fi
fi

# --- 3. recent_conversations 新鲜度 ---
echo ""
echo "3/6 recent_conversations 检查"
if [ -f "memory/_working_recent_conversations.md" ]; then
    LAST_MOD=$(stat -f "%m" "memory/_working_recent_conversations.md" 2>/dev/null || stat -c "%Y" "memory/_working_recent_conversations.md" 2>/dev/null)
    NOW=$(date +%s)
    AGE=$(( (NOW - LAST_MOD) / 3600 ))
    if [ "$AGE" -gt 72 ]; then
        log_issue "recent_conversations ${AGE}h 未更新"
    else
        log_ok "recent_conversations 新鲜 (${AGE}h)"
    fi
fi

# --- 4. episodes 检查 ---
echo ""
echo "4/6 episodes 检查"
EPISODE_COUNT=$(find memory -maxdepth 1 -name "learning_*.md" -o -name "incident_*.md" -o -name "project_*.md" 2>/dev/null | wc -l | tr -d ' ')
echo "  ℹ️ 现有 $EPISODE_COUNT 个 episode 文件"
# 检查是否有今天的 episode
if find memory -maxdepth 1 \( -name "learning_*.md" -o -name "incident_*.md" \) -newer "memory/_working_active_tasks.md" 2>/dev/null | grep -q .; then
    log_ok "最近有新 episode 产出"
else
    echo "  ℹ️ 最近无新 episode（可能不需要）"
fi

# --- 5. 清理过期日记 ---
echo ""
echo "5/6 归档检查"
mkdir -p memory_v2/archive
ARCHIVE_COUNT=0
for f in memory/202[0-9]-[01][0-9]-[0-3][0-9].md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .md)
    FILE_DATE_EPOCH=$(date -j -f "%Y-%m-%d" "$BASENAME" +%s 2>/dev/null || date -d "$BASENAME" +%s 2>/dev/null)
    if [ -n "$FILE_DATE_EPOCH" ]; then
        NOW=$(date +%s)
        DAYS_OLD=$(( (NOW - FILE_DATE_EPOCH) / 86400 ))
        if [ "$DAYS_OLD" -gt 30 ]; then
            ARCHIVE_COUNT=$((ARCHIVE_COUNT + 1))
            mv "$f" memory_v2/archive/ 2>/dev/null && log_fix "归档 $BASENAME.md"
        fi
    fi
done
[ "$ARCHIVE_COUNT" -eq 0 ] && log_ok "无需归档"

# --- 6. 核心文件完整性 ---
echo ""
echo "6/6 核心文件检查"
for f in SOUL.md MEMORY.md AGENTS.md; do
    [ -f "$f" ] && log_ok "$f 存在" || log_issue "$f 缺失"
done

# --- 总结 ---
echo ""
echo "================================"
echo "📊 审计完成 | 修复: $FIXES | 问题遗留: $ISSUES"

AUDIT_LOG="memory/compliance-audit.jsonl"
cat >> "$AUDIT_LOG" << EOF
{"timestamp":"$TIMESTAMP","check":"L4-audit-kitty","fixes":$FIXES,"issues":$ISSUES}
EOF

if [ "$REPORT_MODE" = true ]; then
    if [ "$ISSUES" -eq 0 ]; then
        echo "✅ 记忆系统健康，所有检查通过"
    else
        echo "⚠️ 有 $ISSUES 个问题需要关注，$FIXES 项已自动修复"
    fi
fi

exit $ISSUES
