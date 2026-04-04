#!/usr/bin/env python3
"""
Bryson语音MVP - 后端服务器
基于FastAPI的WebRTC信令服务器和TTS处理
"""

import os
import uuid
import json
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="Bryson Voice Chat MVP", version="0.1.0")

# CORS配置（允许前端跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 状态存储
active_connections: Dict[str, WebSocket] = {}
active_sessions: Dict[str, Dict] = {}

@app.get("/")
async def root():
    """根路径重定向到前端页面"""
    return RedirectResponse(url="/index.html")

@app.get("/voice-chat/{session_id}")
async def get_voice_chat_page(session_id: str):
    """
    获取语音聊天页面（带会话ID的路由）
    实际会渲染前端页面，会话ID通过WebSocket传递
    """
    return RedirectResponse(url=f"/index.html?session={session_id}")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebRTC信令WebSocket端点
    """
    await websocket.accept()
    active_connections[session_id] = websocket
    
    # 记录会话开始
    if session_id not in active_sessions:
        active_sessions[session_id] = {
            "start_time": datetime.now().isoformat(),
            "status": "connected"
        }
    
    logger.info(f"🟢 WebSocket连接建立: session={session_id}")
    
    try:
        # 发送连接确认
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "message": "WebRTC信令服务器已就绪"
        })
        
        # 处理消息循环
        while True:
            data = await websocket.receive_json()
            logger.debug(f"收到消息: {data.get('type')}")
            
            # 处理不同类型的信令消息
            message_type = data.get("type")
            
            if message_type == "offer":
                # 转发offer到对端（如果需要中转）
                await websocket.send_json({
                    "type": "offer",
                    "offer": data.get("offer")
                })
                
            elif message_type == "answer":
                # 转发answer到对端
                await websocket.send_json({
                    "type": "answer", 
                    "answer": data.get("answer")
                })
                
            elif message_type == "candidate":
                # 转发ICE candidate
                await websocket.send_json({
                    "type": "candidate",
                    "candidate": data.get("candidate")
                })
                
            elif message_type == "ready":
                # 客户端就绪
                await websocket.send_json({
                    "type": "system",
                    "message": "✅ 系统准备就绪，可以开始语音对话"
                })
                
            elif message_type == "text_message":
                # 文本消息处理（后续集成TTS）
                text = data.get("text", "")
                await websocket.send_json({
                    "type": "system",
                    "message": f"📝 文本消息已接收: {text[:50]}..."
                })
                
            elif message_type == "heartbeat":
                # 心跳响应
                await websocket.send_json({
                    "type": "heartbeat_ack",
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info(f"🔴 WebSocket断开: session={session_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
    finally:
        # 清理连接
        if session_id in active_connections:
            del active_connections[session_id]
        if session_id in active_sessions:
            active_sessions[session_id]["status"] = "disconnected"
            active_sessions[session_id]["end_time"] = datetime.now().isoformat()

@app.get("/api/status")
async def get_status():
    """获取服务器状态"""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_connections),
        "total_sessions": len(active_sessions),
        "version": "0.1.0-beta"
    }

@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """获取会话信息"""
    if session_id in active_sessions:
        return active_sessions[session_id]
    else:
        raise HTTPException(status_code=404, detail="会话不存在")

@app.post("/api/test-tts")
async def test_tts_endpoint():
    """
    TTS测试端点（后续集成Google TTS）
    """
    return {
        "status": "pending",
        "message": "TTS功能将在下一阶段集成",
        "supported_languages": ["en-US", "zh-CN"],
        "available_voices": ["Google TTS API"]
    }

if __name__ == "__main__":
    # 开发服务器启动
    logger.info("🚀 启动Bryson语音MVP后端服务器...")
    print("=================================================")
    print("Bryson Voice Chat MVP 后端服务器")
    print(f"访问地址: http://localhost:8000")
    print(f"API文档: http://localhost:8000/docs")
    print("=================================================")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )