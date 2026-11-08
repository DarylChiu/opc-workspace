#!/bin/bash
# net_diag_full.sh — 网络故障全链路诊断（DNS → IP → TCP → TLS → HTTP）
# 2026-11-08 建立。起因：排查 Mac mini 境外访问失败时，多次「只测一层就下结论」
#   导致连续 5 次错误口径（段封锁 → SNI 拦截 → 两类并存 → DNS 污染 → 完整链路）
#
# 核心教训（血泪）：
#   1. 绝对不要用 --connect-to / --resolve 直接测 TLS 就下结论 —— 那会跳过 DNS 层，
#      而 DNS 污染恰恰是最常见的病灶。必须逐层走完。
#   2. nc -z 只能验证 TCP 三次握手，对 TLS 层完全无感知。SNI 拦截/证书问题它看不见。
#      实测反例：nc 测百度 443 FAIL，但 curl 返回 200。
#   3. curl 的 %{time_connect} 和 %{time_appconnect} 是区分故障层的关键：
#        time_connect=0.000      → TCP 没建立（IP 不可达 / 黑洞）
#        time_connect>0, appconnect=0.000 → TCP 通、TLS 被掐（SNI/证书/中间设备）
#        appconnect>0             → TLS 建起来了，看 HTTP 码判断业务层
#   4. 必须用 whois 验证返回的 IP 归属 —— 污染 IP 的 whois 会和目标域名完全无关。
#      实测：www.google.com → Facebook IP，api.openai.com → 上海某公司 IP。
#
# 用法:
#   bash net_diag_full.sh                  # 诊断默认目标列表
#   bash net_diag_full.sh example.com ...  # 诊断指定域名
#   bash net_diag_full.sh --iface en1 x.com  # 绑定网卡（多线路对比）

set -uo pipefail
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

IFACE=""
DOMAINS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --iface) IFACE="$2"; shift 2 ;;
    -*) echo "unknown flag: $1"; exit 2 ;;
    *) DOMAINS+=("$1"); shift ;;
  esac
done
if [ ${#DOMAINS[@]} -eq 0 ]; then
  DOMAINS=(github.com www.google.com chatgpt.com api.openai.com www.baidu.com)
fi

CURLBASE=(--connect-timeout 3 --max-time 10 -s -o /dev/null -w "%{http_code}|%{time_connect}|%{time_appconnect}|%{size_download}")
if [ -n "$IFACE" ]; then
  CURLBASE+=(--interface "$IFACE")
  echo "=== 绑定网卡: $IFACE ($(ipconfig getifaddr "$IFACE" 2>/dev/null)) ==="
else
  echo "=== 默认路由 ==="
  route -n get default 2>/dev/null | grep -E "gateway|interface"
fi
echo

for d in "${DOMAINS[@]}"; do
  echo "════════════════════════════════════════════════════════"
  echo "  $d"
  echo "════════════════════════════════════════════════════════"

  # ---- L1: DNS ----
  ips=$(dig +short "$d" 2>/dev/null | grep -E '^[0-9]+\.' | head -3)
  if [ -z "$ips" ]; then
    echo "  [L1 DNS]  解析失败或无 A 记录"
    echo
    continue
  fi
  echo "  [L1 DNS]  系统 DNS 返回:"
  for ip in $ips; do
    owner=$(whois "$ip" 2>/dev/null | grep -iE "^(OrgName|netname|descr):" | head -1 | sed 's/^[^:]*: *//')
    printf "            %-18s 归属: %s\n" "$ip" "${owner:-未知}"
  done

  # ---- L2~L4: 逐 IP 走完整链路 ----
  echo "  [L2-L4]   逐 IP 完整链路:"
  for ip in $ips; do
    r=$(curl "${CURLBASE[@]}" --connect-to "$d:443:$ip:443" "https://$d/" 2>/dev/null)
    code="${r%%|*}"; rest="${r#*|}"; tc="${rest%%|*}"; rest2="${rest#*|}"; ac="${rest2%%|*}"; sz="${rest2##*|}"
    [ -z "$code" ] && code="---"

    if [ "$code" != "000" ] && [ "$code" != "---" ]; then
      layer="✅ HTTP层通 ($code, ${sz}B)"
    elif [ "$tc" = "0.000000" ] || [ "$tc" = "0.000" ]; then
      layer="❌ IP不可达 (TCP未建立)"
    elif [ "$ac" = "0.000000" ] || [ "$ac" = "0.000" ]; then
      layer="❌ TCP通/TLS被掐 (SNI或中间设备)"
    else
      layer="⚠️ TLS通但HTTP层无响应"
    fi
    printf "            %-18s connect=%-10s appconnect=%-10s %s\n" "$ip" "$tc" "$ac" "$layer"
  done

  # ---- L5: 默认路径（走系统 DNS + 系统路由，最真实）----
  r=$(curl "${CURLBASE[@]}" "https://$d/" 2>/dev/null)
  code="${r%%|*}"; rest="${r#*|}"; tc="${rest%%|*}"; rest2="${rest#*|}"; ac="${rest2%%|*}"; sz="${rest2##*|}"
  remote=$(curl -s -o /dev/null -w "%{remote_ip}" --connect-timeout 3 --max-time 8 "${CURLBASE[@]:0:2}" "https://$d/" 2>/dev/null || echo "?")
  [ -z "$code" ] && code="---"
  echo "  [L5 默认] 实际访问: code=$code connect=$tc appconnect=$ac size=${sz}B"

  echo
done

echo "════════════════════════════════════════════════════════"
echo "  判定规则"
echo "════════════════════════════════════════════════════════"
echo "  DNS 归属与目标域名无关     → DNS 污染/劫持（最常见，先查这层）"
echo "  IP 可达 + TLS 通 + HTTP 通 → 正常，无需处理"
echo "  IP 可达但 TLS 被掐         → SNI 拦截 / 证书问题 / 中间设备"
echo "  IP 不可达 (connect=0.000)  → 该 IP 被黑洞，需换 IP"
echo "  换 SNI 能通 = 换域名可达   → 但要注意：伪装成不匹配的 SNI 反而可能失败"
