#!/usr/bin/env python3
"""
极简嵌入式服务器 - 确保没有任何外部资源引用
"""

import os
import json
import logging
import asyncio
import base64
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import aiohttp
import requests

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
app = FastAPI(title="Bryson Voice Chat - Inline Version")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def serve_index():
    """返回完全内联的前端页面"""
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎤 Bryson语音对话 - 极简嵌入式版</title>
</head>
<body style="font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto;">
    <h1 style="color: #333; text-align: center;">🎤 Bryson语音对话 - IELTS陪练助手</h1>
    
    <div id="connectionStatus" style="padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; background: #f5f5f5;">
        🔄 正在建立连接...
    </div>
    
    <div style="border: 1px solid #eee; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <h2>📊 系统状态</h2>
        <p><strong>服务器状态:</strong> <span id="serverStatus">检查中...</span></p>
        <p><strong>TTS配置:</strong> <span id="ttsStatus">未知</span></p>
        <button onclick="checkAPI()" style="padding: 12px 24px; font-size: 16px; background: #2196F3; color: white; border: none; border-radius: 5px; cursor: pointer;">
            🔄 检查系统状态
        </button>
    </div>
    
    <div style="border: 1px solid #eee; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <h2>🎤 Bryson语音反馈</h2>
        <textarea id="ttsText" rows="3" style="width: 100%; padding: 10px;" placeholder="输入要合成的英文文本...">Hello Daryl! This is Bryson voice test. Welcome to investor meeting practice.</textarea><br>
        <button onclick="testCustomTTS()" style="padding: 12px 24px; margin: 10px 0; font-size: 16px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">
            🔊 播放Bryson语音
        </button><br>
        <audio id="ttsAudio" controls style="width: 100%; margin-top: 10px;"></audio>
    </div>
    
    <div style="border: 1px solid #eee; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <h2>✅ 快捷模板语音</h2>
        <button onclick="speak('opening')" style="padding: 12px 24px; margin: 5px; font-size: 16px; background: #2196F3; color: white; border: none; border-radius: 5px; cursor: pointer;">
            👥 投资人开场白
        </button>
        <button onclick="speak('financial')" style="padding: 12px 24px; margin: 5px; font-size: 16px; background: #2196F3; color: white; border: none; border-radius: 5px; cursor: pointer;">
            💰 财务数据演示
        </button>
        <button onclick="speak('vision')" style="padding: 12px 24px; margin: 5px; font-size: 16px; background: #2196F3; color: white; border: none; border-radius: 5px; cursor: pointer;">
            🚀 公司愿景陈述
        </button>
        <button onclick="speak('call_to_action')" style="padding: 12px 24px; margin: 5px; font-size: 16px; background: #2196F3; color: white; border: none; border-radius: 5px; cursor: pointer;">
            📢 号召行动结尾
        </button>
    </div>
    
    <div id="debugInfo" style="margin-top: 30px; padding: 15px; background: #f9f9f9; border-left: 4px solid #999; font-size: 14px; color: #666;">
        <strong>调试信息:</strong><br>
        <span id="debugContent">页面加载完成，等待用户操作...</span>
    </div>
    
    <script>
        // 更新状态显示
        function updateStatus(status, message) {
            const elem = document.getElementById('connectionStatus');
            elem.innerHTML = (status === 'connected' ? '✅ ' : status === 'error' ? '❌ ' : '🔄 ') + message;
            elem.style.borderColor = status === 'connected' ? '#4CAF50' : status === 'error' ? '#f44336' : '#FFC107';
            elem.style.background = status === 'connected' ? '#e8f5e8' : status === 'error' ? '#ffebee' : '#fff8e1';
        }
        
        // 更新调试信息
        function debug(msg) {
            const elem = document.getElementById('debugContent');
            elem.innerHTML = new Date().toLocaleTimeString() + ': ' + msg + '<br>' + elem.innerHTML;
        }
        
        // 检查服务器API状态
        async function checkAPI() {
            debug('开始检查服务器状态...');
            try {
                const start = Date.now();
                const response = await fetch('/api/status');
                const latency = Date.now() - start;
                const data = await response.json();
                
                document.getElementById('serverStatus').innerHTML = `✅ 正常 (延迟: ${latency}ms)`;
                document.getElementById('ttsStatus').innerHTML = data.tts_configured ? '✅ 已配置' : '❌ 未配置';
                
                updateStatus('connected', `服务器连接正常，延迟: ${latency}ms`);
                debug('服务器状态检查成功');
                return true;
            } catch (error) {
                debug('服务器状态检查失败: ' + error.message);
                document.getElementById('serverStatus').innerHTML = `❌ 错误: ${error.message}`;
                updateStatus('error', '服务器连接失败');
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
            
            debug('开始TTS请求: ' + text.substring(0, 50) + '...');
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
                    throw new Error(`TTS请求失败: ${response.status} ${response.statusText}`);
                }
                
                const audioData = await response.json();
                if (audioData.audioContent) {
                    const audioElement = document.getElementById('ttsAudio');
                    audioElement.src = 'data:audio/mp3;base64,' + audioData.audioContent;
                    audioElement.play();
                    debug('TTS成功，正在播放音频');
                } else {
                    debug('TTS响应无音频内容');
                    alert('TTS合成失败: 无音频内容返回');
                }
            } catch (error) {
                debug('TTS错误: ' + error.message);
                alert('TTS错误: ' + error.message);
            }
        }
        
        // 播放模板音频
        async function speak(template) {
            debug('请求模板音频: ' + template);
            try {
                const response = await fetch(`/api/tts/${template}`);
                if (!response.ok) throw new Error(`模板请求失败: ${response.status}`);
                
                const audioData = await response.json();
                if (audioData.audioContent) {
                    const audioElement = document.getElementById('ttsAudio');
                    audioElement.src = 'data:audio/mp3;base64,' + audioData.audioContent;
                    audioElement.play();
                    debug('模板音频播放成功: ' + template);
                } else {
                    alert('模板音频无效');
                }
            } catch (error) {
                debug('播放模板错误: ' + error.message);
                alert('播放错误: ' + error.message);
            }
        }
        
        // 页面加载初始化
        window.onload = async function() {
            debug('页面加载完成，开始初始化...');
            // 直接显示连接状态，不等待API检查
            await checkAPI();
            debug('初始化完成');
        };
        
        // 绑定Enter键触发TTS
        document.getElementById('ttsText').addEventListener('keypress', function(event) {
            if (event.key === 'Enter' && event.ctrlKey) {
                event.preventDefault();
                testCustomTTS();
            }
        });
        
        // 初始调试信息
        debug('JavaScript已加载，等待DOM就绪');
    </script>
