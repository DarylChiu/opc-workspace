#!/usr/bin/env python3
"""
简化版Vertex AI TTS API测试
"""

import requests
import json
import sys

# 用户提供的API密钥
API_KEY = "Ab8RN6LrUuSQqwZ2KWCjd7ePZrYKGWSrZA9KZyppTnaKefsCRQ"

def test_tts_api():
    """测试Text-to-Speech API"""
    print("=== Vertex AI TTS API 测试 ===\n")
    
    # 检查API密钥格式
    print(f"API密钥: {API_KEY[:12]}... (前12位)")
    print(f"密钥长度: {len(API_KEY)} 字符")
    
    # Google Cloud Text-to-Speech API端点
    endpoints = [
        {
            "name": "Text-to-Speech v1",
            "url": "https://texttospeech.googleapis.com/v1/text:synthesize",
            "method": "POST"
        },
        {
            "name": "Text-to-Speech v1beta1",
            "url": "https://texttospeech.googleapis.com/v1beta1/text:synthesize",
            "method": "POST"
        },
        {
            "name": "列出可用声音 (测试GET请求)",
            "url": "https://texttospeech.googleapis.com/v1/voices",
            "method": "GET"
        }
    ]
    
    success = False
    
    for endpoint in endpoints:
        print(f"\n尝试端点: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")
        
        try:
            if endpoint['method'] == 'POST':
                # 构建TTS请求
                payload = {
                    "input": {
                        "text": "Hello, this is a test of Google Cloud Text-to-Speech API."
                    },
                    "voice": {
                        "languageCode": "en-US",
                        "name": "en-US-Neural2-J"
                    },
                    "audioConfig": {
                        "audioEncoding": "MP3"
                    }
                }
                
                # 尝试几种不同的认证方式
                auth_methods = [
                    ("API Key参数", {"key": API_KEY}, {}),
                    ("X-Goog-Api-Key头", {}, {"X-Goog-Api-Key": API_KEY}),
                    ("Authorization头", {}, {"Authorization": f"Bearer {API_KEY}"})
                ]
                
                for method_name, params, headers in auth_methods:
                    print(f"  使用认证方式: {method_name}")
                    
                    all_headers = {"Content-Type": "application/json", **headers}
                    
                    response = requests.post(
                        endpoint['url'],
                        params=params,
                        headers=all_headers,
                        json=payload,
                        timeout=10
                    )
                    
                    print(f"    状态码: {response.status_code}")
                    if response.status_code == 200:
                        print(f"    ✅ 成功！认证方式: {method_name}")
                        print("    API密钥有效，可以调用Text-to-Speech API")
                        success = True
                        # 显示部分响应
                        data = response.json()
                        if "audioContent" in data:
                            audio_len = len(data["audioContent"])
                            print(f"    音频数据大小: {audio_len} 字节")
                        return True
                    elif response.status_code == 403:
                        print(f"    ❌ 权限不足 (403)")
                        if "error" in response.json():
                            error = response.json()["error"]
                            print(f"    错误信息: {error.get('message', '未知错误')}")
                    elif response.status_code == 401:
                        print(f"    ❌ 认证失败 (401)")
                    else:
                        print(f"    ❌ 错误: {response.status_code}")
                        if response.text:
                            print(f"    响应: {response.text[:200]}")
                            
            elif endpoint['method'] == 'GET':
                # 测试GET请求
                params = {"key": API_KEY}
                
                response = requests.get(
                    endpoint['url'],
                    params=params,
                    timeout=10
                )
                
                print(f"  状态码: {response.status_code}")
                if response.status_code == 200:
                    print(f"  ✅ 成功！可以列出可用声音")
                    data = response.json()
                    voices = data.get("voices", [])
                    print(f"  找到 {len(voices)} 种声音")
                    success = True
                    return True
                else:
                    print(f"  ❌ 错误: {response.status_code}")
                    if response.text:
                        print(f"  响应: {response.text[:200]}")
                        
        except requests.exceptions.Timeout:
            print(f"  ⏰ 请求超时")
        except requests.exceptions.ConnectionError:
            print(f"  🔌 连接错误")
        except Exception as e:
            print(f"  ❗ 其他错误: {str(e)}")
    
    return success

def check_key_type():
    """分析API密钥类型"""
    print("\n=== API密钥分析 ===")
    
    # 检查密钥格式
    if len(API_KEY) > 100:
        print("这是一个较长的密钥，可能是JWT令牌或访问令牌")
    elif 30 <= len(API_KEY) <= 60:
        print("这看起来像标准的Google API密钥")
    else:
        print("密钥长度不标准，可能是其他类型的凭证")
    
    print("\n重要提醒:")
    print("1. 确保在Google Cloud控制台中启用了Text-to-Speech API")
    print("2. 确认API密钥有足够的权限")
    print("3. 检查是否需要在服务中使用项目ID")

def main():
    """主函数"""
    # 先检查密钥类型
    check_key_type()
    
    # 测试API
    print("\n" + "="*50)
    success = test_tts_api()
    
    if not success:
        print("\n⚠️ API测试失败，可能的原因:")
        print("1. API密钥无效或已过期")
        print("2. Text-to-Speech API未启用")
        print("3. 需要创建Google Cloud项目并进行配置")
        print("4. 密钥类型不正确")
        
        print("\n✅ 建议:")
        print("1. 访问: https://console.cloud.google.com/")
        print("2. 创建项目（如果还没有）")
        print("3. 启用'Cloud Text-to-Speech API'")
        print("4. 在'API和服务 -> 凭证'中创建API密钥")
        print("5. 复制新的API密钥")
        print("6. 可选：为安全起见，限制API密钥的访问范围")

if __name__ == "__main__":
    main()