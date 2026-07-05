#!/usr/bin/env python3
"""
即时修复Google STT测试 - 使用已知工作的TTS API密钥测试Speech API
"""

import os
import json
import base64
import subprocess
from pathlib import Path
import requests

def check_current_status():
    """检查当前状态"""
    print("✅ **Google STT状态诊断**")
    print("="*60)
    
    # 1. 已知问题
    print("📊 **已知问题**:")
    print("   测试结果: API错误: 403 - API_KEY_SERVICE_BLOCKED")
    print("   含义: API密钥已认证，但未授权访问Speech-to-Text服务")
    print("")
    
    # 2. 已知工作
    print("📊 **已知工作**:")
    print("   ✅ 同一API密钥可以正常访问Text-to-Speech API")
    print("   ✅ API密钥格式有效（AIzaSyBdfhzjxPoYBOr8NWCNJA7oSwgttHeqwgk）")
    print("")
    
    print("🎯 **解决方案**: 我们需要为API密钥启用Speech-to-Text服务权限")
    print("")

def get_api_key():
    """获取API密钥"""
    api_key_path = Path.home() / ".openclaw/auth/google/ielts_tts_2026.key"
    if not api_key_path.exists():
        return None
    
    api_key = api_key_path.read_text().strip()
    return api_key

def verify_tts_working(api_key):
    """验证TTS API工作正常"""
    print("🔍 **验证TTS API工作状态**")
    
    tts_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    request_data = {
        "input": {"text": "Testing TTS API"},
        "voice": {"languageCode": "en-US", "name": "en-US-Wavenet-D"},
        "audioConfig": {"audioEncoding": "MP3"}
    }
    
    try:
        response = requests.post(f"{tts_url}?key={api_key}", json=request_data, timeout=10)
        if response.status_code == 200:
            print("✅ **验证通过**: TTS API工作正常！")
            print(f"   状态码: {response.status_code}")
            print(f"   证明API密钥有效且可以访问Google Cloud服务")
            return True
        else:
            print(f"❌ **意外结果**: TTS API也返回错误 {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ **请求失败**: {e}")
        return False

def enable_speech_api_instructions():
    """提供启用Speech API的逐步指导"""
    print("\n" + "="*60)
    print("🚀 **立即启用Speech-to-Text API**")
    print("="*60)
    
    api_key = get_api_key()
    if api_key:
        print(f"📋 **你的API密钥**: {api_key[:10]}...")
    
    print("")
    print("📝 **步骤1: 登录Google Cloud Console**")
    print("   网址: https://console.cloud.google.com/")
    print("")
    print("📝 **步骤2: 导航到API库**")
    print("   路径: APIs & Services > Library")
    print("   或直接访问: https://console.cloud.google.com/apis/library")
    print("")
    print("📝 **步骤3: 搜索并启用Speech-to-Text API**")
    print("   1. 在搜索框中输入 'Speech-to-Text API'")
    print("   2. 点击结果中的 'Speech-to-Text API'")
    print("   3. 点击 '启用' 按钮")
    print("")
    print("📝 **步骤4: 检查API密钥限制（可选但推荐）**")
    print("   1. 导航到: APIs & Services > Credentials")
    print("   2. 找到你的API密钥（部分显示: AIzaSyBdfh...）")
    print("   3. 点击密钥名称进入详情")
    print("   4. 点击 'API restrictions' 选项卡")
    print("   5. 确保 'Speech-to-Text API' 被选中")
    print("   6. 点击 '保存'")
    print("")
    print("⏰ **等待时间**: API启用通常立即生效，但偶尔需要几分钟")
    print("")

