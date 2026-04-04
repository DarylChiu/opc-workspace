#!/usr/bin/env python3
"""
生成立体声测试音频并Base64编码
"""

import os
import sys
import base64
import tempfile
import json
import requests
import time

def load_api_key():
    """加载API密钥"""
    api_key_file = os.path.expanduser("~/.openclaw/auth/google/ielts_tts_2026.key")
    if not os.path.exists(api_key_file):
        print(f"❌ API密钥文件不存在: {api_key_file}")
        return None
    
    with open(api_key_file, 'r') as f:
        return f.read().strip()

def synthesize_stereo_speech(text, language_code="en-US", voice_name="en-US-Wavenet-D"):
    """使用Google TTS生成立体声音频"""
    api_key = load_api_key()
    if not api_key:
        return None, "API密钥加载失败"
    
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
    
    # 立体声配置
    payload = {
        "input": {"text": text},
        "voice": {
            "languageCode": language_code,
            "name": voice_name
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "sampleRateHertz": 24000,
            "effectsProfileId": ["headphone-class-device"],
            # 立体声设置
            "stereoConfig": {
                "leftChannel": {
                    "volumeGainDb": 0.0
                },
                "rightChannel": {
                    "volumeGainDb": 0.0
                }
            }
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # 解码base64音频数据
        audio_content = base64.b64decode(data['audioContent'])
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(audio_content)
            return f.name, "成功"
            
    except Exception as e:
        return None, f"语音合成失败: {e}"

def file_to_base64(file_path):
    """将文件转换为Base64字符串"""
    try:
        with open(file_path, 'rb') as f:
            audio_bytes = f.read()
            return base64.b64encode(audio_bytes).decode('utf-8')
    except Exception as e:
        return None, f"Base64编码失败: {e}"

def main():
    print("🎵 生成立体声测试音频")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        {
            "name": "英语测试",
            "text": "Hello Bryson, this is a stereo audio test.",
            "lang": "en-US",
            "voice": "en-US-Wavenet-D"  # 立体声兼容的语音
        },
        {
            "name": "中文测试", 
            "text": "这是立体声语音合成测试。",
            "lang": "cmn-CN",
            "voice": "cmn-CN-Wavenet-C"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 测试 {i}: {test['name']}")
        print(f"  文本: {test['text']}")
        print(f"  语言: {test['lang']}")
        print(f"  语音: {test['voice']}")
        
        print("  🔄 正在生成立体声音频...")
        start_time = time.time()
        
        # 生成音频
        audio_file, status = synthesize_stereo_speech(
            test["text"], 
            test["lang"], 
            test["voice"]
        )
        
        if audio_file:
            # 获取文件大小
            file_size = os.path.getsize(audio_file)
            
            # 转换为Base64
            print("  🔄 正在转换为Base64...")
            base64_str, error = file_to_base64(audio_file)
            
            if base64_str:
                # 清理临时文件
                os.unlink(audio_file)
                
                elapsed = time.time() - start_time
                print(f"  ✅ 生成成功!")
                print(f"  ⏱️  耗时: {elapsed:.2f}秒")
                print(f"  📏 文件大小: {file_size:,}字节")
                print(f"  📊 Base64长度: {len(base64_str):,}字符")
                
                results.append({
                    "name": test["name"],
                    "text": test["text"],
                    "base64": base64_str[:100] + "..." if len(base64_str) > 100 else base64_str,
                    "full_base64": base64_str,
                    "file_size": file_size,
                    "time": elapsed
                })
            else:
                print(f"  ❌ Base64转换失败: {error}")
        else:
            print(f"  ❌ 音频生成失败: {status}")
    
    # 输出结果
    print(f"\n{'='*60}")
    print("📋 测试结果总结")
    print(f"{'='*60}")
    
    for result in results:
        print(f"\n🎵 {result['name']}")
        print(f"   文本: {result['text']}")
        print(f"   文件大小: {result['file_size']:,}字节")
        print(f"   生成时间: {result['time']:.2f}秒")
        print(f"   Base64预览: {result['base64']}")
        
        # 保存到文件
        output_file = f"stereo_audio_{result['name']}.base64.txt"
        with open(output_file, 'w') as f:
            f.write(result['full_base64'])
        print(f"   💾 完整Base64已保存到: {output_file}")
        
        # 解码说明
        print(f"   🔧 解码方法:")
        print(f"     echo '{result['full_base64'][:50]}...' | base64 -d > audio.mp3")
    
    # Python解码示例
    print(f"\n{'='*60}")
    print("🐍 Python解码示例")
    print(f"{'='*60}")
    print("""
import base64

# Base64字符串(太长，这里用...代替)
base64_str = \"\"\"[复制的Base64内容]\"\"\"

# 解码并保存
audio_bytes = base64.b64decode(base64_str)
with open('decoded_audio.mp3', 'wb') as f:
    f.write(audio_bytes)

print("✅ 音频已保存为 decoded_audio.mp3")
    """)
    
    print(f"\n💡 提示: Base64字符串很长，建议复制保存到文件中")

if __name__ == "__main__":
    main()