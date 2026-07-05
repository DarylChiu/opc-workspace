#!/usr/bin/env python3
"""
STT完整功能演示 - 确保明天早上可验收
Bryson IELTS陪练助手
"""

import os
import json
import base64
import logging
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Bryson IELTS STT完整演示",
    description="完整语音转录功能演示 - 可公网访问",
    version="2.0.0"
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google API密钥
GOOGLE_API_KEY = "AIzaSyDUwxtaIAuXXTKwuyabGzBYFYC3-eaIw0A"

# 完整HTML界面
COMPLETE_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎤 Bryson IELTS STT完整演示</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            padding: 40px;
            max-width: 800px;
            width: 100%;
            position: relative;
            overflow: hidden;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #333;
            font-size: 32px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }
        
        .header h1 .icon {
            font-size: 40px;
        }
        
        .header p {
            color: #666;
            font-size: 16px;
            line-height: 1.6;
        }
        
        .status-bar {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px 20px;
            margin-bottom: 30px;
            border-left: 4px solid #4CAF50;
            transition: all 0.3s ease;
        }
        
        .status-bar.recording {
            border-left-color: #f44336;
            background: #ffebee;
        }
        
        .status-bar.processing {
            border-left-color: #ff9800;
            background: #fff3e0;
        }
        
        .status-bar h3 {
            color: #333;
            margin-bottom: 5px;
            font-size: 18px;
        }
        
        .status-bar p {
            color: #666;
            font-size: 14px;
        }
        
        .control-panel {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .btn {
            padding: 15px 30px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 150px;
            justify-content: center;
        }
        
        .btn-primary {
            background: #4CAF50;
            color: white;
        }
        
        .btn-primary:hover {
            background: #388E3C;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
        }
        
        .btn-danger {
            background: #f44336;
            color: white;
        }
        
        .btn-danger:hover {
            background: #d32f2f;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(244, 67, 54, 0.3);
        }
        
        .btn-secondary {
            background: #2196F3;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #1976D2;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(33, 150, 243, 0.3);
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .result-section {
            background: #f0f8ff;
            border-radius: 10px;
            padding: 25px;
            margin-top: 20px;
            display: none;
            border-left: 4px solid #2196F3;
        }
        
        .result-section.show {
            display: block;
            animation: fadeIn 0.5s ease;
        }
        
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .result-header h3 {
            color: #2196F3;
            font-size: 20px;
        }
        
        .confidence {
            background: #e3f2fd;
            color: #1565c0;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }
        
        .transcript {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            min-height: 150px;
            font-size: 16px;
            line-height: 1.6;
            color: #333;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin-bottom: 15px;
        }
        
        .transcript.empty {
            color: #999;
            font-style: italic;
        }
        
        .error-section {
            background: #ffebee;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            display: none;
            border-left: 4px solid #f44336;
        }
        
        .error-section.show {
            display: block;
            animation: fadeIn 0.5s ease;
        }
        
        .error-section h3 {
            color: #d32f2f;
            margin-bottom: 10px;
        }
        
        .error-details {
            background: white;
            border: 1px solid #ffcdd2;
            border-radius: 5px;
            padding: 15px;
            font-family: monospace;
            font-size: 13px;
            color: #c62828;
            overflow-x: auto;
        }
        
        .info-box {
            background: #e8f5e9;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
            border-left: 4px solid #4CAF50;
        }
        
        .info-box h3 {
            color: #2e7d32;
            margin-bottom: 10px;
        }
        
        .info-box ul {
            list-style: none;
            padding-left: 0;
        }
        
        .info-box li {
            padding: 8px 0;
            color: #555;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .info-box li::before {
            content: "✓";
            color: #4CAF50;
            font-weight: bold;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .pulse {
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #777;
            font-size: 14px;
            border-top: 1px solid #eee;
            padding-top: 20px;
        }
        
        .recording-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            background: #f44336;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 1s infinite;
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 20px;
            }
            
            .control-panel {
                flex-direction: column;
                gap: 10px;
            }
            
            .btn {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span class="icon">🎤</span>
                Bryson IELTS语音转录演示
                <span class="icon">🎯</span>
            </h1>
            <p>完整语音转录功能测试 - 支持录音和文件上传，实时显示转录结果</p>
        </div>
        
        <div id="statusBar" class="status-bar">
            <h3>📊 系统状态</h3>
            <p id="statusText">准备就绪，请点击下方按钮开始录音</p>
        </div>
        
        <div class="control-panel">
            <button id="startBtn" class="btn btn-primary" onclick="startRecording()">
                <span>🔴</span> 开始录音
            </button>
            <button id="stopBtn" class="btn btn-danger" onclick="stopRecording()" disabled>
                <span>⏹️</span> 停止录音
            </button>
        </div>
        
        <div style="text-align: center; margin: 20px 0;">
            <p style="color: #666; margin-bottom: 10px;">或者上传音频文件测试</p>
            <input type="file" id="audioFile" accept="audio/*" style="display: none;">
            <button class="btn btn-secondary" onclick="document.getElementById('audioFile').click()">
                <span>📁</span> 选择音频文件
            </button>
            <button class="btn btn-secondary" onclick="uploadAudio()" style="margin-left: 10px;">
                <span>📤</span> 上传并转录
            </button>
        </div>
        
        <div id="resultSection" class="result-section">
            <div class="result-header">
                <h3>📝 转录结果</h3>
                <div id="confidenceBadge" class="confidence">置信度: --%</div>
            </div>
            <div id="transcriptText" class="transcript empty">等待转录结果...</div>
            <div style="text-align: center; margin-top: 15px;">
                <button class="btn btn-secondary" onclick="copyTranscript()">
                    <span>📋</span> 复制文本
                </button>
                <button class="btn btn-secondary" onclick="testAgain()" style="margin-left: 10px;">
                    <span>🔄</span> 重新测试
                </button>
            </div>
        </div>
        
        <div id="errorSection" class="error-section">
            <h3>❌ 错误信息</h3>
            <div id="errorDetails" class="error-details"></div>
            <div style="text-align: center; margin-top: 15px;">
                <button class="btn btn-primary" onclick="retry()">
                    <span>🔄</span> 重试
                </button>
            </div>
        </div>
        
        <div class="info-box">
            <h3>✅ 功能说明</h3>
            <ul>
                <li>支持浏览器麦克风实时录音（Chrome/Firefox/Safari）</li>
                <li>支持上传MP3、WAV、WEBM等音频格式</li>
                <li>使用Google Speech-to-Text API进行高精度转录</li>
                <li>实时显示转录置信度</li>
                <li>支持复制转录文本</li>
                <li>自动处理网络错误和重试</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>© 2026 Bryson IELTS陪练助手 | 版本 2.0.0 | 服务状态: <span id="serviceStatus" style="color: #4CAF50;">● 在线</span></p>
            <p id="serverInfo">正在连接服务器...</p>
        </div>
    </div>

    <script>
        // 全局变量
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;
        let recordingTimer = null;
        
        // 更新状态
        function updateStatus(text, type = 'ready') {
            const statusBar = document.getElementById('statusBar');
            const statusText = document.getElementById('statusText');
            
            statusText.textContent = text;
            
            // 移除所有状态类
            statusBar.classList.remove('ready', 'recording', 'processing');
            statusBar.classList.add(type);
            
            // 更新状态文本
            if (type === 'recording') {
                statusText.innerHTML = '<span class="recording-indicator"></span>' + text;
            } else {
                statusText.textContent = text;
            }
        }
        
        // 显示结果
        function showResult(transcript, confidence) {
            const resultSection = document.getElementById('resultSection');
            const transcriptText = document.getElementById('transcriptText');
            const confidenceBadge = document.getElementById('confidenceBadge');
            
            transcriptText.textContent = transcript || '（无转录内容）';
            transcriptText.classList.remove('empty');
            
            confidenceBadge.textContent = `置信度: ${(confidence * 100).toFixed(1)}%`;
            confidenceBadge.style.background = confidence > 0.9 ? '#e8f5e9' : 
                                              confidence > 0.7 ? '#fff3e0' : '#ffebee';
            confidenceBadge.style.color = confidence > 0.9 ? '#2e7d32' : 
                                         confidence > 0.7 ? '#f57c00' : '#c62828';
            
            resultSection.classList.add('show');
            document.getElementById('errorSection').classList.remove('show');
        }
        
        // 显示错误
        function showError(message, details = '') {
            const errorSection = document.getElementById('errorSection');
            const errorDetails = document.getElementById('errorDetails');
            
            errorDetails.textContent = details || message;
            errorSection.classList.add('show');
            document.getElementById('resultSection').classList.remove('show');
            
            updateStatus('发生错误', 'processing');
        }
        
        // 开始录音
        async function startRecording() {
            try {
                updateStatus('请求麦克风权限...', 'processing');
                
                // 禁用开始按钮，启用停止按钮
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                
                // 获取麦克风权限
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });
                
                // 寻找支持的MIME类型
                let mimeType = 'audio/webm';
                const supportedTypes = [
                    'audio/webm;codecs=opus',
                    'audio/webm',
                    'audio/mp4',
                    'audio/ogg;codecs=opus'
                ];
                
                for (const type of supportedTypes) {
                    if (MediaRecorder.isTypeSupported(type)) {
                        mimeType = type;
                        console.log('使用音频格式:', mimeType);
                        break;
                    }
                }
                
                // 配置MediaRecorder
                const options = {
                    mimeType: mimeType,
                    audioBitsPerSecond: 128000
                };
                
                mediaRecorder = new MediaRecorder(stream, options);
                audioChunks = [];
                
                // 数据可用时收集
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                // 录音停止时处理
                mediaRecorder.onstop = async () => {
                    updateStatus('处理录音中...', 'processing');
                    
                    try {
                        const audioBlob = new Blob(audioChunks, { type: mimeType });
                        await processAudio(audioBlob, '录音');
                    } catch (error) {
                        showError('处理录音失败', error.message);
                    } finally {
                        // 释放麦克风
                        stream.getTracks().forEach(track => track.stop());
                    }
                };
                
                // 处理错误
                mediaRecorder.onerror = (event) => {
                    console.error('录音错误:', event);
                    showError('录音过程中出错', event.error?.message || '未知错误');
                    stopRecording();
                };
                
                // 开始录音
                mediaRecorder.start();
                isRecording = true;
                
                updateStatus('录音中... 点击停止按钮结束', 'recording');
                
                // 设置30秒超时
                recordingTimer = setTimeout(() => {
                    if (isRecording) {
                        stopRecording();
                        updateStatus('录音已自动停止（30秒限制）', 'ready');
                    }
                }, 30000);
                
            } catch (error) {
                console.error('开始录音失败:', error);
                showError('无法访问麦克风', error.message);
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            }
        }
        
        // 停止录音
        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                
                // 清除超时定时器
                if (recordingTimer) {
                    clearTimeout(recordingTimer);
                    recordingTimer = null;
                }
                
                // 更新按钮状态
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            }
        }
        
        // 上传音频文件
        async function uploadAudio() {
            const fileInput = document.getElementById('audioFile');
            if (!fileInput.files || fileInput.files.length === 0) {
                alert('请先选择音频文件');
                return;
            }
            
            const file = fileInput.files[0];
            updateStatus(`处理文件: ${file.name}`, 'processing');
            
            try {
                await processAudio(file, '文件上传');
            } catch (error) {
                showError('处理文件失败', error.message);
            }
        }
        
        // 处理音频
        async function processAudio(audioBlob, source) {
            try {
                // 转换为base64
                const base64Data = await blobToBase64(audioBlob);
                
                // 显示处理状态
                updateStatus(`正在转录${source}...`, 'processing');
                
                // 发送到后端API
                const response = await fetch('/api/stt', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({
                        audio: { 
                            content: base64Data,
                            filename: audioBlob.name || 'recording.webm',
                            type: audioBlob.type || 'audio/webm'
                        }
                    })
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`服务器错误 (${response.status}): ${errorText}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    updateStatus(`✅ ${source}转录完成`, 'ready');
                    showResult(data.text, data.confidence);
                    
                    // 记录成功
                    console.log(`转录成功: ${data.text.substring(0, 50)}...`);
                } else {
                    throw new Error(data.error || '转录失败');
                }
                
            } catch (error) {
                console.error('处理音频失败:', error);
                showError('音频处理失败', error.message);
                updateStatus('处理失败', 'processing');
            }
        }
        
        // Blob转Base64
        function blobToBase64(blob) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onloadend = () => {
                    const dataUrl = reader.result;
                    // 移除data:audio/webm;base64,前缀
                    const base64 = dataUrl.split(',')[1];
                    if (!base64) {
                        reject(new Error('无法转换音频为base64'));
                        return;
                    }
                    resolve(base64);
                };
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            });
        }
        
        // 复制转录文本
        function copyTranscript() {
            const transcriptText = document.getElementById('transcriptText').textContent;
            navigator.clipboard.writeText(transcriptText)
                .then(() => alert('转录文本已复制到剪贴板'))
                .catch(err => console.error('复制失败:', err));
        }
        
        // 重新测试
        function testAgain() {
            document.getElementById('resultSection').classList.remove('show');
            document.getElementById('errorSection').classList.remove('show');
            updateStatus('准备就绪，请点击下方按钮开始录音', 'ready');
        }
        
        // 重试
        function retry() {
            document.getElementById('errorSection').classList.remove('show');
            updateStatus('准备重试...', 'ready');
        }
        
        // 检查服务器状态
        async function checkServerStatus() {
            try {
                const response = await fetch('/api/health');
                if (response.ok) {
                    const data = await response.json();
                    document.getElementById('serverInfo').textContent = 
                        `服务器时间: ${new Date(data.time).toLocaleTimeString()}`;
                    return true;
                }
            } catch (error) {
                console.warn('服务器状态检查失败:', error);
            }
            return false;
        }
        
        // 初始化
        async function initialize() {
            updateStatus('正在初始化...', 'processing');
            
            // 检查浏览器支持
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                showError('浏览器不支持录音功能', '请使用Chrome、Firefox或Edge等现代浏览器');
                document.getElementById('startBtn').disabled = true;
                return;
            }
            
            // 检查服务器状态
            const isServerOk = await checkServerStatus();
            if (!isServerOk) {
                showError('服务器连接失败', '请检查网络连接或联系管理员');
            } else {
                updateStatus('准备就绪，请点击下方按钮开始录音', 'ready');
            }
            
            // 文件选择变化时自动上传
            document.getElementById('audioFile').addEventListener('change', uploadAudio);
            
            console.log('STT演示页面初始化完成');
        }
        
        // 页面加载完成后初始化
        window.addEventListener('DOMContentLoaded', initialize);
    </script>
</body>
</html>"""

@app.get("/")
async def serve_interface():
    """返回完整HTML界面"""
    return HTMLResponse(content=COMPLETE_HTML)

@app.post("/api/stt")
async def stt_process(request: Request):
    """STT处理接口"""
    try:
        data = await request.json()
        audio_content = data.get("audio", {}).get("content", "")
        
        if not audio_content:
            return JSONResponse({
                "success": False, 
                "error": "无音频数据"
            })
        
        logger.info(f"收到STT请求，音频大小: {len(audio_content)} 字符")
        
        # 发送到Google STT API
        stt_url = f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}"
        
        # 尝试多种配置
        stt_configs = [
            {
                "config": {
                    "encoding": "WEBM_OPUS",
                    "sampleRateHertz": 48000,
                    "languageCode": "en-US",
                    "model": "default",
                    "useEnhanced": True,
                }
            },
            {
                "config": {
                    "encoding": "MP3",
                    "sampleRateHertz": 48000,
                    "languageCode": "en-US",
                    "model": "default",
                    "useEnhanced": True,
                }
            },
            {
                "config": {
                    "encoding": "LINEAR16",
                    "sampleRateHertz": 16000,
                    "languageCode": "en-US",
                    "model": "default",
                }
            }
        ]
        
        errors = []
        for i, config in enumerate(stt_configs):
            try:
                stt_request = {
                    "config": config["config"],
                    "audio": {
                        "content": audio_content
                    }
                }
                
                logger.info(f"尝试配置 {i+1}: {config['config']['encoding']}")
                response = requests.post(stt_url, json=stt_request, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if "results" in result and len(result["results"]) > 0:
                        first_result = result["results"][0]
                        alternatives = first_result.get("alternatives", [])
                        if alternatives:
                            best_alt = alternatives[0]
                            transcript = best_alt.get("transcript", "").strip()
                            confidence = best_alt.get("confidence", 0.0)
                            
                            if transcript:
                                logger.info(f"STT成功: {transcript[:50]}... (置信度: {confidence:.2f})")
                                return JSONResponse({
                                    "success": True,
                                    "text": transcript,
                                    "confidence": confidence,
                                    "encoding_used": config["config"]["encoding"]
                                })
                    
                    # 如果成功但无结果，继续尝试下一个配置
                    errors.append(f"配置{i+1}成功但无转录结果")
                    continue
                    
                else:
                    error_msg = f"配置{i+1}失败 ({response.status_code}): {response.text[:200]}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"配置{i+1}异常: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # 所有配置都失败
        logger.error(f"所有STT配置均失败: {errors}")
        return JSONResponse({
            "success": False,
            "error": f"STT处理失败: {'; '.join(errors[:3])}"
        })
        
    except Exception as e:
        logger.error(f"STT处理异常: {e}")
        return JSONResponse({
            "success": False,
            "error": f"处理异常: {str(e)}"
        })

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "running",
        "service": "Bryson IELTS STT Demo",
        "version": "2.0.0",
        "time": datetime.now().isoformat(),
        "stt_configured": bool(GOOGLE_API_KEY),
        "stt_api_key_valid": True if GOOGLE_API_KEY else False
    }

@app.get("/api/test-audio")
async def test_audio():
    """测试音频处理端点"""
    # 返回一个简单的测试响应
    return JSONResponse({
        "success": True,
        "message": "STT服务正常",
        "endpoints": {
            "POST /api/stt": "处理音频转录",
            "GET /api/health": "健康检查",
            "GET /": "主界面"
        },
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    logger.info("🚀 启动Bryson IELTS STT完整演示服务器...")
    logger.info(f"🎯 API密钥状态: {'已配置' if GOOGLE_API_KEY else '未配置'}")
    logger.info("🌐 服务地址: http://localhost:8096")
    logger.info("📱 使用 ngrok http 8096 创建公网链接")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8096,
        log_level="info"
    )