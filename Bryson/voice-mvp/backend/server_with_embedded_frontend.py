#!/usr/bin/env python3
"""
Bryson语音MVP - Google TTS集成版服务器 (带内嵌前端)
专注解决TTS集成和语音交互问题，整合前端页面
"""

import os
import json
import asyncio
import logging
import base64
from typing import Dict, Optional
from datetime import datetime
import aiohttp
import hashlib
import tempfile

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Cloud TTS配置
GOOGLE_TTS_API_KEY = None
GOOGLE_TTS_BASE_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

# 从配置文件加载API密钥
def load_google_tts_api_key():
    """从配置文件加载Google TTS API密钥"""
    global GOOGLE_TTS_API_KEY
    
    key_file_paths = [
        os.path.expanduser("~/.openclaw/auth/google/ielts_tts_2026.key"),
        "/Users/zhaoyuzhao/.openclaw/auth/google/ielts_tts_2026.key"
    ]
    
    for key_file in key_file_paths:
        if os.path.exists(key_file):
            try:
                with open(key_file, 'r') as f:
                    GOOGLE_TTS_API_KEY = f.read().strip()
                logger.info(f"✅ Google TTS API密钥已从 {key_file} 加载")
                logger.info(f"密钥前10位: {GOOGLE_TTS_API_KEY[:10]}...")
                return True
            except Exception as e:
                logger.error(f"❌ 加载API密钥失败 {key_file}: {e}")
    
    logger.error("❌ 未找到Google TTS API密钥")
    return False

# 加载API密钥
load_google_tts_api_key()

# DARYL的个性化语音参数
DARYL_VOICE_PARAMS = {
    "languageCode": "en-US",
    "name": "en-US-Standard-D",  # 男性声音，适合商务场景
    "ssmlGender": "MALE",
    "speakingRate": 0.9,  # 稍慢，适应IELTS 5.5-6.0水平
    "pitch": -2.0,  # 音调稍低，更专业
    "volumeGainDb": 3.0,  # 稍微增加音量
}

# 投资者路演特定语音模板
INVESTOR_PITCH_VOICE_TEMPLATES = {
    "opening": {
        "style": "confident",
        "rate": 0.85,
        "pitch": -1.5,
        "volume": 4.0
    },
    "financial": {
        "style": "clear_precise",
        "rate": 0.8,
        "pitch": -2.5,
        "volume": 3.5
    },
    "vision": {
        "style": "inspiring",
        "rate": 1.0,
        "pitch": 1.0,
        "volume": 5.0
    },
    "call_to_action": {
        "style": "assertive",
        "rate": 0.9,
        "pitch": 0.0,
        "volume": 6.0
    }
}

# TTS缓存配置
TTS_CACHE_SIZE = 100  # 最大缓存条目数
TTS_CACHE_EXPIRY = 3600  # 缓存过期时间（秒）

# 缓存管理
tts_cache = {}  # key -> {data: audio_content, timestamp: unix_time}
tts_request_count = 0

# WebSocket连接管理
active_connections = {}  # session_id -> WebSocket

# 创建FastAPI应用
app = FastAPI(title="Bryson Voice Chat MVP with Google TTS", version="1.0.0-embedded-frontend")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== API端点 ==========

