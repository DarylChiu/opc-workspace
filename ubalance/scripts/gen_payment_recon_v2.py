#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_payment_recon_v2.py — Payment 核销底稿生成器 v2（明细表 + 附件包 + OCR 三源合一）

Daryl 2026-10-05 口径（新模板 `Payment核销测试1005-1- MINH.xlsx`）：
  B STT(我填) | C Tên khách hàng ←明细表F/M(英文无音调) | D Ngân hàng ←明细DA | E Số tài khoản ←明细CZ
  F Chứng từ giải ngân = 发票号(OCR) | G Ngày hóa đơn = 发票日期(OCR) | H 发票金额(OCR 价税合计)
  K BÚT TOÁN=放款账号(留空待填) | L payment date(留空待填)
  O Tiếng việt = 越南文供应商名(OCR) | P Mặt hàng/Mục đích GN = 产品类型(关键词触发)
  R 请款单号 = OA流程号 ←明细S/DQ | S 凭证摘要(公式) | T 税号(OCR)
  一行 = 一张发票；摘要 = 在{K}账号于{L}放款OA流程号{R}的{O}发票号{F}金额{H}vnd

用法:
  python3 scripts/gen_payment_recon_v2.py --template <新模板.xlsx> --detail <明细.xlsx> \
      --attach <附件包根目录> --out <输出.xlsx> [--map-folder-by amount|order]
