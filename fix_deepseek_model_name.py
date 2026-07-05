#!/usr/bin/env python3
"""
修复OpenClaw配置中的Deepseek模型名
从错误的 `deepseek/deepseek-r1` 改为正确的模型名
"""

import json
from pathlib import Path

def main():
    config_path = Path("/Users/zhaoyuzhao/.openclaw/openclaw.json")
    
    print(f"📋 读取配置文件: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # 检查模型名
    print("\n🔍 检查模型配置:")
    
    # 原始模型名
    wrong_model = "deepseek/deepseek-r1"
    correct_model_chat = "deepseek-chat"
    correct_model_reasoner = "deepseek-reasoner"
    
    # 修复agetes.defaults
    if "agents" in config:
        agents = config["agents"]
        
        # 检查defaults
        if "defaults" in agents:
            defaults = agents["defaults"]
            
            # 修复主模型
            if "model" in defaults and "primary" in defaults["model"]:
                if defaults["model"]["primary"] == wrong_model:
                    print(f"⚠️  找到错误的主模型: {defaults['model']['primary']}")
                    defaults["model"]["primary"] = correct_model_chat
                    print(f"   修改为: {correct_model_chat}")
            
            # 修复fallbacks
            if "model" in defaults and "fallbacks" in defaults["model"]:
                for i, model in enumerate(defaults["model"]["fallbacks"]):
                    if model == wrong_model:
                        print(f"⚠️  找到错误的fallback模型: {model}")
                        defaults["model"]["fallbacks"][i] = f"openrouter/{correct_model_chat}"
                        print(f"   修改为: openrouter/{correct_model_chat}")
            
            # 修复models列表
            if "models" in defaults:
                if wrong_model in defaults["models"]:
                    print(f"⚠️  找到错误的models配置: {wrong_model}")
                    # 保留配置但移除错误条目
                    # 添加正确模型配置
                    defaults["models"][correct_model_chat] = {}
                    # 如果openrouter模型存在，也需要更新
                    openrouter_wrong = f"openrouter/{wrong_model}"
                    openrouter_correct = f"openrouter/{correct_model_chat}"
                    if openrouter_wrong in defaults["models"]:
                        defaults["models"][openrouter_correct] = defaults["models"].pop(openrouter_wrong)
                        print(f"   更新OpenRouter模型: {openrouter_wrong} -> {openrouter_correct}")
        
        # 修复agent列表中的配置
        if "list" in agents:
            for agent in agents["list"]:
                if agent.get("id") == "xiaofeng":
                    if agent.get("model") == wrong_model:
                        print(f"⚠️  找到xiaofeng agent的错误模型: {agent.get('model')}")
                        agent["model"] = correct_model_chat
                        print(f"   修改为: {correct_model_chat}")
    
    # 保存修改
    backup_path = config_path.with_suffix(".json.fix_backup")
    config_path.rename(backup_path)
    print(f"\n💾 原始配置已备份到: {backup_path}")
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ 新配置已保存到: {config_path}")
    
    # 验证修改
    print("\n🔍 验证修改:")
    print(f"   主模型: {config['agents']['defaults']['model']['primary']}")
    print(f"   fallbacks: {config['agents']['defaults']['model']['fallbacks']}")
    print(f"   models列表: {list(config['agents']['defaults']['models'].keys())}")
    for agent in config["agents"]["list"]:
        if agent.get("id") == "xiaofeng":
            print(f"   xiaofeng agent模型: {agent.get('model')}")
    
    print("\n💡 建议执行:")
    print("1. 重启Gateway: openclaw gateway restart")
    print("2. 验证配置: openclaw status")

if __name__ == "__main__":
    main()