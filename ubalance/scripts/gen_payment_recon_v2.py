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
    ("能源费", ["điện kỳ", "điện năng", "kwh", "tiền điện", "phí điện", "nước", "điện"]),
    # 检测/检验类（INTERTEK / SGS / TÜV 等）→ 检测费；Daryl 2026-10-07：不能把检测费归到运费
    ("检测费", ["kiểm định", "kiểm nghiệm", "thử nghiệm", "phân tích", "giám định", "test",
              "inspection", "testing", "tuv", "sgs", "intertek"]),
    ("租赁费", ["phí thuê", "tiền thuê", "thuê xe", "thuê mặt bằng", "thuê kho", "nhà xưởng", "thuê"]),
    ("运费", ["cước", "vận đơn", "vận chuyển", "xếp dỡ", "bốc xếp", "cfs", "thc",
            "seal", "niêm chì", "logistics", "hải quan", "bill", "thu hộ", "nâng hạ"]),
    ("原材料", ["nguyên liệu", "vải", "sợi", "xơ", "bông", "polyester", "nylon", "yarn", "fabric"]),
    ("设备", ["máy", "thiết bị", "machine", "equipment", "phụ tùng"]),
    # 兜底：通用费类（含『phí』这种通用词，必须放最后，否则会把检测费/能源费抢走）
    ("服务费", ["duy tu", "quản lý", "dịch vụ", "service", "tư vấn", "bảo hiểm", "phí"]),
]
# 供应商直接定性（优先于关键词；只放有明确凭证证据的）
VENDOR_CATEGORY = [('INTERTEK', '检测费'), ('SGS', '检测费'), ('T[ÜU]V', '检测费')]
ITEM_KW = ['điện', 'phí', 'thuê', 'cước', 'dịch vụ', 'hàng hóa', 'nguyên liệu', 'vải', 'sợi',
           'chi phí', 'nước', 'quản lý']


def classify_by_vendor(vendor):
    """供应商定性（优先于关键词）：INTERTEK/SGS/TÜV → 检测费"""
    v = (vendor or '').upper()
    for pat, cat in VENDOR_CATEGORY:
        if re.search(pat, v):
            return cat
    return None


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
def load_detail(path, currency_filter=None):
    """读明细表 → 行列表。currency_filter: None/'all' | 'vnd' | 'nonvnd'（Q5 币别分流）。"""
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
            'orig_amount': g(r, '原币金额'),
            'rate': g(r, '本币汇率'),
            'cur': str(g(r, '原币币种') or '').strip(),
            'item': str(g(r, '资金现流项目') or '').strip(),
            'reason': str(g(r, '请款事由') or '').strip(),
            'own_acct': str(g(r, '本方银行账户') or '').strip(),
        })
    for i, d in enumerate(rows):
        d['idx'] = i          # 明细行序（1-based = i+1），供「目录号 ↔ 明细行号」匹配/校验
    cf = (currency_filter or 'all').lower()
    if cf == 'vnd':
        rows = [d for d in rows if '盾' in d['cur'] or 'VND' in d['cur'].upper()]
    elif cf == 'nonvnd':
        rows = [d for d in rows if not ('盾' in d['cur'] or 'VND' in d['cur'].upper())]
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


# Daryl 2026-10-07 口径③：**直接排除合同/订单类文件**（不得当发票行；仍写入附件清单留痕）
_NONINV_STRONG = re.compile(
    r'(合同|订单|采购|报价|价格分析|验收|结算单|对账|账单|送货|入库单|签呈|申请单|说明|进度支付|盖章|框架|'
    r'h[ợo]p\s*đ[ồo]ng|đ[ơơ]n\s*đ[ặa]t\s*h[àa]ng|purchase\s*order|b[áa]o\s*gi[áa]|b[ảa]ng\s*k[êe])', re.I)
_NONINV_WEAK = re.compile(r'(YNHT|CGDD|CGJS|WXBH|CGRK)', re.I)
_INVFILE = re.compile(r'(发票|ho[áa]\s*đ[ơo]n|invoice|H[ĐD][\s_\-]*\d|C26|1C2\d)', re.I)


