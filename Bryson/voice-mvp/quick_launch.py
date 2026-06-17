#!/usr/bin/env python3
"""
Bryson语音MVP - 快速启动脚本（外部访问版）
专为明天的30分钟测试优化
"""

import os
import sys
import time
import socket
import asyncio
import subprocess
import threading
from datetime import datetime
import webbrowser

def check_dependencies():
    """检查依赖是否已安装"""
    print("🔍 检查依赖...")
    
    dependencies = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("websockets", "websockets"),
        ("pyngrok", "pyngrok")
    ]
    
    missing = []
    for name, module in dependencies:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} (未安装)")
            missing.append(module)
    
    if missing:
        print(f"\n📦 安装缺失依赖...")
        for module in missing:
            subprocess.run([sys.executable, "-m", "pip", "install", module], check=False)
    
    return True

def check_port_available(port):
    """检查端口是否可用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return True
        except socket.error:
            return False

def get_server_script():
    """获取快速服务器脚本"""
    return '''
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bryson Voice MVP", version="0.1.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(current_dir, "frontend")

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
        
    @app.get("/{path:path}")
    async def serve_static(path):
        full_path = os.path.join(frontend_dir, path)
        if os.path.exists(full_path):
            return FileResponse(full_path)
        return FileResponse(os.path.join(frontend_dir, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Bryson Voice MVP", "status": "ready"}

# 基础API
@app.get("/api/status")
async def status():
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0-test",
        "features": ["static_ui", "mobile_compatible", "webrtc_ready"]
    }

if __name__ == "__main__":
    print("🚀 启动Bryson语音MVP测试服务器...")
    print(f"访问地址: http://localhost:8080")
    print("按 Ctrl+C 停止服务器")
    uvicorn.run(app, host="0.0.0.0", port=8080, access_log=True)
'''

def get_mobile_test_html():
    """获取移动端测试HTML"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Bryson语音MVP - 移动端测试</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .logo {
            font-size: 40px;
            margin-bottom: 10px;
        }
        
        h1 {
            color: #333;
            font-size: 24px;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 16px;
            line-height: 1.5;
        }
        
        .status-card {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 5px solid #4CAF50;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        
        .status-item:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        
        .status-label {
            color: #666;
            font-weight: 500;
        }
        
        .status-value {
            color: #333;
            font-weight: bold;
        }
        
        .status-good {
            color: #4CAF50 !important;
        }
        
        .status-warning {
            color: #FF9800 !important;
        }
        
        .test-buttons {
            display: grid;
            gap: 15px;
            margin-top: 30px;
        }
        
        .btn {
            padding: 18px 24px;
            border: none;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            text-decoration: none;
            display: block;
            width: 100%;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #f8f9fa;
            color: #667eea;
            border: 2px solid #667eea;
        }
        
        .btn-secondary:hover {
            background: #e9ecef;
        }
        
        .btn-success {
            background: #4CAF50;
            color: white;
        }
        
        .btn-success:hover {
            background: #43a047;
        }
        
        .test-result {
            margin-top: 20px;
            padding: 15px;
            background: #e8f5e9;
            border-radius: 10px;
            display: none;
        }
        
        .test-result.show {
            display: block;
        }
        
        .test-result p {
            margin: 10px 0;
            color: #2e7d32;
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 20px;
            }
            
            .btn {
                padding: 16px;
                font-size: 16px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎤</div>
            <h1>Bryson语音MVP测试版</h1>
            <p class="subtitle">移动端兼容性测试 - 专为蓝牙耳机优化</p>
        </div>
        
        <div class="status-card">
            <div class="status-item">
                <span class="status-label">连接状态</span>
                <span id="connectionStatus" class="status-value status-good">✅ 已连接</span>
            </div>
            <div class="status-item">
                <span class="status-label">测试会话</span>
                <span id="sessionId" class="status-value">测试-2026-03-31</span>
            </div>
            <div class="status-item">
                <span class="status-label">移动端适配</span>
                <span id="mobileStatus" class="status-value status-good">✅ 已优化</span>
            </div>
            <div class="status-item">
                <span class="status-label">音频设备</span>
                <span id="audioStatus" class="status-value status-warning">需要授权麦克风</span>
            </div>
        </div>
        
        <div class="test-buttons">
            <button class="btn btn-primary" onclick="testAudioDevices()">
                🔊 测试音频设备
            </button>
            
            <button class="btn btn-secondary" onclick="checkMicrophone()">
                🎤 检查麦克风权限
            </button>
            
            <a href="/static/index.html" class="btn btn-success" target="_blank">
                🚀 进入完整测试界面
            </a>
        </div>
        
        <div id="testResult" class="test-result">
            <!-- 测试结果会显示在这里 -->
        </div>
    </div>
    
    <script>
        // 更新会话ID为当前时间
        document.getElementById('sessionId').textContent = 
            '测试-' + new Date().toISOString().slice(0, 10);
        
        // 自动检测移动端
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        document.getElementById('mobileStatus').textContent = 
            isMobile ? '✅ 移动端检测成功' : '✅ 桌面端';
        
        async function testAudioDevices() {
            const resultDiv = document.getElementById('testResult');
            resultDiv.innerHTML = '<p>正在测试音频设备...</p>';
            resultDiv.classList.add('show');
            
            try {
                // 测试音频输出
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = 440; // A4音
                gainNode.gain.value = 0.05;
                
                oscillator.start();
                
                setTimeout(() => {
                    oscillator.stop();
                    resultDiv.innerHTML = `
                        <p>✅ 测试音频播放成功！</p>
                        <p>如果您听到了440Hz的测试音，说明扬声器工作正常。</p>
                        <p>如果使用蓝牙耳机，请确保耳机已连接并设置为音频输出设备。</p>
                    `;
                    
                    // 继续测试麦克风
                    checkMicrophone();
                }, 1000);
                
            } catch (error) {
                resultDiv.innerHTML = `
                    <p>❌ 音频测试失败</p>
                    <p>错误: ${error.message}</p>
                    <p>请检查浏览器音频权限或尝试切换音频输出设备。</p>
                `;
            }
        }
        
        async function checkMicrophone() {
            const resultDiv = document.getElementById('testResult');
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const audioStatus = document.getElementById('audioStatus');
                audioStatus.textContent = '✅ 麦克风已授权';
                audioStatus.className = 'status-value status-good';
                
                resultDiv.innerHTML += `
                    <p>✅ 麦克风权限已获取！</p>
                    <p>设备: ${stream.getAudioTracks()[0].label || '默认麦克风'}</p>
                    <p>您现在可以进入完整测试界面进行语音测试。</p>
                `;
                
                // 停止所有轨道
                stream.getTracks().forEach(track => track.stop());
                
            } catch (error) {
                resultDiv.innerHTML += `
                    <p>❌ 麦克风权限被拒绝</p>
                    <p>请在浏览器设置中允许麦克风访问，然后刷新页面重试。</p>
                    <p>对于iOS设备，需要手动启用"Safari->设置->网站设置->麦克风"权限。</p>
                `;
            }
        }
        
        // 页面加载时检查基本状态
        window.addEventListener('load', () => {
            // 检查页面是否通过HTTPS加载（WebRTC要求）
            if (window.location.protocol !== 'https:' && !window.location.hostname.includes('localhost')) {
                alert('⚠️ 建议使用HTTPS连接以获得最佳WebRTC兼容性');
            }
        });
    </script>
</body>
</html>'''

def start_server_in_thread(port=8080):
    """在子线程中启动服务器"""
    # 保存服务器脚本
    server_script = "test_server.py"
    with open(server_script, 'w', encoding='utf-8') as f:
        f.write(get_server_script())
    
    # 保存移动端测试页面
    mobile_html = "mobile_test.html"
    with open(mobile_html, 'w', encoding='utf-8') as f:
        f.write(get_mobile_test_html())
    
    def run_server():
        subprocess.run([sys.executable, server_script])
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    time.sleep(3)
    
    # 检查服务器是否启动成功
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"✅ 服务器已在端口 {port} 启动")
            return True
        else:
            print(f"❌ 服务器启动失败，端口 {port} 不可用")
            return False
            
    except Exception as e:
        print(f"❌ 服务器检查失败: {e}")
        return False

def start_ngrok_tunnel(port=8080):
    """启动ngrok隧道"""
    try:
        from pyngrok import ngrok
        
        print("🔗 启动ngrok隧道...")
        
        # 获取公开URL
        public_url = ngrok.connect(port, proto="http", options={
            "region": "ap",
        })
        
        print(f"✅ ngrok隧道已建立!")
        print(f"   公开网址: {public_url}")
        print(f"   本地地址: http://localhost:{port}")
        
        # 保存链接到文件
        with open("external_url.txt", "w", encoding="utf-8") as f:
            f.write(f"Bryson语音MVP测试链接\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"有效期: 24小时\n\n")
            f.write(f"🔥 主测试链接:\n")
            f.write(f"{public_url}\n\n")
            f.write(f"📱 移动端测试链接:\n")
            f.write(f"{public_url}/mobile_test.html\n\n")
            f.write(f"🎯 完整界面链接:\n")
            f.write(f"{public_url}/static/index.html\n\n")
            f.write(f"📋 测试说明:\n")
            f.write(f"1. 使用手机/平板浏览器打开链接\n")
            f.write(f"2. 连接蓝牙耳机并设置为音频设备\n")
            f.write(f"3. 允许浏览器访问麦克风\n")
            f.write(f"4. 按界面提示进行测试\n")
        
        return public_url
        
    except ImportError:
        print("❌ pyngrok未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyngrok"], check=False)
        
        # 重试
        try:
            from pyngrok import ngrok
            return start_ngrok_tunnel(port)
        except:
            print("❌ ngrok隧道启动失败")
            return None
            
    except Exception as e:
        print(f"❌ ngrok隧道启动失败: {e}")
        print("⚠️  备用方案: 使用公开端口8080")
        print(f"   请尝试访问: http://113.176.70.27:{port}")
        return None

def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 Bryson语音MVP - 快速启动（外部访问版）")
    print("="*60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("目标: 为明天30分钟测试准备外部可访问链接")
    print("="*60)
    
    # 步骤1: 检查依赖
    print("\n1️⃣ 环境检查...")
    check_dependencies()
    
    # 步骤2: 检查端口
    print("\n2️⃣ 端口检查...")
    PORT = 8080  # 使用已确认可用的端口
    
    if check_port_available(PORT):
        print(f"  ✅ 端口 {PORT} 可用")
    else:
        print(f"  ⚠️  端口 {PORT} 被占用，尝试释放...")
        # 这里可以添加释放端口的逻辑
        # 暂时使用其他端口
        PORT = 8081
    
    # 步骤3: 启动服务器
    print(f"\n3️⃣ 启动服务器 (端口: {PORT})...")
    if start_server_in_thread(PORT):
        print(f"  ✅ 服务器启动成功")
    else:
        print("  ❌ 服务器启动失败")
        return
    
    # 步骤4: 创建ngrok隧道
    print("\n4️⃣ 创建外部访问链接...")
    public_url = start_ngrok_tunnel(PORT)
    
    if public_url:
        print("\n" + "="*60)
        print("🎉 Bryson语音MVP测试环境已准备就绪!")
        print("="*60)
        print(f"公开访问地址: {public_url}")
        print(f"移动端测试页: {public_url}/mobile_test.html")
        print(f"完整测试界面: {public_url}/static/index.html")
        print(f"本地管理地址: http://localhost:{PORT}")
        print("\n📱 测试说明:")
        print("1. 将以上链接发送给测试人员")
        print("2. 测试人员使用手机/平板浏览器打开")
        print("3. 连接蓝牙耳机并授权麦克风")
        print("4. 进行30分钟测试体验")
        print("="*60)
        
        # 在浏览器中打开
        open_browser = input("\n是否在浏览器中打开测试页面? [y/N]: ").lower().strip()
        if open_browser in ['y', 'yes', '是的']:
            webbrowser.open(f"{public_url}/mobile_test.html")
        
        # 保持运行
        print("\n🔄 服务器正在运行...")
        print("按 Ctrl+C 停止")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🔴 停止服务器...")
            
    else:
        print("\n❌ 无法创建外部链接")
        print("备选方案:")
        print("1. 手动配置路由器端口转发")
        print("2. 使用其他隧道工具 (Cloudflare Tunnel, localhost.run)")
        print("3. 临时使用云服务器部署")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 操作已取消")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()