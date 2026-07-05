#!/bin/bash
# Deepseek成本跟踪系统启动脚本

set -e

echo "🚀 启动Deepseek成本跟踪系统"
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3"
    exit 1
fi

# 检查依赖
echo "📦 检查Python依赖..."
python3 -c "import sqlite3, aiohttp" 2>/dev/null && echo "✅ 依赖检测通过" || {
    echo "⚠️  缺少依赖，尝试安装..."
    pip3 install aiohttp
}

# 进入工作目录
cd /Users/zhaoyuzhao/.openclaw/xiaofeng_workspace

# 检查主脚本
if [ ! -f "deepseek_cost_tracker.py" ]; then
    echo "❌ 错误: 未找到 deepseek_cost_tracker.py"
    exit 1
fi

# 模式选择
MODE=${1:-service}

case $MODE in
    service)
        echo "🔧 启动服务模式..."
        if [ -f "deepseek_tracker_service.py" ]; then
            python3 deepseek_tracker_service.py
        else
            echo "⚠️  服务脚本未找到，启动单一报告模式"
            python3 deepseek_cost_tracker.py --action report
        fi
        ;;
    
    report)
        echo "📊 生成成本报告..."
        python3 deepseek_cost_tracker.py --action report
        ;;
    
    summary)
        echo "📈 显示成本摘要..."
        python3 deepseek_cost_tracker.py --action summary
        ;;
    
    test)
        echo "🧪 运行集成测试..."
        if [ -f "test_deepseek_integration.py" ]; then
            python3 test_deepseek_integration.py
        else
            echo "⚠️  测试脚本未找到"
            python3 deepseek_cost_tracker.py --action test
        fi
        ;;
    
    alerts)
        echo "🔔 检查成本警报..."
        python3 deepseek_cost_tracker.py --action alerts
        ;;
    
    monitor)
        echo "👁️  启动监控模式..."
        echo "按 Ctrl+C 停止监控"
        while true; do
            clear
            echo "=== Deepseek成本实时监控 ==="
            echo "更新时间: $(date '+%H:%M:%S')"
            echo "---------------------------"
            python3 deepseek_cost_tracker.py --action summary
            sleep 60  # 每分钟更新一次
        done
        ;;
    
    *)
        echo "使用方法: $0 {service|report|summary|test|alerts|monitor}"
        echo ""
        echo "模式说明:"
        echo "  service   长期运行的服务模式"
        echo "  report    生成完整成本报告"
        echo "  summary   显示简要成本摘要"
        echo "  test      运行集成测试"
        echo "  alerts    检查成本警报"
        echo "  monitor   实时监控模式"
        exit 1
        ;;
esac

echo ""
echo "✅ 操作完成"
