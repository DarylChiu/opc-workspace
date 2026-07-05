#!/usr/bin/env python3
"""
检查Google Cloud认证和API状态
"""

import os
import json
from pathlib import Path

def check_api_key():
    """检查API密钥"""
    api_key_path = Path.home() / ".openclaw/auth/google/ielts_tts_2026.key"
    if not api_key_path.exists():
        print("❌ API密钥文件不存在")
        return None
    
    api_key = api_key_path.read_text().strip()
    print(f"📁 API密钥文件: {api_key_path}")
    print(f"🔑 API密钥: {api_key[:10]}... (长度: {len(api_key)} 字符)")
    
    if not api_key.startswith("AIza"):
        print("⚠️  API密钥格式异常（通常以AIza开头）")
    
    return api_key

def check_service_account():
    """检查服务账户文件"""
    service_account_path = Path.home() / ".openclaw/auth/google/service_account_info.txt"
    if not service_account_path.exists():
        print("❌ 服务账户文件不存在")
        return None
    
    content = service_account_path.read_text()
    print(f"\n📁 服务账户文件: {service_account_path}")
    print(f"📄 文件大小: {len(content)} 字符")
    
    # 检查文件内容
    lines = content.split('\n')
    print("\n📋 文件前10行:")
    for i, line in enumerate(lines[:10]):
        if line.strip():
            print(f"   {i+1:2}: {line[:80]}...")
    
    # 检查是否有JSON格式的服务账户
    import re
    json_match = re.search(r'(\{.*\})', content, re.DOTALL)
    if json_match:
        print("✅ 找到JSON格式的服务账户信息")
        try:
            json_data = json.loads(json_match.group())
            keys_to_check = ["type", "project_id", "private_key_id", "client_email"]
            for key in keys_to_check:
                if key in json_data:
                    value = json_data[key]
                    if key == "private_key_id":
                        print(f"   {key}: {value[:20]}...")
                    else:
                        print(f"   {key}: {value}")
            return json_match.group()
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            return None
    else:
        print("❌ 文件中未找到有效的JSON服务账户信息")
        return content

def validate_tts_api(api_key):
    """验证TTS API是否工作（我们知道这个API密钥在TTS上是工作的）"""
    print("\n" + "="*60)
    print("🎤 验证Google TTS API（已知工作）")
    print("="*60)
    
    import requests
    
    # Google TTS API端点
    tts_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    
    # 简单的请求数据
    request_data = {
        "input": {"text": "Hello"},
        "voice": {"languageCode": "en-US", "name": "en-US-Wavenet-D"},
        "audioConfig": {"audioEncoding": "MP3"}
    }
    
    try:
        response = requests.post(f"{tts_url}?key={api_key}", json=request_data, timeout=10)
        print(f"📡 TTS API请求状态: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ TTS API工作正常！")
            return True
        else:
            print(f"❌ TTS API错误: {response.status_code}")
            if response.text:
                try:
                    error_json = response.json()
                    print(f"   错误详情: {json.dumps(error_json, indent=2)}")
                except:
                    print(f"   响应内容: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ TTS API请求失败: {e}")
        return False