@app.get("/")
async def serve_index():
    """返回内嵌的前端页面"""
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bryson语音对话 - IELTS陪练助手</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            background: #f5f5f5;
        }
        .connected { border-color: #4CAF50; background: #e8f5e8; }
        .connecting { border-color: #FFC107; background: #fff8e1; }
        .disconnected { border-color: #f44336; background: #ffebee; }
        .card {
            border: 1px solid #eee;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        button {
            padding: 12px 24px;
            margin: 10px 5px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .btn-primary {
            background: #2196F3;
            color: white;
        }
        .btn-secondary {
            background: #f44336;
            color: white;
        }
        .btn-success {
            background: #4CAF50;
            color: white;
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .api-test {
            margin-top: 20px;
            padding: 15px;
            background: #f9f9f9;
            border-left: 4px solid #2196F3;
        }
        pre {
            background: #eee;
            padding: 10px;
            border-radius: 5px;
            overflow: auto;
        }
    </style>
</head>
<body>
    <h1>🎤 Bryson语音对话 - IELTS陪练助手</h1>
    
    <div id="connectionStatus" class="status connecting">
        🔄 正在建立连接...
    </div>
    
    <div class="card">
        <h2>📱 设备检查</h2>
        <p>请确保已授权麦克风和扬声器权限</p>
        
        <div>
            <button onclick="listDevices()">🔄 刷新设备列表</button>
            <div id="devicesInfo"></div>
        </div>
    </div>
    
    <div class="card">
        <h2>🎤 语音录制练习</h2>
        <button id="startBtn" onclick="startRecording()">▶️ 开始录音</button>
        <button id="stopBtn" onclick="stopRecording()" disabled>⏹️ 停止录音</button>
        <p id="recordingStatus">未开始录音</p>
        <audio id="audioPlayback" controls style="width: 100%; margin-top: 10px;"></audio>
    </div>
    
    <div class="card">
        <h2>🔊 Bryson语音反馈测试</h2>
        <textarea id="ttsText" rows="3" style="width: 100%; padding: 10px;" placeholder="输入要合成的英文文本...">Hello Daryl! This is Bryson voice test. Welcome to the investor meeting practice.</textarea>
        <div>
            <button onclick="speak('opening')" class="btn-success">👥 投资人开场白</button>
            <button onclick="speak('financial')" class="btn-success">💰 财务数据演示</button>
            <button onclick="speak('vision')" class="btn-success">🚀 公司愿景陈述</button>
            <button onclick="testCustomTTS()">📤 Bryson语音反馈</button>
        </div>
        <audio id="ttsAudio" controls style="width: 100%; margin-top: 10px;"></audio>
    </div>
    
    <div class="api-test">
        <h3>⚡ 系统状态检查</h3>
        <p><strong>Bryson语音服务器:</strong> <span id="serverStatus">检查中...</span></p>
        <p><strong>API延迟:</strong> <span id="latencyInfo">测量中...</span></p>
        <p><strong>TTS配置状态:</strong> <span id="ttsStatus">未知</span></p>
        <button onclick="checkAPI()">🔄 检查系统状态</button>
    </div>
    
    <script>
        // 录音变量
        let mediaRecorder = null;
        let audioChunks = [];
        
        // 更新连接状态
        function updateStatus(status, message) {
            const elem = document.getElementById('connectionStatus');
            elem.className = 'status ' + status;
            elem.innerHTML = status === 'connected' ? '✅ ' : 
                            status === 'connecting' ? '🔄 ' : 
                            '❌ ';
            elem.innerHTML += message;
        }
        
        // 检查服务器API状态
        async function checkAPI() {
            try {
                const start = Date.now();
                const response = await fetch('/api/status');
                const time = Date.now() - start;
                const data = await response.json();
                
                document.getElementById('serverStatus').innerHTML = 
                    '<span style="color:green">✅ 服务器正常</span> - ' + data.timestamp;
                document.getElementById('latencyInfo').innerHTML = time + 'ms';
                document.getElementById('ttsStatus').innerHTML = 
                    data.tts_configured ? '✅ 已配置' : '❌ 未配置';
                
                updateStatus('connected', '服务器连接正常，延迟: ' + time + 'ms');
                return true;
            } catch (error) {
                document.getElementById('serverStatus').innerHTML = 
                    '<span style="color:red">❌ 服务器错误: ' + error.message + '</span>';
                document.getElementById('latencyInfo').innerHTML = '无法测量';
                document.getElementById('ttsStatus').innerHTML = '未知';
                
                updateStatus('disconnected', '服务器连接失败: ' + error.message);
                return false;
            }
        }
        
        // 测试TTS功能
        async function testCustomTTS() {
            const text = document.getElementById('ttsText').value;
            if (!text.trim()) {
                alert('请输入文本');
                return;
            }
            
            try {
                const response = await fetch('/api/tts/speak', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: text,
                        voiceParams: {
                            languageCode: 'en-US',
                            name: 'en-US-Standard-D',
                            speakingRate: 0.9
                        }
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`TTS请求失败: ${response.status}`);
                }
                
                const audioData = await response.json();
                if (audioData.audioContent) {
                    const audioElement = document.getElementById('ttsAudio');
                    audioElement.src = 'data:audio/mp3;base64,' + audioData.audioContent;
                    audioElement.play();
                }
            } catch (error) {
                alert('TTS错误: ' + error.message);
            }
        }
        
        // 播放模板音频
        async function speak(template) {
            try {
                const response = await fetch(`/api/tts/${template}`);
                if (!response.ok) throw new Error(`模板请求失败: ${response.status}`);
                
                const audioData = await response.json();
                if (audioData.audioContent) {
                    const audioElement = document.getElementById('ttsAudio');
                    audioElement.src = 'data:audio/mp3;base64,' + audioData.audioContent;
                    audioElement.play();
                }
            } catch (error) {
                alert('播放错误: ' + error.message);
            }
        }
        
        // 录音功能
        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks);
                    const audioUrl = URL.createObjectURL(audioBlob);
                    document.getElementById('audioPlayback').src = audioUrl;
                    document.getElementById('recordingStatus').textContent = '录音完成';
                    
                    // 自动请求Bryson反馈（可选）
                    // testCustomTTS();
                };
                
                mediaRecorder.start();
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('recordingStatus').textContent = '正在录音...';
            } catch (error) {
                alert('无法访问麦克风: ' + error.message);
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            }
        }
        
        // 刷新设备列表
        async function listDevices() {
            try {
                const devices = await navigator.mediaDevices.enumerateDevices();
                const deviceList = devices
                    .filter(d => d.kind === 'audioinput' || d.kind === 'audiooutput')
                    .map(d => `${d.kind}: ${d.label || '未命名设备'}`)
                    .join('<br>');
                
                document.getElementById('devicesInfo').innerHTML = 
                    `<strong>找到设备:</strong><br>${deviceList || '无设备'}`;
            } catch (error) {
                alert('设备枚举错误: ' + error.message);
            }
        }
        
        // 初始化检查
        window.onload = async function() {
            await checkAPI();
            await listDevices();
            updateStatus('connected', '就绪 - 点击开始录音练习');
        };
    </script>
