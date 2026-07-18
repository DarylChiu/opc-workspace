#!/usr/bin/env python3
"""
成本扫描对比脚本 — Dashboard vs Balance 口径差异定位
"""
import json, os, sys
from datetime import datetime, date
from collections import defaultdict

HOME = os.path.expanduser('~')
ADJ_FILE = os.path.join(HOME, 'WorkBuddy/Claw/opc-dashboard/data/cost_adjustments.json')

# ============ Balance 口径 ============
def balance_scan():
    """完全模拟 Balance full_cost_scan.py 的扫描逻辑（不含 append-only ledger）"""
    OPENCLAW = os.path.join(HOME, '.openclaw')
    EXCLUDE = ('backups', '.trash', 'backup', '.git')
    
    found = {}  # responseId -> entry
    files = 0
    agent_map_bal = {
        'balance': 'Balance', 'main': 'Kitty', 'xiaofeng': 'Bryson',
        'self': 'Self', 'bryson': 'Bryson', 'kitty': 'Kitty',
    }
    
    for root, dirs, fs in os.walk(OPENCLAW):
        dirs[:] = [d for d in dirs if not any(mk in d for mk in EXCLUDE)]
        if any(mk in root for mk in EXCLUDE):
            continue
        for fn in fs:
            if not fn.endswith('.jsonl') or 'trajectory' in fn:
                continue
            fp = os.path.join(root, fn)
            files += 1
            
            # Infer agent same as Balance
            parts = root.replace(OPENCLAW + os.sep, '').split(os.sep)
            agent = 'Archived'
            for i, p in enumerate(parts):
                if p == 'agents' and i + 1 < len(parts):
                    agent = agent_map_bal.get(parts[i+1], parts[i+1])
                    break
            if agent == 'Archived':
                if 'workspace-balance' in parts: agent = 'Balance'
                elif 'workspace-self' in parts: agent = 'Self'
                elif 'workspace-main' in parts: agent = 'Kitty'
                elif 'xiaofeng_workspace' in parts: agent = 'Bryson'
            
            try:
                with open(fp, errors='replace') as fh:
                    for line in fh:
                        line = line.strip()
                        if not line: continue
                        try: r = json.loads(line)
                        except: continue
                        if not isinstance(r, dict) or r.get('type') != 'message': continue
                        m = r.get('message')
                        if not isinstance(m, dict) or m.get('role') != 'assistant': continue
                        u = m.get('usage') or {}
                        cost = (u.get('cost') or {}).get('total', 0) if isinstance(u, dict) else 0
                        if not cost or cost <= 0: continue
                        rid = m.get('responseId') or r.get('id')
                        if not rid: continue
                        
                        ts = r.get('timestamp', '')
                        if isinstance(ts, (int, float)):
                            d = datetime.fromtimestamp(ts / 1000).date()
                        else:
                            try: d = datetime.fromisoformat(str(ts).replace('Z', '+00:00')).date()
                            except: d = None
                        
                        if rid in found:
                            if found[rid]['agent'] == 'Archived' and agent != 'Archived':
                                found[rid]['agent'] = agent
                            continue
                        
                        model = f"{m.get('provider','')}/{m.get('model','unknown')}" if m.get('provider') else m.get('model','unknown')
                        found[rid] = {
                            'id': rid, 'cost': cost, 'tokens': u.get('totalTokens', 0),
                            'model': model, 'agent': agent,
                            'date': d.isoformat() if d else '',
                            'file': fp,
                        }
            except: pass
    
    return found, files

# ============ Dashboard 口径 ============
AGENT_MAP_DS = {
    'main': 'kitty', 'xiaofeng': 'xiaofeng', 'balance': 'balance', 'self': 'self',
    'bryson': 'xiaofeng', 'kitty': 'kitty',
}

