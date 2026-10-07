#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fill_bank_receipt.py — 银行放款回单信息 → 回填 Payment 核销表

从银行回单（GIẤY BÁO NỢ / Debit Advice / 网银回单 PDF）提取：
  · 放款账号（From account number）→ 模板 K 列「BÚT TOÁN」
  · 放款日期（Ngày thực hiện / Transaction date）→ 模板 L 列「payment date」
  · 金额+币种 → 模板 A 列批次标签（沿用旧表惯例 "<金额> <币种> GIẢI NGÂN <日期>"）
可选（--set-method / --set-bank）：
  · payment method、Bank（默认不写，避免我替 Daryl 决定）

用法:
  python3 scripts/fill_bank_receipt.py --xlsx <输入.xlsx> --receipt <回单.pdf> \
      --out <输出.xlsx> [--set-method Loan] [--set-bank VTB] [--dry-run]
"""
import os
import re
import sys
import argparse
import datetime


def _txt(pdf):
    import pdfplumber
    with pdfplumber.open(pdf) as pdfobj:
        t = '\n'.join((pg.extract_text() or '') for pg in pdfobj.pages)
    if len(t.strip()) < 120:   # 扫描件 → OCR
        try:
            from pdf2image import convert_from_path
            import pytesseract
            imgs = convert_from_path(pdf, dpi=250)
            t = '\n'.join(pytesseract.image_to_string(im, lang='vie+eng+chi_sim') for im in imgs)
        except Exception as e:
            print('[WARN] OCR 回退失败: %s' % e, file=sys.stderr)
    return t


BANK_MAP = {
    'công thương': 'VTB',       # VietinBank
    'ngoại thương': 'VCB',      # Vietcombank
    'đầu tư và phát triển': 'BIDV',
    'đầu tư phát triển': 'BIDV',
    'kỹ thương': 'TCB',
    'á châu': 'ACB',
    'quân đội': 'MBB',
    'sài gòn thương tín': 'STB',
    'việt nam thịnh vượng': 'VPB',
    'công thương việt nam': 'VTB',
}


def parse_receipt(pdf):
    t = _txt(pdf)
    out = {'raw_len': len(t.strip())}
    # 放款账号：第一个非空的 "Số tài khoản"
    for m in re.finditer(r'S[ốo] t[àa]i kho[ảa]n\s*[:：]?\s*([0-9][0-9\s\-]{7,})', t, re.I):
        d = re.sub(r'[^0-9]', '', m.group(1))
        if 8 <= len(d) <= 20:
            out['account'] = d
            break
    # 放款日期
    m = re.search(r'Ng[àa]y th[ựu]c hi[ệe]n\s*[:：]?\s*(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})', t, re.I) \
        or re.search(r'Transaction date[^\d]{0,10}(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})', t, re.I)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        out['date'] = datetime.date(y, mo, d)
    # 金额 + 币种
    m = re.search(r'S[ốo] ti[ềe]n b[ằa]ng s[ốo]\s*[:：]?\s*([0-9][0-9.,]*)', t, re.I)
    if m:
        out['amount_raw'] = m.group(1)
        out['amount'] = float(re.sub(r'[^0-9.]', '', m.group(1).replace(',', '')))
    m = re.search(r'Lo[ạa]i ti[ềe]n\s*[:：]?\s*([A-Za-z]{3})', t, re.I)
    if m:
        out['currency'] = m.group(1).upper()
    # 银行
    m = re.search(r'Ng[âa]n\s*H[àa]ng\s+([A-Za-zÀ-ỹ\s]+)', t, re.I)
    if m:
        nm = m.group(1).strip().lower()
        out['bank_raw'] = m.group(1).strip()
        for k, v in BANK_MAP.items():
            if k in nm:
                out['bank'] = v
                break
    # 贷款放款回单（GIẤY BÁO NỢ / Debit Advice）→ payment method = Loan
    # （Daryl 2026-10-07 明确：GNN/UNC/回单信息本就可判定放款性质，不必等人填）
    if re.search(r'GI[ẤA]Y B[ÁA]O N[ỢO]|Debit\s*Advice', t, re.I):
        out['method'] = 'Loan'
    # 交易号
    m = re.search(r'S[ốo] giao d[ịi]ch\s*[:：]?\s*([0-9A-Za-z\-/]+)', t, re.I)
    if m:
        out['txn'] = m.group(1)
    return out


def fmt_amount(v, cur):
    s = f'{v:,.2f}'
    return f'{s} {cur}' if cur else s


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import summary_text
    except ImportError:
        summary_text = None
    ap = argparse.ArgumentParser()
    ap.add_argument('--xlsx', required=True)
    ap.add_argument('--receipt', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--set-method', default=None, help='写 payment method（如 Loan）；默认不动')
    ap.add_argument('--set-bank', default=None, help='写 Bank（如 VTB）；默认按回单银行识别')
    ap.add_argument('--summary-lang', choices=['vi', 'zh'], default='vi',
                    help='凭证摘要语言；默认 vi（Daryl 2026-10-07 定）')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    info = parse_receipt(a.receipt)
    print('=== 回单解析 ===')
    for k in ('account', 'date', 'amount', 'currency', 'bank', 'bank_raw', 'txn', 'method'):
        if info.get(k) is not None:
            print('  %-9s %s' % (k, info[k]))
    if not info.get('account') or not info.get('date'):
        print('❌ 未取到账号/日期，终止（需人工核）')
        sys.exit(2)

    label = f"{fmt_amount(info['amount'], info.get('currency'))} GIẢI NGÂN {info['date'].strftime('%d.%m.%Y')}"
    if a.dry_run:
        print('\n[dry-run] 将写入：')
        print('  A File Name      = %s' % label)
        print('  K BÚT TOÁN       = %s' % info['account'])
        print('  L payment date   = %s' % info['date'].isoformat())
        print('  M payment method = %s' % (a.set_method or '(不动)'))
        print('  N Bank           = %s' % (a.set_bank or info.get('bank') or '(不动)'))
        return

    import openpyxl
    wb = openpyxl.load_workbook(a.xlsx)
    ws = wb[wb.sheetnames[0]]
    hdr = 2
    for r in range(1, min(ws.max_row, 6) + 1):
        vals = [str(ws.cell(r, c).value or '') for c in range(1, ws.max_column + 1)]
        if any('Tên khách hàng' in v or v.strip() == 'STT' for v in vals):
            hdr = r
            break
    col = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(hdr, c).value
        if v:
            col[str(v).strip()] = c
    rows = [r for r in range(hdr + 1, ws.max_row + 1)
            if ws.cell(r, col.get('Chứng từ giải ngân', 6)).value
            or ws.cell(r, col.get('请款单号', 18)).value]
    date_txt = '%d月%d日' % (info['date'].month, info['date'].day)
    n = 0
    for r in rows:
        if 'File Name' in col:
            ws.cell(r, col['File Name'], label)
        ws.cell(r, col.get('BÚT TOÁN', 11), info['account'])
        ws.cell(r, col.get('payment date', 12), info['date'])
        method = a.set_method or info.get('method')
        if method and 'payment method' in col:
            ws.cell(r, col['payment method'], method)
        if 'Bank' in col:
            ws.cell(r, col['Bank'], a.set_bank or info.get('bank') or '')
        # ★ 凭证摘要：改写成**静态文本**（公式在飞书预览/Numbers 等不重算会显空）
        if '凭证摘要' in col:
            oa = ws.cell(r, col.get('请款单号', 18)).value or ''
            vn = ws.cell(r, col.get('Tiếng việt', 15)).value or ''
            inv = ws.cell(r, col.get('Chứng từ giải ngân', 6)).value or 'Thiếu hóa đơn'
            c_h = None
            for k, cc in col.items():
                if re.match(r'^Số tiền trên hóa đơn/\s*Hợp đồng', k or ''):
                    c_h = cc
                    break
            amt = ws.cell(r, c_h).value if c_h else ''
            if isinstance(amt, float):
                amt = int(amt)
            if summary_text:
                txt = summary_text.build(a.summary_lang, info['account'], info['date'], oa, vn, inv, amt)
            else:
                txt = f"在{info['account']}账号于{date_txt}放款OA流程号{oa}的{vn}发票号{inv}金额{amt}vnd"
            ws.cell(r, col['凭证摘要'], txt)
        n += 1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    wb.save(a.out)
    print('\n✅ 已回填 %d 行 → %s' % (n, a.out))
    print('   A=%s | K=%s | L=%s | M=%s | N=%s' % (label, info['account'], info['date'],
          a.set_method or info.get('method') or '(未动)', a.set_bank or info.get('bank') or '(未动)'))


if __name__ == '__main__':
    main()
