#!/usr/bin/env python3
"""
将现有音频文件转换为Base64编码
"""

import os
import base64
import json

def file_to_base64(file_path):
    """将文件转换为Base64字符串"""
    try:
        with open(file_path, 'rb') as f:
            audio_bytes = f.read()
            return base64.b64encode(audio_bytes).decode('utf-8')
    except Exception as e:
        return None, f"Base64编码失败: {e}"

def main():
    print("📤 音频文件转Base64")
    print("=" * 60)
    
    # 测试音频文件路径
    audio_files = {
        "英语测试": "/var/folders/c2/nd4_btzd07d0kn33582947z00000gn/T/bryson_tts_893.mp3",
        "中文测试": "/var/folders/c2/nd4_btzd07d0kn33582947z00000gn/T/bryson_tts_7634.mp3"
    }
    
    results = []
    
    for name, file_path in audio_files.items():
        print(f"\n📂 {name}")
        print(f"  文件: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"  ❌ 文件不存在: {file_path}")
            continue
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        print(f"  📏 大小: {file_size:,}字节 ({file_size/1024:.1f}KB)")
        
        # 转换为Base64
        print("  🔄 正在转换为Base64...")
        base64_str = file_to_base64(file_path)
        
        if base64_str:
            # 只显示部分预览
            preview = base64_str[:80] + "..." if len(base64_str) > 80 else base64_str
            print(f"  ✅ 转换成功!")
            print(f"  📊 Base64长度: {len(base64_str):,}字符")
            print(f"  👀 预览: {preview}")
            
            results.append({
                "name": name,
                "file_path": file_path,
                "file_size": file_size,
                "base64_length": len(base64_str),
                "base64_preview": preview,
                "base64_full": base64_str
            })
        else:
            print(f"  ❌ 转换失败")
    
    # 输出结果
    print(f"\n{'='*60}")
    print("📋 输出结果")
    print(f"{'='*60}")
    
    for result in results:
        print(f"\n🎵 {result['name']}")
        print(f"   文件: {result['file_path']}")
        print(f"   大小: {result['file_size']:,}字节")
        print(f"   Base64长度: {result['base64_length']:,}字符")
        print(f"   预览: {result['base64_preview']}")
        
        # 保存到文件
        output_file = f"{result['name']}_audio.base64.txt"
        with open(output_file, 'w') as f:
            f.write(result['base64_full'])
        print(f"   💾 完整Base64已保存到: {output_file}")
    
    # 解码说明
    print(f"\n{'='*60}")
    print("🔧 使用说明")
    print(f"{'='*60}")
    
    print("\n📱 在飞书中直接发送Base64:")
    print("1. 将上面的Base64字符串直接粘贴到聊天中")
    print("2. 或者将保存的.txt文件发给你")
    
    print("\n💻 解码为MP3文件:")
    for result in results:
        print(f"\n🎵 {result['name']}:")
        file_name = f"{result['name'].replace('测试', '').lower()}_audio.mp3"
        print(f"   echo '{result['base64_full'][:50]}...' | base64 -d > {file_name}")
        print(f"   或者用Python:")
        print(f"""   import base64
   audio_data = base64.b64decode(\"{result['base64_full'][:50]}...\")
   with open('{file_name}', 'wb') as f:
       f.write(audio_data)""")
    
    print(f"\n⚠️ 注意: Base64字符串很长，飞书可能有消息长度限制")
    print(f"💡 建议: 我直接在聊天中发送Base64字符串，你按行复制解码")

if __name__ == "__main__":
    main()