#!/bin/bash
# L0: 启动验证 — 合规系统健康检查
# 用法: bash scripts/compliance/startup.sh
# 在每个 session 启动时运行，验证基建是否完整

WORKSPACE="${OPENCLAW_WORKSPACE:-/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace}"
cd "$WORKSPACE" || exit 1

STATUS_FILE="memory/compliance-status.json"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TODAY=$(date +%Y-%m-%d)
ISSUES=()
PASSES=()

echo "🔍 L0 合规启动验证 | $TIMESTAMP"
echo "================================"

# 1. 必读文件存在性检查
check_file() {
    local file="$1"
    local label="$2"
    if [ -f "$file" ] && [ -s "$file" ]; then
        PASSES+=("$label 存在且非空")
        echo "  ✅ $label"
        return 0
    else
        ISSUES+=("$label 缺失或为空")
        echo "  ❌ $label 缺失或为空"
        return 1
    fi
}

check_file "memory/identity.md" "identity.md"
check_file "memory/active.md" "active.md"
check_file "memory/workflow-rules.md" "workflow-rules.md"
check_file "AGENTS.md" "AGENTS.md"

# 2. 今日日记存在性
TODAY_FILE="memory/$TODAY.md"
if [ -f "$TODAY_FILE" ]; then
    PASSES+=("今日日记 $TODAY.md 存在")
    echo "  ✅ 今日日记存在"
else
    ISSUES+=("今日日记 $TODAY.md 缺失 — 需要从 session 历史补充")
    echo "  ⚠️ 今日日记缺失"
fi

# 3. active.md 新鲜度检查
if [ -f "memory/active.md" ]; then
    LAST_MODIFIED=$(stat -f "%m" "memory/active.md" 2>/dev/null || stat -c "%Y" "memory/active.md" 2>/dev/null)
    NOW=$(date +%s)
    AGE_HOURS=$(( (NOW - LAST_MODIFIED) / 3600 ))
    if [ "$AGE_HOURS" -gt 48 ]; then
        ISSUES+=("active.md 超过48小时未更新（${AGE_HOURS}h）")
        echo "  ⚠️ active.md 老旧 — 最后更新 ${AGE_HOURS} 小时前"
    else
        PASSES+=("active.md 新鲜度正常（${AGE_HOURS}h）")
        echo "  ✅ active.md 新鲜度正常"
    fi
fi

# 4. 目录结构完整性
for dir in memory scripts/compliance; do
    if [ -d "$dir" ]; then
        echo "  ✅ 目录 $dir 存在"
    else
        ISSUES+=("目录 $dir 缺失")
        echo "  ❌ 目录 $dir 缺失"
    fi
done

# 5. 合规脚本自身完整性
for script in startup.sh pre-op.sh post-op.sh audit.sh; do
    if [ -x "scripts/compliance/$script" ]; then
        echo "  ✅ $script 就绪"
    else
        ISSUES+=("合规脚本 $script 不可执行")
        echo "  ❌ $script 不可执行"
    fi
done

# 总结
PASS_COUNT=${#PASSES[@]}
ISSUE_COUNT=${#ISSUES[@]}
HEALTH="OK"
if [ "$ISSUE_COUNT" -gt 0 ]; then
    HEALTH="DEGRADED"
fi
if [ "$ISSUE_COUNT" -gt 3 ]; then
    HEALTH="CRITICAL"
fi

echo ""
echo "================================"
echo "📊 结果: $HEALTH | 通过: $PASS_COUNT | 问题: $ISSUE_COUNT"

# 写入状态文件
cat > "$STATUS_FILE" << EOF
{
  "timestamp": "$TIMESTAMP",
  "health": "$HEALTH",
  "passes": $PASS_COUNT,
  "issues": $ISSUE_COUNT,
  "issue_list": $(printf '%s\n' "${ISSUES[@]}" | jq -R . | jq -s .),
  "pass_list": $(printf '%s\n' "${PASSES[@]}" | jq -R . | jq -s .)
}
EOF

echo "📝 状态已写入 $STATUS_FILE"

# 返回码
if [ "$ISSUE_COUNT" -eq 0 ]; then
    exit 0
elif [ "$ISSUE_COUNT" -le 3 ]; then
    exit 1
else
    exit 2
fi
