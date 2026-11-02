#!/bin/bash
# 启动 Mac 旁路由代理（路径 C）— 局域网设备可用 192.168.x.x:7893 上网
# 用法: bash scripts/net/start-lan-proxy.sh
set -e
DIR="$HOME/.openclaw/workspace/memory/network"
LOG=/tmp/mihomo_lan.log

# 已在跑就不重复起
if lsof -nP -iTCP:7893 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "✅ 7893 已在监听"
  HOSTIP=$(ipconfig getifaddr en0 2>/dev/null)
  echo "   手机/电视填: $HOSTIP:7893"
  exit 0
fi

cd "$DIR"
# 每次重新拉订阅（含自愈），并允许局域网
MIHOMO_LAN=1 MIHOMO_BIND='*' MIHOMO_PORT=7893 python3 build_mihomo_config.py --check || {
  echo "❌ 配置生成失败"; exit 1; }

nohup mihomo -d "$DIR" -f "$DIR/mihomo_prod.yaml" > "$LOG" 2>&1 &
sleep 12

if lsof -nP -iTCP:7893 -sTCP:LISTEN >/dev/null 2>&1; then
  HOSTIP=$(ipconfig getifaddr en0 2>/dev/null)
  echo "✅ 旁路由已启动"
  echo "   Mac 本机:  http://127.0.0.1:7893"
  echo "   手机/电视: http://$HOSTIP:7893  (HTTP 代理)"
else
  echo "❌ 启动失败，查看 $LOG"; tail -5 "$LOG"; exit 1
fi
