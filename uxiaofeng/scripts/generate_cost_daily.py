#!/usr/bin/env python3
"""
每日成本数据文件生成器
输出到共享路径，供Kitty的node server直接读取
作为sessions_send超时时的兜底方案
"""
import json, os, sys
from datetime import datetime

HOME = os.path.expanduser('~')
OUTPUT_DIR = os.path.join(HOME, 'WorkBuddy', 'Claw', 'opc-dashboard', 'data')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'cost_daily.json')

# 读取全量扫描结果
scan_result = sys.argv[1] if len(sys.argv) > 1 else '/tmp/cost_daily_report.json'

with open(scan_result, 'r') as f:
    data = json.load(f)

# 转换为dashboard兼容格式
daily_report = {
    'timestamp': datetime.now().isoformat(),
    'source': 'balance-jsonl-full-scan',
    'summary': data['summary'],
    'by_agent': data['by_agent'],
    'by_model': data['by_model'],
    'daily_last7': data.get('daily_last7', {}),
}

os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(OUTPUT_FILE, 'w') as f:
    json.dump(daily_report, f, ensure_ascii=False, indent=2)

print(f"✅ 兜底数据已写入: {OUTPUT_FILE}")
print(json.dumps(daily_report['summary'], indent=2))
