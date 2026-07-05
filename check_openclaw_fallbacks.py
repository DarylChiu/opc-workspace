#!/usr/bin/env python3
"""
检查OpenClaw的fallback模型配置
"""
import json
import os
from pathlib import Path

def main():
    print("🔍 检查OpenClaw fallback配置")
    print("="*60)
    
    config_file = Path("openclaw.json")
    if not config_file.exists():
        print(f"❌ 配置文件不存在: {config_file}")
        return
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("📋 当前Agent配置:")
    print("-"*60)
    
    if "agents" in config and "defaults" in config["agents"]:
        defaults = config["agents"]["defaults"]
        
        if "model" in defaults:
            model_config = defaults["model"]
            print(f"📌 主模型: {model_config.get('primary', '未设置')}")
            
            fallbacks = model_config.get("fallbacks", [])
            print(f"🔁 Fallback模型: {fallbacks}")
            print(f"   当前配置了 {len(fallbacks)} 个fallback模型")
            
            if not fallbacks:
                print("⚠️  警告: 没有配置fallback模型")
            else:
                for i, fb in enumerate(fallbacks, 1):
                    print(f"   {i}. {fb}")
        
        # 检查model详细配置
        if "models" in defaults:
            models = defaults["models"]
            print(f"\n📊 模型详情 (共{len(models)}个):")
            for model_name, model_config in models.items():
                provider = model_config.get("provider", "unknown")
                api_key_prefix = "sk-" + model_config.get("apiKey", "")[:8] + "..." if model_config.get("apiKey") else "未设置"
                print(f"   🔹 {model_name}")
                print(f"      提供商: {provider}")
                print(f"      密钥: {api_key_prefix}")
    
    # 检查认证配置
    print("\n🔐 认证配置:")
    print("-"*60)
    if "auth" in config and "profiles" in config["auth"]:
        profiles = config["auth"]["profiles"]
        for profile_name, profile_config in profiles.items():
            provider = profile_config.get("provider", "unknown")
            print(f"   📝 {profile_name}: {provider}")
    
    print("\n🎯 我的Agent配置:")
    print("-"*60)
    if "agents" in config and "list" in config["agents"]:
        for agent in config["agents"]["list"]:
            if agent.get("id") == "xiaofeng":
                print(f"   ID: {agent.get('id')}")
                print(f"   名称: {agent.get('name')}")
                print(f"   模型: {agent.get('model', '使用默认')}")
                if "identity" in agent:
                    print(f"   身份: {agent['identity'].get('name')} {agent['identity'].get('emoji')}")
    
    print("\n⚠️  问题诊断:")
    print("-"*60)
    print("session_status显示:")
    print("   主模型: deepseek/deepseek-r1 · 🔑 unknown")
    print("   Fallback: openrouter/deepseek/deepseek-r1 · 🔑 api-key (model not found)")
    print()
    print("这意味着:")
    print("1. deepseek/deepseek-r1 密钥状态为 unknown (可能配置问题)")
    print("2. fallback模型 openrouter/deepseek/deepseek-r1 找不到")
    
    print("\n💡 添加fallback到openrouter/anthropic/claude 3.7 sonnet的建议:")
    print("-"*60)
    print("需要在 openclaw.json 的 agents.defaults.model.fallbacks 中添加:")
    print('   "fallbacks": ["deepseek/deepseek-chat", "openrouter/anthropic/claude-3-5-sonnet-latest"]')
    print()
    print("并需要在 auth.profiles 中添加openrouter或anthropic的密钥配置:")
    print("""
  "auth": {
    "profiles": {
      "deepseek_bryson": { ... },
      "openrouter_anthropic": {
        "type": "apiKey",
        "provider": "openrouter",
        "apiKey": "sk-or-..."
      }
    }
  }
    """)
    
    print("\n📝 建议的配置更新:")
    print("-"*60)
    
    # 显示agent defaults的实际配置
    print("当前agents.defaults应该扩展为:")
    print(json.dumps({
        "model": {
            "primary": "deepseek/deepseek-r1",
            "fallbacks": ["deepseek/deepseek-chat", "openrouter/anthropic/claude-3-5-sonnet-20241022"]
        },
        "models": {
            "deepseek/deepseek-chat": {
                "provider": "deepseek",
                "apiKey": "REDACTED_API_KEY"
            },
            "deepseek/deepseek-r1": {
                "provider": "deepseek", 
                "apiKey": "REDACTED_API_KEY"
            },
            "openrouter/anthropic/claude-3-5-sonnet-20241022": {
                "provider": "openrouter",
                "apiKey": "需要添加OpenRouter密钥"
            }
        }
    }, indent=2, ensure_ascii=False))
    
    print("\n🎯 立即验证:")
    print("-"*60)
    print("1. 检查Deepseek密钥是否有效")
    print("2. 获取OpenRouter密钥 (如需claude fallback)")
    print("3. 更新openclaw.json配置")
    print("4. 重启gateway使配置生效")

if __name__ == "__main__":
    main()