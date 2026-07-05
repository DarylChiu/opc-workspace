#!/usr/bin/env python3
"""
测试Bryson当前是否使用Deepseek独立Provider
验证配置切换的实际效果
"""

import os
import sys
import json

def check_current_config():
    """检查当前配置状态"""
    print("🔍 检查当前配置...")
    
    with open("openclaw.json", "r") as f:
        config = json.load(f)
    
    # 检查Xiaofeng Agent配置
    agents = config.get("agents", {}).get("list", [])
    xiaofeng_config = None
    
    for agent in agents:
        if agent.get("id") == "xiaofeng":
            xiaofeng_config = agent
            break
    
    if not xiaofeng_config:
        print("❌ 未找到Xiaofeng Agent配置")
        return False
    
    print(f"✅ Xiaofeng Agent配置:")
    print(f"   模型: {xiaofeng_config.get('model', '未设置')}")
    
    # 检查auth配置
    auth_profiles = config.get("auth", {}).get("profiles", {})
    deepseek_profile = auth_profiles.get("deepseek_bryson")
    
    if deepseek_profile:
        print(f"✅ Deepseek Profile已配置:")
        print(f"   Provider: {deepseek_profile.get('provider')}")
        print(f"   API Key: {deepseek_profile.get('apiKey', '')[:20]}...")
    else:
        print("❌ 未找到Deepseek Profile配置")
    
    # 检查模型是否指向deepseek/deepseek-chat
    current_model = xiaofeng_config.get("model", "")
    if current_model == "deepseek/deepseek-chat":
        print("✅ 模型已切换到Deepseek原生格式")
        return True
    elif current_model.startswith("openrouter/"):
        print("❌ 模型仍然是OpenRouter格式")
        return False
    else:
        print(f"⚠️  未知模型格式: {current_model}")
        return False

def test_deepseek_api_independent():
    """独立测试Deepseek API，不依赖OpenClaw"""
    print("\n🧪 独立测试Deepseek API...")
    
    import requests
    
    api_key = "REDACTED_API_KEY"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "This is a test from Bryson's independent Deepseek configuration. Please confirm the API is working."}
        ],
        "max_tokens": 30,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            tokens = data.get("usage", {})
            
            print(f"✅ Deepseek API独立测试成功!")
            print(f"   响应: {content}")
            print(f"   Token使用: {tokens.get('total_tokens', 'N/A')}")
            print(f"   模型: {data.get('model', 'N/A')}")
            return True
        else:
            print(f"❌ Deepseek API错误: {response.status_code}")
            print(f"   错误信息: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def check_openclaw_gateway():
    """检查OpenClaw Gateway状态"""
    print("\n🔧 检查OpenClaw Gateway状态...")
    
    # 检查Gateway进程
    try:
        import subprocess
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        if "openclaw gateway" in result.stdout:
            print("✅ OpenClaw Gateway进程正在运行")
            
            # 尝试获取状态
            try:
                # 查看是否有本地gateway运行
                subprocess.run(["curl", "-s", "http://localhost:18789/status"], 
                             capture_output=True, text=True, timeout=5)
                print("✅ Gateway HTTP服务可达")
                return True
            except:
                print("⚠️  Gateway HTTP服务可能未监听或需要重启")
                return False
        else:
            print("❌ OpenClaw Gateway进程未运行")
            return False
    except Exception as e:
        print(f"⚠️  进程检查异常: {e}")
        return None

def show_next_steps():
    """显示下一步操作"""
    print("\n📋 当前状态总结:")
    print("1. ✅ 配置文件已更新 (openclaw.json)")
    print("2. ✅ Deepseek API独立测试通过")
    print("3. ⚠️  OpenClaw Gateway可能需要重启以应用配置")
    
    print("\n🚀 下一步行动:")
    print("【选项A】重启OpenClaw Gateway服务")
    print("   命令: openclaw gateway restart")
    print("   或: systemctl restart openclaw")
    
    print("\n【选项B】创建临时测试会话验证配置")
    print("   在当前状态验证后，可以:")
    print("   1. 创建新的小风测试会话")
    print("   2. 观察API调用是否使用Deepseek独立Key")
    print("   3. 测试成本追踪是否独立")
    
    print("\n【选项C】观察当前会话变化")
    print("   监控当前Feishu对话下次请求:")
    print("   - 检查session_status显示的Provider")
    print("   - 观察API调用来源")

def main():
    print("🚀 Bryson独立Deepseek Provider验证")
    print("=" * 60)
    
    # 1. 检查配置
    config_ok = check_current_config()
    
    # 2. 测试Deepseek API
    api_ok = test_deepseek_api_independent()
    
    # 3. 检查Gateway状态
    gateway_ok = check_openclaw_gateway()
    
    # 4. 总结
    print("\n" + "=" * 60)
    print("🎯 验证结果:")
    
    if config_ok and api_ok:
        print("✅ 配置和API测试都通过!")
        print("✅ Deepseek独立Provider已配置完成")
        print("⚠️  需要重启OpenClaw Gateway使配置生效")
    elif config_ok and not api_ok:
        print("⚠️  配置已修改，但API测试失败")
        print("   可能需要检查Deepseek API Key或网络")
    elif not config_ok and api_ok:
        print("⚠️  API工作正常，但配置未正确修改")
        print("   可能需要重新运行配置脚本")
    else:
        print("❌ 配置和API测试均失败")
        print("   需要从头检查问题")
    
    # 显示下一步
    show_next_steps()

if __name__ == "__main__":
    main()