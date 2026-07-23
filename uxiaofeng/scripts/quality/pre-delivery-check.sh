#!/bin/bash
# L5 · 交付前质量自检 — pre-delivery checklist
# 用法: bash scripts/quality/pre-delivery-check.sh "项目名" "交付物路径"
# 返回: 0=全部通过, 1=有未通过项

set -e

PROJECT="${1:-未指定项目}"
ARTIFACT="${2:-未指定产物}"

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║  L5 · 交付前质量自检                           ║"
echo "╠════════════════════════════════════════════════╣"
echo "║  项目: ${PROJECT}"
echo "║  产物: ${ARTIFACT}"
echo "╚════════════════════════════════════════════════╝"
echo ""

PASS=0
FAIL=0
RESULTS=""

check() {
  local num=$1
  local label=$2
  local result=$3
  if [ "$result" = "OK" ]; then
    echo -e "  ✅ [${num}] ${label}"
    PASS=$((PASS + 1))
  else
    echo -e "  ❌ [${num}] ${label} — ${result}"
    FAIL=$((FAIL + 1))
  fi
}

# ─── 1. 完整流程跑通 ───
echo "── 检查 1: 完整流程是否跑通 ──"
read -p "  本地完整流程走通至少一次？(y/n) " yn
case $yn in
  [Yy]*) check 1 "本地完整流程走通" "OK" ;;
  *) check 1 "本地完整流程走通" "未跑通——请先本地验证" ;;
esac

# ─── 2. 代码正确性 ───
echo ""
echo "── 检查 2: 代码正确性 ──"

# Check JS syntax if index.html exists
JS_OK="未检测到 JS 文件"
for f in ${ARTIFACT} $(find . -name "*.html" -maxdepth 3 2>/dev/null); do
  if [ -f "$f" ] && file "$f" | grep -q "HTML"; then
    sed -n '/<script>/,/<\/script>/p' "$f" | sed '1d;$d' > /tmp/l5_js_check.js
    if node --check /tmp/l5_js_check.js 2>/dev/null; then
      JS_OK="OK ($f)"
    else
      JS_OK="JS 语法错误 ($f)"
    fi
    break
  fi
done
check 2 "前端 JS 语法" "$JS_OK"

# Check API if running
API_OK="未检测到 API 端点"
HEALTH=$(curl -s http://localhost:8768/api/health 2>/dev/null || \
         curl -s http://localhost:8766/api/health 2>/dev/null || \
         curl -s http://localhost:8765/health 2>/dev/null || echo "")
if echo "$HEALTH" | grep -q '"ok"'; then
  API_OK="OK"
else
  API_OK="API 健康检查失败或服务未启动"
fi
check 2 "API 端点可达" "$API_OK"

# ─── 3. 数据准确性 ───
echo ""
echo "── 检查 3: 数据准确性 ──"
read -p "  Mock数据/API返回与实际素材一致（无越界/格式不匹配/时长错误）？(y/n) " yn
case $yn in
  [Yy]*) check 3 "数据准确性" "OK" ;;
  *) check 3 "数据准确性" "请修正数据" ;;
esac

# ─── 4. 可访问性 ───
echo ""
echo "── 检查 4: 可访问性 ──"
read -p "  是否需要公网访问？(y/n) " yn
case $yn in
  [Yy]*)
    read -p "  公网 URL: " url
    if curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 5 2>/dev/null | grep -q "200"; then
      check 4 "公网可访问" "OK ($url)"
    else
      check 4 "公网可访问" "无法访问 $url"
    fi
    ;;
  *)
    check 4 "公网访问" "跳过（不需要）"
    ;;
esac

# ─── 5. 文档一致性 ───
echo ""
echo "── 检查 5: 文档一致性 ──"
read -p "  功能实现与设计方案文档一致？(y/n) " yn
case $yn in
  [Yy]*) check 5 "文档一致性" "OK" ;;
  *) check 5 "文档一致性" "请更新文档或修正实现" ;;
esac

# ─── 结果 ───
echo ""
echo "════════════════════════════════════════════════"
echo "  自检结果: ${PASS}/5 通过"
echo "════════════════════════════════════════════════"

if [ $FAIL -gt 0 ]; then
  echo ""
  echo "  ⚠️  有 ${FAIL} 项未通过，请修复后重新自检。"
  echo "  不要把 Daryl 当 Debugger。"
  exit 1
else
  echo ""
  echo "  ✅ L5 交付自检全部通过，可以提测。"
  echo "  回复中请标注「✅ L5 交付自检通过」"
  exit 0
fi
