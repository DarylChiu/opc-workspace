#!/usr/bin/env python3
"""
修复IELTS音频数据集的元数据文件
重新扫描已生成的音频文件并更新metadata.json
"""

import os
import json
import glob
from datetime import datetime

def scan_audio_files(base_dir: str):
    """扫描所有音频文件，重建元数据"""
    
    # 从原始生成器导入样本生成函数来重建文本
    import sys
    sys.path.append('.')
    
    # 动态导入样本生成器
    import ielts_audio_generator
    generator = ielts_audio_generator.IELTSAudioGenerator()
    
    # 获取样本列表
    beginner_samples = generator.generate_beginner_samples(20)
    intermediate_samples = generator.generate_intermediate_samples(30)
    advanced_samples = generator.generate_advanced_samples(40)
    chinese_samples = generator.generate_chinese_accent_audio(10)
    
    # 合并所有样本
    all_original_samples = beginner_samples + intermediate_samples + advanced_samples + chinese_samples
    print(f"原始样本数量: {len(all_original_samples)}")
    
    # 重建元数据
    metadata = {
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
    
    # 扫描beginner目录
    print("扫描beginner目录...")
    beginner_files = sorted(glob.glob(os.path.join(base_dir, "beginner", "*.mp3")))
    for i, file_path in enumerate(beginner_files):
        if i < len(beginner_samples):
            sample = beginner_samples[i]
            sample["audio_file"] = os.path.relpath(file_path, base_dir)
            sample["generated_at"] = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            sample["audio_length"] = os.path.getsize(file_path)
            
            metadata["samples"].append(sample)
            metadata["levels"]["beginner"]["count"] += 1
            metadata["total_samples"] += 1
    
    # 扫描intermediate目录
    print("扫描intermediate目录...")
    intermediate_files = sorted(glob.glob(os.path.join(base_dir, "intermediate", "*.mp3")))
    for i, file_path in enumerate(intermediate_files):
        if i < len(intermediate_samples):
            sample = intermediate_samples[i]
            sample["audio_file"] = os.path.relpath(file_path, base_dir)
            sample["generated_at"] = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            sample["audio_length"] = os.path.getsize(file_path)
            
            metadata["samples"].append(sample)
            metadata["levels"]["intermediate"]["count"] += 1
            metadata["total_samples"] += 1
    
    # 扫描advanced目录
    print("扫描advanced目录...")
    advanced_files = sorted(glob.glob(os.path.join(base_dir, "advanced", "*.mp3")))
    for i, file_path in enumerate(advanced_files):
        if i < len(advanced_samples):
            sample = advanced_samples[i]
            sample["audio_file"] = os.path.relpath(file_path, base_dir)
            sample["generated_at"] = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            sample["audio_length"] = os.path.getsize(file_path)
            
            metadata["samples"].append(sample)
            metadata["levels"]["advanced"]["count"] += 1
            metadata["total_samples"] += 1
    
    # 扫描chinese_accent目录
    print("扫描chinese_accent目录...")
    chinese_files = sorted(glob.glob(os.path.join(base_dir, "chinese_accent", "*.mp3")))
    for i, file_path in enumerate(chinese_files):
        if i < len(chinese_samples):
            sample = chinese_samples[i]
            sample["audio_file"] = os.path.relpath(file_path, base_dir)
            sample["generated_at"] = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            sample["audio_length"] = os.path.getsize(file_path)
            
            metadata["samples"].append(sample)
            metadata["levels"]["chinese_accent"]["count"] += 1
            metadata["total_samples"] += 1
    
    # 保存元数据
    metadata_path = os.path.join(base_dir, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return metadata

def main():
    """主函数"""
    base_dir = "test_audio/ielts_benchmark"
    
    if not os.path.exists(base_dir):
        print(f"❌ 目录不存在: {base_dir}")
        return
    
    print("🔧 修复IELTS音频数据集元数据...")
    print(f"📂 基础目录: {base_dir}")
    
    # 统计文件总数
    mp3_count = len(glob.glob(os.path.join(base_dir, "**", "*.mp3"), recursive=True))
    print(f"📊 发现的音频文件数量: {mp3_count}")
    
    # 扫描并更新元数据
    metadata = scan_audio_files(base_dir)
    
    print("\n" + "="*60)
    print("✅ 元数据修复完成")
    print("="*60)
    print(f"📊 更新后的统计:")
    print(f"总样本数: {metadata['total_samples']}")
    for level, info in metadata["levels"].items():
        print(f"  - {level}: {info['count']} 个样本")
    print(f"📋 元数据文件: {os.path.join(base_dir, 'metadata.json')}")
    print("="*60)

if __name__ == "__main__":
    main()