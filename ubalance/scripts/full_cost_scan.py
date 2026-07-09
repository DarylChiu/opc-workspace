#!/usr/bin/env python3
"""
.jsonl 全量解析 - OPC 成本统计
扫描所有Agent的sessions/*.jsonl，解析assistant消息中的usage.cost
输出完整成本统计表
"""
import json, os, sys, glob
from datetime import datetime, date
from collections import defaultdict

HOME = os.path.expanduser('~')
AGENTS_DIR = os.path.join(HOME, '.openclaw', 'agents')

# Agent ID -> 显示名映射
AGENT_MAP = {
    'balance': 'Balance ⚖️',
    'main': 'Kitty 😿',
    'xiaofeng': 'Bryson 🌬️',
    'self': 'Self 📚',
    'bryson': 'Bryson 🌬️',
    'kitty': 'Kitty 😿',
    'default': 'Default',
    'system-notifier': 'System',
    'openclaw-cron': 'Cron',
    'claude': 'Claude',
    'claude-opus-4-6': 'Claude Opus',
    'anthropic-claude-opus-4-6': 'Claude Opus',
}

today = date.today()
month_start = today.replace(day=1)

# 统计结构
by_agent = defaultdict(lambda: {'cost': 0.0, 'tokens': 0, 'calls': 0, 'today_cost': 0.0, 'month_cost': 0.0})
by_model = defaultdict(lambda: {'cost': 0.0, 'tokens': 0, 'calls': 0})
daily = defaultdict(float)  # date -> cost
total_cost = 0.0
total_tokens = 0
total_calls = 0
errors = 0

def parse_timestamp(ts):
    """解析ISO时间戳，返回date对象"""
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000).date()
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00')).date()
    except:
        return None

# 全量扫描
agent_dirs = [d for d in os.listdir(AGENTS_DIR) 
              if os.path.isdir(os.path.join(AGENTS_DIR, d))]
print(f"🔍 扫描 {len(agent_dirs)} 个Agent目录...")

