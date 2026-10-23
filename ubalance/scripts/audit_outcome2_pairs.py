#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_outcome2_pairs.py — Outcome2 逐票「PDF / Excel 成对」体检（Balance 验收用）

判定口径（比"文件名含清关资料"更稳）：
  · 成对 = 同一 stem 同时存在 .pdf 与 .xlsx/.xlsm（排除 ToKhai 类 stem）
  · 只有 PDF = 有非 ToKhai 的 pdf，但没有任何非 ToKhai 的 Excel
  · 只有 Excel = 有非 ToKhai 的 Excel，但没有非 ToKhai 的 pdf
  · 空夹 = 一个文件都没有
  · 命名规范性：stem 是否含 清关资料 / 出货资料 / 明细 等关键词（不标准不影响判定，只做提示）

用法: python3 scripts/audit_outcome2_pairs.py <Outcome2 目录> [更多目录...]
"""
import os
import sys
import json
from collections import Counter

XLS = ('.xlsx', '.xlsm', '.xls')


def is_tokhai(stem):
    u = stem.upper()
    return 'TOKHAI' in u or 'QDTQ' in u


def audit(out2):
    res = {'dir': out2, 'tickets': {}, 'summary': Counter()}
    if not os.path.isdir(out2):
        res['error'] = 'not a dir'
        return res
    for t in sorted(os.listdir(out2), key=lambda x: (len(x.split('-')[0]), x)):
        tp = os.path.join(out2, t)
        if not os.path.isdir(tp):
            continue
        files = [f for f in os.listdir(tp) if not f.startswith('.')]
        stems = {}
        for f in files:
            b, e = os.path.splitext(f)
            e = e.lower()
            if e not in ('.pdf',) + XLS:
                continue
            stems.setdefault(b, set()).add(e)
        pairs, pdf_only, xls_only = [], [], []
        for b, exts in stems.items():
            if is_tokhai(b):
                continue
            has_pdf = '.pdf' in exts
            has_xls = any(x in exts for x in XLS)
            if has_pdf and has_xls:
                pairs.append(b)
            elif has_pdf:
                pdf_only.append(b)
            elif has_xls:
                xls_only.append(b)
        if not files:
            kind = '空夹(源盘无目录)'
        elif pairs:
            kind = '成对'
        elif xls_only:
            kind = '只有Excel'
        elif pdf_only:
            kind = '只有PDF'
        else:
            kind = '其他(仅提单/ToKhai等)'
        odd_naming = [b for b in (pairs + pdf_only + xls_only)
                      if not any(k in b for k in ('清关资料', '出货资料', '明细', '清关'))]
        res['tickets'][t] = {
            'kind': kind, 'files': len(files),
            'pairs': len(pairs), 'pdf_only': pdf_only, 'xls_only': xls_only,
            'odd_naming': odd_naming,
        }
        res['summary'][kind] += 1
    return res


if __name__ == '__main__':
    dirs = sys.argv[1:]
    total = Counter()
    out = {}
    for d in dirs:
        r = audit(d)
        out[d] = r
        print(f"=== {d}")
        print('   ', dict(r['summary']))
        for t, v in r['tickets'].items():
            if v['kind'] in ('只有Excel', '只有PDF', '空夹(源盘无目录)', '其他(仅提单/ToKhai等)'):
                extra = ''
                if v['odd_naming']:
                    extra = ' | 命名不标准: ' + ', '.join(v['odd_naming'][:2])
                print(f"    {v['kind']:<18} {t}{extra}")
        total.update(r['summary'])
    if len(dirs) > 1:
        print('\n=== 合计 ===', dict(total))
    if os.environ.get('AUDIT_JSON'):
        json.dump(out, open(os.environ['AUDIT_JSON'], 'w'), ensure_ascii=False, indent=1)
