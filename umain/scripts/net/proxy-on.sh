#!/bin/bash
# 开启 macOS 系统代理 → 127.0.0.1:7890
set -e
PORT="${1:-7890}"
IF=$(route -n get default 2>/dev/null | awk '/interface:/{print $2}')
SVC=$(networksetup -listnetworkserviceorder | awk -v i="$IF" 'BEGIN{RS="\n\n"} $0 ~ "Device: "i"\\)" {match($0,/^\([0-9]+\) ([^\n]+)/,m); print m[1]; exit}')
[ -z "$SVC" ] && SVC="Wi-Fi"
echo "接口=$IF  服务=$SVC  端口=$PORT"
networksetup -setwebproxy "$SVC" 127.0.0.1 "$PORT"
networksetup -setsecurewebproxy "$SVC" 127.0.0.1 "$PORT"
networksetup -setwebproxystate "$SVC" on
networksetup -setsecurewebproxystate "$SVC" on
networksetup -setproxybypassdomains "$SVC" "*.local" "169.254/16" "127.0.0.1" "localhost" "*.cn"
echo "✅ 系统代理已开启 ($SVC → 127.0.0.1:$PORT)"