</body>
</html>
""")

@app.get("/api/status")
async def get_status():
    """服务器状态检查端点"""
    return {
        "status": "ok",
        "version": "1.0.0-simple-inline",
        "timestamp": datetime.now().isoformat(),
        "tts_configured": bool(GOOGLE_TTS_API_KEY),
        "message": "Bryson语音对话服务器 - 极简嵌入式版"
    }

async def synthesize_speech(text: str, voice_params: Optional[Dict] = None) -> Optional[str]:
    """使用Google TTS合成语音"""
    if not GOOGLE_TTS_API_KEY:
        logger.error("❌ 无Google TTS API密钥")
        return None
    
    if not text or not text.strip():
        logger.error("❌ 文本为空")
        return None
    
    # 默认语音参数
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

@app.get("/api/tts/{template_name}")
async def tts_template(template_name: str):
    """投资者路演讲音模板"""
    template_texts = {
        "opening": "Good morning ladies and gentlemen. My name is Daryl, and today I'm excited to present our business opportunity. Our company focuses on innovative solutions that address real market needs.",
        "financial": "Let me walk you through our financial projections. We expect to achieve 2.5 million in revenue by year two, with a strong gross margin of 65%. Our growth plan is sustainable and focused on profitability.",
        "vision": "Our vision is to become the market leader in this segment. We believe in creating sustainable value through customer-centric innovation. This is not just a company, but a legacy in the making.",
        "call_to_action": "I invite you to join us on this exciting journey. Together, we can build something remarkable. This is the right opportunity at the right time. Let's make history together."
    }
    
    text = template_texts.get(template_name, "")
    if not text:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    audio_content = await synthesize_speech(text)
    if not audio_content:
        raise HTTPException(status_code=500, detail="模板语音生成失败")
    
    return {
        "success": True,
        "audioContent": audio_content,
        "template": template_name,
        "textLength": len(text)
    }

if __name__ == "__main__":
    logger.info("🚀 启动Bryson语音服务器 (极简嵌入式版)")
    logger.info("🌐 访问地址: http://localhost:8082")
    logger.info("📊 API状态: http://localhost:8082/api/status")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8082,
        reload=False,
        log_config=None
    )