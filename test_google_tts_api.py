#!/usr/bin/env python3
"""
快速测试Google Cloud TTS API密钥
"""

import os
import sys
import requests
import json

# 用户提供的API密钥
API_KEY = "AIzaSyBdfhzjxPoYBOr8NWCNJA7oSwgttHeqwgk"

def test_google_tts_api():
    """测试Google Cloud Text-to-Speech API"""
    print("=== Google Cloud TTS API测试 ===\n")
    
    # Google Cloud TTS端点
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={API_KEY}"
    
    # 请求参数
    payload = {
        "input": {
            "text": "Hello, this is a test of the Google Text-to-Speech API."
        },
        "voice": {
            "languageCode": "en-US",
            "name": "en-US-Standard-D",
            "ssmlGender": "MALE"
        },
        "audioConfig": {
            "audioEncoding": "MP3"
        }
    }
    
    print(f"API密钥: {API_KEY[:15]}...")
    print(f"端点URL: texttospeech.googleapis.com/v1/text:synthesize")
    print(f"测试文本: {payload['input']['text']}")
    print()
    
    try:
        # 发送请求
        print("正在发送API请求...")
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {response.headers.get('content-type', 'Unknown')}")
        
        if response.status_code == 200:
            # 成功响应
            result = response.json()
            print("\n✅ API调用成功!")
            
            # 检查响应内容
            if "audioContent" in result:
                audio_len = len(result["audioContent"])
                print(f"✅ 收到音频数据: {audio_len} 字节")
                
                # 保存音频文件供测试
                import base64
                audio_data = base64.b64decode(result["audioContent"])
                
                # 保存到文件
                audio_file = "/tmp/google_tts_test.mp3"
                with open(audio_file, "wb") as f:
                    f.write(audio_data)
                
                print(f"✅ 音频文件已保存: {audio_file}")
                print("🎧 尝试播放音频...")
                
                # 尝试播放音频
                try:
                    import subprocess
                    subprocess.run(["afplay", audio_file], timeout=5)
                    print("✅ 音频播放成功!")
                except Exception as e:
                    print(f"⚠️ 音频播放失败: {e}")
                    print("（这没问题，API功能本身已验证）")
                
                return True
            else:
                print("❌ 响应中没有audioContent字段")
                print(f"完整响应: {json.dumps(result, indent=2)[:500]}...")
                return False
                
        elif response.status_code == 403:
            print("\n❌ 认证失败 (403)")
            print("可能原因:")
            print("1. API密钥无效")
            print("2. Text-to-Speech API未启用")
            print("3. 需要启用计费账户")
            print(f"错误详情: {response.text[:200]}")
            
        elif response.status_code == 400:
            print("\n❌ 请求错误 (400)")
            print(f"错误详情: {response.text[:200]}")
            
        else:
            print(f"\n❌ 未知错误 ({response.status_code})")
            print(f"响应: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("\n❌ 请求超时")
        print("网络连接可能有问题")
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接错误")
        print("无法连接到Google Cloud API")
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
    
    return False

def save_api_key():
    """保存API密钥到配置文件"""
    key_file = os.path.expanduser("~/.openclaw/auth/google/ielts_tts_2026.key")
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        
        # 保存密钥
        with open(key_file, "w") as f:
            f.write(API_KEY)
        
        print(f"\n💾 API密钥已保存到: {key_file}")
        return True
    except Exception as e:
        print(f"❌ 保存密钥失败: {e}")
        return False

def main():
    """主函数"""
    print("开始Google Cloud TTS API测试")
    print("-" * 50)
    
    # 测试API密钥
    success = test_google_tts_api()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 API密钥验证成功!")
        
        # 保存密钥
        print("\n正在保存API密钥...")
        if save_api_key():
            print("✅ 配置文件已更新")
        
        print("\n🎯 下一步:")
        print("1. ✅ API密钥已验证")
        print("2. ⏳ 开始集成到Bryson的TTS系统中")
        print("3. 📊 准备第一小时的开发汇报")
        print("4. 🎤 创建个性化语音模板")
        
    else:
        print("\n" + "=" * 50)
        print("❌ API密钥验证失败")
        
        print("\n🔧 解决步骤:")
        print("1. 访问: https://console.cloud.google.com/apis/credentials")
        print("   - 确认密钥存在且有效")
        print("2. 访问: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com")
        print("   - 确保Text-to-Speech API已启用")
        print("3. 检查计费账户:")
        print("   - https://console.cloud.google.com/billing")
        print("   - 可能需要启用计费（免费配额也需要）")
        print("4. 备选方案: 创建服务账号JSON密钥")
        print("   - 按照TTS_DEVELOPMENT_RESOURCE_NEEDS.md中的步骤")
    
    return success

if __name__ == "__main__":
    sys.exit(0 if main() else 1)