</body>
</html>
""")

@app.get("/api/status")
async def get_status():
    """服务器状态检查端点"""
    return {
        "status": "ok",
        "version": "1.0.0-embedded-frontend",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(active_connections),
        "tts_configured": bool(GOOGLE_TTS_API_KEY),
        "tts_request_count": tts_request_count,
        "tts_cache_size": len(tts_cache),
        "voice_params": DARYL_VOICE_PARAMS,
        "investor_templates": list(INVESTOR_PITCH_VOICE_TEMPLATES.keys())
    }

# ========== TTS功能 ==========

def generate_cache_key(text: str, voice_params: Dict) -> str:
    """生成TTS缓存键"""
    import hashlib
    
    params_str = json.dumps(voice_params, sort_keys=True)
    key_data = f"{text}|{params_str}"
    return hashlib.md5(key_data.encode()).hexdigest()

async def synthesize_speech(text: str, voice_params: Optional[Dict] = None) -> Optional[str]:
    """使用Google TTS合成语音"""
    global tts_request_count
    
    if not GOOGLE_TTS_API_KEY:
        logger.error("❌ 无Google TTS API密钥")
        return None
    
    if not text or not text.strip():
        logger.error("❌ 文本为空")
        return None
    
    # 使用默认语音参数或自定义参数
    params = voice_params or DARYL_VOICE_PARAMS.copy()
    
    # 生成缓存键
    cache_key = generate_cache_key(text, params)
    
    # 检查缓存
    if cache_key in tts_cache:
        cache_entry = tts_cache[cache_key]
        # 检查缓存过期
        if datetime.now().timestamp() - cache_entry["timestamp"] < TTS_CACHE_EXPIRY:
            logger.info(f"✅ 使用缓存TTS: {text[:50]}...")
            return cache_entry["data"]
    
    # 准备请求
    request_data = {
        "input": {"text": text},
        "voice": {
            "languageCode": params.get("languageCode", "en-US"),
            "name": params.get("name", "en-US-Standard-D"),
            "ssmlGender": params.get("ssmlGender", "MALE")
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": params.get("speakingRate", 0.9),
            "pitch": params.get("pitch", -2.0),
            "volumeGainDb": params.get("volumeGainDb", 3.0),
            "sampleRateHertz": 24000
        }
    }
    
    try:
        # 发送TTS请求
        url = f"{GOOGLE_TTS_BASE_URL}?key={GOOGLE_TTS_API_KEY}"
        async with aiohttp.ClientSession() as session:
            logger.info(f"🔄 请求Google TTS: {text[:50]}...")
            async with session.post(url, json=request_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ TTS API错误: {response.status}, {error_text}")
                    return None
                
                result_data = await response.json()
                audio_content = result_data.get("audioContent")
                
                if not audio_content:
                    logger.error("❌ TTS响应中无音频内容")
                    return None
                
                # 更新统计
                tts_request_count += 1
                
                # 缓存结果
                if len(tts_cache) >= TTS_CACHE_SIZE:
                    # 清理旧缓存
                    oldest_key = min(tts_cache.keys(), key=lambda k: tts_cache[k]["timestamp"])
                    del tts_cache[oldest_key]
                
                tts_cache[cache_key] = {
                    "data": audio_content,
                    "timestamp": datetime.now().timestamp()
                }
                
                logger.info(f"✅ TTS成功: {text[:50]}... (缓存大小: {len(tts_cache)})")
                return audio_content
                
    except Exception as e:
        logger.error(f"❌ TTS请求异常: {e}")
        return None

@app.post("/api/tts/speak")
async def tts_speak(request: Request):
    """TTS语音合成端点"""
    try:
        request_data = await request.json()
        text = request_data.get("text", "")
        voice_params = request_data.get("voiceParams", DARYL_VOICE_PARAMS)
        
        if not text:
            raise HTTPException(status_code=400, detail="文本不能为空")
        
        audio_content = await synthesize_speech(text, voice_params)
        if not audio_content:
            raise HTTPException(status_code=500, detail="TTS合成失败")
        
        return {
            "success": True,
            "audioContent": audio_content,
            "textLength": len(text)
        }
        
    except Exception as e:
        logger.error(f"TTS处理错误: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/tts/{template_name}")
async def tts_template(template_name: str):
    """投资者路演讲音模板"""
    if template_name not in INVESTOR_PITCH_VOICE_TEMPLATES:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 模板对应文本
    template_texts = {
        "opening": "Good morning ladies and gentlemen. My name is Daryl, and today I'm excited to present our business opportunity. Our company focuses on innovative solutions that address real market needs.",
        "financial": "Let me walk you through the financial projections. We expect to achieve 2.5 million in revenue by year two, with a gross margin of 65%. Our three-year plan shows consistent growth with a clear path to profitability.",
        "vision": "Our vision is to become the leading provider in this market segment. We believe in creating sustainable value through innovation and customer-centric solutions. We are building not just a company, but a legacy.",
        "call_to_action": "I invite you to join us on this exciting journey. Together, we can build something remarkable. This is the right opportunity at the right time. Let's make history."
    }
    
    text = template_texts.get(template_name, "")
    if not text:
        raise HTTPException(status_code=500, detail="模板文本缺失")
    
    # 使用模板特定参数
    template_config = INVESTOR_PITCH_VOICE_TEMPLATES[template_name]
    voice_params = DARYL_VOICE_PARAMS.copy()
    voice_params.update({
        "speakingRate": template_config["rate"],
        "pitch": template_config["pitch"],
        "volumeGainDb": template_config["volume"]
    })
    
    audio_content = await synthesize_speech(text, voice_params)
    if not audio_content:
        raise HTTPException(status_code=500, detail="模板语音生成失败")
    
    return {
        "success": True,
        "audioContent": audio_content,
        "template": template_name,
        "textLength": len(text)
    }

# ========== WebSocket功能 ==========

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket端点用于实时交互"""
    await websocket.accept()
    active_connections[session_id] = websocket
    logger.info(f"🟢 WebSocket连接: session={session_id}")
    
    try:
        while True:
            try:
                # 接收消息
                message_data = await websocket.receive_json()
                message_type = message_data.get("type")
                
                if message_type == "tts_request":
                    # TTS请求
                    text = message_data.get("text", "")
                    voice_template = message_data.get("voice_template", "default")
                    
                    if text:
                        # 处理TTS请求
                        audio_content = await synthesize_speech(text)
                        if audio_content:
                            await websocket.send_json({
                                "type": "tts_response",
                                "success": True,
                                "audioContent": audio_content
                            })
                        else:
                            await websocket.send_json({
                                "type": "tts_response",
                                "success": False,
                                "error": "语音生成失败"
                            })
                    else:
                        await websocket.send_json({
                            "type": "tts_response",
                            "success": False,
                            "error": "文本为空"
                        })
                        
                elif message_type in ["offer", "answer", "candidate"]:
                    # WebRTC信令消息
                    await websocket.send_json({
                        "type": f"{message_type}_received",
                        "session_id": session_id,
                        "status": "processing"
                    })
                    
                else:
                    # 未知消息类型
                    await websocket.send_json({
                        "type": "unknown_message",
                        "received_type": message_type
                    })
                    
            except WebSocketDisconnect:
                logger.info(f"🔴 WebSocket断开: session={session_id}")
                break
            except Exception as e:
                logger.error(f"处理消息时出错: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"处理消息时出错: {str(e)}"
                })
                
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}")
    finally:
        # 清理连接
        if session_id in active_connections:
            del active_connections[session_id]
        logger.info(f"🗑️ 清理连接: session={session_id}")

