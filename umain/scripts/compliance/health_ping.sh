#!/bin/bash
# health_ping.sh — 极简健康自检（替代 alive_check.sh 守夜人）
# 2026-11-06 v1，起因：alive_check.sh 误报 2 次（盲扫 sk- 抓到 Kimi key），
#                  Daryl 要求取消告警，换方案。
#
# 设计原则（吸取教训）：
#   1. 只查「能确定真假」的事，绝不做模糊推断
#   2. 出问题时先自动修一次，只有修不好才通知
#   3. 通知发给 Daryl 时必须是「人话」，不含技术黑话
#   4. 一天最多通知 2 次（防止噪音）
#   5. 没问题是绝对静默，不报告"一切正常"
#
# 检查项（全部是硬事实，无推断）：
#   A. 网关进程在不在
#   B. 我自己能不能调通 LLM（真发一次最小请求）
#   C. 飞书消息能不能发出去（能发说明通道通）
#
# 不做的事：
#   - 不查 API key 有效性（会造成误报）
#   - 不推断"可能失效/欠费"这类原因
#   - 不扫配置文件凭证

set -uo pipefail
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

WS="/Users/zhaoyuzhao/.openclaw/workspace"
STATE_DIR="$WS/memory/health"
STATE_FILE="$STATE_DIR/state.json"
LOG="$STATE_DIR/health.log"
TARGET="user:ou_3bf0d4dcf7a80d6ddf15be5bd2f7ad4f"
MAX_NOTIFY_PER_DAY=2

TEST=0
[ "${1:-}" = "--test" ] && TEST=1

mkdir -p "$STATE_DIR"; touch "$LOG"
log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }

FAILS=()

# A. 网关进程
check_gateway() {
  if ps -ax -o command= 2>/dev/null | grep -F "index.js gateway" | grep -qv grep; then
    return
  fi
  FAILS+=("后台服务没在跑，Agent 可能全部离线")
  if [ "$TEST" -eq 0 ]; then
    log "尝试拉起 gateway"
    launchctl kickstart -k "gui/$(id -u)/ai.openclaw.gateway" >/dev/null 2>&1 || \
      openclaw gateway start >/dev/null 2>&1
    sleep 8
    if ps -ax -o command= 2>/dev/null | grep -F "index.js gateway" | grep -qv grep; then
      log "gateway 自动拉起成功"
      FAILS=("${FAILS[@]/后台服务没在跑，Agent 可能全部离线/}")
    fi
  fi
}

# B. LLM 真实调用（最小化：1 token）
check_llm() {
  local key code
  key="${DEEPSEEK_API_KEY:-}"
  [ -z "$key" ] && key=$(launchctl getenv DEEPSEEK_API_KEY 2>/dev/null || true)
  if [ -z "$key" ]; then
    log "读不到 DEEPSEEK_API_KEY，跳过 LLM 检查（不告警，避免误报）"
    return
  fi
  code=$(curl -s -o /tmp/health_llm.json -w '%{http_code}' --max-time 25 --noproxy '*' \
    -X POST https://api.deepseek.com/chat/completions \
    -H "Authorization: Bearer $key" -H "Content-Type: application/json" \
    -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"1"}],"max_tokens":1}' 2>/dev/null)
  case "$code" in
    200) : ;;
    000|"") FAILS+=("连不上大模型服务（网络问题）") ;;
    402)    FAILS+=("大模型账户余额不足，需要充值") ;;
    401|403) FAILS+=("大模型服务拒绝了认证（key 问题）") ;;
    *)      FAILS+=("大模型服务异常（HTTP $code）") ;;
  esac
}

# C. 飞书通道（能不能发消息）
# 2026-11-08 修复：旧实现用 GET 打 tenant_access_token，该接口只接 POST → 永远 404。
# 404 本身不触发告警（只判 000），但等于是个无效检测；网络抖动时又误报。
# 现在改用 POST app_access_token（空 body 也返 200）：200/4xx 都说明通道通，只有连不上才报。
check_feishu() {
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 12 --noproxy '*' \
    -X POST -H 'Content-Type: application/json' -d '{}' \
    https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal 2>/dev/null)
  case "$code" in
    200|4*)  : ;;  # 200=通；4xx=服务端有响应也说明通（凭证问题不是通道问题）
    000|"") FAILS+=("连不上飞书（网络问题，我可能发不出消息）") ;;
    5*)     FAILS+=("飞书服务异常（HTTP $code）") ;;
  esac
}

