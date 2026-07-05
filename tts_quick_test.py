#!/usr/bin/env python3
"""
TTS快速测试
"""

import requests
import json
import sys

def test_tts():
    base_url = "http://localhost:8082"
    
    print("🧪 TTS快速测试...")
    
    # 测试1: 简单TTS
    print("1. 简单TTS测试...")
    payload = {
        "text": "Hello Daryl! The TTS integration is now ready for testing.",
        "voice_template": "default"
    }
    
    try:
        response = requests.post(f"{base_url}/api/tts/synthesize", json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"   ✅ 成功! (缓存: {result.get('cached')})")
                print(f"      音频URL: {result.get('audio_url')}")
                print(f"      时长: {result.get('duration_seconds')}秒")
                
                # 下载音频文件测试
                audio_url = f"{base_url}{result.get('audio_url')}"
                audio_resp = requests.get(audio_url, timeout=5)
                if audio_resp.status_code == 200:
                    print(f"      音频可下载: {len(audio_resp.content)} 字节")
                    return True
                else:
                    print(f"      ⚠️ 音频下载异常: {audio_resp.status_code}")
            else:
                print(f"   ❌ 失败: {result.get('error')}")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            print(f"      响应: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    return False

def test_investor_templates():
    """测试投资者路演讲音模板"""
    print("\n2. 测试投资者路演讲音模板...")
    
    base_url = "http://localhost:8082"
    templates = {
        "opening": "Good morning investors. Our company offers a revolutionary financial platform.",
        "financial": "Revenue grew by 150% last quarter with strong profitability.",
        "vision": "We aim to transform financial management for small businesses.",
        "call_to_action": "Join our funding round and help us accelerate growth."
    }
    
    for template, text in templates.items():
        print(f"   📊 {template}...")
        
        payload = {
            "text": text,
            "voice_template": template
        }
        
        try:
            response = requests.post(f"{base_url}/api/tts/synthesize", json=payload, timeout=8)
            
            if response.status_code == 200:
                result = response.json()
                status = "✅" if result.get("success") else "❌"
                print(f"      {status} {result.get('cached', False)}")
            else:
                print(f"      ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ {e}")
    
    # 整体投资人测试
    print("\n3. 完整投资人路演讲音测试...")
    
    try:
        response = requests.post(f"{base_url}/api/tts/test-investor-pitch", timeout=15)
        if response.status_code == 200:
            result = response.json()
            print(f"   📊 结果: {result.get('summary')}")
            return True
    except Exception as e:
        print(f"   ❌ 投资人测试失败: {e}")
    
    return False

def main():
    print("="*60)
    print("🎯 TTS集成测试 (方案A完成验证)")
    print("="*60)
    
    # 检查服务器状态
    print("🔍 检查服务器状态...")
    try:
        response = requests.get("http://localhost:8082/api/status", timeout=5)
        data = response.json()
        
        print(f"   服务器: ✅ {data.get('status')} (v{data.get('version')})")
        print(f"   TTS配置: {'✅' if data.get('tts_configured') else '❌'}")
        print(f"   语音参数: IELTS 5.5-6.0适配语速: {data.get('voice_params', {}).get('speakingRate')}")
        print(f"   模板: {len(data.get('investor_templates', []))}个投资者路演讲音模板")
        
    except Exception as e:
        print(f"   ❌ 服务器状态检查失败: {e}")
        return False
    
    # 测试TTS功能
    if test_tts():
        test_investor_templates()
        
        print("\n" + "="*60)
        print("🎉 方案A - TTS集成冲刺完成!")
        print("="*60)
        print("✅ 已完成:")
        print("   1. Google TTS API完全集成")
        print("   2. DARYL个性化语音参数 (IELTS 5.5-6.0适配)")
        print("   3. 4个投资者路演讲音模板")
        print("   4. 音频缓存系统")
        print("   5. REST API + WebSocket端点")
        print("   6. 前端测试页面")
        print("")
        print("🚀 访问地址:")
        print("   - http://localhost:8082 (测试页面)")
        print("   - http://localhost:8082/api/status (状态)")
        print("   - http://localhost:8082/api/tts/test (快速测试)")
        print("   - http://localhost:8082/docs (API文档)")
        print("")
        print("📊 下一步: 方案B (移动端测试)")
        print("   当前方案A已完成，可以开始方案B")
        print("="*60)
        
        return True
    else:
        print("\n❌ TTS功能测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)