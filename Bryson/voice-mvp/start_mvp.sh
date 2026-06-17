#!/bin/bash
# Bryson语音MVP启动脚本

echo "================================================="
echo "🎤 Bryson语音MVP - 方案B (飞书+Web实时桥接)"
echo "================================================="

# 检查Python环境
echo "🔍 检查Python环境..."
python3 --version || { echo "❌ Python3未安装"; exit 1; }

# 检查依赖
echo "📦 检查Python依赖..."
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "🔄 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

echo "📦 安装依赖包..."
pip install -r requirements.txt

# 创建静态文件目录
echo "📁 准备静态文件..."
mkdir -p static
cp -r frontend/* static/ 2>/dev/null || true

# 启动后端服务器
echo "🚀 启动后端服务器..."
echo "----------------------------------------"
echo "访问地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "----------------------------------------"
echo "按 Ctrl+C 停止服务器"
echo ""

cd backend
uvicorn server:app --host 0.0.0.0 --port 8000 --reload