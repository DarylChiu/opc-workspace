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
OUT=$(python3 scripts/evolution/retrieve_patterns.py --task "OPC看板前端UI修改" --project opc-dashboard --debug 2>&1)
echo "$OUT" | grep -q "frontend_design" && check "场景1 前端任务命中设计语言" 0 || check "场景1 前端任务命中设计语言" 1

# 场景2: 天气 → 无注入
OUT=$(python3 scripts/evolution/retrieve_patterns.py --task "今天天气怎么样" --debug 2>&1)
echo "$OUT" | grep -q "注入: 0" && check "场景2 闲聊零注入" 0 || check "场景2 闲聊零注入" 1

# 场景3: 开发 → git规则
OUT=$(python3 scripts/evolution/retrieve_patterns.py --task "开发新脚本" --debug 2>&1)
echo "$OUT" | grep -q "git_compliance" && check "场景3 开发任务命中git规则" 0 || check "场景3 开发任务命中git规则" 1

echo "== M2: 任务识别状态机 =="
SID="test_m2_$$"
# 场景4: 纯推理任务开始 → new_task
OUT=$(python3 scripts/evolution/classify_task.py --msg "帮我分析XX方案可行性" --session $SID 2>&1)
echo "$OUT" | grep -q '"decision": "new_task"' && check "M2-1 新任务识别" 0 || check "M2-1 新任务识别" 1

# 场景5: 继续 → continuation
OUT=$(python3 scripts/evolution/classify_task.py --msg "继续分析成本部分" --session $SID 2>&1)
echo "$OUT" | grep -q '"decision": "continuation"' && check "M2-2 延续识别" 0 || check "M2-2 延续识别" 1

# 场景6: 中途要md报告 → deliverable_upgrade
OUT=$(python3 scripts/evolution/classify_task.py --msg "给我输出个md文件报告" --session $SID 2>&1)
echo "$OUT" | grep -q '"decision": "deliverable_upgrade"' && check "M2-3 产出升级识别" 0 || check "M2-3 产出升级识别" 1

# 场景7: 天气闲聊 → chat
OUT=$(python3 scripts/evolution/classify_task.py --msg "今天天气怎么样" --session ${SID}_b 2>&1)
echo "$OUT" | grep -q '"decision": "chat"' && check "M2-4 闲聊零注入" 0 || check "M2-4 闲聊零注入" 1

# 场景8: 主题切换 → new_task
OUT=$(python3 scripts/evolution/classify_task.py --msg "别算了，改一下OPC看板前端UI" --session $SID 2>&1)
echo "$OUT" | grep -q '"decision": "new_task"' && check "M2-5 主题切换识别" 0 || check "M2-5 主题切换识别" 1

# 清理测试session
python3 scripts/evolution/classify_task.py --reset --session $SID >/dev/null 2>&1
python3 scripts/evolution/classify_task.py --reset --session ${SID}_b >/dev/null 2>&1

echo "== M2: 注入器 =="
INJ_SID="test_inj_$$"
# 场景9: 全量注入产出模板
OUT=$(python3 scripts/evolution/inject_lessons.py --msg "开发成本统计脚本" --mode full --session $INJ_SID 2>&1)
echo "$OUT" | grep -q "历史教训" && check "M2-6 全量注入模板" 0 || check "M2-6 全量注入模板" 1

# 场景10: 轻量注入产出模板
OUT=$(python3 scripts/evolution/inject_lessons.py --msg "给我输出个md文件报告" --mode light --session $INJ_SID 2>&1)
echo "$OUT" | grep -q "产出物规范" && check "M2-7 轻量注入模板" 0 || check "M2-7 轻量注入模板" 1

# 清理注入测试session
python3 -c "
import json, os, sys
f = os.path.expanduser('~/.openclaw/workspace/memory/evolution/state/task_state.json')
sid = sys.argv[1]
if os.path.exists(f):
    d = json.load(open(f))
    d['sessions'].pop(sid, None)
    json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)
" $INJ_SID 2>/dev/null || true

echo ""
echo "=================================="
echo "结果: $PASS 通过 / $FAIL 失败"
[[ "$FAIL" == "0" ]] && echo "✅ 全部通过" || echo "❌ 有失败项"
exit $FAIL
