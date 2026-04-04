#!/usr/bin/env python3
"""
Bryson TTS语音对话集成测试
演示如何在对话中集成语音功能
"""

import os
import sys
import time
from bryson_tts_core import GoogleTTSClient

class BrysonTTSDialogue:
    """Bryson TTS对话集成"""
    
    def __init__(self):
        print("初始化Bryson TTS对话系统...")
        self.tts = GoogleTTSClient()
        self.char_count = 0  # 字符用量统计
        self.audio_files = []  # 生成的音频文件列表
        
        print("✅ TTS客户端就绪")
        
    def say(self, text: str, scenario: str = "default") -> bool:
        """
        Bryson说出文本并播放语音
        
        Args:
            text: 要说的文本
            scenario: 场景 (default, investor_pitch, financial_report, daily_conversation)
        
        Returns:
            是否成功
        """
        print(f"\n[👤 Bryson] {text}")
        
        # 模拟打字效果
        self._typing_effect(text)
        
        # 更新字符统计
        self.char_count += len(text)
        
        # 根据场景选择声音
        voice_type = "default"
        if scenario == "investor_pitch":
            voice_type = "investor_male"
        elif scenario == "financial_report":
            voice_type = "financial_female"
        elif scenario == "daily_conversation":
            voice_type = "friendly"
        
        # 合成并播放语音
        success, audio_file = self.tts.text_to_speech(
            text, 
            voice_type=voice_type,
            scenario=scenario,
            play_immediately=True
        )
        
        if success:
            self.audio_files.append(audio_file)
            print(f"✅ 已生成并播放语音")
            return True
        else:
            print(f"❌ 语音生成失败: {audio_file}")
            return False
    
    def _typing_effect(self, text: str, delay: float = 0.03):
        """模拟打字效果 (可选)"""
        # 为保持速度，这里跳过实际效果
        pass
    
    def get_usage_stats(self) -> dict:
        """获取使用统计"""
        return {
            "characters_generated": self.char_count,
            "audio_files_created": len(self.audio_files),
            "estimated_cost": self.char_count / 1000000 * 4.0,  # Google TTS $4/百万字符
            "free_quota_remaining": max(0, 1000000 - self.char_count)
        }

def demonstration_dialogue():
    """演示对话 - 投资者演示场景"""
    print("=" * 70)
    print("Bryson TTS对话演示 - 投资者演示场景")
    print("=" * 70)
    
    bryson = BrysonTTSDialogue()
    
    print("\n🎯 场景: 投资者路演前练习")
    print("-" * 50)
    
    # 对话开始
    time.sleep(1)
    
    # 1. 自我介绍环节
    bryson.say("Good morning everyone. Thank you for joining us today.", "investor_pitch")
    time.sleep(2)
    
    bryson.say("My name is Daryl, and I'm the Financial Manager of our textile company in Vietnam.", "investor_pitch")
    time.sleep(2)
    
    # 2. 业务介绍环节
    bryson.say("We specialize in sustainable textile manufacturing with a focus on quality and innovation.", "investor_pitch")
    time.sleep(2)
    
    bryson.say("Our competitive advantage comes from our patented production techniques and strong supplier relationships.", "investor_pitch")
    time.sleep(2)
    
    # 3. 财务表现环节
    bryson.say("Financially, we've achieved fifteen percent revenue growth in the last quarter.", "financial_report")
    time.sleep(2)
    
    bryson.say("We're projecting twenty percent growth for the upcoming year, driven by new market expansion.", "financial_report")
    time.sleep(2)
    
    # 4. 融资需求环节
    bryson.say("To accelerate this growth, we're seeking one million dollars in funding.", "investor_pitch")
    time.sleep(2)
    
    bryson.say("These funds will be used for equipment upgrades and entering the European market.", "investor_pitch")
    time.sleep(2)
    
    # 5. 问答环节准备
    bryson.say("Now I'd be happy to answer any questions you might have.", "investor_pitch")
    time.sleep(2)
    
    # 演示结束
    print("\n" + "=" * 70)
    print("演示完成!")
    
    # 显示统计
    stats = bryson.get_usage_stats()
    print(f"\n📊 使用统计:")
    print(f"   生成字符: {stats['characters_generated']}")
    print(f"   音频文件: {stats['audio_files_created']}")
    print(f"   预估成本: ${stats['estimated_cost']:.6f}")
    print(f"   剩余免费配额: {stats['free_quota_remaining']:,} 字符")
    
    print(f"\n💾 音频文件保存在临时目录:")
    for file in bryson.audio_files[:3]:  # 显示前3个文件
        print(f"   - {file}")
    if len(bryson.audio_files) > 3:
        print(f"   ... 和 {len(bryson.audio_files)-3} 个其他文件")
    
    return bryson

def mini_english_practice():
    """简单的英语练习演示"""
    print("\n" + "=" * 70)
    print("Bryson TTS英语练习演示")
    print("=" * 70)
    
    bryson = BrysonTTSDialogue()
    
    print("\n📚 对话练习:")
    print("-" * 50)
    
    # 练习对话
    bryson.say("Hi Daryl, ready to practice some English?", "daily_conversation")
    time.sleep(2)
    
    bryson.say("Let's start with a simple self-introduction.", "daily_conversation")
    time.sleep(2)
    
    bryson.say("Imagine you're meeting potential business partners for the first time.", "investor_pitch")
    time.sleep(2)
    
    bryson.say("How would you introduce yourself and your company?", "daily_conversation")
    time.sleep(2)
    
    bryson.say("Remember to speak slowly and clearly.", "daily_conversation")
    time.sleep(2)
    
    bryson.say("Focus on your key strengths and achievements.", "investor_pitch")
    time.sleep(2)
    
    # 统计
    stats = bryson.get_usage_stats()
    print(f"\n📊 本次练习使用统计:")
    print(f"   字符数: {stats['characters_generated']}")
    print(f"   成本: ${stats['estimated_cost']:.6f}")
    
    print("\n🎯 实际使用时:")
    print("   1. Bryson会说出一段话")
    print("   2. 你可以跟着模仿发音")
    print("   3. 我们可以反复练习同一句话")
    print("   4. 重点关注投资者演示所需的语调")

def main():
    """主函数"""
    print("Bryson TTS语音对话集成演示")
    print("=" * 50)
    
    # 检查API密钥
    api_key_file = "/Users/zhaoyuzhao/.openclaw/auth/google/ielts_tts_2026.key"
    if not os.path.exists(api_key_file):
        print(f"❌ API密钥文件不存在: {api_key_file}")
        print("请确保已获取并保存Google Cloud API密钥")
        return
    
    print(f"✅ API密钥文件: {api_key_file}")
    print()
    
    print("选择演示模式:")
    print("1. 📈 投资者演示完整对话")
    print("2. 🎤 简单英语练习片段")
    print("3. 📊 仅统计信息（无播放）")
    
    try:
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            demonstration_dialogue()
        elif choice == "2":
            mini_english_practice()
        elif choice == "3":
            # 仅显示系统状态
            print(f"\n📊 系统状态:")
            print(f"   API密钥: {'✅ 存在' if os.path.exists(api_key_file) else '❌ 不存在'}")
            print(f"   密钥大小: {os.path.getsize(api_key_file) if os.path.exists(api_key_file) else 0} 字节")
            print(f"   免费配额: 每月1,000,000字符")
            print(f"   预估练习成本: 每1000字符约$0.004")
        else:
            print("无效选择")
    
    except KeyboardInterrupt:
        print("\n\n演示已取消")
    except Exception as e:
        print(f"演示出错: {e}")

if __name__ == "__main__":
    main()