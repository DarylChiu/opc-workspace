#!/usr/bin/env bash
# net_body_check.sh — 独立于 audit.sh 的「日记净正文」校验
#
# 背景（2026-11-14 Daryl 指令）：
#   现有 audit.sh 步骤 7 的骨架检测只能证明「检测器不再误报」，
#   不能证明「日记有实质内容」。两件事必须分开记账，
#   否则真出空日记时会被全绿盖住。
#
# 判定口径（与 audit.sh 完全解耦，不读它的任何变量）：
#   净正文行数 = 总行数
#              - 空行
#              - HTML 注释行
#              - cron 模板标记行（见 CRON_MARKERS）
#              - 纯 `##`/`###` 标题行（无正文）
#              - 纯表格分隔行（|---|）
#              - 「待补充/待填写/TODO」占位行
#
#   净正文行数 > MIN_LINES 且 非占位字符数 > MIN_CHARS 才算 PASS
#   默认 MIN_LINES=8 / MIN_CHARS=200（可用 --min-lines / --min-chars 覆盖）
#
# 退出码：0=PASS  1=WARN  2=FAIL(净正文不足)  3=文件不存在
#
# 用法：
#   bash scripts/compliance/net_body_check.sh memory/2026-11-14.md
#   bash scripts/compliance/net_body_check.sh --recent 3      # 检查最近 3 天
#   bash scripts/compliance/net_body_check.sh --all          # 检查全部日记
#   bash scripts/compliance/net_body_check.sh --json         # 机器可读

set -uo pipefail

MIN_LINES=8
MIN_CHARS=200
JSON=0
MODE="file"
TARGET=""
RECENT=0

while [ $# -gt 0 ]; do
  case "$1" in
    --min-lines) MIN_LINES="$2"; shift 2 ;;
    --min-chars) MIN_CHARS="$2"; shift 2 ;;
    --json) JSON=1; shift ;;
    --recent) MODE="recent"; RECENT="$2"; shift 2 ;;
    --all) MODE="all"; shift ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    *) MODE="file"; TARGET="$1"; shift ;;
  esac
done

# cron 模板标记 / 占位符特征（小写匹配）
CRON_MARKERS='cron 审计自动创建|cron 自动创建|由 .*cron 自动创建|内容待补充|待从 session 历史|需从 session 历史|待补充|待填写|待现场补|todo|tbd|占位'

check_file() {
  local f="$1"
  if [ ! -f "$f" ]; then
    echo "MISSING  $f"
    return 3
  fi

  local total net chars
  total=$(wc -l < "$f" | tr -d ' ')

  # 逐行过滤，输出净正文
  local body
  body=$(awk '
    {
      line=$0
      # 去首尾空白
      gsub(/^[ \t]+|[ \t]+$/, "", line)
      if (line == "") next                      # 空行
      if (line ~ /^<!--/) next                  # HTML 注释
      if (line ~ /^---+$/) next                 # 分隔线
      if (line ~ /^\|?[ :|-]+\|?$/) next        # 表格分隔行
      if (line ~ /^#+[ ]*$/) next               # 纯标题无文字
      print line
    }
  ' "$f" | grep -viE "$CRON_MARKERS" || true)

  # 注意：body 为空时 printf '%s\n' 会输出一个空行，导致 grep -c . 误计为 1。
  # 另：grep -c . 无匹配时退出码为 1，`|| true` 会把输出吞掉，所以用 awk 计数更稳。
  if [ -z "$body" ]; then
    net=0
    chars=0
  else
    net=$(printf '%s\n' "$body" | awk 'NF{n++} END{print n+0}')
    chars=$(printf '%s' "$body" | tr -d '[:space:]' | wc -c | tr -d ' ')
  fi

  local verdict
  if [ "$net" -ge "$MIN_LINES" ] && [ "$chars" -ge "$MIN_CHARS" ]; then
    verdict="PASS"
  elif [ "$net" -ge 3 ] && [ "$chars" -ge 60 ]; then
    # 有实质文字但不够厚 → WARN（允许进一步人工判断）
    verdict="WARN"
  else
    # 去掉模板标记后基本为空 → 真账缺失，必须 FAIL
    verdict="FAIL"
  fi

  if [ "$JSON" -eq 1 ]; then
    printf '{"file":"%s","total":%d,"net_lines":%d,"net_chars":%d,"min_lines":%d,"min_chars":%d,"verdict":"%s"}\n' \
      "$f" "$total" "$net" "$chars" "$MIN_LINES" "$MIN_CHARS" "$verdict"
  else
    printf '%-6s %-42s 总%4d行 / 净%3d行 / %5d字\n' "$verdict" "$(basename "$f")" "$total" "$net" "$chars"
  fi

  case "$verdict" in
    PASS) return 0 ;;
    WARN) return 1 ;;
    *)    return 2 ;;
  esac
}

WORST=0
shopt -s nullglob

case "$MODE" in
  file)
    check_file "$TARGET"; WORST=$?
    ;;
  recent|all)
    if [ "$MODE" = "recent" ]; then
      files=$(ls -1t memory/2026-*.md 2>/dev/null | head -"$RECENT")
    else
      files=$(ls -1t memory/2026-*.md 2>/dev/null)
    fi
    for f in $files; do
      check_file "$f"
      rc=$?
      [ "$rc" -gt "$WORST" ] && WORST=$rc
    done
    ;;
esac

[ "$JSON" -eq 1 ] && echo "{\"worst_rc\":$WORST,\"min_lines\":$MIN_LINES,\"min_chars\":$MIN_CHARS}"

echo ""
case "$WORST" in
  0) echo "→ 结论: PASS（净正文达标，与「检测器不误报」是两件事，此为内容侧独立校验）" ;;
  1) echo "→ 结论: WARN（有内容但偏薄，未达 $MIN_LINES 行 / $MIN_CHARS 字）" ;;
  2) echo "→ 结论: FAIL（净正文不足，去掉模板标记后基本为空 → 真账缺失，需补实内容）" ;;
  3) echo "→ 结论: MISSING（文件不存在）" ;;
esac
exit "$WORST"
