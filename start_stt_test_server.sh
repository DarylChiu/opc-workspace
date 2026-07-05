#!/bin/bash

# Google STT测试服务器启动脚本

echo "🚀 启动 Google STT 测试服务器"
echo "="*50

# 检查Python依赖
echo "🔍 检查Python依赖..."
python3 -c "
import importlib, sys
requirements = ['fastapi', 'uvicorn', 'aiohttp', 'requests', 'pydantic']
for req in requirements:
    try:
        importlib.import_module(req.replace('-', '_'))
        print(f'✅ {req}')
    except ImportError:
        print(f'❌ {req} (可能需要安装)')
        sys.exit(1)
"

echo "="*50

# 检查端口占用
echo "🔌 检查端口 8084..."
PID=$(lsof -ti:8084 2>/dev/null || echo "")
if [ ! -z "$PID" ]; then
    echo "🔄 端口 8084 被占用 (PID: $PID)，正在停止..."
    kill -9 $PID 2>/dev/null
    sleep 1
fi

# 检查必要文件
echo "📁 检查必要文件..."
HTML_FILE="google_stt_test_interface.html"
PYTHON_FILE="stt_test_server.py"
IELTS_DIR="test_audio/ielts_benchmark"

if [ -f "$HTML_FILE" ]; then
    echo "✅ HTML界面文件: $HTML_FILE (存在)"
else
    echo "❌ 缺少HTML界面文件: $HTML_FILE"
fi

if [ -f "$PYTHON_FILE" ]; then
    echo "✅ Python服务器文件: $PYTHON_FILE (存在)"
else
    echo "❌ 缺少Python服务器文件: $PYTHON_FILE"
    exit 1
fi

if [ -d "$IELTS_DIR" ]; then
    echo "✅ IELTS音频数据目录: $IELTS_DIR (存在)"
else
    echo "⚠️  警告: IELTS音频数据目录不存在，但服务器仍可启动"
    mkdir -p "$IELTS_DIR" 2>/dev/null || true
fi

echo "="*50

# 启动服务器
echo "📡 启动服务器..."
echo "🔗 访问地址: http://localhost:8084"
echo "🎮 STT测试界面: http://localhost:8084/"
echo "📊 API状态: http://localhost:8084/api/status"
echo "="*50

# 显示API帮助
cat << 'HELP'
📖 快速API参考:

1. STT转录音频:
   POST /api/stt/transcribe
   {
     "audio_content": "base64编码的音频",
     "api_key": "AIzaSy...",
     "language_code": "en-US"
   }

2. 测试直接调用:
   POST /api/stt/test-direct
   {
     "api_key": "AIzaSy..."
   }

3. 获取IELTS样本:
   GET /api/ielts/samples?level=beginner&limit=5

4. 上传音频文件:
   POST /api/stt/upload (form-data, file字段)

5. 获取统计信息:
   GET /api/stats
HELP

echo "="*50
echo "🖥️  服务器日志如下:"
echo "="*50

# 启动服务器
python3 stt_test_server.py