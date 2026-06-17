#!/bin/bash
# L2: 操作前合规判断 — P0-P3 决策前置
# 用法: bash scripts/compliance/pre-op.sh "<操作描述>" "[涉及文件]" "[影响范围]"
# 
# 输入参数:
#   $1 - 操作描述（必填）
#   $2 - 涉及文件路径，逗号分隔（可选）
#   $3 - 影响范围: local/project/external（可选，默认 local）
#
# 输出: JSON 格式的判断结果
#   { "decision": "PASS|BLOCK|CONFIRM", "level": "P0|P1|P2|P3", "reason": "...", "action": "..." }

OP_DESC="${1:-未指定操作}"
FILES="${2:-无}"
SCOPE="${3:-local}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 危险模式检测——P0 自动 BLOCK
check_p0_danger() {
    local desc="$1"
    # 金额相关
    if echo "$desc" | grep -qiE "(付款|扣款|转账|充值|购买|订阅|cost.*\$[0-9]+)"; then
        echo "BLOCK" "P0" "涉及金钱交易，必须 Daryl 手动确认"
        return 0
    fi
    # 生产环境
    if echo "$desc" | grep -qiE "(production|生产环境|prod\b)"; then
        echo "BLOCK" "P0" "涉及生产环境操作，必须确认"
        return 0
    fi
    # 删除/销毁
    if echo "$desc" | grep -qiE "(删除所有|rm -rf|drop\s+table|销毁|清空数据库)"; then
        echo "BLOCK" "P0" "涉及不可逆删除操作，必须确认"
        return 0
    fi
    # 敏感信息
    if echo "$desc" | grep -qiE "(密码|token|secret|api.?key|私钥|泄露)"; then
        echo "BLOCK" "P0" "涉及敏感信息操作，必须确认"
        return 0
    fi
    return 1
}

# P1 重要决策——需要 CONFIRM
check_p1_confirm() {
    local desc="$1"
    # 架构方向
    if echo "$desc" | grep -qiE "(架构|重构|方案|选型|技术栈|框架选择)"; then
        echo "CONFIRM" "P1" "架构方向决策，建议提供 2-3 方案后请示 Daryl"
        return 0
    fi
    # 大范围修改
    if echo "$desc" | grep -qiE "(全部|所有|整个项目|批量|一键)"; then
        echo "CONFIRM" "P1" "大范围修改操作，建议先确认范围"
        return 0
    fi
    # 跨 agent 操作
    if echo "$desc" | grep -qiE "(跨.?agent|多.?agent|sessions_send)"; then
        echo "CONFIRM" "P1" "跨 agent 操作，确认对方已就绪"
        return 0
    fi
    return 1
}

# P2 正常——自主决策 PASS
check_p2_pass() {
    local desc="$1"
    # 代码修改
    if echo "$desc" | grep -qiE "(修改|修复|实现|开发|添加|删除单个|优化|重构小)"; then
        # 检查文件范围
        if [ "$SCOPE" = "local" ] && [ "$FILES" != "无" ]; then
            local file_count=$(echo "$FILES" | tr ',' '\n' | wc -l | tr -d ' ')
            if [ "$file_count" -gt 5 ]; then
                echo "CONFIRM" "P2" "涉及 $file_count 个文件，建议分批处理"
                return 0
            fi
        fi
        echo "PASS" "P2" "标准开发操作，可自主决策"
        return 0
    fi
    # 文档/配置
    if echo "$desc" | grep -qiE "(文档|readme|配置|注释|格式化|lint)"; then
        echo "PASS" "P2" "文档/配置类操作，可自主进行"
        return 0
    fi
    # 搜索/查询
    if echo "$desc" | grep -qiE "(搜索|查找|查询|检索|读取|查看|列出)"; then
        echo "PASS" "P2" "只读操作，可自主进行"
        return 0
    fi
    return 1
}

# P3 参考——不等待直接做 PASS
check_p3_pass() {
    local desc="$1"
    if echo "$desc" | grep -qiE "(格式|风格|命名|空格|缩进|import.*排序|代码风格)"; then
        echo "PASS" "P3" "代码风格类，直接执行不等待"
        return 0
    fi
    return 1
}

# 执行判断链
echo "🔒 L2 操作前合规判断"
echo "  操作: $OP_DESC"
echo "  文件: $FILES"
echo "  范围: $SCOPE"
echo ""

# P0 优先
RESULT=$(check_p0_danger "$OP_DESC")
if [ $? -eq 0 ]; then
    read DECISION LEVEL REASON <<< "$RESULT"
elif RESULT=$(check_p1_confirm "$OP_DESC") && [ $? -eq 0 ]; then
    read DECISION LEVEL REASON <<< "$RESULT"
elif RESULT=$(check_p2_pass "$OP_DESC") && [ $? -eq 0 ]; then
    read DECISION LEVEL REASON <<< "$RESULT"
elif RESULT=$(check_p3_pass "$OP_DESC") && [ $? -eq 0 ]; then
    read DECISION LEVEL REASON <<< "$RESULT"
else
    DECISION="PASS"
    LEVEL="P2"
    REASON="未匹配到特定规则，按 P2 处理（可自主决策，超时6h按最佳理解执行）"
fi

# 输出 JSON 结果
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

# 返回码：BLOCK=2, CONFIRM=1, PASS=0
case "$DECISION" in
    BLOCK) exit 2 ;;
    CONFIRM) exit 1 ;;
    PASS) exit 0 ;;
esac
