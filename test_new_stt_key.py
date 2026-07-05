#!/usr/bin/env python3
"""
测试新STT API密钥
"""

import os
import json
import base64
import requests
from pathlib import Path

def load_api_key():
    """加载新API密钥"""
    key_path = Path.home() / ".openclaw/auth/google/ielts_stt_2026.key"
    if key_path.exists():
        api_key = key_path.read_text().strip()
        print(f"✅ 加载新API密钥: {api_key[:10]}... (长度: {len(api_key)})")
        return api_key
    else:
        print(f"❌ 密钥文件不存在: {key_path}")
        return None

def test_tts_api(api_key):
    """测试Text-to-Speech API（确认密钥基本工作）"""
    print("\n🎤 测试Text-to-Speech API...")
    
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    params = {"key": api_key}
    
    data = {
        "input": {"text": "Hello Google STT test"},
        "voice": {"languageCode": "en-US", "name": "en-US-Wavenet-D"},
        "audioConfig": {"audioEncoding": "MP3"}
    }
    
    try:
        response = requests.post(url, params=params, json=data, timeout=10)
        print(f"📡 TTS API状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ TTS API工作正常！")
            return True
        else:
            print(f"❌ TTS API错误: {response.status_code}")
            if response.text:
                try:
                    error = response.json()
                    print(f"   错误详情: {json.dumps(error, indent=2)}")
                except:
                    print(f"   响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ TTS API请求失败: {e}")
        return False

def test_stt_api(api_key, audio_file):
    """测试Speech-to-Text API"""
    print(f"\n🎤 测试Speech-to-Text API: {audio_file.name}")
    
    # 读取音频
    with open(audio_file, 'rb') as f:
        audio_content = f.read()
    
    audio_b64 = base64.b64encode(audio_content).decode('utf-8')
    
    url = "https://speech.googleapis.com/v1/speech:recognize"
    params = {"key": api_key}
    
    data = {
        "config": {
            "encoding": "MP3",
            "sampleRateHertz": 16000,
            "languageCode": "en-US",
            "enableAutomaticPunctuation": True,
            "model": "default",
            "useEnhanced": True
        },
        "audio": {
            "content": audio_b64
        }
    }
    
    try:
        print("📡 发送STT API请求...")
        response = requests.post(url, params=params, json=data, timeout=30)
        print(f"📡 STT API状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if "results" in result and result["results"]:
                transcription = ""
                for result_obj in result["results"]:
                    if "alternatives" in result_obj:
                        transcription += result_obj["alternatives"][0]["transcript"] + " "
                
                print(f"✅ STT转写成功！")
                print(f"   转写结果: {transcription.strip()}")
                return True, transcription.strip(), result
            else:
                print("❌ API返回空结果")
                if result:
                    print(f"   完整响应: {json.dumps(result, indent=2)[:500]}...")
                return False, "空结果", result
        
        else:
            print(f"❌ STT API错误: {response.status_code}")
            if response.text:
                try:
                    error = response.json()
                    print(f"   错误详情: {json.dumps(error, indent=2)}")
                    
                    # 检查特定错误
                    if "error" in error:
                        error_code = error["error"].get("code")
                        error_message = error["error"].get("message")
                        print(f"   错误代码: {error_code}")
                        print(f"   错误信息: {error_message}")
                        
                except:
                    print(f"   响应内容: {response.text[:500]}...")
            return False, f"API错误 {response.status_code}", None
            
    except Exception as e:
        print(f"❌ STT API请求失败: {e}")
        return False, f"请求失败: {str(e)}", None

def find_test_audio():
    """查找测试音频文件"""
    audio_dir = Path("test_audio/ielts_benchmark/beginner")
    if not audio_dir.exists():
        print(f"❌ 音频目录不存在: {audio_dir}")
        return None
    
    # 找一个简单的音频
    mp3_files = list(audio_dir.glob("*.mp3"))
    if not mp3_files:
        print("❌ 未找到MP3文件")
        return None
    
    # 选择第1个文件
    test_file = mp3_files[0]
    print(f"✅ 找到测试音频: {test_file.name}")
    
    # 显示音频信息
    metadata_path = Path("test_audio/ielts_benchmark/metadata.json")
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        if "samples" in metadata:
            for sample in metadata["samples"][:20]:  # 检查前20个
                if sample.get("audio_file", "").endswith(f"beginner/{test_file.name}"):
                    print(f"   原文: {sample.get('text', 'N/A')}")
                    print(f"   等级: {sample.get('level', 'N/A')}")
                    break
    
    return test_file

def main():
    print("🎤 新STT API密钥测试")
    print("="*60)
    
    # 1. 加载密钥
    api_key = load_api_key()
    if not api_key:
        return
    
    # 2. 测试TTS API（快速验证密钥基本功能）
    if not test_tts_api(api_key):
        print("\n⚠️  TTS API测试失败，可能密钥无效或API未启用")
        print("   检查步骤:")
        print("   1. 确保在Google Cloud Console中" + "" + "启用Text-to-Speech API")
        print("   2. 检查API密钥限制设置")
        return
    else:
        print("\n✅ TTS API测试通过，密钥基本有效")
    
    # 3. 查找测试音频
    audio_file = find_test_audio()
    if not audio_file:
        return
    
    # 4. 测试STT API
    print("\n" + "="*60)
    print("🚀 开始Speech-to-Text API测试")
    print("="*60)
    
    success, transcription, raw_result = test_stt_api(api_key, audio_file)
    
    # 5. 保存结果
    if raw_result:
        output_file = "new_stt_key_test_result.json"
        result_data = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "api_key_prefix": api_key[:10],
            "audio_file": str(audio_file),
            "success": success,
            "transcription": transcription,
            "response_summary": {
                "has_results": "results" in raw_result and bool(raw_result["results"]),
                "result_count": len(raw_result.get("results", []))
            } if raw_result else None
        }
        
        with open(output_file, 'w') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 结果已保存: {output_file}")
    
    # 6. 总结和建议
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    
    if success:
        print("🎉 **新STT API密钥工作正常！**")
        print("")
        print("✅ 验证完成:")
        print("   - API密钥加载成功")
        print("   - TTS API测试通过")
        print("   - STT API测试通过")
        print("   - 音频转写功能正常")
        print("")
        print("🚀 下一步行动:")
        print("1. 集成到Bryson语音MVP中")
        print("   - 替换whisper_stt_test.js中的模拟输入")
        print("   - 实现真实语音转文本处理")
        print("2. 创建Google STT测试界面")
        print("   - 基于现有Whisper.js界面修改")
        print("   - 保持外部访问（ngrok）")
        print("3. 进行外部网络测试")
        print("   - 通过: https://unwhispering-imani-digitately.ngrok-free.dev")
    else:
        print("❌ **新STT API密钥测试失败**")
        print("")
        print("🔧 故障排除:")
        print("1. 检查API密钥限制设置:")
        print("   - 确保已启用Cloud Speech-to-Text API")
        print("   - 确保API密钥限制只包含必要API")
        print("2. 检查项目配置:")
        print("   - 访问: https://console.cloud.google.com/apis/api/speech.googleapis.com/overview")
        print("   - 确保Speech-to-Text API已启用")
        print("3. 检查配额:")
        print("   - 可能免费配额已用尽")
        print("   - 需要升级到付费账户")
        print("")
        print("📋 请按提示检查并重试")
    
    print(f"\n🕐 当前时间: {__import__('datetime').datetime.now().strftime('%H:%M')}")

if __name__ == "__main__":
    main()