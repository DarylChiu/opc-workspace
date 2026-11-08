#!/bin/bash
# ============================================================
# agent_fail_probe.sh — 高频窄窗口故障探针
# ============================================================
# 背景：2026-11-08 实测发现代理故障窗口极窄（120 轮 @3s 只命中 1 次），
#       launchd 3min 探针 + 手动压测都难以稳定命中。
#       本脚本是唯一能高频命中的工具，必须入库（数字资产红线）。
#
# 用途：故障复盘 / 判据取数 / 验证 L1 参数是否有效
# 注意：不要常驻运行（会污染 proxy_alert.log 的独立观测），仅诊断时手动跑
#
# 用法：
#   bash agent_fail_probe.sh                    # 120 轮 @3s（约 6 分钟）
#   bash agent_fail_probe.sh 60 2               # 60 轮 @2s
#   bash agent_fail_probe.sh 120 3 chatgpt      # 指定目标
# ============================================================

ROUNDS="${1:-120}"
INTERVAL="${2:-3}"
TARGET="${3:-chatgpt}"
PROXY="127.0.0.1:7892"
OUT_DIR="$(dirname "$0")/../../memory/diagnostics"
mkdir -p "$OUT_DIR"
TS=$(date +%Y%m%d_%H%M%S)
OUT="$OUT_DIR/fail_probe_${TS}.log"

case "$TARGET" in
  chatgpt) URL="https://chatgpt.com" ;;
  ctrl)    URL="https://www.gstatic.com/generate_204" ;;
  *)       URL="$TARGET" ;;
esac

# L1 参数（与 proxy_alert.sh 保持一致）
CT=1.5
MT=3

echo "# agent_fail_probe  $(date '+%F %T')  rounds=$ROUNDS interval=${INTERVAL}s target=$URL" | tee -a "$OUT"
echo "# proxy=$PROXY connect-timeout=$CT max-time=$MT" | tee -a "$OUT"

T0=$(date +%s)
OK=0; FAIL=0; i=0
while [ $i -lt "$ROUNDS" ]; do
  i=$((i+1))
  r=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" \
      --connect-timeout "$CT" --max-time "$MT" \
      -x "$PROXY" "$URL" 2>/dev/null)
  c="${r%% *}"; t="${r##* }"
  if [ "$c" = "200" ] || [ "$c" = "204" ]; then
    OK=$((OK+1))
  else
    FAIL=$((FAIL+1))
    el=$(( $(date +%s) - T0 ))
    # 失败时补对照探针 + 出口 IP，供归因
    ctrl=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout "$CT" --max-time "$MT" \
           -x "$PROXY" https://www.gstatic.com/generate_204 2>/dev/null)
    eip=$(curl -s --connect-timeout "$CT" --max-time "$MT" -x "$PROXY" \
          https://api.ipify.org 2>/dev/null | head -c 40)
    [ -z "$eip" ] && eip="(取不到)"
    line="FAIL#$FAIL @$(date '+%F %T') code=$c t=${t}s elapsed=${el}s ctrl=$ctrl exit_ip=$eip"
    echo "$line" | tee -a "$OUT"
  fi
  sleep "$INTERVAL"
done

DUR=$(( $(date +%s) - T0 ))
SUMMARY="DONE: OK=$OK FAIL=$FAIL rounds=$ROUNDS duration=${DUR}s target=$URL"
echo "$SUMMARY" | tee -a "$OUT"
echo "$SUMMARY"
echo "# log: $OUT"
