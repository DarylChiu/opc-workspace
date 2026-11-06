#!/bin/bash
# alive_check.sh — 可用性守夜人（系统级，不依赖 LLM）
# 2026-11-06 建立，起因：11-05 全天静默故障，无任何告警送达 Daryl
#
# 设计铁律：
#   1. 不回显任何 secret（凭证只写临时 header 文件，用后即删）
#   2. 告警走 openclaw message send —— 与 Agent 的 LLM 链路完全独立
#      （LLM 挂了 → 消息通道照样能发；两者同时挂才发不出，此时本地落盘）
#   3. 状态机去重：FAIL 只在「首次进入失败」时告警，持续失败每 30min 复报一次
#   4. 依赖仅 curl / python3 / openclaw，无第三方包
#
# 检查项：
#   A. DeepSeek API 直连可达（带真实鉴权）
#   B. 飞书 API 可达
#   C. 网关进程存活 + 18789 端口监听
#   D. 网关出站是否仍被代理污染（OPENCLAW_PROXY_ACTIVE）
#   E. 各 Agent 最近一次 LLM 调用是否报错（扫 session jsonl 尾部）
#   F. 本机默认路由可用
#   G. 代理健康（2026-11-06 新增，Bryson 协作 + Kitty 实测）：
#      G1 代理端口是否监听（7892）
#      G2 节点域名 DoH 解析是否正常（mihomo 用 DoH 不依赖系统 DNS）
#      G3 代理出口是否真的能出网（连续多探，抓间歇性抖动）
#      G4 系统代理开启状态 + 是否与代理存活一致（最大风险源）
#      G5 订阅剩余流量/到期提醒
#
# 用法：
#   alive_check.sh            # 正常检查，异常才告警（静默成功）
#   alive_check.sh --test     # 只跑检查并打印结果，不发送告警

set -uo pipefail
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

WS="/Users/zhaoyuzhao/.openclaw/workspace"
STATE_DIR="$WS/memory/alive"
STATE_FILE="$STATE_DIR/state.json"
LOG_FILE="$STATE_DIR/alive.log"
TARGET="user:ou_3bf0d4dcf7a80d6ddf15be5bd2f7ad4f"
COOLDOWN=1800   # 持续失败时复报间隔（秒）

# 代理相关参数（微风 / mihomo）
PROXY_HOST="127.0.0.1"
PROXY_PORT="7892"
PROXY_API="http://127.0.0.1:9090"     # mihomo external-controller
PROXY_PROBE_URL="https://chatgpt.com"  # 只能走代理由境外可达的目标
PROXY_PROBES=5                          # 抖动检测：连续探测次数
PROXY_MIN_OK=3                          # 至少成功 N 次才算健康（5 次里≥3 次=60%）
SUBS_DB="$HOME/Library/Application Support/com.wfnetwork/database.sqlite"
# 系统代理值守开关：1=期望系统代理开启（关掉则告警），0=按应用注入模式（关闭属正常）
EXPECT_SYSTEM_PROXY=1

TEST_MODE=0
[ "${1:-}" = "--test" ] && TEST_MODE=1

mkdir -p "$STATE_DIR"
touch "$LOG_FILE"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }

FAILS=()
FAIL_KEYS=()
add_fail() { FAIL_KEYS+=("$1"); FAILS+=("$2"); log "FAIL[$1] $2"; }

