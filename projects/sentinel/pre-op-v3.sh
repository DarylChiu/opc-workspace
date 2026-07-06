#!/bin/bash
# L2: 操作前合规判断 — P0-P3 决策前置 v3 (Sentinel 对齐)
# 用法: bash scripts/compliance/pre-op.sh "<操作描述>" "[涉及文件]" "[影响范围]"
#
# v3 变更 (2026-07-06, Sentinel Grill-me 确认):
#   - sessions_send → P2
#   - >3 文件 → P2 (不阻断，记录警告)
#   - 删除非注释代码 → P2 (靠回滚兜底)
#   - 新增: 外部边界操作判定 (API/发布/密钥)
#   - 新增: 公共接口/依赖/schema → P1
#   - 路径敏感度分级

OP_DESC="${1:-未指定操作}"
FILES="${2:-无}"
SCOPE="${3:-local}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ─── P0 绝对红线 ────────────────────────────────────
check_p0_block() {
    local desc="$1"
    # 金钱
    if echo "$desc" | grep -qiE "(付款|扣款|转账|充值|购买|订阅|cost.*\$[0-9]+)"; then
        echo "BLOCK" "P0" "涉及金钱交易，必须 Daryl 手动确认"; return 0
    fi
    # 生产环境
    if echo "$desc" | grep -qiE "(production|生产环境|prod\b)"; then
        echo "BLOCK" "P0" "涉及生产环境操作，必须确认"; return 0
    fi
    # 不可逆删除
    if echo "$desc" | grep -qiE "(删除所有|rm -rf|drop\s+table|销毁|清空数据库)"; then
        echo "BLOCK" "P0" "涉及不可逆删除操作，必须确认"; return 0
    fi
    # 敏感信息
    if echo "$desc" | grep -qiE "(密码|token|secret|api.?key|私钥|泄露)"; then
        echo "BLOCK" "P0" "涉及敏感信息操作，必须确认"; return 0
    fi
    # 发布操作
    if echo "$desc" | grep -qiE "(npm\s+publish|发布到.*npm|docker\s+push)"; then
        echo "BLOCK" "P0" "涉及公开发布操作，必须确认"; return 0
    fi
    # Git force push to main
    if echo "$desc" | grep -qiE "(git.*push.*(main|master).*force|force.*push.*(main|master))"; then
        echo "BLOCK" "P0" "force push 到主分支，必须确认"; return 0
    fi
    # 修改环境/密钥配置
    if echo "$desc" | grep -qiE "(修改.*\.env|修改.*api.?key|修改.*secrets|修改.*token)"; then
        echo "BLOCK" "P0" "修改环境变量/密钥配置，必须确认"; return 0
    fi
    return 1
}

# ─── P1 需要确认 ────────────────────────────────────
check_p1_confirm() {
    local desc="$1"
    # 架构/方案
    if echo "$desc" | grep -qiE "(架构|重构|方案|选型|技术栈|框架选择)"; then
        echo "CONFIRM" "P1" "架构方向决策，建议提供 2-3 方案后请示 Daryl"; return 0
    fi
    # 公共接口变更
    if echo "$desc" | grep -qiE "(修改.*接口|修改.*API|修改.*签名|修改.*export|公共接口|类型定义.*修改)"; then
        echo "CONFIRM" "P1" "涉及公共接口/类型签名变更，需确认兼容性"; return 0
    fi
    # 新增依赖
    if echo "$desc" | grep -qiE "(新增.*依赖|添加.*依赖|install.*新包|npm\s+install.*\-\-save|pip\s+install)"; then
        echo "CONFIRM" "P1" "新增依赖包，需确认供应链风险"; return 0
    fi
    # 数据结构/schema 变更
    if echo "$desc" | grep -qiE "(修改.*schema|修改.*表结构|修改.*数据结构|migration|数据库.*变更)"; then
        echo "CONFIRM" "P1" "数据结构/schema 变更，需确认兼容性"; return 0
    fi
    # 跨 agent
    if echo "$desc" | grep -qiE "(跨.?agent|多.?agent)"; then
        echo "CONFIRM" "P1" "跨 agent 操作，确认对方已就绪"; return 0
    fi
    # 外部 API (非只读)
    if echo "$desc" | grep -qiE "(调用.*API|webhook|发送.*请求|POST.*api)"; then
        echo "CONFIRM" "P1" "外部 API 调用（非只读），需确认"; return 0
    fi
    # Git push 到非 main 分支
    if echo "$desc" | grep -qiE "(git\s+push.*(?!main|master))" && ! echo "$desc" | grep -qiE "(main|master)"; then
        echo "CONFIRM" "P1" "Git push 到非主分支，需告知"; return 0
    fi
    return 1
}

