#!/usr/bin/env python3
"""
IELTS口语考试音频生成器
生成基于公开考题的测试音频，用于STT准确性评估
"""

import os
import sys
import json
import base64
import time
import random
from datetime import datetime
import subprocess
from typing import List, Dict, Tuple, Optional
import requests

# 导入现有的TTS核心模块
sys.path.append('.')
from bryson_tts_core import GoogleTTSClient, DarylTTSParameters

class IELTSAudioGenerator:
    """IELTS口语考试音频生成器"""
    
    def __init__(self):
        # 使用已有的Google TTS客户端
        self.tts_client = GoogleTTSClient()
        self.base_dir = "test_audio/ielts_benchmark"
        
        # 确保目录存在
        os.makedirs(f"{self.base_dir}/beginner", exist_ok=True)
        os.makedirs(f"{self.base_dir}/intermediate", exist_ok=True)
        os.makedirs(f"{self.base_dir}/advanced", exist_ok=True)
        os.makedirs(f"{self.base_dir}/chinese_accent", exist_ok=True)
        
        # 初始化元数据文件
        self.metadata = {
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
    
    def generate_part1_topics(self) -> List[Dict]:
        """IELTS Part 1: 个人信息与日常话题"""
        return [
            {
                "category": "personal_information",
                "questions": [
                    {"question": "Can you tell me your full name?", "answer": "My full name is Li Ming, but you can call me David."},
                    {"question": "Where are you from?", "answer": "I'm from Shanghai, a vibrant city in eastern China."},
                    {"question": "Do you work or are you a student?", "answer": "I work as a financial analyst in a multinational company."},
                    {"question": "What do you like about your hometown?", "answer": "I like the food culture and the modern infrastructure in my hometown."}
                ]
            },
            {
                "category": "hobbies_and_interests",
                "questions": [
                    {"question": "What do you do in your free time?", "answer": "In my free time, I enjoy reading business books and playing basketball."},
                    {"question": "Do you like listening to music?", "answer": "Yes, I like listening to pop music, especially when I'm exercising."},
                    {"question": "What type of movies do you prefer?", "answer": "I prefer action movies and documentaries about technology."},
                    {"question": "Do you like traveling?", "answer": "Yes, I enjoy traveling to different countries to experience new cultures."}
                ]
            },
            {
                "category": "daily_activities",
                "questions": [
                    {"question": "What is your typical day like?", "answer": "I usually start work at 9 AM, have meetings in the afternoon, and exercise in the evening."},
                    {"question": "Do you prefer morning or evening?", "answer": "I prefer morning because I feel more energetic and productive."},
                    {"question": "How do you usually spend your weekends?", "answer": "I usually spend weekends with family, doing groceries, and relaxing at home."},
                    {"question": "Do you cook at home?", "answer": "Yes, I cook simple meals at home, like fried rice and vegetable dishes."}
                ]
            }
        ]
    
    def generate_part2_topics(self) -> List[Dict]:
        """IELTS Part 2: 长独白描述题卡"""
        return [
            {
                "topic": "Describe a skill you learned recently",
                "cue_card": "You should say:\n- What the skill is\n- Where and when you learned it\n- How you learned it\n- And explain why this skill is useful to you",
                "sample_answer": "Recently, I learned how to use Python for data analysis. I started learning this skill about three months ago through online courses. The main reason was to improve my work efficiency. At my job as a financial analyst, I need to process large amounts of data regularly. Before learning Python, I used Excel, which was time-consuming for complex calculations. Now with Python, I can automate many repetitive tasks. For example, I wrote a script that automatically generates financial reports. This saves me at least five hours every week. Another useful aspect is data visualization. With libraries like Matplotlib, I can create clear charts to present findings to my team. Overall, learning Python has made me more productive and confident in my abilities."
            },
            {
                "topic": "Describe an important decision you made",
                "cue_card": "You should say:\n- What the decision was\n- When you made it\n- How you made it\n- And explain why it was important",
                "sample_answer": "An important decision I made was to pursue an MBA degree while working full-time. I made this decision two years ago after realizing I needed stronger business knowledge for career advancement. The decision-making process involved careful consideration of costs, time commitment, and potential benefits. First, I researched different programs and compared their curricula. Then, I spoke with colleagues who had completed similar programs to understand the workload. Finally, I evaluated my financial situation to ensure I could afford the tuition. This decision was important because it significantly improved my business understanding. I learned about strategy, finance, and leadership in depth. As a result, I was promoted to a managerial position last year. The MBA also expanded my professional network, which has been valuable for business opportunities."
            },
            {
                "topic": "Describe a time you helped someone",
                "cue_card": "You should say:\n- Who you helped\n- How you helped them\n- Why they needed help\n- And explain how you felt about helping",
                "sample_answer": "I remember helping a new colleague who joined our team last year. His name is Tom, and he was struggling with our company's financial software. I noticed he was spending too much time on basic tasks and seemed frustrated. So, I offered to guide him through the software features. We scheduled one-hour sessions every Friday afternoon for a month. During these sessions, I showed him shortcuts, formulas, and reporting templates. I also shared documentation I had created for myself. Tom needed help because he came from a different industry and wasn't familiar with financial analysis tools. Helping him made me feel accomplished and useful. It was rewarding to see his confidence grow each week. Later, Tom told me that my help saved him at least a month of trial and error. This experience also improved my own teaching skills and patience."
            }
        ]
    
    def generate_part3_topics(self) -> List[Dict]:
        """IELTS Part 3: 抽象思考与讨论"""
        return [
            {
                "category": "education_and_learning",
                "questions": [
                    {"question": "How has technology changed education?", "answer": "Technology has revolutionized education by making learning more accessible and interactive. Online platforms allow students to access courses from anywhere in the world. Digital tools like simulations and virtual reality provide hands-on experiences that were previously impossible. Additionally, technology enables personalized learning, where content adapts to each student's pace and level. However, it's important to maintain a balance and ensure technology enhances rather than replaces human interaction in education."},
                    {"question": "What skills do you think are most important for young people today?", "answer": "In today's rapidly changing world, I believe adaptability and digital literacy are crucial skills for young people. The ability to learn new technologies quickly is essential as job requirements evolve constantly. Critical thinking is also important to navigate the vast amount of information available online. Furthermore, soft skills like communication and collaboration remain valuable, especially in remote work environments. Finally, emotional intelligence helps young people manage stress and build positive relationships in both personal and professional settings."},
                    {"question": "Do you think traditional classrooms will disappear in the future?", "answer": "While online learning will continue to grow, I don't believe traditional classrooms will disappear completely. Face-to-face interaction provides social development opportunities that are difficult to replicate online. Classrooms also offer structured environments that help some students focus better. However, I think we'll see more hybrid models combining the best of both approaches. Traditional classrooms might evolve to focus more on discussion, collaboration, and hands-on activities, while basic content delivery moves online. This blended approach can cater to different learning styles and needs."}
                ]
            },
            {
                "category": "business_and_work",
                "questions": [
                    {"question": "What are the advantages of working in a team?", "answer": "Working in a team offers several advantages. First, it brings together diverse perspectives and skills, leading to more creative solutions. Different team members can contribute specialized knowledge that no single person possesses. Second, teamwork allows sharing of workload, making complex projects more manageable. Third, collaboration provides learning opportunities as team members can learn from each other's expertise. Finally, teams often provide social support and motivation, which can improve job satisfaction and reduce stress during challenging projects."},
                    {"question": "How important is leadership in business success?", "answer": "Leadership plays a crucial role in business success. Effective leaders provide clear vision and direction, aligning team efforts toward common goals. They inspire and motivate employees, which directly impacts productivity and innovation. Good leaders also create positive work cultures that retain talented staff. In times of crisis or change, strong leadership becomes even more critical for navigating challenges and making difficult decisions. However, leadership should be combined with good management systems to ensure sustainable success. The best leaders empower their teams rather than controlling every detail."},
                    {"question": "What impact has globalization had on business?", "answer": "Globalization has significantly transformed business in multiple ways. It has expanded market opportunities, allowing companies to reach customers worldwide. This has led to increased competition, forcing businesses to innovate and improve quality. Globalization has also enabled access to global talent pools and supply chains, optimizing costs and capabilities. However, it has introduced complexities like cultural differences, regulatory variations, and supply chain vulnerabilities. Companies now need to consider ethical responsibilities across borders and adapt products for different markets. Overall, globalization has made business more interconnected and dynamic."}
                ]
            }
        ]
    
    def generate_chinese_accent_samples(self) -> List[Dict]:
        """生成中国口音英文样本"""
        return [
            {
                "text": "I work in fi-nan-cial sector. My company is loca-ted in Shang-hai.",
                "description": "典型音节分离发音（将英文单词按中文音节发音）"
            },
            {
                "text": "I like to eat rice and vegetable. It is very healthy food.",
                "description": "冠词和复数形式简化（中式英语特征）"
            },
            {
                "text": "Yesterday I go to meeting with my boss. We discuss about new project.",
                "description": "时态错误（go代替went）和介词冗余（discuss about）"
            },
            {
                "text": "The weather in my hometown is very good. People is very friendly.",
                "description": "主谓不一致（people is）和简单词汇重复"
            },
            {
                "text": "I think technology is important for develop economy in our country.",
                "description": "动词名词化（develop代替development）的中式表达"
            }
        ]
    
    def generate_beginner_samples(self, count: int = 20) -> List[Dict]:
        """生成Beginner级别（A2-B1）样本"""
        beginner_samples = []
        
        # Part 1 简单问题
        part1_topics = self.generate_part1_topics()
        for topic in part1_topics:
            for qa in topic["questions"]:
                beginner_samples.append({
                    "text": qa["answer"],
                    "level": "beginner",
                    "category": "part1",
                    "subcategory": topic["category"],
                    "reference_question": qa["question"]
                })
        
        # 简单句子补充
        simple_sentences = [
            "I go to work every day.",
            "My family lives in Beijing.",
            "I can speak English and Chinese.",
            "The weather is sunny today.",
            "I like to watch movies on weekends.",
            "My favorite food is noodles.",
            "I have two brothers and one sister.",
            "In the morning, I drink coffee.",
            "My job is interesting and challenging.",
            "I want to travel to Europe next year."
        ]
        
        for sentence in simple_sentences:
            beginner_samples.append({
                "text": sentence,
                "level": "beginner",
                "category": "simple_sentences",
                "subcategory": "basic_structures"
            })
        
        return beginner_samples[:count]
    
    def generate_intermediate_samples(self, count: int = 30) -> List[Dict]:
        """生成Intermediate级别（B2）样本"""
        intermediate_samples = []
        
        # Part 2 长独白
        part2_topics = self.generate_part2_topics()
        for topic in part2_topics:
            intermediate_samples.append({
                "text": topic["sample_answer"],
                "level": "intermediate",
                "category": "part2",
                "subcategory": "long_turn",
                "topic": topic["topic"]
            })
        
        # Part 3 讨论问题
        part3_topics = self.generate_part3_topics()
        for topic in part3_topics[:2]:  # 只取前两个类别
            for qa in topic["questions"]:
                intermediate_samples.append({
                    "text": qa["answer"],
                    "level": "intermediate",
                    "category": "part3",
                    "subcategory": topic["category"],
                    "reference_question": qa["question"]
                })
        
        # 复杂句子补充
        complex_sentences = [
            "Although the project was challenging, our team managed to complete it on time.",
            "In my opinion, education should focus more on practical skills than theoretical knowledge.",
            "The company's decision to expand internationally was based on thorough market research.",
            "While technology offers many benefits, it also creates new challenges for privacy.",
            "Effective communication requires not only speaking clearly but also listening actively."
        ]
        
        for sentence in complex_sentences:
            intermediate_samples.append({
                "text": sentence,
                "level": "intermediate",
                "category": "complex_sentences",
                "subcategory": "advanced_structures"
            })
        
        return intermediate_samples[:count]
    
    def generate_advanced_samples(self, count: int = 40) -> List[Dict]:
        """生成Advanced级别（C1-C2）样本"""
        advanced_samples = []
        
        # 完整的Part 3 抽象讨论
        part3_topics = self.generate_part3_topics()
        for topic in part3_topics:
            for qa in topic["questions"]:
                advanced_samples.append({
                    "text": qa["answer"],
                    "level": "advanced",
                    "category": "part3",
                    "subcategory": topic["category"],
                    "reference_question": qa["question"]
                })
        
        # 学术和抽象话题
        academic_topics = [
            {
                "text": "The correlation between economic development and environmental sustainability presents a complex dichotomy that necessitates innovative policy frameworks.",
                "description": "学术抽象表达"
            },
            {
                "text": "Technological disruption has catalyzed paradigm shifts across industries, rendering traditional business models obsolete while simultaneously creating unprecedented opportunities.",
                "description": "复杂商业概念"
            },
            {
                "text": "Cognitive biases in decision-making processes, though often imperceptible, significantly influence organizational outcomes and strategic direction.",
                "description": "心理学专业术语"
            }
        ]
        
        for topic in academic_topics:
            advanced_samples.append({
                "text": topic["text"],
                "level": "advanced",
                "category": "academic",
                "subcategory": "abstract_concepts",
                "description": topic["description"]
            })
        
        # 投资路演内容（Daryl重点关注）
        investor_pitch_content = [
            "Our platform leverages machine learning algorithms to optimize financial workflows, reducing operational costs by approximately thirty percent while improving accuracy metrics.",
            "Market analysis indicates a total addressable market of three billion dollars, with a compound annual growth rate of fifteen percent over the next five years.",
            "We have secured strategic partnerships with three pilot customers, achieving a ninety-two percent customer satisfaction rate and validating our value proposition.",
            "The investment will accelerate our product development roadmap, expand our market reach across Southeast Asia, and strengthen our competitive positioning."
        ]
        
        for i, content in enumerate(investor_pitch_content):
            advanced_samples.append({
                "text": content,
                "level": "advanced",
                "category": "business",
                "subcategory": "investor_pitch",
                "segment": f"segment_{i+1}"
            })
        
        return advanced_samples[:count]
    
    def generate_chinese_accent_audio(self, count: int = 10) -> List[Dict]:
        """生成中国口音样本"""
        chinese_samples = self.generate_chinese_accent_samples()
        return [
            {
                "text": sample["text"],
                "level": "chinese_accent",
                "category": "accent_samples",
                "description": sample["description"]
            }
            for sample in chinese_samples[:count]
        ]
    
    def synthesize_speech(self, text: str, slow_down: float = 1.0) -> Optional[bytes]:
        """使用Google TTS合成语音"""
        try:
            # 调整场景参数来模拟语速变化
            scenario = "default"
            if slow_down < 0.9:
                scenario = "financial_report"  # 金融报告场景更慢
            elif slow_down > 1.0:
                scenario = "daily_conversation"  # 日常对话更快
            
            # 调用TTS合成 - 使用正确的参数
            # 注意：synthesize_speech方法返回的是(success, result)元组
            success, result = self.tts_client.synthesize_speech(
                text=text,
                voice_type="default",
                scenario=scenario
            )
            
            if success:
                # result是文件路径，读取音频数据
                with open(result, 'rb') as f:
                    audio_data = f.read()
                return audio_data
            else:
                print(f"❌ TTS合成失败: {result}")
                return None
                
        except Exception as e:
            print(f"❌ TTS合成失败: {e}")
            return None
    
    def save_audio_file(self, audio_data: bytes, filename: str) -> bool:
        """保存音频文件并清理临时文件"""
        try:
            filepath = os.path.join(self.base_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            # 设置合理的权限
            os.chmod(filepath, 0o644)
            
            # 验证文件大小
            if os.path.getsize(filepath) < 100:
                print(f"   ⚠️ 文件太小，可能有问题: {filepath} ({os.path.getsize(filepath)} bytes)")
            
            return True
        except Exception as e:
            print(f"❌ 保存音频文件失败: {e}")
            return False
    
    def generate_all_samples(self):
        """生成所有测试样本"""
        print("🎤 开始生成IELTS测试音频数据集...")
        print("="*60)
        
        # 生成各级别样本
        beginner_samples = self.generate_beginner_samples(20)
        intermediate_samples = self.generate_intermediate_samples(30)
        advanced_samples = self.generate_advanced_samples(40)
        chinese_samples = self.generate_chinese_accent_audio(10)
        
        all_samples = beginner_samples + intermediate_samples + advanced_samples + chinese_samples
        
        # 记录生成进度
        success_count = 0
        fail_count = 0
        
        for i, sample in enumerate(all_samples):
            level = sample["level"]
            category = sample["category"]
            
            # 确定保存路径
            if level == "beginner":
                rel_path = f"beginner/sample_{i+1:03d}.mp3"
                slow_down = 0.8  # 初学者语速更慢
            elif level == "intermediate":
                rel_path = f"intermediate/sample_{i+1:03d}.mp3"
                slow_down = 0.9  # 中级稍慢
            elif level == "advanced":
                rel_path = f"advanced/sample_{i+1:03d}.mp3"
                slow_down = 1.0  # 高级正常语速
            else:  # chinese_accent
                rel_path = f"chinese_accent/sample_{i+1:03d}.mp3"
                slow_down = 0.85  # 口音样本中等语速
            
            # 生成语音
            print(f"[{i+1}/{len(all_samples)}] 生成 {level}/{category}: {sample['text'][:50]}...")
            audio_data = self.synthesize_speech(sample["text"], slow_down)
            
            if audio_data:
                # 保存音频文件
                if self.save_audio_file(audio_data, rel_path):
                    # 更新元数据
                    sample_info = sample.copy()
                    sample_info["audio_file"] = rel_path
                    sample_info["generated_at"] = datetime.now().isoformat()
                    sample_info["audio_length"] = len(audio_data)
                    
                    self.metadata["samples"].append(sample_info)
                    self.metadata["levels"][level]["count"] += 1
                    self.metadata["total_samples"] += 1
                    
                    success_count += 1
                    print(f"   ✅ 已保存: {rel_path}")
                else:
                    fail_count += 1
                    print(f"   ❌ 保存失败")
            else:
                fail_count += 1
                print(f"   ❌ 语音合成失败")
            
            # 避免API限制，添加延迟
            if (i + 1) % 10 == 0:
                print(f"   ⏸️ 暂停2秒避免API限制...")
                time.sleep(2)
        
        # 保存元数据
        metadata_path = os.path.join(self.base_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        
        # 生成统计报告
        print("\n" + "="*60)
        print("🎯 IELTS测试音频数据集生成完成")
        print("="*60)
        print(f"✅ 成功生成: {success_count} 个音频样本")
        print(f"❌ 失败: {fail_count} 个")
        print(f"📁 保存位置: {self.base_dir}/")
        print(f"📊 级别分布:")
        for level, info in self.metadata["levels"].items():
            print(f"   - {level}: {info['count']} 个样本 ({info['ielts_band']})")
        print(f"📋 元数据: {metadata_path}")
        print("="*60)
        
        return success_count, fail_count

def main():
    """主函数"""
    generator = IELTSAudioGenerator()
    
    # 检查TTS配置
    print("🔧 检查TTS配置...")
    if not generator.tts_client.api_key:
        print("❌ 未找到Google TTS API密钥")
        print("请确保 ~/.openclaw/auth/google/ielts_tts_2026.key 文件存在")
        return
    
    print(f"✅ TTS配置正常，密钥长度: {len(generator.tts_client.api_key)}")
    
    # 生成所有样本
    success, fail = generator.generate_all_samples()
    
    if success > 0:
        print(f"\n🎉 数据集生成完成！总计 {success} 个IELTS音频样本")
        print("可用于STT准确性测试和Whisper.js模型评估")
    else:
        print("\n❌ 数据集生成失败，请检查TTS配置")

if __name__ == "__main__":
    main()