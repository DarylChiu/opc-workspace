#!/bin/bash
# ============================================================
# test_evolution.sh — OPC自进化基建L1 M0+M1 回归测试
# 用法: bash scripts/evolution/test_evolution.sh
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/../.."
PASS=0; FAIL=0

check() {
  local name="$1" result="$2"
  if [[ "$result" == "0" ]]; then
    echo "  ✅ $name"; PASS=$((PASS+1))
  else
    echo "  ❌ $name"; FAIL=$((FAIL+1))
  fi
}

echo "== M0: 信号捕获 =="
# 捕获脚本测试
OUT=$(bash scripts/evolution/capture_correction.sh --agent self --type retro --source milestone_report --text "测试复盘信号" --dry-run)
echo "$OUT" | grep -q '"type": "retro"' && check "capture dry-run JSON格式" 0 || check "capture dry-run JSON格式" 1

echo "== M1: 检索器 =="
# 场景1: 前端任务 → 规则命中
OUT=$(python3 scripts/evolution/retrieve_patterns.py --task "OPC看板前端UI修改" --project opc-dashboard 2>&1)
echo "$OUT" | grep -q "frontend_design" && check "场景1 前端任务命中设计语言" 0 || check "场景1 前端任务命中设计语言" 1

# 场景2: 天气 → 无注入
OUT=$(python3 scripts/evolution/retrieve_patterns.py --task "今天天气怎么样" 2>&1)
# 无debug时输出为空 = 无注入；有输出则检查是否无 [n] 行
if echo "$OUT" | grep -qE '^\[[0-9]\]'; then
  check "场景2 闲聊零注入" 1
else
  check "场景2 闲聊零注入" 0
fi

# 场景3: 开发 → git规则
OUT=$(python3 scripts/evolution/retrieve_patterns.py --task "开发新脚本" 2>&1)
echo "$OUT" | grep -q "git_compliance" && check "场景3 开发任务命中git规则" 0 || check "场景3 开发任务命中git规则" 1

echo ""
echo "=================================="
echo "结果: $PASS 通过 / $FAIL 失败"
[[ "$FAIL" == "0" ]] && echo "✅ 全部通过" || echo "❌ 有失败项"
exit $FAIL
