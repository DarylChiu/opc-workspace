#!/bin/bash
# freshness_check.sh — 检查4个project文件是否超过24小时未更新
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

PROJECT_FILES=(
  "Kitty:/Users/zhaoyuzhao/.openclaw/workspace/memory/project_main.md"
  "Xiaofeng:/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/memory/project_xiaofeng.md"
  "Balance:/Users/zhaoyuzhao/.openclaw/workspace-balance/memory/project_Balance.md"
  "Self:/Users/zhaoyuzhao/.openclaw/workspace-self/memory/project_Self.md"
)

NOW=$(date +%s)
ALERTS=()

for entry in "${PROJECT_FILES[@]}"; do
  agent="${entry%%:*}"
  filepath="${entry#*:}"

  if [[ ! -f "$filepath" ]]; then
    ALERTS+=("  ⚠️ ${agent} project文件不存在: $filepath")
    continue
  fi

  # macOS stat format
  if [[ "$(uname)" == "Darwin" ]]; then
    mtime=$(stat -f %m "$filepath" 2>/dev/null || echo 0)
  else
    mtime=$(stat -c %Y "$filepath" 2>/dev/null || echo 0)
  fi

  if [[ "$mtime" -eq 0 ]]; then
    ALERTS+=("  ⚠️ ${agent} 无法获取文件修改时间")
    continue
  fi

  age_seconds=$((NOW - mtime))
  age_hours=$((age_seconds / 3600))

  if [[ $age_hours -gt 48 ]]; then
    ALERTS+=("  🔴 ${agent} project文件 ${age_hours}h未更新")
  elif [[ $age_hours -gt 24 ]]; then
    ALERTS+=("  ⚠️ ${agent} project文件 ${age_hours}h未更新")
  fi
done

if [[ ${#ALERTS[@]} -gt 0 ]]; then
  echo "📁 文件新鲜度"
  for alert in "${ALERTS[@]}"; do
    echo "$alert"
  done
fi
# 全部新鲜时不输出