# ─── P2 自主决策 ────────────────────────────────────
check_p2_pass() {
    local desc="$1"
    # 标准开发
    if echo "$desc" | grep -qiE "(修改|修复|实现|开发|添加|优化|重构小|调试|测试)"; then
        echo "PASS" "P2" "标准开发操作，可自主决策"; return 0
    fi
    # sessions_send
    if echo "$desc" | grep -qiE "(sessions_send|发送消息|转发消息)"; then
        echo "PASS" "P2" "Agent 间消息通信"; return 0
    fi
    # 文档/配置
    if echo "$desc" | grep -qiE "(文档|readme|配置|注释|格式化|lint)"; then
        echo "PASS" "P2" "文档/配置类操作，可自主进行"; return 0
    fi
    # 搜索/查询
    if echo "$desc" | grep -qiE "(搜索|查找|查询|检索|读取|查看|列出)"; then
        echo "PASS" "P2" "只读操作，可自主进行"; return 0
    fi
    # 删除代码块 (P2, 回滚兜底)
    if echo "$desc" | grep -qiE "(删除.*函数|删除.*代码|删除.*文件|移除.*模块)"; then
        echo "PASS" "P2" "删除操作（回滚机制兜底）"; return 0
    fi
    return 1
}

# ─── P3 直接执行 ────────────────────────────────────
check_p3_pass() {
    local desc="$1"
    if echo "$desc" | grep -qiE "(格式|风格|命名|空格|缩进|import.*排序|代码风格|日志|log)"; then
        echo "PASS" "P3" "代码风格/日志类，直接执行不等待"; return 0
    fi
    return 1
}

# ─── 执行判定链 ──────────────────────────────────────
echo "🔒 Sentinel L2 操作前合规判断"
echo "  操作: $OP_DESC"
echo "  文件: $FILES"
echo "  范围: $SCOPE"
echo ""

RESULT=""
DECISION="PASS"; LEVEL="P2"; REASON="未匹配到特定规则，按 P2 处理（可自主决策）"

if RESULT=$(check_p0_block "$OP_DESC") && [ $? -eq 0 ]; then
    read DECISION LEVEL REASON <<< "$RESULT"
elif RESULT=$(check_p1_confirm "$OP_DESC") && [ $? -eq 0 ]; then
    read DECISION LEVEL REASON <<< "$RESULT"
elif RESULT=$(check_p2_pass "$OP_DESC") && [ $? -eq 0 ]; then
    read DECISION LEVEL REASON <<< "$RESULT"
elif RESULT=$(check_p3_pass "$OP_DESC") && [ $? -eq 0 ]; then
    read DECISION LEVEL REASON <<< "$RESULT"
fi

cat << EOF
{
  "timestamp": "$TIMESTAMP",
  "decision": "$DECISION",
  "level": "$LEVEL",
  "description": "$OP_DESC",
  "reason": "$REASON",
  "files": "$FILES",
  "scope": "$SCOPE"
}
EOF

echo ""
echo "→ 判定: [$LEVEL] $DECISION — $REASON"

case "$DECISION" in
    BLOCK) exit 2 ;;
    CONFIRM) exit 1 ;;
    PASS) exit 0 ;;
esac