def is_non_invoice_file(basename):
    """合同/订单/报价/验收/结算/账单/入库/签呈… → True（不做发票候选）。
    若文件名带明确发票标记（发票/HÓA ĐƠN/C26/1C2x…）且无强关键词 → False（保留）。"""
    b = unicodedata.normalize('NFC', str(basename or ''))
    if _NONINV_STRONG.search(b):
        return True
    if _INVFILE.search(b):
        return False
    return bool(_NONINV_WEAK.search(b))


def ocr_invoice(path):
    """单文件 → 发票 dict；一文件多票时把其余票放在 `_extra_invoices`。

  2026-10-07 改：确定性解析（vn_invoice_parse）优先，第三方引擎降为兑底——
  引擎在本批出现「只取未税」「多票只取首张」「跨文件串号」三类错，均不可审计。"""
    eng = None
    try:
        sys.path.insert(0, MVP)
        from ocr_engine import ocr_with_classify
        r = ocr_with_classify(path, department='采购部')
        if r.get('ok'):
            eng = dict(r['classification']['extracted'])
            fb = extract_full(r['ocr'].get('text', ''))
            for k, v in fb.items():
                if eng.get(k) in (None, '', 0, []):
                    eng[k] = v
            eng['_items_text'] = fb.get('items') or ' '.join(
                (li.get('description') or '') for li in (eng.get('line_items') or []))
            eng['_ocr'] = r['ocr'].get('source_format')
    except Exception as ex:
        print('  [warn] OCR 引擎不可用 %s: %s' % (os.path.basename(path), ex))

    try:
        from vn_invoice_parse import parse_pdf
        det = parse_pdf(path, engine_result=eng)
    except Exception as ex:
        print('  [warn] 确定性解析异常 %s: %s' % (os.path.basename(path), ex))
        det = []

    if det:
        first = dict(det[0])
        first['_file'] = os.path.basename(path)
        if eng and not first.get('vendor_tax_code'):
            first['vendor_tax_code'] = eng.get('vendor_tax_code')
        # 号码来源（Daryl 2026-10-07 再修正）：正文读不出（仅文件名兜底）
        # → 引擎对**正文**的读数可作依据（仍为 body 读数，不补零），并撤掉待核备注
        if eng and eng.get('invoice_number') and (not first.get('invoice_number') or
                                                 first.get('_num_src') in ('filename', 'none', None)):
            _e_no = str(eng['invoice_number']).strip()
            _e_dig = re.sub(r'\D', '', _e_no)
            if _e_dig and 1 <= len(_e_dig) <= 10 and _e_dig != re.sub(r'\D', '', str(first.get('invoice_number') or '')):
                first['invoice_number'] = _e_no
                first['_num_src'] = 'body'
                first['_engine_no'] = True
                first.pop('_need_check_no', None)
        # 引擎读值也入候选（确定性读法失真时供对账仲裁）
        if eng and (eng.get('total_amount') or 0) > 0:
            cs = list(first.get('_cands') or [])
            if int(eng['total_amount']) not in cs:
                cs.append(int(eng['total_amount']))
            first['_cands'] = cs
        first['_items_text'] = (eng or {}).get('_items_text', '')
        if len(det) > 1:
            first['_extra_invoices'] = det[1:]
        return first

    if eng:
        eng['_file'] = os.path.basename(path)
        return eng
    return None


