#!/usr/bin/env python3
"""
Google STT快速测试脚本
使用Google Cloud Speech-to-Text API进行IELTS音频转写测试
"""

import os
import sys
import json
import base64
from pathlib import Path
from typing import Dict, List

# 检查并安装必要依赖
def check_dependencies():
    try:
        from google.cloud import speech
        print("✅ google-cloud-speech 已安装")
        return speech
    except ImportError:
        print("❌ google-cloud-speech 未安装")
        print("正在安装依赖...")
        os.system("pip install google-cloud-speech")
        try:
            from google.cloud import speech
            print("✅ google-cloud-speech 安装成功")
            return speech
        except ImportError:
            print("❌ 无法安装 google-cloud-speech")
            return None

def setup_google_credentials():
    """设置Google Cloud凭据"""
    service_account_path = Path.home() / ".openclaw/auth/google/service_account_info.txt"
    api_key_path = Path.home() / ".openclaw/auth/google/ielts_tts_2026.key"
    
    # 方法1: 使用服务账号文件 (推荐)
    if service_account_path.exists():
        print(f"📁 找到服务账号文件: {service_account_path}")
        
        # 从文件提取JSON内容
        content = service_account_path.read_text()
        # 查找JSON格式的服务账号信息
        import re
        
        # 尝试提取JSON部分
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                # 创建临时服务账号JSON文件
                temp_file = Path("/tmp/google_service_account.json")
                temp_file.write_text(json_str)
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(temp_file)
                print(f"✅ 设置服务账号环境变量: {temp_file}")
                return True
            except Exception as e:
                print(f"❌ 解析服务账号JSON失败: {e}")
    
    # 方法2: 使用API密钥
    if api_key_path.exists():
        api_key = api_key_path.read_text().strip()
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            print(f"✅ 设置API密钥: {api_key[:10]}...")
            return True
    
    print("❌ 未找到有效的Google Cloud凭据")
    print("请确保以下文件之一存在:")
    print(f"  1. {service_account_path} (服务账号JSON)")
    print(f"  2. {api_key_path} (API密钥)")
    return False

def get_audio_samples():
    """获取IELTS音频样本用于测试"""
    audio_dir = Path("test_audio/ielts_benchmark")
    samples = []
    
    if not audio_dir.exists():
        print(f"❌ 音频目录不存在: {audio_dir}")
        return samples
    
    # 读取元数据
    metadata_path = audio_dir / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        for sample in metadata:
            level = sample.get("level", "unknown")
            topic = sample.get("topic", "unknown")
            audio_path = audio_dir / level / f"{sample['id']}.mp3"
            
            if audio_path.exists():
                samples.append({
                    "id": sample["id"],
                    "level": level,
                    "topic": topic,
                    "text": sample["text"],
                    "duration": sample.get("duration", 0),
                    "path": str(audio_path)
                })
    
    print(f"📊 找到 {len(samples)} 个音频样本")
    return samples[:5]  # 限制前5个用于测试

def transcribe_audio(speech_client, audio_path: str) -> str:
    """使用Google STT转写单个音频文件"""
    try:
        with open(audio_path, 'rb') as audio_file:
            audio_content = audio_file.read()
        
        audio = speech.RecognitionAudio(content=audio_content)
        
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model="default",
            use_enhanced=True,
            enable_word_time_offsets=True
        )
        
        print(f"🔍 正在转写: {Path(audio_path).name}")
        response = speech_client.recognize(config=config, audio=audio)
        
        if not response.results:
            return "❌ 未识别到任何文本"
        
        transcription = ""
        for result in response.results:
            transcription += result.alternatives[0].transcript + " "
        
        return transcription.strip()
    
    except Exception as e:
        return f"❌ 转写失败: {str(e)}"

def main():
    print("🎤 Google STT快速测试")
    print("=" * 50)
    
    # 检查依赖
    speech = check_dependencies()
    if not speech:
        print("请手动安装: pip install google-cloud-speech")
        return
    
    # 设置凭据
    if not setup_google_credentials():
        return
    
    try:
        # 初始化客户端
        client = speech.SpeechClient()
        print("✅ Google Speech客户端初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 获取音频样本
    samples = get_audio_samples()
    if not samples:
        print("❌ 没有可用的音频样本")
        return
    
    # 开始测试转写
    print("\n" + "=" * 50)
    print("🎯 开始音频转写测试")
    print("=" * 50)
    
    results = []
    for i, sample in enumerate(samples, 1):
        print(f"\n[{i}/{len(samples)}] 测试样本: {sample['id']}")
        print(f"   等级: {sample['level']}")
        print(f"   话题: {sample['topic']}")
        print(f"   原文: {sample['text'][:100]}...")
        
        transcription = transcribe_audio(client, sample["path"])
        print(f"   转写: {transcription}")
        
        results.append({
            "sample_id": sample["id"],
            "original_text": sample["text"],
            "transcription": transcription,
            "level": sample["level"],
            "match_rate": estimate_match(sample["text"], transcription) if transcription else 0
        })
    
    # 生成测试报告
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    successful = sum(1 for r in results if not r["transcription"].startswith("❌"))
    total = len(results)
    
    print(f"✅ 成功转写: {successful}/{total}")
    print(f"📈 平均匹配率: {sum(r['match_rate'] for r in results)/total:.1f}%")
    
    for result in results:
        print(f"\n🔹 {result['sample_id']} ({result['level']}):")
        print(f"   原文: {result['original_text'][:80]}...")
        if result["transcription"]:
            print(f"   转写: {result['transcription'][:80]}...")
            print(f"   匹配率: {result['match_rate']:.1f}%")
        else:
            print(f"   结果: {result['transcription']}")
    
    # 保存结果到文件
    output_file = "google_stt_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "total_samples": total,
            "successful_transcriptions": successful,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 详细结果已保存: {output_file}")
    
    # 生成下一个步骤建议
    print("\n" + "=" * 50)
    print("🚀 下一步建议")
    print("=" * 50)
    print("1. 集成到Bryson语音MVP:")
    print("   - 替换现有模拟输入处理逻辑")
    print("   - 实现录音→STT→智能反馈的完整流程")
    print("2. 批量测试所有115个IELTS音频样本")
    print("   - 计算准确率统计")
    print("   - 识别常见错误模式")
    print("3. 性能优化:")
    print("   - 实现流式转录（实时反馈）")
    print("   - 缓存机制减少API调用")

def estimate_match(original: str, transcription: str) -> float:
    """简单估算文本匹配率（实际应使用更复杂的算法）"""
    if not transcription or transcription.startswith("❌"):
        return 0.0
    
    original_lower = "".join(filter(str.isalnum, original.lower()))
    trans_lower = "".join(filter(str.isalnum, transcription.lower()))
    
    if not original_lower or not trans_lower:
        return 0.0
    
    # 简单计算共有字符比例
    common = sum(1 for c in set(original_lower) if c in trans_lower)
    return min(100.0, common / len(set(original_lower)) * 100)

if __name__ == "__main__":
    main()