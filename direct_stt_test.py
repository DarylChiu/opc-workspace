#!/usr/bin/env python3
"""
直接测试STT API，忽略TTS错误
"""

import json
import base64
import requests
from pathlib import Path

def test_stt_directly():
    # 新API密钥
    api_key = "AIzaSyDUwxtaIAuXXTKwuyabGzBYFYC3-eaIw0A"
    print(f"🔑 使用API密钥: {api_key[:10]}...")
    
    # 找一个简单的音频文件
    audio_file = Path("test_audio/ielts_benchmark/beginner/sample_001.mp3")
    if not audio_file.exists():
        print(f"❌ 找不到音频文件: {audio_file}")
        return False
    
    print(f"🎵 测试音频: {audio_file.name}")
    
    # 读取音频
    with open(audio_file, 'rb') as f:
        audio_content = f.read()
    
    audio_b64 = base64.b64encode(audio_content).decode('utf-8')
    
    # STT API请求
    url = "https://speech.googleapis.com/v1/speech:recognize"
    params = {"key": api_key}
    
    data = {
        "config": {
            "encoding": "MP3",
            "sampleRateHertz": 16000,
            "languageCode": "en-US",
            "enableAutomaticPunctuation": True,
            "model": "default"
        },
        "audio": {
            "content": audio_b64
        }
    }
    
    try:
        print("📡 发送STT API请求...")
        response = requests.post(url, params=params, json=data, timeout=30)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if "results" in result and result["results"]:
                transcription = ""
                for result_obj in result["results"]:
                    if "alternatives" in result_obj:
                        transcription += result_obj["alternatives"][0]["transcript"] + " "
                
                print(f"✅ STT转写成功！")
                print(f"🔊 转写结果: {transcription.strip()}")
                
                # 获取原文对比
                metadata_path = Path("test_audio/ielts_benchmark/metadata.json")
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    if "samples" in metadata:
                        for sample in metadata["samples"]:
                            if sample.get("audio_file", "").endswith(f"beginner/{audio_file.name}"):
                                original_text = sample.get("text", "")
                                print(f"📝 原文: {original_text}")
                                break
                
                return True, transcription.strip(), result
            else:
                print("⚠️  API返回空结果")
                if result:
                    print(f"   响应: {json.dumps(result, indent=2)[:500]}...")
                return False, "空结果", result
        
        else:
            print(f"❌ STT API错误: {response.status_code}")
            if response.text:
                try:
                    error = response.json()
                    print(f"📋 错误详情:")
                    print(json.dumps(error, indent=2))
                except:
                    print(f"   响应: {response.text[:500]}...")
            return False, f"API错误 {response.status_code}", None
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False, f"请求失败: {str(e)}", None

def main():
    print("🎤 直接STT API测试")
    print("="*50)
    
    success, transcription, result = test_stt_directly()
    
    print("\n" + "="*50)
    print("📊 测试总结")
    print("="*50)
    
    if success:
        print("🎉 STT API工作正常！")
        print(f"   转写: {transcription}")
        
        # 创建成功报告
        report = {
            "status": "SUCCESS",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "api_key_prefix": "AIzaSyDUwx",
            "transcription": transcription,
            "recommendation": "立即创建Google STT测试界面"
        }
        
        with open("stt_success_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("\n🚀 下一步:")
        print("1. 创建Google STT测试HTML界面")
        print("2. 更新现有服务器或创建新服务器")
        print("3. 配置ngrok外部访问")
        print("4. 发送测试URL给用户")
        
    else:
        print("❌ STT API测试失败")
        
        # 检查是否需要启用API
        if result and "error" in result:
            error = result.get("error", {})
            if error.get("details"):
                for detail in error["details"]:
                    if isinstance(detail, dict) and detail.get("@type") == "type.googleapis.com/google.rpc.ErrorInfo":
                        if detail.get("reason") == "API_KEY_SERVICE_BLOCKED":
                            print("\n🔧 问题诊断:")
                            print("   API密钥被阻止访问Speech-to-Text API")
                            print("")
                            print("💡 解决方案:")
                            print("1. 访问Google Cloud Console")
                            print("2. 确保启用了Speech-to-Text API")
                            print("3. 检查API密钥限制设置")
                            print("4. 确保API密钥允许访问该API")
        
        print("\n📋 请用户检查:")
        print("1. 访问: https://console.cloud.google.com/apis/library/speech.googleapis.com")
        print("2. 点击'启用'按钮（如果未启用）")
        print("3. 访问: https://console.cloud.google.com/apis/credentials")
        print("4. 找到API密钥，点击'编辑'")
        print("5. 在'API限制'中确保包含'Cloud Speech-to-Text API'")

if __name__ == "__main__":
    main()