def dashboard_scan():
    """完全模拟 Dashboard server.js refreshCostFromJsonl 的扫描逻辑"""
    agents_dir = os.path.join(HOME, '.openclaw', 'agents')
    found = []  # list of entries (no dedup!)
    files = 0
    
    for agent_dir in os.listdir(agents_dir):
        session_dir = os.path.join(agents_dir, agent_dir, 'sessions')
        if not os.path.exists(session_dir):
            continue
        mapped_agent = AGENT_MAP_DS.get(agent_dir, agent_dir)
        
        for fname in os.listdir(session_dir):
            if not fname.endswith('.jsonl') or 'trajectory' in fname:
                continue
            fp = os.path.join(session_dir, fname)
            files += 1
            
            try:
                with open(fp) as fh:
                    for line in fh:
                        line = line.strip()
                        if not line: continue
                        try: r = json.loads(line)
                        except: continue
                        if r.get('type') != 'message': continue
                        m = r.get('message', {})
                        if m.get('role') != 'assistant': continue
                        u = m.get('usage', {})
                        cost = u.get('cost', {}).get('total', 0) if isinstance(u, dict) else 0
                        cost = cost if isinstance(cost, (int, float)) else 0
                        if cost <= 0: continue
                        ts = r.get('timestamp')
                        if not ts: continue
                        
                        if isinstance(ts, (int, float)):
                            d = datetime.fromtimestamp(ts / 1000).date().isoformat()
                        else:
                            d = str(ts)[:10]
                        
                        model = f"{m.get('provider','')}/{m.get('model','unknown')}" if m.get('provider') else m.get('model','unknown')
                        found.append({
                            'id': m.get('responseId', r.get('id', '')),
                            'cost': cost,
                            'tokens': u.get('totalTokens', 0),
                            'model': model,
                            'agent': mapped_agent,
                            'date': d,
                            'file': fp,
                        })
            except: pass
    
    return found, files

# ============ Adjustment 分析 ============
def load_adjustments():
    try:
        with open(ADJ_FILE) as f:
            d = json.load(f)
        return d.get('adjustments', [])
    except:
        return []

# ============ Main ============
print("=" * 80)
print("  成本扫描口径对比：Dashboard vs Balance")
print("=" * 80)

# Balance scan (fresh, no ledger)
bal_found, bal_files = balance_scan()
print(f"\n📊 Balance 口径 (全量 .openclaw walk + responseId 去重):")
print(f"   扫描文件: {bal_files}")
print(f"   唯一调用: {len(bal_found)}")
bal_total = sum(e['cost'] for e in bal_found.values())
print(f"   累计成本: ${bal_total:.2f}")

# Dashboard scan
ds_found, ds_files = dashboard_scan()
print(f"\n📊 Dashboard 口径 (仅 agents/*/sessions/ + 无去重):")
print(f"   扫描文件: {ds_files}")
print(f"   总调用(含重复): {len(ds_found)}")
ds_total = sum(e['cost'] for e in ds_found)
print(f"   累计成本(JSONL部分): ${ds_total:.2f}")

# Adjustments
adjs = load_adjustments()
adj_total = sum(a['amount'] for a in adjs)
print(f"   + 历史成本调整: ${adj_total:.2f}")
print(f"   = Dashboard 最终总成本: ${ds_total + adj_total:.2f}")

# ============ 差异分析 ============
print(f"\n{'='*80}")
print(f"  差异分析")
print(f"{'='*80}")

# 1. 差异1：扫描范围
bal_ids = set(bal_found.keys())
ds_ids = set(e['id'] for e in ds_found if e['id'])

only_in_bal = bal_ids - ds_ids
only_in_ds = ds_ids - bal_ids
both = bal_ids & ds_ids

print(f"\n🔍 响应ID对比:")
print(f"   Balance独有: {len(only_in_bal)}")
print(f"   Dashboard独有: {len(only_in_ds)}")
print(f"   共有: {len(both)}")

only_bal_cost = sum(bal_found[rid]['cost'] for rid in only_in_bal)
only_ds_cost = sum(sum(e['cost'] for e in ds_found if e['id'] == rid) for rid in only_in_ds)
print(f"   Balance独有成本: ${only_bal_cost:.2f}")
print(f"   Dashboard独有成本: ${only_ds_cost:.2f}")

# 2. 差异2：去重
# Dashboard可能有重复计数
dup_count = len(ds_found) - len(ds_ids)
print(f"\n🔍 Dashboard重复计数: {dup_count}次")

# 重复造成的额外成本
from collections import Counter
ds_id_counts = Counter(e['id'] for e in ds_found if e['id'])
dup_ids = {rid for rid, cnt in ds_id_counts.items() if cnt > 1}
dup_extra_cost = sum(
    sum(sorted([e['cost'] for e in ds_found if e['id'] == rid])[1:])
    for rid in dup_ids
)
print(f"   重复的响应ID: {len(dup_ids)}个")
print(f"   重复造成的虚增成本: ${dup_extra_cost:.2f}")

# 3. 差异3：cost_adjustments
print(f"\n🔍 历史成本调整:")
for adj in adjs:
    print(f"   id={adj['id']} agent={adj['agent']} amount=${adj['amount']:.2f} date={adj['date']}")
    print(f"   reason: {adj['reason']}")

