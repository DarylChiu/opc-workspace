#!/usr/bin/env python3
"""
测试SSL修复后的TTS功能
"""

import os
import json
import ssl
import aiohttp
import asyncio

# 修复SSL证书问题
ssl._create_default_https_context = ssl._create_unverified_context

def load_google_tts_api_key():
    """加载Google TTS API密钥"""
    key_file = os.path.expanduser("~/.openclaw/auth/google/ielts_tts_2026.key")
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r') as f:
                return f.read().strip()
        except Exception as e:
            print(f"❌ 加载API密钥失败: {e}")
            return None
    else:
        print("❌ 未找到Google TTS API密钥文件")
        return None

async def test_tts(api_key):
    """测试TTS功能"""
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
    
    request_data = {
        "input": {"text": "Hello Daryl! This is a test to verify SSL certificate fix on macOS."},
        "voice": {
            "languageCode": "en-US",
            "name": "en-US-Standard-D",
            "ssmlGender": "MALE"
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": 0.9,
            "pitch": -2.0,
            "volumeGainDb": 3.0
        }
    }
    
    try:
        print("🔄 正在测试TTS连接...")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_data) as response:
                print(f"✅ HTTP状态码: {response.status}")
                
                if response.status == 200:
                    result_data = await response.json()
                    audio_content = result_data.get("audioContent")
                    if audio_content:
                        print("✅ TTS测试成功! 音频内容大小:", len(audio_content), "字符")
                        return True
                    else:
                        print("❌ TTS响应中无音频内容")
                        print("响应预览:", json.dumps(result_data)[:200])
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ TTS API错误: {response.status}")
                    print("错误详情:", error_text[:500])
                    return False
                    
    except Exception as e:
        print(f"❌ TTS请求异常: {type(e).__name__}: {e}")
        return False

async def main():
    """主测试函数"""
    print("🔧 SSL证书修复测试")
    print("=" * 50)
    
    # 1. 检查API密钥
    api_key = load_google_tts_api_key()
    if not api_key:
        print("❌ 无法加载API密钥")
        return False
    
    print(f"✅ API密钥已加载 (长度: {len(api_key)} 字符)")
    print(f"   密钥片段: {api_key[:20]}...")
    
    # 2. 测试TTS连接
    success = await test_tts(api_key)
    
    if success:
        print("=" * 50)
        print("🎉 SSL证书修复成功! TTS功能现在应该正常工作")
        print("\n建议测试:")
        print("1. 访问 http://localhost:8083")
        print("2. 点击'开始录音'按钮")
        print("3. 录音后查看Bryson自动反馈")
        return True
    else:
        print("=" * 50)
        print("❌ SSL证书仍有问题")
        print("\n可能需要手动安装证书:")
        print("1. 打开 /Applications/Python 3.12/Install Certificates.command")
        print("2. 如果还有问题，尝试: pip install --upgrade certifi")
        return False

if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(main())
    exit(0 if result else 1)