def create_environment_summary():
    """创建环境总结报告"""
    print("\n" + "="*60)
    print("📊 Google Cloud环境诊断")
    print("="*60)
    
    # 1. 检查API密钥
    api_key = check_api_key()
    
    # 2. 检查服务账户
    service_account = check_service_account()
    
    # 3. 验证已知工作的TTS API
    if api_key:
        validate_tts_api(api_key)
    
    # 4. 建议
    print("\n" + "="*60)
    print("🚀 问题诊断与解决方案")
    print("="*60)
    
    print("\n❌ 问题：Google Speech-to-Text API返回403错误（API_KEY_SERVICE_BLOCKED）")
    print("")
    print("可能原因：")
    print("1. API密钥未启用Speech-to-Text服务")
    print("2. API密钥访问受限（IP限制、引用来源限制等）")
    print("3. API密钥禁用或配额已用尽")
    print("4. 项目未启用Speech-to-Text API")
    print("")
    print("✅ 解决方案步骤：")
    print("")
    print("方案A：使用服务账户认证（推荐）")
    print("1. 创建服务账户JSON密钥文件")
    print("2. 设置环境变量：export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json")
    print("3. 使用google-cloud-speech库进行认证")
    print("")
    print("方案B：启用Speech-to-Text API")
    print("1. 访问Google Cloud Console")
    print("2. 导航到APIs & Services > Library")
    print("3. 搜索'Speech-to-Text API'并启用")
    print("4. 更新API密钥限制设置")
    print("")
    print("方案C：创建新的API密钥")
    print("1. 创建新的API密钥专门用于Speech-to-Text")
    print("2. 确保启用Speech-to-Text API")
    print("3. 将新密钥保存到文件")
    print("")
    print("立即执行方案A：")
    print("")
    print("1. 创建服务账户密钥：")
    print("   https://console.cloud.google.com/iam-admin/serviceaccounts")
    print("2. 下载JSON密钥文件")
    print("3. 将文件保存到 ~/.openclaw/auth/google/speech_service_account.json")
    print("4. 运行测试脚本")
    
    # 5. 创建配置说明文件
    config_guide = """
# Google Speech-to-Text API配置指南

## 现状分析
- ✅ TTS API工作正常
- ❌ Speech-to-Text API被阻止（API_KEY_SERVICE_BLOCKED）

## 推荐解决方案：服务账户认证

### 步骤1：创建服务账户
1. 访问Google Cloud Console：
   https://console.cloud.google.com/iam-admin/serviceaccounts
2. 选择你的项目或创建新项目
3. 点击"创建服务账户"
4. 名称：ielts-speech-stt
5. 授予权限：Project > Editor（或至少Cloud Speech-to-Text User）
6. 点击完成

### 步骤2：创建JSON密钥
1. 在服务账户列表中，找到新创建的账户
2. 点击"操作"菜单（三个点）> "管理密钥"
3. 点击"添加密钥" > "创建新密钥"
4. 选择JSON格式，点击"创建"
5. 下载文件到：~/.openclaw/auth/google/speech_service_account.json

### 步骤3：测试配置
运行以下Python脚本验证配置：
```python
from google.cloud import speech

# 自动从环境变量读取凭据
client = speech.SpeechClient()
print("✅ Speech客户端初始化成功")
```

## 备选方案：启用现有API密钥的Speech-to-Text访问

### 步骤1：检查API密钥限制
1. 访问：https://console.cloud.google.com/apis/credentials
2. 找到现有API密钥（显示部分：AIzaSyBdfh...）
3. 点击"API限制"选项卡
4. 确保"Speech-to-Text API"在允许的API列表中
5. 如果没有，点击"编辑密钥" > "限制密钥"
6. 选择"Speech-to-Text API"和"Cloud Text-to-Speech API"
7. 点击"保存"

### 步骤2：检查配額
1. 访问：https://console.cloud.google.com/apis/api/speech.googleapis.com/quotas
2. 确保Speech-to-Text API有可用配額
3. 如果需要，申请提高配額

## 测试脚本
运行以下脚本验证配置：
```bash
# 测试服务账户认证
python3 google_stt_service_account_test.py

# 测试API密钥认证  
python3 google_stt_api_key_test.py
```

## 故障排除
- 错误403：API_KEY_SERVICE_BLOCKED → 需要启用API或解除限制
- 错误401：凭据无效 → 检查密钥文件和服务账户权限
- 错误429：配額耗尽 → 等待或申请更多配額
"""
    
    with open("google_stt_config_guide.md", "w") as f:
        f.write(config_guide)
    
    print(f"\n📘 详细配置指南已保存: google_stt_config_guide.md")
    
    # 创建服务账户测试脚本
    create_service_account_test()

def create_service_account_test():
    """创建服务账户测试脚本"""
    script = """#!/usr/bin/env python3
"""
Google Speech-to-Text服务账户测试脚本
"""

import os
import sys
from pathlib import Path

def setup_service_account():
    # 检查环境变量
    env_var = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_var:
        print(f"✅ 环境变量已设置: {env_var}")
        if Path(env_var).exists():
            return env_var
        else:
            print(f"⚠️  文件不存在: {env_var}")
    
    # 检查默认位置
    default_path = Path.home() / ".openclaw/auth/google/speech_service_account.json"
    if default_path.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(default_path)
        print(f"✅ 找到默认服务账户文件: {default_path}")
        return str(default_path)
    
    # 列出可能的文件
    auth_dir = Path.home() / ".openclaw/auth/google"
    if auth_dir.exists():
        json_files = list(auth_dir.glob("*.json"))
        if json_files:
            print(f"📁 找到的JSON文件:")
            for file in json_files:
                print(f"   - {file.name}")
    
    print("❌ 未找到服务账户文件")
    print("")
    print("📝 请执行以下步骤:")
    print("1. 从Google Cloud Console下载服务账户JSON文件")
    print("2. 保存到: ~/.openclaw/auth/google/speech_service_account.json")
    print("3. 或设置环境变量: GOOGLE_APPLICATION_CREDENTIALS=/path/to/file.json")
    return None

def test_speech_client():
    try:
        from google.cloud import speech
        print("✅ google-cloud-speech库已安装")
        
        client = speech.SpeechClient()
        print("✅ Speech客户端初始化成功")
        
        # 测试客户端可用性
        print("🎯 客户端配置信息:")
        print(f"   项目: {client.project}")
        
        return client
    except ImportError:
        print("❌ google-cloud-speech未安装")
        print("📦 安装: pip install google-cloud-speech")
        return None
    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        return None

def main():
    print("🎤 Google Speech-to-Text服务账户测试")
    print("="*60)
    
    # 设置服务账户
    service_account_file = setup_service_account()
    if not service_account_file:
        return
    
    # 测试客户端
    client = test_speech_client()
    if not client:
        return
    
    print("\n" + "="*60)
    print("✅ 服务账户配置成功！")
    print("")
    print("下一步行动:")
    print("1. 运行音频转写测试:")
    print("   python3 google_stt_with_service_account.py")
    print("")
    print("2. 集成到Bryson语音MVP:")
    print("   - 替换现有模拟输入处理")
    print("   - 实现真实STT功能")
    print("")
    print("3. 性能优化:")
    print("   - 添加流式转录支持")
    print("   - 实现错误处理和重试")

if __name__ == "__main__":
    main()
"""
    
    with open("google_stt_service_account_test.py", "w") as f:
        f.write(script)
    
    print(f"📝 创建服务账户测试脚本: google_stt_service_account_test.py")

if __name__ == "__main__":
    create_environment_summary()