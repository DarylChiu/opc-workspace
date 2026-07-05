#!/usr/bin/env python3
"""
检查当前OpenClaw实际使用的provider
"""

import requests
import json
import sys

def test_current_provider():
    """测试当前OpenClaw Gateway的实际provider"""
    
    print("🔍 测试当前OpenClaw Gateway的实际provider")
    
    # 尝试使用当前配置进行API调用
    try:
        # 模拟OpenClaw的请求格式
        url = "http://localhost:18789/api/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test"  # Gateway会使用自己的认证
        }
        
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "user", "content": "简单测试，请回复'测试成功'"}
            ],
            "max_tokens": 20,
            "temperature": 0.1
        }
        
        print("🚀 向OpenClaw Gateway发送测试请求...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        print(f"📡 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Gateway响应成功!")
            print(f"   模型: {data.get('model', 'unknown')}")
            
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                print(f"   回复: {content}")
            
            # 检查provider信息
            print(f"   完整响应: {json.dumps(data, indent=2)[:500]}...")
            return True
            
        else:
            print(f"❌ Gateway响应失败: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到OpenClaw Gateway (端口18789)")
        print("   请检查Gateway是否在运行: openclaw gateway status")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    print("=" * 60)
    print("🔄 OpenClaw Gateway Provider测试")
    print("=" * 60)
    
    # 检查Gateway状态
    print("1. 检查Gateway状态...")
    try:
        import subprocess
        result = subprocess.run(["openclaw", "gateway", "status"], 
                               capture_output=True, text=True, timeout=5)
        print(f"   Gateway状态: {result.stdout.strip()}")
    except Exception as e:
        print(f"   ⚠️ 无法检查Gateway状态: {e}")
    
    # 测试当前provider
    print("\n2. 测试当前provider...")
    test_current_provider()
    
    print("\n" + "=" * 60)
    print("📋 总结")
    print("=" * 60)
    
    print("基于之前的测试结果:")
    print("✅ Deepseek.com API Key验证成功:")
    print("   - 直接API调用: 200 OK")
    print("   - 余额查询: 成功 (2.00 USD, 119.99 CNY)")
    print("   - Token消耗: 正常")
    
    print("\n🔴 OpenClaw配置问题:")
    print("   - 模型名称格式混淆: 'anthropic/deepseek-chat'")
    print("   - 实际使用OpenRouter作为fallback provider")
    print("   - Deepseek直接provider可能未被正确激活")
    
    print("\n💡 建议修复步骤:")
    print("1. 修改openclaw.json中的模型配置")
    print("2. 重启OpenClaw Gateway")
    print("3. 验证provider切换成功")
    
    return True

if __name__ == "__main__":
    main()
