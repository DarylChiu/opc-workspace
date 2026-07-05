#!/usr/bin/env python3
"""
测试Deepseek API直接调用
验证Daryl提供的API Key和端点正常工作
"""

import os
import sys
import requests
import json

def test_deepseek_direct():
    """测试Deepseek原生API端点"""
    api_key = "REDACTED_API_KEY"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "你好，请用一个简短的句子测试API连接。"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    print("🧪 测试Deepseek原生API端点: https://api.deepseek.com/chat/completions")
    print(f"🔑 API Key: {api_key[:20]}...")
    
    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API调用成功！")
            print("📝 响应内容:", data.get("choices", [{}])[0].get("message", {}).get("content", ""))
            print("🔢 Token使用:", data.get("usage", {}))
            print("🌐 模型:", data.get("model", ""))
            return True, data
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"   错误信息: {response.text[:200]}")
            return False, {"error": response.text[:200]}
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False, {"error": str(e)}

def check_openrouter_config():
    """检查当前OpenRouter配置"""
    print("\n🔍 检查当前OpenClaw配置:")
    print("   1. 全局默认模型:", openclaw_config.get("agents", {}).get("defaults", {}).get("model", {}).get("primary", "未找到"))
    print("   2. Xiaofeng Agent模型:", xiaofeng_config.get("model", "未找到"))
    print("   3. 环境变量OPENROUTER_API_KEY:", "已设置" if "OPENROUTER_API_KEY" in os.environ else "未设置")

if __name__ == "__main__":
    print("🚀 Bryson独立Deepseek Provider测试")
    print("=" * 60)
    
    # 先测试Deepseek API
    success, response = test_deepseek_direct()
    
    if success:
        print("\n🎯 Deepseek API测试通过！")
        print("📋 下一步：配置Deepseek作为OpenClaw Provider")
        
        # 建议配置方案
        print("\n💡 建议配置方案:")
        print("""方案1：通过OpenAI兼容接口
   provider: "openai"
   baseURL: "https://api.deepseek.com"
   apiKey: "REDACTED_API_KEY"
   model: "deepseek-chat"
   
方案2：替换OpenRouter模型引用
   model: "deepseek/deepseek-chat" (可能需要自定义provider)""")
    else:
        print("\n⚠️  Deepseek API测试失败，将保持当前OpenRouter配置")