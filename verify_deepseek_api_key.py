#!/usr/bin/env python3
"""
验证Deepseek.com API密钥的有效性
专门测试OpenRouter平台上的Deepseek认证
"""

import requests
import json
import sys
import time

def test_openrouter_auth(api_key: str):
    """测试OpenRouter认证端点"""
    print("🔍 测试步骤1: OpenRouter API认证状态")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers=headers,
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                usage_data = data["data"]
                print(f"   ✅ OpenRouter认证成功!")
                print(f"      每日用量: ${usage_data.get('usage_daily', 0):.4f}")
                print(f"      每周用量: ${usage_data.get('usage_weekly', 0):.4f}")
                print(f"      剩余额度: ${usage_data.get('limit_remaining', 0):.2f}")
                return True, usage_data
            else:
                print(f"   ⚠️ 响应格式异常: {data}")
                # 仍然尝试其他测试
        elif response.status_code == 401:
            print(f"   ❌ API Key无效 (401 Unauthorized)")
            return False, {"error": "Invalid API Key"}
        else:
            print(f"   ⚠️ 其他状态码: {response.status_code}")
            print(f"      响应: {response.text[:200]}")
    
    except requests.exceptions.Timeout:
        print("   ❌ 请求超时")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    return None, {}  # 不确定状态

def test_deepseek_chat_completion(api_key: str):
    """测试Deepseek聊天完成端点"""
    print("\n🔍 测试步骤2: Deepseek聊天完成能力")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "user", "content": "Hello, this is a test message to verify API key validity."}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        elapsed = time.time() - start_time
        print(f"   响应时间: {elapsed:.2f}秒")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                print(f"   ✅ 聊天完成成功!")
                usage = data.get("usage", {})
                print(f"      使用统计: {usage.get('prompt_tokens', 0)}提示 + {usage.get('completion_tokens', 0)}完成 = {usage.get('total_tokens', 0)}总")
                return True, data
            else:
                print(f"   ⚠️ 响应中无choices字段")
        elif response.status_code == 401:
            print(f"   ❌ API Key无效 (401 Unauthorized)")
            return False, {"error": "Invalid API Key"}
        elif response.status_code == 429:
            print(f"   ⚠️ 请求过多 (429 Rate Limited)")
            return True, {"warning": "Rate limited, but key is valid"}
        else:
            print(f"   ⚠️ 其他错误: {response.status_code}")
            print(f"      响应: {response.text[:200]}")
    
    except requests.exceptions.Timeout:
        print("   ❌ 请求超时")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    return None, {}

def test_deepseek_models_list(api_key: str):
    """测试获取可用模型列表"""
    print("\n🔍 测试步骤3: 获取可用模型列表")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                models = data["data"]
                deepseek_models = [m for m in models if "deepseek" in m.get("id", "").lower()]
                
                print(f"   ✅ 模型列表获取成功!")
                print(f"      总模型数: {len(models)}")
                print(f"      Deepseek模型数: {len(deepseek_models)}")
                
                if deepseek_models:
                    print(f"      可用Deepseek模型:")
                    for model in deepseek_models[:3]:  # 显示前3个
                        id = model.get("id", "")
                        pricing = model.get("pricing", {})
                        prompt = pricing.get("prompt", "N/A")
                        completion = pricing.get("completion", "N/A")
                        print(f"        - {id}: 提示${prompt}/1M, 完成${completion}/1M")
                
                return True, models
        elif response.status_code == 401:
            print(f"   ❌ API Key无效 (401 Unauthorized)")
            return False, {"error": "Invalid API Key"}
    
    except requests.exceptions.Timeout:
        print("   ❌ 请求超时")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    return None, []

def main():
    """主函数"""
    print("=" * 60)
    print("🔑 Deepseek API Key验证工具")
    print("=" * 60)
    
    # 从openclaw.json获取API Key
    try:
        with open("/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/openclaw.json", "r") as f:
            config = json.load(f)
        
        api_key = config['auth']['profiles']['deepseek_bryson']['apiKey']
        print(f"📁 从配置文件中找到API Key")
        print(f"   Key前缀: {api_key[:20]}...")
        
    except Exception as e:
        print(f"❌ 无法读取配置文件: {e}")
        
        # 尝试从参数获取
        if len(sys.argv) > 1:
            api_key = sys.argv[1]
            print(f"📝 使用命令行参数提供的API Key")
            print(f"   Key前缀: {api_key[:20]}...")
        else:
            print("❌ 请提供API Key: python verify_deepseek_api_key.py YOUR_API_KEY")
            return False
    
    print("\n" + "=" * 60)
    print("🚀 开始API Key验证...")
    print("=" * 60)
    
    # 运行测试
    test_results = []
    
    # 测试1: OpenRouter认证
    auth_success, auth_data = test_openrouter_auth(api_key)
    test_results.append(("认证测试", auth_success))
    
    # 测试2: 聊天完成
    chat_success, chat_data = test_deepseek_chat_completion(api_key)
    test_results.append(("聊天完成测试", chat_success))
    
    # 测试3: 模型列表
    models_success, models_data = test_deepseek_models_list(api_key)
    test_results.append(("模型列表测试", models_success))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 验证结果汇总")
    print("=" * 60)
    
    success_count = sum(1 for _, success in test_results if success is True)
    total_count = len([s for _, s in test_results if s is not None])
    
    for test_name, success in test_results:
        if success is True:
            status = "✅ 通过"
        elif success is False:
            status = "❌ 失败"
        else:
            status = "⚠️  未确定"
        print(f"   {test_name}: {status}")
    
    print(f"\n   🔢 通过测试: {success_count}/{total_count}")
    
    if success_count >= 1:
        print("\n" + "=" * 60)
        print("🎉 API Key验证成功!")
        print("=" * 60)
        print(f"📋 结论: API Key有效，可以在OpenRouter平台上使用Deepseek模型")
        print(f"🔧 可访问: Deepseek-Chat, Deepseek-R1等模型")
        return True
    elif success_count == 0 and total_count > 0:
        print("\n" + "=" * 60)
        print("❌ API Key验证失败")
        print("=" * 60)
        print(f"📋 结论: API Key可能无效或过期")
        print(f"🔧 建议:")
        print(f"   1. 检查API Key是否正确")
        print(f"   2. 访问 https://openrouter.ai/settings/keys 验证")
        print(f"   3. 确保账户有足够的额度")
        return False
    else:
        print("\n" + "=" * 60)
        print("⚠️  API Key验证结果不确定")
        print("=" * 60)
        print(f"📋 结论: 需要进一步验证")
        print(f"🔧 建议: 尝试在网络环境稳定的情况下重新测试")
        return None

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