def _reconcile(invs, target, apply_scale=True):
    """把一组发票金额归到明细金额：优先在各发票的「候选读法」里找恰好等于 target 的组合，
    退一步再做整体 VAT 还原。返回方法名（已就地改写 total_amount）或 None。
    候选读法来源：发票总额行 / 未税+税额 / 未税×(1+税率) / 第三方引擎读值
    （水印干扰常使单一读法失真，但明细金额是硬约束 → 用它做仲裁）"""
    import itertools
    cand_lists = []
    for iv in invs:
        cs = []
        for c in list(iv.get('_cands') or []) + [int(iv.get('total_amount') or 0)]:
            try:
                c = int(c)
            except (TypeError, ValueError):
                continue
            if c and c not in cs:
                cs.append(c)
        cand_lists.append(cs)
    best = None
    for combo in itertools.product(*cand_lists):
        if sum(combo) != target:
            continue
        diff = sum(abs(c - int(iv.get('total_amount') or 0)) for c, iv in zip(combo, invs))
        if best is None or diff < best[0]:
            best = (diff, combo)
    if best:
        for iv, v in zip(invs, best[1]):
            iv['total_amount'] = v
        return 'candidates'
    tot = sum(int(i.get('total_amount') or 0) for i in invs)
    for rate in (8, 10):
        if tot and abs(tot * (100 + rate) / 100 - target) <= max(2, len(invs)):
            if apply_scale:
                _scale_to(invs, target)
            return 'vat+%d%%' % rate
    # 最后兑底：卷内读值与明细对不上 → 标记待核（是否按明细改写由上层按 Q1/Q4 决定）
    if tot and target:
        if apply_scale:
            _scale_to(invs, target)
        return 'proportional-theo-bảng-kê'
    return None


def _scale_to(invs, target):
    """把一组发票金额按比例缩放到 target（消除未税口径带来的整体偏差，尾差压到最后一张）"""
    tot = sum(int(i['total_amount'] or 0) for i in invs)
    if not tot or tot == target:
        return
    acc = 0
    for i in invs[:-1]:
        v = int(int(i['total_amount'] or 0) * target / tot)
        i['total_amount'] = v
        acc += v
    invs[-1]['total_amount'] = target - acc


# ═════════ v2 金额呈现（Daryl 2026-10-07 口径 Q1/Q2/Q4/Q5/Q6）═════════
def _amt(v):
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


def vn_num(v):
    """越式千分位：1451652058 → 1.451.652.058"""
    return format(int(v or 0), ',').replace(',', '.')


def is_vnd(cur):
    c = str(cur or '').upper()
    return ('盾' in c) or ('VND' in c) or ('VIET' in c and 'NAM' in c)


def _cand_hit(invs, target):
    """组内候选读法能否组合出 target —— 命中即证明「发票真額 == 本次付款」（Q4 优先于 Q1）"""
    import itertools
    lists = []
    for iv in invs:
        cs = []
        for c in list(iv.get('_cands') or []) + [_amt(iv.get('total_amount'))]:
            try:
                c = int(c)
            except (TypeError, ValueError):
                continue
            if c and c not in cs:
                cs.append(c)
        lists.append(cs)
    if lists:
        for combo in itertools.product(*lists):
            if sum(combo) == target:
                return True
    tot = sum(_amt(i.get('total_amount')) for i in invs)
    for rate in (8, 10):
        if tot and abs(tot * (100 + rate) / 100 - target) <= max(2, len(invs)):
            return True
    return False


def plan_group(invs, target):
    """按 Daryl 口径的**优先序**给出呈现方式（不就地改数，由调用方决定）：
      ① 负数发票（调整票/贷项通知单） → 净额单行（Q2）
      ② 组内合計 == 明细 → 逐票金额、无备注
      ③ 读不准（通用版式 / 候选命中）→ H 取明细，备注「发票 OCR 金额不准」（Q4）
      ④ 合計 > 明细 → 部分付款（Q1）；若卷内恰有一张票全额 == 付款额 → 只取该票（其余标注未计入）
      ⑤ 合計 < 明细 → Q4（按明细对齐 + 备注）
    """
    total = sum(_amt(i.get('total_amount')) for i in invs)
    if any(_amt(i.get('total_amount')) < 0 for i in invs):
        return 'net-single'
    if total == target:
        return 'exact'
    if any(str(i.get('_src')) == 'generic' for i in invs):
        return 'ocr-inaccurate'
    if _cand_hit(invs, target):
        return 'ocr-inaccurate'
    if total > target:
        same = [i for i in invs if _amt(i.get('total_amount')) == target]
        if len(invs) > 1 and len(same) == 1:
            return 'subset-exact'
        return 'partial'
    return 'ocr-inaccurate'


