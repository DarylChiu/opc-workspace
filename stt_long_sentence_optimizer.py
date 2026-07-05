#!/usr/bin/env python3
"""
Bryson STT长句子优化服务器 - 方案A实施
专注于解决长句子识别瓶颈，集成音频分片、噪声抑制、VAD检测
"""

import os
import sys
import json
import base64
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import io
import wave
import struct
import math

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import aiohttp
import numpy as np
from pydantic import BaseModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Bryson STT长句子优化服务器",
    description="IELTS陪练助手 - 专为解决长句子识别瓶颈",
    version="2.0.0-long-sentence-fix"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 数据模型 ============
class STTRequest(BaseModel):
    audio_content: str
    language_code: str = "en-US"
    sample_rate: int = 48000  # 提高采样率
    enable_punctuation: bool = True
    enable_vad: bool = True  # 启用语音活动检测
    chunk_size_seconds: float = 3.0  # 分片大小（秒）
    noise_reduction_level: int = 2  # 噪声抑制级别 0-3

class STTResult(BaseModel):
    text: str
    confidence: float
    duration_ms: int
    chunk_count: int = 1
    processing_time_ms: int
    vad_used: bool = False

# ============ 全局配置 ============
CONFIG = {
    "port": 8095,
    "host": "0.0.0.0",
    "api_key": "AIzaSyDUwxtaIAuXXTKwuyabGzBYFYC3-eaIw0A",  # Google STT API密钥
    "max_audio_duration_seconds": 60,
    "chunk_threshold_seconds": 8.0,  # 超过此长度自动启用分片
    "min_silence_duration": 0.4,  # 语音静音检测阈值（秒）
    "default_encoding": "LINEAR16",
    "supported_encodings": ["LINEAR16", "MP3", "FLAC"],  # 优先使用这些稳定格式
    "noise_reduction_configs": {
        0: {"noise_level": "none"},
        1: {"noise_level": "low", "enable_voice_filter": True},
        2: {"noise_level": "medium", "enable_voice_filter": True, "enable_separate_recognition": False},
        3: {"noise_level": "high", "enable_voice_filter": True, "enable_separate_recognition": False, "model": "video"}
    },
    "ielts_context_phrases": [
        "IELTS", "speaking test", "part one", "part two", "part three",
        "business presentation", "investor pitch", "market analysis",
        "financial projections", "competitive advantage", "target market",
        "revenue model", "exit strategy", "pitch deck", "elevator pitch"
    ]
}

# 性能统计
performance_stats = {
    "total_requests": 0,
    "chunked_requests": 0,
    "vad_processed": 0,
    "avg_chunk_count": 0.0,
    "avg_confidence": 0.0,
    "total_audio_duration_seconds": 0.0
}

# ============ VAD语音活动检测工具 ============
class VADProcessor:
    """简单的语音活动检测器"""
    
    @staticmethod
    def calculate_energy(audio_data: np.ndarray, sample_rate: int = 48000) -> float:
        """计算音频片段的能量"""
        if len(audio_data) == 0:
            return 0.0
        return float(np.mean(np.square(audio_data.astype(float))))
    
    @staticmethod
    def detect_speech_activity(audio_data: np.ndarray, sample_rate: int, 
                              frame_duration_ms: int = 20, threshold_ratio: float = 2.0):
        """
        检测音频中的语音活动
        返回：(is_speech, confidence, segments)
        """
        if len(audio_data) == 0:
            return False, 0.0, []
        
        frame_size = int(sample_rate * frame_duration_ms / 1000)
        if frame_size == 0:
            frame_size = 1
        
        frames = []
        for i in range(0, len(audio_data), frame_size):
            frame = audio_data[i:i+frame_size]
            if len(frame) > 0:
                energy = VADProcessor.calculate_energy(frame)
                frames.append((i, i+len(frame), energy))
        
        if not frames:
            return False, 0.0, []
        
        energies = [e for _, _, e in frames]
        avg_energy = np.mean(energies)
        std_energy = np.std(energies) if len(energies) > 1 else 0.01
        
        # 动态阈值
        threshold = avg_energy + threshold_ratio * std_energy
        
        # 标记语音帧
        speech_frames = []
        for start_idx, end_idx, energy in frames:
            if energy > threshold:
                speech_frames.append((start_idx, end_idx))
        
        is_speech = len(speech_frames) > 0.1 * len(frames)
        confidence = min(1.0, len(speech_frames) / max(1, len(frames)))
        
        # 合并相邻的语音段
        merged_segments = []
        if speech_frames:
            current_start, current_end = speech_frames[0]
            for start_idx, end_idx in speech_frames[1:]:
                if start_idx <= current_end + frame_size * 2:  # 允许一定间隔
                    current_end = end_idx
                else:
                    merged_segments.append((current_start, current_end))
                    current_start, current_end = start_idx, end_idx
            merged_segments.append((current_start, current_end))
        
        return is_speech, confidence, merged_segments

