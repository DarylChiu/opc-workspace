#!/usr/bin/env python3
"""
修复STT编码格式问题
"""

import json
import base64
import requests

def test_audio_formats():
    """测试不同音频编码格式"""
    api_key = "AIzaSyDUwxtaIAuXXTKwuyabGzBYFYC3-eaIw0A"
    url = "https://speech.googleapis.com/v1/speech:recognize"
    
    # 测试不同的编码格式
    formats = [
        "LINEAR16",      # PCM 16-bit
        "FLAC",          # FLAC
        "MULAW",         # μ-law
        "AMR",           # Adaptive Multi-Rate
        "AMR_WB",        # AMR Wideband
        "OGG_OPUS",      # Ogg Opus
        "WEBM_OPUS",     # WebM Opus
        "MP3",           # MP3
        "WAV"            # WAV (实际上应该是LINEAR16)
    ]
    
    print("🔍 测试Google STT API支持的编码格式...")
    
    # 创建一个简单的测试音频（静音）
    # 实际上我们需要一个真实的音频文件来测试
    # 先测试API密钥有效性
    
    test_data = {
        "config": {
            "encoding": "LINEAR16",
            "sampleRateHertz": 16000,
            "languageCode": "en-US",
            "enableAutomaticPunctuation": True
        },
        "audio": {
            "content": base64.b64encode(b"\x00" * 1000).decode('utf-8')  # 简单的静音
        }
    }
    
    for encoding in formats:
        test_data["config"]["encoding"] = encoding
        try:
            response = requests.post(
                url,
                params={"key": api_key},
                json=test_data,
                timeout=10
            )
            
            print(f"\n格式: {encoding}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if "results" in result:
                    print("✅ 格式支持: 是")
                    if result.get("results"):
                        print(f"   结果: {result['results']}")
                    else:
                        print(f"   结果: 空（可能是音频内容无效）")
                else:
                    print("❌ 格式支持: 可能不支持")
                    print(f"   响应: {response.text[:200]}")
            else:
                print(f"❌ 错误: HTTP {response.status_code}")
                print(f"   响应: {response.text[:200]}")
                
        except Exception as e:
            print(f"\n格式: {encoding}")
            print(f"❌ 异常: {str(e)}")

def check_google_stt_docs():
    """检查Google STT支持的编码格式"""
    print("\n📚 Google Cloud Speech-to-Text 支持的编码格式:")
    print("=" * 60)
    print("1. LINEAR16 - PCM 16-bit (最常用)")
    print("2. FLAC - 无损压缩")
    print("3. MULAW - μ-law 8-bit")
    print("4. AMR - Adaptive Multi-Rate")
    print("5. AMR_WB - AMR Wideband")
    print("6. OGG_OPUS - Ogg Opus 容器")
    print("7. WEBM_OPUS - WebM Opus 容器")
    print("8. MP3 - MPEG-1/2 Audio Layer III")
    print("9. WAV - 实际上使用LINEAR16")
    print("\n⚠️  注意:")
    print("- WEBM_OPUS 需要Opus编解码器")
    print("- 浏览器录音通常是Opus编码的WebM")
    print("- 可能需要转换编码格式")
    print("\n🔧 建议解决方案:")
    print("1. 前端: 使用MediaRecorder的audio/webm;codecs=opus")
    print("2. 后端: 尝试多种编码格式")
    print("3. 或使用音频转换库")

def create_fixed_stt_function():
    """创建修复后的STT转换函数"""
    fixed_code = '''
def transcribe_audio_fixed(audio_content_b64: str, api_key: str, config: Dict) -> Dict:
    """
    修复后的STT转换函数，支持多种编码格式
    """
    try:
        url = "https://speech.googleapis.com/v1/speech:recognize"
        params = {"key": api_key}
        
        # 检测并修正编码格式
        encoding = config.get("encoding", "WEBM_OPUS")
        
        # Google STT对WebM Opus的支持可能有问题，尝试自动转换
        if encoding == "WEBM_OPUS":
            # 尝试WebM Opus，如果不成功则尝试其他格式
            encodings_to_try = ["WEBM_OPUS", "OGG_OPUS", "MP3", "LINEAR16"]
        elif encoding == "audio/webm":
            encodings_to_try = ["WEBM_OPUS", "OGG_OPUS", "MP3", "LINEAR16"]
        else:
            encodings_to_try = [encoding]
        
        last_error = None
        last_response = None
        
        for attempt_encoding in encodings_to_try:
            try:
                data = {
                    "config": {
                        "encoding": attempt_encoding,
                        "sampleRateHertz": config.get("sample_rate", 16000),
                        "languageCode": config.get("language_code", "en-US"),
                        "enableAutomaticPunctuation": config.get("enable_punctuation", True),
                        "model": config.get("model", "default"),
                        "useEnhanced": config.get("use_enhanced", True),
                        "speechContexts": [{
                            "phrases": [
                                "IELTS", "speaking", "test", "practice",
                                "introduction", "hometown", "education", "work",
                                "business", "investment", "presentation",
                                "hello", "my name is", "I am", "thank you",
                                "good morning", "good afternoon", "how are you"
                            ],
                            "boost": 15.0
                        }]
                    },
                    "audio": {
                        "content": audio_content_b64
                    }
                }
                
                logger.info(f"尝试编码格式: {attempt_encoding}")
                response = requests.post(url, params=params, json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "results" in result and result["results"]:
                        transcription = ""
                        max_confidence = 0.0
                        
                        for result_obj in result["results"]:
                            if "alternatives" in result_obj:
                                for alt in result_obj["alternatives"]:
                                    transcription += alt["transcript"] + " "
                                    if "confidence" in alt and alt["confidence"] > max_confidence:
                                        max_confidence = alt["confidence"]
                        
                        return {
                            "success": True,
                            "transcription": transcription.strip(),
                            "confidence": max_confidence,
                            "language_code": config.get("language_code"),
                            "encoding_used": attempt_encoding,
                            "raw_response": result
                        }
                    else:
                        last_response = result
                        logger.warning(f"编码 {attempt_encoding}: API返回空结果")
                        continue
                else:
                    error_text = response.text[:200] if response.text else "无错误信息"
                    logger.warning(f"编码 {attempt_encoding}: HTTP {response.status_code} - {error_text}")
                    last_error = f"HTTP {response.status_code}"
                    continue
                    
            except Exception as e:
                logger.warning(f"编码 {attempt_encoding} 尝试失败: {str(e)}")
                last_error = str(e)
                continue
        
        # 所有编码格式都失败
        return {
            "success": False,
            "error": f"所有编码格式尝试失败。最后错误: {last_error}",
            "language_code": config.get("language_code"),
            "suggestions": [
                "尝试使用LINEAR16 (PCM) 格式",
                "检查音频样本率是否为16000Hz",
                "确保音频内容不为空",
                "检查API密钥是否有配额限制"
            ]
        }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"STT处理异常: {str(e)}"
        }
'''
    return fixed_code

def main():
    print("🔧 STT编码格式问题诊断与修复")
    print("=" * 60)
    
    # 测试API密钥
    print("\n1. 测试API密钥有效性...")
    api_key = "AIzaSyDUwxtaIAuXXTKwuyabGzBYFYC3-eaIw0A"
    test_url = "https://speech.googleapis.com/v1/speech:recognize"
    
    test_data = {
        "config": {
            "encoding": "LINEAR16",
            "sampleRateHertz": 16000,
            "languageCode": "en-US"
        },
        "audio": {
            "content": base64.b64encode(b"\x00" * 1000).decode('utf-8')
        }
    }
    
    try:
        response = requests.post(test_url, params={"key": api_key}, json=test_data, timeout=10)
        print(f"✅ API密钥测试状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ API密钥有效")
        else:
            print(f"⚠️  API密钥可能有问题: {response.text[:200]}")
    except Exception as e:
        print(f"❌ API密钥测试失败: {e}")
    
    # 显示支持的编码格式
    check_google_stt_docs()
    
    # 生成修复代码
    print("\n🔧 修复后的transcribe_audio函数:")
    print("=" * 60)
    print(create_fixed_stt_function())
    
    print("\n🎯 建议修复步骤:")
    print("1. 替换STT_QUICK_FIX.py中的transcribe_audio函数")
    print("2. 重启服务器")
    print("3. 前端也更新编码格式为LINEAR16")
    print("4. 添加环境噪音过滤选项")

if __name__ == "__main__":
    main()