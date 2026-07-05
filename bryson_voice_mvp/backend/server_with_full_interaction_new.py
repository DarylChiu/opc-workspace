#!/usr/bin/env python3
"""
Bryson语音交互MVP - 完整交互架构
实现录音→音频处理→TTS反馈的完整流程
"""

import os
import json
import logging
import asyncio
import base64
from datetime import datetime
from typing import Dict, Optional
import time

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import aiohttp

# 修复SSL证书问题
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Cloud TTS配置
GOOGLE_TTS_API_KEY = None
GOOGLE_TTS_BASE_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

def load_google_tts_api_key():
    """加载Google TTS API密钥"""
    global GOOGLE_TTS_API_KEY
    
    key_file = os.path.expanduser("~/.openclaw/auth/google/ielts_tts_2026.key")
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r') as f:
                GOOGLE_TTS_API_KEY = f.read().strip()
            logger.info(f"✅ Google TTS API密钥已加载")
            return True
        except Exception as e:
            logger.error(f"❌ 加载API密钥失败: {e}")
            return False
    else:
        logger.error("❌ 未找到Google TTS API密钥文件")
        return False

load_google_tts_api_key()

# 创建FastAPI应用
app = FastAPI(title="Bryson Voice MVP - Full Interaction")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 会话状态管理
user_sessions = {}  # session_id -> {last_recording_time: ..., feedback_count: ...}

