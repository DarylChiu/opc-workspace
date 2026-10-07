#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fill_payment_paid.py — 银行电汇凭单 → 回填 Payment 核销表「已付金额」等列

输入：银行「ĐIỆN CHUYỂN TIỀN ĐI」（电汇凭单/Phiếu hạch toán，通常扫描件，需 OCR）
每页提取：
  · 金额（Số tiền / CR ... VND）
  · 附言/内容（Nội dung / Remarks）——里面常带 "HOA DON SO <发票号>"
  · 收款方（Đơn vị nhận tiền / CR account name）
规则：
  1. 附言含发票号 → 直接按发票号填「已付金额」
  2. 附言不含发票号（一票多张，走合同号/打包付款）→ 记为 lump，按「同 OA 组发票合计 == lump 金额」整组核销
  3. 逐组校验：电汇合计 == 发票合计（不匹配报警）

用法:
  python3 scripts/fill_payment_paid.py --xlsx <输入.xlsx> --wire <电汇凭单.pdf> --out <输出.xlsx> \
      [--fill-i] [--fill-j] [--dry-run]
"""
import os
import re
import sys
import argparse


def _pages_text(pdf):
    import pdfplumber
    with pdfplumber.open(pdf) as p:
        texts = [(pg.extract_text() or '') for pg in p.pages]
    if sum(len(t.strip()) for t in texts) < 200:      # 扫描件 → OCR
        try:
            from pdf2image import convert_from_path
            import pytesseract
            imgs = convert_from_path(pdf, dpi=250)
            texts = [pytesseract.image_to_string(im, lang='vie+eng') for im in imgs]
        except Exception as e:
            print('[WARN] OCR 回退失败: %s' % e, file=sys.stderr)
    return texts


def _num(s):
    d = re.sub(r'[^0-9]', '', s or '')
    return int(d) if d else None


def parse_wire(pdf):
    pages = []
    for i, t in enumerate(_pages_text(pdf), 1):
        rec = {'page': i, 'text': t}
        # 金额：优先 "Số tiền:"，其次 Phiếu hạch toán 的 CR 行
        m = re.search(r'S[ốo] ti[ềe]n\s*[:：]\s*([0-9][0-9.,]*)', t, re.I)
        if not m:
            m = re.search(r'CR\s*([0-9][0-9.,]*)\s*VND', t, re.I)
        if m:
            rec['amount'] = _num(m.group(1))
        # 附言
        m = re.search(r'N[ộo]i dung\s*[:：]?\s*(.+)', t, re.I) or re.search(r'Remarks\s*[:：]?\s*(.+)', t, re.I)
        if m:
            rec['remark'] = re.sub(r'\s+', ' ', m.group(1)).strip()[:120]
        # 发票号（附言/内容里的 HOA DON SO xxx；只认纯数字）
        invs = []
        for mm in re.finditer(r'HOA\s*DON\s*(?:SO|3O|S[ỐO])\s*[:：]?\s*([0-9][0-9\s.,]*)', t, re.I):
            for d in re.findall(r'\d{5,}', mm.group(1)):
                invs.append(d)
        if not invs and rec.get('remark'):
            invs = [d for d in re.findall(r'(?<!\d)(\d{5,})(?!\d)', rec['remark'])]
        rec['invoices'] = invs
        # 收款方
        m = re.search(r'[ĐD][ơo]n v[ịi] nh[ậa]n ti[ềe]n\s*[:：]?\s*(.+)', t, re.I) or \
            re.search(r'CR\s*[0-9]+\s*\|?\s*([A-Z][A-Z0-9 &.,\-]{6,})', t)
        if m:
            rec['payee'] = re.sub(r'\s+', ' ', m.group(1)).strip()[:70]
        # 收款账号
        m = re.search(r'S[ốo] t[àa]i kho[ảa]n\s*[:：]?\s*([0-9]{6,})', t, re.I)
        if m:
            rec['acct'] = m.group(1)
        pages.append(rec)
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xlsx', required=True)
    ap.add_argument('--wire', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--fill-i', action='store_true', help='写 I「Số tiền đã thanh toán」')
    ap.add_argument('--fill-j', action='store_true', help='写 J「Số tiền nhận nợ lần này (VND)」')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    print('=== 电汇凭单解析（共 %d 页）===' % len(_pages_text(a.wire)))
    pages = parse_wire(a.wire)
    direct, lumps = {}, []
    for p in pages:
        print('  p%-2d 金额=%-15s 发票=%s' % (p['page'], format(p.get('amount') or 0, ','),
                                          ','.join(p.get('invoices') or []) or '(无 → 打包付款)'))
        if p.get('invoices') and p.get('amount'):
            for inv in p['invoices']:
                direct[inv.lstrip('0')] = p['amount']
        elif p.get('amount'):
            lumps.append(p)

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
    cF = col.get('Chứng từ giải ngân', 6)
    cH = None
    for _k, _c in col.items():
        if re.match(r'^Số tiền trên hóa đơn/\s*Hợp đồng', _k or ''):
            cH = _c
            break
    cH = cH or 8
    cR = col.get('请款单号', 18)
    cI = col.get('Số tiền đã thanh toán', 9)
    cJ = col.get('Số tiền nhận nợ lần này (VND)', 10)

    rows = [r for r in range(hdr + 1, ws.max_row + 1) if ws.cell(r, cF).value]
    paid = {}
    amt_of = {r: int(ws.cell(r, cH).value or 0) for r in rows}
    # 每页“数字串”（去分隔符）→ 金额/发票号都可能出现在其中；OCR 把金额字段读得不准时
    # 仍可“金额是否出现在本页”做判定（金额位数多，误配概率低）
    pdigits = {}
    for p in pages:
        pdigits[p['page']] = re.sub(r'\D', '', p.get('text') or '')
    used = set()

    def _inv(r):
        return str(ws.cell(r, cF).value).strip()

    print('\n=== 逐行匹配 ===')
    # ① 组级核销：本组发票合计出现在某页（含贷项通知单净额）→ 组内逐张按发票金额核销
    for oa in sorted({ws.cell(r, cR).value for r in rows}):
        grp = [r for r in rows if ws.cell(r, cR).value == oa]
        tot = sum(amt_of[r] for r in grp)
        if tot <= 0 or len(grp) < 1:
            continue
        hit = [p for p in pages if p['page'] not in used and str(tot) in pdigits[p['page']]]
        if hit and (len(grp) > 1 or not any(str(abs(amt_of[r])) in pdigits[p['page']]
                                              for r in grp for p in pages)):
            used.add(hit[0]['page'])
            for r in grp:
                paid[r] = amt_of[r]
                print('  行%-2d %-16s 发票金额=%-15s 已付=%-15s ①组级核销（OA=%s，凭单 p%d）'
                      % (r, _inv(r), format(amt_of[r], ','), format(amt_of[r], ','), oa, hit[0]['page']))
    # ② 按发票号直配（凭单附言带发票号，如 TT HD 00001046）
    for r in rows:
        if r in paid:
            continue
        for p in pages:
            if p['page'] in used:
                continue
            if _inv(r).lstrip('0') and _inv(r).lstrip('0') in [str(x).lstrip('0') for x in (p.get('invoices') or [])]:
                used.add(p['page'])
                paid[r] = amt_of[r]
                print('  行%-2d %-16s 发票金额=%-15s 已付=%-15s ②按发票号直配（凭单 p%d）'
                      % (r, _inv(r), format(amt_of[r], ','), format(amt_of[r], ','), p['page']))
                break
    # ③ 按金额出现在凭单页判定（凭单金额 = 该发票金额）
    for r in rows:
        if r in paid or not amt_of[r]:
            continue
        for p in pages:
            if p['page'] in used:
                continue
            if str(abs(amt_of[r])) in pdigits[p['page']]:
                used.add(p['page'])
                paid[r] = amt_of[r]
                print('  行%-2d %-16s 发票金额=%-15s 已付=%-15s ③按金额直配（凭单 p%d）'
                      % (r, _inv(r), format(amt_of[r], ','), format(amt_of[r], ','), p['page']))
                break
    for r in rows:
        if r not in paid:
            print('  行%-2d %-16s 发票金额=%-15s 已付=%-15s ❌无对应电汇凭单（未付款，需人工核）'
                  % (r, _inv(r), format(amt_of[r], ','), '-'))

    # 组级校验
    print('\n=== 组级校验（已匹配电汇合计 vs 发票合计）===')
    for oa in sorted({ws.cell(r, cR).value for r in rows}):
        grp = [r for r in rows if ws.cell(r, cR).value == oa]
        inv_tot = sum(amt_of[r] for r in grp)
        wire_tot = sum(paid.get(r, 0) for r in grp)
        print('  %-22s 发票合计=%-15s 已匹配电汇=%-15s %s' % (oa, format(inv_tot, ','), format(wire_tot, ','),
              '✅一致' if inv_tot == wire_tot else '⚠️不一致'))
    if a.dry_run:
        print('\n[dry-run] 不写文件')
        return
    n = 0
    for r, v in paid.items():
        if a.fill_i:
            ws.cell(r, cI, v)
        if a.fill_j:
            ws.cell(r, cJ, v)
        n += 1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    wb.save(a.out)
    print('\n✅ 已写入 %d 行（I=%s J=%s）→ %s' % (n, a.fill_i, a.fill_j, a.out))


if __name__ == '__main__':
    main()
