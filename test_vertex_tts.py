#!/usr/bin/env python3
"""
测试Vertex AI Text-to-Speech API
使用提供的API密钥
"""

import requests
import json
import base64
import os
from google.auth.transport.requests import Request
from google.oauth2 import service_account

# 用户提供的API密钥
API_KEY = "Ab8RN6LrUuSQqwZ2KWCjd7ePZrYKGWSrZA9KZyppTnaKefsCRQ"

def test_with_api_key():
    """使用API密钥测试Vertex TTS API"""
    try:
        # Vertex AI API端点 (需要替换为正确的端点)
        project_id = "your-project-id"  # 需要获取项目ID
        location = "us-central1"
        
        # API endpoint (来自Google文档)
        endpoint = f"https://{location}-aiplatform.googleapis.com/v1"
        
        # 测试请求
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 检查API密钥格式
        print(f"API密钥格式检查:")
        print(f"  长度: {len(API_KEY)} 字符")
        print(f"  前缀: {API_KEY[:10]}...")
        
        # 尝试不同的API端点
        test_endpoints = [
            "https://texttospeech.googleapis.com/v1/text:synthesize",
            "https://us-central1-texttospeech.googleapis.com/v1/text:synthesize",
            "https://texttospeech.googleapis.com/v1beta1/text:synthesize"
        ]
        
        for url in test_endpoints:
            print(f"\n尝试请求端点: {url}")
            try:
                # 简单的测试请求
                test_payload = {
                    "input": {
                        "text": "Hello, this is a test of Vertex AI Text-to-Speech."
                    },
                    "voice": {
                        "languageCode": "en-US",
                        "name": "en-US-Neural2-J"
                    },
                    "audioConfig": {
                        "audioEncoding": "MP3"
                    }
                }
                
                response = requests.post(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "X-Goog-Api-Key": API_KEY
                    },
                    params={"key": API_KEY},
                    json=test_payload,
                    timeout=10
                )
                
                print(f"  状态码: {response.status_code}")
                if response.status_code == 200:
                    print(f"  ✅ 成功！API密钥有效")
                    return True
                else:
                    print(f"  响应: {response.text[:200]}")
                    
            except Exception as e:
                print(f"  错误: {str(e)}")
        
        return False
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def check_api_key_info():
    """检查API密钥信息"""
    print("\n=== API密钥信息 ===")
    print("Vertex AI Text-to-Speech API通常使用服务账号JSON文件进行认证")
    print("如果这是API密钥字符串，可能需要通过不同方式进行配置")
    
    # 可能的API密钥类型
    print("\n可能的API密钥类型:")
    print("1. 标准API密钥 (用于GCP API)")
    print("2. 服务账号密钥 (JSON文件)")
    print("3. OAuth 2.0访问令牌")
    
    # 建议步骤
    print("\n建议:")
    print("1. 确认这是否是完整的API密钥字符串")
    print("2. 检查是否需要在Google Cloud控制台启用Vertex AI API")
    print("3. 确保有足够的权限")

if __name__ == "__main__":
    print("=== Vertex AI TTS API测试 ===\n")
    
    # 检查API密钥
    check_api_key_info()
    
    # 测试API密钥
    print("\n=== 开始API测试 ===")
    success = test_with_api_key()
    
    if not success:
        print("\n⚠️ API密钥测试失败")
        print("\n可能的原因:")
        print("1. API密钥格式不正确")
        print("2. Vertex AI API未启用")
        print("3. 需要创建服务账号并分配权限")
        print("4. 需要生成服务账号JSON密钥文件")
        
        print("\n推荐的解决方案:")
        print("1. 访问Google Cloud控制台: https://console.cloud.google.com/")
        print("2. 启用Vertex AI API")
        print("3. 创建服务账号并分配'Vertex AI User'角色")
        print("4. 生成JSON密钥文件")
        print("5. 下载JSON文件并用于认证")