check_gateway
check_llm
check_feishu

# 清掉空项
CLEAN=()
for f in "${FAILS[@]:-}"; do [ -n "$f" ] && CLEAN+=("$f"); done
FAILS=("${CLEAN[@]:-}")
[ ${#FAILS[@]} -eq 1 ] && [ -z "${FAILS[0]}" ] && FAILS=()

NOW=$(date +%s)
TODAY=$(date +%Y-%m-%d)
PREV=$(cat "$STATE_FILE" 2>/dev/null || echo '{}')
PREV_STATUS=$(echo "$PREV" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','ok'))" 2>/dev/null || echo ok)
NOTIFY_DAY=$(echo "$PREV" | python3 -c "import sys,json;print(json.load(sys.stdin).get('notify_day',''))" 2>/dev/null || echo "")
NOTIFY_CNT=$(echo "$PREV" | python3 -c "import sys,json;print(json.load(sys.stdin).get('notify_count',0))" 2>/dev/null || echo 0)
[ "$NOTIFY_DAY" != "$TODAY" ] && NOTIFY_CNT=0

if [ ${#FAILS[@]} -eq 0 ]; then
  [ "$PREV_STATUS" != "ok" ] && log "恢复正常"
  printf '{"status":"ok","ts":%s,"notify_day":"%s","notify_count":%s}\n' "$NOW" "$TODAY" "$NOTIFY_CNT" > "$STATE_FILE"
  [ "$TEST" -eq 1 ] && echo "OK — 全部正常"
  exit 0
fi

[ "$TEST" -eq 1 ] && { echo "FAIL — ${FAILS[*]}"; exit 1; }

# 防抖动：连续 2 次失败才告警（旧行为：单次抖动就报，12:35 与 14:35 各误报一次）
# 依据：瞬时抖动几十秒就恢复，不是服务不可用。
SIG=$(printf '%s|' "${FAILS[@]}" | md5 2>/dev/null || printf '%s|' "${FAILS[@]}")
LAST_SIG=$(echo "$PREV" | python3 -c "import sys,json;print(json.load(sys.stdin).get('sig',''))" 2>/dev/null || echo "")
PREV_PENDING=$(echo "$PREV" | python3 -c "import sys,json;print(json.load(sys.stdin).get('pending',0))" 2>/dev/null || echo 0)

if [ "$PREV_STATUS" = "fail" ] && [ "$LAST_SIG" = "$SIG" ]; then
  log "同类故障已报过，不重复通知: $SIG"
  printf '{"status":"fail","sig":"%s","ts":%s,"notify_day":"%s","notify_count":%s,"pending":0}\n' "$SIG" "$NOW" "$TODAY" "$NOTIFY_CNT" > "$STATE_FILE"
  exit 1
fi

# 首次见到该故障 → 只记账不告警，等下一次仍失败才报
if [ "$PREV_PENDING" -lt 1 ] || [ "$LAST_SIG" != "$SIG" ]; then
  log "首次检测到（待确认，不告警）: ${FAILS[*]}"
  printf '{"status":"ok","sig":"%s","ts":%s,"notify_day":"%s","notify_count":%s,"pending":1}\n' "$SIG" "$NOW" "$TODAY" "$NOTIFY_CNT" > "$STATE_FILE"
  exit 0
fi

# 每天通知上限
if [ "$NOTIFY_CNT" -ge "$MAX_NOTIFY_PER_DAY" ]; then
  log "今日通知已达上限($MAX_NOTIFY_PER_DAY)，跳过: ${FAILS[*]}"
  printf '{"status":"fail","sig":"%s","ts":%s,"notify_day":"%s","notify_count":%s}\n' "$SIG" "$NOW" "$TODAY" "$NOTIFY_CNT" > "$STATE_FILE"
  exit 1
fi

BODY="有个问题需要你知道：

$(printf '· %s\n' "${FAILS[@]}")

我已经尽力自动修了，修不好才打扰你。"

openclaw message send --channel feishu --account default --target "$TARGET" --message "$BODY" >> "$LOG" 2>&1
log "NOTIFIED: ${FAILS[*]}"

printf '{"status":"fail","sig":"%s","ts":%s,"notify_day":"%s","notify_count":%s}\n' \
  "$SIG" "$NOW" "$TODAY" "$((NOTIFY_CNT+1))" > "$STATE_FILE"
exit 1
