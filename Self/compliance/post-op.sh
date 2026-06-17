#!/bin/bash
# L3: 操作后合规验证 — 任务完成后检查是否需要更新记忆系统
# 用法: bash scripts/compliance/post-op.sh "<任务描述>" "[涉及文件]"
#
# 输出需要执行的记忆更新动作清单

WORKSPACE="${OPENCLAW_WORKSPACE:-/Users/zhaoyuzhao/.openclaw/workspace-self}"
cd "$WORKSPACE" || exit 1

TASK_DESC="${1:-未指定任务}"
FILES="${2:-无}"
TIMESTAMP=$(date +"%Y-%m-%dT%H:%M:%S%z")
TODAY=$(date +%Y-%m-%d)

ACTIONS=()
WARNINGS=()
SCORE=0
TOTAL=5

echo "✅ L3 操作后合规验证"
echo "  任务: $TASK_DESC"
echo "  文件: $FILES"
echo ""

# 1. active.md 是否需要更新？
ACTIVE_LAST=$(stat -f "%m" "memory/active.md" 2>/dev/null || echo 0)
NOW=$(date +%s)
ACTIVE_AGE=$(( (NOW - ACTIVE_LAST) / 3600 ))

if echo "$TASK_DESC" | grep -qiE "(新任务|新项目|完成|交付|启动|启用|新增|开始)"; then
    if [ "$ACTIVE_AGE" -gt 4 ]; then
        WARNINGS+=("🔴 active.md 需更新 — 有新任务变更但 $ACTIVE_AGE 小时未动")
    else
        ACTIONS+=("✅ active.md 最近已更新，无需操作")
        SCORE=$((SCORE + 1))
    fi
elif echo "$TASK_DESC" | grep -qiE "(修复|bug|修改|更新|变更)"; then
    if [ "$ACTIVE_AGE" -gt 12 ]; then
        WARNINGS+=("🟡 考虑更新 active.md — 有任务修改且已 $ACTIVE_AGE 小时")
    else
        ACTIONS+=("✅ active.md 状态正常")
        SCORE=$((SCORE + 1))
    fi
else
    ACTIONS+=("ℹ️ 本次为查询/阅读类操作，active.md 无需更新")
    SCORE=$((SCORE + 1))
fi

# 2. 日记是否需要写入？
TODAY_FILE="memory/$TODAY.md"
if [ -f "$TODAY_FILE" ]; then
    TODAY_CONTENT=$(wc -l < "$TODAY_FILE" | tr -d ' ')
    if [ "$TODAY_CONTENT" -lt 3 ]; then
        WARNINGS+=("🟡 今日日记内容过短（${TODAY_CONTENT}行），建议补充")
    else
        ACTIONS+=("✅ 今日日记存在且内容充足")
        SCORE=$((SCORE + 1))
    fi
else
    WARNINGS+=("🔴 今日日记缺失 — 必须创建")
fi

if echo "$TASK_DESC" | grep -qiE "(完成|交付|验收|通过|修复成功|解决|上线)"; then
    ACTIONS+=("📝 建议写入今日日记: $TASK_DESC")
fi

# 3. lessons.md 是否需要提炼？
if echo "$TASK_DESC" | grep -qiE "(报错|失败|bug|踩坑|问题|教训|忘了|遗漏|错了|不对)"; then
    WARNINGS+=("🔴 任务涉及问题/失败，建议提炼到 lessons.md")
fi

# 4. 产出文件格式检查
if [ "$FILES" != "无" ]; then
    IFS=',' read -ra FILE_ARRAY <<< "$FILES"
    for f in "${FILE_ARRAY[@]}"; do
        if echo "$f" | grep -qE "\.(md|py|sh|js|html|css|json|yaml|yml)$"; then
            ACTIONS+=("✅ 产出类型: 文本/代码文件")
            SCORE=$((SCORE + 1))
            break
        fi
    done
fi

# 5. 跨 session 同步检查
if echo "$TASK_DESC" | grep -qiE "(跨.*session|DM|私聊|群聊|同步|互相同步)"; then
    ACTIONS+=("🌐 跨 session 工作 — 确认已同步到共享 memory")
    SCORE=$((SCORE + 1))
fi

# 输出检查结果
echo "--- 📊 合规评分: $SCORE/$TOTAL ---"
echo ""

if [ ${#WARNINGS[@]} -gt 0 ]; then
    echo "⚠️ 需要处理的事项:"
    for w in "${WARNINGS[@]}"; do
        echo "  $w"
    done
fi

if [ ${#ACTIONS[@]} -gt 0 ]; then
    echo ""
    echo "已完成/跳过项:"
    for a in "${ACTIONS[@]}"; do
        echo "  $a"
    done
fi

echo ""
echo "📊 合规评分: $SCORE/$TOTAL"

# 写入 audit 日志
mkdir -p "$WORKSPACE/memory"
AUDIT_LOG="$WORKSPACE/memory/compliance-audit.jsonl"
cat >> "$AUDIT_LOG" << EOF
{"timestamp":"$TIMESTAMP","check":"post-op","task":"$TASK_DESC","score":$SCORE,"total":$TOTAL,"warnings":$(printf '%s\n' "${WARNINGS[@]}" | jq -R . | jq -s .)}
EOF

# 返回码：满分 pass，否则 warn
if [ "$SCORE" -eq "$TOTAL" ]; then
    exit 0
else
    exit 1
fi
