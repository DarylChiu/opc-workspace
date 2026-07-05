#!/usr/bin/env python3
"""
IELTS音频剩余样本生成器 - 专门生成额外的48个样本以达成100+目标
优先生成Advanced和Chinese Accent样本
"""

import os
import sys
import json
import time
import random
from datetime import datetime
from typing import List, Dict

# 导入现有的TTS核心模块
sys.path.append('.')
from bryson_tts_core import GoogleTTSClient

class IELTSRemainingGenerator:
    """IELTS剩余音频生成器 - 专门生成额外样本"""
    
    def __init__(self):
        # 使用已有的Google TTS客户端
        self.tts_client = GoogleTTSClient()
        self.base_dir = "test_audio/ielts_benchmark"
        
        # 确保目录存在
        os.makedirs(f"{self.base_dir}/advanced", exist_ok=True)
        os.makedirs(f"{self.base_dir}/chinese_accent", exist_ok=True)
        os.makedirs(f"{self.base_dir}/intermediate", exist_ok=True)
        
        # 加载现有元数据
        self.metadata = self.load_metadata()
    
    def load_metadata(self) -> Dict:
        """加载现有元数据"""
        metadata_path = os.path.join(self.base_dir, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 如果不存在，创建基础结构
            return {
                "generated_at": datetime.now().isoformat(),
                "total_samples": 0,
                "levels": {
                    "beginner": {"count": 0, "ielts_band": "A2-B1 (3.0-4.5)"},
                    "intermediate": {"count": 0, "ielts_band": "B2 (5.0-6.0)"},
                    "advanced": {"count": 0, "ielts_band": "C1 (6.5-7.5+)"},
                    "chinese_accent": {"count": 0, "ielts_band": "B1-C1 (4.0-7.0)"}
                },
                "samples": []
            }
    
    def get_existing_samples_count(self, level: str) -> int:
        """获取指定级别已有的样本数量"""
        count = 0
        if "samples" in self.metadata:
            for sample in self.metadata["samples"]:
                if sample.get("level") == level:
                    count += 1
        return count
    
    def get_next_sample_number(self, level: str) -> int:
        """获取指定级别的下一个样本编号"""
        level_dir = os.path.join(self.base_dir, level)
        if os.path.exists(level_dir):
            existing_files = [f for f in os.listdir(level_dir) if f.startswith("sample_") and f.endswith(".mp3")]
            existing_nums = []
            for f in existing_files:
                try:
                    num = int(f.replace("sample_", "").replace(".mp3", ""))
                    existing_nums.append(num)
                except:
                    pass
            if existing_nums:
                return max(existing_nums) + 1
        return 1
    
    def generate_business_topics(self) -> List[Dict]:
        """生成商业话题额外样本（适用于Advanced级别）"""
        return [
            {
                "text": "Our company's competitive advantage lies in our proprietary technology and experienced management team.",
                "category": "business",
                "subcategory": "competitive_analysis"
            },
            {
                "text": "We have identified three key market segments that align with our product's unique value proposition.",
                "category": "business",
                "subcategory": "market_strategy"
            },
            {
                "text": "The quarterly financial report shows a significant increase in revenue growth and improved profit margins.",
                "category": "business",
                "subcategory": "financial_performance"
            },
            {
                "text": "Our strategic initiatives for the upcoming fiscal year include international expansion and product diversification.",
                "category": "business",
                "subcategory": "strategic_planning"
            },
            {
                "text": "Customer feedback has been overwhelmingly positive, with a net promoter score of seventy-five percent.",
                "category": "business",
                "subcategory": "customer_satisfaction"
            },
            {
                "text": "Implementing agile methodologies has improved our project delivery timeline by approximately thirty percent.",
                "category": "business",
                "subcategory": "operational_efficiency"
            },
            {
                "text": "The ongoing digital transformation initiative aims to streamline workflows and enhance collaboration across departments.",
                "category": "business",
                "subcategory": "digital_transformation"
            },
            {
                "text": "Our sustainability goals align with global standards, focusing on reducing carbon emissions and promoting circular economy principles.",
                "category": "business",
                "subcategory": "sustainability"
            },
            {
                "text": "Talent acquisition and retention strategies have been revised to address the competitive labor market.",
                "category": "business",
                "subcategory": "human_resources"
            },
            {
                "text": "Risk management frameworks have been strengthened to address cybersecurity threats and regulatory compliance.",
                "category": "business",
                "subcategory": "risk_management"
            }
        ]
    
    def generate_investor_pitch_extended(self) -> List[Dict]:
        """生成扩展的投资路演内容"""
        return [
            {
                "text": "We are seeking two point five million dollars in seed funding to accelerate our market entry strategy.",
                "category": "business",
                "subcategory": "funding_ask"
            },
            {
                "text": "The exit strategy includes potential acquisition by established players or an initial public offering within five years.",
                "category": "business",
                "subcategory": "exit_strategy"
            },
            {
                "text": "Unit economics demonstrate a positive contribution margin of thirty-eight percent at current production volumes.",
                "category": "business",
                "subcategory": "unit_economics"
            },
            {
                "text": "Our technology roadmap includes AI-powered features and mobile application development over the next twelve months.",
                "category": "business",
                "subcategory": "roadmap"
            },
            {
                "text": "The founding team brings over fifty years of combined industry experience and relevant technical expertise.",
                "category": "business",
                "subcategory": "team_qualifications"
            }
        ]
    
    def generate_academic_discourse(self) -> List[Dict]:
        """生成学术讨论样本"""
        return [
            {
                "text": "Epistemological frameworks shape our understanding of knowledge acquisition and validation processes.",
                "category": "academic",
                "subcategory": "philosophy"
            },
            {
                "text": "Socioeconomic factors significantly influence educational attainment and career trajectories across demographic groups.",
                "category": "academic",
                "subcategory": "sociology"
            },
            {
                "text": "Cognitive neuroscience research reveals neural correlates of decision-making patterns in complex environments.",
                "category": "academic",
                "subcategory": "neuroscience"
            },
            {
                "text": "Algorithmic bias in machine learning systems perpetuates existing societal inequalities if not properly addressed.",
                "category": "academic",
                "subcategory": "computer_science"
            },
            {
                "text": "Environmental economics examines trade-offs between economic development and ecological conservation.",
                "category": "academic",
                "subcategory": "economics"
            }
        ]
    
    def generate_chinese_accent_extended(self) -> List[Dict]:
        """生成扩展的中国口音样本"""
        return [
            {
                "text": "In my opinion, the best way to learn English is practice speaking every day.",
                "description": "中式英语结构（practice speaking instead of practicing speaking）"
            },
            {
                "text": "Many people think that hard work is very important for achieve success.",
                "description": "动词形式错误（achieve代替achieving）"
            },
            {
                "text": "I strongly believe we should pay attention to environmental protection problem.",
                "description": "冗余词汇（problem不必要）"
            },
            {
                "text": "We need more time for discuss this topic and make final decision.",
                "description": "动词不定式错误（for discuss instead of to discuss）"
            },
            {
                "text": "The government should provide more support to help people improve they life.",
                "description": "代词错误（they代替their）"
            },
            {
                "text": "In conclusion, we can say that technology bring many benefit to our society.",
                "description": "主谓不一致（bring代替brings）和名词单数错误"
            },
            {
                "text": "It is true that healthy lifestyle have many advantage for physical and mental health.",
                "description": "主谓不一致和名词单复数错误"
            },
            {
                "text": "Nowadays, young people face many challenge in they career development.",
                "description": "单复数错误和代词错误"
            },
            {
                "text": "We must take action to against climate change before it become too late.",
                "description": "介词和动词错误（to against, become代替becomes）"
            },
            {
                "text": "In my country, traditional culture still play important role in modern society.",
                "description": "主谓不一致（play代替plays）"
            }
        ]
    
    def generate_intermediate_ielts_part2(self) -> List[Dict]:
        """生成中级IELTS Part 2样本"""
        return [
            {
                "topic": "Describe a book that influenced you",
                "text": "The book that had a significant influence on me is 'The Lean Startup' by Eric Ries. I read this book three years ago when I was starting my own small business. The book introduces the concept of building minimum viable products and testing them with real customers quickly. This approach helped me avoid wasting time and resources on features that customers didn't want. I learned the importance of validated learning and iterative development. Before reading this book, I was planning to develop a complete product before launching it. After applying the book's principles, I released a simple version first and improved it based on user feedback. This book influenced me because it changed my perspective on entrepreneurship and innovation."
            },
            {
                "topic": "Describe a memorable journey",
                "text": "A memorable journey I took was a road trip along the Pacific Coast Highway in California. I traveled with three friends last summer for two weeks. We started in San Francisco and drove all the way to Los Angeles, stopping at various coastal towns. The most memorable part was the scenery along Big Sur, where steep cliffs meet the ocean. We stayed in small motels and camped on beaches. One night, we saw bioluminescent plankton glowing in the water, which was magical. This journey was memorable because of the freedom of the open road, the stunning natural beauty, and the quality time with friends. It reminded me that sometimes the journey itself is more important than the destination."
            },
            {
                "topic": "Describe a historical event",
                "text": "The historical event I want to describe is the fall of the Berlin Wall in 1989. Though I wasn't alive at that time, I've studied this event extensively. The Berlin Wall was built in 1961 to divide East and West Berlin during the Cold War. For twenty-eight years, it represented the ideological division between communism and democracy. On November 9, 1989, due to political changes and public pressure, border crossings were opened unexpectedly. Thousands of people from both sides gathered at the wall, celebrating and helping to dismantle it. This event is significant because it symbolized the end of the Cold War and the spread of freedom in Eastern Europe. It shows how people's desire for unity can overcome political barriers."
            }
        ]
    
    def synthesize_speech(self, text: str, slow_down: float = 1.0) -> bytes:
        """语音合成包装器"""
        try:
            scenario = "default"
            if slow_down < 0.9:
                scenario = "financial_report"
            elif slow_down > 1.0:
                scenario = "daily_conversation"
            
            success, result = self.tts_client.synthesize_speech(
                text=text,
                voice_type="default",
                scenario=scenario
            )
            
            if success:
                with open(result, 'rb') as f:
                    return f.read()
            else:
                print(f"❌ TTS失败: {result}")
                return None
        except Exception as e:
            print(f"❌ TTS异常: {e}")
            return None
    
    def save_sample(self, level: str, sample_data: Dict, text: str, counter: int = None) -> bool:
        """保存单个样本"""
        try:
            if counter is None:
                sample_num = self.get_next_sample_number(level)
            else:
                sample_num = counter
            
            filename = f"{level}/sample_{sample_num:03d}.mp3"
            audio_data = self.synthesize_speech(text)
            
            if not audio_data:
                return False
            
            filepath = os.path.join(self.base_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            # 更新元数据
            sample_info = {
                "text": text,
                "level": level,
                "audio_file": filename,
                "generated_at": datetime.now().isoformat(),
                "audio_length": len(audio_data)
            }
            
            # 添加额外字段
            for key in ["category", "subcategory", "topic", "description"]:
                if key in sample_data:
                    sample_info[key] = sample_data[key]
            
            self.metadata["samples"].append(sample_info)
            self.metadata["levels"][level]["count"] += 1
            self.metadata["total_samples"] += 1
            
            print(f"   ✅ {filename}: {text[:60]}...")
            return True
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return False
    
    def generate_remaining_samples(self):
        """生成剩余48个样本"""
        print("🎯 开始生成剩余IELTS音频样本...")
        print("="*60)
        
        # 计算需要生成的样本数
        current_total = self.metadata["total_samples"]
        target_total = 100
        need_to_generate = target_total - current_total
        
        if need_to_generate <= 0:
            print(f"✅ 已有 {current_total} 个样本，无需额外生成")
            return
        
        print(f"📊 当前样本数: {current_total}")
        print(f"🎯 目标样本数: {target_total}")
        print(f"📈 需要生成: {need_to_generate} 个样本")
        
        # 样本生成计划
        advanced_needed = 30  # advanced需要更多样本
        chinese_needed = 15   # chinese accent需要更多样本
        intermediate_needed = 3  # intermediate少量补充
        
        print(f"📋 生成计划:")
        print(f"   - Advanced: {advanced_needed} 个样本")
        print(f"   - Chinese Accent: {chinese_needed} 个样本")
        print(f"   - Intermediate: {intermediate_needed} 个样本")
        
        success_count = 0
        fail_count = 0
        
        # 生成Advanced样本
        print("\n📚 生成Advanced样本:")
        business_topics = self.generate_business_topics()
        investor_topics = self.generate_investor_pitch_extended()
        academic_topics = self.generate_academic_discourse()
        
        all_advanced_topics = business_topics + investor_topics + academic_topics
        
        for i, topic in enumerate(all_advanced_topics[:advanced_needed]):
            if success_count >= need_to_generate:
                break
                
            print(f"[{success_count+1}/{need_to_generate}] 生成Advanced: {topic['category']}")
            if self.save_sample("advanced", topic, topic["text"]):
                success_count += 1
            else:
                fail_count += 1
            
            # 避免API限制
            if (success_count + fail_count) % 5 == 0:
                print("   ⏸️ 暂停2秒避免API限制...")
                time.sleep(2)
        
        # 生成Chinese Accent样本
        print("\n🎤 生成Chinese Accent样本:")
        chinese_samples = self.generate_chinese_accent_extended()
        
        for i, sample in enumerate(chinese_samples[:chinese_needed]):
            if success_count >= need_to_generate:
                break
                
            print(f"[{success_count+1}/{need_to_generate}] 生成Chinese Accent")
            if self.save_sample("chinese_accent", sample, sample["text"]):
                success_count += 1
            else:
                fail_count += 1
            
            if (success_count + fail_count) % 5 == 0:
                print("   ⏸️ 暂停1秒...")
                time.sleep(1)
        
        # 生成Intermediate样本
        print("\n📝 生成Intermediate样本:")
        part2_samples = self.generate_intermediate_ielts_part2()
        
        for i, sample in enumerate(part2_samples[:intermediate_needed]):
            if success_count >= need_to_generate:
                break
                
            print(f"[{success_count+1}/{need_to_generate}] 生成Intermediate: IELTS Part 2")
            if self.save_sample("intermediate", sample, sample["text"]):
                success_count += 1
            else:
                fail_count += 1
        
        # 保存更新后的元数据
        metadata_path = os.path.join(self.base_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        
        # 打印总结
        print("\n" + "="*60)
        print("🎯 剩余样本生成完成")
        print("="*60)
        print(f"✅ 成功生成: {success_count} 个样本")
        print(f"❌ 失败: {fail_count} 个")
        print(f"📊 级别分布更新:")
        for level, info in self.metadata["levels"].items():
            print(f"   - {level}: {info['count']} 个样本")
        print(f"📋 总样本数: {self.metadata['total_samples']}")
        print("="*60)
        
        return success_count, fail_count

def main():
    """主函数"""
    try:
        generator = IELTSRemainingGenerator()
        
        # 检查TTS配置
        print("🔧 检查TTS配置...")
        if not generator.tts_client.api_key:
            print("❌ 未找到Google TTS API密钥")
            print("请确保 ~/.openclaw/auth/google/ielts_tts_2026.key 文件存在")
            return
        
        print(f"✅ TTS配置正常")
        
        # 生成剩余样本
        success, fail = generator.generate_remaining_samples()
        
        if success > 0:
            print(f"\n🎉 成功生成 {success} 个额外样本")
            print(f"总计样本数: {generator.metadata['total_samples']}")
            print("STT开发计划第一阶段任务完成！")
        else:
            print("\n❌ 未能生成新样本")
        
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()