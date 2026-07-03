#!/bin/bash
# 每日记忆系统合规检查 (23:59触发)
# 检查: 今日日记、active_tasks更新、recent_conversations更新
# 完成后发送群聊汇报

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

WORKSPACE="$HOME/.openclaw/workspace"
TODAY=$(date +%Y-%m-%d)
TODAY_DIARY="$WORKSPACE/memory/$TODAY.md"
ACTIVE_TASKS="$WORKSPACE/memory/_working_active_tasks.md"
RECENT_CONVOS="$WORKSPACE/memory/_working_recent_conversations.md"
GROUP_CHAT="chat:oc_7d71d54d87cbd265d9c3811bc59840b2"
SEND_CMD="/opt/homebrew/bin/node /opt/homebrew/lib/node_modules/openclaw/dist/index.js message send --channel feishu --account default"

# 检查状态
DIARY_OK=false
TASKS_OK=false
CONVOS_OK=false

# 1. 检查今日日记
if [ -f "$TODAY_DIARY" ]; then
    DIARY_OK=true
    echo "✅ 今日日记存在: $TODAY_DIARY"
else
    echo "❌ 今日日记缺失: $TODAY_DIARY"
fi

# 2. 检查活跃任务是否今日更新
if [ -f "$ACTIVE_TASKS" ]; then
    TASKS_MOD=$(stat -f "%Sm" -t "%Y-%m-%d" "$ACTIVE_TASKS" 2>/dev/null || stat -c "%y" "$ACTIVE_TASKS" 2>/dev/null | cut -d' ' -f1)
    if [ "$TASKS_MOD" = "$TODAY" ]; then
        TASKS_OK=true
        echo "✅ active_tasks 今日已更新"
    else
        echo "❌ active_tasks 最后更新: $TASKS_MOD (今天未更新)"
    fi
else
    echo "❌ active_tasks 文件不存在"
fi

# 3. 检查近期对话是否今日更新
if [ -f "$RECENT_CONVOS" ]; then
    CONVOS_MOD=$(stat -f "%Sm" -t "%Y-%m-%d" "$RECENT_CONVOS" 2>/dev/null || stat -c "%y" "$RECENT_CONVOS" 2>/dev/null | cut -d' ' -f1)
    if [ "$CONVOS_MOD" = "$TODAY" ]; then
        CONVOS_OK=true
        echo "✅ recent_conversations 今日已更新"
    else
        echo "❌ recent_conversations 最后更新: $CONVOS_MOD (今天未更新)"
    fi
else
    echo "❌ recent_conversations 文件不存在"
fi

# 4. 构建汇报消息
if $DIARY_OK && $TASKS_OK; then
    REPORT="已完成今日（$TODAY）的记忆系统更新 ✅"
else
    MISSING=""
    if ! $DIARY_OK; then MISSING="${MISSING}日记"; fi
    if ! $TASKS_OK; then MISSING="${MISSING:+${MISSING}、}活跃任务"; fi
    if ! $CONVOS_OK; then MISSING="${MISSING:+${MISSING}、}近期对话"; fi
    REPORT="今日（$TODAY）记忆系统更新不完整 ⚠️ 缺失: $MISSING。请 Kitty 和 Bryson 立即完成归档"
fi

echo "📤 发送群聊汇报: $REPORT"
$SEND_CMD --target "$GROUP_CHAT" --message "$REPORT" 2>&1
EXIT_CODE=$?
echo "发送结果: exit_code=$EXIT_CODE"
exit $EXIT_CODE
