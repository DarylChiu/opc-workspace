#!/bin/bash
# ChatGPT / Codex 桌面版启动器 — 强制走微风网络代理 (127.0.0.1:7892)
# 用法: bash scripts/net/launch-chatgpt.sh
# 版本: v3 (2026-11-04) — 端口探测从 lsof LISTEN 改为流量实测（微风非标准 listen，lsof 永远查不到）
set -e

PROXY="http://127.0.0.1:7892"

# 1. 代理可用性：直接打流量，不看端口监听状态
#    （微风网络用私有协议，lsof -iTCP:7892 -sTCP:LISTEN 探测不到，会误判为未启动）
IPINFO=$(curl -sS --max-time 10 -x "$PROXY" "http://ip-api.com/json/?fields=countryCode,country,city,query" 2>/dev/null || true)
if [ -z "$IPINFO" ] || ! echo "$IPINFO" | grep -q countryCode; then
  echo "❌ 代理 $PROXY 不可用（无出口响应），请检查微风网络是否已连接"
  echo "   open -a ~/Applications/微风网络.app"
  exit 1
fi

COUNTRY=$(echo "$IPINFO" | sed -E 's/.*"countryCode":"([A-Z]+)".*/\1/')
COUNTRY_NAME=$(echo "$IPINFO" | sed -E 's/.*"country":"([^"]+)".*/\1/')
CITY=$(echo "$IPINFO" | sed -E 's/.*"city":"([^"]+)".*/\1/')
EXIT_IP=$(echo "$IPINFO" | sed -E 's/.*"query":"([^"]+)".*/\1/')

# 2. HK 节点被 OpenAI 403 封锁
if [ "$COUNTRY" = "HK" ]; then
  echo "⚠️  当前节点是香港 (HK)，OpenAI 会 403。请切到新加坡/日本/美国节点"
  exit 1
fi
echo "✅ 出口: ${COUNTRY_NAME:-unknown} / ${CITY:-?} / ${EXIT_IP:-?} (${COUNTRY:-unknown})"

# 3. 探测 chatgpt.com 是否 403（仅提示，不阻断——桌面版应用内登录可能仍可用）
CG=$(curl -s -o /dev/null -w "%{http_code}" --max-time 12 -x "$PROXY" https://chatgpt.com 2>/dev/null || echo 000)
if [ "$CG" = "403" ]; then
  echo "⚠️  chatgpt.com 返回 403（该节点 IP 被 Cloudflare 风控），桌面版可试，若登录失败请换节点"
else
  echo "✅ chatgpt.com 探测: HTTP $CG"
fi

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