# ---------- A. DeepSeek 真实鉴权探测 ----------
probe_deepseek() {
  local key="" hdr resp code
  # 优先环境变量
  key="${DEEPSEEK_API_KEY:-}"
  # 退回配置里的 apiKey（只读取，不打印）
  # 注意（2026-11-06 修正）：绝不能盲扫配置文件里的 sk- 前缀 ——
  # 会抓到其他服务商的 key（如 plugins.entries.moonshot.* 是 Kimi 的），
  # 拿去请求 DeepSeek 必然 401，造成误报"key 失效"。
  # 只认 deepseek 专属路径或模型 provider 配置。
  if [ -z "$key" ] && [ -f "$HOME/.openclaw/openclaw.json" ]; then
    key=$(python3 - <<'PY' 2>/dev/null
import json, os
p = os.path.expanduser('~/.openclaw/openclaw.json')
try:
    d = json.load(open(p))
except Exception:
    raise SystemExit
# 1) 优先直查 models.providers.deepseek.apiKey
try:
    k = d['models']['providers']['deepseek'].get('apiKey') or d['models']['providers']['deepseek'].get('api_key')
    if isinstance(k, str) and k.startswith('sk-'):
        print(k); raise SystemExit
except Exception:
    pass
# 2) 按 provider 名精确匹配，只取 deepseek 命中的分支
def walk(o, prov=None):
    if isinstance(o, dict):
        for k, v in o.items():
            nxt = k if k.lower() in ('deepseek','deepseek-native','deepseek-official') else prov
            if isinstance(v, str) and v.startswith('sk-') and nxt:
                return v
            r = walk(v, nxt)
            if r: return r
    elif isinstance(o, list):
        for v in o:
            r = walk(v, prov)
            if r: return r
    return None
print(walk(d) or '')
PY
)
  fi
  # 兜底：从 shell 环境变量取（gateway 启动环境的 DEEPSEEK_API_KEY）
  if [ -z "$key" ]; then
    key=$(launchctl getenv DEEPSEEK_API_KEY 2>/dev/null || true)
  fi
  if [ -z "$key" ]; then
    add_fail "deepseek_key" "DeepSeek 凭证读取失败（无法验证 API 可用性）"
    return
  fi

  hdr=$(mktemp)
  chmod 600 "$hdr"
  printf 'Authorization: Bearer %s\n' "$key" > "$hdr"
  # 用余额查询接口：能鉴权即代表链路+凭证双通（不消耗 token）
  resp=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 \
        --noproxy '*' -H @"$hdr" https://api.deepseek.com/user/balance 2>/dev/null)
  rm -f "$hdr"

  case "$resp" in
    200) : ;;  # 完全健康
    401|403) add_fail "deepseek_auth" "DeepSeek 鉴权失败（HTTP $resp）—— key 可能失效/欠费" ;;
    000|"") add_fail "deepseek_net" "DeepSeek 网络不可达（连接失败）—— 网络或代理问题" ;;
    *) add_fail "deepseek_http" "DeepSeek 返回异常状态 HTTP $resp" ;;
  esac
}

# ---------- B. 飞书 API ----------
probe_feishu() {
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 --noproxy '*' \
         https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal 2>/dev/null)
  case "$code" in
    000|"") add_fail "feishu_net" "飞书 API 不可达（连接失败）" ;;
    5*)     add_fail "feishu_5xx" "飞书 API 异常 HTTP $code" ;;
    *)      : ;;
  esac
}

# ---------- C. 网关进程 + 端口 ----------
# 端口探测优先（不受 argv 截断影响）：18789 监听 = 网关活着
GW_PIDS=""
find_gateway() {
  # 候选 1: 端口持有者
  local p
  p=$(lsof -nP -iTCP:18789 -sTCP:LISTEN -t 2>/dev/null | head -1)
  if [ -n "$p" ]; then echo "$p"; return; fi
  # 候选 2: ps 全量比对（避免 pgrep -f 的 argv 截断误判）
  ps -ax -o pid,command 2>/dev/null | grep -F "index.js gateway" | grep -v grep | awk '{print $1}' | head -1
}

probe_gateway() {
  GW_PIDS=$(find_gateway)
  if [ -z "$GW_PIDS" ]; then
    add_fail "gateway_proc" "网关进程不存在（Agent 全部离线）"
    return
  fi
  if ! lsof -nP -iTCP:18789 -sTCP:LISTEN >/dev/null 2>&1; then
    add_fail "gateway_port" "网关 18789 未监听"
  fi
}

