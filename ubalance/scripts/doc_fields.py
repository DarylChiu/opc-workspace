#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc_fields.py — 贷款材料字段补全（v1.0，2026-10-03）

用途：当 **L1 只有发票号**（如 Daryl 直接给一张票号图）时，
      金额/日期/供应商/采购类别 必须从**材料本身**补全，而不是留空。

字段来源优先级：
  金额(USD)   : L1 > ToKhai「Tổng trị giá hóa đơn」
  报关日期    : L1 > ToKhai「Ngày đăng ký」
  发票日期    : L1 > Invoice/清关资料 PDF 上的 Invoice Date > ToKhai 报关日期(标注为兜底)
  供应商      : L1 > Invoice/清关资料 PDF 上的 Seller/Exporter/受益人 > 已知供应商名录扫描
  采购类别    : HS 码（ToKhai「Mã số hàng hóa đại diện」）+ Invoice 品名 交叉验证
  分类依据    : 记录两个来源的判定与是否互证/打架

⚠️ 兜底策略：任一字段拿不到 → 写「待补」并计入 note，**不留空、不静默**。
"""
import re

# ================= 一、采购类别 =================
# 纺织原料类 HS 章节 50-63；机器设备类 73/82/84/85/90
HS_RAW_CH = ('50', '51', '52', '53', '54', '55', '56', '57', '58', '59',
             '60', '61', '62', '63')
HS_EQUIP_CH = ('84', '85', '90', '73', '82')


def classify_by_hs(hs):
    if not hs or len(hs) < 2:
        return None
    ch = str(hs)[:2]
    if ch in HS_RAW_CH:
        return '原材料'
    if ch in HS_EQUIP_CH:
        return '设备'
    return None


EQUIP_KW = ['MACHINE', 'MÁY', 'MAY ', '浆纱机', '验布机', '水洗机', '染色机', '经编机', '织机',
            '一体机', 'WARPING', 'SIZING', 'WEAVING', 'KNITTING', 'DYEING', '设备', '机器',
            '配件', 'SPARE PART', '钢筘', '盘头', '储油槽', '锅炉', '立库', '喷淋塔', '试验机',
            'MOTOR', 'PUMP', 'BOILER', '空调', '定型机']
RAW_KW = ['YARN', 'POLYESTER', 'FABRIC', 'NYLON', 'FIBER', 'FILAMENT', '胚布', '成品', '纱线',
          '助剂', '染料', '毛坯', '布', 'DTEX', 'DENIER', 'GREIGE', 'WOVEN', 'SPANDEX', 'COTTON',
          'VẢI', 'SỢI']


def classify_by_goods(text):
    """读 Invoice/清关资料品名 → (类别, 命中的品名关键词)"""
    if not text:
        return None, ''
    u = text.upper()
    eq = [k for k in EQUIP_KW if k.upper() in u]
    rw = [k for k in RAW_KW if k.upper() in u]
    if eq and rw:
        return '混合(待拆分)', f'{"/".join(eq[:2])}+{"/".join(rw[:2])}'
    if eq:
        return '设备', '/'.join(eq[:3])
    if rw:
        return '原材料', '/'.join(rw[:3])
    return None, ''


def cross_validate(inv_cls, inv_prod, hs_cls, hs):
    """Invoice 品名为主 + HS 码交叉验证（沿用 Daryl 确认口径）
    互证一致→高；仅一源→中/高；两源打架→存疑低；都无→待确认低"""
    hs_tag = f'HS{hs}' if hs else '无HS码'
    prod = f'品名:{inv_prod}' if inv_prod else '品名未命中'
    if inv_cls and hs_cls:
        if inv_cls == hs_cls:
            return inv_cls, f'{prod} + {hs_tag}互证', '高'
        if inv_cls == '混合(待拆分)':
            return inv_cls, f'{prod}(含多品类) | {hs_tag}仅主类{hs_cls}', '中'
        return f'⚠️存疑({inv_cls}/{hs_cls})', f'{prod}判{inv_cls} vs {hs_tag}判{hs_cls}', '低'
    if inv_cls:
        return inv_cls, f'{prod}(品名判定); {hs_tag}未归类', '中'
    if hs_cls:
        return hs_cls, f'{hs_tag}(海关编码); {prod}', '高'
    return '⚠️待确认', f'{hs_tag}无法归类 + {prod}', '低'


# ================= 二、发票日期 =================
DATE_PAT = [
    r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})',                       # 15/09/2026
    r'(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})',                       # 2026-09-15
    r'(\d{1,2})[ \-]([A-Z]{3})[ \-](\d{4})',                        # 15 SEP 2026
]
MONTHS = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
          'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
DATE_LABELS = ['INVOICE DATE', 'DATE OF INVOICE', 'NGÀY HÓA ĐƠN', 'NGAY HOA DON',
               'INVOICE DT', 'ISSUE DATE', '发票日期', '开票日期', 'DATE:']


def _to_ymd(a, b, c):
    if len(a) == 4:      # YYYY-MM-DD
        y, mo, d = a, b, c
    elif b.upper() in MONTHS:   # DD-MON-YYYY
        y, mo, d = c, MONTHS[b.upper()], a
    else:                # DD/MM/YYYY
        y, mo, d = c, b, a
    try:
        return f'{int(y):04d}/{int(mo):02d}/{int(d):02d}'
    except (ValueError, TypeError):
        return ''


def extract_invoice_date(text):
    """从 Invoice/清关资料文本抓发票日期（优先标签附近，否则取首个合理日期）"""
    if not text:
        return ''
    U = text.upper()
    for lb in DATE_LABELS:
        i = U.find(lb)
        while i != -1:
            seg = text[i:i + 120]
            for p in DATE_PAT:
                m = re.search(p, seg)
                if m:
                    r = _to_ymd(*m.groups())
                    if r:
                        return r
            i = U.find(lb, i + 1)
    # 无标签 → 全文首个日期（置信度较低）
    for p in DATE_PAT:
        m = re.search(p, text)
        if m:
            r = _to_ymd(*m.groups())
            if r:
                return r
    return ''


# ================= 三、供应商 =================
SUP_LABELS = ['THE SELLER', 'SELLER', 'EXPORTER', 'BENEFICIARY', 'SHIPPER', 'SUPPLIER',
              'NGƯỜI BÁN', 'NGUOI BAN', 'BÊN BÁN', '供应商', '卖方', '发货人', '出口商']
KNOWN_SUPPLIERS = ['HUA FENG', 'HUAFENG', 'Fujian Cyclone', 'CYCLONE', 'SUMEC',
                   'WELLNAME', 'HUATE X', 'HUATEX']
_LEGAL_TAIL = (r'(?:CO\.,?\s*LTD\.?|COMPANY\s+LIMITED|CO\s+LTD|LIMITED|GROUP\s+CO\.,?\s*LTD\.?|'
               r'GROUP|CORPORATION|CORP\.?|INC\.?|TNHH|CÔNG TY|CONG TY|'
               r'股份有限公司|有限公司|集团)')


def extract_supplier(text):
    """从 Invoice/清关资料文本抓供应商（Seller/Exporter），否则扫已知名录"""
    if not text:
        return ''
    U = text.upper()
    for lb in SUP_LABELS:
        i = U.find(lb)
        while i != -1:
            seg = text[i + len(lb): i + len(lb) + 220]
            seg = re.sub(r'^[\s:：\-]+', '', seg)
            # 取含公司后缀的最长片段（贪婪，避免在 GROUP 处截断）
            m = re.search(r'([A-Z0-9&.,\'\- ]{3,80}' + _LEGAL_TAIL + r')', seg, re.IGNORECASE)
            if m:
                cand = re.sub(r'\s+', ' ', m.group(1)).strip(' .,;:')
                if 3 < len(cand) < 80:
                    return cand
            first = re.split(r'[\n\r]', seg)[0]
            first = re.sub(r'\s+', ' ', first).strip(' .,;:')
            if 3 < len(first) < 80:
                return first
            i = U.find(lb, i + 1)
    for k in KNOWN_SUPPLIERS:
        if k.upper() in U:
            return k
    return ''


# ================= 四、统一补全入口 =================
def fill_fields(l1=None, tk=None, inv_text=''):
    """返回 {'amount','date','supplier','cls','cls_src','cf','notes'}
    l1: {'amount','date','supplier'} 可为空；tk: extract_tokhai 结果；inv_text: 清关资料/Invoice 文本
    """
    l1 = l1 or {}
    tk = tk or {}
    notes = []

    amount = l1.get('amount')
    if amount is None and tk.get('amount') is not None:
        amount = tk['amount']
        notes.append('金额取自ToKhai')

    date = (l1.get('date') or '').strip()
    if not date:
        d = extract_invoice_date(inv_text)
        if d:
            date = d
            notes.append('发票日期取自清关资料')
        elif tk.get('ngay_ymd'):
            date = tk['ngay_ymd']
            notes.append('⚠️发票日期缺，暂用报关日期兜底')

    supplier = (l1.get('supplier') or '').strip()
    if not supplier:
        s = extract_supplier(inv_text)
        if s:
            supplier = s
            notes.append('供应商取自清关资料')
        else:
            supplier = '待补'
            notes.append('⚠️供应商未识别，待补')

    hs = tk.get('hs_code') or ''
    hs_cls = classify_by_hs(hs)
    inv_cls, prod = classify_by_goods(inv_text)
    cls, src, cf = cross_validate(inv_cls, prod, hs_cls, hs)

    if amount is None:
        notes.append('⚠️金额缺失')
    return {'amount': amount, 'date': date, 'supplier': supplier,
            'cls': cls, 'cls_src': src, 'cf': cf, 'notes': notes}
