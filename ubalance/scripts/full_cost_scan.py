#!/usr/bin/env python3
"""
OPC 成本统计 v2 — append-only 台账模式 (Balance 财务口径)

核心原则 (Daryl 2026-07-14 指令):
  「历史成本就是历史成本，不会因为解决了某个问题就消失；沉没成本也是成本。」

因此本脚本不再"只扫活着的 agent 目录"。它:
  1. 全量遍历 ~/.openclaw 下所有 *.jsonl (含 .trash / backups / 归档),不漏任何已发生的支出;
  2. 按 responseId 去重 —— 同一次 API 调用在 live/backup/trash 里有多份拷贝也只计一次,杜绝重复计数;
  3. 维护 append-only 台账 (data/cost_ledger.jsonl):一旦某次调用被记账,永久保留;
     即使原 session 文件后来被轮转/删除/移入 .trash,成本仍留在账上,累计只增不减。

去重键: message.responseId (回退 record.id)。
成本源: message.usage.cost.total (真实 provider 回写值,无估算/无 mock)。
"""
import json, os, sys, glob
from datetime import datetime, date
from collections import defaultdict

HOME = os.path.expanduser('~')
OPENCLAW_ROOT = os.path.join(HOME, '.openclaw')
LEDGER_PATH = os.path.join(OPENCLAW_ROOT, 'workspace-balance', 'data', 'cost_ledger.jsonl')

# Agent ID -> 显示名映射
AGENT_MAP = {
    'balance': 'Balance ⚖️', 'main': 'Kitty 😿', 'xiaofeng': 'Bryson 🌬️',
    'self': 'Self 📚', 'bryson': 'Bryson 🌬️', 'kitty': 'Kitty 😿',
    'default': 'Default', 'system-notifier': 'System', 'openclaw-cron': 'Cron',
    'claude': 'Claude', 'claude-opus-4-6': 'Claude Opus',
    'anthropic-claude-opus-4-6': 'Claude Opus',
}
ARCHIVED = 'Archived 🗄️'  # 无法从路径归属到具体 agent 的历史/僵尸 session

today = date.today()
month_start = today.replace(day=1)


def parse_ts(ts):
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000).date()
    try:
        return datetime.fromisoformat(str(ts).replace('Z', '+00:00')).date()
    except Exception:
        return None


def infer_agent(path):
    """从文件路径推断 agent；归档/垃圾桶里无法归属的记为 Archived。"""
    parts = path.replace(OPENCLAW_ROOT + os.sep, '').split(os.sep)
    for i, p in enumerate(parts):
        if p == 'agents' and i + 1 < len(parts):
            return AGENT_MAP.get(parts[i + 1], parts[i + 1])
    if 'workspace-balance' in parts: return AGENT_MAP['balance']
    if 'workspace-self' in parts:    return AGENT_MAP['self']
    if 'workspace-main' in parts:    return AGENT_MAP['main']
    if 'xiaofeng_workspace' in parts: return AGENT_MAP['xiaofeng']
    return ARCHIVED


def load_ledger():
    """读入既有台账 -> {responseId: entry}。台账是唯一真值来源。"""
    led = {}
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH, errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                rid = e.get('id')
                if rid:
                    led[rid] = e
    return led


# FIX 2026-07-14 (Kitty): 排除 backups / .trash / 历史快照目录。
# 病根: 旧代码全量 walk OPENCLAW_ROOT 把 backups/.trash 里的历史副本也扫了,
# 而无 responseId 的记录回退用 record.id (副本与 live 不同) → 去重失败 →
# 同一次调用被重复计 N 次, 凭空多出 ~$215 挂在 Archived 名下, 总额虚高到 $281。
# 修复: 只扫存活的 ~/.openclaw/agents/*/sessions 与各 workspace, 跳过备份/垃圾桁。
EXCLUDE_DIR_MARKERS = ('backups', '.trash', 'backup', '.git')


def scan_all():
    """遍历存活 *.jsonl (排除 backups/.trash)，产出 {responseId: entry}。"""
    found = {}
    files = 0
    for root, dirs, fs in os.walk(OPENCLAW_ROOT):
        # 就地剪枝: 不进入备份/垃圾桁目录, 避免历史副本重复计数
        dirs[:] = [d for d in dirs if not any(mk in d for mk in EXCLUDE_DIR_MARKERS)]
        if any(mk in root for mk in EXCLUDE_DIR_MARKERS):
            continue
        for fn in fs:
            if not fn.endswith('.jsonl') or 'trajectory' in fn:
                continue
            fp = os.path.join(root, fn)
            files += 1
            agent = infer_agent(fp)
            try:
                fh = open(fp, errors='replace')
            except Exception:
                continue
            with fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if not isinstance(r, dict) or r.get('type') != 'message':
                        continue
                    m = r.get('message')
                    if not isinstance(m, dict) or m.get('role') != 'assistant':
                        continue
                    u = m.get('usage') or {}
                    cost = (u.get('cost') or {}).get('total', 0) if isinstance(u, dict) else 0
                    if not cost or cost <= 0:
                        continue
                    rid = m.get('responseId') or r.get('id')
                    if not rid:
                        continue
                    if rid in found:
                        # 同一调用的重复拷贝：保留可归属的 agent（非 Archived 优先）
                        if found[rid]['agent'] == ARCHIVED and agent != ARCHIVED:
                            found[rid]['agent'] = agent
                        continue
                    model = m.get('model', 'unknown')
                    prov = m.get('provider', '')
                    found[rid] = {
                        'id': rid,
                        'cost': cost,
                        'tokens': u.get('totalTokens', 0),
                        'model': f"{prov}/{model}" if prov else model,
                        'agent': agent,
                        'date': (parse_ts(r.get('timestamp', '')) or '').isoformat()
                                if parse_ts(r.get('timestamp', '')) else '',
                    }
    return found, files