# ---------- D. 代理污染检测 ----------
probe_proxy_pollution() {
  local gwpid
  local gwpid
  gwpid=$([ -n "${GW_PIDS:-}" ] && echo "$GW_PIDS" || find_gateway)
  [ -z "$gwpid" ] && return
  if ps eww "$gwpid" 2>/dev/null | grep -q "OPENCLAW_PROXY_ACTIVE=1"; then
    local pj
    pj=$(python3 -c "import json,os;print(json.dumps(json.load(open(os.path.expanduser('~/.openclaw/openclaw.json'))).get('proxy'),ensure_ascii=False))" 2>/dev/null)
    add_fail "proxy_pollution" "网关进程仍带代理环境变量（proxy 配置=$pj）—— 与 11-05 故障同形态"
  fi
}

# ---------- E. Agent 最近 LLM 调用健康 ----------
probe_agent_llm() {
  local bad=""
  for d in "$HOME"/.openclaw/agents/*/sessions; do
    [ -d "$d" ] || continue
    local agent newest
    agent=$(basename "$(dirname "$d")")
    newest=$(ls -t "$d"/*.jsonl 2>/dev/null | head -1)
    [ -z "$newest" ] && continue
    # 只看最近 10 分钟内有更新的 session，避免历史错误反复报警
    if [ -n "$(find "$newest" -mmin -10 2>/dev/null)" ]; then
      local err
      err=$(tail -20 "$newest" 2>/dev/null | python3 -c "
import sys,json
last=None
for line in sys.stdin:
    try: o=json.loads(line)
    except: continue
    if o.get('type')=='message' and o.get('message',{}).get('role')=='assistant':
        last=o['message']
if last and last.get('stopReason')=='error':
    print(last.get('errorMessage','error')[:120])
" 2>/dev/null)
      [ -n "$err" ] && bad="$bad $agent($err)"
    fi
  done
  [ -n "$bad" ] && add_fail "agent_llm" "Agent 最近调用报错:$bad"
}

# ---------- F. 默认路由 ----------
probe_route() {
  local gw
  gw=$(route -n get default 2>/dev/null | awk '/gateway:/{print $2}')
  if [ -z "$gw" ]; then
    add_fail "route" "无默认路由（网络断开）"
  elif ! ping -c 1 -t 3 "$gw" >/dev/null 2>&1; then
    add_fail "route_gw" "默认网关 $gw 不可达"
  fi
}


# ---------- G. 代理健康 ----------
PROXY_UP=0
probe_proxy_port() {
  if nc -z -G 2 "$PROXY_HOST" "$PROXY_PORT" >/dev/null 2>&1; then
    PROXY_UP=1
  else
    add_fail "proxy_port" "代理端口 ${PROXY_HOST}:${PROXY_PORT} 未监听（微风内核未启动或节点全失效）"
  fi
}

probe_proxy_doh() {
  local host ok
  host=$(curl -s --max-time 5 --noproxy '*' "$PROXY_API/proxies" 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin).get('proxies',{})
except Exception:
    sys.exit()
for k,v in d.items():
    t=(v.get('type') or '').upper()
    if t in ('VLESS','VMESS','TROJAN','SHADOWSOCKS','SS'):
        s=v.get('server')
        if s and ':' not in s:
            print(s); break
" 2>/dev/null)
  [ -z "$host" ] && return
  ok=$(curl -s --max-time 8 --noproxy '*' -H 'accept: application/dns-json' \
        "https://doh.pub/dns-query?name=${host}&type=A" 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
except Exception:
    print('PARSE_ERR'); raise SystemExit
print('OK' if (d.get('Answer') or []) else 'NODATA')
" 2>/dev/null)
  case "$ok" in
    OK) : ;;
    PARSE_ERR) return ;;
    NODATA) add_fail "proxy_dns" "节点域名 ${host} 经 DoH 无解析结果（节点可能集体失效）" ;;
  esac
}

probe_proxy_egress() {
  [ "$PROXY_UP" -eq 0 ] && return
  local ok=0 i code failed=""
  for i in $(seq 1 "$PROXY_PROBES"); do
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 \
           -x "http://${PROXY_HOST}:${PROXY_PORT}" "$PROXY_PROBE_URL" 2>/dev/null)
    if [ "$code" = "200" ]; then ok=$((ok+1)); else failed="$failed ${code:-timeout}"; fi
  done
  if [ "$ok" -lt "$PROXY_MIN_OK" ]; then
    add_fail "proxy_egress" "代理出口异常：${PROXY_PROBES} 次探测仅 ${ok} 次成功（失败码:${failed}）"
  elif [ "$ok" -lt "$PROXY_PROBES" ]; then
    log "WARN 代理抖动 ${ok}/${PROXY_PROBES}（失败码:${failed}）"
  fi
}

probe_system_proxy() {
  local http_en https_en socks_en any_on=0
  http_en=$(scutil --proxy 2>/dev/null | awk '/HTTPEnable/{print $3}')
  https_en=$(scutil --proxy 2>/dev/null | awk '/HTTPSEnable/{print $3}')
  socks_en=$(scutil --proxy 2>/dev/null | awk '/SOCKSEnable/{print $3}')
  [ "${http_en:-0}" = "1" ] && any_on=1
  [ "${https_en:-0}" = "1" ] && any_on=1
  [ "${socks_en:-0}" = "1" ] && any_on=1
  if [ "$any_on" -eq 1 ] && [ "$PROXY_UP" -eq 0 ]; then
    add_fail "sys_proxy_dead" "系统代理开启但代理端口 ${PROXY_PORT} 不可用 —— 全系统联网受阻（浏览器/git/npm 等）"
  elif [ "$any_on" -eq 1 ]; then
    log "INFO 系统代理开启（代理健康，预期状态）"
  elif [ "$PROXY_UP" -eq 1 ]; then
    # 反向盲区（Bryson 2026-11-06 提出）：代理活着但系统代理关了
    # → ChatGPT.app 从 Launchpad 直接点会连不上（实测直连 000 超时）
    # 仅在「代理可用但系统代理关闭」时提示，避免按应用注入模式下反复误报
    if [ "${EXPECT_SYSTEM_PROXY:-1}" = "1" ]; then
      add_fail "sys_proxy_off" "代理正常但系统代理已关闭 —— ChatGPT.app 直接点击可能连不上，需用 launch-chatgpt.sh 启动"
    else
      log "INFO 系统代理关闭（按应用注入模式，符合预期）"
    fi
  else
    log "INFO 系统代理关闭且代理不可用"
  fi
}

probe_subscription() {
  local info msg
  info=$(sqlite3 "$SUBS_DB" "SELECT subscription_info FROM profiles LIMIT 1;" 2>/dev/null)
  [ -z "$info" ] && return
  msg=$(python3 - "$info" <<'PY' 2>/dev/null
import sys, json, datetime
try: d = json.loads(sys.argv[1])
except Exception: raise SystemExit
total = d.get('total') or 0
used = (d.get('upload') or 0) + (d.get('download') or 0)
exp = d.get('expire') or 0
gs = 1024 ** 3
out = []
if total and used / total * 100 > 90:
    out.append(f"订阅流量已用 {used/total*100:.1f}%（{used/gs:.1f}/{total/gs:.0f} GB）")
if exp:
    days = (datetime.datetime.fromtimestamp(exp) - datetime.datetime.now()).days
    if days < 0: out.append("订阅已过期")
    elif days <= 3: out.append(f"订阅 {days} 天后到期")
print("；".join(out))
PY
)
  [ -n "$msg" ] && add_fail "subscription" "$msg"
}


# ---------- H. 代理自愈（2026-11-06 新增）----------
# 依据 11-02 历史：DNS 轮询导致节点 IP 变化 → mihomo 缓存旧 IP → 全部节点"不可达"
# 历史解法：重启 mihomo 重新解析。这里用更轻量的 9090 API 触发，不重启内核。
AUTO_HEAL=${AUTO_HEAL:-1}     # 1=允许自愈，0=只告警
HEAL_COOLDOWN=600             # 自愈最小间隔（秒）

proxy_self_heal() {
  [ "$AUTO_HEAL" -ne 1 ] && return
  [ "$PROXY_UP" -eq 1 ] || return     # 端口都没通，自愈救不了（需重开 App）

  # 只在「代理出口异常」时自愈
  local has_egress_fail=0 k
  for k in "${FAIL_KEYS[@]:-}"; do
    [ "$k" = "proxy_egress" ] && has_egress_fail=1
  done
  [ "$has_egress_fail" -eq 0 ] && return

  # 冷却检查
  local last_heal
  last_heal=$(python3 -c "import json;print(json.load(open('$STATE_FILE')).get('last_heal_ts',0))" 2>/dev/null || echo 0)
  if [ $((NOW - last_heal)) -lt $HEAL_COOLDOWN ]; then
    log "自愈跳过（冷却中，上次 $(( (NOW-last_heal)/60 )) 分钟前）"
    return
  fi

  log "自愈开始：触发节点重测以刷新 DNS 解析"
  # 1. 触发各代理组重新测速（url-test 会重新解析节点域名）
  local grp
  for grp in "自动选择" "故障转移" "微风网络"; do
    curl -s --max-time 20 --noproxy '*' -G \
      --data-urlencode "url=http://www.gstatic.com/generate_204" \
      --data-urlencode "timeout=5000" \
      "http://127.0.0.1:9090/group/${grp}/delay" >/dev/null 2>&1 && \
      log "自愈：${grp} 重测完成"
  done
  sleep 3

  # 2. 复测出口
  local ok=0 i code
  for i in 1 2 3; do
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 \
           -x "http://${PROXY_HOST}:${PROXY_PORT}" "$PROXY_PROBE_URL" 2>/dev/null)
    [ "$code" = "200" ] && ok=$((ok+1))
  done
  log "自愈复测：${ok}/3 成功"

  # 3. 记录自愈时间戳
  python3 - "$STATE_FILE" "$NOW" <<'PY' 2>/dev/null
import sys, json
f, ts = sys.argv[1], int(sys.argv[2])
try:
    d = json.load(open(f))
except Exception:
    d = {}
d['last_heal_ts'] = ts
json.dump(d, open(f, 'w'))
PY

  if [ "$ok" -ge 2 ]; then
    HEAL_RESULT="代理自愈成功（${ok}/3 复测通过）"
    log "自愈成功"
    # 从 FAILS 中移除 proxy_egress（已修复）
    return 0
  else
    HEAL_RESULT="代理自愈尝试失败（${ok}/3）"
    log "自愈失败"
    return 1
  fi
}

# ========== 执行 ==========
NOW=$(date +%s)
probe_route
probe_gateway          # 先定位网关 pid
probe_proxy_pollution
probe_deepseek
probe_feishu
probe_agent_llm
probe_proxy_port
probe_proxy_doh
probe_proxy_egress
probe_system_proxy
probe_subscription

# 自愈：若代理出口异常，先尝试自动修复，再决定是否告警
HEAL_RESULT=""
if proxy_self_heal; then
  # 自愈成功 → 从 FAILS / FAIL_KEYS 中移除 proxy_egress
  NEW_FAILS=(); NEW_KEYS=()
  for i in "${!FAIL_KEYS[@]}"; do
    if [ "${FAIL_KEYS[$i]}" != "proxy_egress" ]; then
      NEW_KEYS+=("${FAIL_KEYS[$i]}")
      NEW_FAILS+=("${FAILS[$i]}")
    fi
  done
  FAIL_KEYS=("${NEW_KEYS[@]:-}")
  FAILS=("${NEW_FAILS[@]:-}")
  [ ${#FAIL_KEYS[@]} -eq 0 ] && FAIL_KEYS=() && FAILS=()
fi

NOW=$(date +%s)
PREV_STATUS=$(python3 -c "import json,os;print(json.load(open('$STATE_FILE'))['status'])" 2>/dev/null || echo "ok")
PREV_TS=$(python3 -c "import json,os;print(json.load(open('$STATE_FILE'))['last_alert_ts'])" 2>/dev/null || echo "0")

if [ ${#FAILS[@]} -eq 0 ] || { [ "${#FAILS[@]}" -eq 1 ] && [ -z "${FAILS[0]}" ]; }; then
  if [ "$PREV_STATUS" != "ok" ]; then
    # 计算故障持续时长（Bryson 2026-11-06 建议：没有持续时间的恢复通知等于没通知）
    FAIL_SINCE=$(python3 -c "import json;print(json.load(open('$STATE_FILE')).get('fail_since_ts') or 0)" 2>/dev/null || echo "0")
    DUR_HUMAN=$(python3 -c "
try:
    fs = int('${FAIL_SINCE:-0}')
    secs = ($NOW - fs) if fs > 0 else 0
except Exception:
    secs = 0
if secs > 86400: secs = 0   # 脏数据保护：超过1天的时长不予采信
if secs < 60: print(f'{secs}秒')
elif secs < 3600: print(f'{secs//60}分钟')
else:
    h=secs//3600; m=(secs%3600)//60
    print(f'{h}小时{m}分钟' if m else f'{h}小时')
" 2>/dev/null)
    PREV_FAILS=$(python3 -c "import json;print('；'.join(json.load(open('$STATE_FILE')).get('fails',[])))" 2>/dev/null)
    log "RECOVERED after $DUR_HUMAN"
    if [ $TEST_MODE -eq 0 ]; then
      RECOVER_BODY="✅ 守夜人恢复 · $(date '+%m-%d %H:%M')

故障已恢复，持续 ${DUR_HUMAN}。
期间异常：
$(python3 -c "import sys;print('\n'.join('• '+x for x in sys.argv[1:] if x))" "$PREV_FAILS")

（系统级通知，不消耗模型额度）"
      openclaw message send --channel feishu --account default --target "$TARGET" --message "$RECOVER_BODY" >> "$LOG_FILE" 2>&1
      log "RECOVERY NOTICE SENT (duration=$DUR_HUMAN)"
    fi
  fi
  printf '{"status":"ok","last_check_ts":%s,"last_alert_ts":%s,"fails":[]}\n' "$NOW" "$PREV_TS" > "$STATE_FILE"
  if [ $TEST_MODE -eq 1 ]; then echo "OK — 全部检查通过"; fi
  exit 0
fi

# 有失败
SIG=$(printf '%s\n' "${FAIL_KEYS[@]}" | sort | tr '\n' ',')
LAST_SIG=$(python3 -c "import json;print(json.load(open('$STATE_FILE')).get('sig',''))" 2>/dev/null || echo "")

NEED_ALERT=0
if [ "$PREV_STATUS" = "ok" ] || [ "$LAST_SIG" != "$SIG" ]; then
  NEED_ALERT=1                      # 首次进入失败 / 故障集合变化
elif [ $((NOW - PREV_TS)) -ge $COOLDOWN ]; then
  NEED_ALERT=1                      # 持续失败，定期复报
fi

HEAL_LINE=""
[ -n "${HEAL_RESULT:-}" ] && HEAL_LINE="
（自愈：${HEAL_RESULT}）"

BODY="🚨 守夜人告警 · $(date '+%m-%d %H:%M')

检测到 ${#FAILS[@]} 项异常：
$(printf '• %s\n' "${FAILS[@]}")${HEAL_LINE}

（若需排查请直接问我；这是系统级自动告警，不消耗模型额度）"

FAIL_SINCE=$(python3 -c "import json;print(json.load(open('$STATE_FILE')).get('fail_since_ts',0) or $NOW)" 2>/dev/null || echo "$NOW")
printf '{"status":"fail","sig":"%s","fail_since_ts":%s,"last_check_ts":%s,"last_alert_ts":%s,"fails":%s}\n' \
  "$SIG" "$FAIL_SINCE" "$NOW" \
  "$([ $NEED_ALERT -eq 1 ] && echo $NOW || echo $PREV_TS)" \
  "$(python3 -c "import json,sys;print(json.dumps(sys.argv[1:],ensure_ascii=False))" "${FAILS[@]}")" \
  > "$STATE_FILE"

if [ $TEST_MODE -eq 1 ]; then
  echo "FAIL — ${FAILS[*]}"
  exit 1
fi

if [ $NEED_ALERT -eq 1 ]; then
  openclaw message send --channel feishu --account default --target "$TARGET" --message "$BODY" >> "$LOG_FILE" 2>&1
  log "ALERT SENT: $SIG"
else
  log "fail persists (no alert, cooldown): $SIG"
fi
exit 1
