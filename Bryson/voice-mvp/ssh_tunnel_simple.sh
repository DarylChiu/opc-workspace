#!/bin/bash

echo "🚀 Bryson语音MVP - SSH隧道启动 (方案2)"
echo "========================================="

# 检查SSH
if ! command -v ssh > /dev/null 2>&1; then
  echo "❌ SSH未安装，请先安装OpenSSH"
  exit 1
fi

# 检查服务器
echo "检查服务器状态..."
if curl -s http://localhost:8080/api/status > /dev/null 2>&1; then
  echo "✅ 服务器运行正常"
else
  echo "❌ 服务器未运行"
  echo "请先启动服务器:"
  echo "cd ~/.openclaw/xiaofeng_workspace/bryson_voice_mvp"
  echo "python3 backend/simple_server.py"
  exit 1
fi

echo ""
echo "选择SSH隧道服务:"
echo "1. localhost.run (推荐使用)"
echo "2. Serveo (备选)"
echo "3. 查看帮助信息"
echo "4. 退出"
echo ""

read -p "请输入选项 [1-4]: " choice

case $choice in
  1)
    echo "🔗 连接到 localhost.run..."
    echo "正在建立SSH隧道，请耐心等待..."
    echo "成功后会显示类似: https://yourname.localhost.run"
    echo "在手机浏览器中打开此链接即可测试"
    echo ""
    echo "按Ctrl+C停止隧道"
    ssh -v -R 80:localhost:8080 ssh.localhost.run
    ;;
  2)
    echo "🔗 连接到 Serveo..."
    echo "正在建立SSH隧道，请耐心等待..."
    echo "成功后会显示链接地址"
    echo ""
    echo "按Ctrl+C停止隧道"
    ssh -v -R bryson:80:localhost:8080 serveo.net
    ;;
  3)
    echo "📚 帮助信息:"
    echo "----------"
    echo "localhost.run 和 Serveo 都是免费的SSH隧道服务"
    echo ""
    echo "测试步骤:"
    echo "1. 选择选项1或2建立隧道"
    echo "2. 复制生成的链接 (如: https://xxx.localhost.run)"
    echo "3. 在手机浏览器中打开链接"
    echo "4. 授权麦克风权限"
    echo "5. 开始语音测试"
    echo ""
    echo "如果连接失败，请检查:"
    echo "1. 网络连接是否正常"
    echo "2. 防火墙是否允许SSH连接"
    echo "3. 服务器是否在端口8080运行"
    ;;
  4)
    echo "👋 退出"
    exit 0
    ;;
  *)
    echo "❌ 无效选项"
    exit 1
    ;;
esac