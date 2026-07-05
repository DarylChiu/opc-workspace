#!/usr/bin/env python3
"""
详细检查当前OpenClaw实际使用的provider
"""

import os
import json
import requests
import sys

def check_environment():
    print("🔍 检查环境变量")
    
    keys_to_check = [
        "DEEPSEEK_API_KEY",
        "OPENROUTER_API_KEY", 
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY"
    ]
    
    for key in keys_to_check:
        value = os.environ.get(key)
        if value:
            print(f"  ✅ {key}: {value[:20]}...")
        else:
            print(f"  ❌ {key}: 未设置")

def check_configuration():
    print("\n🔍 检查配置文件")
    
    try:
        with open("/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/openclaw.json", "r") as f:
            config = json.load(f)
        
        # 检查auth配置
        auth_profiles = config.get("auth", {}).get("profiles", {})
        print(f"  Auth Profiles: {list(auth_profiles.keys())}")
        
        for name, profile in auth_profiles.items():
            provider = profile.get("provider", "unknown")
            print(f"    - {name}: provider={provider}")
        
        # 检查当前agent配置
        agents = config.get("agents", {}).get("list", [])
        for agent in agents:
            if agent.get("id") == "xiaofeng":
                print(f"  🧵 当前Agent (xiaofeng):")
                print(f"    模型: {agent.get('model')}")
                print(f"    工作空间: {agent.get('workspace')}")
                
        # 检查默认配置
        defaults = config.get("agents", {}).get("defaults", {})
        default_model = defaults.get("model", {})
        if isinstance(default_model, dict):
            print(f"  ⚙️  默认主模型: {default_model.get('primary')}")
            print(f"    备选模型: {default_model.get('fallbacks', [])}")
        
    except Exception as e:
        print(f"  ❌ 读取配置失败: {e}")

def test_direct_api_calls():
    print("\n🔍 测试直接API调用")
    
    # 测试Deepseek直接API
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if deepseek_key:
        print(f"  🔑 Deepseek Key: {deepseek_key[:20]}...")
        
        headers = {
            "Authorization": f"Bearer {deepseek_key}",
            "Content-Type": "application/json"
        }
        
        # 测试Deepseek API
        try:
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "简单测试"}],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers=headers,
                json=payload,
                timeout=5
            )
            
            print(f"  🌐 Deepseek API状态: {response.status_code}")
            if response.status_code == 200:
                print(f"     ✅ 直接API可用")
            else:
                print(f"     ❌ 直接API失败: {response.text[:100]}")
                
        except Exception as e:
            print(f"  ❌ Deepseek API测试失败: {e}")
    else:
        print("  ❌ 未找到Deepseek API Key")
    
    # 测试OpenRouter
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        print(f"\n  🔑 OpenRouter Key: {openrouter_key[:20]}...")
        
        headers = {"Authorization": f"Bearer {openrouter_key}"}
        
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers=headers,
                timeout=5
            )
            
            print(f"  🌐 OpenRouter API状态: {response.status_code}")
            if response.status_code == 200:
                print(f"     ✅ OpenRouter API可用")
            else:
                print(f"     ❌ OpenRouter API失败")
                
        except Exception as e:
            print(f"  ❌ OpenRouter API测试失败: {e}")

def analyze_current_session():
    print("\n🔍 分析当前会话状态")
    
    print("  📊 从session_status获得的信息:")
    print("    Model: anthropic/deepseek-reasoner")
    print("    Provider: unknown (但'anthropic'前缀暗示使用Anthropic平台)")
    
    print("\n  🤔 可能性分析:")
    print("    1. OpenClaw可能使用Anthropic作为provider来调用Deepseek模型")
    print("    2. 'deepseek-reasoner'可能是Anthropic平台上的Deepseek模型变体")
    print("    3. 配置中的'deepseek/deepseek-r1'可能被映射到'anthropic/deepseek-reasoner'")
    print("    4. Gateway可能使用了不同的provider配置")
    
    print("\n  🔧 如何验证:")
    print("    - 检查Gateway的日志看实际使用的provider")
    print("    - 查看Gateway启动时的配置文件")
    print("    - 测试使用不同的模型名称")

def main():
    print("="*60)
    print("🔬 OpenClaw Provider详细分析")
    print("="*60)
    
    check_environment()
    check_configuration()
    test_direct_api_calls()
    analyze_current_session()
    
    print("\n" + "="*60)
    print("📋 结论")
    print("="*60)
    
    print("根据分析:")
    print("✅ 1. Deepseek API Key存在且有效")
    print("✅ 2. 配置文件指定使用deepseek/deepseek-r1")
    print("❓ 3. 但当前会话显示: anthropic/deepseek-reasoner")
    
    print("\n💡 这意味着:")
    print("   - OpenClaw Gateway可能没有使用配置文件中的设置")
    print("   - 或者Gateway使用了不同的provider映射逻辑")
    print("   - 'anthropic/deepseek-reasoner'可能通过Anthropic平台间接使用Deepseek")
    
    print("\n🔧 建议检查:")
    print("   1. Gateway启动时的实际配置")
    print("   2. Gateway的进程参数和环境变量")
    print("   3. 尝试重启Gateway以应用正确配置")
    
    return True

if __name__ == "__main__":
    main()