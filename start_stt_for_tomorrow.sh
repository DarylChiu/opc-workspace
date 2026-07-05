#!/bin/bash
# STT完整演示启动脚本 - 明天早上执行

set -e

echo "========================================="
echo "Bryson IELTS STT完整演示启动脚本"
echo "========================================="
echo "启动时间: $(date)"
echo ""

# 检查Python环境
echo "🔍 检查环境..."
python3 --version || { echo "❌ Python3未安装"; exit 1; }

# 检查依赖
echo "📦 检查Python依赖..."
pip3 list | grep -E "fastapi|uvicorn|requests" || { 
    echo "⚠️  缺少依赖，正在安装..."
    pip3 install fastapi uvicorn requests
}

# 备份旧日志
echo "📄 清理旧日志..."
if [ -f stt_demo.log ]; then
    mv stt_demo.log "stt_demo_$(date +%Y%m%d_%H%M).log"
fi
if [ -f stt_ngrok.log ]; then
    mv stt_ngrok.log "stt_ngrok_$(date +%Y%m%d_%H%M).log"
fi

# 关闭可能存在的旧进程
echo "🔄 清理旧进程..."
pkill -f "stt_final_demo.py" 2>/dev/null || true
pkill -f "ngrok http 8096" 2>/dev/null || true
sleep 2

# 启动STT服务器
echo "🚀 启动STT服务器..."
nohup python3 stt_final_demo.py > stt_demo.log 2>&1 &
SERVER_PID=$!
echo "📌 服务器PID: $SERVER_PID"

# 等待服务器启动
echo "⏳ 等待服务器启动..."
sleep 5

# 检查服务器状态
echo "🔍 检查服务器状态..."
if curl -s http://localhost:8096/api/health > /dev/null; then
    echo "✅ 服务器启动成功"
else
    echo "❌ 服务器启动失败，查看日志:"
    tail -20 stt_demo.log
    exit 1
fi

# 启动ngrok
echo "🌐 启动ngrok隧道..."
nohup ngrok http 8096 --log stt_ngrok.log > /dev/null 2>&1 &
NGROK_PID=$!
echo "📌 ngrok PID: $NGROK_PID"

# 等待ngrok启动
echo "⏳ 等待ngrok启动..."
sleep 8

# 获取ngrok公网URL
echo "🔗 获取公网链接..."
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
for tunnel in data['tunnels']:
    if tunnel['proto'] == 'https':
        print(tunnel['public_url'])
        break
" 2>/dev/null || echo "")

if [ -n "$NGROK_URL" ]; then
    echo "🎯 公网链接: $NGROK_URL"
    echo "📋 可访问链接:"
    echo "   主界面: $NGROK_URL"
    echo "   健康检查: $NGROK_URL/api/health"
    echo "   测试端点: $NGROK_URL/api/test-audio"
    
    # 保存到文件供早上查看
    echo "公网链接: $NGROK_URL" > stt_public_url.txt
    echo "启动时间: $(date)" >> stt_public_url.txt
    echo "服务器PID: $SERVER_PID" >> stt_public_url.txt
    echo "ngrok PID: $NGROK_PID" >> stt_public_url.txt
else
    echo "⚠️  无法获取ngrok链接，查看日志:"
    tail -20 stt_ngrok.log 2>/dev/null || echo "无ngrok日志"
fi

echo ""
echo "========================================="
echo "✅ 启动完成！"
echo ""
echo "📝 操作指南:"
echo "   1. 访问上面的公网链接进行测试"
echo "   2. 点击'开始录音'按钮测试录音功能"
echo "   3. 可以上传音频文件测试"
echo "   4. 页面会显示转录结果和置信度"
echo ""
echo "🛑 停止服务命令:"
echo "   pkill -f 'stt_final_demo.py'"
echo "   pkill -f 'ngrok http 8096'"
echo ""
echo "📊 查看日志:"
echo "   tail -f stt_demo.log"
echo "   tail -f stt_ngrok.log"
echo "========================================="