# 4. Balance独有来源分析（哪些文件产生了这些cost？）
print(f"\n🔍 Balance独有的成本来源文件（前20）:")
bal_only_files = defaultdict(lambda: {'count': 0, 'cost': 0.0})
for rid in only_in_bal:
    f = bal_found[rid]['file']
    bal_only_files[f]['count'] += 1
    bal_only_files[f]['cost'] += bal_found[rid]['cost']

for fp, info in sorted(bal_only_files.items(), key=lambda x: x[1]['cost'], reverse=True)[:20]:
    print(f"   ${info['cost']:.2f} | {info['count']} calls | {fp}")

# 5. Dashboard独有分析
print(f"\n🔍 Dashboard独有的成本来源文件（前20）:")
ds_only_files = defaultdict(lambda: {'count': 0, 'cost': 0.0})
for e in ds_found:
    if e['id'] in only_in_ds:
        ds_only_files[e['file']]['count'] += 1
        ds_only_files[e['file']]['cost'] += e['cost']

for fp, info in sorted(ds_only_files.items(), key=lambda x: x[1]['cost'], reverse=True)[:20]:
    print(f"   ${info['cost']:.2f} | {info['count']} calls | {fp}")

# ============ 月度对比 ============
print(f"\n{'='*80}")
print(f"  月度对比 (July 2026)")
print(f"{'='*80}")

today = date.today()
month_start = today.replace(day=1)

# Balance 月度
bal_monthly = sum(e['cost'] for rid, e in bal_found.items() 
                  if e.get('date') and e['date'] >= str(month_start))
# Dashboard 月度 (no adj)
ds_monthly = sum(e['cost'] for e in ds_found
                 if e.get('date') and e['date'] >= str(month_start))
# Dashboard 月度含 adj
adj_monthly = sum(a['amount'] for a in adjs 
                  if a.get('date', '') and a['date'] >= str(month_start))

print(f"   Balance 七月合计:  ${bal_monthly:.2f}")
print(f"   Dashboard 七月合计(JSONL): ${ds_monthly:.2f}")
print(f"   Dashboard 七月合计(含调整): ${ds_monthly + adj_monthly:.2f}")

# By agent comparison
print(f"\n🔍 按Agent对比:")
print(f"   {'Agent':<16} {'Balance':>10} {'Dashboard':>10} {'Diff':>10}")
print(f"   {'-'*16} {'-'*10} {'-'*10} {'-'*10}")

bal_by_agent = defaultdict(float)
for rid, e in bal_found.items():
    if e.get('date') and e['date'] >= str(month_start):
        bal_by_agent[e['agent']] += e['cost']

ds_by_agent = defaultdict(float)
for e in ds_found:
    if e.get('date') and e['date'] >= str(month_start):
        ds_by_agent[e['agent']] += e['cost']

# Map Balance agent names to Dashboard names
AGENT_NAME_MAP = {
    'Kitty': 'kitty', 'Bryson': 'xiaofeng', 'Balance': 'balance', 'Self': 'self',
    'Archived': 'archived',
}

all_agents = sorted(set(list(bal_by_agent.keys()) + list(ds_by_agent.keys())))
for agent in all_agents:
    bal_val = bal_by_agent.get(agent, 0)
    ds_agent = AGENT_NAME_MAP.get(agent, agent)
    ds_val = ds_by_agent.get(ds_agent, 0) + (adj_monthly if ds_agent == 'kitty' and agent == 'Kitty' else 0)
    diff = ds_val - bal_val
    flag = ' ⚠️' if abs(diff) > 0.50 else ''
    print(f"   {agent:<16} ${bal_val:>9.2f} ${ds_val:>9.2f} ${diff:>+9.2f}{flag}")

# ============ 结论 ============
print(f"\n{'='*80}")
print(f"  根因分析结论")
print(f"{'='*80}")
print(f"""
差异来源 (按影响力排序):
1. 成本调整台账 (cost_adjustments.json): Dashboard +${adj_total:.2f}, Balance $0
   → 调节项，Balance缺少Sentinel事故($20)的外部账单登记
2. 扫描范围差异: Balance扫描 {bal_files - ds_files} 个额外文件(workspace等)
   Balance独有成本: ${only_bal_cost:.2f}, Dashboard独有: ${only_ds_cost:.2f}
3. 去重差异: Dashboard未去重，{len(dup_ids)}个responseId被重复计费
   虚增成本: ${dup_extra_cost:.2f}

净差异: Dashboard ${ds_total + adj_total:.2f} - Balance ${bal_total:.2f} = ${ds_total + adj_total - bal_total:.2f}
""")
