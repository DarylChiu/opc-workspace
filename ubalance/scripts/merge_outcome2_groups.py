#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge_outcome2_groups.py — 合并分组跑批产出（Outcome1 / Outcome2）+ 出待补清单

用法：
  python3 scripts/merge_outcome2_groups.py --out work/loan-materials-2026-10/merged [--ts 20261023]
逻辑：
  1. 按 G01..G10 顺序扫描各 STAGE（work/loan-materials-2025-12/out/v2.8d-2025_12-Gxx-*）
  2. Outcome2 文件夹按「组内序号」重编为全局序号 1..N，拷入合并目录
  3. Outcome1 合并为单表（13 列不变，序号全局重编），另加「分组对照」+「待补清单」两个 sheet
  4. 不改任何源产出，只读+复制
"""
import argparse
import glob
import os
import re
import shutil
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_outcome2_from_report import parse_report, judge  # noqa

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

WS = '/Users/zhaoyuzhao/.openclaw/workspace-balance'
OUTROOT = os.path.join(WS, 'work/loan-materials-2025-12/out')
GROUP_RE = re.compile(r'v2\.8d-2025_12-(G\d{2})-(\d{8}_\d{4})$')


def find_stages():
    found = {}
    for d in glob.glob(os.path.join(OUTROOT, 'v2.8d-2025_12-G*-*')):
        m = GROUP_RE.search(os.path.basename(d))
        if m and os.path.isdir(d):
            g = m.group(1)
            if g not in found or m.group(2) > found[g][0]:
                found[g] = (m.group(2), d)
    return {g: v[1] for g, v in sorted(found.items())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--ts', default='20261023')
    a = ap.parse_args()
    stages = find_stages()
    print('发现分组:', {g: os.path.basename(d) for g, d in stages.items()})
    merged = a.out
    out2 = os.path.join(merged, 'Outcome2')
    for p in (merged,):
        shutil.rmtree(p, ignore_errors=True)
    os.makedirs(out2, exist_ok=True)

    rows13, mapping, pending, gaps = [], [], [], []
    gidx = 0
    for g, stage in stages.items():
        o2 = os.path.join(stage, 'Outcome2')
        rep = [f for f in glob.glob(os.path.join(stage, '处理报告-*.txt'))]
        tk = parse_report(rep[0]) if rep else {}
        xls = [f for f in glob.glob(os.path.join(stage, 'Outcome1-*.xlsx'))]
        # 组内 Outcome1 行（跳过表头）
        local = []
        if xls:
            wb = openpyxl.load_workbook(xls[0], data_only=True)
            wsx = wb.active
            hdr = [c.value for c in wsx[1]]
            for r in wsx.iter_rows(min_row=2, values_only=True):
                if r[0] is None:
                    continue
                local.append((int(r[0]), r))
            wb.close()
        else:
            hdr = []
        dirs = sorted([d for d in os.listdir(o2) if os.path.isdir(os.path.join(o2, d))],
                      key=lambda x: int(x.split('-', 1)[0]))
        for d in dirs:
            lidx = int(d.split('-', 1)[0])
            ticket = d.split('-', 1)[1]
            gidx += 1
            newd = f'{gidx}-{ticket}'
            shutil.copytree(os.path.join(o2, d), os.path.join(out2, newd), symlinks=False)
            mapping.append({'全局序号': gidx, '组别': g, '组内序号': lidx, '票号': ticket,
                            '文件数': len(os.listdir(os.path.join(out2, newd)))})
            files = tk.get(ticket, [])
            kind = judge(files) if files or ticket in tk else ('空夹(源盘无目录)' if not os.listdir(os.path.join(out2, newd)) else '未在处理报告中')
            if kind != '成对':
                pending.append({'全局序号': gidx, '组别': g, '票号': ticket, '结论': kind,
                                '现有文件': ' | '.join([f['name'] for f in files][:3])})
            tags = set()
            for f in files:
                tags |= set(f['tags'])
            for need, tag in (('ToKhai', 'TOKHAI_QDTQ'), ('BL/AWB', None)):
                if need == 'ToKhai':
                    if 'TOKHAI_QDTQ' not in tags:
                        gaps.append({'全局序号': gidx, '票号': ticket, '缺项': 'ToKhai'})
                else:
                    if not (tags & {'BL', 'SWB', 'AWB'}):
                        gaps.append({'全局序号': gidx, '票号': ticket, '缺项': 'BL/AWB'})
        for lidx, r in local:
            rows13.append(list(r[:13]) + [g])

    # ---- 写合并 Outcome1 ----
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Outcome1'
    cols = ['序号', '发票号', '关单号', '报关日期', '金额(USD)', '日期', '供应商',
            '贷款用途分类', '分类依据', '置信度', '五类材料完整性', 'ToKhai勾稽', '备注']
    ws.append(cols)
    for c in range(1, len(cols) + 1):
        ws.cell(1, c).font = Font(bold=True)
        ws.cell(1, c).fill = PatternFill('solid', fgColor='DDEBF7')
        ws.cell(1, c).alignment = Alignment(horizontal='center', wrap_text=True)
    rows13.sort(key=lambda r: r[0])
    for i, r in enumerate(rows13, 1):
        vals = list(r[:13])
        vals[0] = i
        ws.append(vals)
    for i, w in enumerate([6, 22, 16, 12, 12, 14, 22, 16, 30, 8, 20, 14, 52], 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    ws2 = wb.create_sheet('分组对照')
    ws2.append(['全局序号', '组别', '组内序号', '票号', '文件数'])
    for m in mapping:
        ws2.append([m['全局序号'], m['组别'], m['组内序号'], m['票号'], m['文件数']])

    ws3 = wb.create_sheet('待补清单')
    ws3.append(['全局序号', '组别', '票号', '结论', '现有文件'])
    for p in pending:
        ws3.append([p['全局序号'], p['组别'], p['票号'], p['结论'], p['现有文件']])
    ws4 = wb.create_sheet('完整性缺口')
    ws4.append(['全局序号', '票号', '缺项'])
    for g2 in gaps:
        ws4.append([g2['全局序号'], g2['票号'], g2['缺项']])
    for s in (ws2, ws3, ws4):
        for c in range(1, s.max_column + 1):
            s.cell(1, c).font = Font(bold=True)

    xlsx = os.path.join(merged, f'Outcome1-ALL-{len(rows13)}票-{a.ts}.xlsx')
    wb.save(xlsx)
    print(f'Outcome1 合并: {xlsx}（{len(rows13)} 行）')
    print(f'Outcome2 合并: {out2}（{gidx} 个票夹）')
    print(f'待补清单: {len(pending)} 条｜完整性缺口: {len(gaps)} 条')
    stats = defaultdict(int)
    for p in pending:
        stats[p['结论']] += 1
    print('待补分布:', dict(stats))


if __name__ == '__main__':
    main()
