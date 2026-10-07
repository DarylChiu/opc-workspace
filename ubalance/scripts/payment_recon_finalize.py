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
import sys
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
    ap.add_argument('--summary-lang', choices=['vi', 'zh'], default='vi',
                    help='凭证摘要语言；默认 vi（Daryl 2026-10-07 定）')
    ap.add_argument('--currency', choices=['VND', 'USD'], default=None,
                    help='金额列（H）表头币别；不传则推断：金额≥1,000,000 → VND 否则 USD')
    ap.add_argument('--no-style', action='store_true',
                    help='不套用输出格式规范（Times New Roman + 全框线 + 取消 wrap text）')
    ap.add_argument('--submit', '--clean-submit', dest='submit', action='store_true',
                    help='提交版净化（Q7）：K/L 为空时摘要留空（不写占位符），并清掉全表残留的 {放款账号}/{放款日期}')
    ap.add_argument('--hdr-currency', default=None,
                    help='H 列表头币别文本，如 VND / USD / USD-EUR；默认按 VND/USD 推断')
    a = ap.parse_args()

    import openpyxl
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import summary_text
    from openpyxl.utils import column_index_from_string
    from openpyxl.styles import Alignment, Border, Side
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
    n_empty = 0
    for r in range(hdr + 1, ws.max_row + 1):
        inv = ws.cell(r, idx['inv']).value if idx['inv'] else None
        if not inv:
            continue
        _acct = ws.cell(r, idx['acct']).value if idx['acct'] else None
        _date = ws.cell(r, idx['date']).value if idx['date'] else None
        cell = ws.cell(r, cS)
        # Q7 提交版净化：K/L 为空 → 摘要留空（不写 {放款账号}/{放款日期} 占位符）
        if a.submit and (not str(_acct or '').strip() or not str(_date or '').strip()):
            cell.value = ''
            n_empty += 1
            continue
        txt = summary_text.build(
            a.summary_lang,
            _acct, _date,
            ws.cell(r, idx['oa']).value if idx['oa'] else None,
            ws.cell(r, idx['vendor']).value if idx['vendor'] else None,
            inv,
            ws.cell(r, idx['amt']).value if idx['amt'] else None)
        cell.value = txt
        cell.alignment = Alignment(vertical='top', wrap_text=True)
        n += 1
        print(f'  S{r} {txt}')
    print(f'✅ 摘要静态化 {n} 行' + (f'（提交版：{n_empty} 行因 K/L 空 → 摘要留空）' if a.submit else ''))
    if a.submit:
        # 防御：全表不得残留占位符（含公式文本）
        _left = 0
        for _r in range(hdr + 1, ws.max_row + 1):
            _v = ws.cell(_r, cS).value
            if isinstance(_v, str) and ('{放款账号}' in _v or '{放款日期}' in _v):
                ws.cell(_r, cS, '')
                _left += 1
        if _left:
            print('🧹 清除残留占位符摘要 %d 行' % _left)

    # H 列表头币别校准（Daryl 2026-10-07：按实际支付币别写表头，一般 VND / USD）
    c_h = None
    for c in range(1, ws.max_column + 1):
        v = ws.cell(hdr, c).value
        if v and re.match(r'^Số tiền trên hóa đơn/\s*Hợp đồng', str(v)):
            c_h = c
            break
    if c_h:
        if a.hdr_currency:
            cur = a.hdr_currency                # 调用方指定（如混合非 VND 表的 'Ngoại tệ / 原币'），原样使用
        else:
            cur = (a.currency or '').upper().strip()
            if cur not in ('VND', 'USD'):
                mx = max([int(_num(ws.cell(r, c_h).value) or 0) for r in range(hdr + 1, ws.max_row + 1)] or [0])
                cur = 'VND' if mx >= 1_000_000 else 'USD'
        old = str(ws.cell(hdr, c_h).value)
        new = re.sub(r'^Số tiền trên hóa đơn/\s*Hợp đồng.*$',
                     f'Số tiền trên hóa đơn/ Hợp đồng ({cur})', old)
        ws.cell(hdr, c_h, new)
        print(f'💱 {col_letter(c_h)} 列表头: 「{old}」→「{new}」')

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

    # ── 日期格式（Daryl 2026-10-07 定）：发票日期 / payment date 一律 MM/DD/YYYY
    def _to_date(v):
        if isinstance(v, (datetime.datetime, datetime.date)):
            return v
        s = str(v or '').strip()
        m = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})', s)
        if m:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        m = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', s)
        if m:
            return datetime.date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
        return None

    for _name, _fallback in (('Ngày hóa đơn', 7), ('payment date', None)):
        _c = find_col(_name) or _fallback
        if not _c:
            continue
        _n = 0
        for _r in range(hdr + 1, ws.max_row + 1):
            _v = ws.cell(_r, _c).value
            if _v in (None, ''):
                continue
            _d = _to_date(_v)
            if _d:
                ws.cell(_r, _c, _d)
                ws.cell(_r, _c).number_format = 'mm/dd/yyyy'
                _n += 1
        print('📅 %s → MM/DD/YYYY（%d 格）' % (_name, _n))

    # ── 输出格式规范（Daryl 2026-10-07 定，已写入 workflow）:
    #    ① 字体全部 Times New Roman  ② 全部加框线  ③ 取消 wrap text
    if not a.no_style:
        thin = Side(style='thin', color='000000')
        bd = Border(left=thin, right=thin, top=thin, bottom=thin)
        nr, nc = ws.max_row, ws.max_column
        for rr in range(1, nr + 1):
            for cc in range(1, nc + 1):
                cell = ws.cell(rr, cc)
                f = copy(cell.font)
                f.name = 'Times New Roman'
                f.size = f.size or 11
                cell.font = f
                cell.border = bd
                al = cell.alignment
                cell.alignment = Alignment(horizontal=al.horizontal,
                                           vertical=al.vertical or 'center', wrap_text=False)
        print('🎨 格式规范: Times New Roman + 全框线 + 取消 wrap text（%d行×%d列）' % (nr, nc))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    wb.save(a.out)
    print(f'\n✅ 输出 → {a.out}')


if __name__ == '__main__':
    main()
