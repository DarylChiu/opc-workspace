#!/bin/bash
# stability_monitor.sh — 微风连接稳定性监控（24h 观察用）
# 2026-11-06 建立。Daryl 要求：观察微风一天的连接稳定性
#
# 与 alive_check.sh 的分工：
#   alive_check.sh   = 守夜人，出问题才告警（每5分钟，静默成功）
#   stability_monitor.sh = 监测仪，每 2 分钟采样一次，记录全部数据，不告警
#
# 设计：
#   - 纯数据采集，不发任何消息（避免打扰）
#   - 每 2 分钟一轮，一轮采 3 个样本（间隔 1s），共 720 轮/天，2160 样本
#   - 同时记录：出口连通性、延迟、当前节点、系统代理状态、网关状态
#   - 输出：memory/network/stability/YYYY-MM-DD.jsonl （每行一个样本）
#
# 用法：
#   stability_monitor.sh           # 单轮采样（launchd 每2分钟调用）
#   stability_monitor.sh --report  # 生成今日报告
#   stability_monitor.sh --test    # 采样但打印结果

set -uo pipefail
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
export LC_ALL=en_US.UTF-8

WS="/Users/zhaoyuzhao/.openclaw/workspace"
OUT_DIR="$WS/memory/network/stability"
TODAY=$(date +%Y-%m-%d)
OUT_FILE="$OUT_DIR/${TODAY}.jsonl"
LOG_FILE="$OUT_DIR/monitor.log"

PROXY="http://127.0.0.1:7892"
API="http://127.0.0.1:9090"
PROBE_URL="https://chatgpt.com"       # 只能走代理的境外目标
PROBE_URL_CN="https://www.baidu.com"  # 国内直连目标（对照组）
SAMPLES_PER_ROUND=3
SAMPLE_INTERVAL=1

MODE="${1:-run}"
mkdir -p "$OUT_DIR"
touch "$LOG_FILE"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }

# ---------- 采集单轮 ----------
collect_round() {
  local ts round_id
  local http_ok=0 http_fail=0
  local lat_sum=0 lat_n=0
  local cn_ok=0
  local proxy_port_up=0 sys_proxy=0 gw_up=0
  local node_name="" node_delay=""
  local fail_reasons=""

  ts=$(date +%s)
  round_id=$(date '+%Y%m%d%H%M%S')

  # 端口
  nc -z -G 2 127.0.0.1 7892 >/dev/null 2>&1 && proxy_port_up=1

  # 系统代理
  local he
  he=$(scutil --proxy 2>/dev/null | awk '/HTTPEnable/{print $3}')
  [ "${he:-0}" = "1" ] && sys_proxy=1

  # 网关
  ps -ax -o command= 2>/dev/null | grep -F "index.js gateway" | grep -qv grep && gw_up=1

  # 当前节点（9090 API）
  node_name=$(curl -s --max-time 4 --noproxy '*' "$API/proxies/微风网络" 2>/dev/null \
    | python3 -c "import sys,json;print(json.load(sys.stdin).get('now',''))" 2>/dev/null)

  # 代理出口采样
  local i code t
  for i in $(seq 1 $SAMPLES_PER_ROUND); do
    local out
    out=$(curl -s -o /dev/null -w '%{http_code} %{time_total}' --max-time 10 \
          -x "$PROXY" "$PROBE_URL" 2>/dev/null)
    code=$(echo "$out" | awk '{print $1}')
    t=$(echo "$out" | awk '{print $2}')
    if [ "$code" = "200" ]; then
      http_ok=$((http_ok+1))
      lat_sum=$(python3 -c "print($lat_sum + ${t:-0})" 2>/dev/null || echo "$lat_sum")
      lat_n=$((lat_n+1))
    else
      http_fail=$((http_fail+1))
      fail_reasons="$fail_reasons ${code:-timeout}"
    fi
    [ "$i" -lt "$SAMPLES_PER_ROUND" ] && sleep $SAMPLE_INTERVAL
  done

  # 国内直连对照组（判断是代理问题还是整体断网）
  local cncode
  cncode=$(curl -s -o /dev/null -w '%{http_code}' --max-time 6 --noproxy '*' "$PROBE_URL_CN" 2>/dev/null)
  [ "$cncode" = "200" ] && cn_ok=1

  # 平均延迟
  local lat_avg=0
  [ "$lat_n" -gt 0 ] && lat_avg=$(python3 -c "print(round($lat_sum/$lat_n, 3))" 2>/dev/null || echo 0)

  # 写 JSONL
  python3 - "$OUT_FILE" <<PY
import json, sys
rec = {
    "ts": $ts,
    "round": "$round_id",
    "proxy_port_up": $proxy_port_up,
    "sys_proxy": $sys_proxy,
    "gateway_up": $gw_up,
    "node": """$node_name""",
    "ok": $http_ok,
    "fail": $http_fail,
    "total": $SAMPLES_PER_ROUND,
    "lat_avg": $lat_avg,
    "fail_codes": """$fail_reasons""".strip(),
    "cn_direct_ok": $cn_ok,
}
with open(sys.argv[1], "a") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
PY

  [ "$MODE" = "--test" ] && echo "节点=${node_name:-?} 成功=${http_ok}/${SAMPLES_PER_ROUND} 平均延迟=${lat_avg}s 国内直连=$([ $cn_ok -eq 1 ] && echo OK || echo FAIL) 端口=$proxy_port_up 系统代理=$sys_proxy ${fail_reasons:+(失败码:$fail_reasons)}"
  return 0
}

