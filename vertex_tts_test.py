#!/usr/bin/env python3
"""
测试Vertex AI Text-to-Speech调用
基于Google的官方文档
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta

# 用户提供的API密钥
USER_API_KEY = "Ab8RN6LrUuSQqwZ2KWCjd7ePZrYKGWSrZA9KZyppTnaKefsCRQ"

def test_vertex_tts_direct():
    """直接测试Vertex AI TTS可能的工作方式"""
    print("=== Vertex AI Text-to-Speech 测试 ===\n")
    
    # 根据最新文档，Vertex AI TTS可能需要不同的端点
    # 参考资料：https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/text-to-speech
    
    # 可能的Vertex AI端点
    vertex_endpoints = [
        {
            "name": "Vertex AI TTS (us-central1)",
            "url": "https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/us-central1/text:synthesize",
            "requires": ["PROJECT_ID", "ACCESS_TOKEN"]
        },
        {
            "name": "Vertex AI TTS (global)",
            "url": "https://aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/global/text:synthesize",
            "requires": ["PROJECT_ID", "ACCESS_TOKEN"]
        },
        {
            "name": "Vertex AI Speech API",
            "url": "https://speech.googleapis.com/v1/speech:synthesize",
            "requires": ["PROJECT_ID", "ACCESS_TOKEN"]
        }
    ]
    
    print(f"API密钥长度: {len(USER_API_KEY)} 字符")
    print(f"密钥前缀: {USER_API_KEY[:15]}...")
    print()
    
    # 分析可能的密钥类型
    print("=== 密钥类型分析 ===")
    if len(USER_API_KEY) == 50:
        print("这看起来像标准的Google Cloud API密钥 (50字符)")
    elif len(USER_API_KEY) > 100:
        print("这可能是一个JWT令牌或OAuth访问令牌")
    else:
        print("密钥长度非标准，可能不是API密钥")
    
    print("\n=== Google Cloud TTS API迁移状态 ===")
    print("根据你提到的情况：")
    print("✅ Google Cloud Text-to-Speech API 仍可直接使用")
    print("✅ Vertex AI 提供了增强功能，但不是强制迁移")
    print()
    
    # 测试当前API密钥的基本有效性
    print("=== 测试密钥有效性 ===")
    
    # 使用标准的Cloud TTS API测试（应该仍然可用）
    tts_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    
    payload = {
        "input": {
            "text": "Hello from Google Cloud Text-to-Speech"
        },
        "voice": {
            "languageCode": "en-US",
            "name": "en-US-Neural2-J"
        },
        "audioConfig": {
            "audioEncoding": "MP3"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": USER_API_KEY
    }
    
    params = {
        "key": USER_API_KEY
    }
    
    # 尝试多种认证方式
    methods = [
        ("URL参数 (key=)", {"params": params}, {}),
        ("X-Goog-Api-Key头部", {}, {"X-Goog-Api-Key": USER_API_KEY}),
        ("Authorization Bearer", {}, {"Authorization": f"Bearer {USER_API_KEY}"})
    ]
    
    for method_name, req_params, req_headers in methods:
        print(f"尝试: {method_name}")
        
        try:
            all_headers = {**headers, **req_headers}
            
            response = requests.post(
                tts_url,
                headers=all_headers,
                params=req_params.get("params", {}),
                json=payload,
                timeout=10
            )
            
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ 成功！可以使用标准TTS API")
                print(f"  响应长度: {len(response.text)} 字符")
                data = response.json()
                if "audioContent" in data:
                    print(f"  音频数据大小: {len(data['audioContent'])} 字节")
                return True
            elif response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "")
                print(f"  ❌ 错误: {error_msg[:100]}")
            elif response.status_code == 403:
                print(f"  🔒 权限不足 (403)，可能需要启用API或检查权限")
            elif response.status_code == 401:
                print(f"  🔑 认证无效 (401)")
            else:
                print(f"  ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ⚠️ 请求异常: {str(e)}")
    
    print("\n=== 解决方案 ===")
    print("\n1. **验证API密钥状态**")
    print("   访问: https://console.cloud.google.com/apis/credentials")
    print("   检查密钥是否显示为'活动'状态")
    
    print("\n2. **启用TTS API**")
    print("   访问: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com")
    print("   点击'启用'按钮")
    
    print("\n3. **创建新API密钥**")
    print("   - 删除当前密钥")
    print("   - 创建新API密钥")
    print("   - 立即复制保存")
    print("   - 添加API限制: texttospeech.googleapis.com")
    
    print("\n4. **检查账单账户**")
    print("   确保Google Cloud账户有有效的付款方式")
    print("   即使是免费额度也需要验证付款方式")
    
    print("\n5. **使用Vertex AI（如果需要）**")
    print("   如果确实需要Vertex AI特性:")
    print("   a. 创建服务账号")
    print("   b. 分配'Vertex AI User'角色")
    print("   c. 生成JSON密钥文件")
    print("   d. 使用服务账号认证")
    
    return False

def create_simple_test_script():
    """创建简单的测试脚本供用户使用"""
    script_content = """#!/usr/bin/env python3
import requests
import json
import sys

# 替换为你的API密钥
API_KEY = "YOUR_API_KEY_HERE"

def test_tts():
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    
    payload = {
        "input": {"text": "Hello, this is a test."},
        "voice": {"languageCode": "en-US"},
        "audioConfig": {"audioEncoding": "MP3"}
    }
    
    # 方法1: URL参数
    print("测试方法1: URL参数")
    response = requests.post(
        f"{url}?key={API_KEY}",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=10
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print("✅ API密钥有效！")
        data = response.json()
        print(f"音频数据大小: {len(data.get('audioContent', ''))} 字节")
        return True
    else:
        print(f"❌ 错误: {response.text[:200]}")
        return False

if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("请先在脚本中替换API_KEY变量")
        sys.exit(1)
    
    print("=== Google Cloud TTS API 测试 ===")
    success = test_tts()
    
    if not success:
        print("\\n可能的问题:")
        print("1. API密钥无效或过期")
        print("2. Text-to-Speech API未启用")
        print("3. 需要启用Google Cloud API")
        print("\\n解决方案:")
        print("1. 访问: https://console.cloud.google.com/apis/credentials")
        print("2. 创建新API密钥")
        print("3. 访问: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com")
        print("4. 点击'启用'按钮")
"""
    
    with open("simple_tts_test.py", "w") as f:
        f.write(script_content)
    
    print("已创建测试脚本: simple_tts_test.py")
    print("请将YOUR_API_KEY_HERE替换为你的API密钥")

if __name__ == "__main__":
    test_vertex_tts_direct()
    create_simple_test_script()