#!/bin/bash
# OPC Workspace 每日自动备份脚本
# 每天 23:59 自动 commit + push 到 GitHub

WS=/Users/zhaoyuzhao/opc-workspace
LOG=/Users/zhaoyuzhao/opc-workspace/.git-auto-backup.log

cd "$WS" || exit 1

# 拉取远程更新
git pull --rebase origin main >> "$LOG" 2>&1

# 提交本地变更
git add -A
if git diff --cached --quiet; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] No changes to commit" >> "$LOG"
else
    git commit -m "📦 Auto backup: $(date '+%Y-%m-%d %H:%M')" >> "$LOG" 2>&1
    git push origin main >> "$LOG" 2>&1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Auto backup committed and pushed ✓" >> "$LOG"
fi
