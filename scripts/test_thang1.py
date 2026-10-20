#!/usr/bin/env python3
"""
test_thang1.py — 在 THÁNG 1-2023 全月验证 ToKhai 抽取 + 方案B金额勾稽
不写任何输出，只打印验证报告。
"""
import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
from tokhai_extract import extract_tokhai, is_tokhai_filename
import openpyxl

DISK = '/Volumes/TOSHIBA EXT/HUATEX贷款材料'
L1 = os.path.join(DISK, 'L1-Raw Materials-Year2023.xlsx')
MONTH = os.path.join(DISK, 'RM-Database/2023', 'THÁNG 1-2023')

# ---- 读 L1: 发票号 -> (金额, 关单号, 日期) ----
wb = openpyxl.load_workbook(L1, data_only=True)
ws = wb.active
l1 = {}   # inv_no -> dict
for row in ws.iter_rows(min_row=4, values_only=True):
    if not row or len(row) < 7:
        continue
    inv = str(row[2]).strip() if row[2] else ''
    if not inv or inv == 'None':
        continue
    try:
        amt = float(row[5]) if row[5] is not None else None
    except (ValueError, TypeError):
        amt = None
    l1[inv] = {'amount': amt, 'so': str(row[3]).strip() if row[3] else '',
               'date': row[4]}
print(f'L1 发票数: {len(l1)}')

# ---- 遍历 THÁNG 1 各发票目录 ----
def dir_invoice(dirname):
    # 去掉 '数字. ' 前缀，取第一个 token 作为发票号候选
    core = re.sub(r'^\s*\d+\.\s*', '', dirname).strip()
    return core.split()[0] if core.split() else core

TOL = 0.001  # 金额完全相等（容忍浮点误差）
dirs = sorted([d for d in os.listdir(MONTH) if os.path.isdir(os.path.join(MONTH, d))])
print(f'THÁNG 1 目录数: {len(dirs)}\n')
print('='*100)

matched, multi_cleared, no_cleared, amt_ok, amt_mismatch = 0, 0, 0, 0, 0
for d in dirs:
    dp = os.path.join(MONTH, d)
    inv_no = dir_invoice(d)
    l1e = l1.get(inv_no)
    # 收集所有疑似 ToKhai 文件 → 读内容
    cands = [f for f in os.listdir(dp) if is_tokhai_filename(f)]
    cleared = []
    for f in cands:
        r = extract_tokhai(os.path.join(dp, f))
        if r['is_cleared']:
            cleared.append(r)
    # 方案B: 金额勾稽
    l1amt = l1e['amount'] if l1e else None
    picked = None
    note = ''
    if len(cleared) == 0:
        no_cleared += 1
        note = '⚠️无已通关报关单'
    elif len(cleared) == 1:
        picked = cleared[0]
    else:
        # 多张通关 → 金额勾稽
        exact = [c for c in cleared if c['amount'] is not None and l1amt is not None
                 and abs(c['amount'] - l1amt) < TOL]
        if len(exact) == 1:
            picked = exact[0]
            note = f'多通关{len(cleared)}→金额勾稽选中1'
        elif len(exact) > 1:
            multi_cleared += 1
            note = f'⚠️分批报关?{len(exact)}张金额均符'
            picked = exact[0]
        else:
            multi_cleared += 1
            note = f'⚠️多通关{len(cleared)}张金额均不符L1({l1amt})'

    if picked:
        matched += 1
        ok = (l1amt is not None and picked['amount'] is not None
              and abs(picked['amount'] - l1amt) < TOL)
        if ok: amt_ok += 1
        else: amt_mismatch += 1
        flag = '✅' if ok else '❌金额不符'
        print(f'{d[:42]:44} inv={inv_no:16} 关单={picked["so_to_khai"]:13} '
              f'日期={picked["ngay_ymd"]:10} 单额={picked["amount"]} L1={l1amt} {flag} {note}')
    else:
        print(f'{d[:42]:44} inv={inv_no:16} {note} (候选ToKhai={len(cands)}, 通关={len(cleared)})')

print('='*100)
print(f'目录总数        : {len(dirs)}')
print(f'成功匹配通关单  : {matched}')
print(f'  金额勾稽一致  : {amt_ok}')
print(f'  金额不符      : {amt_mismatch}')
print(f'无已通关报关单  : {no_cleared}')
print(f'多通关待核查    : {multi_cleared}')