@app.get("/")
async def serve_index():
    """返回完整交互前端页面"""
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎤 Bryson语音交互MVP</title>
</head>
<body style="font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto;">
    <h1 style="color: #333; text-align: center;">🎤 Bryson语音交互 - IELTS陪练助手</h1>
    
    <!-- 系统状态 -->
    <div id="connectionStatus" style="padding: 10px; margin: 10px 0; border: 2px solid #ddd; border-radius: 5px; background: #f5f5f5;">
        🔄 正在初始化系统...
    </div>
    
    <!-- 语音交互主区域 -->
    <div style="border: 1px solid #4CAF50; padding: 25px; margin: 20px 0; border-radius: 10px; background: #f9fff9;">
        <h2 style="color: #2E7D32;">🎤 语音交互练习</h2>
        
        <div style="margin: 20px 0; text-align: center;">
            <button id="startBtn" onclick="startRecording()" 
                style="padding: 15px 30px; font-size: 18px; background: #4CAF50; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">
                🎙️ 开始录音
            </button>
            <button id="stopBtn" onclick="stopRecording()" disabled
                style="padding: 15px 30px; font-size: 18px; background: #f44336; color: white; border: none; border-radius: 8px; cursor: pointer;">
                ⏹️ 停止录音
            </button>
        </div>
        
        <p id="recordingStatus" style="text-align: center; font-size: 16px; color: #666;">
            准备开始语音练习...
        </p>
        
        <div style="display: flex; justify-content: space-between; margin: 20px 0;">
            <div style="flex: 1; margin-right: 10px;">
                <h4>🎤 你的录音</h4>
                <audio id="audioPlayback" controls style="width: 100%;"></audio>
            </div>
            <div style="flex: 1; margin-left: 10px;">
                <h4>🔊 Bryson的反馈</h4>
                <audio id="brysonFeedback" controls style="width: 100%;"></audio>
            </div>
        </div>
        
        <div id="interactionStatus" style="margin-top: 15px; padding: 10px; background: #e3f2fd; border-radius: 5px; text-align: center;">
            <strong>交互状态:</strong> <span id="statusText">等待你开始练习</span>
        </div>
    </div>
    
    <!-- 交互统计 -->
    <div style="border: 1px solid #2196F3; padding: 20px; margin: 20px 0; border-radius: 10px; background: #e3f2fd;">
        <h3>📊 练习统计</h3>
        <p><strong>已完成交互:</strong> <span id="interactionCount">0</span> 次</p>
        <p><strong>上次练习:</strong> <span id="lastPracticeTime">尚未开始</span></p>
        <div style="margin-top: 15px;">
            <button onclick="resetStats()" style="padding: 8px 16px; background: #999; color: white; border: none; border-radius: 4px; cursor: pointer;">
                🔄 重置统计
            </button>
        </div>
    </div>
    
    <!-- TTS独立测试区域 -->
    <div style="border: 1px solid #FF9800; padding: 20px; margin: 20px 0; border-radius: 10px; background: #fff3e0;">
        <h3>🔧 TTS功能测试</h3>
        <textarea id="ttsText" rows="3" style="width: 100%; padding: 10px; margin-bottom: 10px;" 
            placeholder="输入要Bryson朗读的英文内容...">Hello Daryl! I'm Bryson. Thank you for practicing English with me. Let's start our conversation!</textarea><br>
        <button onclick="testCustomTTS()" style="padding: 12px 24px; background: #FF9800; color: white; border: none; border-radius: 5px; cursor: pointer;">
            🔊 独立测试TTS
        </button><br>
        <audio id="ttsAudio" controls style="width: 100%; margin-top: 10px;"></audio>
    </div>
    
    <!-- 系统信息 -->
    <div style="margin-top: 30px; padding: 15px; background: #f5f5f5; border-left: 4px solid #666; font-size: 12px; color: #666;">
        <strong>📱 系统状态</strong><br>
        <span id="serverInfo">正在检查服务器...</span><br>
        <span id="lastUpdate">最后更新时间: -</span>
    </div>
    
    <script>
        // 核心状态管理
        let mediaRecorder = null;
        let audioChunks = [];
        let interactionCount = 0;
        let sessionId = `session_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
        
        // 更新UI状态
        function updateStatus(status, message) {
            const elem = document.getElementById('connectionStatus');
            elem.innerHTML = (status === 'connected' ? '✅ ' : status === 'error' ? '❌ ' : '🔄 ') + message;
            elem.style.borderColor = status === 'connected' ? '#4CAF50' : status === 'error' ? '#f44336' : '#FFC107';
        }
        
        function updateInteractionStatus(status) {
            document.getElementById('statusText').textContent = status;
        }
        
        function updateSystemInfo(info) {
            document.getElementById('serverInfo').textContent = info;
            document.getElementById('lastUpdate').textContent = '最后更新时间: ' + new Date().toLocaleTimeString();
        }
        
        // 检查服务器状态
        async function checkAPI() {
            try {
                const start = Date.now();
                const response = await fetch('/api/status');
                const latency = Date.now() - start;
                const data = await response.json();
                
                updateStatus('connected', `服务器正常 (延迟: ${latency}ms)`);
                updateSystemInfo(`服务器版本: ${data.version} | TTS: ${data.tts_configured ? '✅' : '❌'}`);
                return true;
            } catch (error) {
                updateStatus('error', '服务器连接失败: ' + error.message);
                return false;
            }
        }
        
        // TTS独立测试
        async function testCustomTTS() {
            const text = document.getElementById('ttsText').value;
            if (!text.trim()) {
                alert('请输入文本');
                return;
            }
            
            try {
                const response = await fetch('/api/tts/speak', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text})
                });
                
                if (!response.ok) throw new Error(`TTS请求失败: ${response.status}`);
                
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
        
        // 主要交互功能
        
        // 1. 开始录音
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
                
                mediaRecorder.onstop = async () => {
                    // 创建本地播放
                    const audioBlob = new Blob(audioChunks);
                    const audioUrl = URL.createObjectURL(audioBlob);
                    document.getElementById('audioPlayback').src = audioUrl;
                    
                    // 更新状态
                    document.getElementById('recordingStatus').textContent = '录音完成，等待Bryson反馈...';
                    updateInteractionStatus('正在生成反馈...');
                    
                    // 自动获取Bryson反馈
                    await getBrysonFeedback();
                };
                
                mediaRecorder.start();
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('recordingStatus').textContent = '正在录音...';
                updateInteractionStatus('录音中...');
                
            } catch (error) {
                alert('无法访问麦克风: ' + error.message);
                updateInteractionStatus('设备权限错误');
            }
        }
        
        // 2. 停止录音
        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            }
        }
        
        // 3. 获取Bryson反馈（核心交互）
        async function getBrysonFeedback() {
            try {
                // 模拟用户语音内容 - 未来STT会替换这里
                const userSpeechSimulation = "学生说了几句英语，需要Bryson给出反馈";
                
                // 发送到后端处理
                const response = await fetch('/api/process_recording', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        session_id: sessionId,
                        user_input: userSpeechSimulation,
                        timestamp: new Date().toISOString()
                    })
                });
                
                if (!response.ok) throw new Error(`处理失败: ${response.status}`);
                
                const result = await response.json();
                
                if (result.success && result.feedback_audio) {
                    // 播放Bryson反馈
                    const feedbackAudio = document.getElementById('brysonFeedback');
                    feedbackAudio.src = 'data:audio/mp3;base64,' + result.feedback_audio;
                    feedbackAudio.play();
                    
                    // 更新统计
                    interactionCount++;
                    document.getElementById('interactionCount').textContent = interactionCount;
                    document.getElementById('lastPracticeTime').textContent = new Date().toLocaleTimeString();
                    
                    document.getElementById('recordingStatus').textContent = 'Bryson反馈已播放！';
                    updateInteractionStatus('交互完成');
                    
                    // 自动重新准备下一次
                    setTimeout(() => {
                        document.getElementById('recordingStatus').textContent = '准备下一次练习...';
                        updateInteractionStatus('就绪，等待你开始练习');
                    }, 3000);
                    
                } else {
                    throw new Error('无有效反馈音频');
                }
                
            } catch (error) {
                document.getElementById('recordingStatus').textContent = '反馈生成失败: ' + error.message;
                updateInteractionStatus('反馈生成失败');
                
                // 回退到默认反馈
                playFallbackFeedback();
            }
        }
        
        // 4. 备用反馈（TTS直接生成）
        async function playFallbackFeedback() {
            try {
                const response = await fetch('/api/tts/speak', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        text: "Great practice! Keep going. Try to speak a little louder next time."
                    })
                });
                
                if (response.ok) {
                    const audioData = await response.json();
                    if (audioData.audioContent) {
                        const audioElement = document.getElementById('brysonFeedback');
                        audioElement.src = 'data:audio/mp3;base64,' + audioData.audioContent;
                        audioElement.play();
                    }
                }
            } catch (error) {
                console.warn('备用反馈失败:', error);
            }
        }
        
        // 5. 重置统计
        function resetStats() {
            interactionCount = 0;
            document.getElementById('interactionCount').textContent = '0';
            document.getElementById('lastPracticeTime').textContent = '重置于 ' + new Date().toLocaleTimeString();
            updateInteractionStatus('统计已重置');
        }
        
        // 初始化
        window.onload = async function() {
            await checkAPI();
            updateInteractionStatus('就绪，等待你开始练习');
            
            // 初始提示
            setTimeout(() => {
                if (interactionCount === 0) {
                    document.getElementById('recordingStatus').textContent = '点击"开始录音"按钮开始语音交互练习';
                }
            }, 1000);
        };
        
        // 定期检查状态
        setInterval(checkAPI, 30000); // 每30秒检查一次
    </script>
</body>
</html>
""")

@app.get("/api/status")
async def get_status():
    """服务器状态检查端点"""
    return {
        "status": "ok",
        "version": "1.1.0-full-interaction",
        "timestamp": datetime.now().isoformat(),
        "tts_configured": bool(GOOGLE_TTS_API_KEY),
        "session_count": len(user_sessions),
        "message": "Bryson语音交互MVP - 完整交互架构"
    }

async def synthesize_speech(text: str, voice_params: Optional[Dict] = None) -> Optional[str]:
    """使用Google TTS合成语音"""
    if not GOOGLE_TTS_API_KEY:
        logger.error("❌ 无Google TTS API密钥")
        return None
    
    if not text or not text.strip():
        logger.error("❌ 文本为空")
        return None
    
    # 默认语音参数 - Daryl个性化设置
    params = voice_params or {
        "languageCode": "en-US",
        "name": "en-US-Standard-D",
        "ssmlGender": "MALE",
        "speakingRate": 0.9,
        "pitch": -2.0,
        "volumeGainDb": 3.0
    }
    
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
                
                logger.info(f"✅ TTS成功: {text[:50]}...")
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
        
        if not text:
            raise HTTPException(status_code=400, detail="文本不能为空")
        
        audio_content = await synthesize_speech(text)
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

@app.post("/api/process_recording")
async def process_recording(request: Request):
    """处理用户录音并生成反馈"""
    try:
        request_data = await request.json()
        session_id = request_data.get("session_id", "anonymous")
        user_input = request_data.get("user_input", "User completed a recording practice.")
        timestamp = request_data.get("timestamp", datetime.now().isoformat())
        
        # 初始化会话
        if session_id not in user_sessions:
            user_sessions[session_id] = {
                "first_seen": timestamp,
                "interaction_count": 0,
                "last_interaction": None
            }
        
        session = user_sessions[session_id]
        session["interaction_count"] = session.get("interaction_count", 0) + 1
        session["last_interaction"] = timestamp
        
        logger.info(f"👤 处理录音: session={session_id}, 交互#{session['interaction_count']}")
        
        # 生成智能反馈（模拟逻辑，未来STT替换）
        feedback_text = generate_feedback_response(session['interaction_count'], user_input)
        
        # 合成语音反馈
        audio_content = await synthesize_speech(feedback_text)
        
        if not audio_content:
            # 回退到默认反馈
            feedback_text = "Great practice session! Your recording was received successfully."
            audio_content = await synthesize_speech(feedback_text)
            
            if not audio_content:
                raise HTTPException(status_code=500, detail="无法生成语音反馈")
        
        return {
            "success": True,
            "session_id": session_id,
            "interaction_number": session['interaction_count'],
            "feedback_text": feedback_text,
            "feedback_audio": audio_content,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"处理录音错误: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

def generate_feedback_response(interaction_num: int, user_input: str) -> str:
    """根据用户输入生成反馈内容"""
    
    feedback_templates = [
        # 第一次交互
        "Great start! I can hear you're practicing your English pronunciation. Keep going with confidence.",
        
        # 第二次交互
        "Nice pronunciation! Try to speak a little slower for better clarity.",
        
        # 第三次交互
        "Good effort! Remember to use complete sentences when speaking.",
        
        # 投资者相关反馈
        "That sounds like a business presentation. Remember to use strong, confident language for investor meetings.",
        
        # 通用鼓励
        "Excellent practice! Consistent speaking practice will improve your fluency significantly.",
        
        # 技术相关
        "Your recording quality is good. Make sure you're in a quiet environment for best results.",
        
        # 雅思相关
        "For the IELTS speaking test, remember to structure your answers with clear introduction, body, and conclusion.",
    ]
    
    # 简单逻辑：根据交互次数和输入内容选择模板
    template_idx = (interaction_num - 1) % len(feedback_templates)
    
    # 如果用户输入包含特定关键词，选择相关模板
    lower_input = user_input.lower()
    if "investor" in lower_input or "business" in lower_input or "pitch" in lower_input:
        return "For investor presentations, focus on clear value proposition and confident delivery. Practice your opening statement until it feels natural."
    elif "ielts" in lower_input or "test" in lower_input or "exam" in lower_input:
        return "IELTS speaking success comes from structured answers and varied vocabulary. Practice answering common topics like hometown, work, or leisure activities."
    
    return feedback_templates[template_idx]

if __name__ == "__main__":
    logger.info("🚀 启动Bryson语音交互MVP (完整交互架构)")
    logger.info("🌐 访问地址: http://localhost:8085")
    logger.info("🎤 核心功能: 录音→处理→反馈 完整工作流")
    logger.info("📊 API状态: http://localhost:8085/api/status")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8085,
        reload=False,
        log_config=None
    )