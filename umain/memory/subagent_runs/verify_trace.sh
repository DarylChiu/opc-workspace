#!/bin/bash
# =============================================================================
# verify_trace.sh — 子代理 execution_trace.jsonl 验收脚本
# 版本: v1.0 | 创建: 2026-07-18 | 作者: 忧郁小猫(main)
#
# 用法:
#   bash verify_trace.sh <trace文件路径>
#
# 返回值:
#   PASS — 所有检查通过，trace 完整合规
#   WARN — 存在轻微问题（缺字段、缺summary.md），但仍可接受
#   FAIL — 存在严重问题（文件不存在、JSON 非法、时间戳乱序）
#
# 检查项目:
#   ① 文件存在且非空
#   ② 每行是合法 JSON
#   ③ 每行含 ts/step/action/result 四字段
#   ④ ts 时间戳单调递增
#   ⑤ summary.md 同时存在
# =============================================================================

set -euo pipefail

# --- 颜色 ---
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# --- 参数解析 ---
TRACE_FILE="${1:-}"

if [[ -z "$TRACE_FILE" ]]; then
    echo -e "${RED}[FAIL]${NC} 用法: bash verify_trace.sh <trace文件路径>"
    exit 2
fi

if [[ ! -f "$TRACE_FILE" ]]; then
    echo -e "${RED}[FAIL]${NC} ① 文件不存在: $TRACE_FILE"
    exit 2
fi

TRACE_DIR="$(dirname "$TRACE_FILE")"
SUMMARY_FILE="$TRACE_DIR/summary.md"

ERRORS=0
WARNINGS=0
LINE_COUNT=0

# =============================================================================
# ① 文件存在且非空
# =============================================================================
if [[ ! -s "$TRACE_FILE" ]]; then
    echo -e "${RED}[FAIL]${NC} ① 文件为空: $TRACE_FILE"
    exit 2
fi
echo -e "${GREEN}[PASS]${NC} ① 文件存在且非空: $TRACE_FILE ($(wc -c < "$TRACE_FILE" | tr -d ' ') bytes)"

# =============================================================================
# ② 每行是合法 JSON
# =============================================================================
JSON_ERRORS=0
while IFS= read -r line; do
    LINE_COUNT=$((LINE_COUNT + 1))
    # 跳过空行
    [[ -z "$(echo "$line" | tr -d '[:space:]')" ]] && continue
    if ! echo "$line" | python3 -c "import sys,json; json.loads(sys.stdin.readline())" 2>/dev/null; then
        echo -e "${RED}[FAIL]${NC} ② 第${LINE_COUNT}行不是合法 JSON: ${line:0:80}..."
        JSON_ERRORS=$((JSON_ERRORS + 1))
    fi
done < "$TRACE_FILE"

if [[ $JSON_ERRORS -gt 0 ]]; then
    echo -e "${RED}[FAIL]${NC} ② 共 ${JSON_ERRORS}/${LINE_COUNT} 行 JSON 解析失败"
    exit 2
fi
echo -e "${GREEN}[PASS]${NC} ② 全部 ${LINE_COUNT} 行 JSON 合法"

# =============================================================================
# ③ 每行含 ts/step/action/result 四字段
# =============================================================================
MISSING_FIELDS=0
LINE_NUM=0
while IFS= read -r line; do
    LINE_NUM=$((LINE_NUM + 1))
    [[ -z "$(echo "$line" | tr -d '[:space:]')" ]] && continue
    
    missing_for_line=""
    if ! echo "$line" | python3 -c "import sys,json; d=json.loads(sys.stdin.readline()); _=d['ts']" 2>/dev/null; then
        missing_for_line="$missing_for_line ts"
    fi
    if ! echo "$line" | python3 -c "import sys,json; d=json.loads(sys.stdin.readline()); _=d['step']" 2>/dev/null; then
        missing_for_line="$missing_for_line step"
    fi
    if ! echo "$line" | python3 -c "import sys,json; d=json.loads(sys.stdin.readline()); _=d['action']" 2>/dev/null; then
        missing_for_line="$missing_for_line action"
    fi
    if ! echo "$line" | python3 -c "import sys,json; d=json.loads(sys.stdin.readline()); _=d['result']" 2>/dev/null; then
        missing_for_line="$missing_for_line result"
    fi
    
    if [[ -n "$missing_for_line" ]]; then
        echo -e "${YELLOW}[WARN]${NC} ③ 第${LINE_NUM}行缺少字段:${missing_for_line}"
        echo "   > ${line:0:100}"
        MISSING_FIELDS=$((MISSING_FIELDS + 1))
    fi
done < "$TRACE_FILE"

if [[ $MISSING_FIELDS -gt 0 ]]; then
    echo -e "${YELLOW}[WARN]${NC} ③ 共 ${MISSING_FIELDS}/${LINE_COUNT} 行缺少必要字段（ts/step/action/result）"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}[PASS]${NC} ③ 全部 ${LINE_COUNT} 行包含 ts/step/action/result 四字段"
fi

# =============================================================================
# ④ ts 时间戳单调递增
# =============================================================================
TIMESTAMPS_OK=true
PREV_TS=""
LINE_NUM=0
while IFS= read -r line; do
    LINE_NUM=$((LINE_NUM + 1))
    [[ -z "$(echo "$line" | tr -d '[:space:]')" ]] && continue
    
    current_ts=$(echo "$line" | python3 -c "import sys,json; d=json.loads(sys.stdin.readline()); print(d.get('ts',''))" 2>/dev/null || echo "")
    
    if [[ -z "$current_ts" ]]; then
        continue  # already warned in ③
    fi
    
    if [[ -n "$PREV_TS" ]]; then
        # Compare ISO timestamps (lexicographic comparison works for ISO 8601)
        if [[ "$current_ts" < "$PREV_TS" ]]; then
            echo -e "${RED}[FAIL]${NC} ④ 第${LINE_NUM}行时间戳倒退: $current_ts < $PREV_TS (前一行)"
            TIMESTAMPS_OK=false
        fi
    fi
    PREV_TS="$current_ts"
done < "$TRACE_FILE"

if $TIMESTAMPS_OK; then
    echo -e "${GREEN}[PASS]${NC} ④ 时间戳单调递增: ${LINE_COUNT} 行全部有序"
else
    ERRORS=$((ERRORS + 1))
fi

# =============================================================================
# ⑤ summary.md 同时存在
# =============================================================================
if [[ -f "$SUMMARY_FILE" ]]; then
    echo -e "${GREEN}[PASS]${NC} ⑤ summary.md 存在: $SUMMARY_FILE ($(wc -c < "$SUMMARY_FILE" | tr -d ' ') bytes)"
else
    echo -e "${YELLOW}[WARN]${NC} ⑤ summary.md 不存在: $SUMMARY_FILE"
    WARNINGS=$((WARNINGS + 1))
fi

# =============================================================================
# 最终判定
# =============================================================================
echo ""
echo "--- 验收结果 ---"
echo "  文件: $TRACE_FILE"
echo "  行数: $LINE_COUNT"
echo "  错误: $ERRORS"
echo "  警告: $WARNINGS"

if [[ $ERRORS -gt 0 ]]; then
    echo -e "\n${RED}═══ [FAIL] 存在 ${ERRORS} 个严重错误，验收不通过 ═══${NC}"
    exit 2
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "\n${YELLOW}═══ [WARN] 存在 ${WARNINGS} 个警告，建议修复后重跑 ═══${NC}"
    exit 1
else
    echo -e "\n${GREEN}═══ [PASS] 全部检查通过，trace 完整合规 ═══${NC}"
    exit 0
fi
