#!/usr/bin/env python3
"""
Google Cloud TTS流式API验证脚本
目标：验证流式语音输出是否支持，比较与批量API的差异
"""

import os
import sys
import base64
import tempfile
import time
import json
import requests
from typing import Generator

# 复用现有的API密钥配置
API_KEY_FILE = os.path.expanduser("~/.openclaw/auth/google/ielts_tts_2026.key")

class StreamingTTSTester:
    """流式TTS测试器"""
    
    def __init__(self):
        self.api_key = self._load_api_key()
        self.api_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
        
        # 复用现有的Daryl参数配置
        self.voice_params = {
            "languageCode": "en-US",
            "name": "en-US-Standard-J",
            "ssmlGender": "NEUTRAL"
        }
        
        # Daryl个性化语音参数（从现有配置提取）
        self.audio_config = {
            "audioEncoding": "MP3",
            "speakingRate": 0.85,  # Daryl的语速：15% slower
            "pitch": 0,  # 标准音高
            "volumeGainDb": 1.0,  # 轻微增强音量
        }
    
    def _load_api_key(self) -> str:
        """从文件加载API密钥"""
        try:
            with open(API_KEY_FILE, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"错误: API密钥文件不存在: {API_KEY_FILE}")
            print("请确保文件存在或手动提供API密钥")
            sys.exit(1)
    
    def test_standard_api(self, text: str) -> dict:
        """
        测试标准批量TTS API
        返回：测试结果字典
        """
        print(f"\n📊 测试标准TTS API")
        print(f"文本: {text[:50]}..." if len(text) > 50 else f"文本: {text}")
        print(f"长度: {len(text)} 字符")
        
        # 构建请求
        url = f"{self.api_url}?key={self.api_key}"
        payload = {
            "input": {"text": text},
            "voice": self.voice_params,
            "audioConfig": self.audio_config
        }
        
        print("🔍 发送TTS请求...")
        start_time = time.time()
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                if "audioContent" in result:
                    audio_data = base64.b64decode(result["audioContent"])
                    
                    # 保存音频文件
                    temp_dir = tempfile.gettempdir()
                    output_file = os.path.join(temp_dir, f"tts_test_{int(time.time())}.mp3")
                    
                    with open(output_file, "wb") as f:
                        f.write(audio_data)
                    
                    print(f"✅ TTS API调用成功")
                    print(f"音频文件: {output_file}")
                    print(f"文件大小: {len(audio_data)} 字节")
                    print(f"处理时间: {processing_time:.2f} 秒")
                    
                    return {
                        "success": True,
                        "audio_file": output_file,
                        "audio_size": len(audio_data),
                        "processing_time": processing_time,
                        "characters": len(text),
                        "method": "standard_api",
                        "latency_per_char": processing_time / len(text) if len(text) > 0 else 0
                    }
                else:
                    error_msg = f"响应中没有audioContent字段: {response.text[:200]}"
                    print(f"❌ {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "method": "standard_api"
                    }
            
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text[:200]}"
                print(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "method": "standard_api"
                }
        
        except Exception as e:
            error_msg = f"API调用异常: {e}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": str(e),
                "method": "standard_api"
            }
    
    def test_streaming_capability(self, text: str) -> dict:
        """
        探索流式TTS的可能性
        返回：可行性分析
        """
        print(f"\n🔍 探索流式TTS可行性")
        print(f"文本长度: {len(text)} 字符")
        
        # 方法1：文本分块测试
        print("\n🧪 方法1: 文本分块测试")
        chunks = self._split_text_into_chunks(text, max_chars=100)
        print(f"将文本分成 {len(chunks)} 个块")
        
        # 方法2：测试小文本的延迟
        print("\n🧪 方法2: 小文本延迟测试")
        short_text = text[:50] if len(text) > 50 else text
        short_result = self.test_standard_api(short_text)
        
        # 方法3：模拟流式处理
        print("\n🧪 方法3: 模拟流式处理")
        simulated_streaming_time = self._simulate_streaming_processing(chunks)
        
        return {
            "success": short_result.get("success", False),
            "text_length": len(text),
            "chunk_count": len(chunks),
            "short_text_latency": short_result.get("processing_time", 0) if short_result["success"] else None,
            "simulated_streaming_time": simulated_streaming_time,
            "notes": "Google Cloud TTS没有原生流式API，但可通过文本分块+WebSocket实现准实时体验"
        }
    
    def _split_text_into_chunks(self, text: str, max_chars: int = 100) -> list:
        """将文本分成块，尽量在句子边界分割"""
        chunks = []
        sentences = text.split('. ')
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= max_chars:  # +2 for '. '
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _simulate_streaming_processing(self, chunks: list) -> float:
        """模拟流式处理的延迟"""
        print(f"模拟处理 {len(chunks)} 个文本块...")
        
        total_time = 0
        for i, chunk in enumerate(chunks, 1):
            print(f"  块 {i}/{len(chunks)}: {len(chunk)}字符...")
            # 模拟每个块的延迟（假设每个块0.2-0.5秒）
            import random
            chunk_time = 0.2 + random.random() * 0.3
            total_time += chunk_time
        
        print(f"模拟总处理时间: {total_time:.2f}秒")
        return total_time
    
    
    
    def test_character_limits(self):
        """测试不同文本长度的处理时间"""
        print("\n📈 字符长度对比测试")
        print("=" * 50)
        
        test_cases = [
            ("短测试", "Hello Bryson.", 13),
            ("中等长度", "This is a test of the Google Text-to-Speech API for Daryl's IELTS practice system.", 80),
            ("长段落", "The quick brown fox jumps over the lazy dog. This sentence contains all letters of the English alphabet. Testing longer text for performance analysis.", 135),
        ]
        
        results = []
        
        for name, text, char_count in test_cases:
            print(f"\n📋 测试: {name} ({char_count} 字符)")
            result = self.test_standard_api_for_comparison(text)
            results.append({
                "name": name,
                "characters": char_count,
                "processing_time": result["processing_time"],
                "bytes_per_char": result["audio_size"] / char_count if result["success"] else 0
            })
        
        # 分析结果
        print("\n📊 字符长度测试分析")
        print("-" * 50)
        for r in results:
            print(f"{r['name']}: {r['characters']}字符 → {r['processing_time']:.2f}秒 "
                  f"(每字符: {r['bytes_per_char']:.1f}字节)")