def create_quick_test_script():
    """创建快速测试脚本"""
    script_content = '''#!/usr/bin/env python3
"""
快速Google STT测试脚本
在启用Speech API后立即测试
"""

import os
import json
import base64
import requests
from pathlib import Path

# 读取API密钥
key_path = Path.home() / ".openclaw/auth/google/ielts_tts_2026.key"
if not key_path.exists():
    print("❌ API密钥文件不存在")
    exit(1)

api_key = key_path.read_text().strip()
print(f"🔑 使用API密钥: {api_key[:10]}...")

# 选取一个简单的测试音频
audio_dir = Path("test_audio/ielts_benchmark/beginner")
if not audio_dir.exists():
    print("❌ 音频目录不存在")
    exit(1)

# 找一个小文件测试
import random
mp3_files = list(audio_dir.glob("*.mp3"))
if not mp3_files:
    print("❌ 没有音频文件")
    exit(1)

test_file = mp3_files[0]  # 第一个文件
print(f"🎵 使用测试音频: {test_file.name}")

# 读取音频并编码
try:
    with open(test_file, 'rb') as f:
        audio_content = f.read()
    
    audio_b64 = base64.b64encode(audio_content).decode('utf-8')
    print(f"📊 音频大小: {len(audio_content)} bytes")
    
except Exception as e:
    print(f"❌ 读取音频失败: {e}")
    exit(1)

# 构建请求
request_data = {
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

# 发送请求
url = f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}"
print(f"📡 发送请求到: {url}")

try:
    import time
    start_time = time.time()
    
    response = requests.post(url, json=request_data, timeout=30)
    elapsed = time.time() - start_time
    
    print(f"⏱️  响应时间: {elapsed:.2f}秒")
    print(f"📊 状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if "results" in result and result["results"]:
            transcription = ""
            for result_obj in result["results"]:
                if "alternatives" in result_obj:
                    best = result_obj["alternatives"][0]
                    transcription += best["transcript"] + " "
                    confidence = best.get("confidence", "N/A")
                    print(f"   🔹 置信度: {confidence}")
            
            print(f"✅ **成功!** 转写结果: {transcription.strip()}")
            print("\n🎉 **Speech-to-Text API现在工作正常！**")
            print("\n💡 **下一步**:")
            print("   1. 集成到Bryson语音MVP")
            print("   2. 批量测试所有IELTS音频样本")
            print("   3. 实现实时流式转录")
        else:
            print("⚠️  API返回空结果")
            print(f"   完整响应: {json.dumps(result, indent=2)}")
            
    elif response.status_code == 403:
        print("❌ **仍然被阻止 (403)**")
        print(f"   {response.text}")
        print("\n💡 **还需要什么**:")
        print("   1. 确保Speech-to-Text API已启用")
        print("   2. 确保API密钥有访问权限")
        print("   3. 如果使用API限制，确保Speech-to-Text在允许列表中")
        
    else:
        print(f"❌ **其他错误**: {response.status_code}")
        print(f"   响应: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print("❌ **请求超时** (30秒)")
except Exception as e:
    print(f"❌ **异常**: {e}")

print(f"\n🕐 测试完成时间: {time.strftime('%H:%M')}")
'''
    
    output_path = "quick_stt_test.py"
    with open(output_path, 'w') as f:
        f.write(script_content)
    
    print(f"📝 **已创建快速测试脚本**: {output_path}")
    print("")
    print("💡 **用法**: 在启用Speech API后运行:")
    print(f"   python3 {output_path}")

def provide_immediate_workaround():
    """提供立即可用的替代方案"""
    print("\n" + "="*60)
    print("🔄 **立即可用的解决方案（不需要启用API）**")
    print("="*60)
    
    print("")
    print("🎯 **方案A: 使用Whisper.js本地识别**")
    print("   尽管Whisper.js界面有bug，但我们可以修复它:")
    print("   1. 修复JavaScript导入问题")
    print("   2. 改为使用简单的FileReader + Python后端")
    print("   3. 创建轻量级测试界面")
    print("")
    print("🎯 **方案B: 创建纯Python STT解决方案**")
    print("   1. 使用SpeechRecognition库（支持Google、Sphinx等）")
    print("   2. 创建简单的Flask后端")
    print("   3. 与现有Bryson MVP集成")
    print("")
    print("🎯 **方案C: 临时使用其他STT服务**")
    print("   1. OpenAI Whisper API")
    print("   2. Azure Speech-to-Text")
    print("   3. AWS Transcribe")
    print("")
    
    print("📋 **我推荐方案A+B组合**:")
    print("   1. **今晚**修复Whisper.js测试界面")
    print("   2. **同时**开始启用Google Speech API的流程")
    print("   3. **明天**测试两种方案")
    print("")

def main():
    print("🎤 Google STT即时修复助手")
    print("="*60)
    
    # 检查当前状态
    check_current_status()
    
    # 获取API密钥
    api_key = get_api_key()
    if not api_key:
        print("❌ 无法读取API密钥")
        return
    
    # 验证TTS工作状态
    if not verify_tts_working(api_key):
        print("⚠️  TTS API验证失败，可能需要检查网络或密钥状态")
    
    # 提供启用指南
    enable_speech_api_instructions()
    
    # 创建快速测试脚本
    create_quick_test_script()
    
    # 提供备选方案
    provide_immediate_workaround()
    
    print("\n" + "="*60)
    print("📋 **今晚执行计划**")
    print("="*60)
    print("")
    print("1. 🏃‍♂️ **立即行动** (22:10之前):")
    print("   - 登录Google Cloud Console")
    print("   - 启用Speech-to-Text API")
    print("   - 运行 quick_stt_test.py 验证")
    print("")
    print("2. 🔧 **并行修复** (现在开始):")
    print("   - 我修复Whisper.js测试界面的前端错误")
    print("   - 创建更简单的测试页面")
    print("   - 确保现有Ngrok链接可以测试")
    print("")
    print("3. 🎯 **目标成果**:")
    print("   - 今晚22:30之前至少有一个STT方案可用")
    print("   - 提供截图或演示证明STT工作")
    print("   - 明确下一步集成计划")
    print("")
    print("⏰ **时间线**:")
    print("   22:00-22:15 - Google API配置")
    print("   22:15-22:30 - 修复Whisper.js界面")
    print("   22:30-22:45 - 测试和验证")
    print("")

if __name__ == "__main__":
    main()