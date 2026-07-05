#!/usr/bin/env python3
"""
简单Google STT测试 - 使用API密钥
直接调用Google Speech-to-Text API，无需复杂配置
"""

import os
import sys
import json
import base64
from pathlib import Path
import requests

def get_api_key():
    """获取Google API密钥"""
    api_key_path = Path.home() / ".openclaw/auth/google/ielts_tts_2026.key"
    if api_key_path.exists():
        api_key = api_key_path.read_text().strip()
        if api_key and api_key.startswith("AIza"):
            print(f"✅ 找到API密钥: {api_key[:10]}...")
            return api_key
    print("❌ 未找到Google API密钥")
    print(f"检查: {api_key_path}")
    return None

def get_test_audio():
    """获取测试音频"""
    audio_dir = Path("test_audio/ielts_benchmark")
    if not audio_dir.exists():
        print(f"❌ 音频目录不存在: {audio_dir}")
        return None
    
    # 找一个beginners级别的音频
    beginner_dir = audio_dir / "beginner"
    if beginner_dir.exists():
        mp3_files = list(beginner_dir.glob("*.mp3"))
        if mp3_files:
            test_file = mp3_files[0]
            print(f"✅ 找到测试音频: {test_file.name}")
            return test_file
    
    print("❌ 未找到测试音频")
    return None

def transcribe_with_api_key(api_key: str, audio_file: Path):
    """使用API密钥调用Google STT API"""
    print(f"🎯 正在转写: {audio_file.name}")
    
    # 读取音频文件
    with open(audio_file, 'rb') as f:
        audio_content = f.read()
    
    # Base64编码音频内容
    audio_b64 = base64.b64encode(audio_content).decode('utf-8')
    
    # 构建请求数据
    request_data = {
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
    
    # Google Speech-to-Text API端点
    url = f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}"
    
    try:
        print("📡 发送请求到Google STT API...")
        response = requests.post(url, json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if "results" in result and result["results"]:
                transcription = ""
                for result_obj in result["results"]:
                    if "alternatives" in result_obj:
                        transcription += result_obj["alternatives"][0]["transcript"] + " "
                
                return transcription.strip(), result
            else:
                return "❌ API返回空结果", result
        
        else:
            error_msg = f"❌ API错误: {response.status_code}"
            if response.text:
                try:
                    error_json = response.json()
                    error_msg += f" - {json.dumps(error_json)}"
                except:
                    error_msg += f" - {response.text[:200]}"
            return error_msg, None
            
    except Exception as e:
        return f"❌ 请求失败: {str(e)}", None

def main():
    print("🎤 Google STT快速测试 (API密钥方式)")
    print("=" * 60)
    
    # 1. 获取API密钥
    api_key = get_api_key()
    if not api_key:
        return
    
    # 2. 获取测试音频
    audio_file = get_test_audio()
    if not audio_file:
        return
    
    # 3. 转写测试
    print("\n" + "=" * 60)
    print("🚀 开始转写测试")
    print("=" * 60)
    
    transcription, raw_result = transcribe_with_api_key(api_key, audio_file)
    
    print(f"\n📝 转写结果: {transcription}")
    
    # 读取原始文本进行比较
    metadata_path = Path("test_audio/ielts_benchmark/metadata.json")
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        audio_id = audio_file.stem  # 去掉.mp3扩展名
        original_text = ""
        
        for item in metadata:
            if item.get("id") == audio_id:
                original_text = item.get("text", "")
                level = item.get("level", "unknown")
                topic = item.get("topic", "unknown")
                print(f"\n📖 音频信息:")
                print(f"   ID: {audio_id}")
                print(f"   等级: {level}")
                print(f"   话题: {topic}")
                print(f"   原文: {original_text}")
                break
        
        # 简单对比
        if original_text and transcription and not transcription.startswith("❌"):
            # 转换为小写进行粗略比较
            original_words = set(original_text.lower().split())
            trans_words = set(transcription.lower().split())
            common_words = original_words.intersection(trans_words)
            
            match_percentage = len(common_words) / max(len(original_words), 1) * 100
            print(f"\n📊 粗略匹配率: {match_percentage:.1f}%")
            print(f"   共同词汇数: {len(common_words)} / {len(original_words)}")
    
    # 4. 保存结果
    output_file = "google_stt_single_test_result.json"
    result_data = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "audio_file": str(audio_file),
        "transcription": transcription,
        "api_key_used": f"{api_key[:10]}...",
        "original_text": original_text if 'original_text' in locals() else "Not found"
    }
    
    if raw_result:
        result_data["raw_response"] = raw_result
    
    with open(output_file, 'w') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 结果已保存到: {output_file}")
    
    # 5. 下一步建议
    print("\n" + "=" * 60)
    print("🚀 下一步建议")
    print("=" * 60)
    
    if transcription and not transcription.startswith("❌"):
        print("✅ Google STT API工作正常！")
        print("")
        print("下一步行动:")
        print("1. 批量测试更多音频")
        print("   python3 -c \"import simple_google_stt_test; simple_google_stt_test.batch_test()\"")
        print("2. 集成到Bryson语音MVP中")
        print("   - 替换现有模拟输入逻辑")
        print("   - 实现真正的语音转文本处理")
        print("3. 优化和扩展")
        print("   - 添加实时流式转录")
        print("   - 支持多种音频格式")
        print("   - 添加错误处理和重试机制")
    else:
        print("❌ Google STT测试遇到问题")
        print("")
        print("故障排除建议:")
        print("1. 检查API密钥权限")
        print("   - 确保已启用Speech-to-Text API")
        print("2. 检查音频格式")
        print("   - 确保是MP3格式，16000Hz采样率")
        print("3. 检查网络连接")
        print("   - API密钥需要能访问Google Cloud")
    
    print(f"\n🕐 当前时间: {__import__('datetime').datetime.now().strftime('%H:%M')}")

def batch_test():
    """批量测试函数"""
    print("批量测试功能 - 待实现")
    print("TODO: 添加批量测试多个音频的功能")

if __name__ == "__main__":
    main()