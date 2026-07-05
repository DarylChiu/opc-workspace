
#!/usr/bin/env python3
# Deepseek配置修复回退脚本

import os
import shutil
import sys

backup_path = "/Users/zhaoyuzhao/.openclaw/openclaw.json.backup_before_fix"
main_config_path = "/Users/zhaoyuzhao/.openclaw/openclaw.json"

if os.path.exists(backup_path):
    shutil.copy2(backup_path, main_config_path)
    print(f"✅ 配置已回退: /Users/zhaoyuzhao/.openclaw/openclaw.json")
    print(f"   从备份恢复: /Users/zhaoyuzhao/.openclaw/openclaw.json.backup_before_fix")
else:
    print(f"❌ 备份文件不存在: /Users/zhaoyuzhao/.openclaw/openclaw.json.backup_before_fix")
    sys.exit(1)
