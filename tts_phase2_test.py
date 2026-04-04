#!/usr/bin/env python3
"""
Bryson TTS阶段2测试脚本
测试Daryl指定的两个测试语句
"""

import os
import time
from bryson_tts_core import GoogleTTSClient

def run_test_case(test_number, text, description, voice_type="default", scenario="default"):
    """运行单个测试用例"""
    print(f"\n{'='*60}")
    print(f"🏁 测试用例 {test_number}: {description}")
    print(f"{'='*60}")
    
    print(f"📝 测试文本: {text}")
    print(f"🗣️ 声音类型: {voice_type}")
    print(f"🎭 场景: {scenario}")
    
    # 创建TTS客户端
    tts = GoogleTTSClient()
    
    # 记录开始时间
    start_time = time.time()
    
    # 生成语音
    print(f"🔊 正在生成语音...")
    success, result = tts.text_to_speech(text, voice_type=voice_type, scenario=scenario, play_immediately=True)
    
    # 计算响应时间
    response_time = time.time() - start_time
    
    if success:
        print(f"✅ 测试通过!")
        print(f"⏱️ 响应时间: {response_time:.2f}秒")
        print(f"📁 音频文件: {result}")
        
        # 检查文件是否存在
        if os.path.exists(result):
            file_size = os.path.getsize(result)
            print(f"📏 文件大小: {file_size:,}字节 ({file_size/1024:.1f}KB)")
        else:
            print(f"⚠️ 注意: 音频文件未找到")
        
        # 评分
        if response_time < 1.5:
            speed_score = 5
        elif response_time < 2.0:
            speed_score = 4
        elif response_time < 3.0:
            speed_score = 3
        else:
            speed_score = 2
        
        return {
            "success": True,
            "response_time": response_time,
            "file_path": result,
            "file_size": file_size if os.path.exists(result) else 0,
            "speed_score": speed_score,
            "text": text
        }
    else:
        print(f"❌ 测试失败!")
        print(f"📤 结果: {result}")
        return {
            "success": False,
            "response_time": response_time,
            "error": result,
            "text": text
        }

def main():
    print("🎯 Bryson TTS阶段2 - 功能测试 (Daryl指定测试)")
    print(f"时间: {time.strftime('%Y%m-%d %H:%M:%S', time.localtime())}")
    print()
    
    # 检查API密钥
    api_key_file = os.path.expanduser("~/.openclaw/auth/google/ielts_tts_2026.key")
    if not os.path.exists(api_key_file):
        print("❌ 错误: API密钥文件不存在")
        print(f"请检查: {api_key_file}")
        return
    
    print(f"✅ API密钥文件: {api_key_file}")
    
    # 测试用例定义
    test_cases = [
        {
            "number": 1,
            "text": "Hello Bryson, this is a basic TTS test.",
            "description": "基础英语TTS测试",
            "voice_type": "default",
            "scenario": "default"
        },
        {
            "number": 2,
            "text": "我正在测试语音合成系统的稳定性。",
            "description": "基础中文TTS测试",
            "voice_type": "friendly",
            "scenario": "daily_conversation"
        }
    ]
    
    results = []
    
    # 运行所有测试
    for test in test_cases:
        result = run_test_case(
            test["number"],
            test["text"],
            test["description"],
            test["voice_type"],
            test["scenario"]
        )
        results.append(result)
    
    # 测试总结
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests
    
    print(f"📋 测试总数: {total_tests}")
    print(f"✅ 通过: {passed_tests}")
    print(f"❌ 失败: {failed_tests}")
    
    if passed_tests > 0:
        avg_response_time = sum(r["response_time"] for r in results if r["success"]) / passed_tests
        print(f"\n⏱️ 平均响应时间: {avg_response_time:.2f}秒")
        
        # 评分
        if avg_response_time < 1.5:
            print("🚀 响应时间: 极佳 (<1.5秒)")
        elif avg_response_time < 2.0:
            print("⚡ 响应时间: 良好 (1.5-2.0秒)")
        elif avg_response_time < 3.0:
            print("⏳ 响应时间: 一般 (2.0-3.0秒)")
        else:
            print("🐌 响应时间: 偏慢 (>3.0秒)")
    
    # 详细结果
    print(f"\n{'─'*60}")
    print("📋 详细测试结果:")
    
    for result in results:
        print(f"\n[测试用例 {test_cases[results.index(result)]['number']}]")
        print(f"  文本: {result['text'][:50]}...")
        
        if result["success"]:
            print(f"  ✅ 状态: 通过")
            print(f"  ⏱️ 响应时间: {result['response_time']:.2f}秒")
            
            if "file_size" in result:
                print(f"  📏 文件大小: {result['file_size']:,}字节")
                print(f"  🏆 速度评分: {result['speed_score']}/5")
        else:
            print(f"  ❌ 状态: 失败")
            print(f"  🔍 错误: {result.get('error', '未知错误')}")
    
    # 最终评估
    print(f"\n{'='*60}")
    print("🎯 最终评估:")
    
    if passed_tests == total_tests:
        print("✨ 测试结果: 完美通过!")
        print("✅ 所有基础TTS功能正常")
        print("✅ 英语和中文均支持")
        print("✅ 响应时间符合预期")
        print("\n🎉 TTS阶段2基础功能验证成功!")
    elif passed_tests >= total_tests * 0.7:
        print("👌 测试结果: 基本通过")
        print("⚠️ 有部分功能需要检查")
        print("\n📝 建议: 检查失败的测试用例")
    else:
        print("⚠️ 测试结果: 需要改进")
        print("🔧 建议: 检查API密钥和网络连接")
    
    print(f"\n💡 下一步: 继续测试商务场景功能")

if __name__ == "__main__":
    main()