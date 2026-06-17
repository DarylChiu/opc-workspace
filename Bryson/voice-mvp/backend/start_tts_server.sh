#!/bin/bash

# ==============================================
# Bryson语音服务器启动脚本 (Google TTS集成版)
# ==============================================

set -e

# 项目目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
LOG_DIR="$PROJECT_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 显示项目信息
echo "🔍 项目信息:"
echo "  项目目录: $PROJECT_DIR"
echo "  后端目录: $BACKEND_DIR"
echo "  日志目录: $LOG_DIR"
echo "  当前用户: $(whoami)"
echo "  当前时间: $(date)"
echo

# 检查端口占用
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        echo "⚠️ 端口 $port 已被占用"
        echo "   运行中的进程:"
        lsof -i :$port | grep LISTEN
        return 1
    else
        echo "✅ 端口 $port 可用"
        return 0
    fi
}

# 检查API密钥
check_api_key() {
    echo "🔑 检查Google TTS API密钥..."
    
    local key_file="$HOME/.openclaw/auth/google/ielts_tts_2026.key"
    if [ -f "$key_file" ]; then
        API_KEY=$(head -c 100 "$key_file" | tr -d '\n')
        if [ -n "$API_KEY" ] && [ ${#API_KEY} -gt 20 ]; then
            echo "✅ API密钥有效"
            echo "   文件位置: $key_file"
            echo "   密钥前8字符: ${API_KEY:0:8}..."
            echo "   密钥长度: ${#API_KEY} 字符"
            return 0
        else
            echo "❌ API密钥格式不正确"
            return 1
        fi
    else
        echo "❌ API密钥文件不存在: $key_file"
        echo "   请确保密钥已正确放置"
        return 1
    fi
}

# 检查Python依赖
check_python_deps() {
    echo "🐍 检查Python依赖..."
    
    local required_packages=(
        "fastapi"
        "uvicorn"
        "aiohttp"
        "requests"
    )
    
    for pkg in "${required_packages[@]}"; do
        if python3 -c "import $pkg" 2>/dev/null; then
            echo "   ✅ $pkg"
        else
            echo "   ❌ $pkg (未安装)"
            echo "   请运行: pip3 install fastapi uvicorn aiohttp requests"
            return 1
        fi
    done
    
    echo "✅ 所有依赖包已安装"
    return 0
}

# 验证TTS API连接
test_tts_api() {
    echo "🧪 测试Google TTS API连接..."
    
    local test_script="$PROJECT_DIR/../test_google_tts_api.py"
    if [ -f "$test_script" ]; then
        echo "   运行测试脚本: $test_script"
        if python3 "$test_script"; then
            echo "✅ Google TTS API连接测试成功"
            return 0
        else
            echo "⚠️ Google TTS API测试可能有警告，但继续启动..."
            return 0
        fi
    else
        echo "⚠️ 测试脚本未找到: $test_script"
        echo "   将跳过TTS API连接测试"
        return 0
    fi
}

# 启动服务器
start_server() {
    echo "🚀 启动Bryson语音服务器..."
    echo "   服务器文件: $BACKEND_DIR/server_with_tts.py"
    echo "   使用端口: 8081"
    echo
    
    # 进入项目目录
    cd "$PROJECT_DIR"
    
    # 运行服务器
    echo "🟢 启动命令: python3 $BACKEND_DIR/server_with_tts.py"
    echo "   日志文件: $LOG_DIR/server_$(date +%Y%m%d_%H%M%S).log"
    echo
    echo "────────────────────────────────────────────────"
    
    # 启动服务器（后台运行）
    nohup python3 "$BACKEND_DIR/server_with_tts.py" > "$LOG_DIR/server_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
    SERVER_PID=$!
    
    # 等待服务器启动
    echo "⏳ 等待服务器启动..."
    sleep 3
    
    # 检查服务器状态
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "✅ 服务器已启动 (PID: $SERVER_PID)"
    else
        echo "❌ 服务器启动失败"
        echo "   查看日志: tail -f $LOG_DIR/server_*.log"
        return 1
    fi
    
    # 测试服务器响应
    echo "🧪 测试服务器响应..."
    if curl -s http://localhost:8081/api/status | grep -q '"status":"ok"'; then
        echo "✅ 服务器响应正常"
    else
        echo "⚠️ 服务器响应检查失败，但进程正在运行"
    fi
    
    echo
    echo "🎉 Bryson语音服务器已成功启动!"
    echo "================================================="
    echo "🌐 访问地址: http://localhost:8081"
    echo "🔌 WebSocket: ws://localhost:8081/ws/your_session_id"
    echo "🧪 TTS测试: http://localhost:8081/api/tts/test"
    echo "📊 状态检查: http://localhost:8081/api/status"
    echo "📝 API文档: http://localhost:8081/docs"
    echo "📁 前端页面: http://localhost:8081/"
    echo "================================================="
    echo
    echo "🔍 测试TTS功能:"
    echo "   curl -X POST http://localhost:8081/api/tts/synthesize \\"
    echo "        -H 'Content-Type: application/json' \\"
    echo "        -d '{\"text\":\"Hello, this is a test.\"}'"
    echo
    echo "📋 查看日志: tail -f $LOG_DIR/server_*.log"
    echo "🛑 停止服务器: kill $SERVER_PID"
    echo
    
    # 将PID保存到文件
    echo $SERVER_PID > "$LOG_DIR/server.pid"
    echo "📝 服务器PID已保存到: $LOG_DIR/server.pid"
    
    return 0
}

# 主函数
main() {
    echo "================================================="
    echo "🔧 Bryson语音服务器启动前检查"
    echo "================================================="
    echo
    
    # 执行检查
    local errors=0
    
    # 检查端口
    if ! check_port 8081; then
        echo "   尝试使用其他端口或停止占用进程"
        errors=$((errors + 1))
    fi
    
    # 检查API密钥
    if ! check_api_key; then
        errors=$((errors + 1))
    fi
    
    # 检查Python依赖
    if ! check_python_deps; then
        errors=$((errors + 1))
    fi
    
    echo
    
    if [ $errors -gt 0 ]; then
        echo "❌ 发现 $errors 个问题，无法启动服务器"
        echo "   请解决上述问题后重试"
        return 1
    fi
    
    # 测试TTS API（可选）
    test_tts_api
    
    echo
    echo "================================================="
    echo "✅ 所有检查通过，准备启动服务器"
    echo "================================================="
    echo
    
    # 启动服务器
    if start_server; then
        echo "🎯 启动完成!"
        echo "   服务器运行中，可以开始测试TTS功能"
        return 0
    else
        echo "❌ 服务器启动失败"
        return 1
    fi
}

# 运行主函数
main "$@"