#!/bin/bash
# 启动简单的STT测试服务器

# 检查端口8087是否被占用
if lsof -i :8087 >/dev/null 2>&1; then
    echo "端口8087被占用，使用8089端口"
    PORT=8089
else
    PORT=8087
fi

echo "🌐 启动HTTP服务器在端口 $PORT"
echo "📁 提供当前目录的静态文件"
echo "📄 访问: http://localhost:$PORT/google_stt_test_interface.html"

# 启动Python HTTP服务器
python3 -m http.server $PORT