#!/usr/bin/env python3
# Bryson配置回退脚本
import json
import os
import sys

def restore_backup():
    """恢复备份配置"""
    backup_files = [f for f in os.listdir(".") if f.startswith("openclaw.json.backup")]
    if not backup_files:
        print("❌ 未找到备份文件")
        return False
    
    latest_backup = sorted(backup_files)[-1]
    print(f"📁 恢复备份: {latest_backup}")
    
    try:
        with open(latest_backup, "r") as f:
            backup_data = json.load(f)
        
        with open("openclaw.json", "w") as f:
            json.dump(backup_data, f, indent=2)
        
        print("✅ 配置已恢复")
        
        # 验证恢复
        with open("openclaw.json", "r") as f:
            restored = json.load(f)
        
        # 检查xiao-feng模型
        agents = restored.get("agents", {}).get("list", [])
        for agent in agents:
            if agent.get("id") == "xiaofeng":
                model = agent.get("model", "")
                print(f"   Xiaofeng Agent模型: {model}")
                if "openrouter" in model:
                    print("   ✅ 已恢复OpenRouter配置")
                else:
                    print("   ⚠️  模型配置可能有误")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Bryson独立Provider配置回退")
    restore_backup()
