#!/usr/bin/env python3
"""
测试OpenClaw实际使用的provider
通过分析Gateway日志来确定是否使用Deepseek直接provider还是OpenRouter
"""

import subprocess
import json
import os
import time
from pathlib import Path

def test_gateway_connection():
    """测试Gateway连接"""
    print("🔍 测试Gateway连接...")
    try:
        result = subprocess.run(
            ["~/.nvm/versions/node/v24.14.0/bin/openclaw", "gateway", "status"],
            capture_output=True,
            text=True,
            shell=True
        )
        if "running" in result.stdout.lower():
            print("✅ Gateway正在运行")
            print(f"   {result.stdout.split('Gateway service')[1].split('\\n')[0]}")
            return True
        else:
            print(f"❌ Gateway状态异常: {result.stdout[:200]}")
            return False
    except Exception as e:
        print(f"❌ Gateway连接失败: {e}")
        return False

def check_gateway_logs():
    """检查Gateway日志"""
    print("\n🔍 检查Gateway日志...")
    log_path = "/tmp/openclaw/openclaw-2026-04-12.log"
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            lines = f.readlines()[-50:]  # 最后50行
        deepseek_mentions = [line for line in lines if "deepseek" in line.lower() or "provider" in line.lower()]
        openrouter_mentions = [line for line in lines if "openrouter" in line.lower()]
        
        print(f"✅ 找到日志文件: {log_path}")
        print(f"   包含'deepseek'的行数: {len(deepseek_mentions)}")
        print(f"   包含'openrouter'的行数: {len(openrouter_mentions)}")
        
        if len(deepseek_mentions) > 0:
            print("\n📍 最近的Deepseek相关日志:")
            for line in deepseek_mentions[-5:]:
                print(f"   {line.strip()}")
        
        if len(openrouter_mentions) > 0:
            print("\n📍 最近的OpenRouter相关日志:")
            for line in openrouter_mentions[-5:]:
                print(f"   {line.strip()}")
        return True
    else:
        print(f"❌ 日志文件不存在: {log_path}")
        return False

def test_direct_api_call():
    """测试直接API调用"""
    print("\n🔍 测试Direct API调用...")
    
    # 测试脚本内容
    test_code = '''
import json
import requests

api_key = "REDACTED_API_KEY"
url = "https://api.deepseek.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Say 'Direct API Test Successful'"}],
    "max_tokens": 5
}

try:
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    
    response = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"Response: {content}")
        print("✅ Direct Deepseek API调用成功")
    else:
        print(f"Error Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Direct API调用失败: {e}")
'''
    
    try:
        result = subprocess.run(
            ["python3", "-c", test_code],
            capture_output=True,
            text=True,
            timeout=15
        )
        print(result.stdout)
        if "Direct API调用成功" in result.stdout:
            return True
        else:
            print(f"stderr: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Direct API测试超时")
        return False

def analyze_auth_config():
    """分析认证配置"""
    print("\n🔍 分析认证配置...")
    
    auth_dir = Path("/Users/zhaoyuzhao/.openclaw/auth")
    
    print(f"🔑 查找API keys:")
    for key_file in auth_dir.rglob("*.json"):
        print(f"   - {key_file.relative_to(auth_dir)}")
        try:
            content = json.loads(key_file.read_text())
            if "key" in content:
                key_preview = content["key"][:20] + "..." if len(content["key"]) > 20 else content["key"]
                print(f"      Key: {key_preview}")
        except:
            pass
    
    # 检查agents/xiaofeng目录
    agent_auth_dir = auth_dir / "agents" / "xiaofeng"
    print(f"\n🔑 {agent_auth_dir}:")
    for key_file in agent_auth_dir.glob("*.json"):
        print(f"   - {key_file.name}")
        try:
            content = json.loads(key_file.read_text())
            if "key" in content:
                key_preview = content["key"][:20] + "..." if len(content["key"]) > 20 else content["key"]
                print(f"      Key: {key_preview}")
        except:
            pass

def main():
    print("="*60)
    print("🐙 测试OpenClaw Provider 切换情况")
    print("="*60)
    
    # 1. 测试Gateway状态
    gateway_ok = test_gateway_connection()
    
    # 2. 分析认证配置
    analyze_auth_config()
    
    # 3. 测试直接API调用
    direct_api_ok = test_direct_api_call()
    
    # 4. 检查日志
    logs_ok = check_gateway_logs()
    
    print("\n" + "="*60)
    print("📊 测试结果摘要")
    print("="*60)
    print(f"Gateway状态: {'✅ 正常' if gateway_ok else '❌ 异常'}")
    print(f"Direct API: {'✅ 成功' if direct_api_ok else '❌ 失败'}")
    print(f"日志检查: {'✅ 完成' if logs_ok else '❌ 失败'}")
    
    if gateway_ok and direct_api_ok:
        print("\n💡 建议:")
        print("1. 重启Gateway: openclaw gateway restart")
        print("2. 验证配置: openclaw config get agents.defaults.models")
        print("3. 监控下一次会话调用的provider信息")
    else:
        print("\n🚨 需要修复的问题:")
        if not direct_api_ok:
            print("   - Deepseek API Key可能无效或过期")
        if not gateway_ok:
            print("   - Gateway服务可能未正确重启")

if __name__ == "__main__":
    main()