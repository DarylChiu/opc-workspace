#!/usr/bin/env python3
"""
极简STT测试服务器
确保按钮交互正常工作
"""

import os
import json
import base64
import logging
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="STT速测服务器")

# 内置Google API密钥
GOOGLE_API_KEY = "AIzaSyDUwxtaIAuXXTKwuyabGzBYFYC3-eaIw0A"

# 非常简化的HTML界面
SIMPLE_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STT速测 - Bryson IELTS陪练助手</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        h1 { color: #1a73e8; text-align: center; }
        .btn { background: #1a73e8; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 6px; cursor: pointer; margin: 10px; }
        .btn:hover { background: #0d62d9; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .recording { background: #ffebee; color: #c62828; }
        .ready { background: #e8f5e9; color: #2e7d32; }
        .result { background: #f0f8ff; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 5px solid #2196F3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 STT音频转录速测</h1>
        <p style="text-align: center; color: #666;">确保按键交互正常 - 优化版</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <button class="btn" id="startBtn" onclick="startSimpleRecording()">🔴 录音</button>
            <button class="btn" id="stopBtn" onclick="stopSimpleRecording()" style="background: #f44336;" disabled>⏹️ 停止</button>
        </div>
        
        <div id="status" class="status ready">准备就绪</div>
        
        <div style="margin: 20px 0; text-align: center;">
            <input type="file" id="audioFile" accept="audio/*">
            <button class="btn" onclick="uploadSimpleAudio()" style="background: #4CAF50;">📤 上传文件测试</button>
        </div>
        
        <div id="result" class="result" style="display: none;">
            <h3>📝 转录结果</h3>
            <div id="transcript"></div>
        </div>
        
        <div id="error" style="color: #c62828; display: none;"></div>
    </div>

    <script>
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;
        
        function updateStatus(text, isRec = false) {
            const el = document.getElementById('status');
            el.textContent = text;
            el.className = 'status ' + (isRec ? 'recording' : 'ready');
        }
        
        function showResult(text, isError = false) {
            const resultEl = document.getElementById('result');
            const transcriptEl = document.getElementById('transcript');
            const errorEl = document.getElementById('error');
            
            if (isError) {
                errorEl.textContent = "错误: " + text;
                errorEl.style.display = 'block';
                resultEl.style.display = 'none';
            } else {
                transcriptEl.innerHTML = text;
                resultEl.style.display = 'block';
                errorEl.style.display = 'none';
            }
        }
        
        async function startSimpleRecording() {
            try {
                updateStatus("请求麦克风权限...");
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                
                // 最简单的配置
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: true 
                });
                
                // 尝试所有支持的格式
                let options = { audioBitsPerSecond: 128000 };
                const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'];
                
                for (const type of types) {
                    if (MediaRecorder.isTypeSupported(type)) {
                        options.mimeType = type;
                        break;
                    }
                }
                
                mediaRecorder = new MediaRecorder(stream, options);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = async () => {
                    updateStatus("处理录音中...");
                    const audioBlob = new Blob(audioChunks, { type: options.mimeType || 'audio/webm' });
                    await processSimpleAudio(audioBlob, '录音');
                    
                    // 释放麦克风
                    stream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.start();
                isRecording = true;
                updateStatus("🔴 录音中...", true);
                
                // 30秒超时
                setTimeout(() => {
                    if (isRecording) {
                        stopSimpleRecording();
                    }
                }, 30000);
                
            } catch (err) {
                updateStatus("录音失败: " + err.message);
                showResult(err.message, true);
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            }
        }
        
        function stopSimpleRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            }
        }
        
        async function uploadSimpleAudio() {
            const fileInput = document.getElementById('audioFile');
            if (!fileInput.files || fileInput.files.length === 0) {
                showResult("请先选择音频文件", true);
                return;
            }
            
            updateStatus("处理文件中...");
            await processSimpleAudio(fileInput.files[0], '文件上传');
        }
        
        async function processSimpleAudio(audioBlob, source) {
            try {
                // 转换为base64
                const reader = new FileReader();
                const base64Data = await new Promise((resolve, reject) => {
                    reader.onloadend = () => {
                        const dataUrl = reader.result;
                        const base64 = dataUrl.split(',')[1] || dataUrl;
                        resolve(base64);
                    };
                    reader.onerror = reject;
                });
                reader.readAsDataURL(audioBlob);
                
                // 发送到后端API
                const response = await fetch('/api/stt-simple', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        audio: { content: base64Data }
                    })
                });
                
                if (!response.ok) {
                    const errText = await response.text();
                    throw new Error(`服务器错误: ${response.status} - ${errText}`);
                }
                
                const data = await response.json();
                updateStatus(`✅ 处理完成 (${source})`);
                
                if (data.success) {
                    showResult(`
                        <strong>转录文本:</strong><br>
                        <textarea style="width:100%; height:100px; margin:10px 0; padding:10px;">${data.text}</textarea><br>
                        <small>置信度: ${(data.confidence * 100).toFixed(1)}%</small>
                    `, false);
                } else {
                    showResult(data.error || "处理失败", true);
                }
                
            } catch (err) {
                updateStatus("处理失败");
                showResult(err.message, true);
            }
        }
        
        // 页面加载检查
        window.onload = () => {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                showResult("浏览器不支持录音功能", true);
                document.getElementById('startBtn').disabled = true;
            }
            updateStatus("就绪 - 点击录音按钮开始");
        };
    </script>
</body>
</html>"""

@app.get("/")
async def serve_simple_interface():
    """返回极简HTML界面"""
    return HTMLResponse(content=SIMPLE_HTML)

@app.post("/api/stt-simple")
async def stt_simple(request: Request):
    """简化的STT处理接口"""
    try:
        data = await request.json()
        audio_content = data.get("audio", {}).get("content", "")
        
        if not audio_content:
            return JSONResponse({"success": False, "error": "无音频数据"})
        
        # 发送到Google STT
        stt_url = f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}"
        
        stt_request = {
            "config": {
                "encoding": "WEBM_OPUS",
                "sampleRateHertz": 48000,
                "languageCode": "en-US",
                "model": "default",
                "useEnhanced": True,
            },
            "audio": {
                "content": audio_content
            }
        }
        
        response = requests.post(stt_url, json=stt_request, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if "results" in result and len(result["results"]) > 0:
                first_result = result["results"][0]
                alternatives = first_result.get("alternatives", [])
                if alternatives:
                    best_alt = alternatives[0]
                    return JSONResponse({
                        "success": True,
                        "text": best_alt.get("transcript", ""),
                        "confidence": best_alt.get("confidence", 0.0)
                    })
        
        return JSONResponse({
            "success": False, 
            "error": f"STT处理失败: {response.status_code} - {response.text[:100]}"
        })
        
    except Exception as e:
        logger.error(f"STT处理异常: {e}")
        return JSONResponse({"success": False, "error": f"处理异常: {str(e)}"})

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "running", "time": datetime.now().isoformat()}

if __name__ == "__main__":
    logger.info("🚀 启动极简STT测试服务器...")
    logger.info("🎯 API密钥状态: 已内置")
    logger.info("🌐 服务地址: http://localhost:8095")
    uvicorn.run(app, host="0.0.0.0", port=8095)