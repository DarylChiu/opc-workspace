#!/bin/bash
# ============================================================
# capture_correction.sh — M0 信号捕获（确定性脚本，不依赖Agent自觉）
#
# 用途: 捕获纠错/失败/审计违规等进化信号，追加到 corrections_inbox.jsonl
# 触发: Daryl纠错时 / checker FAIL时 / 审计违规时 / 里程碑复盘时
#
# 用法:
#   capture_correction.sh --agent <AgentID> --type <type> --text "<纠错内容>" [--source <来源>] [--project <项目>]
#
#   --agent   AgentID: main|xiaofeng|balance|self   (必填)
#   --type    信号类型: correction(纠错)|failure(失败)|audit(审计违规)|retro(复盘)  (必填)
#   --text    信号内容原文（必填，建议含"上下文+错误+正确做法"三要素）
#   --source  来源: daryl_message|checker_fail|cron_audit|milestone_report (默认: manual)
#   --project 涉及项目（可选）
#   --dry-run 只打印将要写入的内容，不写入
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${WORKSPACE:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
INBOX="${WORKSPACE}/memory/evolution/corrections_inbox.jsonl"
TS=$(date +%Y-%m-%dT%H:%M:%S%z)

AGENT=""; TYPE=""; TEXT=""; SOURCE="manual"; PROJECT=""; DRY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)   AGENT="$2"; shift 2 ;;
    --type)    TYPE="$2"; shift 2 ;;
    --text)    TEXT="$2"; shift 2 ;;
    --source)  SOURCE="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) echo "❌ 未知参数: $1" >&2; exit 2 ;;
  esac
done

# ---- 校验 ----
if [[ -z "$AGENT" || -z "$TYPE" || -z "$TEXT" ]]; then
  echo "❌ 必填参数缺失: --agent --type --text" >&2
  echo "用法见脚本头部注释" >&2
  exit 2
fi

case "$AGENT" in main|xiaofeng|balance|self) ;; *) echo "❌ 非法 AgentID: $AGENT" >&2; exit 2 ;; esac
case "$TYPE" in correction|failure|audit|retro) ;; *) echo "❌ 非法 type: $TYPE (correction|failure|audit|retro)" >&2; exit 2 ;; esac

# 文本转义为 JSON 安全（用 python3 做，避免 jq 依赖）
JSON_LINE=$(python3 -c "
import json, sys
rec = {
    'ts': sys.argv[1],
    'agent': sys.argv[2],
    'type': sys.argv[3],
    'text': sys.argv[4],
    'source': sys.argv[5],
    'project': sys.argv[6] or None,
    'status': 'pending',   # pending → distilled → dropped
}
print(json.dumps(rec, ensure_ascii=False))
" "$TS" "$AGENT" "$TYPE" "$TEXT" "$SOURCE" "$PROJECT")

if [[ "$DRY" == "1" ]]; then
  echo "$JSON_LINE"
  exit 0
fi

mkdir -p "$(dirname "$INBOX")"
echo "$JSON_LINE" >> "$INBOX"
echo "✅ 信号已捕获 → $INBOX"
python3 -c "import json,sys; d=json.loads(sys.argv[1]); print('   %s | %s | %s | %s' % (d['ts'], d['agent'], d['type'], d['text'][:60]))" "$JSON_LINE"
