#!/bin/bash
# OPC看板小任务上报助手
# 用法:
#   bash scripts/report_tasks.sh "任务1,任务2,任务3" "in_progress,pending,done"
#   或直接编辑脚本中的任务列表

OPC_API="http://localhost:8765/api/report"
AGENT="xiaofeng"

report_tasks() {
    # 从参数构建任务JSON
    IFS=',' read -ra TITLES <<< "$1"
    IFS=',' read -ra STATUSES <<< "$2"
    
    local tasks_json=""
    for i in "${!TITLES[@]}"; do
        local title="${TITLES[$i]}"
        local status="${STATUSES[$i]:-in_progress}"
        tasks_json+="{\"title\":\"$title\",\"status\":\"$status\"},"
    done
    tasks_json="[${tasks_json%,}]"
    
    curl -s -X POST "$OPC_API" \
        -H 'Content-Type: application/json' \
        -d "{\"agent\":\"$AGENT\",\"type\":\"tasks\",\"data\":{\"tasks\":$tasks_json}}"
}

# 默认: 如果无参数，使用硬编码的当前任务
if [ $# -eq 0 ]; then
    # === 编辑这里更新当前任务 ===
    curl -s -X POST "$OPC_API" \
        -H 'Content-Type: application/json' \
        -d '{
            "agent": "xiaofeng",
            "type": "tasks",
            "data": {
                "tasks": [
                    {"title": "管线2 Qwen-Omni streaming", "status": "in_progress"},
                    {"title": "等待模型开通(百炼控制台)", "status": "blocked"},
                    {"title": "管线2端到端测试", "status": "pending"}
                ]
            }
        }'
else
    report_tasks "$1" "$2"
fi
