#!/bin/bash
# Bryson语音MVP - 2小时进度报告定时任务

# 配置
PROJECT_DIR="/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/bryson_voice_mvp"
LOG_DIR="${PROJECT_DIR}/logs"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
PYTHON_PATH="/usr/local/bin/python3"

# 创建日志目录
mkdir -p "${LOG_DIR}"

# 进入项目目录
cd "${PROJECT_DIR}" || {
    echo "❌ 无法进入项目目录: ${PROJECT_DIR}"
    exit 1
}

# 执行报告生成
echo "🕓 [$(date '+%Y-%m-%d %H:%M:%S')] 开始生成2小时进度报告..." >> "${LOG_DIR}/cron_${TIMESTAMP}.log"

# 运行Python报告脚本
"${PYTHON_PATH}" progress_report.py >> "${LOG_DIR}/cron_${TIMESTAMP}.log" 2>&1
PYTHON_EXIT=$?

# 检查执行结果
if [ $PYTHON_EXIT -eq 0 ]; then
    echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] 报告生成成功" >> "${LOG_DIR}/cron_${TIMESTAMP}.log"
    
    # 生成发送到飞书的报告（简化版）
    REPORT_JSON="${PROJECT_DIR}/reports/progress_report_$(date '+%Y%m%d_%H%M').json"
    if [ -f "$REPORT_JSON" ]; then
        echo "📧 报告文件: $REPORT_JSON" >> "${LOG_DIR}/cron_${TIMESTAMP}.log"
        
        # 这里可以添加发送到飞书的逻辑
        # 目前先输出报告内容到日志
        "${PYTHON_PATH}" -c "import json, sys; data=json.load(open('$REPORT_JSON')); print(f'总体进度: {data[\"progress\"][\"overall_percent\"]}%')" >> "${LOG_DIR}/cron_${TIMESTAMP}.log"
    fi
else
    echo "❌ [$(date '+%Y-%m-%d %H:%M:%S')] 报告生成失败 (退出码: $PYTHON_EXIT)" >> "${LOG_DIR}/cron_${TIMESTAMP}.log"
    echo "=== 错误详情 ===" >> "${LOG_DIR}/cron_${TIMESTAMP}.log"
    tail -20 "${LOG_DIR}/cron_${TIMESTAMP}.log" >> "${LOG_DIR}/cron_${TIMESTAMP}.log"
fi

echo "🔄 [$(date '+%Y-%m-%d %H:%M:%S')] 下次报告时间: $(date -v+2H '+%H:%M')" >> "${LOG_DIR}/cron_${TIMESTAMP}.log"

# 清理旧日志（保留最近7天）
find "${LOG_DIR}" -name "cron_*.log" -mtime +7 -delete
find "${PROJECT_DIR}/reports" -name "*.json" -mtime +3 -delete 2>/dev/null || true

exit 0