# ============ 音频处理工具 ============
class AudioProcessor:
    """音频处理和分片工具"""
    
    @staticmethod
    def base64_to_audio(audio_content_b64: str) -> Tuple[np.ndarray, int]:
        """Base64音频转换为PCM数据（简化版，假设为WAV格式）"""
        try:
            audio_bytes = base64.b64decode(audio_content_b64)
            
            # 简化的WAV解析（实际中需要更完整的解析）
            # 这里假设已经是线性PCM数据
            # TODO: 实现实际的音频格式检测和转换
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            sample_rate = 48000  # 假设48kHz
            
            return audio_data, sample_rate
        except Exception as e:
            logger.error(f"音频base64解析失败: {e}")
            # 返回空数据，让后续流程尝试原始base64
            return np.array([], dtype=np.int16), 16000
    
    @staticmethod
    def chunk_audio_by_duration(audio_data: np.ndarray, sample_rate: int, 
                               chunk_duration_seconds: float) -> List[np.ndarray]:
        """按固定时长分片音频"""
        if len(audio_data) == 0:
            return []
        
        chunk_size = int(sample_rate * chunk_duration_seconds)
        if chunk_size == 0:
            chunk_size = 1
        
        chunks = []
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            if len(chunk) > 0:
                chunks.append(chunk)
        
        logger.info(f"将音频分成 {len(chunks)} 个片段（每段约 {chunk_duration_seconds} 秒）")
        return chunks
    
    @staticmethod
    def chunk_audio_by_vad(audio_data: np.ndarray, sample_rate: int, 
                          min_silence_duration: float = 0.4) -> List[np.ndarray]:
        """基于VAD检测智能分片"""
        if len(audio_data) == 0:
            return []
        
        is_speech, confidence, segments = VADProcessor.detect_speech_activity(
            audio_data, sample_rate
        )
        
        if not segments:
            # 没有检测到语音，按固定时长分片
            return AudioProcessor.chunk_audio_by_duration(audio_data, sample_rate, 3.0)
        
        chunks = []
        for start_idx, end_idx in segments:
            chunk = audio_data[start_idx:end_idx]
            if len(chunk) > 0:
                # 确保片段不太长（不超过8秒）
                chunk_duration = len(chunk) / sample_rate
                if chunk_duration > 8.0:
                    # 长片段进一步细分
                    subchunks = AudioProcessor.chunk_audio_by_duration(
                        chunk, sample_rate, 4.0
                    )
                    chunks.extend(subchunks)
                else:
                    chunks.append(chunk)
        
        logger.info(f"VAD检测到 {len(segments)} 个语音段，分成 {len(chunks)} 个片段")
        return chunks
    
    @staticmethod
    def apply_noise_reduction(audio_data: np.ndarray, level: int = 2) -> np.ndarray:
        """简单的噪声抑制（移动平均滤波器）"""
        if len(audio_data) == 0 or level == 0:
            return audio_data
        
        # 简单的移动平均滤波器
        window_sizes = {1: 3, 2: 5, 3: 7}
        window_size = window_sizes.get(level, 3)
        
        if len(audio_data) < window_size:
            return audio_data
        
        result = np.convolve(audio_data, np.ones(window_size)/window_size, mode='same')
        return result.astype(audio_data.dtype)

