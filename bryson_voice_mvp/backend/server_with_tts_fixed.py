#!/usr/bin/env python3
"""
Bryson语音MVP - Google TTS集成版服务器 (修复版本)
改用requests同步版本，避免SSL证书问题
"""

import os
import json
import asyncio
import logging
import base64
import ssl
from typing import Dict, Optional
from datetime import datetime
import hashlib
import tempfile

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import uvicorn
import requests
import certifi

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

# 创建FastAPI应用
app = FastAPI(title="Bryson Voice Chat MVP with Google TTS (Fixed)", version="1.0.1")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 状态存储
active_connections: Dict[str, WebSocket] = {}
tts_request_count = 0
tts_cache: Dict[str, dict] = {}  # text_hash -> {audio_data, timestamp}

# ========== TTS核心功能 (使用requests同步版本) ==========

async def synthesize_speech(text: str, voice_params: Optional[dict] = None) -> Optional[bytes]:
    """使用Google Text-to-Speech API生成语音（使用requests同步版本）"""
    global GOOGLE_TTS_API_KEY, tts_request_count
    
    if not GOOGLE_TTS_API_KEY:
        logger.error("❌ Google TTS API密钥未配置")
        return None
    
    if not text or not text.strip():
        logger.warning("❌ 文本为空")
        return None
    
    # 使用缓存
    text_hash = hashlib.md5(text.encode()).hexdigest()
    if text_hash in tts_cache:
        logger.info(f"📦 使用缓存语音: {text[:50]}...")
        return tts_cache[text_hash]["audio_data"]
    
    # 合并基础语音参数和自定义参数
    params = DARYL_VOICE_PARAMS.copy()
    if voice_params:
        params.update(voice_params)
    
    # 构建请求
    url = f"{GOOGLE_TTS_BASE_URL}?key={GOOGLE_TTS_API_KEY}"
    
    payload = {
        "input": {
            "text": text
        },
        "voice": {
            "languageCode": params["languageCode"],
            "name": params["name"],
            "ssmlGender": params["ssmlGender"]
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": params.get("speakingRate", 1.0),
            "pitch": params.get("pitch", 0.0),
            "volumeGainDb": params.get("volumeGainDb", 0.0),
            "effectsProfileId": ["headphone-class-device"]  # 优化耳机收听
        }
    }
    
    try:
        logger.info(f"🎤 发送TTS请求: {text[:50]}...")
        logger.debug(f"语音参数: {json.dumps(payload, indent=2)}")
        
        # 使用requests同步请求，避免SSL问题
        response = requests.post(url, json=payload, timeout=10)
        tts_request_count += 1
        
        if response.status_code == 200:
            result = response.json()
            
            if "audioContent" in result:
                audio_data = base64.b64decode(result["audioContent"])
                logger.info(f"✅ TTS成功: {len(audio_data)} 字节")
                
                # 更新缓存
                tts_cache[text_hash] = {
                    "audio_data": audio_data,
                    "timestamp": datetime.now().isoformat(),
                    "text": text[:100]
                }
                
                # 保持缓存大小
                if len(tts_cache) > 100:
                    oldest_key = min(tts_cache.keys(), key=lambda k: tts_cache[k]["timestamp"])
                    del tts_cache[oldest_key]
                
                return audio_data
            else:
                logger.error(f"❌ TTS响应缺少audioContent: {result}")
                return None
        else:
            error_text = response.text[:200]
            logger.error(f"❌ TTS API错误 {response.status_code}: {error_text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ TTS请求异常: {e}")
        return None

# ========== API端点 ==========

