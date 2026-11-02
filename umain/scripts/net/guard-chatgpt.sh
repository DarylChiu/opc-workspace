#!/bin/bash
# ChatGPT 代理守卫 — 检测到未经代理注入直接启动的 ChatGPT 就重拉
# 用法: 由 LaunchAgent 每 30s 调用
LOG=/tmp/chatgpt_guard.log
NP=$(pgrep -f "ChatGPT.app/Contents/MacOS" | head -1)
[ -z "$NP" ] && exit 0   # 没运行，不管

# 检查是否已注入代理
if ps eww -p "$NP" 2>/dev/null | tr ' ' '\n' | grep -q "^HTTPS_PROXY=http://127.0.0.1:7892"; then
  exit 0   # 正常，退出
fi

echo "[$(date '+%F %T')] ⚠️ 检测到 PID $NP 未经代理启动，重拉中" >> "$LOG"
# 用包装器重拉
open "/Applications/ChatGPT 代理.app"
