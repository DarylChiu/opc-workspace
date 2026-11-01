#!/bin/bash
# 用法: ./import-sub.sh "<Clash订阅URL>"
# 作用: 拉取订阅 → 校验 → 替换 mihomo 配置 → 重启 → 系统代理开启
set -euo pipefail
URL="${1:?用法: import-sub.sh <clash订阅URL>}"
DIR=/opt/homebrew/etc/mihomo
TMP=$(mktemp /tmp/sub_XXXX.yaml)

echo "① 拉取订阅…"
curl -sSL --max-time 60 -A "clash-verge/v2.0 mihomo/1.19" "$URL" -o "$TMP"
SIZE=$(wc -c < "$TMP" | tr -d ' ')
echo "   已下载 $SIZE bytes"
head -3 "$TMP" | grep -qiE "proxies:|port:|mixed-port:|proxy-groups:" || { echo "❌ 不是 Clash 格式（可能是 base64 的 v2ray 订阅），把原始链接发我"; head -c 300 "$TMP"; exit 1; }
grep -q "^proxies:" "$TMP" || { echo "❌ 订阅里没有 proxies 段"; exit 1; }
N=$(awk '/^proxies:/{f=1;next} f&&/^[a-zA-Z]/{exit} f&&/^ *- /{c++} END{print c+0}' "$TMP")
echo "   节点数: $N"

echo "② 备份旧配置…"
[ -f "$DIR/config.yaml" ] && cp "$DIR/config.yaml" "$DIR/config.yaml.bak.$(date +%s)"

echo "③ 写入订阅…"
cp "$TMP" "$DIR/config.yaml"

echo "④ 语法校验…"
/opt/homebrew/opt/mihomo/bin/mihomo -d "$DIR" -t 2>&1 | tail -2

echo "⑤ 重启 mihomo…"
brew services restart mihomo >/dev/null 2>&1
sleep 4
nc -z 127.0.0.1 7890 && echo "   ✅ 7890 监听中" || { echo "   ❌ 未启动，看日志: brew services info mihomo"; exit 1; }

echo "⑥ 链路测试…"
bash "$(dirname "$0")/proxy-test.sh"

echo "⑦ 开启系统代理…"
bash "$(dirname "$0")/proxy-on.sh"
rm -f "$TMP"
echo "🎉 完成"