@app.get("/")
async def serve_index():
    """返回前端页面"""
    # 返回一个简单的测试页面
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bryson TTS Integration Test</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; }
            h1 { color: #333; }
            .status { padding: 20px; background: #f0f9ff; border-radius: 10px; margin: 20px 0; }
            button { padding: 12px 24px; background: #4285f4; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; margin: 10px 5px; }
            button:hover { background: #3367d6; }
            button:disabled { background: #ccc; cursor: not-allowed; }
            .test-area { margin: 30px 0; padding: 25px; border: 2px solid #e0e0e0; border-radius: 10px; background: #fafafa; }
            textarea { width: 100%; padding: 15px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; resize: vertical; }
            audio { margin: 15px 0; width: 100%; }
            .result { margin: 15px 0; padding: 15px; border-radius: 8px; }
            .success { background: #e8f5e8; color: #2e7d32; border: 1px solid #c8e6c9; }
            .error { background: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }
            .info { background: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb; }
        </style>
    </head>
    <body>
        <h1>🎤 Bryson TTS Integration Test</h1>
        <div class="status" id="status">
            <h3>🔧 System Status</h3>
            <p><strong>Server:</strong> <span id="server-status">Checking...</span></p>
            <p><strong>TTS API:</strong> <span id="tts-status">Checking...</span></p>
            <p><strong>Voice Params:</strong> Speaking Rate: 0.9, Pitch: -2.0, Volume: +3.0dB</p>
        </div>
        
        <div class="test-area">
            <h3>🔊 Test TTS Function</h3>
            <textarea id="test-text" rows="4" placeholder="Enter text to synthesize...">Hello Daryl! This is Bryson's Google TTS integration test. Perfect for IELTS speaking practice.</textarea>
            
            <div>
                <button onclick="testTTS('default')">🎙️ Test Default Voice</button>
                <button onclick="testTTS('opening')">💼 Investor Opening</button>
                <button onclick="testTTS('financial')">📊 Financial Data</button>
                <button onclick="testTTS('vision')">🚀 Vision Statement</button>
                <button onclick="testTTS('call_to_action')">🎯 Call to Action</button>
            </div>
            
            <audio id="audio-player" controls style="display: none;"></audio>
            <div id="tts-result"></div>
        </div>
        
        <div class="test-area">
            <h3>📊 Quick Tests</h3>
            <button onclick="checkStatus()">🔄 Check Status</button>
            <button onclick="testSimpleTTS()">🧪 Quick TTS Test</button>
            <button onclick="testInvestorPitch()">💼 Full Investor Pitch Test</button>
        </div>
        
        <script>
            async function checkStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    
                    document.getElementById('server-status').innerHTML = `<span style="color: green">✅ ${data.status} (v${data.version})</span>`;
                    document.getElementById('tts-status').innerHTML = data.tts_configured 
                        ? '<span style="color: green">✅ Configured</span>' 
                        : '<span style="color: red">❌ Not Configured</span>';
                        
                    showResult(`✅ Status OK: ${data.tts_request_count || 0} TTS requests, ${data.tts_cache_size || 0} cached`, 'success');
                } catch (error) {
                    document.getElementById('server-status').innerHTML = '<span style="color: red">❌ Error</span>';
                    showResult(`❌ Status check failed: ${error}`, 'error');
                }
            }
            
            async function testTTS(template) {
                const text = document.getElementById('test-text').value;
                const resultDiv = document.getElementById('tts-result');
                const audioPlayer = document.getElementById('audio-player');
                
                showResult(`⏳ Generating ${template} voice...`, 'info');
                
                try {
                    const response = await fetch('/api/tts/synthesize', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            text: text,
                            voice_template: template
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success && result.audio_url) {
                        showResult(`✅ ${template} voice generated successfully! (${result.duration_seconds}s, cached: ${result.cached ? 'yes' : 'no'})`, 'success');
                        
                        audioPlayer.src = result.audio_url;
                        audioPlayer.style.display = 'block';
                    } else {
                        showResult(`❌ ${template} failed: ${result.error || 'Unknown error'}`, 'error');
                    }
                } catch (error) {
                    showResult(`❌ Request failed: ${error}`, 'error');
                }
            }
            
            async function testSimpleTTS() {
                const testText = "This is a simple test of the TTS integration.";
                const response = await fetch('/api/tts/test');
                const data = await response.json();
                showResult(`🧪 Quick test: ${data.message || 'No message'}`, data.success ? 'success' : 'error');
            }
            
            async function testInvestorPitch() {
                showResult('💼 Testing all investor pitch templates...', 'info');
                
                try {
                    const response = await fetch('/api/tts/test-investor-pitch', {method: 'POST'});
                    const data = await response.json();
                    
                    if (data.success) {
                        let summary = `✅ Investor pitch test: ${data.summary}`;
                        showResult(summary, 'success');
                    } else {
                        showResult(`❌ Investor pitch test failed: ${data.message}`, 'error');
                    }
                } catch (error) {
                    showResult(`❌ Investor pitch test error: ${error}`, 'error');
                }
            }
            
            function showResult(message, type) {
                const resultDiv = document.getElementById('tts-result');
                resultDiv.innerHTML = `<div class="result ${type}">${message}</div>`;
            }
            
            // 页面加载时检查状态
            window.onload = function() {
                checkStatus();
            };
        </script>
    </body>
    </html>
    """)

@app.get("/api/status")
async def get_status():
    """API状态检查"""
    return {
        "status": "ok",
        "version": "1.0.1-tts-integrated-fixed",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(active_connections),
        "tts_configured": bool(GOOGLE_TTS_API_KEY),
        "tts_request_count": tts_request_count,
        "tts_cache_size": len(tts_cache),
        "voice_params": DARYL_VOICE_PARAMS,
        "investor_templates": list(INVESTOR_PITCH_VOICE_TEMPLATES.keys())
    }

@app.post("/api/tts/synthesize")
async def synthesize_tts_endpoint(request: Request):
    """TTS合成端点"""
    try:
        data = await request.json()
        text = data.get("text", "").strip()
        voice_template = data.get("voice_template", "default")
        
        if not text:
            return JSONResponse({"success": False, "error": "文本不能为空"}, status_code=400)
        
        # 使用缓存
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cached = text_hash in tts_cache
        
        # 检查是否是投资者路演讲音模板
        voice_params = DARYL_VOICE_PARAMS.copy()
        if voice_template != "default" and voice_template in INVESTOR_PITCH_VOICE_TEMPLATES:
            template = INVESTOR_PITCH_VOICE_TEMPLATES[voice_template]
            voice_params["speakingRate"] = template["rate"]
            voice_params["pitch"] = template["pitch"]
            voice_params["volumeGainDb"] = template["volume"]
        
        # 生成语音
        audio_data = await synthesize_speech(text, voice_params)
        
        if audio_data:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # 返回音频URL
            audio_filename = f"tts_{text_hash}.mp3"
            audio_dir = "/tmp/bryson_tts_audio"
            os.makedirs(audio_dir, exist_ok=True)
            
            final_path = os.path.join(audio_dir, audio_filename)
            os.rename(temp_file_path, final_path)
            
            # 简单估算音频时长
            duration_seconds = len(audio_data) / 16000  # 粗略估算
            
            return JSONResponse({
                "success": True,
                "audio_url": f"/api/tts/audio/{audio_filename}",
                "duration_seconds": round(duration_seconds, 2),
                "cached": cached,
                "text_length": len(text),
                "voice_template": voice_template
            })
        else:
            return JSONResponse({"success": False, "error": "语音生成失败"}, status_code=400)
            
    except Exception as e:
        logger.error(f"❌ TTS合成端点异常: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/tts/audio/{filename}")
async def get_audio_file(filename: str):
    """获取音频文件"""
    audio_dir = "/tmp/bryson_tts_audio"
    file_path = os.path.join(audio_dir, filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    else:
        raise HTTPException(status_code=404, detail="音频文件未找到")

@app.get("/api/tts/test")
async def test_tts_endpoint():
    """TTS测试端点 - 快速测试"""
    test_text = "Integration test: Daryl's personalized Google TTS is now working."
    
    logger.info("🧪 执行TTS快速测试...")
    audio_data = await synthesize_speech(test_text)
    
    if audio_data:
        return JSONResponse({
            "success": True,
            "message": "✅ Google TTS API工作正常",
            "audio_size": len(audio_data),
            "test_text": test_text,
            "voice_params": DARYL_VOICE_PARAMS
        })
    else:
        return JSONResponse({
            "success": False,
            "error": "❌ TTS测试失败，请检查API密钥",
            "api_key_configured": bool(GOOGLE_TTS_API_KEY)
        })

@app.post("/api/tts/test-investor-pitch")
async def test_investor_pitch():
    """测试投资人路演讲音模板"""
    test_scripts = {
        "opening": "Good morning, investors. Thank you for joining us today. My name is Daryl, and I'm excited to present our innovative financial platform.",
        "financial": "Our total addressable market is $3 billion, with a compound annual growth rate of 15%. We have secured three pilot customers and achieved a 92% customer satisfaction rate.",
        "vision": "In three years, we will be the leading provider of financial automation solutions in Southeast Asia. Our vision is to transform how small businesses manage their finances.",
        "call_to_action": "We are seeking $2 million in seed funding. This investment will accelerate our product development and expand our market reach. Join us in this exciting journey."
    }
    
    results = {}
    for template, text in test_scripts.items():
        logger.info(f"🎤 测试模板: {template}")
        
        # 应用模板参数
        voice_params = DARYL_VOICE_PARAMS.copy()
        if template in INVESTOR_PITCH_VOICE_TEMPLATES:
            tpl = INVESTOR_PITCH_VOICE_TEMPLATES[template]
            voice_params["speakingRate"] = tpl["rate"]
            voice_params["pitch"] = tpl["pitch"]
            voice_params["volumeGainDb"] = tpl["volume"]
        
        audio_data = await synthesize_speech(text, voice_params)
        
        results[template] = {
            "success": audio_data is not None,
            "audio_size": len(audio_data) if audio_data else 0,
            "text": text,
            "voice_params": voice_params
        }
    
    return JSONResponse({
        "success": True,
        "message": "✅ 投资人路演讲音测试完成",
        "results": results,
        "summary": f"成功: {sum(1 for r in results.values() if r['success'])}/{len(results)}"
    })

# ========== WebSocket端点 ==========

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket端点"""
    await websocket.accept()
    active_connections[session_id] = websocket
    
    logger.info(f"🟢 WebSocket连接建立: session={session_id}")
    
    try:
        # 发送连接确认
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "message": "WebRTC信令服务器已就绪，Google TTS集成完成",
            "timestamp": datetime.now().isoformat(),
            "tts_available": bool(GOOGLE_TTS_API_KEY)
        })
        
        # 处理消息循环
        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "ready":
                    await websocket.send_json({
                        "type": "server_ready",
                        "message": "服务器已准备好处理WebRTC信令和TTS请求",
                        "session_id": session_id
                    })
                    
                elif message_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif message_type == "tts_request":
                    # TTS请求
                    text = data.get("text", "")
                    voice_template = data.get("voice_template", "default")
                    
                    if text:
                        logger.info(f"🎤 WebSocket TTS请求: {text[:50]}...")
                        
                        # 生成语音
                        voice_params = DARYL_VOICE_PARAMS.copy()
                        if voice_template != "default" and voice_template in INVESTOR_PITCH_VOICE_TEMPLATES:
                            tpl = INVESTOR_PITCH_VOICE_TEMPLATES[voice_template]
                            voice_params["speakingRate"] = tpl["rate"]
                            voice_params["pitch"] = tpl["pitch"]
                            voice_params["volumeGainDb"] = tpl["volume"]
                        
                        audio_data = await synthesize_speech(text, voice_params)
                        
                        if audio_data:
                            # 创建临时文件
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                                temp_file.write(audio_data)
                                temp_file_path = temp_file.name
                            
                            # 移动到音频目录
                            audio_dir = "/tmp/bryson_tts_audio"
                            os.makedirs(audio_dir, exist_ok=True)
                            
                            import uuid
                            audio_filename = f"ws_{session_id}_{uuid.uuid4().hex[:8]}.mp3"
                            final_path = os.path.join(audio_dir, audio_filename)
                            os.rename(temp_file_path, final_path)
                            
                            await websocket.send_json({
                                "type": "tts_response",
                                "success": True,
                                "audio_url": f"/api/tts/audio/{audio_filename}",
                                "text": text[:100],
                                "voice_template": voice_template
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
    logger.info("🚀 启动Bryson语音服务器 (Google TTS集成修复版)...")
    print("\n" + "="*60)
    print("🎤 Bryson Voice Chat MVP with Google TTS (Fixed)")
    print("="*60)
    
    # 显示配置状态
    print(f"✅ Google TTS API密钥: {'已配置' if GOOGLE_TTS_API_KEY else '❌ 未配置'}")
    if GOOGLE_TTS_API_KEY:
        print(f"   密钥长度: {len(GOOGLE_TTS_API_KEY)} 字符")
        print(f"   密钥前段: {GOOGLE_TTS_API_KEY[:8]}...")
    
    print(f"👤 DARYL个性化参数:")
    for key, value in DARYL_VOICE_PARAMS.items():
        print(f"   {key}: {value}")
    
    print(f"💼 投资人路演讲音模板: {list(INVESTOR_PITCH_VOICE_TEMPLATES.keys())}")
    
    print("="*60)
    print("🌐 访问地址: http://localhost:8082")
    print("📚 API文档: http://localhost:8082/docs")
    print("🔌 WebSocket: ws://localhost:8082/ws/{session_id}")
    print("🧪 TTS测试: http://localhost:8082/api/tts/test")
    print("🧪 状态检查: http://localhost:8082/api/status")
    print("🔄 本版本使用requests同步调用，修复SSL证书问题")
    print("="*60 + "\n")
    
    # 启动服务器
    uvicorn.run(
        "server_with_tts_fixed:app",
        host="0.0.0.0",
        port=8082,  # 使用8082端口
        reload=True,
        log_level="info"
    )