#!/bin/bash
# L4 Audit Cron Wrapper — runs audit, git backups, and reports to OPC group
WORKSPACE="${OPENCLAW_WORKSPACE:-/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace}"
OPC_REPO="/Users/zhaoyuzhao/opc-workspace"
cd "$WORKSPACE" || exit 1

TODAY=$(date +%Y年%m月%d日)
TODAY_EN=$(date +%Y-%m-%d)

# Run audit
RESULT=$(bash scripts/compliance/audit.sh --report 2>&1)
AUDIT_EXIT=$?

# --- Git backup: opc-workspace ---
GIT_MSG=""
if [ -d "$OPC_REPO/.git" ]; then
    cd "$OPC_REPO"
    git pull --rebase origin main 2>/dev/null
    git add -A 2>/dev/null
    if ! git diff --cached --quiet 2>/dev/null; then
        git commit -m "auto: 每日记忆备份 ${TODAY_EN}" 2>/dev/null
        git push origin main 2>/dev/null && GIT_MSG="，Git 备份已推送" || GIT_MSG="，Git push 失败"
    else
        GIT_MSG="，Git 无变更"
    fi
    cd "$WORKSPACE"
fi

# Build report message
if echo "$RESULT" | grep -q "问题遗留: 0"; then
    MSG="✅ 已完成今日（${TODAY}）的记忆系统审计，所有检查通过${GIT_MSG}"
else
    ISSUE_COUNT=$(echo "$RESULT" | grep "问题遗留:" | grep -o '[0-9]\+' | tail -1)
    MSG="⚠️ 已完成今日（${TODAY}）的记忆系统审计，${ISSUE_COUNT} 项问题已记录${GIT_MSG}"
fi

# Send to OPC group chat
/opt/homebrew/bin/openclaw message send \
    --channel feishu \
    --account xiaofeng \
    --target chat:oc_7d71d54d87cbd265d9c3811bc59840b2 \
    --message "$MSG" >/dev/null 2>&1

exit $AUDIT_EXIT