"""
import os
import re
import sys
import glob
import json
import shutil
import zipfile
import argparse
import datetime
import unicodedata

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MVP = os.path.join(WS, 'expense_mvp')

# ═════════ 产品类型：发票品名关键词触发（顺序即优先级）═════════
CATEGORY_RULES = [
    # 措辞对齐 HUATEX 明细表口径：系统里写「付能源费 / 报能源费用」（2026-10-05）
    ("能源费", ["điện kỳ", "điện năng", "kwh", "tiền điện", "nước"]),
    ("租赁费", ["phí thuê", "thuê xe", "thuê mặt bằng", "thuê kho", "phí quản lý"]),
    ("运费", ["phí", "cước", "vận đơn", "vận chuyển", "xếp dỡ", "bốc xếp", "cfs", "thc",
            "seal", "niêm chì", "logistics", "hải quan", "bill", "thu hộ", "nâng hạ"]),
    ("检测费", ["kiểm định", "giám định", "tuv", "sgs"]),
    ("原材料", ["nguyên liệu", "vải", "sợi", "xơ", "bông", "polyester", "nylon", "yarn", "fabric"]),
    ("设备", ["máy", "thiết bị", "machine", "equipment", "phụ tùng"]),
    ("服务费", ["dịch vụ", "service", "tư vấn", "bảo hiểm"]),
]
ITEM_KW = ['điện', 'phí', 'thuê', 'cước', 'dịch vụ', 'hàng hóa', 'nguyên liệu', 'vải', 'sợi',
           'chi phí', 'nước', 'quản lý']


def classify_items(text):
    low = (text or '').lower()
    for cat, kws in CATEGORY_RULES:
        for kw in kws:
            if kw in low:
                return cat, kw
    return "其他（待指定）", ""


def items_from_text(t):
    out, seen = [], set()
    for line in (t or '').split('\n'):
        s = re.sub(r'\s+', ' ', line.strip())
        if len(s) < 12 or 'thoại' in s.lower():
            continue
        if any(k in s.lower() for k in ITEM_KW):
            if s not in seen:
                seen.add(s)
                out.append(s)
    return ' | '.join(out[:6])[:320]


# ═════════ 统计/工具 ═════════
def norm_name(s):
    s = unicodedata.normalize('NFKD', str(s or ''))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]', '', s.lower())


def _digits(s):
    d = re.sub(r'[^0-9]', '', s or '')
    return d


def _vn_num(s):
    d = _digits(s)
    return int(d) if d else None


# ═════════ 明细表读取（泛微导出的 xlsx 有畸形样式，需清洗）═════════
def load_detail(path):
    import openpyxl
    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception:
        tmp = os.path.join(os.path.dirname(os.path.abspath(path)), '_clean_tmp.xlsx')
        zin = zipfile.ZipFile(path)
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
            for it in zin.infolist():
                data = zin.read(it.filename)
                if it.filename == 'xl/styles.xml':
                    s = data.decode('utf-8', 'ignore')
                    s = re.sub(r'<cellStyle(?![^>]*\bname=)[^>]*/>', '', s)
                    s = re.sub(r'<cellStyle[^>]*name=""/>', '', s)
                    data = s.encode('utf-8')
                zout.writestr(it, data)
        wb = openpyxl.load_workbook(tmp, data_only=True)
    ws = wb[wb.sheetnames[0]]
    from openpyxl.utils import column_index_from_string as CI
    # 表头在第 2 行（含「请款单号」）
    hdr_row = 2
    for r in range(1, min(ws.max_row, 6) + 1):
        vals = [str(ws.cell(r, c).value or '') for c in range(1, ws.max_column + 1)]
        if any('请款单号' in v for v in vals):
            hdr_row = r
            break
    col = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(hdr_row, c).value
        if v:
            col[str(v).strip()] = c
    def g(r, key, default=None):
        c = col.get(key)
        return ws.cell(r, c).value if c else default
    rows = []
    for r in range(hdr_row + 1, ws.max_row + 1):
        oa = str(g(r, '请款单号') or '').strip()
        if not oa:
            continue
        rows.append({
            'r': r,
            'oa': oa,
            'name_en': str(g(r, '对方名称') or '').strip(),
            'bank_name': str(g(r, '对方开户行名') or '').strip(),
            'bank_acct': str(g(r, '对方银行账号') or '').strip(),
            'amount': g(r, '本币付款金额'),
            'cur': str(g(r, '原币币种') or '').strip(),
            'item': str(g(r, '资金现流项目') or '').strip(),
            'reason': str(g(r, '请款事由') or '').strip(),
            'own_acct': str(g(r, '本方银行账户') or '').strip(),
        })
    return rows


# ═════════ 发票 OCR + 水印容错提取 ═════════
def mst_from_raw(raw):
    if not raw:
        return ''
    for pat in (r'Mã số thuế\s*\(Tax code\)\s*:?\s*([0-9][0-9 \-]{7,})',
                r'Mã số thuế\s*:?\s*([0-9][0-9 \-]{7,})',
                r'Tax code\)\s*:?\s*([0-9][0-9 \-]{7,})'):
        m = re.search(pat, raw, re.I)
        if m:
            d = _digits(m.group(1))
            if 10 <= len(d) <= 14:
                return d
    return ''


CJK_JUNK = '阮⽟⽒⼀⼆⼗'


def clean_vendor(name):
    """清理水印噪声：① 词内插入的数字（TH4Ị→THỊ）② 汉越扫描件混入的 CJK 字 ③ 多余空格"""
    s = str(name or '')
    s = ''.join(ch for ch in s if ch not in CJK_JUNK)
    s = re.sub(r'(?<=[A-Za-zÀ-ỹ])\d+(?=[A-Za-zÀ-ỹ])', '', s)   # 词内插字 TH4Ị→THỊ
    s = re.sub(r'(\s+\d+)+\s*$', '', s)                        # 尾部水印数字串 " 4 0"
    s = re.sub(r'\s+', ' ', s).strip()
    return re.sub(r'[\s\-–—]+$', '', s)


def extract_full(text):
    """统一提取（含水印容错）"""
    t = text or ''
    o = {}
    m = re.search(r'S[ốo]\s*\(Invoice No[^)]*\)\s*[:.\s]*([0-9]{5,})', t, re.I) or \
        re.search(r'S[ốo]\s*[:.\s]*([0-9]{6,})', t, re.I)
    if m:
        o['invoice_number'] = m.group(1)
    # 序列号（Ký hiệu）：只在含 "Ký hiệu" 的行里取 token，要求「字母+数字」且非标签词
    # （越南发票序列号形如 1C26TYY / C26TDP / 1C26TVN）
    for line in t.split('\n'):
        if not re.search(r'K[ýy] hi[ệe]u', line, re.I):
            continue
        for cand in re.findall(r'[0-9A-Z]{5,}', line.upper()):
            if re.search(r'\d', cand) and re.search(r'[A-Z]', cand) and cand not in ('SERIAL', 'NUMBER'):
                o['invoice_serial'] = cand
                break
        if o.get('invoice_serial'):
            break
    m = re.search(r'Ng[àa]y[^0-9]{0,20}(\d{1,2})[^0-9]{0,20}th[áa]ng[^0-9]{0,20}(\d{1,6})'
                  r'[^0-9]{0,20}n[ăa]m[^0-9]{0,20}(\d{4})', t, re.I)
    if m:
        day, yr = m.group(1), m.group(3)
        raw_mon = m.group(2)
        # 水印会在月份前后插字（如 "085" 实为 08）→ 先看前两位，无效再用后两位
        mon = raw_mon[:2]
        if not (1 <= int(mon) <= 12):
            mon = raw_mon[-2:]
        if 1 <= int(mon) <= 12 and 1 <= int(day) <= 31:
            o['invoice_date'] = f'{int(yr):04d}-{int(mon):02d}-{int(day):02d}'
    # 卖方名：优先标签；无标签则取文档最上方第一行 CÔNG TY（排除买方 HUATEX）
    m = re.search(r'[ĐD][ơo]n v[ịi] b[áa]n\s*\(Seller\)\s*[:.\s]*(.+)', t, re.I)
    if m:
        o['vendor_name'] = re.sub(r'\s+', ' ', m.group(1)).strip()
    else:
        for line in t.split('\n'):
            s = re.sub(r'\s+', ' ', line.strip())
            if re.match(r'^C[ÔO]NG TY', s, re.I) and 'HUATEX' not in s.upper() and len(s) > 12:
                o['vendor_name'] = clean_vendor(s)
                break
    if o.get('vendor_name'):
        o['vendor_name'] = clean_vendor(o['vendor_name'])
    mst = mst_from_raw(t)
    if mst:
        o['vendor_tax_code'] = mst
    for key, pat in (('amount_pretax', r'C[ộo]ng ti[ềe]n h[àa]ng(?:\s*\([^)]*\))?\s*[:.\s]*([0-9.,]+)'),
                     ('vat_amount', r'C[ộo]ng ti[ềe]n thu[ếe] GTGT(?:\s*\([^)]*\))?\s*[:.\s]*([0-9.,]+)'),
                     ('total_amount', r'T[ổo]ng c[ộo]ng ti[ềe]n thanh to[áa]n(?:\s*\([^)]*\))?\s*[:.\s]*([0-9.,]+)')):
        m = re.search(pat, t, re.I)
        if m:
            o[key] = _vn_num(m.group(1))
    m = re.search(r'Thu[ếe] su[ấa]t GTGT[^0-9]{0,10}([0-9]{1,2})\s*%', t, re.I)
    if m:
        o['vat_rate'] = int(m.group(1))
    items = items_from_text(t)
    if items:
        o['items'] = items
    return o


def ocr_invoice(path):
    sys.path.insert(0, MVP)
    from ocr_engine import ocr_with_classify
    r = ocr_with_classify(path, department='采购部')
    if not r.get('ok'):
        return None
    e = dict(r['classification']['extracted'])
    fb = extract_full(r['ocr'].get('text', ''))
    for k, v in fb.items():
        if e.get(k) in (None, '', 0, []):
            e[k] = v
    e['_items_text'] = fb.get('items') or ' '.join(
        (li.get('description') or '') for li in (e.get('line_items') or []))
    e['_file'] = os.path.basename(path)
    e['_ocr'] = r['ocr'].get('source_format')
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--template', required=True)
    ap.add_argument('--detail', required=True)
    ap.add_argument('--attach', required=True, help='附件包根目录（含 1/2/3 子文件夹）')
    ap.add_argument('--out', required=True)
    ap.add_argument('--map-folder-by', choices=['amount', 'order'], default='amount')
    a = ap.parse_args()

    import openpyxl
    from openpyxl.utils import get_column_letter as L

    print('=== ① 读明细表 ===')
    det = load_detail(a.detail)
    for d in det:
        print('  OA=%-22s %-42s %s %s' % (d['oa'], d['name_en'][:40], format(int(d['amount'] or 0), ','), d['cur']))

    print('\n=== ② OCR 附件包 ===')
    folders = sorted([p for p in glob.glob(os.path.join(a.attach, '*')) if os.path.isdir(p)],
                     key=lambda x: (len(os.path.basename(x)), os.path.basename(x)))
    groups = []
    for fd in folders:
        invs, others = [], []
        for p in sorted(glob.glob(os.path.join(fd, '*'))):
            if os.path.splitext(p)[1].lower() not in ('.pdf', '.jpg', '.jpeg', '.png', '.tif', '.tiff'):
                continue
            e = ocr_invoice(p)
            if not e:
                others.append({'file': os.path.basename(p), 'err': 'OCR失败'})
                continue
            if e.get('invoice_number') and (e.get('total_amount') or 0) > 0:
                invs.append(e)
                print('  📁%-3s 发票 %-10s %-12s 合计=%-14s %s' % (
                    os.path.basename(fd), e.get('invoice_number'), e.get('invoice_serial'),
                    format(int(e.get('total_amount') or 0), ','), str(e.get('vendor_name'))[:34]))
            else:
                others.append({'file': os.path.basename(p), 'kind': '附件(非发票)'})
                print('  📁%-3s 附件 %s' % (os.path.basename(fd), os.path.basename(p)))
        groups.append({'folder': os.path.basename(fd), 'invoices': invs, 'others': others,
                       'sum': sum(int(i.get('total_amount') or 0) for i in invs)})

    print('\n=== ③ 文件夹 ↔ 明细行 匹配 ===')
    used = set()
    for g in groups:
        match = None
        if a.map_folder_by == 'amount':
            for i, d in enumerate(det):
                if i in used:
                    continue
                if int(d['amount'] or 0) == g['sum']:
                    match = i
                    break
        if match is None:
            idx = int(re.sub(r'\D', '', g['folder'])) - 1
            if 0 <= idx < len(det) and idx not in used:
                match = idx
        if match is None:
            print('  📁%-3s 合计=%-14s → ❌ 无匹配明细行（需人工核）' % (g['folder'], format(g['sum'], ',')))
            continue
        used.add(match)
        d = det[match]
        ok = int(d['amount'] or 0) == g['sum']
        print('  📁%-3s 合计=%-14s → OA=%s %s' % (g['folder'], format(g['sum'], ','), d['oa'],
                                              '✅金额一致' if ok else '⚠️金额不一致(明细 %s)' % format(int(d["amount"] or 0), ',')))
        g['detail'] = d

    print('\n=== ④ 写模板 ===')
    wb = openpyxl.load_workbook(a.template)
    ws = wb[wb.sheetnames[0]]
    hdr = 2
    for r in range(1, min(ws.max_row, 6) + 1):
        vals = [str(ws.cell(r, c).value or '') for c in range(1, ws.max_column + 1)]
        if any(('STT' == v.strip()) or ('Tên khách hàng' in v) for v in vals):
            hdr = r
            break
    col = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(hdr, c).value
        if v:
            col[str(v).strip()] = c
    def C(name, default):
        return col.get(name, default)
    cB, cC, cD = C('STT', 2), C('Tên khách hàng', 3), C('Ngân hàng', 4)
    cE, cF, cG = C('Số tài khoản', 5), C('Chứng từ giải ngân', 6), C('Ngày hóa đơn', 7)
    cH, cK, cL = C('Số tiền trên hóa đơn/ Hợp đồng (USD)', 8), C('BÚT TOÁN', 11), C('payment date', 12)
    cO, cP, cR = C('Tiếng việt', 15), C('Mặt hàng / Mục đích GN', 16), C('请款单号', 18)
    cS, cT = C('凭证摘要', 19), C('税号', 20)

    row = hdr + 1
    n = 0
    for g in groups:
        d = g.get('detail')
        if not d:
            continue
        for inv in sorted(g['invoices'], key=lambda x: str(x.get('invoice_number'))):
            cat, kw = classify_items(inv.get('_items_text'))
            ws.cell(row, cB, n + 1)
            ws.cell(row, cC, d['name_en'])
            ws.cell(row, cD, d['bank_name'])
            ws.cell(row, cE, d['bank_acct'])
            ws.cell(row, cF, str(inv.get('invoice_number') or ''))
            ws.cell(row, cG, inv.get('invoice_date') or '')
            ws.cell(row, cH, int(inv.get('total_amount') or 0))
            ws.cell(row, cO, inv.get('vendor_name') or '')
            ws.cell(row, cP, cat)
            ws.cell(row, cR, d['oa'])
            ws.cell(row, cT, inv.get('vendor_tax_code') or '')
            # 摘要公式：K账号 + L日期 + R OA号 + O越南名 + F发票号 + H金额
            Lc = L
            # K/L 未填时不显示错误日期 → 用 IF 占位（Daryl 填上后全表自动更新）
            ws.cell(row, cS, f'="在"&IF({Lc(cK)}{row}="","{{放款账号}}",{Lc(cK)}{row})&"账号于"&'
                             f'IF({Lc(cL)}{row}="","{{放款日期}}",TEXT({Lc(cL)}{row},"m""月""d""日""))&'
                             f'"放款OA流程号"&{Lc(cR)}{row}&"的"&{Lc(cO)}{row}&"发票号"&{Lc(cF)}{row}&'
                             f'"金额"&{Lc(cH)}{row}&"vnd"')
            print('  行%-2d %-10s %-12s %-14s %-8s(触发:%s) | %s' % (
                row, inv.get('invoice_number'), inv.get('invoice_serial'),
                format(int(inv.get('total_amount') or 0), ','), cat, kw, str(inv.get('vendor_name'))[:30]))
            row += 1
            n += 1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    wb.save(a.out)
    print('\n✅ 输出: %s（%d 行 = %d 张发票）' % (a.out, n, n))


if __name__ == '__main__':
    main()
