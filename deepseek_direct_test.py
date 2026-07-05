#!/usr/bin/env python3
import json
import os
import sys

def verify_deepseek_key():
    """直接验证Deepseek API密钥"""
    config_path = os.path.expanduser('~/.openclaw/openclaw.json')
    
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        profiles = config.get('auth', {}).get('profiles', {})
        deepseek_profile = profiles.get('deepseek_bryson')
        
        if not deepseek_profile:
            print("❌ 没有找到deepseek_bryson配置")
            return False
        
        provider = deepseek_profile.get('provider')
        mode = deepseek_profile.get('mode')
        
        print(f"✅ 找到Deepseek配置:")
        print(f"   提供方: {provider}")
        print(f"   模式: {mode}")
        
        # 模拟API调用测试
        if mode == 'api_key':
            print("✅ API密钥配置存在")
            
            # 测试环境变量和配置
            env_key = os.environ.get('DEEPSEEK_API_KEY')
            print(f"环境变量DEEPSEEK_API_KEY: {'已设置' if env_key else '未设置'}")
            
            return True
        else:
            print(f"❌ 不支持的模式: {mode}")
            return False
            
    except Exception as e:
        print(f"❌ 读取配置失败: {e}")
        return False

def check_current_agent_model():
    """检查当前agent的模型配置"""
    config_path = os.path.expanduser('~/.openclaw/openclaw.json')
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        agents = config.get('agents', {}).get('list', [])
        xiaofeng_agent = None
        
        for agent in agents:
            if agent.get('id') == 'xiaofeng':
                xiaofeng_agent = agent
                break
        
        if xiaofeng_agent:
            model = xiaofeng_agent.get('model')
            print(f"\n🎯 xiaofeng agent当前模型配置: {model}")
            print(f"   是否为Deepseek直连: {'deepseek/deepseek-r1' in str(model)}")
            
            defaults = config.get('agents', {}).get('defaults', {})
            primary_model = defaults.get('model', {}).get('primary')
            print(f"\n🔧 默认模型配置: {primary_model}")
            
            return model
        else:
            print("❌ 未找到xiaofeng agent配置")
            return None
            
    except Exception as e:
        print(f"❌ 检查agent配置失败: {e}")
        return None

def main():
    print("🔍 Deepseek直连配置验证")
    print("=" * 50)
    
    # 验证配置
    config_ok = verify_deepseek_key()
    
    print("\n" + "=" * 50)
    
    # 检查agent模型配置
    model = check_current_agent_model()
    
    print("\n" + "=" * 50)
    
    if config_ok and model and 'deepseek/deepseek-r1' in str(model):
        print("✅ 状态良好")
        print("   1. Deepseek API密钥配置存在")
        print("   2. xiaofeng agent配置为Deepseek直连模型")
        print("   3. 模型名称为: deepseek/deepseek-r1")
        return True
    else:
        print("⚠️ 需要进一步检查:")
        if not config_ok:
            print("   - Deepseek API配置可能有问题")
        if not model or 'deepseek/deepseek-r1' not in str(model):
            print("   - agent未配置为Deepseek直连模型")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)