# ---------- 报告 ----------
report() {
  local f="$OUT_FILE"
  [ -f "$f" ] || { echo "今日无数据"; return 1; }
  python3 - "$f" <<'PY'
import json, sys, datetime
from collections import Counter

rows = []
for line in open(sys.argv[1]):
    line = line.strip()
    if not line: continue
    try: rows.append(json.loads(line))
    except Exception: pass

if not rows:
    print("今日无有效数据"); raise SystemExit

total_samples = sum(r["total"] for r in rows)
total_ok = sum(r["ok"] for r in rows)
total_fail = sum(r["fail"] for r in rows)
rate = total_ok / total_samples * 100 if total_samples else 0

rounds_with_fail = [r for r in rows if r["fail"] > 0]
full_fail = [r for r in rows if r["ok"] == 0]
partial = [r for r in rows if 0 < r["ok"] < r["total"]]

lats = [r["lat_avg"] for r in rows if r["lat_avg"] > 0]
lat_avg = sum(lats)/len(lats) if lats else 0
lat_max = max(lats) if lats else 0
lat_min = min(lats) if lats else 0

first = datetime.datetime.fromtimestamp(rows[0]["ts"]).strftime("%H:%M")
last = datetime.datetime.fromtimestamp(rows[-1]["ts"]).strftime("%H:%M")
span_h = (rows[-1]["ts"] - rows[0]["ts"]) / 3600

print(f"# 微风稳定性报告 · {datetime.date.today()}")
print(f"采样时段: {first} → {last}（{span_h:.1f} 小时）")
print()
print(f"## 总体可用率")
print(f"- 采样轮次: {len(rows)} 轮 / {total_samples} 个样本")
print(f"- 成功: {total_ok}  失败: {total_fail}")
print(f"- **可用率: {rate:.2f}%**")
print()
print(f"## 延迟（成功请求）")
print(f"- 平均: {lat_avg:.2f}s")
print(f"- 最快: {lat_min:.2f}s  最慢: {lat_max:.2f}s")
print()
print(f"## 故障分布")
print(f"- 完全不可用轮次（3/3 全失败）: {len(full_fail)} 轮")
print(f"- 部分失败轮次（抖动）: {len(partial)} 轮")
print(f"- 受影响总轮次: {len(rounds_with_fail)} 轮 ({len(rounds_with_fail)/len(rows)*100:.1f}%)")

# 失败码统计
codes = Counter()
for r in rows:
    if r.get("fail_codes"):
        for c in r["fail_codes"].split():
            codes[c] += 1
if codes:
    print(f"- 失败码分布: {dict(codes)}")

# 系统代理与代理状态错配统计
mismatch = [r for r in rows if r["sys_proxy"] == 1 and r["proxy_port_up"] == 0]
if mismatch:
    print(f"- ⚠️ 系统代理开着但代理端口不通: {len(mismatch)} 轮")

# 国内直连失败（说明整体断网）
cn_fail = [r for r in rows if r["cn_direct_ok"] == 0]
if cn_fail:
    print(f"- ⚠️ 国内直连也失败（整体断网）: {len(cn_fail)} 轮")

# 节点分布
nodes = Counter(r["node"] for r in rows if r.get("node"))
if nodes:
    print()
    print("## 使用过的节点")
    for n, c in nodes.most_common(5):
        print(f"- {n}: {c} 轮")

# 故障时段
if full_fail:
    print()
    print("## 完全不可用时段")
    runs = []
    cur = [full_fail[0]]
    for prev, r in zip(full_fail, full_fail[1:]):
        if r["ts"] - prev["ts"] <= 300:
            cur.append(r)
        else:
            runs.append(cur); cur = [r]
    runs.append(cur)
    for run in runs:
        s = datetime.datetime.fromtimestamp(run[0]["ts"]).strftime("%H:%M")
        e = datetime.datetime.fromtimestamp(run[-1]["ts"]).strftime("%H:%M")
        dur = (run[-1]["ts"] - run[0]["ts"]) / 60
        print(f"- {s} → {e}（约 {dur:.0f} 分钟，{len(run)} 轮）")
PY
}

# ---------- 主流程 ----------
case "$MODE" in
  --report) report ;;
  --test)   collect_round ;;
  *)        collect_round; log "round done" ;;
esac
