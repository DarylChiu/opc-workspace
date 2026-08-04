#!/bin/bash
# ============================================================
# distill_weekly.sh — 周度蒸馏入口 (cron 调用)
# 每周日 22:00 运行: 0 22 * * 0
# ============================================================
set -euo pipefail

WORKSPACE="${WORKSPACE:-/Users/zhaoyuzhao/.openclaw/workspace}"
LOG="${WORKSPACE}/memory/evolution/distill_weekly.log"

echo "=== 周度蒸馏 $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG"
cd "$WORKSPACE"
python3 scripts/evolution/distill_patterns.py >> "$LOG" 2>&1
echo "完成: $(date '+%H:%M:%S')" >> "$LOG"
