#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""payment_recon_finalize.py — Payment 核销表收尾（可复用于后续批次）

做两件事，幂等（可重复跑）：
1. 「凭证摘要」列若为**公式** → 就地转成**静态文本**
   （原因：openpyxl 写公式不带缓存值，飞书/WPS 云预览显示空白；MISA 需要可直接复制的文本）
   格式：在{K账号}账号于{L月D日}放款OA流程号{R}的{O越南文名}发票号{F}金额{H}vnd
2. --drop 指定列（表头名或列字母）→ **整列删除并向左平移**（列宽同步跟随）

用法:
  python3 scripts/payment_recon_finalize.py \
      --xlsx work/.../Payment核销测试0904-3.xlsx \
      --out  work/.../Payment核销测试0904-5.xlsx \
      --drop 款项类别
"""
import os
import re
import argparse
import datetime
from copy import copy

# 摘要里各字段的列名候选（按优先级匹配）
FIELDS = {
    'acct':   ['BÚT TOÁN', 'BÚT TOAN'],
    'date':   ['payment date'],
    'oa':     ['请款单号'],
    'vendor': ['Tiếng việt', 'Tieng viet'],
    'inv':    ['Chứng từ giải ngân'],
    'amt':    ['Số tiền trên hóa đơn/ Hợp đồng (USD)', 'Số tiền trên hóa đơn/Hợp đồng (USD)',
               'Số tiền trên hóa đơn/ Hợp đồng (VND)', 'Số tiền trên hóa đơn/Hợp đồng (VND)'],
}
FALLBACK = {'acct': '{放款账号}', 'date': '{放款日期}', 'oa': '{OA流程号}'}


def _date_txt(v):
    if isinstance(v, (datetime.datetime, datetime.date)):
        return f'{v.month}月{v.day}日'
    s = str(v or '').strip()
    m = re.match(r'^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', s)
    return f'{int(m.group(2))}月{int(m.group(3))}日' if m else s


def _num(v):
    if v is None or v == '':
        return ''
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return re.sub(r'[^0-9]', '', str(v))


def col_letter(n):
    s = ''
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xlsx', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--summary-col', default='凭证摘要')
    ap.add_argument('--drop', action='append', default=[])
    a = ap.parse_args()

    import openpyxl
    from openpyxl.utils import column_index_from_string
    from openpyxl.styles import Alignment

    wb = openpyxl.load_workbook(a.xlsx)
    ws = wb[wb.sheetnames[0]]

    # 定位表头行（含 'STT' 或 'Tên khách hàng' 的那一行）
    hdr = 2
    for r in range(1, min(ws.max_row, 8) + 1):
        vals = [str(ws.cell(r, c).value or '').strip() for c in range(1, ws.max_column + 1)]
        if 'STT' in vals or any('Tên khách hàng' in v for v in vals):
            hdr = r
            break

    def find_col(name):
        for c in range(1, ws.max_column + 1):
            v = ws.cell(hdr, c).value
            if v and str(v).strip() == name.strip():
                return c
        return None

    def find_field(key):
        for cand in FIELDS[key]:
            c = find_col(cand)
            if c:
                return c
        return None

    cS = find_col(a.summary_col)
    if not cS:
        raise SystemExit(f'❌ 找不到摘要列「{a.summary_col}」')
    idx = {k: find_field(k) for k in FIELDS}

    n = 0
    for r in range(hdr + 1, ws.max_row + 1):
        inv = ws.cell(r, idx['inv']).value if idx['inv'] else None
        if not inv:
            continue
        acct = str(ws.cell(r, idx['acct']).value or '').strip() if idx['acct'] else ''
        txt = (f"在{acct or FALLBACK['acct']}账号于"
               f"{_date_txt(ws.cell(r, idx['date']).value) if idx['date'] else '' or FALLBACK['date']}放款"
               f"OA流程号{str(ws.cell(r, idx['oa']).value or '').strip() if idx['oa'] else '' or FALLBACK['oa']}的"
               f"{str(ws.cell(r, idx['vendor']).value or '').strip() if idx['vendor'] else ''}"
               f"发票号{inv}"
               f"金额{_num(ws.cell(r, idx['amt']).value) if idx['amt'] else ''}vnd")
        cell = ws.cell(r, cS)
        cell.value = txt
        cell.alignment = Alignment(vertical='top', wrap_text=True)
        n += 1
        print(f'  S{r} {txt}')
    print(f'✅ 摘要静态化 {n} 行')

    # 删除指定列（向左平移 + 列宽跟随）
    for name in a.drop:
        c = find_col(name) if not re.fullmatch(r'[A-Za-z]{1,3}', name) else column_index_from_string(name)
        if not c:
            print(f'⚠️ 未找到列「{name}」，跳过')
            continue
        orig_w = {column_index_from_string(L): d.width for L, d in ws.column_dimensions.items()}
        ws.delete_cols(c, 1)
        # 列宽整体左移一格（openpyxl 不会自动搬 column_dimensions）
        for i in range(c, ws.max_column + 2):
            w = orig_w.get(i + 1)
            if w is not None:
                ws.column_dimensions[col_letter(i)].width = w
            else:
                ws.column_dimensions.pop(col_letter(i), None)
        print(f'🗑️ 已删除列「{name}」(原 {col_letter(c)} 列)')

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    wb.save(a.out)
    print(f'\n✅ 输出 → {a.out}')


if __name__ == '__main__':
    main()