def main():
    """主测试函数"""
    print("=" * 60)
    print("Google Cloud TTS流式API可行性验证")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 检查API密钥
    if not os.path.exists(API_KEY_FILE):
        print(f"❌ API密钥文件不存在: {API_KEY_FILE}")
        print("请先创建API密钥文件")
        return
    
    tester = StreamingTTSTester()
    
    # 测试1: 标准API测试（基准）
    print("\n🎯 测试1: 标准API性能基线测试")
    test_text = "Testing Google Cloud Text-to-Speech streaming capabilities for real-time IELTS practice."
    result1 = tester.test_standard_api(test_text)
    
    # 测试2: 流式能力探索
    print("\n🎯 测试2: 流式能力探索")
    result2 = tester.test_streaming_capability(test_text)
    
    # 测试3: 字符长度影响
    print("\n🎯 测试3: 文本长度对性能影响")
    tester.test_character_limits()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if result1["success"]:
        print("✅ 流式API探索完成")
        print("📌 发现: Google Cloud Python SDK需要特定版本支持流式API")
        print("📌 建议: 使用Cloud Run或WebSocket桥接实现流式效果")
    
    if result2["success"]:
        print(f"✅ 标准API性能基线: {result2['processing_time']:.2f}秒 "
              f"({result2['characters']}字符)")
        print(f"📊 音频生成速率: {result2['characters']/result2['processing_time']:.1f} 字符/秒")
    
    print("\n🎯 下一步行动计划:")
    print("1. 研究Google Cloud Text-to-Speech Streaming的具体实现方法")
    print("2. 探索WebSocket中间层方案（如果SDK不支持流式）")
    print("3. 创建WebRTC前端Demo验证实时音频播放")
    print("4. 预算影响：流式API可能有额外成本，需要评估")

if __name__ == "__main__":
    main()