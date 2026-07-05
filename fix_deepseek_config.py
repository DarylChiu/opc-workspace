#!/usr/bin/env python3
"""
修正Deepseek主配置文件 - 确保100%使用Deepseek直连API
修复主目录配置中缺少API Key的问题
"""

import os
import json
import shutil
import sys
from pathlib import Path

def main():
    print("🔧 修正Deepseek主配置文件")
    print("="*50)
    
    # 配置文件路径
    main_config_path = "/Users/zhaoyuzhao/.openclaw/openclaw.json"
    workspace_config_path = "/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/openclaw.json"
    
    # Deepseek API Key (从工作区配置读取或硬编码)
    DEEPSEEK_API_KEY = "REDACTED_API_KEY"
    
    # 1. 备份原始配置
    backup_path = f"{main_config_path}.backup_before_fix"
    if os.path.exists(main_config_path):
        shutil.copy2(main_config_path, backup_path)
        print(f"📁 备份原始配置: {backup_path}")
    
    # 2. 读取主配置文件
    with open(main_config_path, 'r') as f:
        config = json.load(f)
    
    print(f"📄 当前配置版本: {config.get('meta', {}).get('lastTouchedVersion', 'unknown')}")
    
    # 3. 检查并修正Deepseek profile
    if "auth" not in config:
        config["auth"] = {}
    if "profiles" not in config["auth"]:
        config["auth"]["profiles"] = {}
    
    deepseek_profile = config["auth"]["profiles"].get("deepseek_bryson", {})
    
    print("🔍 当前Deepseek profile状态:")
    print(f"   Provider: {deepseek_profile.get('provider', 'MISSING')}")
    print(f"   Mode: {deepseek_profile.get('mode', 'MISSING')}")
    print(f"   API Key字段: {'✓' if 'apiKey' in deepseek_profile else '✗'} 存在")
    
    # 修正profile
    config["auth"]["profiles"]["deepseek_bryson"] = {
        "provider": "deepseek",
        "type": "apiKey",
        "apiKey": DEEPSEEK_API_KEY
    }
    
    print("✅ Deepseek profile已更新:")
    print(f"   Provider: deepseek")
    print(f"   Type: apiKey")
    print(f"   API Key: {DEEPSEEK_API_KEY[:10]}...")
    
    # 4. 检查xiaofeng agent配置
    xiaofeng_found = False
    for agent in config.get("agents", {}).get("list", []):
        if agent.get("id") == "xiaofeng":
            xiaofeng_found = True
            print(f"🔍 Xiaofeng Agent配置:")
            print(f"   模型: {agent.get('model', 'MISSING')}")
            print(f"   身份: {agent.get('identity', {}).get('name', 'MISSING')}")
            
            # 确保模型是deepseek/deepseek-chat
            if agent.get("model") != "deepseek/deepseek-chat":
                agent["model"] = "deepseek/deepseek-chat"
                print(f"⚠️  修正模型为: deepseek/deepseek-chat")
            break
    
    if not xiaofeng_found:
        print("❌ 未找到xiaofeng agent配置")
    
    # 5. 写入修正后的配置
    with open(main_config_path, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"💾 配置已保存到: {main_config_path}")
    
    # 6. 验证修正
    print("\n🧪 配置文件验证:")
    
    # 读取验证
    with open(main_config_path, 'r') as f:
        new_config = json.load(f)
    
    verified_profile = new_config["auth"]["profiles"].get("deepseek_bryson", {})
    api_key_exists = "apiKey" in verified_profile and len(verified_profile["apiKey"]) > 10
    
    print(f"   API Key存在: {'✅' if api_key_exists else '❌'}")
    print(f"   Provider正确: {'✅' if verified_profile.get('provider') == 'deepseek' else '❌'}")
    
    # 检查模型配置
    xiaofeng_model = None
    for agent in new_config.get("agents", {}).get("list", []):
        if agent.get("id") == "xiaofeng":
            xiaofeng_model = agent.get("model")
            break
    
    print(f"   Xiaofeng模型: {xiaofeng_model or '未找到'}")
    model_correct = xiaofeng_model == "deepseek/deepseek-chat"
    print(f"   模型正确: {'✅' if model_correct else '❌'}")
    
    # 7. 创建回退脚本
    create_restore_script(backup_path, main_config_path)
    
    # 8. 输出下一步建议
    print("\n" + "="*50)
    print("🚀 下一步行动建议:")
    print("1. 重启OpenClaw Gateway使新配置生效")
    print("2. 使用临时测试会话验证Deepseek调用")
    print("3. 检查session_status确认Provider和Key状态")
    print("4. 开始成本跟踪系统优化开发")
    print("\n📋 回退命令:")
    print(f"   cp {backup_path} {main_config_path}")
    print("   或运行: python3 restore_deepseek_fix.py")
    
    return api_key_exists and model_correct

def create_restore_script(backup_path, main_config_path):
    """创建回退脚本"""
    restore_script = """
#!/usr/bin/env python3
# Deepseek配置修复回退脚本

import os
import shutil
import sys

backup_path = "{backup_path}"
main_config_path = "{main_config_path}"

if os.path.exists(backup_path):
    shutil.copy2(backup_path, main_config_path)
    print(f"✅ 配置已回退: {main_config_path}")
    print(f"   从备份恢复: {backup_path}")
else:
    print(f"❌ 备份文件不存在: {backup_path}")
    sys.exit(1)
""".format(backup_path=backup_path, main_config_path=main_config_path)
    
    script_path = "/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/restore_deepseek_fix.py"
    with open(script_path, 'w') as f:
        f.write(restore_script)
    
    os.chmod(script_path, 0o755)
    print(f"🔧 回退脚本已创建: {script_path}")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)