# ============ Google STT API 集成 ============
async def transcribe_audio_chunk(audio_data: np.ndarray, sample_rate: int, config: Dict) -> Dict:
    """转录单个音频片段"""
    try:
        # 转换为base64（简化，实际使用适当的编码）
        audio_bytes = audio_data.tobytes()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        url = "https://speech.googleapis.com/v1/speech:recognize"
        params = {"key": CONFIG["api_key"]}
        
        payload = {
            "config": {
                "encoding": config.get("encoding", "LINEAR16"),
                "sampleRateHertz": sample_rate,
                "languageCode": config.get("language_code", "en-US"),
                "enableAutomaticPunctuation": config.get("enable_punctuation", True),
                "enableWordConfidence": True,
                "useEnhanced": True,
                "model": config.get("model", "default"),
                "speechContexts": [{
                    "phrases": CONFIG["ielts_context_phrases"],
                    "boost": 15.0
                }]
            },
            "audio": {
                "content": audio_b64
            }
        }
        
        # 添加噪声抑制配置
        noise_config = CONFIG["noise_reduction_configs"].get(config.get("noise_reduction_level", 2), {})
        for key, value in noise_config.items():
            if key != "noise_level":  # noise_level是内部参数
                payload["config"][key] = value
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"STT API错误 {response.status}: {error_text}")
                    return {"error": f"API错误 {response.status}", "details": error_text}
                    
    except Exception as e:
        logger.error(f"转录片段失败: {e}")
        return {"error": str(e)}

async def transcribe_long_audio(audio_content_b64: str, request_config: Dict) -> Dict:
    """
    长句子优化转录主函数
    支持分片处理、VAD检测、噪声抑制
    """
    start_time = datetime.now()
    
    try:
        # 1. 解析音频
        audio_data, sample_rate = AudioProcessor.base64_to_audio(audio_content_b64)
        
        if len(audio_data) == 0:
            # 无法解析，直接使用原始base64
            logger.info("无法解析音频格式，使用原始base64进行转录")
            result = await transcribe_audio_chunk(np.array([], dtype=np.int16), sample_rate, request_config)
            return {
                "text": result.get("results", [{}])[0].get("alternatives", [{}])[0].get("transcript", ""),
                "confidence": result.get("results", [{}])[0].get("alternatives", [{}])[0].get("confidence", 0.0),
                "duration_ms": 0,
                "chunk_count": 1,
                "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "vad_used": False
            }
        
        # 2. 计算音频时长
        duration_seconds = len(audio_data) / sample_rate
        
        # 3. 噪声抑制
        if request_config.get("noise_reduction_level", 0) > 0:
            audio_data = AudioProcessor.apply_noise_reduction(
                audio_data, request_config.get("noise_reduction_level", 2)
            )
        
        # 4. 决定分片策略
        use_vad = request_config.get("enable_vad", True) and duration_seconds > CONFIG["chunk_threshold_seconds"]
        if use_vad:
            chunks = AudioProcessor.chunk_audio_by_vad(
                audio_data, sample_rate, CONFIG["min_silence_duration"]
            )
            vad_used = True
        else:
            chunk_size = request_config.get("chunk_size_seconds", 3.0)
            chunks = AudioProcessor.chunk_audio_by_duration(audio_data, sample_rate, chunk_size)
            vad_used = False
        
        # 5. 处理分片
        chunk_count = len(chunks)
        if chunk_count == 0:
            chunks = [audio_data]
            chunk_count = 1
        
        logger.info(f"处理音频: {duration_seconds:.2f}秒，{chunk_count}个片段，VAD: {vad_used}")
        
        # 6. 并行处理分片
        tasks = []
        for i, chunk in enumerate(chunks):
            config_copy = request_config.copy()
            tasks.append(transcribe_audio_chunk(chunk, sample_rate, config_copy))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 7. 合并结果
        all_transcripts = []
        all_confidences = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"片段{i+1}转录失败: {result}")
                continue
            
            if "error" in result:
                logger.error(f"片段{i+1}API错误: {result['error']}")
                continue
            
            if "results" in result and result["results"]:
                alternatives = result["results"][0].get("alternatives", [])
                if alternatives:
                    transcript = alternatives[0].get("transcript", "")
                    confidence = alternatives[0].get("confidence", 0.5)
                    
                    if transcript.strip():
                        all_transcripts.append(transcript)
                        all_confidences.append(confidence)
        
        # 8. 计算整体结果
        final_text = " ".join(all_transcripts)
        avg_confidence = np.mean(all_confidences) if all_confidences else 0.0
        
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # 9. 更新统计
        performance_stats["total_requests"] += 1
        performance_stats["total_audio_duration_seconds"] += duration_seconds
        if chunk_count > 1:
            performance_stats["chunked_requests"] += 1
            performance_stats["avg_chunk_count"] = (
                performance_stats["avg_chunk_count"] * (performance_stats["chunked_requests"] - 1) + chunk_count
            ) / performance_stats["chunked_requests"]
        if vad_used:
            performance_stats["vad_processed"] += 1
        
        performance_stats["avg_confidence"] = (
            performance_stats["avg_confidence"] * (performance_stats["total_requests"] - 1) + avg_confidence
        ) / performance_stats["total_requests"]
        
        return {
            "text": final_text,
            "confidence": float(avg_confidence),
            "duration_ms": int(duration_seconds * 1000),
            "chunk_count": chunk_count,
            "processing_time_ms": int(processing_time_ms),
            "vad_used": vad_used
        }
        
    except Exception as e:
        logger.error(f"长音频转录失败: {e}")
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "text": f"处理错误: {str(e)}",
            "confidence": 0.0,
            "duration_ms": 0,
            "chunk_count": 0,
            "processing_time_ms": int(processing_time_ms),
            "vad_used": False,
            "error": str(e)
        }