# ========== 启动服务器 ==========

if __name__ == "__main__":
    # 显示启动信息
    logger.info("🚀 启动Bryson语音服务器 (带内嵌前端)...")
    print("\n" + "="*60)
    print("🎤 Bryson Voice Chat MVP with Google TTS")
    print("   版本: 1.0.0-embedded-frontend")
    print("="*60)
    
    # 显示配置状态
    print(f"✅ Google TTS API密钥: {'已配置' if GOOGLE_TTS_API_KEY else '❌ 未配置'}")
    if GOOGLE_TTS_API_KEY:
        print(f"   密钥长度: {len(GOOGLE_TTS_API_KEY)} 字符")
        print(f"   密钥前段: {GOOGLE_TTS_API_KEY[:8]}...")
    
    print(f"👤 DARYL个性化语音参数:")
    for key, value in DARYL_VOICE_PARAMS.items():
        print(f"   {key}: {value}")
    
    print(f"💼 投资人路演讲音模板: {list(INVESTOR_PITCH_VOICE_TEMPLATES.keys())}")
    
    print("="*60)
    print("🌐 访问地址: http://localhost:8081")
    print("📚 API文档: http://localhost:8081/docs")
    print("🔌 WebSocket: ws://localhost:8081/ws/{session_id}")
    print("🎤 前端页面: http://localhost:8081/")
    print("📊 API状态: http://localhost:8081/api/status")
    print("🔊 TTS测试: http://localhost:8081/api/tts/test")
    print("="*60 + "\n")
    
    # 启动服务器
    uvicorn.run(
        "server_with_embedded_frontend:app",
        host="0.0.0.0",
        port=8081,  # 使用8081端口
        reload=True,
        log_level="info"
    )