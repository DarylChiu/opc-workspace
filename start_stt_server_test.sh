#!/bin/bash
# 启动STT测试服务器（无需API密钥版本）

echo "🚀 启动Google STT测试服务器 (内置密钥版)"
echo "=========================================="

# 检查端口占用
if lsof -i :8090 >/dev/null 2>&1; then
    echo "⚠️  端口8090已被占用，请先停止相关进程"
    echo "   运行命令：lsof -ti:8090 | xargs kill -9"
    exit 1
fi

# 检查Python依赖
echo "🔧 检查Python依赖..."
python3 -c "import fastapi, uvicorn, aiohttp, requests, pydantic" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 所有依赖已安装"
else
    echo "❌ 缺少Python依赖"
    echo "   请运行: pip install fastapi uvicorn aiohttp requests pydantic"
    exit 1
fi

# 检查音频样本
echo "📚 检查IELTS音频样本..."
if [ -d "test_audio/ielts_benchmark" ]; then
    sample_count=$(find "test_audio/ielts_benchmark" -name "*.mp3" -o -name "*.wav" | wc -l)
    echo "✅ 找到 $sample_count 个IELTS音频样本"
else
    echo "⚠️  IELTS音频样本目录不存在，将使用模拟模式"
fi

# 启动服务器
echo "🌐 启动服务器..."
echo "=========================================="
echo "访问地址: http://localhost:8090"
echo "API状态: http://localhost:8090/api/status"
echo "测试界面: http://localhost:8090/"
echo "=========================================="
echo ""
echo "📢 重要: API密钥已内置！用户无需提供任何密钥。"
echo "=========================================="

python3 STT_QUICK_FIX.py