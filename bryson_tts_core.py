#!/usr/bin/env python3
"""
Bryson的TTS语音交互核心模块
基于Google Cloud Text-to-Speech API
包含Daryl评估结果的个性化语音参数
"""

import os
import sys
import json
import base64
import tempfile
import subprocess
import requests
from typing import Dict, Any, Optional, Tuple

# API密钥配置
API_KEY_FILE = os.path.expanduser("~/.openclaw/auth/google/ielts_tts_2026.key")

class DarylTTSParameters:
    """基于Daryl评估结果的个性化语音参数"""
    
    def __init__(self):
        # 从昨晚的英语水平评估结果获取参数
        # Daryl_IELTS_Level: 5.5-6.0 → Speech_Rate: 0.85x_normal
        # Chinese_Logic_Challenge: true → Sentence_Complexity: simplified  
        # Business_Priority: investor_pitch → Tone_Emphasis: confidence_+30%
        # Vocabulary_Focus: financial_terms → Pronunciation_Precision: +40%
        # Motivation_Triple: daily_life + career + funding → Scenario_Weighting: [0.2, 0.3, 0.5]
        
        self.parameters = {
            # 1. 语速控制 (针对IELTS 5.5-6.0水平)
            "speaking_rate": 0.85,  # 15% slower (0.85x normal)
            
            # 2. 语调控制 (针对商务演示)
            "pitch": 0,  # 标准音高
            "volume_gain_db": 1.0,  # 轻微增强音量
            
            # 3. 发音控制 (针对财务术语)
            "speaking_rate_variation": 0.1,  # 轻微变化保持自然
            "pronunciation_focus": "financial_terms",
            
            # 4. 句子复杂度 (针对中文逻辑挑战)
            "sentence_max_length": 15,  # 单词数限制
            "prefer_simple_sentences": True,
            
            # 5. 场景权重 (基于Daryl的动机)
            "scenario_weights": {
                "investor_pitch": 0.5,      # 融资演示 (最高优先级)
                "career_development": 0.3,  # 职业发展
                "daily_conversation": 0.2   # 日常对话
            }
        }
    
    def get_voice_params(self, scenario: str = "default") -> Dict[str, Any]:
        """获取特定场景的语音参数"""
        base_params = {
            "speakingRate": self.parameters["speaking_rate"],
            "pitch": self.parameters["pitch"],
            "volumeGainDb": self.parameters["volume_gain_db"]
        }
        
        if scenario == "investor_pitch":
            # 投资者演示场景: 更自信、更清晰
            base_params["speakingRate"] = 0.90  # 稍快一些保持活力
            base_params["pitch"] = 2  # 稍高音调增加说服力
        
        elif scenario == "financial_report":
            # 财务报告场景: 更准确、更专业
            base_params["speakingRate"] = 0.80  # 更慢确保发音准确
            base_params["pitch"] = -1  # 稍低音调增加权威性
        
        elif scenario == "daily_conversation":
            # 日常对话场景: 更自然、更流畅
            base_params["speakingRate"] = 1.0  # 正常速度
            base_params["volumeGainDb"] = 0  # 标准音量
        
        return base_params

