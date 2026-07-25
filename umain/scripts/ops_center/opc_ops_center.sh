#!/bin/bash
# opc_ops_center.sh — OPC运营中心主集成脚本
# 串联阻塞扫描、成本预警、文件新鲜度、搜索质量监控
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

SCRIPTS="/Users/zhaoyuzhao/.openclaw/workspace/scripts/ops_center"
DATE=$(date +%Y-%m-%d)

# 运行各模块
BLOCK=$("$SCRIPTS/block_scanner.py" 2>&1 || true)
COST=$("$SCRIPTS/cost_alert.py" 2>&1 || true)
FRESH=$(bash "$SCRIPTS/freshness_check.sh" 2>&1 || true)
SEARCH=$("$SCRIPTS/search_quality_monitor.py" 2>&1 || true)

# 构建消息体
PARTS=()
[ -n "$BLOCK" ] && PARTS+=("$BLOCK")
[ -n "$COST" ] && PARTS+=("$COST")
[ -n "$FRESH" ] && PARTS+=("$FRESH")
[ -n "$SEARCH" ] && PARTS+=("$SEARCH")

if [ ${#PARTS[@]} -eq 0 ]; then
  BODY="✅ 全部正常，无异常项"
else
  # Join parts with double newline
  BODY=""
  for part in "${PARTS[@]}"; do
    if [ -n "$BODY" ]; then
      BODY="$BODY"$'\n\n'"$part"
    else
      BODY="$part"
    fi
  done
  # Remove leading/trailing blank lines
  BODY=$(echo "$BODY" | sed '/^$/N;/^\n$/D')
fi

MESSAGE="📊 OPC运营日报 | $DATE

$BODY"

# 发送到OPC群
/opt/homebrew/bin/openclaw message send \
  --channel feishu \
  --account default \
  --target "chat:oc_7d71d54d87cbd265d9c3811bc59840b2" \
  --message "$MESSAGE"
