#!/bin/bash
# ChatGPT / Codex 桌面版启动器 — 强制走微风网络代理 (127.0.0.1:7892)
# 用法: bash scripts/net/launch-chatgpt.sh
# 版本: v2 (2026-11-01) — 加 NO_PROXY 排除本地回环，修复 Codex rendezvous connection_refused
set -e

PROXY="http://127.0.0.1:7892"

# 1. 检查代理端口
if ! lsof -nP -iTCP:7892 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "❌ 代理端口 7892 未监听，请先启动微风网络客户端并连接"
  echo "   open -a ~/Applications/微风网络.app"
  exit 1
fi

# 2. 检查出口地区（HK 被 OpenAI 403 封锁）
COUNTRY=$(curl -sS --max-time 8 -x "$PROXY" "http://ip-api.com/json/?fields=countryCode" 2>/dev/null | sed -E 's/.*"countryCode":"([A-Z]+)".*/\1/')
if [ "$COUNTRY" = "HK" ]; then
  echo "⚠️  当前节点是香港 (HK)，OpenAI 会 403。请切到新加坡/日本/美国节点"
  exit 1
fi
echo "✅ 出口地区: ${COUNTRY:-unknown}"

# 3. 重启 ChatGPT
pkill -f "ChatGPT.app/Contents/MacOS" 2>/dev/null || true
sleep 3

# 4. 关键：NO_PROXY 排除本地回环，否则 Codex 的本地 websocket 会 connection_refused
NO_PROXY_LIST="127.0.0.1,localhost,::1,0.0.0.0,*.local"

nohup env \
  HTTP_PROXY="$PROXY" HTTPS_PROXY="$PROXY" ALL_PROXY="$PROXY" \
  http_proxy="$PROXY" https_proxy="$PROXY" all_proxy="$PROXY" \
  NO_PROXY="$NO_PROXY_LIST" no_proxy="$NO_PROXY_LIST" \
  /Applications/ChatGPT.app/Contents/MacOS/ChatGPT \
  --proxy-server="$PROXY" \
  --proxy-bypass-list="127.0.0.1;localhost;<local>" \
  > /tmp/chatgpt_run.log 2>&1 &

echo "✅ ChatGPT 已启动 (pid=$!)，代理: $PROXY → ${COUNTRY:-unknown}"
