#!/bin/bash
# net_boundary_test.sh — 网络出口边界定位测试（只读，不改任何系统设置）
# 2026-11-08 建立。起因：Mac mini 国际出口疑似被限，需区分「线路问题」vs「运营商级限制」
#
# 设计要点：
#   1. 只用 curl，不用 nc —— nc -z 在本机会假 FAIL（实测：nc 测百度 443 FAIL，curl 200）
#   2. 必须看 %{time_connect}：
#        connect=0.000 + 000  → TCP 未建立（SYN 黑洞）
#        connect>0     + 000  → TCP 建立但 TLS 被拒（RST/策略拦截）
#        2xx/3xx              → 通
#   3. 支持 --interface 绑定，测热点时不影响主网络
#   4. gstatic 不能当境外证据（实测 120.232.234.34 是国内移动 CDN）
#
# 用法:
#   bash net_boundary_test.sh                  # 走默认路由
#   bash net_boundary_test.sh en0              # 强制走 en0（热点）
#   bash net_boundary_test.sh --list           # 列出所有接口及其 IP

set -uo pipefail
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

IFACE=""
LIST=0
for a in "$@"; do
  case "$a" in
    --list) LIST=1 ;;
    -*) echo "unknown flag: $a"; exit 2 ;;
    *) IFACE="$a" ;;
  esac
done

if [ "$LIST" -eq 1 ]; then
  echo "=== 网络接口 ==="
  for i in $(ifconfig -l); do
    ip=$(ipconfig getifaddr "$i" 2>/dev/null)
    [ -n "$ip" ] && printf "%-6s %s\n" "$i" "$ip"
  done
  echo
  echo "=== 默认路由 ==="
  route -n get default 2>/dev/null | grep -E "gateway|interface"
  exit 0
fi

CURL_OPTS=(--connect-timeout 3 --max-time 6 -s -o /dev/null -w "%{http_code}|%{time_connect}|%{time_total}")
if [ -n "$IFACE" ]; then
  CURL_OPTS+=(--interface "$IFACE")
  echo "=== 绑定接口: $IFACE ($(ipconfig getifaddr "$IFACE" 2>/dev/null)) ==="
else
  echo "=== 默认路由 ==="
  route -n get default 2>/dev/null | grep -E "gateway|interface"
fi
echo

# 目标分组：段类型 | 目标 | 说明
# 注意：gstatic 只作为「国内 CDN 对照」，不作为境外证据
targets=(
  "国内基准|https://www.baidu.com|应通"
  "国内CDN|https://www.gstatic.com/generate_204|204但走国内CDN,非境外证据"
  "RST段|https://104.16.132.229|Cloudflare,期望TCP通TLS拒"
  "RST段|https://47.242.89.235|HK Aliyun,期望TCP通TLS拒"
  "黑洞段|https://github.com|期望connect=0"
  "黑洞段|https://www.google.com|期望connect=0"
  "黑洞段|https://chatgpt.com|期望connect=0"
  "公共DNS|https://1.1.1.1|期望FAIL"
)

printf "%-10s %-42s %-10s %-10s %s\n" "段类型" "目标" "code" "connect" "判定"
printf "%-10s %-42s %-10s %-10s %s\n" "------" "----" "----" "-------" "----"

for t in "${targets[@]}"; do
  IFS='|' read -r kind url note <<< "$t"
  r=$(curl "${CURL_OPTS[@]}" "$url" 2>/dev/null)
  code="${r%%|*}"; rest="${r#*|}"; tc="${rest%%|*}"; tt="${rest##*|}"
  [ -z "$code" ] && code="---"
  [ -z "$tc" ] && tc="---"

  if [ "$code" != "000" ] && [ "$code" != "---" ]; then
    verdict="通"
  elif [ "$tc" = "0.000000" ] || [ "$tc" = "0.000" ]; then
    verdict="TCP黑洞"
  else
    verdict="TLS被拒(TCP通)"
  fi
  printf "%-10s %-42s %-10s %-10s %s\n" "$kind" "${url:0:42}" "$code" "$tc" "$verdict"
done

echo
echo "=== 结论指引 ==="
echo "RST段变'通' + 黑洞段仍'TCP黑洞' → 出口对特定段策略，非整体封锁"
echo "RST段和黑洞段都变'通'       → 原线路问题，换网络有效"
echo "RST段和黑洞段仍全失败        → 运营商级国际出口限制，换同运营商热点无用"

# ---------------------------------------------------------------
# SNI 对照实验（2026-11-08 新增，最关键的判断手段）
# 原理：对同一个可达 IP，只改 SNI，看 TLS 握手（%{time_appconnect}）能否建立
#   appconnect 有值 + 有 HTTP 码  → 该 SNI 未被拦
#   appconnect = 0.000 + 000      → 该 SNI 被中间设备打断
# 意义：区分「IP 段封锁」（换 IP 才有救）vs「SNI 拦截」（换 SNI/伪装即可救）
# ---------------------------------------------------------------
echo
SNI_TEST_IP="${SNI_TEST_IP:-104.16.132.229}"
echo "=== SNI 对照实验（同一 IP $SNI_TEST_IP，只改 SNI）==="
echo "测试 IP: $SNI_TEST_IP (Cloudflare)"
printf "%-22s %-6s %-12s %-14s %s\n" "SNI" "code" "connect" "appconnect(TLS)" "判定"
printf "%-22s %-6s %-12s %-14s %s\n" "---" "----" "-------" "---------------" "----"

for sni in cloudflare.com www.baidu.com github.com chatgpt.com; do
  r=$(curl -s -o /dev/null -w "%{http_code}|%{time_connect}|%{time_appconnect}" \
        --connect-timeout 3 --max-time 6 \
        --resolve "$sni:443:$SNI_TEST_IP" "https://$sni/" 2>/dev/null)
  code="${r%%|*}"; rest="${r#*|}"; tc="${rest%%|*}"; ac="${rest##*|}"
  [ -z "$code" ] && code="---"
  [ -z "$ac" ] && ac="---"

  if [ "$code" != "000" ] && [ "$code" != "---" ]; then
    verdict="未被拦"
  elif [ "$ac" = "0.000000" ] || [ "$ac" = "0.000" ] || [ "$ac" = "---" ]; then
    verdict="TLS被掐(SNI拦截)"
  else
    verdict="TLS通但HTTP层拒"
  fi
  printf "%-22s %-6s %-12s %-14s %s\n" "$sni" "$code" "$tc" "$ac" "$verdict"
done

echo
echo "=== SNI 实验结论指引 ==="
echo "部分 SNI 的 appconnect 有值 (=TLS 建起来了) → SNI 拦截，换 SNI/伪装域名/Reality 即可救，IP 段没被封"
echo "所有 SNI 的 appconnect 都是 0.000        → 真 IP 段封锁，只能换 IP/换中转"
echo "可用 SNI_TEST_IP=<其他IP> bash $0 换测试目标"
