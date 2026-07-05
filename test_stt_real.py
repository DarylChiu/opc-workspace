#!/usr/bin/env python3
"""
测试实际的STT功能
"""

import requests
import base64
import json
import os

GOOGLE_API_KEY = "AIzaSyDUwxtaIAuXXTKwuyabGzBYFYC3-eaIw0A"

def test_with_real_mp3():
    """使用真实MP3文件测试"""
    print("🎵 测试真实MP3文件...")
    
    # 读取MP3文件
    mp3_path = "test_audio/ielts_benchmark/advanced/sample_087.mp3"
    
    if not os.path.exists(mp3_path):
        print(f"❌ 文件不存在: {mp3_path}")
        return
    
    with open(mp3_path, 'rb') as f:
        audio_bytes = f.read()
    
    audio_base64 = base64.b64encode(audio_bytes).decode('ascii')
    print(f"📊 MP3文件大小: {len(audio_bytes)}字节")
    print(f"📊 Base64长度: {len(audio_base64)}字符")
    
    stt_url = f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}"
    
    # 尝试不同编码
    configs = [
        {
            "name": "MP3格式",
            "config": {
                "encoding": "MP3",  # MP3编码
                "sampleRateHertz": 48000,  # MP3通常是44.1k或48k
                "languageCode": "en-US",
                "model": "default",
                "useEnhanced": True,
            }
        },
        {
            "name": "LINEAR16格式（先转换）",
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": 16000,
                "languageCode": "en-US", 
                "model": "default",
            }
        }
    ]
    
    for config in configs:
        print(f"\n🔧 测试配置: {config['name']}")
        
        stt_request = {
            "config": config["config"],
            "audio": {
                "content": audio_base64
            }
        }
        
        try:
            response = requests.post(stt_url, json=stt_request, timeout=30)
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ STT成功!")
                if "results" in result and result["results"]:
                    for i, r in enumerate(result["results"]):
                        for alt in r.get("alternatives", []):
                            conf = alt.get("confidence", 0) * 100
                            print(f"  结果 {i+1}: '{alt.get('transcript', '')}' ({conf:.1f}%)")
                else:
                    print("⚠️  无识别结果")
                    print(f"详情: {json.dumps(result, indent=2)[:500]}")
            else:
                print(f"❌ 失败: {response.status_code}")
                print(f"错误: {response.text[:500]}")
                
        except Exception as e:
            print(f"💥 异常: {str(e)}")

def test_webm_simulation():
    """模拟WebRTC录制的WEBM格式"""
    print("\n🎤 模拟WebRTC WEBM格式测试...")
    
    # 创建一个极简的WEBM/Opus音频（使用实际录制的小音频）
    # 先检查是否有之前录制的测试文件
    test_files = ["test_recording.webm", "test_audio.webm", "recording_test.webm"]
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"🔍 找到测试文件: {test_file}")
            with open(test_file, 'rb') as f:
                audio_bytes = f.read()
            
            audio_base64 = base64.b64encode(audio_bytes).decode('ascii')
            print(f"📊 文件大小: {len(audio_bytes)}字节")
            
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
                    "content": audio_base64
                }
            }
            
            try:
                response = requests.post(stt_url, json=stt_request, timeout=30)
                print(f"📊 状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ WEBM_OPUS STT成功!")
                    if "results" in result and result["results"]:
                        for r in result["results"]:
                            for alt in r.get("alternatives", []):
                                conf = alt.get("confidence", 0) * 100
                                print(f"  识别结果: '{alt.get('transcript', '')}' ({conf:.1f}%)")
                else:
                    print(f"❌ WEBM_OPUS失败: {response.status_code}")
                    print(f"错误: {response.text[:300]}")
                    
            except Exception as e:
                print(f"💥 异常: {str(e)}")
            break
    else:
        print("⚠️  未找到WEBM测试文件，需要先录制")

def test_local_server():
    """测试本地服务器"""
    print("\n🌐 测试本地FastAPI服务器...")
    
    # 读取音频文件并转换为base64
    mp3_path = "test_audio/ielts_benchmark/advanced/sample_087.mp3"
    
    if os.path.exists(mp3_path):
        with open(mp3_path, 'rb') as f:
            audio_bytes = f.read()
        
        audio_base64 = base64.b64encode(audio_bytes).decode('ascii')
        
        request_data = {
            "audio": {
                "content": audio_base64
            }
        }
        
        try:
            response = requests.post(
                "http://localhost:8095/api/stt-simple",
                json=request_data,
                timeout=30
            )
            
            print(f"📊 本地服务器响应状态码: {response.status_code}")
            print(f"📋 响应内容: {response.text[:500]}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ 本地服务器STT成功: {result.get('text', '')}")
                else:
                    print(f"❌ 本地服务器STT失败: {result.get('error', 'Unknown')}")
            
        except Exception as e:
            print(f"💥 连接本地服务器失败: {str(e)}")
    else:
        print("⚠️  测试文件不存在")

if __name__ == "__main__":
    print("=" * 60)
    print("STT功能深度测试")
    print("=" * 60)
    
    test_with_real_mp3()
    test_webm_simulation()
    test_local_server()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)