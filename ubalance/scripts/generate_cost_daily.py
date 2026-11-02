#!/usr/bin/env python3
"""
每日成本数据文件生成器
输出到共享路径，供Kitty的node server直接读取
作为sessions_send超时时的兜底方案
"""
import json, os, sys, tempfile
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
    # 看板契约 v2: 把 by_agent × by_date 交叉表一并传出，供 server.js 直接画图
    'by_agent_daily_last30': data.get('by_agent_daily_last30', {}),
    'ledger_coverage': data.get('ledger_coverage', {}),
}

os.makedirs(OUTPUT_DIR, exist_ok=True)
# FIX 2026-11-03: 此文件每 2 小时被 launchd 重写（com.balance.cost-refresh），
# 而看板 server.js 随时可能读 → 非原子写会让它读到半截 JSON 导致解析失败。
# 先写临时文件，再 os.replace() 原子替换。
fd, tmp = tempfile.mkstemp(dir=OUTPUT_DIR, prefix='.cost_daily.', suffix='.tmp')
try:
    with os.fdopen(fd, 'w') as f:
        json.dump(daily_report, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, OUTPUT_FILE)
except Exception:
    try:
        os.unlink(tmp)
    except Exception:
        pass
    raise

print(f"✅ 兜底数据已写入: {OUTPUT_FILE}")
print(json.dumps(daily_report['summary'], indent=2))
