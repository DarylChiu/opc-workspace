#!/usr/bin/env python3
"""
检查Google STT API密钥状态
"""

import requests
import base64
import json

# Google STT API密钥
GOOGLE_API_KEY = "AIzaSyDUwxtaIAuXXTKwuyabGzBYFYC3-eaIw0A"

def test_google_stt_simple():
    """简单测试Google STT API"""
    print("🧪 测试Google STT API密钥...")
    
    # 构造一个极短的测试音频（静音）
    # 创建一个极简的base64音频数据
    test_audio_base64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAgLsAAAB3AQACABAAZGF0YQAAAAA="
    
    stt_url = f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}"
    
    stt_request = {
        "config": {
            "encoding": "LINEAR16",
            "sampleRateHertz": 16000,
            "languageCode": "en-US",
            "model": "default",
        },
        "audio": {
            "content": test_audio_base64
        }
    }
    
    try:
        print(f"🔗 请求URL: {stt_url[:80]}...")
        response = requests.post(stt_url, json=stt_request, timeout=10)
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📋 响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Google STT API响应成功")
            print(f"📝 结果: {json.dumps(result, indent=2)[:500]}")
        elif response.status_code == 400:
            print("❌ Google STT API请求错误 (400)")
            try:
                error_data = response.json()
                print(f"⚠️  错误详情: {json.dumps(error_data, indent=2)}")
            except:
                print(f"⚠️  错误文本: {response.text}") 
        elif response.status_code == 403:
            print("❌ Google STT API认证失败 (403)")
            print("⚠️  可能原因: API密钥无效、配额不足或未启用Speech-to-Text API")
            try:
                error_data = response.json()
                print(f"🔍 错误详情: {json.dumps(error_data, indent=2)}")
            except:
                print(f"🔍 错误文本: {response.text}")
        else:
            print(f"❌ Google STT API其他错误: {response.status_code}")
            
    except Exception as e:
        print(f"💥 请求异常: {str(e)}")

def check_api_key_status():
    """检查API密钥基本状态"""
    print("\n🔑 检查API密钥基本信息...")
    
    # 测试简单请求获取错误信息
    test_url = f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}"
    
    # 故意发送错误请求以获取认证状态
    bad_request = {"bad": "request"}
    
    try:
        response = requests.post(test_url, json=bad_request, timeout=10)
        print(f"测试响应状态码: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ API密钥可以访问服务（返回400是正常的，因为我们发送了错误请求）")
            try:
                error_data = response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    print(f"📋 服务消息: {error_data['error']['message']}")
            except:
                print("📋 解析响应失败")
        elif response.status_code == 403:
            print("❌ API密钥认证失败")
        else:
            print(f"⚠️  未知响应: {response.status_code}")
            
    except Exception as e:
        print(f"💥 检查失败: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("Google STT API密钥诊断工具")
    print("=" * 60)
    
    test_google_stt_simple()
    check_api_key_status()
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)