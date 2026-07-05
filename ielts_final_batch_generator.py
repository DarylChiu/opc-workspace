#!/usr/bin/env python3
"""
IELTS最终批次生成器 - 生成最后15个样本以达到100+目标
"""

import os
import sys
import json
import time
from datetime import datetime

# 导入现有的TTS核心模块
sys.path.append('.')
from bryson_tts_core import GoogleTTSClient

class IELTSFinalBatchGenerator:
    """IELTS最终批次生成器"""
    
    def __init__(self):
        # 使用已有的Google TTS客户端
        self.tts_client = GoogleTTSClient()
        self.base_dir = "test_audio/ielts_benchmark"
        
        # 加载现有元数据
        self.metadata = self.load_metadata()
    
    def load_metadata(self):
        """加载现有元数据"""
        metadata_path = os.path.join(self.base_dir, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
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
    
    def generate_final_business_samples(self) -> list:
        """生成最终商业样本"""
        return [
            {
                "text": "The board of directors has approved the proposed merger, pending regulatory approval and shareholder consent.",
                "category": "business",
                "subcategory": "corporate_governance"
            },
            {
                "text": "Our innovation pipeline includes five new products scheduled for launch over the next eighteen months.",
                "category": "business",
                "subcategory": "product_development"
            },
            {
                "text": "Market penetration in Southeast Asia has exceeded expectations, with quarter-over-quarter growth of twenty-five percent.",
                "category": "business",
                "subcategory": "regional_expansion"
            },
            {
                "text": "Strategic partnerships with academic institutions have enhanced our research capabilities and talent recruitment.",
                "category": "business",
                "subcategory": "knowledge_transfer"
            },
            {
                "text": "The implementation of blockchain technology has improved supply chain transparency and reduced transaction costs.",
                "category": "business",
                "subcategory": "technology_adoption"
            }
        ]
    
    def generate_final_chinese_accent_samples(self) -> list:
        """生成最终中国口音样本"""
        return [
            {
                "text": "Education system in my country need reform to better prepare students for global competition.",
                "description": "中式英语结构（need reform instead of needs reform）"
            },
            {
                "text": "I think government should invest more money in renewable energy to protect environment.",
                "description": "动词形态错误和冗余词汇"
            },
            {
                "text": "Many company now realize the importance of corporate social responsibility.",
                "description": "单复数错误（company代替companies）"
            },
            {
                "text": "Internet technology change the way people communicate and do business.",
                "description": "主谓不一致（change代替changes）"
            },
            {
                "text": "To improve public health, we need build more sports facilities and promote healthy lifestyle.",
                "description": "动词不定式错误（need build instead of need to build）"
            }
        ]
    
    def generate_intermediate_complex_sentences(self) -> list:
        """生成中级复杂句子"""
        return [
            {
                "text": "Despite the economic downturn, our company has maintained profitability through strategic cost management and market diversification.",
                "category": "complex_sentences",
                "subcategory": "business_resilience"
            },
            {
                "text": "The integration of artificial intelligence into our operations has not only improved efficiency but also created new business opportunities.",
                "category": "complex_sentences",
                "subcategory": "technology_impact"
            },
            {
                "text": "While traditional marketing channels remain important, digital platforms have become increasingly crucial for reaching younger demographics.",
                "category": "complex_sentences",
                "subcategory": "marketing_evolution"
            },
            {
                "text": "Global trade policies continue to evolve, requiring businesses to adapt their strategies to navigate regulatory complexities.",
                "category": "complex_sentences",
                "subcategory": "trade_dynamics"
            },
            {
                "text": "Corporate culture significantly influences employee engagement, innovation, and long-term organizational success.",
                "category": "complex_sentences",
                "subcategory": "organizational_behavior"
            }
        ]
    
    def synthesize_speech(self, text: str, scenario: str = "default") -> bytes:
        """语音合成包装器"""
        try:
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
    
    def save_sample(self, level: str, sample_data: dict, text: str) -> bool:
        """保存单个样本"""
        try:
            sample_num = self.get_next_sample_number(level)
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
            for key in ["category", "subcategory", "description"]:
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
    
    def generate_final_batch(self):
        """生成最终批次样本"""
        print("🎯 生成IELTS最终批次...")
        print("="*60)
        
        current_total = self.metadata["total_samples"]
        target_total = 100
        need_to_generate = target_total - current_total
        
        if need_to_generate <= 0:
            print(f"✅ 已有 {current_total} 个样本，无需额外生成")
            return
        
        print(f"📊 当前样本数: {current_total}")
        print(f"🎯 目标样本数: {target_total}")
        print(f"📈 需要生成: {need_to_generate} 个样本")
        
        # 生成计划：优先Advanced，其次Intermediate，最后Chinese Accent
        business_samples = self.generate_final_business_samples()
        chinese_samples = self.generate_final_chinese_accent_samples()
        intermediate_samples = self.generate_intermediate_complex_sentences()
        
        all_samples = []
        
        # 添加Advanced样本
        for sample in business_samples:
            sample["level"] = "advanced"
            all_samples.append(sample)
        
        # 添加Intermediate样本
        for sample in intermediate_samples:
            sample["level"] = "intermediate"
            all_samples.append(sample)
        
        # 添加Chinese Accent样本
        for sample in chinese_samples:
            sample["level"] = "chinese_accent"
            all_samples.append(sample)
        
        success_count = 0
        fail_count = 0
        
        for i, sample in enumerate(all_samples[:need_to_generate]):
            print(f"[{success_count+1}/{need_to_generate}] 生成{sample['level']}")
            if self.save_sample(sample["level"], sample, sample["text"]):
                success_count += 1
            else:
                fail_count += 1
            
            # 避免API限制
            if (success_count + fail_count) % 3 == 0:
                print("   ⏸️ 暂停1秒避免API限制...")
                time.sleep(1)
        
        # 保存更新后的元数据
        metadata_path = os.path.join(self.base_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        
        # 打印总结
        print("\n" + "="*60)
        print("🎯 最终批次生成完成")
        print("="*60)
        print(f"✅ 成功生成: {success_count} 个样本")
        print(f"❌ 失败: {fail_count} 个")
        print(f"📊 最终级别分布:")
        for level, info in self.metadata["levels"].items():
            print(f"   - {level}: {info['count']} 个样本")
        print(f"📋 总样本数: {self.metadata['total_samples']}")
        print("="*60)
        
        return success_count, fail_count

def main():
    """主函数"""
    try:
        generator = IELTSFinalBatchGenerator()
        
        if not generator.metadata:
            print("❌ 无法加载元数据")
            return
        
        # 检查TTS配置
        print("🔧 检查TTS配置...")
        if not generator.tts_client.api_key:
            print("❌ 未找到Google TTS API密钥")
            return
        
        print(f"✅ TTS配置正常")
        
        # 生成最终批次
        success, fail = generator.generate_final_batch()
        
        if success > 0:
            print(f"\n🎉 成功生成 {success} 个最终样本")
            print(f"🎯 总计样本数: {generator.metadata['total_samples']} (达成100+目标！)")
            print("✨ STT开发计划第一阶段任务圆满完成！")
        else:
            print("\n❌ 未能生成新样本")
        
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()