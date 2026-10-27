#!/bin/bash
# ============================================================
# archive-before-cleanup.sh — 项目清理前归档
# 
# 用法: bash scripts/archive-before-cleanup.sh "<清理描述>"
# 
# 作用: 
#   1. 在清理/删除/替换文件前，把当前全量代码+DB快照到 _archive/
#   2. 自动创建 git commit 作为版本基线
#   3. 记录清理原因，方便以后回滚
# ============================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ARCHIVE_DIR="$PROJECT_DIR/_archive"
TIMESTAMP=$(date +%Y-%m-%d_%H%M)
REASON="${1:-未记录原因}"
SNAPSHOT_DIR="$ARCHIVE_DIR/${TIMESTAMP}_${REASON// /_}"

mkdir -p "$SNAPSHOT_DIR"

echo "📦 归档快照: $SNAPSHOT_DIR"

# 1. 复制关键文件（排除 venv, __pycache__, _archive 自身）
rsync -a --exclude 'venv/' --exclude '__pycache__/' --exclude '_archive/' \
      --exclude '*.pyc' --exclude '.git/' \
      "$PROJECT_DIR/" "$SNAPSHOT_DIR/"

# 2. 记录清理原因
cat > "$SNAPSHOT_DIR/_CLEANUP_NOTE.txt" << EOF
清理时间: $(date)
清理原因: $REASON
快照目录: $SNAPSHOT_DIR
EOF

# 3. Git commit 当前状态
cd "$PROJECT_DIR"
git add -A 2>/dev/null || true
git commit -m "snapshot: pre-cleanup — $REASON" 2>/dev/null || echo "  (git commit skipped — no changes or not a repo)"

echo ""
echo "✅ 快照已保存: $SNAPSHOT_DIR"
echo "   如需回滚: cp -r $SNAPSHOT_DIR/* $PROJECT_DIR/"
echo "   或从 git:  git checkout <commit-hash> -- <file>"