class GoogleTTSClient:
    """Google Cloud TTS客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._load_api_key()
        self.api_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
        self.daryl_params = DarylTTSParameters()
        
        # 语音配置 (基于Daryl的商务需求)
        self.voice_configs = {
            "default": {
                "languageCode": "en-US",
                "name": "en-US-Standard-J",  # 中性、专业的声音
                "ssmlGender": "NEUTRAL"
            },
            "investor_male": {
                "languageCode": "en-US",
                "name": "en-US-Standard-D",  # 深沉的商务男声
                "ssmlGender": "MALE"
            },
            "financial_female": {
                "languageCode": "en-US", 
                "name": "en-US-Standard-F",  # 清晰的商务女声
                "ssmlGender": "FEMALE"
            },
            "friendly": {
                "languageCode": "en-US",
                "name": "en-US-Standard-A",  # 友好的标准声音
                "ssmlGender": "FEMALE"
            }
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
    
    def _preprocess_text_for_daryl(self, text: str) -> str:
        """为Daryl预处理文本 (基于他的评估结果)"""
        # 简化句子结构 (针对中文逻辑挑战)
        # 这个功能会在后续版本中增强
        
        # 当前版本: 确保句子长度合理
        sentences = text.split('. ')
        if len(sentences) > 3:
            # 如果文本太长，取前三个句子
            text = '. '.join(sentences[:3]) + '.'
        
        return text
    
    def synthesize_speech(self, text: str, 
                         voice_type: str = "default",
                         scenario: str = "default",
                         output_file: Optional[str] = None) -> Tuple[bool, str]:
        """
        合成语音
        
        Args:
            text: 要转换为语音的文本
            voice_type: 声音类型 (default, investor_male, financial_female, friendly)
            scenario: 场景 (default, investor_pitch, financial_report, daily_conversation)
            output_file: 输出音频文件路径 (可选)
        
        Returns:
            (success, message_or_filepath)
        """
        # 预处理文本
        text = self._preprocess_text_for_daryl(text)
        
        # 获取语音配置
        voice_config = self.voice_configs.get(voice_type, self.voice_configs["default"])
        
        # 获取Daryl参数
        audio_params = self.daryl_params.get_voice_params(scenario)
        
        # 构建请求
        url = f"{self.api_url}?key={self.api_key}"
        payload = {
            "input": {"text": text},
            "voice": voice_config,
            "audioConfig": {
                "audioEncoding": "MP3",
                **audio_params
            }
        }
        
        print(f"正在合成语音...")
        print(f"文本长度: {len(text)} 字符")
        print(f"场景: {scenario}")
        print(f"语音类型: {voice_type}")
        
        try:
            # 发送请求
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                
                if "audioContent" in result:
                    # 解码音频数据
                    audio_data = base64.b64decode(result["audioContent"])
                    
                    # 保存到文件
                    if not output_file:
                        # 创建临时文件
                        temp_dir = tempfile.gettempdir()
                        output_file = os.path.join(temp_dir, f"bryson_tts_{hash(text) % 10000}.mp3")
                    
                    with open(output_file, "wb") as f:
                        f.write(audio_data)
                    
                    print(f"✅ 语音合成成功!")
                    print(f"音频文件: {output_file}")
                    print(f"文件大小: {len(audio_data)} 字节")
                    
                    return True, output_file
                else:
                    error_msg = f"响应中没有audioContent字段: {response.text[:200]}"
                    print(f"❌ {error_msg}")
                    return False, error_msg
            
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text[:200]}"
                print(f"❌ {error_msg}")
                return False, error_msg
        
        except Exception as e:
            error_msg = f"语音合成异常: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def play_audio(self, audio_file: str) -> bool:
        """播放音频文件"""
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["afplay", audio_file], timeout=10)
                print(f"✅ 音频播放完成: {audio_file}")
                return True
            elif sys.platform == "linux":
                # Linux系统可能需要安装播放器
                subprocess.run(["mpg123", audio_file], timeout=10)
                return True
            else:
                print(f"⚠️ 不支持的操作系统: {sys.platform}")
                return False
        except subprocess.TimeoutExpired:
            print("⚠️ 音频播放超时 (可能文件过长)")
            return False
        except Exception as e:
            print(f"❌ 音频播放失败: {e}")
            return False
    
    def text_to_speech(self, text: str, 
                      voice_type: str = "default",
                      scenario: str = "default",
                      play_immediately: bool = True) -> Tuple[bool, str]:
        """
        完整流程: 文本转语音并播放
        
        Returns:
            (success, message_or_filepath)
        """
        # 合成语音
        success, result = self.synthesize_speech(text, voice_type, scenario)
        
        if success:
            audio_file = result
            if play_immediately:
                # 播放音频
                play_success = self.play_audio(audio_file)
                if not play_success:
                    print(f"⚠️ 语音合成成功但播放失败")
                    print(f"音频文件存储在: {audio_file}")
            
            return True, audio_file
        else:
            return False, result

def test_basic_tts():
    """基础TTS功能测试"""
    print("=" * 60)
    print("Bryson TTS模块 - 基础功能测试")
    print("=" * 60)
    
    tts = GoogleTTSClient()
    
    # 测试1: 默认设置
    print("\n📌 测试1: 默认语音设置")
    text1 = "Hello Daryl, this is Bryson. I'm ready to help you with your English practice."
    success1, result1 = tts.text_to_speech(text1, play_immediately=False)
    
    if success1:
        print(f"✅ 测试1成功: {result1}")
    
    # 测试2: 投资者演示场景
    print("\n📌 测试2: 投资者演示场景")
    text2 = "Our company provides innovative textile solutions with a focus on sustainability and quality."
    success2, result2 = tts.text_to_speech(text2, voice_type="investor_male", 
                                          scenario="investor_pitch", play_immediately=False)
    
    if success2:
        print(f"✅ 测试2成功: {result2}")
    
    # 测试3: 财务报告场景
    print("\n📌 测试3: 财务报告场景")
    text3 = "The quarterly financial report shows a revenue growth of fifteen percent compared to the same period last year."
    success3, result3 = tts.text_to_speech(text3, voice_type="financial_female",
                                          scenario="financial_report", play_immediately=False)
    
    if success3:
        print(f"✅ 测试3成功: {result3}")
    
    # 测试4: 日常对话场景
    print("\n📌 测试4: 日常对话场景")
    text4 = "How was your day? Did you have any interesting conversations?"
    success4, result4 = tts.text_to_speech(text4, voice_type="friendly",
                                          scenario="daily_conversation", play_immediately=False)
    
    if success4:
        print(f"✅ 测试4成功: {result4}")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结:")
    successes = [success1, success2, success3, success4]
    print(f"✅ 成功: {sum(successes)} / {len(successes)}")
    
    if all(successes):
        print("🎉 所有TTS功能测试通过!")
        print("\n下一步:")
        print("1. ✅ TTS核心模块就绪")
        print("2. ⏳ 集成到Bryson对话系统")
        print("3. 📊 字符用量监控系统")
        print("4. 🎤 投资者演示模板库")
    else:
        print("⚠️ 部分测试失败，需要调试")

def main():
    """主函数"""
    print("Bryson TTS语音交互核心模块")
    print(f"API密钥文件: {API_KEY_FILE}")
    print(f"操作系统: {sys.platform}")
    print()
    
    # 检查API密钥
    if not os.path.exists(API_KEY_FILE):
        print("❌ API密钥文件不存在")
        print(f"请在 {API_KEY_FILE} 中保存Google Cloud API密钥")
        return
    
    # 运行测试
    test_basic_tts()

if __name__ == "__main__":
    main()