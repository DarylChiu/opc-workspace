#!/usr/bin/env python3
"""
Deepseek API Key 测试脚本
测试提供的Deepseek官方API Key是否可用
"""

import os
import sys
import requests
import json
from datetime import datetime

def test_deepseek_key(api_key: str):
    """测试Deepseek API Key是否可用"""
    
    # 检查Key格式
    print(f"🔑 测试API Key: {api_key[:20]}...")
    
    # 测试OpenRouter API端点（与Deepseek兼容）
    test_endpoints = [
        {
            "name": "OpenRouter API状态",
            "url": "https://openrouter.ai/api/v1/auth/key",
            "headers": {"Authorization": f"Bearer {api_key}"}
        },
        {
            "name": "DeepSeek Chat模型测试",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "method": "POST",
            "headers": {"Authorization": f"Bearer {api_key}"},
            "data": json.dumps({
                "model": "deepseek/deepseek-r1",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            })
        }
    ]
    
    results = []
    
    for endpoint in test_endpoints:
        print(f"\n🧪 测试: {endpoint['name']}")
        try:
            if endpoint.get("method", "GET") == "GET":
                response = requests.get(
                    endpoint["url"],
                    headers=endpoint["headers"],
                    timeout=10
                )
            else:
                response = requests.post(
                    endpoint["url"],
                    headers=endpoint["headers"],
                    data=endpoint.get("data", ""),
                    timeout=15
                )
            
            status_code = response.status_code
            print(f"  状态码: {status_code}")
            
            if status_code == 200:
                try:
                    data = response.json()
                    
                    if "data" in data or "choices" in data:
                        # OpenRouter auth/key端点
                        if "data" in data:
                            print(f"  ✅ 成功 - 账户信息:")
                            print(f"     每日用量: ${data['data'].get('usage_daily', 0):.4f}")
                            print(f"     每周用量: ${data['data'].get('usage_weekly', 0):.4f}")
                            print(f"     剩余额度: ${data['data'].get('limit_remaining', 0):.2f}")
                        
                        # Chat completions端点
                        elif "choices" in data:
                            print(f"  ✅ 成功 - 模型响应正常")
                        
                        results.append({
                            "test": endpoint["name"],
                            "status": "success",
                            "code": status_code,
                            "data": data if endpoint["name"] == "OpenRouter API状态" else {"model_working": True}
                        })
                    else:
                        print(f"  ⚠️  警告: 响应格式异常")
                        print(f"     响应内容: {data}")
                        results.append({
                            "test": endpoint["name"],
                            "status": "warning",
                            "code": status_code,
                            "data": data
                        })
                
                except json.JSONDecodeError:
                    print(f"  ❌ 失败: 响应不是有效的JSON")
                    print(f"     原始响应: {response.text[:200]}")
                    results.append({
                        "test": endpoint["name"],
                        "status": "error",
                        "code": status_code,
                        "error": "Invalid JSON response"
                    })
            
            elif status_code == 401:
                print(f"  ❌ 失败: API Key无效 (401 Unauthorized)")
                results.append({
                    "test": endpoint["name"],
                    "status": "error",
                    "code": status_code,
                    "error": "Invalid API Key"
                })
                return False, results  # 如果Key无效，提前退出
            
            elif status_code == 429:
                print(f"  ⚠️  警告: 请求过于频繁 (429 Rate Limited)")
                results.append({
                    "test": endpoint["name"],
                    "status": "warning",
                    "code": status_code,
                    "error": "Rate limited"
                })
            
            else:
                print(f"  ❌ 失败: HTTP {status_code}")
                print(f"     响应: {response.text[:200]}")
                results.append({
                    "test": endpoint["name"],
                    "status": "error",
                    "code": status_code,
                    "error": response.text[:200]
                })
        
        except requests.exceptions.RequestException as e:
            print(f"  ❌ 网络错误: {e}")
            results.append({
                "test": endpoint["name"],
                "status": "error",
                "code": None,
                "error": str(e)
            })
    
    # 判断整体结果
    success_tests = [r for r in results if r["status"] == "success"]
    if len(success_tests) >= 1:
        return True, results
    else:
        return False, results

def test_current_openrouter_key():
    """测试当前OpenRouter环境变量Key"""
    print("=" * 60)
    print("🔍 测试当前OpenRouter环境变量Key")
    
    current_key = os.environ.get("OPENROUTER_API_KEY")
    if not current_key:
        print("未找到 OPENROUTER_API_KEY 环境变量")
        return False, []
    
    print(f"当前Key: {current_key[:20]}...")
    return test_deepseek_key(current_key)

def main():
    """主函数"""
    print("🧪 Bryson独立API Key测试系统")
    print("-" * 60)
    
    # 检查是否提供了Deepseek Key作为命令行参数
    if len(sys.argv) > 1:
        deepseek_key = sys.argv[1]
        print(f"🎯 测试提供的Deepseek API Key")
        success_deepseek, results_deepseek = test_deepseek_key(deepseek_key)
        
        # 保存测试结果
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "key_type": "deepseek_provided",
            "key_preview": f"{deepseek_key[:10]}...{deepseek_key[-10:]}",
            "success": success_deepseek,
            "tests": results_deepseek
        }
        
        with open("deepseek_key_test_result.json", "w") as f:
            json.dump(test_result, f, indent=2, ensure_ascii=False)
        
        if success_deepseek:
            print("\n✅ Deepseek Key测试通过！可以作为独立Key使用。")
            print("建议保存为: ~/.openclaw/bryson_openrouter.key")
            
            # 保存Key到文件
            key_file = os.path.expanduser("~/.openclaw/bryson_openrouter.key")
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            
            with open(key_file, "w") as f:
                f.write(deepseek_key)
            
            print(f"✅ Key已保存到: {key_file}")
            
            # 创建fallback脚本
            create_fallback_script(deepseek_key)
            
        else:
            print("\n❌ Deepseek Key测试失败，将使用当前OpenRouter Key作为fallback")
            print("Fallback Key: ", os.environ.get("OPENROUTER_API_KEY")[:20] + "...")
    
    else:
        print("⚠️  请提供Deepseek API Key作为命令行参数")
        print("用法: python test_deepseek_key.py YOUR_DEEPSEEK_API_KEY")
        
        # 测试当前环境key
        test_current_openrouter_key()

def create_fallback_script(deepseek_key):
    """创建fallback配置脚本"""
    # 简单保存Key文件，不使用shell变量替换
    script_content = f'''#!/bin/bash
# Bryson API Key Fallback 配置脚本
# 将Deepseek Key设置为Bryson专用环境变量

# 设置Bryson专用Key
export BRYSON_OPENROUTER_KEY="{deepseek_key}"
export BRYSON_DEEPSEEK_KEY="{deepseek_key}"

echo "Bryson专用API Key已设置为环境变量:"
echo "  BRYSON_OPENROUTER_KEY: {deepseek_key[:20]}..."
echo "  BRYSON_DEEPSEEK_KEY: {deepseek_key[:20]}..."

# 提醒用户如何切换
echo ""
echo "使用方法:"
echo "1. 临时切换: export OPENROUTER_API_KEY=\"$BRYSON_DEEPSEEK_KEY\""
echo "2. 测试命令: curl -H \"Authorization: Bearer $BRYSON_DEEPSEEK_KEY\" https://openrouter.ai/api/v1/auth/key"
'''
    
    script_path = os.path.expanduser("~/.openclaw/bryson_key_setup.sh")
    with open(script_path, "w") as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    print(f"✅ Fallback脚本已创建: {script_path}")
    print(f"   使用: source {script_path}")

if __name__ == "__main__":
    main()