#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fill_payment_recon.py — Payment 核销表 · OCR 填充器（小样/批量通用）

口径（Daryl 2026-10-05）:
  输入  = 发票文件（PDF/JPG/PNG，走 expense_mvp 的 OCR+字段提取）
  匹配键 = G列发票号 + J列发票金额（发票号不唯一，故双键）
  填充列 = D Tiếng việt（供应商越南文名，带声调）/ I Mặt hàng-Mục đích GN（产品类型）
           + 末尾新增 U 税号(MST) / V 发票号(OCR) / W 凭证摘要
  摘要模板 = 在{放款账号}账号于{放款日期}放款OA流程号{OA流程号}的{供应商越南文名}发票号{发票号}金额{金额}vnd
            （三项批次参数未知时用 {放款账号}/{放款日期}/{OA流程号} 占位）

用法:
  python3 scripts/fill_payment_recon.py \
      --template "work/Mai岗位效率优化专案/inbox/Payment核销测试1005-1.xlsx" \
      --invoices "work/Mai岗位效率优化专案/inbox" \
      --out      "work/Mai岗位效率优化专案/out/Payment核销-小样.xlsx" \
      [--rows 3] [--batch-account 804008159608] [--batch-date 9月16日] [--batch-oa CGQK2609050101]
"""
import os
import re
import sys
import glob
import json
import argparse
import datetime

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MVP = os.path.join(WS, 'expense_mvp')

# ── 产品类型：发票品名关键词触发（口径待 Daryl 确认，先给一版） ──
CATEGORY_RULES = [
    # ★ Daryl 2026-10-05：产品类型统一写「运费」（运输/物流/车辆租赁类一律归此）
    ("运费", ["phí", "cước", "vận đơn", "vận chuyển", "xếp dỡ", "bốc xếp", "cfs", "thc",
            "seal", "niêm chì", "logistics", "hải quan", "bill", "thu hộ", "nâng hạ", "thuê xe"]),
    ("服务-检测费", ["kiểm định", "giám định", "test", "kiểm tra", "tuv", "sgs"]),
    ("服务-其他", ["dịch vụ", "service", "tư vấn", "bảo hiểm", "phí"]),
    ("原材料采购", ["nguyên liệu", "vải", "sợi", "xơ", "bông", "polyester", "nylon", "yarn",
                "fabric", "dệt", "nhuộm", "chỉ", "hạt nhựa"]),
    ("设备采购", ["máy", "thiết bị", "machine", "equipment", "phụ tùng"]),
    ("采购-其他", ["hàng hóa", "vật tư", "bao bì"]),
]


def classify_item(name_text):
    t = (name_text or '').lower()
    for cat, kws in CATEGORY_RULES:
        for kw in kws:
            if kw in t:
                return cat, kw
    return "其他（待指定）", ""


def _vn_num(s):
    """越南数字格式 '25.715.845' → 25715845"""
    if not s:
        return None
    d = re.sub(r'[^0-9]', '', s)
    return int(d) if d else None


def extract_from_text(txt):
    """水印容错兜底提取（2026-10-05 新增）。
    背景：部分电子发票文字层混入水印字符（如 'Số (Invoice No阮.): 00000147'），
    MVP 分类器的字段正则会失效——这里用宽松锚点从全文补提。
    """
    t = txt or ''
    out = {}
    m = re.search(r'S[ốo]\s*\(Invoice No[^)]*\)\s*[:.\s]*([0-9]{5,})', t, re.I)
    if m:
        out['invoice_number'] = m.group(1)
    m = re.search(r'K[ýy] hi[ệe]u[^\n]*?No\.[^)]*\)\s*[:.\s]*([A-Z0-9]{4,})', t, re.I)
    if m:
        out['invoice_serial'] = m.group(1)
    m = re.search(r'Ng[àa]y\s*\(day\)\s*(\d{1,2})\s*th[áa]ng\s*\(month\)\s*(\d{1,2})\s*n[ăa]m\s*\(year\)\s*(\d{4})', t, re.I)
    if m:
        out['invoice_date'] = f'{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}'
    m = re.search(r'[ĐD][ơo]n v[ịi] b[áa]n\s*\(Seller\)\s*[:.\s]*(.+)', t, re.I)
    if m:
        out['vendor_name'] = m.group(1).strip()
    m = re.search(r'MST\s*\(Tax Code\)\s*[:.\s]*([0-9][0-9\s\-]{8,})', t, re.I)
    if m:
        out['vendor_tax_code'] = re.sub(r'[^0-9]', '', m.group(1))
    m = re.search(r'C[ộo]ng ti[ềe]n h[àa]ng\s*\(Sub total\)\s*[:.\s]*([0-9.,]+)', t, re.I)
    if m:
        out['amount_pretax'] = _vn_num(m.group(1))
    m = re.search(r'C[ộo]ng ti[ềe]n thu[ếe] GTGT\s*\(VAT amount\)\s*[:.\s]*([0-9.,]+)', t, re.I)
    if m:
        out['vat_amount'] = _vn_num(m.group(1))
    m = re.search(r'T[ổo]ng c[ộo]ng ti[ềe]n thanh to[áa]n\s*\(Total payment\)\s*[:.\s]*([0-9.,]+)', t, re.I)
    if m:
        out['total_amount'] = _vn_num(m.group(1))
    m = re.search(r'Thu[ếe] su[ấa]t GTGT\s*\(Tax rate\)\s*[:.\s]*([0-9]{1,2})\s*%', t, re.I)
    if m:
        out['vat_rate'] = int(m.group(1))
    # 品名：抓「PHÍ/Phí/…」开头的服务行（剔除水印噪声）
    items = []
    for line in t.split('\n'):
        s = line.strip()
        if len(s) < 8:
            continue
        if re.match(r'^(Ph[íi]|C[ưu][ớo]c|D[ịi]ch v[ụu]|H[àa]ng h[óo]a|Nguy[êe]n li[ệe]u|V[ảa]i|S[ợo]i)', s, re.I):
            items.append(re.sub(r'\s+', ' ', s))
    if items:
        out['items'] = ' | '.join(items)[:300]
    return out


def mst_from_raw(raw):
    if not raw:
        return ''
    for pat in (r'Mã số thuế\s*\(Tax code\)\s*:?\s*([0-9][0-9 \-]{7,})',
                r'Tax code\)\s*:?\s*([0-9][0-9 \-]{7,})'):
        m = re.search(pat, raw, re.I)
        if m:
            d = re.sub(r'[^0-9]', '', m.group(1))
            if 10 <= len(d) <= 14:
                return d
    return ''


def norm_num(v):
    if v is None:
        return None
    try:
        return round(float(v))
    except Exception:
        return None


def ocr_invoices(folder):
    sys.path.insert(0, MVP)
    from ocr_engine import ocr_with_classify
    out = {}
    files = []
    for ext in ('pdf', 'jpg', 'jpeg', 'png', 'webp', 'tif', 'tiff'):
        files += glob.glob(os.path.join(folder, f'*.{ext}')) + glob.glob(os.path.join(folder, f'*.{ext.upper()}'))
    for p in sorted(set(files)):
        try:
            r = ocr_with_classify(p, department='采购部')
        except Exception as ex:
            print(f'  [OCR-ERR] {os.path.basename(p)}: {ex}')
            continue
        if not r.get('ok'):
            print(f'  [OCR-ERR] {os.path.basename(p)}: {r.get("error")}')
            continue
        e = r['classification']['extracted']
        # ★ 水印容错兜底：分类器字段缺失时，从全文补提（2026-10-05）
        fb = extract_from_text(r['ocr'].get('text', ''))
        for k, v in fb.items():
            if k == 'items':
                continue
            if e.get(k) in (None, '', 0):
                e[k] = v
        name_text = fb.get('items') or ' '.join((li.get('description') or '') for li in (e.get('line_items') or []))
        cat, kw = classify_item(name_text)
        rec = {
            'file': os.path.basename(p),
            'inv_no': (e.get('invoice_number') or '').strip(),
            'inv_serial': (e.get('invoice_serial') or '').strip(),
            'date': e.get('invoice_date') or '',
            'vendor_vn': (e.get('vendor_name') or '').strip(),
            'mst': (e.get('vendor_tax_code') or '').strip() or mst_from_raw(e.get('raw_text_snippet', '')),
            'pretax': norm_num(e.get('amount_pretax')),
            'vat': norm_num(e.get('vat_amount')),
            'total': norm_num(e.get('total_amount')),
            'currency': e.get('currency') or 'VND',
            'category': cat,
            'kw': kw,
            'items': name_text[:300],
        }
        out[(rec['inv_no'], rec['total'])] = rec
        out[('INVONLY', rec['inv_no'])] = rec
        print(f"  发票 {rec['inv_no']} ({rec['inv_serial']}) | {rec['vendor_vn'][:40]} | MST {rec['mst']} | "
              f"合计 {rec['total']} | 类别 {rec['category']}(触发词:{rec['kw']})")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--template', required=True)
    ap.add_argument('--invoices', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--rows', type=int, default=0, help='只处理前 N 行数据（0=全部）')
    ap.add_argument('--batch-account', default='{放款账号}')
    ap.add_argument('--batch-date', default='{放款日期}')
    ap.add_argument('--batch-oa', default='{OA流程号}')
    a = ap.parse_args()

    import openpyxl
    print('=== OCR 发票 ===')
    idx = ocr_invoices(a.invoices)

    wb = openpyxl.load_workbook(a.template)
    ws = wb['Sheet1']
    # 找表头行（含 'Tên khách hàng' 的行）
    hdr = None
    for r in range(1, min(ws.max_row, 8) + 1):
        vals = [str(ws.cell(r, c).value or '') for c in range(1, ws.max_column + 1)]
        if any('Tên khách hàng' in v for v in vals):
            hdr = r
            break
    hdr = hdr or 2
    colmap = {}
    for c in range(1, ws.max_column + 1):
        v = str(ws.cell(hdr, c).value or '').strip()
        if v:
            colmap[v] = c
    c_stt = colmap.get('STT', 2)
    c_vn = colmap.get('Tiếng việt', 4)
    c_item = colmap.get('Mặt hàng / Mục đích GN', 9)
    c_g = colmap.get('Chứng từ giải ngân', 7)
    c_j = next((c for c, v in colmap.items() if isinstance(c, str)), None)
    c_j = colmap.get('Số tiền trên hóa đơn/ Hợp đồng (USD)', 10)
    c_m = colmap.get('Số tiền nhận nợ lần này (VND)', 13)
    c_n = colmap.get('BÚT TOÁN', 14)          # 放款账号
    c_o = colmap.get('payment date', 15)      # 放款日期
    ncol = ws.max_column
    c_u, c_v, c_w = ncol + 1, ncol + 2, ncol + 3
    ws.cell(hdr, c_u, '税号 (MST)')
    ws.cell(hdr, c_v, '发票号 (OCR)')
    ws.cell(hdr, c_w, '凭证摘要')
    for c in (c_u, c_v, c_w):
        src = ws.cell(hdr, 1)
        ws.cell(hdr, c).font = src.font.copy() if src.font else None
        ws.cell(hdr, c).fill = src.fill.copy() if src.fill else None
        ws.cell(hdr, c).border = src.border.copy() if src.border else None
    ws.column_dimensions[openpyxl.utils.get_column_letter(c_u)].width = 14
    ws.column_dimensions[openpyxl.utils.get_column_letter(c_v)].width = 14
    ws.column_dimensions[openpyxl.utils.get_column_letter(c_w)].width = 80
    # 批次参数格：OA 流程号（Daryl 后补，填一格全表摘要自动更新）
    c_oa = ncol + 4
    ws.cell(hdr, c_oa, '批次参数 · OA流程号')
    ws.cell(hdr + 1, c_oa, a.batch_oa)
    ws.column_dimensions[openpyxl.utils.get_column_letter(c_oa)].width = 22

    print('\n=== 逐行匹配（G发票号 + J金额）===')
    done = 0
    for r in range(hdr + 1, ws.max_row + 1):
        g = str(ws.cell(r, c_g).value or '').strip()
        if not g:
            continue
        if a.rows and done >= a.rows:
            break
        gnorm = g.lstrip('0') or g
        jv = norm_num(ws.cell(r, c_j).value)
        rec = idx.get((g, jv)) or idx.get(('INVONLY', g)) or idx.get((gnorm, jv))
        if not rec:
            for (k, amt), v in idx.items():
                if k == 'INVONLY' and (k, ) and str(v['inv_no']).lstrip('0') == gnorm:
                    rec = v
                    break
        if not rec:
            print(f'  行{r}: G={g} J={jv} → ❌ 未匹配到发票')
            continue
        exact = (rec['total'] == jv)
        note = '' if exact else f'  ⚠️金额不一致(发票{rec["total"]} vs J列{jv})'
        ws.cell(r, c_vn, rec['vendor_vn'])
        ws.cell(r, c_item, rec['category'])
        ws.cell(r, c_u, rec['mst'])
        ws.cell(r, c_v, rec['inv_no'])
        # 摘要 = 公式拼接：放款账号取 N列(BÚT TOÁN) / 放款日期取 O列(payment date) / OA流程号取 X3(后补)
        o_val = ws.cell(r, c_o).value
        if hasattr(o_val, 'month'):
            date_txt = f'{o_val.month}月{o_val.day}日'
        else:
            date_txt = str(o_val or '').strip()
        L = openpyxl.utils.get_column_letter
        formula = (f'="在"&{L(c_n)}{r}&"账号于"&"{date_txt}"&"放款OA流程号"&$X$3&"的"&{L(c_vn)}{r}'
                   f'&"发票号"&{L(c_v)}{r}&"金额"&{L(c_j)}{r}&"vnd"')
        ws.cell(r, c_w, formula)
        done += 1
        print(f'  行{r}: G={g} → ✅ {rec["file"]} | {rec["category"]} | MST {rec["mst"]} | 合计 {rec["total"]}{note}')

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    wb.save(a.out)
    print(f'\n✅ 已输出: {a.out}  (填充 {done} 行)')


if __name__ == '__main__':
    main()