files_scanned = 0
for agent_id in sorted(agent_dirs):
    session_dir = os.path.join(AGENTS_DIR, agent_id, 'sessions')
    if not os.path.exists(session_dir):
        continue
    
    agent_name = AGENT_MAP.get(agent_id, agent_id)
    
    for jsonl_path in glob.glob(os.path.join(session_dir, '*.jsonl')):
        if 'trajectory' in jsonl_path:
            continue
        files_scanned += 1
        
        try:
            with open(jsonl_path, 'r', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        errors += 1
                        continue
                    
                    if record.get('type') != 'message':
                        continue
                    
                    msg = record.get('message', {})
                    if msg.get('role') != 'assistant':
                        continue
                    
                    usage = msg.get('usage', {})
                    cost_info = usage.get('cost', {})
                    msg_cost = cost_info.get('total', 0)
                    
                    if msg_cost <= 0:
                        continue
                    
                    msg_tokens = usage.get('totalTokens', 0)
                    model = msg.get('model', 'unknown')
                    provider = msg.get('provider', '')
                    full_model = f"{provider}/{model}" if provider else model
                    
                    ts = record.get('timestamp', '')
                    msg_date = parse_timestamp(ts)
                    
                    # 累计
                    total_cost += msg_cost
                    total_tokens += msg_tokens
                    total_calls += 1
                    
                    by_agent[agent_name]['cost'] += msg_cost
                    by_agent[agent_name]['tokens'] += msg_tokens
                    by_agent[agent_name]['calls'] += 1
                    
                    by_model[full_model]['cost'] += msg_cost
                    by_model[full_model]['tokens'] += msg_tokens
                    by_model[full_model]['calls'] += 1
                    
                    if msg_date:
                        daily[msg_date.isoformat()] += msg_cost
                        if msg_date >= month_start:
                            by_agent[agent_name]['month_cost'] += msg_cost
                        if msg_date == today:
                            by_agent[agent_name]['today_cost'] += msg_cost
                        
        except Exception as e:
            errors += 1
            continue

# ============ 统计汇总 ============
month_total = sum(v['month_cost'] for v in by_agent.values())
today_total = sum(v['today_cost'] for v in by_agent.values())

# 计算最近7天每日成本
last7 = sorted(daily.keys())[-7:]
daily_7 = {d: round(daily.get(d, 0), 4) for d in last7}

print(f"\n{'='*70}")
print(f"  📊 OPC 全量成本统计 (基于 .jsonl 全量解析)")
print(f"{'='*70}")
print(f"  扫描文件: {files_scanned} 个 .jsonl")
print(f"  解析错误: {errors} 条")
print(f"  统计时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 总览
print(f"  💰 全量累计成本:    ${total_cost:.4f}")
print(f"  📅 本月累计:        ${month_total:.4f}")
print(f"  📌 今日:            ${today_total:.4f}")
print(f"  🔢 全量Token:       {total_tokens:,}")
print(f"  📞 全量API调用:     {total_calls:,}")
print()

# 按Agent
print(f"  ┌─ 按Agent ─────────────────────────────────────────────┐")
print(f"  │ {'Agent':<18} {'全量成本':>10} {'本月':>10} {'今日':>10} {'Tokens':>12} {'调用':>8} │")
for name, stats in sorted(by_agent.items(), key=lambda x: x[1]['cost'], reverse=True):
    print(f"  │ {name:<18} ${stats['cost']:>9.4f} ${stats['month_cost']:>9.4f} ${stats['today_cost']:>9.4f} {stats['tokens']:>12,} {stats['calls']:>8} │")
print(f"  └──────────────────────────────────────────────────────┘")
print()

# 按模型
print(f"  ┌─ 按模型 ───────────────────────────────────────────────┐")
print(f"  │ {'Model':<40} {'全量成本':>10} {'Tokens':>12} {'调用':>8} │")
for model, stats in sorted(by_model.items(), key=lambda x: x[1]['cost'], reverse=True):
    print(f"  │ {model:<40} ${stats['cost']:>9.4f} {stats['tokens']:>12,} {stats['calls']:>8} │")
print(f"  └──────────────────────────────────────────────────────┘")
print()

# 最近7天趋势
if daily_7:
    print(f"  📈 最近7天每日成本:")
    for d, c in sorted(daily_7.items()):
        bar = '█' * max(1, int(c * 200)) if c > 0 else ''
        print(f"     {d}: ${c:>8.4f} {bar}")

# ============ 输出 JSON ============
output_json = sys.argv[1] if len(sys.argv) > 1 else None
result = {
    'scan_info': {
        'files_scanned': files_scanned,
        'parse_errors': errors,
        'timestamp': datetime.now().isoformat(),
        'method': '.jsonl full-scan'
    },
    'summary': {
        'total_cost': round(total_cost, 4),
        'month_cost': round(month_total, 4),
        'today_cost': round(today_total, 4),
        'total_tokens': total_tokens,
        'total_calls': total_calls
    },
    'by_agent': {name: {
        'cost': round(s['cost'], 4),
        'month_cost': round(s['month_cost'], 4),
        'today_cost': round(s['today_cost'], 4),
        'tokens': s['tokens'],
        'calls': s['calls']
    } for name, s in sorted(by_agent.items(), key=lambda x: x[1]['cost'], reverse=True)},
    'by_model': {m: {
        'cost': round(s['cost'], 4),
        'tokens': s['tokens'],
        'calls': s['calls']
    } for m, s in sorted(by_model.items(), key=lambda x: x[1]['cost'], reverse=True)},
    'daily_last7': daily_7
}

if output_json:
    os.makedirs(os.path.dirname(output_json) or '.', exist_ok=True)
    with open(output_json, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ JSON报告已输出: {output_json}")

# 返回码
sys.exit(0)
