#!/bin/bash
# L4 Audit Cron Wrapper — runs audit and reports to OPC group
WORKSPACE="${OPENCLAW_WORKSPACE:-/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace}"
cd "$WORKSPACE" || exit 1

TODAY=$(date +%Y年%m月%d日)

# Run audit
RESULT=$(bash scripts/compliance/audit.sh --report 2>&1)
EXIT_CODE=$?

# Build report message
if echo "$RESULT" | grep -q "问题遗留: 0"; then
    MSG="✅ 已完成今日（${TODAY}）的记忆系统审计，所有检查通过"
else
    ISSUE_COUNT=$(echo "$RESULT" | grep "问题遗留:" | grep -o '[0-9]\+' | tail -1)
    MSG="⚠️ 已完成今日（${TODAY}）的记忆系统审计，${ISSUE_COUNT} 项问题已记录"
fi

# Send to OPC group chat
/opt/homebrew/bin/openclaw message send \
    --channel feishu \
    --account xiaofeng \
    --target chat:oc_7d71d54d87cbd265d9c3811bc59840b2 \
    --message "$MSG" >/dev/null 2>&1

exit $EXIT_CODE
