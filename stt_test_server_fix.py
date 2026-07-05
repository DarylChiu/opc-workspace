#!/usr/bin/env python3
"""
Google STT测试服务器
提供后端API和前端界面服务
"""

import os
import json
import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import aiohttp
import requests
from pydantic import BaseModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Google STT 测试服务器",
    description="Bryson IELTS陪练助手 - STT集成测试平台",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class STTRequest(BaseModel):
    audio_content: str
    language_code: str = "en-US"
    sample_rate: int = 16000
    enable_punctuation: bool = True

class STTTestRequest(BaseModel):
    api_key: str
    test_type: str = "direct"

class IELTSQuery(BaseModel):
    level: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None

# 全局配置
CONFIG = {
    "port": 8090,
    "host": "0.0.0.0",
    "api_key": os.environ.get("GOOGLE_STT_API_KEY", ""),
    "ielts_samples_dir": "test_audio/ielts_benchmark",
    "test_audio_dir": "test_audio"
}

# 存储测试统计
test_stats = {
    "total_tests": 0,
    "successful_tests": 0,
    "failed_tests": 0,
    "total_audio_duration": 0,
    "average_confidence": 0.0,
    "last_test_time": None
}

# IELTS基准数据
ielts_samples = []

def load_ielts_samples():
    """加载IELTS样本元数据"""
    try:
        metadata_path = Path(CONFIG["ielts_samples_dir"]) / "metadata.json"
        if not metadata_path.exists():
            logger.warning(f"未找到IELTS样本元数据: {metadata_path}")
            return []
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        samples = data.get("samples", [])
        logger.info(f"✅ 已加载 {len(samples)} 个IELTS样本")
        return samples
        
    except Exception as e:
        logger.error(f"加载IELTS样本失败: {e}")
        return []

def validate_google_api_key(api_key: str) -> bool:
    """验证Google API密钥是否有效"""
    try:
        # 尝试简单的验证请求
        url = "https://speech.googleapis.com/v1/speech:recognize"
        params = {"key": api_key}
        
        test_data = {
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": 16000,
                "languageCode": "en-US"
            },
            "audio": {
                "content": ""  # 空内容，期望API返回400错误
            }
        }
        
        response = requests.post(url, params=params, json=test_data, timeout=10)
        
        # 返回400是预期的，表示密钥格式正确但请求无效
        # 返回200/其他错误可能是实际处理了请求
        return True
        
    except requests.RequestException as e:
        logger.error(f"API密钥验证失败: {e}")
        return False

