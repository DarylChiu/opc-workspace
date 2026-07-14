#!/bin/bash
# ============================================================
# 记忆系统 v3 · Cron: 定时触发各 Agent 更新 project_[AgentID].md
# 触发时间: 07:00 / 13:00 / 19:00 daily
# 闭环: 检查真实文件新鲜度 → 超阈值则用【一次性隔离session】触发对应 Agent 自更新
# ------------------------------------------------------------
# 🛡️ 防僵尸三道硬保险 (2026-07-14 Kitty, 应 Daryl 对 7/5 僵尸事故的追问):
#   ① 一次性 session: 每次触发用唯一 --session-id (带时间戳), 用完即弃,
#      永不复用 agent:X:main 默认key → 上下文不累积, 不会滚雪球烧钱。
#   ② 失败熔断: 单个 Agent 触发失败/超时立即跳过, 不重试不挂起 (7/5 是失败仍烧钱)。
#   ③ 每日触发上限: 每 Agent 每天最多 MAX_DAILY_TRIGGERS 次, 超过硬停 → 成本封顶。
#      单次成本实测 ~$0.002, 即使全触发上限, 单Agent单日 < $0.05, 4Agent < $0.2/天。
# ------------------------------------------------------------
# 修复历史:
#   2026-07-14a 从"只写日志空壳"重构为真正触发闭环 (路径修正 + openclaw agent 触发)
#   2026-07-14b 加防僵尸三道保险 (一次性session + 熔断 + 每日上限)
# ============================================================

set -uo pipefail

export PATH="/opt/homebrew/bin:/opt/homebrew/opt/node@22/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

OPENCLAW_BIN="$(command -v openclaw || echo /opt/homebrew/bin/openclaw)"
LOG_DIR="/tmp/openclaw_project_cron"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cron_$(date +%Y%m%d).log"
GLOBAL_LOG="/tmp/project_cron.log"
# 每日触发计数文件 (防上限用)
COUNT_FILE="$LOG_DIR/trigger_count_$(date +%Y%m%d).txt"
touch "$COUNT_FILE"

# 新鲜度阈值(小时): 超过则触发。20h 使每 Agent 实际每日约触发一次
STALE_HOURS="${STALE_HOURS:-20}"
# 单次触发超时(秒): 到点强杀, 不挂起
AGENT_TIMEOUT="${AGENT_TIMEOUT:-240}"
# 🛡️② 每个 Agent 每天最多触发次数 (成本封顶硬保险)
MAX_DAILY_TRIGGERS="${MAX_DAILY_TRIGGERS:-2}"

AGENT_FILES=(
  "main:$HOME/.openclaw/workspace/memory/project_main.md"
  "xiaofeng:$HOME/.openclaw/xiaofeng_workspace/memory/project_xiaofeng.md"
  "balance:$HOME/.openclaw/workspace-balance/memory/project_Balance.md"
  "self:$HOME/.openclaw/workspace-self/memory/project_Self.md"
)

log() {
  local msg="[$(date '+%Y-%m-%d %H:%M:%S %Z')] $1"
  echo "$msg" | tee -a "$LOG_FILE" >> "$GLOBAL_LOG"
}

# 今天某 agent 已触发次数 (返回干净单个整数; grep -c 无匹配时 exit=1 会触发 || 导致双值, 故用 awk 兵底)
daily_count() {
  local n
  n=$(grep -c "^$1\$" "$COUNT_FILE" 2>/dev/null)
  # 剥离非数字 / 换行, 空则为 0
  n=$(printf '%s' "$n" | tr -cd '0-9')
  echo "${n:-0}"
}

trigger_agent_update() {
  local agent="$1" file="$2" age_h="$3"
  local fname; fname="$(basename "$file")"

  # 🛡️② 每日上限熔断
  local cnt; cnt=$(daily_count "$agent")
  if [ "$cnt" -ge "$MAX_DAILY_TRIGGERS" ]; then
    log "🛑 $agent: 今日已触发 ${cnt} 次 (上限 ${MAX_DAILY_TRIGGERS})，跳过 → 成本封顶保护"
    return 0
  fi

  # 🛡️① 一次性隔离 session id: 用完即弃, 永不复用累积上下文
  local once_sid="proj-update-${agent}-$(date +%Y%m%d%H%M%S)-$$"
  local prompt="[系统定时任务·记忆系统v3] 你的项目看板文件 memory/${fname} 已 ${age_h}h 未更新。请依据当前 memory/active.md 与近期实际工作，更新 memory/${fname}：刷新进行中项目的阶段/进度/本周进展、里程碑状态、成本归集与更新时间戳。仅更新文件，完成后用一句话确认，不要展开长篇汇报。"

  log "🔄 $agent: 触发自更新 (过期 ${age_h}h, 一次性session=${once_sid}, 今日第 $((cnt+1)) 次)"
  # 记一次触发 (先记后跑, 避免失败重刷时不计数)
  echo "$agent" >> "$COUNT_FILE"

  # 🛡️③ 失败熔断: --timeout 到点强杀; 失败仅记录, 不重试不挂起
  if "$OPENCLAW_BIN" agent --agent "$agent" --session-id "$once_sid" \
        --message "$prompt" --timeout "$AGENT_TIMEOUT" --json >>"$LOG_FILE" 2>&1; then
    log "✅ $agent: 触发成功 (一次性session已随本轮结束, 不驻留)"
  else
    log "❌ $agent: 触发失败/超时, 已跳过 (不重试、不挂起, 见 $LOG_FILE)"
  fi
}

log "========== Cron 触发: project 更新闭环 (阈值 ${STALE_HOURS}h, 每日上限 ${MAX_DAILY_TRIGGERS}) =========="

now=$(date +%s)
for entry in "${AGENT_FILES[@]}"; do
  agent="${entry%%:*}"
  file="${entry#*:}"

  if [ ! -f "$file" ]; then
    log "❗ $agent: $(basename "$file") 不存在 → 触发 Agent 创建"
    trigger_agent_update "$agent" "$file" "999"
    continue
  fi

  mtime=$(stat -f %m "$file" 2>/dev/null || echo 0)
  age_h=$(( (now - mtime) / 3600 ))

  if [ "$age_h" -ge "$STALE_HOURS" ]; then
    trigger_agent_update "$agent" "$file" "$age_h"
  else
    log "✅ $agent: $(basename "$file") 新鲜 (${age_h}h < ${STALE_HOURS}h)，跳过"
  fi
done

log "========== 闭环完成 =========="
