#!/bin/bash
# safe_sync_to_backup.sh — 备份仓同步（含软链目录专用，硬编码 dry-run 前置）
#
# 事故背景（2026-11-10 Self）：
#   手工跑 `rsync -a --delete workspace-self/scripts/ 备份仓/uself/scripts/`
#   时，源端 scripts/compliance 是软链、备份仓里是「软链 + 实体 .bak」结构，
#   --delete 把目标端目录当"多余内容"删掉换成软链，链路跟随失败后又写回实体文件
#   → 备份仓布局被破坏（靠 git checkout 回滚救回）。
#
# 本脚本的设计原则：把「先 dry-run 再执行」写进代码，不靠人记得。
#   1. 默认 --dry-run，只打印将要做什么；带 --apply 才真执行
#   2. --apply 时若 dry-run 输出里出现 "deleting"，直接中止并要求 --allow-delete
#   3. 真执行前自动 git 快照（备份仓本身是 git 仓 = 天然保险）
#   4. 不使用 -L；-a 保留软链语义
#
# 用法：
#   bash scripts/safe_sync_to_backup.sh                    # 预览（默认）
#   bash scripts/safe_sync_to_backup.sh --apply            # 执行（含 deleting 则中止）
#   bash scripts/safe_sync_to_backup.sh --apply --allow-delete   # 明确允许删除
#
set -uo pipefail

WORKSPACE="${WORKSPACE:-$HOME/.openclaw/workspace-self}"
BACKUP_REPO="${BACKUP_REPO:-$HOME/.opc-workspace-cache}"
AGENT_CAP="${AGENT_CAP:-uself}"

MODE="dry-run"
ALLOW_DELETE=false
for arg in "$@"; do
    case "$arg" in
        --apply)        MODE="apply" ;;
        --allow-delete) ALLOW_DELETE=true ;;
        --dry-run)      MODE="dry-run" ;;
        -h|--help)      sed -n '2,22p' "$0"; exit 0 ;;
        *) echo "未知参数: $arg" >&2; exit 2 ;;
    esac
done

[ -d "$WORKSPACE" ]   || { echo "❌ workspace 不存在: $WORKSPACE" >&2; exit 1; }
[ -d "$BACKUP_REPO/.git" ] || { echo "❌ 备份仓不存在或非 git 仓: $BACKUP_REPO" >&2; exit 1; }

TARGET="$BACKUP_REPO/$AGENT_CAP"
echo "📦 源:   $WORKSPACE"
echo "📦 目标: $TARGET"
echo "🧭 模式: $MODE (allow_delete=$ALLOW_DELETE)"
echo

# 同步项定义：目录用 rsync（-a 保留软链，不加 --delete），单文件用 cp
SYNC_DIRS=("memory" "scripts")
SYNC_FILES=(AGENTS.md SOUL.md IDENTITY.md MEMORY.md USER.md TOOLS.md HEARTBEAT.md)

HAS_DELETING=false
PLAN=""

echo "── 1/3 dry-run 检查 ──"
for d in "${SYNC_DIRS[@]}"; do
    [ -d "$WORKSPACE/$d" ] || { echo "  ⏭  跳过（源端无此目录）: $d"; continue; }
    OUT=$(rsync -a --dry-run --itemize-changes "$WORKSPACE/$d/" "$TARGET/$d/" 2>&1)
    DEL=$(printf '%s\n' "$OUT" | grep -c '^\*deleting' || true)
    if [ "${DEL:-0}" -gt 0 ]; then
        HAS_DELETING=true
        echo "  ⚠️  $d/ dry-run 含 $DEL 项 deleting（本脚本默认不加 --delete，仅作提示）:"
        printf '%s\n' "$OUT" | grep '^\*deleting' | head -10 | sed 's/^/       /'
    else
        echo "  ✅ $d/ 无删除项（$(printf '%s\n' "$OUT" | grep -c '^[<>ch]' || true) 项变更）"
    fi
    PLAN+="rsync -a \"$WORKSPACE/$d/\" \"$TARGET/$d/\""$'\n'
done

if [ "$HAS_DELETING" = true ] && [ "$MODE" = "apply" ] && [ "$ALLOW_DELETE" = false ]; then
    echo
    echo "🛑 中止：dry-run 出现 deleting。确认无误后加 --allow-delete 重跑。" >&2
    echo "   （提示：本脚本本身不使用 --delete，deleting 通常来自 --delete 参数或源/目标路径尾斜杠错位）" >&2
    exit 3
fi

if [ "$MODE" = "dry-run" ]; then
    echo
    echo "── 执行计划（未生效，加 --apply 执行）──"
    printf '%s' "$PLAN"
    echo "cp ${SYNC_FILES[*]} → $TARGET/"
    exit 0
fi

echo
echo "── 2/3 git 快照（回滚保险）──"
cd "$BACKUP_REPO" || exit 1
if [ -n "$(git status --porcelain -- "$AGENT_CAP/" 2>/dev/null)" ]; then
    git add -- "$AGENT_CAP/" 2>/dev/null
    if git commit -q -m "$AGENT_CAP: pre-sync 快照 $(date +%Y-%m-%dT%H:%M:%S)"; then
        echo "  ✅ 已提交 pre-sync 快照（可 git reset 回滚）"
    else
        echo "  ⚠️  快照提交失败，继续但请留意" >&2
    fi
else
    echo "  ✅ 工作区干净，无需快照"
fi

echo
echo "── 3/3 执行同步 ──"
for d in "${SYNC_DIRS[@]}"; do
    [ -d "$WORKSPACE/$d" ] || continue
    mkdir -p "$TARGET/$d"
    if rsync -a "$WORKSPACE/$d/" "$TARGET/$d/"; then
        echo "  ✅ $d/ 同步完成"
    else
        echo "  ❌ $d/ 同步失败" >&2
        exit 4
    fi
done
for f in "${SYNC_FILES[@]}"; do
    [ -f "$WORKSPACE/$f" ] && cp "$WORKSPACE/$f" "$TARGET/$f" 2>/dev/null
done
echo "  ✅ 顶层文件同步完成"

echo
echo "── 软链完好性校验 ──"
BROKEN=0
while IFS= read -r link; do
    [ -L "$link" ] || continue
    if [ -e "$link" ]; then
        echo "  ✅ $(basename "$link") → $(readlink "$link")"
    else
        echo "  ❌ 断链: $link → $(readlink "$link")" >&2
        BROKEN=$((BROKEN + 1))
    fi
done < <(find "$TARGET" -maxdepth 3 -type l 2>/dev/null)
[ "${BROKEN:-0}" -eq 0 ] || { echo "🛑 发现 $BROKEN 个断链，请检查" >&2; exit 5; }

echo
echo "✅ 同步完成。确认无误后按需 commit/push（本脚本不自动 push）。"
echo "   回滚方式: cd $BACKUP_REPO && git reset --hard HEAD~1"
