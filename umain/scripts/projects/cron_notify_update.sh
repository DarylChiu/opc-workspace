#!/bin/bash
# ============================================================
# 记忆系统 v3 · Cron: 定时通知所有 Agent 更新 project_[AgentID].md
# 触发时间: 07:00 / 13:00 / 19:00 daily
# 流程: 通知各Agent更新 → Agent自行更新 → Dashboard扫描时读到最新数据
# ============================================================

set -euo pipefail

LOG_DIR="/tmp/openclaw_project_cron"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cron_$(date +%Y%m%d).log"
PROJECT_DIR="$HOME/.openclaw/workspace/memory"
AGENTS=("main" "xiaofeng" "Balance" "Self")

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] $1" | tee -a "$LOG_FILE"
}

log "========== Cron 触发: project 文件更新通知 =========="

for agent in "${AGENTS[@]}"; do
  FILE="$PROJECT_DIR/project_${agent}.md"
  
  if [ -f "$FILE" ]; then
    AGE=$(($(date +%s) - $(stat -f %m "$FILE" 2>/dev/null || echo 0)))
    AGE_HOURS=$((AGE / 3600))
    
    if [ $AGE_HOURS -gt 12 ]; then
      log "⚠️  $agent: project_${agent}.md 已过期 ${AGE_HOURS}h，需要更新"
    else
      log "✅ $agent: project_${agent}.md 新鲜 (${AGE_HOURS}h)"
    fi
  else
    log "❌ $agent: project_${agent}.md 不存在！"
  fi
done

log "========== 通知完成 =========="