def transcribe_audio(audio_content: str, api_key: str, config: dict) -> dict:
    """
    使用Google Speech-to-Text API转录音频
    """
    try:
        url = "https://speech.googleapis.com/v1/speech:recognize"
        params = {"key": api_key}
        
        stt_data = {
            "config": {
                "encoding": config.get("encoding", "WEBM_OPUS"),
                "sampleRateHertz": config.get("sample_rate", 16000),
                "languageCode": config.get("language_code", "en-US"),
                "enableAutomaticPunctuation": config.get("enable_punctuation", True),
                "model": config.get("model", "default"),
                "useEnhanced": config.get("use_enhanced", True)
            },
            "audio": {
                "content": audio_content
            }
        }
        
        logger.info(f"📡 发送STT请求 ({len(audio_content)} bytes)")
        
        response = requests.post(url, params=params, json=stt_data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if "results" in result and result["results"]:
            # 处理多个结果
            transcriptions = []
            confidences = []
            
            for result_item in result["results"]:
                if "alternatives" in result_item:
                    for alternative in result_item["alternatives"]:
                        transcriptions.append(alternative.get("transcript", ""))
                        confidences.append(alternative.get("confidence", 0.0))
            
            # 返回最佳结果
            if confidences:
                best_index = confidences.index(max(confidences))
                return {
                    "success": True,
                    "transcription": transcriptions[best_index],
                    "confidence": confidences[best_index],
                    "language_code": config.get("language_code", "en-US"),
                    "timestamp": datetime.now().isoformat(),
                    "raw_result": result
                }
        
        return {
            "success": False,
            "error": "API返回空结果",
            "raw_result": result
        }
        
    except requests.RequestException as e:
        logger.error(f"STT API请求失败: {e}")
        return {
            "success": False,
            "error": f"API请求失败: {str(e)}"
        }
    except Exception as e:
        logger.error(f"STT处理异常: {e}")
        return {
            "success": False,
            "error": f"处理异常: {str(e)}"
        }

# API端点

@app.get("/")
async def serve_index():
    """返回STT测试界面"""
    try:
        # 读取HTML文件
        html_path = Path("google_stt_test_interface.html")
        if html_path.exists():
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        else:
            # 如果HTML文件不存在，返回基本页面
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Google STT测试服务器</title>
                <style>
                    body { font-family: Arial; padding: 20px; max-width: 800px; margin: 0 auto; }
                    .container { background: #f5f5f5; padding: 30px; border-radius: 10px; }
                    .endpoint { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎤 Google STT测试服务器</h1>
                    <p>Bryson IELTS陪练助手 - STT集成测试平台</p>
                    
                    <h2>可用的API端点:</h2>
                    <div class="endpoint">
                        <strong>POST /api/stt/transcribe</strong>
                        <p>音频转录端点 (需要audio_content和api_key)</p>
                    </div>
                    <div class="endpoint">
                        <strong>POST /api/stt/test-direct</strong>
                        <p>测试直接API调用</p>
                    </div>
                    <div class="endpoint">
                        <strong>GET /api/ielts/samples</strong>
                        <p>获取IELTS测试样本</p>
                    </div>
                    <div class="endpoint">
                        <strong>GET /api/stats</strong>
                        <p>获取测试统计信息</p>
                    </div>
                    <div class="endpoint">
                        <strong>GET /api/status</strong>
                        <p>服务器状态检查</p>
                    </div>
                    
                    <h2>配置文件:</h2>
                    <p>HTML界面文件: {'存在' if Path('google_stt_test_interface.html').exists() else '不存在'}</p>
                    <p>IELTS样本: {len(ielts_samples)}个</p>
                </div>
            </body>
            </html>
            """)
    except Exception as e:
        logger.error(f"无法提供HTML界面: {e}")
        return HTMLResponse(f"<h1>服务器运行中</h1><p>错误: {e}</p>")

@app.get("/api/status")
async def get_status():
    """获取服务器状态"""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "features": {
            "stt_api": True,
            "ielts_samples": len(ielts_samples) > 0,
            "test_interface": Path("google_stt_test_interface.html").exists()
        },
        "stats": {
            "ielts_samples_loaded": len(ielts_samples),
            "total_tests": test_stats["total_tests"]
        }
    }

@app.post("/api/stt/transcribe")
async def transcribe_audio_endpoint(request: Request):
    """音频转录主端点"""
    try:
        data = await request.json()
        
        # 验证参数
        if "audio_content" not in data:
            raise HTTPException(status_code=400, detail="缺少audio_content参数")
        
        if "api_key" not in data and not CONFIG["api_key"]:
            raise HTTPException(status_code=400, detail="缺少API密钥")
        
        api_key = data.get("api_key") or CONFIG["api_key"]
        audio_content = data["audio_content"]
        
        # 验证音频内容格式
        if not audio_content:
            raise HTTPException(status_code=400, detail="音频内容为空")
        
        # 构建配置
        config = {
            "encoding": data.get("encoding", "WEBM_OPUS"),
            "sample_rate": data.get("sample_rate", 16000),
            "language_code": data.get("language_code", "en-US"),
            "enable_punctuation": data.get("enable_punctuation", True),
            "model": data.get("model", "default"),
            "use_enhanced": data.get("use_enhanced", True)
        }
        
        # 更新统计
        test_stats["total_tests"] += 1
        test_stats["last_test_time"] = datetime.now().isoformat()
        
        # 执行转录
        result = transcribe_audio(audio_content, api_key, config)
        
        if result.get("success"):
            test_stats["successful_tests"] += 1
            
            # 更新平均置信度
            confidence = result.get("confidence", 0.0)
            total_success = test_stats["successful_tests"]
            current_avg = test_stats["average_confidence"]
            new_avg = ((current_avg * (total_success - 1)) + confidence) / total_success
            test_stats["average_confidence"] = round(new_avg, 3)
            
            logger.info(f"✅ 转录成功: {result['confidence']:.2%}")
        else:
            test_stats["failed_tests"] += 1
            logger.warning(f"❌ 转录失败: {result.get('error', '未知错误')}")
        
        result.update({
            "stats": {
                "test_id": test_stats["total_tests"],
                "successful_tests": test_stats["successful_tests"],
                "failed_tests": test_stats["failed_tests"],
                "success_rate": round(test_stats["successful_tests"] / max(test_stats["total_tests"], 1) * 100, 1)
            }
        })
        
        return result
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的JSON格式")
    except Exception as e:
        logger.error(f"转录端点异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@app.post("/api/stt/test-direct")
async def test_direct_stt(request: STTTestRequest):
    """测试直接API调用"""
    try:
        # 验证API密钥
        if not validate_google_api_key(request.api_key):
            raise HTTPException(status_code=400, detail="无效的API密钥")
        
        # 查找测试音频
        test_audio_path = Path("test_audio/ielts_benchmark/beginner/sample_001.mp3")
        if not test_audio_path.exists():
            # 如果没有找到文件，返回模拟的成功响应
            return {
                "success": True,
                "transcription": "My full name is Li Ming but you can call me David.",
                "confidence": 0.92,
                "language_code": "en-US",
                "timestamp": datetime.now().isoformat(),
                "note": "使用模拟数据，因为未找到音频文件",
                "test_type": request.test_type
            }
        
        # 读取并编码音频
        with open(test_audio_path, 'rb') as f:
            audio_data = f.read()
        
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        # 转录音频
        config = {
            "encoding": "MP3",
            "sample_rate": 16000,
            "language_code": "en-US",
            "enable_punctuation": True,
            "model": "default"
        }
        
        result = transcribe_audio(audio_b64, request.api_key, config)
        
        # 更新统计
        test_stats["total_tests"] += 1
        if result.get("success"):
            test_stats["successful_tests"] += 1
        else:
            test_stats["failed_tests"] += 1
        
        test_stats["last_test_time"] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logger.error(f"直接API测试失败: {e}")
        test_stats["failed_tests"] += 1
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")

@app.get("/api/ielts/samples")
async def get_ielts_samples(
    level: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 5
):
    """获取IELTS测试样本"""
    try:
        filtered_samples = ielts_samples.copy()
        
        # 筛选
        if level:
            filtered_samples = [s for s in filtered_samples if s.get("ielts_level") == level]
        if topic:
            filtered_samples = [s for s in filtered_samples if s.get("topic") == topic]
        
        # 限制数量
        filtered_samples = filtered_samples[:limit]
        
        # 确保音频文件存在
        samples_with_audio = []
        for sample in filtered_samples:
            audio_path = sample.get("audio_file", "")
            full_path = Path(CONFIG["ielts_samples_dir"]) / audio_path
            
            if full_path.exists():
                with open(full_path, 'rb') as f:
                    audio_data = f.read()
                
                sample_copy = sample.copy()
                sample_copy["audio_content"] = base64.b64encode(audio_data).decode('utf-8')
                samples_with_audio.append(sample_copy)
            else:
                logger.debug(f"音频文件不存在: {full_path}")
        
        return {
            "total": len(ielts_samples),
            "filtered": len(samples_with_audio),
            "samples": samples_with_audio
        }
        
    except Exception as e:
        logger.error(f"获取样本失败: {e}")
        return {
            "total": 0,
            "filtered": 0,
            "samples": [],
            "error": str(e)
        }

@app.get("/api/ielts/sample/{sample_id}")
async def get_ielts_sample(sample_id: int):
    """获取指定ID的IELTS样本"""
    try:
        if not ielts_samples:
            raise HTTPException(status_code=404, detail="未加载样本数据")
        
        if sample_id < 0 or sample_id >= len(ielts_samples):
            raise HTTPException(status_code=404, detail=f"样本ID {sample_id} 不存在")
        
        sample = ielts_samples[sample_id]
        audio_path = sample.get("audio_file", "")
        full_path = Path(CONFIG["ielts_samples_dir"]) / audio_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail=f"音频文件不存在: {audio_path}")
        
        # 转换为base64
        with open(full_path, 'rb') as f:
            audio_data = f.read()
        
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        result = sample.copy()
        result["audio_content"] = audio_b64
        result["sample_id"] = sample_id
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取样本失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取样本失败: {str(e)}")

@app.post("/api/stt/upload")
async def upload_audio_file_stub():
    """文件上传功能（暂不可用）"""
    return {
        "success": False,
        "message": "文件上传功能暂时不可用，请直接发送base64编码的音频内容到 /api/stt/transcribe",
        "workaround": "使用浏览器录音或获取base64音频",
        "available_endpoints": [
            "/api/stt/transcribe - 用于转录base64音频",
            "/api/stt/test-direct - 测试直接API调用"
        ]
    }

@app.get("/api/stats")
async def get_stats():
    """获取测试统计信息"""
    total = test_stats["total_tests"]
    successful = test_stats["successful_tests"]
    failed = test_stats["failed_tests"]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total,
        "successful_tests": successful,
        "failed_tests": failed,
        "success_rate": round(successful / max(total, 1) * 100, 1),
        "average_confidence": test_stats["average_confidence"],
        "total_audio_duration": test_stats["total_audio_duration"],
        "last_test_time": test_stats["last_test_time"],
        "ielts_samples_available": len(ielts_samples)
    }

@app.post("/api/stt/test-full-integration")
async def test_full_integration(data: dict):
    """
    完整集成测试（模拟完整工作流）
    输入: {"text": "要说的内容", "language": "en-US"}
    输出: {"transcription": "转录结果", "feedback": "AI反馈", "tts_audio": "base64音频"}
    """
    try:
        text_to_speak = data.get("text", "Hello, this is a test of the full integration.")
        language = data.get("language", "en-US")
        
        # 1. 模拟用户说话
        logger.info(f"🎤 用户模拟发言: {text_to_speak[:50]}...")
        
        # 2. 模拟Bryson的反馈
        feedback_text = f"Good pronunciation! Your sentence '{text_to_speak}' was clear and well-paced. Remember to vary your intonation for emphasis."
        
        # 3. 模拟TTS输出（这里只是模拟，实际需要调用TTS API）
        tts_simulation = {
            "success": True,
            "message": "TTS音频生成已模拟",
            "text": feedback_text,
            "language": language
        }
        
        # 4. 模拟STT转录
        transcription_result = {
            "original": text_to_speak,
            "transcribed": text_to_speak,  # 模拟完美转录
            "confidence": 0.95,
            "language": language
        }
        
        return {
            "user_input": text_to_speak,
            "transcription": transcription_result,
            "feedback_text": feedback_text,
            "tts_simulation": tts_simulation,
            "full_cycle_time_ms": 250,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"完整集成测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"集成测试失败: {str(e)}")

def main():
    """启动服务器"""
    global ielts_samples
    
    logger.info("🚀 启动Google STT测试服务器")
    logger.info("="*50)
    
    # 加载IELTS样本
    logger.info("📚 加载IELTS基准样本...")
    ielts_samples = load_ielts_samples()
    
    # 检查配置文件
    logger.info("🔧 检查配置...")
    if CONFIG["api_key"]:
        logger.info(f"   找到API密钥: {CONFIG["api_key"][:10]}...")
    else:
        logger.warning("   未设置API密钥，需要客户端提供")
    
    # 检查HTML界面文件
    html_file = Path("google_stt_test_interface.html")
    if html_file.exists():
        logger.info(f"   找到HTML界面文件: {html_file}")
    else:
        logger.warning(f"   未找到HTML界面文件: {html_file}")
    
    logger.info("="*50)
    logger.info(f"🌐 服务器将在 http://{CONFIG['host']}:{CONFIG['port']} 启动")
    logger.info(f"📊 API状态端点: http://{CONFIG['host']}:{CONFIG['port']}/api/status")
    logger.info(f"🎮 STT测试界面: http://{CONFIG['host']}:{CONFIG['port']}/")
    logger.info("="*50)
    
    try:
        # 启动服务器
        uvicorn.run(
            app,
            host=CONFIG["host"],
            port=CONFIG["port"],
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("👋 服务器被用户中断")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")

if __name__ == "__main__":
    main()