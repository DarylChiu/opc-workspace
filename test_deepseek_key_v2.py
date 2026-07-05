#!/usr/bin/env python3
"""
Deepseek API Key 测试脚本 - 简化版
测试提供的Deepseek官方API Key是否可用
"""

import os
import sys
import requests
import json
from datetime import datetime

def test_deepseek_key(api_key: str):
    """测试Deepseek API Key是否可用"""
    
    print(f"🔑 测试API Key: {api_key[:20]}...")
    
    # 主要测试：OpenRouter认证端点
    print("\n🧪 测试1: OpenRouter API认证状态")
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers=headers,
            timeout=10
        )
        
        status_code = response.status_code
        print(f"   状态码: {status_code}")
        
        if status_code == 200:
            try:
                data = response.json()
                if "data" in data:
                    usage_data = data["data"]
                    print(f"   ✅ 认证成功!")
                    print(f"      每日用量: ${usage_data.get('usage_daily', 0):.4f}")
                    print(f"      每周用量: ${usage_data.get('usage_weekly', 0):.4f}")
                    print(f"      剩余额度: ${usage_data.get('limit_remaining', 0):.2f}")
                    return True, usage_data
                else:
                    print(f"   ❌ 响应格式异常: {data}")
                    return False, {"error": "Invalid response format"}
            except json.JSONDecodeError:
                print(f"   ❌ JSON解析失败: {response.text[:200]}")
                return False, {"error": "JSON decode error"}
        elif status_code == 401:
            print(f"   ❌ API Key无效 (401 Unauthorized)")
            return False, {"error": "Invalid API Key"}
        elif status_code == 429:
            print(f"   ⚠️  请求过于频繁 (429 Rate Limited)")
            return False, {"error": "Rate limited"}
        else:
            print(f"   ❌ HTTP错误 {status_code}")
            return False, {"error": f"HTTP {status_code}"}
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ 网络错误: {e}")
        return False, {"error": str(e)}

def create_key_file(api_key: str, target_dir: str):
    """创建Key文件"""
    os.makedirs(target_dir, exist_ok=True)
    
    # 创建独立的Key文件
    key_file = os.path.join(target_dir, "bryson_openrouter.key")
    with open(key_file, "w") as f:
        f.write(api_key)
    
    print(f"✅ Key文件已创建: {key_file}")
    
    # 创建环境变量配置文件
    env_file = os.path.join(target_dir, "bryson_env.sh")
    with open(env_file, "w") as f:
        f.write(f"""#!/bin/bash
# Bryson独立API Key配置
export BRYSON_OPENROUTER_KEY="{api_key}"
export BRYSON_DEEPSEEK_KEY="{api_key}"

echo "Bryson独立API Key已加载: {api_key[:20]}..."

# 可选：如果你想立即切换到Bryson Key，取消注释下一行
# export OPENROUTER_API_KEY="{api_key}"
""")
    
    os.chmod(env_file, 0o755)
    print(f"✅ 环境配置脚本: {env_file}")
    print(f"   使用方法: source {env_file}")
    
    return key_file, env_file

def check_current_key():
    """检查当前环境中的OpenRouter Key"""
    current_key = os.environ.get("OPENROUTER_API_KEY", "")
    if current_key:
        print(f"\n🔍 当前环境中的OpenRouter Key: {current_key[:20]}...")
        success, data = test_deepseek_key(current_key)
        return success, data
    else:
        print("⚠️  未找到OPENROUTER_API_KEY环境变量")
        return False, {"error": "No current key found"}

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python test_deepseek_key.py YOUR_DEEPSEEK_API_KEY")
        print("\n或者测试当前Key: python test_deepseek_key.py --current")
        
        # 显示当前Key信息
        check_current_key()
        return
    
    api_key = sys.argv[1]
    
    print("🧪 Bryson独立API Key测试")
    print("=" * 60)
    
    if api_key == "--current":
        success, data = check_current_key()
        return
    
    # 测试提供的Deepseek Key
    success, data = test_deepseek_key(api_key)
    
    # 保存测试结果
    test_result = {
        "timestamp": datetime.now().isoformat(),
        "key_type": "deepseek_provided",
        "key_preview": f"{api_key[:10]}...{api_key[-10:]}",
        "success": success,
        "test_data": data
    }
    
    result_file = "deepseek_key_test_result.json"
    with open(result_file, "w") as f:
        json.dump(test_result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 测试结果已保存: {result_file}")
    
    if success:
        print("\n🎯 Deepseek Key测试通过！可以作为Bryson独立Key使用")
        
        # 创建Key文件
        target_dir = os.path.expanduser("~/.openclaw")
        key_file, env_file = create_key_file(api_key, target_dir)
        
        print("\n📋 配置完成:")
        print(f"   1. Bryson独立Key文件: {key_file}")
        print(f"   2. 环境变量脚本: {env_file}")
        print(f"   3. 要切换到Bryson模式，运行: source {env_file}")
        
    else:
        print("\n❌ Deepseek Key测试失败")
        print("   🔄 将使用现有OpenRouter Key作为fallback")
        
        # 检查当前Key作为fallback
        print("\n🔍 检查当前OpenRouter Key作为fallback...")
        current_success, current_data = check_current_key()
        
        if current_success:
            print("   ✅ 当前OpenRouter Key可用，作为fallback")

if __name__ == "__main__":
    main()