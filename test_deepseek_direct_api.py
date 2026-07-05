#!/usr/bin/env python3
"""
直接测试Deepseek.com官方API Key
使用Deepseek官方端点，不是OpenRouter
"""

import requests
import json
import sys
import time

def test_deepseek_official_api(api_key: str):
    """直接测试Deepseek.com官方API"""
    print("🔗 测试Deepseek.com官方API端点")
    print(f"🔑 API Key: {api_key[:20]}...")
    
    # Deepseek官方聊天完成端点
    url = "https://api.deepseek.com/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "Hello, this is a simple message to test Deepseek API connectivity. Please respond 'API test successful'."}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        print("🚀 发送请求到Deepseek.com官方API...")
        start_time = time.time()
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=20
        )
        
        elapsed = time.time() - start_time
        print(f"⏱️  响应时间: {elapsed:.2f}秒")
        print(f"📡 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Deepseek.com官方API调用成功!")
            
            # 显示模型信息
            model = data.get("model", "unknown")
            print(f"   🤖 使用模型: {model}")
            
            # 显示回复内容
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                content = message.get("content", "").strip()
                print(f"   💬 AI回复: {content[:100]}...")
            
            # 显示用量
            if "usage" in data:
                usage = data["usage"]
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                print(f"   📊 Token使用: {prompt_tokens}提示 + {completion_tokens}完成 = {total_tokens}总")
            
            return True, data
        
        elif response.status_code == 401:
            print("❌ 认证失败 (401 Unauthorized)")
            print("   API Key可能无效或过期")
            print(f"   响应: {response.text[:200]}")
            return False, {"error": "Authentication failed"}
        
        elif response.status_code == 429:
            print("⚠️  请求过多 (429 Rate Limited)")
            print("   API Key有效，但触发了速率限制")
            return True, {"warning": "Rate limited, but key is valid"}
        
        elif response.status_code == 400:
            print("❌ 请求错误 (400 Bad Request)")
            print(f"   响应: {response.text[:200]}")
            return False, {"error": "Bad request"}
        
        elif response.status_code == 403:
            print("❌ 禁止访问 (403 Forbidden)")
            print("   可能原因:")
            print("   1. 账户有欠费")
            print("   2. API功能未开启")
            print("   3. 地域限制")
            return False, {"error": "Forbidden"}
        
        else:
            print(f"⚠️  未知状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False, {"error": f"Status {response.status_code}"}
    
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False, {"error": "Timeout"}
    
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
        print("   无法连接到Deepseek.com")
        return False, {"error": "Connection failed"}
    
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False, {"error": str(e)}

def test_deepseek_balance(api_key: str):
    """测试Deepseek账户余额查询"""
    print("\n💰 测试Deepseek账户余额查询")
    
    # Deepseek官方余额查询端点
    url = "https://api.deepseek.com/user/balance"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📡 状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ 余额查询成功!")
                
                # 根据不同响应格式处理
                if "data" in data:
                    balance_data = data["data"]
                    balance = balance_data.get("balance", "N/A")
                    currency = balance_data.get("currency", "N/A")
                    print(f"   💰 账户余额: {balance} {currency}")
                else:
                    print(f"   📋 响应: {json.dumps(data, indent=2)}")
                
                return True, data
            except:
                print(f"   📋 原始响应: {response.text[:200]}...")
                return True, {"text": response.text}
        else:
            print(f"   ⚠️  余额查询失败: {response.status_code}")
            return False, {"error": f"Status {response.status_code}"}
    
    except Exception as e:
        print(f"   ❌ 余额查询异常: {e}")
        return False, {"error": str(e)}

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 Deepseek.com官方API直接测试")
    print("=" * 60)
    
    # 获取API Key
    try:
        with open("/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/openclaw.json", "r") as f:
            config = json.load(f)
        
        api_key = config['auth']['profiles']['deepseek_bryson']['apiKey']
        print(f"📁 从配置读取Key: {api_key[:20]}...")
        
    except Exception as e:
        print(f"❌ 无法读取配置: {e}")
        
        if len(sys.argv) > 1:
            api_key = sys.argv[1]
            print(f"🔄 使用命令行参数: {api_key[:20]}...")
        else:
            print("❌ 请提供API Key: python test_deepseek_direct_api.py YOUR_API_KEY")
            return False
    
    print("\n" + "=" * 60)
    
    # 测试1: 直接调用Deepseek API
    api_success, api_data = test_deepseek_official_api(api_key)
    
    # 测试2: 余额查询
    balance_success, balance_data = test_deepseek_balance(api_key)
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 最终验证结果")
    print("=" * 60)
    
    if api_success:
        print("✅ Deepseek.com官方API Key验证成功!")
        print("   🚀 可以: 直接调用Deepseek官方服务")
        print("   🤖 支持: deepseek-chat, deepseek-coder等模型")
        
        if balance_success:
            print("   💰 余额查询: 成功")
        else:
            print("   ⚠️  余额查询: 失败（可能是端点变化）")
        
        print("\n📋 结论: API Key完全有效，可以直接使用Deepseek.com服务")
        
    elif api_success is None:
        print("⚠️  API Key状态不确定")
        print("   需要进一步测试")
        
    else:
        print("❌ Deepseek.com官方API Key验证失败")
        print("   可能原因:")
        print("   1. API Key已过期")
        print("   2. 账户余额不足")
        print("   3. API功能未开启")
        print("   4. Key被撤销")
        print("\n💡 建议:")
        print("   1. 访问 https://platform.deepseek.com/api_keys")
        print("   2. 检查账户状态和余额")
        print("   3. 创建新的API Key")
    
    return api_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ 测试过程中出现意外错误: {e}")
        sys.exit(3)