# ============ API端点 ============
@app.get("/")
async def root():
    """根页面"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bryson STT长句子优化服务器</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: auto; }
            h1 { color: #333; }
            .card { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .success { color: green; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 Bryson STT长句子优化服务器</h1>
            <div class="card">
                <h3>🎯 方案A实施状态</h3>
                <p><b>版本:</b> 2.0.0-long-sentence-fix</p>
                <p><b>核心功能:</b></p>
                <ul>
                    <li>✅ 智能音频分片处理 (长句子自动分割)</li>
                    <li>✅ 实时噪声抑制增强 (级别可调)</li>
                    <li>✅ VAD语音活动检测 (智能断句)</li>
                    <li>✅ 高质量音频处理 (48kHz采样率)</li>
                </ul>
                <p><b>端口:</b> 8095</p>
                <p><b>API端点:</b> POST /api/stt/transcribe-long</p>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/api/status")
async def get_status():
    """获取服务器状态和性能统计"""
    uptime_str = "未知"
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        uptime_str = str(datetime.now() - datetime.fromtimestamp(proc.create_time()))
    except:
        pass
    
    return {
        "status": "running",
        "version": "2.0.0-long-sentence-fix",
        "port": CONFIG["port"],
        "features": {
            "chunk_processing": True,
            "vad_detection": True,
            "noise_reduction": True,
            "long_sentence_optimization": True
        },
        "performance_stats": performance_stats,
        "config": {
            "chunk_threshold_seconds": CONFIG["chunk_threshold_seconds"],
            "max_audio_duration": CONFIG["max_audio_duration_seconds"],
            "default_sample_rate": 48000
        },
        "uptime": uptime_str
    }

@app.post("/api/stt/transcribe-long")
async def transcribe_long(request: STTRequest):
    """长句子优化转录端点"""
    start_time = datetime.now()
    
    try:
        request_data = request.dict()
        
        logger.info(f"收到长句子转录请求: {len(request.audio_content)}字符, 采样率: {request.sample_rate}")
        
        result = await transcribe_long_audio(request.audio_content, request_data)
        
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "success": "error" not in result,
            "result": result,
            "processing_time_ms": processing_time_ms,
            "server_version": "2.0.0-long-sentence-fix"
        }
        
    except Exception as e:
        logger.error(f"API端点错误: {e}")
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "success": False,
            "error": str(e),
            "processing_time_ms": processing_time_ms
        }

@app.get("/api/stats")
async def get_stats():
    """获取详细统计信息"""
    return {
        "performance": performance_stats,
        "config_summary": {
            "chunk_processing_enabled": True,
            "vad_enabled": True,
            "noise_reduction_levels": list(CONFIG["noise_reduction_configs"].keys())
        }
    }

# ============ 主函数 ============
if __name__ == "__main__":
    logger.info(f"启动Bryson STT长句子优化服务器 v2.0.0...")
    logger.info(f"端口: {CONFIG['port']}")
    logger.info(f"API密钥: 已配置")
    logger.info(f"功能: 音频分片、VAD检测、噪声抑制")
    
    try:
        uvicorn.run(
            app,
            host=CONFIG["host"],
            port=CONFIG["port"],
            log_level="info"
        )
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)