def note_group(method, invs, target):
    """组级备注（越南语，会貼进表尾备注列）"""
    if method == 'net-single':
        # Q2 口径原文：备注列两张票（主票金额 + 调整发票负数金额）
        parts = []
        for i in invs:
            _v = _amt(i.get('total_amount'))
            parts.append('HĐ %s %s%s VND' % (i.get('invoice_number'), '-' if _v < 0 else '', vn_num(abs(_v))))
        net = sum(_amt(i.get('total_amount')) for i in invs)
        return '有两张发票：%s → 净额 %s VND (ghi nhận theo số net)' % (' + '.join(parts), vn_num(net))
    if method == 'partial':
        # Q1 口径原文：金额列 = 本次支付额；备注「发票金额 X VND，本次支付 Y VND」
        full = sum(_amt(i.get('total_amount')) for i in invs if _amt(i.get('total_amount')) > 0)
        det = '; '.join('hóa đơn %s = %s VND' % (i.get('invoice_number'), vn_num(_amt(i.get('total_amount'))))
                        for i in invs)
        return ('发票金额 %s VND，本次支付 %s VND (Thanh toán một phần: %s)'
                % ('{:,}'.format(full), '{:,}'.format(target), det))
    if method == 'subset-exact':
        same = [i for i in invs if _amt(i.get('total_amount')) == target]
        other = [i for i in invs if i not in same]
        det = '; '.join('%s = %s VND' % (i.get('invoice_number'), vn_num(_amt(i.get('total_amount')))) for i in other)
        return ('Khớp đúng hóa đơn %s = %s VND; hóa đơn khác trong bộ chứng từ không thuộc đợt giải ngân này (%s)'
                % (same[0].get('invoice_number'), vn_num(target), det))
    if method == 'ocr-inaccurate':
        # Q4 口径原文：备注「发票 OCR 金额不准」（金额已按明细改写）
        return '发票 OCR 金额不准，按请款明细金额对齐 (Số tiền hóa đơn OCR chưa chính xác - theo bảng kê giải ngân)'
    return ''


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

    print('\n=== ② OCR 附件包（递归子目录，并优先用真发票）===')
    folders = sorted([p for p in os.listdir(a.attach) if os.path.isdir(os.path.join(a.attach, p))],
                     key=lambda x: (len(x), x))

    def _prio(relpath):
        """子目录『HÓA ĐƠN（真发票）/ HD THAY THE（替换发票）』优先级 0；顶层文件 1。
        Daryl 2026-10-07：优先识别发票（发票常在 HÓA ĐƠN 子目录里），不要拿报告/对账单充当发票。"""
        top = os.path.normpath(relpath).split(os.sep)[0]
        n = unicodedata.normalize('NFC', top).lower()
        if any(k in n for k in ('hóa đơn', 'hoa don', 'hoadon', 'thay thế', 'thay the', 'thaythe')):
            return 0
        return 1

    groups = []
    for fname in folders:
        fd = os.path.join(a.attach, fname)
        invs, others = [], []
        cands = []
        for root, _dirs, files in os.walk(fd):
            for fn in sorted(files):
                if os.path.splitext(fn)[1].lower() not in ('.pdf', '.jpg', '.jpeg', '.png', '.tif', '.tiff'):
                    continue
                p = os.path.join(root, fn)
                cands.append((_prio(os.path.relpath(p, fd)), p))
        cands.sort(key=lambda t: (t[0], t[1]))
        for prio, p in cands:
            has_inner_inv = any(i.get('_prio') == 0 for i in invs)
            if prio == 1 and has_inner_inv:
                others.append({'file': os.path.basename(p), 'kind': '外围文档（已用 HÓA ĐƠN/替换发票）'})
                continue
            if is_non_invoice_file(os.path.basename(p)):      # 口径③：合同/订单类直接排除
                others.append({'file': os.path.basename(p), 'kind': '附件（合同/订单类·已排除）'})
                print('  📁%-3s 排除 %s（合同/订单类）' % (fname, os.path.basename(p)[:52]))
                continue
            e = ocr_invoice(p)
            if not e:
                others.append({'file': os.path.basename(p), 'err': 'OCR失败'})
                continue
            cands2 = [e] + list(e.get('_extra_invoices') or [])
            hit = [c for c in cands2
                   if (c.get('total_amount') or 0) and (c.get('invoice_number') or c.get('_src') == 'generic')]
            if hit:
                for c in hit:
                    c['_prio'] = prio
                    c['_src_path'] = os.path.relpath(p, fd)
                    invs.append(c)
                    print('  📁%-3s 发票 %-14s %-10s 合计=%-15s %s' % (
                        fname, c.get('invoice_number'), c.get('invoice_serial') or '',
                        format(int(c.get('total_amount') or 0), ','), str(c.get('vendor_name'))[:30]))
            else:
                others.append({'file': os.path.basename(p), 'kind': '附件(非发票)'})
                print('  📁%-3s 附件 %s' % (fname, os.path.basename(p)))
        # 噪声清理（Daryl 2026-10-07 发现）：同一卷里既有「有发票号」的行、又有「无号」行时，
        # 无号行多来自合同/订单/验收单等非发票文档（如目录 22 出现的 1,663 假行）→ 丢弃无号行，
        # 只保留有号发票参与对账（被丢弃的文件仍列入附件清单，可追溯）。
        _named = [i for i in invs if str(i.get('invoice_number') or '').strip()]
        if _named and len(_named) < len(invs):
            _ids = {id(i) for i in _named}
            for i in invs:
                if id(i) not in _ids:
                    others.append({'file': i.get('_file') or i.get('_src_path') or '?',
                                   'kind': '附件(非发票·未计金额)'})
            invs = _named
        groups.append({'folder': fname, 'invoices': invs, 'others': others,
                       'sum': sum(int(i.get('total_amount') or 0) for i in invs)})

    print('\n=== ③ 文件夹 ↔ 明细行 匹配（v2：币别分流 + 金额呈现）===')
    used = set()
    nonvnd = []          # 非 VND 卷（Q5：单独出表，不进 VND 表）
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
            g['recon'] = 'nomatch'
            continue
        used.add(match)
        d = det[match]
        g['detail'] = d
        target = int(d['amount'] or 0)
        g['_target'] = target
        # Q5：明细行本身非 VND → 不进 VND 表
        if not is_vnd(d['cur']):
            g['recon'] = 'nonvnd'
            nonvnd.append(g)
            print('  📁%-3s 非 VND（%s）→ 移入非 VND 表' % (g['folder'], d['cur']))
            continue
        # Q5：组内非 VND 发票也分流
        _fx = [i for i in g['invoices'] if not is_vnd(i.get('_currency'))]
        if _fx:
            g['invoices'] = [i for i in g['invoices'] if is_vnd(i.get('_currency'))]
            nonvnd.append({'folder': g['folder'], 'detail': d, 'invoices': _fx, 'others': g['others'],
                           'sum': sum(_amt(i.get('total_amount')) for i in _fx), 'recon': 'nonvnd'})
            print('  📁%-3s 卷内 %d 张非 VND 发票 → 移入非 VND 表' % (g['folder'], len(_fx)))
        g['sum'] = sum(_amt(i.get('total_amount')) for i in g['invoices'])
        if not g['invoices']:
            g['recon_method'] = 'no-invoice'
            g['recon'] = 'ok'
            print('  📁%-3s 无可识别发票 → 占位行 | OA=%s | %s VND' % (
                g['folder'], d['oa'], format(target, ',')))
            continue
        method = plan_group(g['invoices'], target)
        if method in ('ocr-inaccurate', 'subset-scaled'):
            if g['sum'] != target:
                _scale_to(g['invoices'], target)
        # D2：禁止碎行（单行 < 组额 5%）→ 并入最大行
        if len(g['invoices']) > 1:
            _tot = sum(_amt(i.get('total_amount')) for i in g['invoices'])
            _small = [i for i in g['invoices'] if _tot and 0 <= _amt(i.get('total_amount')) < 0.05 * _tot]
            if _small and len(_small) < len(g['invoices']):
                _big = max(g['invoices'], key=lambda x: _amt(x.get('total_amount')))
                for i in _small:
                    _big['total_amount'] = _amt(_big.get('total_amount')) + _amt(i.get('total_amount'))
                    o = i.get('_file') or i.get('_src_path')
                    g['others'].append({'file': str(o), 'kind': '碎行(<5%%)已并入最大行'})
                g['invoices'] = [i for i in g['invoices'] if i not in _small]
                print('     ✂️ 碎行保护：%d 行 <5%% 已并入最大行' % len(_small))
        g['recon_method'] = method
        g['recon'] = 'ok'
        g['_orig_sum'] = g['sum']
        g['sum'] = target
        print('  📁%-3s 读值=%-16s → OA=%-18s | %s' % (
            g['folder'], format(g['_orig_sum'], ','), d['oa'], method))

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
    cS = C('凭证摘要', 19)
    # Daryl 2026-10-07 定：S 列（= 删「款项类别」后的第 19 列）改为「文件夹号」便于回溯原件；税号移到 T 列并补表头
    cFolder = C('文件夹号', 20)
    cT = C('税号', 21)
    for _c, _n in ((cFolder, '文件夹号'), (cT, '税号')):
        if ws.cell(hdr, _c).value != _n:
            ws.cell(hdr, _c, _n)

    row = hdr + 1
    n = 0

    # 备注列（模板无此列时自动在末尾追加；用于「缺发票」「金额待核」等人工关注项）
    cNote = None
    for c in range(1, ws.max_column + 1):
        v = ws.cell(hdr, c).value
        if v and str(v).strip() in ('备注', 'Ghi chú', 'Ghi chu', 'Note', 'Lý do'):
            cNote = c
            break
    if not cNote:
        from openpyxl.styles import Font as _Font
        cNote = ws.max_column + 1
        _c = ws.cell(hdr, cNote, '备注')
        _c.font = _Font(bold=True)
        print('➕ 已新增「备注」列（第 %d 列）' % cNote)

    emitted = []

    def _nofrag(s):
        return [x for x in (s if isinstance(s, list) else [s]) if x]

    def inv_notes(inv):
        """发票级备注（口径：号码来源存疑 / 未确认正式电子发票）"""
        out = []
        if (inv or {}).get('_need_check_no'):
            out.append('số hóa đơn cần kiểm tra (không đọc được từ hóa đơn)')
        if (inv or {}).get('_official') is False:
            out.append('cần kiểm tra thủ công (chưa xác nhận hóa đơn điện tử chính thức)')
        return out

    def emit(d, inv, h, frags, folder, full=None, method=None):
        nonlocal row, n
        inv = inv or {}
        cat, kw = classify_items(inv.get('_items_text'))
        vcat = classify_by_vendor(inv.get('vendor_name') or d.get('name_en'))
        if vcat:
            cat, kw = vcat, 'vendor'
        frags = _nofrag(frags)
        ws.cell(row, cB, n + 1)
        ws.cell(row, cC, d['name_en'])
        ws.cell(row, cD, d['bank_name'])
        ws.cell(row, cE, d['bank_acct'])
        ws.cell(row, cF, str(inv.get('invoice_number') or ''))
        ws.cell(row, cG, inv.get('invoice_date') or '')
        ws.cell(row, cH, int(h))
        ws.cell(row, cO, inv.get('vendor_name') or d.get('name_en') or '')
        ws.cell(row, cP, cat)
        ws.cell(row, cR, d['oa'])
        ws.cell(row, cT, inv.get('vendor_tax_code') or '')
        ws.cell(row, cFolder, int(folder) if str(folder).isdigit() else folder)
        if frags:
            ws.cell(row, cNote, ' | '.join(frags))
        # 摘要公式：K账号 + L日期 + R OA号 + O越南名 + F发票号 + H金额（提交版由 finalize 净化）
        Lc = L
        ws.cell(row, cS, f'="在"&IF({Lc(cK)}{row}="","{{放款账号}}",{Lc(cK)}{row})&"账号于"&'
                         f'IF({Lc(cL)}{row}="","{{放款日期}}",TEXT({Lc(cL)}{row},"m""月""d""日""))&'
                         f'"放款OA流程号"&{Lc(cR)}{row}&"的"&{Lc(cO)}{row}&"发票号"&{Lc(cF)}{row}&'
                         f'"金额"&{Lc(cH)}{row}&"vnd"')
        print('  行%-2d 卷%-3s %-12s %-11s %-15s %-8s(触发:%-7s)%s' % (
            row, folder, str(inv.get('invoice_number') or '-')[:12],
            str(inv.get('_num_src') or '')[ :9], format(int(h), ','), cat, str(kw)[:7],
            ('  📝' + ' / '.join(frags)) if frags else ''))
        emitted.append({
            'folder': str(folder), 'row': row,
            'no': str(inv.get('invoice_number') or ''), 'serial': inv.get('invoice_serial') or '',
            'date': inv.get('invoice_date') or '', 'tax': inv.get('vendor_tax_code') or '',
            'vendor': inv.get('vendor_name') or d.get('name_en') or '',
            'full_amount': int(full if full is not None else (inv.get('total_amount') or 0)),
            'pay': int(h), 'note': ' | '.join(frags),
            'src': inv.get('_src') or '',
            'ocr': str(inv.get('_src') or '') in ('generic', 'engine'),
            'num_src': inv.get('_num_src') or '', 'official': bool(inv.get('_official')),
            'method': method or '', 'oa': d['oa'],
            'file': inv.get('_file') or inv.get('_src_path') or '',
        })
        row += 1
        n += 1
        return row - 1

    def _append_note(r, txt):
        if not txt:
            return
        cur = ws.cell(r, cNote).value
        ws.cell(r, cNote, ' | '.join([x for x in [cur, txt] if x]))

    for g in groups:
        d = g.get('detail')
        if not d or g.get('recon') == 'nonvnd':
            continue
        folder = g['folder']
        tgt = int(d['amount'] or 0)
        if not g['invoices']:
            emit(d, None, tgt, ['Thiếu hóa đơn (缺发票)'], folder, method='no-invoice')
            continue
        method = g.get('recon_method', 'exact')
        invs = sorted(g['invoices'], key=lambda x: str(x.get('invoice_number')))
        if method in ('net-single', 'partial'):
            # 净额单行（Q2，主票号）/ 部分付款单行（Q1）：H = 本次付款，发票全額写入备注
            main = max(invs, key=lambda x: abs(_amt(x.get('total_amount'))))
            full = sum(_amt(i.get('total_amount')) for i in invs if _amt(i.get('total_amount')) > 0) \
                if method == 'net-single' else sum(_amt(i.get('total_amount')) for i in invs)
            emit(d, main, tgt, inv_notes(main) + [note_group(method, invs, tgt)], folder,
                 full=full, method=method)
            continue
        if method == 'subset-exact':
            keep = [i for i in invs if _amt(i.get('total_amount')) == tgt] or invs
            last = None
            for inv in sorted(keep, key=lambda x: str(x.get('invoice_number'))):
                last = emit(d, inv, _amt(inv.get('total_amount')), inv_notes(inv), folder, method=method)
            _append_note(last, note_group(method, invs, tgt))
            continue
        # exact / ocr-inaccurate → 逐票（ocr-inaccurate 已在 ③ 按明细比例对齐）
        last = None
        for inv in invs:
            frags = inv_notes(inv)
            if not str(inv.get('invoice_number') or '').strip():
                frags.append('Thiếu số hóa đơn (需人工补)')
            last = emit(d, inv, _amt(inv.get('total_amount')), frags, folder, method=method)
        _append_note(last, note_group(method, invs, tgt))
    wb.save(a.out)
    print('\n✅ 输出: %s（%d 行）' % (a.out, n))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)

    # ── 台账 sidecar（D3/F2）：发票级数据 + 来源/勾选标记 → 供 recon_ledger.py 生成台账 xlsx ──
    def _row(d, inv=None, no='', note='', amount=None):
        inv = inv or {}
        return {'folder': str(d.get('_folder') or ''), 'oa': d.get('oa'), 'payee': d.get('name_en'),
                'bank': d.get('bank_name'), 'acct': d.get('bank_acct'),
                'currency': d.get('cur'), 'orig_amount': d.get('orig_amount'), 'rate': d.get('rate'),
                'no': no, 'date': inv.get('invoice_date') or '',
                'tax': inv.get('vendor_tax_code') or '',
                'amount': int(amount if amount is not None else (inv.get('total_amount') or d.get('amount') or 0)),
                'note': note, 'num_src': inv.get('_num_src') or '', 'src': inv.get('_src') or '',
                'official': bool(inv.get('_official'))}

    side = {'out': os.path.basename(a.out), 'attach': a.attach,
            'ledger': emitted, 'nonvnd': [], 'unmatched': []}
    for d in det:
        if not is_vnd(d['cur']):
            d['_folder'] = str(det.index(d) + 1)
            side['nonvnd'].append(_row(d, note='Chưa có hóa đơn (chưa nhận tài liệu)'))
    for g in nonvnd:
        d = g.get('detail') or {}
        d['_folder'] = str(g.get('folder') or '')
        for inv in sorted(g.get('invoices') or [], key=lambda x: str(x.get('invoice_number'))):
            side['nonvnd'].append(_row(d, inv, no=str(inv.get('invoice_number') or '')))
    _matched = {id(g.get('detail')) for g in groups if g.get('detail')}
    for i, d in enumerate(det):
        if id(d) in _matched or not is_vnd(d['cur']):
            continue
        d['_folder'] = str(i + 1)
        side['unmatched'].append(_row(d, note='Thiếu hóa đơn (缺发票)'))
    # 卷级对账（供台账「差异清单」）
    side['groups'] = []
    for g in groups:
        d = g.get('detail')
        _fold = str(g['folder'])
        side['groups'].append({
            'folder': _fold, 'oa': (d or {}).get('oa'), 'payee': (d or {}).get('name_en'),
            'currency': (d or {}).get('cur'),
            'detail_amount': _amt((d or {}).get('amount')),
            'read_sum': _amt(g.get('_orig_sum', g.get('sum'))),
            'pay_sum': sum(x['pay'] for x in emitted if x['folder'] == _fold),
            'method': g.get('recon_method') or '-', 'recon': g.get('recon'),
            'note': note_group(g.get('recon_method'), g.get('invoices') or [], g.get('_target', 0)),
        })
    with open(a.out + '.recon.json', 'w', encoding='utf-8') as _f:
        json.dump(side, _f, ensure_ascii=False, indent=1)

    # ── 对账报告（随输出同名 .recon.txt）：逐卷核对 + 金额口径 + 待人工核清单 ──
    lines = ['# Reconcile report · %s' % os.path.basename(a.out), '']
    lines.append('%-4s %-16s %-16s %-14s %-10s %s' % ('DIR', 'READ', 'DETAIL', 'METHOD', 'STATUS', 'OA'))
    for g in groups:
        d = g.get('detail')
        lines.append('%-4s %-16s %-16s %-14s %-10s %s' % (
            g['folder'], format(g.get('_orig_sum', g['sum']), ','),
            format(int(d['amount'] or 0), ',') if d else '-',
            g.get('recon_method', '-'), g.get('recon', 'nomatch'), d['oa'] if d else '-'))
        _rn = note_group(g.get('recon_method'), g.get('invoices') or [], g.get('_target', 0))
        if _rn:
            lines.append('     · 口径备注: %s' % _rn)
        for o in g['others']:
            lines.append('     · 附件: %s' % o.get('file'))
    if side['nonvnd']:
        lines.append('')
        lines.append('## 非 VND 行（Q5：不进 VND 表，单独出表）')
        for r in side['nonvnd']:
            lines.append('  卷%s  OA=%s  %s  %s %s' % (r['folder'], r['oa'], r['payee'],
                                                        format(r['amount'], ','), r['currency']))
    missing = [d for d in det if d['oa'] not in {g['detail']['oa'] for g in groups if g.get('detail')}]
    if missing:
        lines.append('')
        lines.append('## 待人工核（未匹配到发票的明细行）')
        for d in missing:
            lines.append('  OA=%s  %s  %s VND' % (d['oa'], d['name_en'], format(int(d['amount'] or 0), ',')))
    with open(a.out + '.recon.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('📋 对账报告: %s.recon.txt' % a.out)


if __name__ == '__main__':
    main()
