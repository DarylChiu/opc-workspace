#!/usr/bin/env python3
"""
测试OpenClaw是否正确配置Deepseek直接provider
"""
import json
import os
import sys

def check_openclaw_config():
    print("🔍 检查OpenClaw配置中的Deepseek provider设置")
    
    try:
        with open("/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/openclaw.json", "r") as f:
            config = json.load(f)
        
        print("1. ✅ OpenClaw配置文件可访问")
        
        # 检查auth配置
        auth_profiles = config.get("auth", {}).get("profiles", {})
        print(f"2. Auth Profiles: {list(auth_profiles.keys())}")
        
        deepseek_profile = auth_profiles.get("deepseek_bryson")
        if deepseek_profile:
            print(f"   🎯 Deepseek profile存在: {deepseek_profile.get('type')} - {deepseek_profile.get('provider')}")
            print(f"   🔑 API Key: {deepseek_profile.get('apiKey', '')[0:20]}...")
        else:
            print("   ❌ Deepseek profile未找到")
        
        # 检查默认模型配置
        defaults = config.get("agents", {}).get("defaults", {})
        primary_model = defaults.get("model", {}).get("primary")
        print(f"3. 默认主模型: {primary_model}")
        
        # 检查模型配置
        models_config = defaults.get("models", {})
        print(f"4. 模型配置数量: {len(models_config)}")
        
        for model_name, model_config in models_config.items():
            provider = model_config.get("provider", "unknown")
            api_key = model_config.get("apiKey", "none")
            print(f"   - {model_name}: provider={provider}, apiKey={api_key[0:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查配置失败: {e}")
        return False

def check_actual_session():
    print("\n🔧 检查当前会话的实际provider")
    
    # 检查环境变量
    print("环境变量检查:")
    env_vars = ["OPENROUTER_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY"]
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"  {var}: {value[0:20]}...")
        else:
            print(f"  {var}: 未设置")
    
    # 检查OpenClaw当前状态
    print("\n当前会话状态:")
    print("从/status命令中我们看到:")
    print("  - Model: anthropic/deepseek-chat")
    print("  - Provider: unknown")
    print("  - Fallback: openrouter/deepseek/deepseek-r1")
    print("  - Key状态: api-key (model not found)")
    
    return True

def main():
    print("=" * 60)
    print("🤖 OpenClaw Deepseek Provider配置分析")
    print("=" * 60)
    
    config_ok = check_openclaw_config()
    check_actual_session()
    
    print("\n" + "=" * 60)
    print("📊 问题诊断结果")
    print("=" * 60)
    
    print("🔴 关键问题识别:")
    print("1. 配置文件中的Deepseek profile存在，但可能未被正确引用")
    print("2. 当前会话实际使用的是OpenRouter作为fallback provider")
    print("3. 模型名'anthropic/deepseek-chat'格式混淆了provider识别")
    print("4. Deepseek key虽然有效，但OpenClaw可能没有使用Deepseek直接provider")
    
    print("\n💡 解决方案:")
    print("1. 调整模型命名格式: 'deepseek/deepseek-chat'而不是'anthropic/deepseek-chat'")
    print("2. 明确指定provider为'deepseek'而不是依赖自动检测")
    print("3. 创建专属的Deepseek provider配置而不是复用OpenRouter配置")
    print("4. 重启Gateway以确保配置生效")
    
    print("\n🔧 下一步行动:")
    print("1. 修复openclaw.json中的模型配置")
    print("2. 创建明确的Deepseek provider配置")
    print("3. 重启OpenClaw Gateway")
    print("4. 验证provider切换成功")
    
    return config_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
