#!/usr/bin/env python3
"""
Bryson语音MVP - 简化版服务器
专注于解决WebSocket连接问题
"""

import os
import json
import asyncio
import logging
from typing import Dict
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="Bryson Voice Chat MVP - Simple", version="0.1.0")

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

# 静态文件服务 - 使用更简单的方式
@app.get("/")
async def serve_index():
    """返回前端页面"""
    frontend_path = os.path.join(os.path.dirname(__file__), "../frontend")
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return HTMLResponse("<h1>Bryson Voice Chat MVP</h1><p>前端文件未找到</p>")

@app.get("/{filename}")
async def serve_static(filename: str):
    """返回静态文件"""
    frontend_path = os.path.join(os.path.dirname(__file__), "../frontend")
    file_path = os.path.join(frontend_path, filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        # 检查是否在子目录中
        for root, dirs, files in os.walk(frontend_path):
            if filename in files:
                return FileResponse(os.path.join(root, filename))
        raise HTTPException(status_code=404, detail="文件未找到")

@app.get("/api/status")
async def get_status():
    """API状态检查"""
    return {
        "status": "ok",
        "version": "0.1.0-simple",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(active_connections),
        "message": "Bryson语音服务器运行正常"
    }

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
            "message": "WebRTC信令服务器已就绪",
            "timestamp": datetime.now().isoformat()
        })
        
        # 处理消息循环
        while True:
            try:
                data = await websocket.receive_json()
                logger.info(f"收到消息: {data.get('type')}")
                
                message_type = data.get("type")
                
                if message_type == "ready":
                    await websocket.send_json({
                        "type": "server_ready",
                        "message": "服务器已准备好处理WebRTC信令",
                        "session_id": session_id
                    })
                    
                elif message_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif message_type == "offer":
                    # 简单的offer处理
                    await websocket.send_json({
                        "type": "offer_received",
                        "session_id": session_id,
                        "status": "processing"
                    })
                    
                elif message_type == "answer":
                    # 简单的answer处理
                    await websocket.send_json({
                        "type": "answer_received",
                        "session_id": session_id,
                        "status": "processing"
                    })
                    
                elif message_type == "candidate":
                    # ICE candidate处理
                    await websocket.send_json({
                        "type": "candidate_received",
                        "session_id": session_id
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

@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """获取会话信息"""
    return {
        "session_id": session_id,
        "active": session_id in active_connections,
        "timestamp": datetime.now().isoformat(),
        "status": "active" if session_id in active_connections else "inactive"
    }

@app.post("/api/test-tts")
async def test_tts_endpoint():
    """TTS测试端点"""
    return {
        "status": "ok",
        "message": "TTS服务正常（简化版）",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # 启动服务器
    logger.info("🚀 启动简化版Bryson语音服务器...")
    print("=================================================")
    print("Bryson Voice Chat MVP - 简化版服务器")
    print("访问地址: http://localhost:8080")
    print("API文档: http://localhost:8080/docs")
    print("WebSocket端点: ws://localhost:8080/ws/{session_id}")
    print("状态检查: http://localhost:8080/api/status")
    print("=================================================")
    
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )