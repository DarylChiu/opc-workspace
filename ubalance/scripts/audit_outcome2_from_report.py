#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_outcome2_from_report.py — 用「处理报告」的逐票明细做 Outcome2 配对体检（零 OCR）

原理：处理报告里有 `----- 逐票明细 -----` 段，逐票列出
      `['INVOICE', 'PACKING_LIST'...] | attr | [子目录] 文件名`
    这里直接读标签，判定每票是否拿到
      · PDF 版的三件套（INVOICE / SALES_CONTRACT / PACKING_LIST 任一）
      · Excel 版的三件套（同一组标签，扩展名 xlsx/xlsm/xls）
    比起「只看文件名含清关资料」或「同 stem 配对」更准，因为按内容标签算。

用法: python3 scripts/audit_outcome2_from_report.py <处理报告.txt> [...] [--json out.json]
"""
import os
import re
import sys
import json
from collections import Counter

TRIPLE = {'INVOICE', 'SALES_CONTRACT', 'PACKING_LIST'}
XLS = ('.xlsx', '.xlsm', '.xls')
LINE = re.compile(r"^\s+(\[[^\]]*\]) \| (.+?) \| \[.*?\] (.+)$")


def parse_report(path):
    text = open(path, encoding='utf-8', errors='replace').read()
    if '===== 逐票明细 =====' not in text:
        return {}
    seg = text.split('===== 逐票明细 =====', 1)[1]
    seg = seg.split('===== 剔除清单 =====', 1)[0]
    tickets, cur = {}, None
    for line in seg.splitlines():
        m = re.match(r'^\s*\[(\d+)\]\s+(\S.*)$', line)
        if m:
            cur = m.group(2).strip()
            tickets[cur] = []
            continue
        if cur is None:
            continue
        if '未收材料' in line:
            continue
        mm = LINE.match(line)
        if mm:
            tags = [t.strip().strip("'") for t in mm.group(1).strip('[]').split(',') if t.strip()]
            tickets[cur].append({'tags': tags, 'name': mm.group(3).strip()})
    return tickets


def judge(files):
    tset = set()
    for f in files:
        tset |= set(f['tags'])
    has_triple_tags = bool(tset & TRIPLE)
    pdf = any(set(f['tags']) & TRIPLE and f['name'].lower().endswith('.pdf') for f in files)
    xls = any(set(f['tags']) & TRIPLE and f['name'].lower().endswith(XLS) for f in files)
    if not files:
        return '空夹(源盘无目录)'
    if pdf and xls:
        return '成对'
    if pdf:
        return '只有PDF'
    if xls:
        return '只有Excel'
    return '其他(无三件套)'


def main(argv):
    js = None
    if '--json' in argv:
        i = argv.index('--json')
        js = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    total = Counter()
    out = {}
    for p in argv:
        tk = parse_report(p)
        summ = Counter()
        det = {}
        for t, files in tk.items():
            k = judge(files)
            summ[k] += 1
            if k != '成对':
                det[t] = {'kind': k, 'files': [f['name'] for f in files][:4]}
        out[p] = {'summary': dict(summ), 'nonpair': det, 'tickets': len(tk)}
        print(f'=== {os.path.basename(os.path.dirname(p))} ({len(tk)} 票): {dict(summ)}')
        for t, v in det.items():
            print(f'    {v["kind"]:<16} {t}  {" | ".join(v["files"])[:100]}')
        total.update(summ)
    if len(argv) > 1:
        print('\n=== 合计 ===', dict(total))
    if js:
        json.dump(out, open(js, 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