def main():
    ledger = load_ledger()
    scanned, files = scan_all()

    # ===== append-only 合并：台账只增不减 =====
    new_ids = 0
    for rid, e in scanned.items():
        if rid not in ledger:
            ledger[rid] = e
            new_ids += 1
        else:
            # 已在账上：补全更优的 agent 归属，但绝不删除、绝不改成本
            if ledger[rid].get('agent') == ARCHIVED and e['agent'] != ARCHIVED:
                ledger[rid]['agent'] = e['agent']

    # 持久化台账
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, 'w') as f:
        for e in ledger.values():
            f.write(json.dumps(e, ensure_ascii=False) + '\n')

    # ===== 从台账（真值）汇总 =====
    by_agent = defaultdict(lambda: {'cost': 0.0, 'tokens': 0, 'calls': 0,
                                    'today_cost': 0.0, 'month_cost': 0.0})
    by_model = defaultdict(lambda: {'cost': 0.0, 'tokens': 0, 'calls': 0})
    daily = defaultdict(float)
    total_cost = total_tokens = total_calls = 0

    for e in ledger.values():
        c, tk = e['cost'], e.get('tokens', 0)
        total_cost += c; total_tokens += tk; total_calls += 1
        a = by_agent[e['agent']]
        a['cost'] += c; a['tokens'] += tk; a['calls'] += 1
        mm = by_model[e['model']]
        mm['cost'] += c; mm['tokens'] += tk; mm['calls'] += 1
        d = parse_ts(e.get('date')) if e.get('date') else None
        if d:
            daily[d.isoformat()] += c
            if d >= month_start: a['month_cost'] += c
            if d == today:       a['today_cost'] += c

    month_total = sum(v['month_cost'] for v in by_agent.values())
    today_total = sum(v['today_cost'] for v in by_agent.values())
    last7 = sorted(daily.keys())[-7:]
    daily_7 = {d: round(daily.get(d, 0), 4) for d in last7}

    print(f"\n{'='*70}")
    print(f"  📊 OPC 成本统计 v2 (append-only 台账 · 全量去重)")
    print(f"{'='*70}")
    print(f"  扫描文件: {files} 个 .jsonl (已排除 backups/.trash 历史副本)")
    print(f"  台账总调用: {len(ledger):,} (本次新增 {new_ids})")
    print(f"  统计时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"  💰 累计成本(去重真值): ${total_cost:.4f}")
    print(f"  📅 本月累计:           ${month_total:.4f}")
    print(f"  📌 今日:               ${today_total:.4f}")
    print(f"  🔢 Token:              {total_tokens:,}")
    print(f"  📞 API调用:            {total_calls:,}\n")

    print("  ┌─ 按Agent ─────────────────────────────────────────────┐")
    for name, s in sorted(by_agent.items(), key=lambda x: x[1]['cost'], reverse=True):
        print(f"  │ {name:<16} 累计${s['cost']:>9.4f} 本月${s['month_cost']:>8.4f} "
              f"今日${s['today_cost']:>7.4f} {s['calls']:>6}次 │")
    print("  └───────────────────────────────────────────────────────┘\n")

    print("  ┌─ 按模型 ───────────────────────────────────────────────┐")
    for model, s in sorted(by_model.items(), key=lambda x: x[1]['cost'], reverse=True):
        print(f"  │ {model:<42} ${s['cost']:>9.4f} {s['calls']:>6}次 │")
    print("  └───────────────────────────────────────────────────────┘")

    result = {
        'scan_info': {
            'files_scanned': files,
            'ledger_calls': len(ledger),
            'new_calls_this_scan': new_ids,
            'timestamp': datetime.now().isoformat(),
            'method': 'append-only ledger (responseId dedup, full ~/.openclaw walk)',
        },
        'summary': {
            'total_cost': round(total_cost, 4),
            'month_cost': round(month_total, 4),
            'today_cost': round(today_total, 4),
            'total_tokens': total_tokens,
            'total_calls': total_calls,
        },
        'by_agent': {n: {'cost': round(s['cost'], 4), 'month_cost': round(s['month_cost'], 4),
                         'today_cost': round(s['today_cost'], 4), 'tokens': s['tokens'],
                         'calls': s['calls']}
                     for n, s in sorted(by_agent.items(), key=lambda x: x[1]['cost'], reverse=True)},
        'by_model': {m: {'cost': round(s['cost'], 4), 'tokens': s['tokens'], 'calls': s['calls']}
                     for m, s in sorted(by_model.items(), key=lambda x: x[1]['cost'], reverse=True)},
        'daily_last7': daily_7,
    }
    out = sys.argv[1] if len(sys.argv) > 1 else None
    if out:
        os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
        with open(out, 'w') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ JSON报告: {out}")
    sys.exit(0)


if __name__ == '__main__':
    main()
