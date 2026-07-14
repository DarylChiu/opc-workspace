#!/usr/bin/env python3
"""
doc_classify.py — v2.6 共享文档内容分类器
Outcome1 和 Outcome2 共用同一套判定，避免两处逻辑不一致。
关键修复:
  1. 逐页判定 —— 清关资料明细为多页合订(销售确认/Invoice/装箱单/提单可能混在一份)
     只要任一页命中 Invoice 特征 → 判 INVOICE_PDF
  2. Invoice 优先于 B/L
  3. 到货通知(无提单标题)排除
"""
import os

try:
    import pdfplumber
    PDF_READY = True
except ImportError:
    PDF_READY = False

from tokhai_extract import extract_tokhai, is_tokhai_filename, _norm


def pdf_pages_text(fp, pages=8):
    """返回逐页文本 list，清关资料明细为多页合订，需逐页看。"""
    if not PDF_READY:
        return []
    out = []
    try:
        with pdfplumber.open(fp) as pdf:
            for p in pdf.pages[:pages]:
                out.append(p.extract_text() or '')
    except Exception:
        pass
    return out


def pdf_text(fp, pages=8):
    return '\n'.join(pdf_pages_text(fp, pages))


INVOICE_KW_EN = ['COMMERCIAL INVOICE', 'SALES CONFIRMATION',
                 'PACKING LIST', 'PROFORMA INVOICE']
INVOICE_KW_CN = ['清关资料', '中英文明细', '商业发票', '装箱单']


def _page_is_invoice(page_text):
    """单页是否为 Invoice/Sales Confirmation/Packing List"""
    tu = page_text.upper()
    if any(k in tu for k in INVOICE_KW_EN):
        return True
    # 中文发票页: 含"发票/装箱单/销售确认" + 金额USD + 单价
    if any(k in page_text for k in ['发票', '装箱单', '销售确认']) and 'USD' in tu:
        return True
    # 发票结构三要素(≥3个,且必须有COMMODITY_CODE/NAME_OF_COMMODITY等产品清单特征)
    struct = sum(1 for k in ['CONTRACT NO', 'UNIT PRICE', 'COMMODITY CODE',
                             'DESCRIPTION AND SPECIFICATION', 'NAME OF COMMODITY'] if k in tu)
    if struct >= 3 and 'UNIT PRICE' in tu:
        return True
    return False


def _page_is_bl(page_text):
    tu = page_text.upper()
    return any(k in tu for k in ['BILL OF LADING', 'SEA WAYBILL', 'NON-NEGOTIABLE',
                                 'TELEX RELEASE', 'AIR WAYBILL', 'HAWB', 'MAWB'])


def classify_file(fp):
    """
    内容级分类。返回 (category, extract_result)
    保留类: INVOICE_PDF / TOKHAI_QDTQ / BL / SWB / AWB
    排除类: TOKHAI_OTHER(未通关) / ARRIVAL_NOTICE / OTHER
    """
    fname = os.path.basename(fp)
    ext = os.path.splitext(fp)[1].lower()

    # ===== Excel: ToKhai 内容级通关判定 =====
    if ext in ('.xls', '.xlsx', '.xlsm'):
        if is_tokhai_filename(fname):
            r = extract_tokhai(fp)
            return ('TOKHAI_QDTQ', r) if r['is_cleared'] else ('TOKHAI_OTHER', r)
        return ('OTHER', None)

    # ===== PDF =====
    if ext == '.pdf':
        pages = pdf_pages_text(fp)
        full = '\n'.join(pages)
        tu = full.upper()
        n = _norm(full)

        # (1) 逐页: 任一页是 Invoice → INVOICE_PDF (清关资料明细第2-3页含发票)
        if any(_page_is_invoice(pg) for pg in pages):
            return ('INVOICE_PDF', None)
        # 文件名含中文清关特征也认(内容读不全时兜底)
        if any(k in fname for k in INVOICE_KW_CN):
            return ('INVOICE_PDF', None)

        # (2) 到货通知 —— 直接排除(含 B/L 引用信息仍排除,v2.6修正)
        is_arrival = any(k in tu for k in ['ARRIVAL NOTICE', 'NOTICE OF ARRIVAL']) \
                     or 'thong bao hang den' in n or 'ARRIVALNOTICE' in fname.upper()
        if is_arrival:
            return ('ARRIVAL_NOTICE', None)

        # (3) 运费单/运费发票 —— 排除(不混入B/L)
        is_freight = any(k in tu for k in ['FREIGHT NOTE', 'FREIGHT INVOICE',
                         'CƯỚC VẬN CHUYỂN', 'CƯỚC TÀU', 'CƯỚC BIỂN',
                         'PHÍ VẬN CHUYỂN', 'OCEAN FREIGHT']) \
                     or any(k in n for k in ['cuoc van chuyen', 'cuoc tau', 'cuoc bien',
                         'phi van chuyen', 'hoa don van tai', 'hoa don cuoc'])
        if is_freight:
            return ('FREIGHT', None)

        # (4) B/L 类（先排除承运人通知:AN/DO/FREIGHT/到货单→不是提单;余下正常判）
        is_carrier_note = any(k in tu for k in ['FREE TIME', 'EST. ARRIVAL',
                           'AS AGENT FOR THE CARRIER', 'HANG LENH', 'SO LENH',
                           'ALL AS ARRANGED', 'REVISED ETA', 'EST. ISSUE DATE']) \
                     or any(k in n for k in ['han lenh', 'so lenh'])
        if 'BILL OF LADING' in tu:
            return ('BL', None)
        if 'SEA WAYBILL' in tu or 'NON-NEGOTIABLE' in tu:
            return ('SWB', None)
        if any(k in tu for k in ['AIR WAYBILL', 'HAWB', 'MAWB', 'AWB NO']):
            return ('AWB', None)
        if ('TELEX RELEASE' in tu or 'SURRENDER' in tu) and not is_carrier_note:
            return ('BL', None)
        # 航运特征兜底：有船务信息但无提单标题，且非承运人通知 → B/L
        has_ship = any(k in tu for k in ['SHIPPER', 'CONSIGNEE'])
        has_vessel = any(k in tu for k in ['VESSEL', 'VOYAGE', 'CONTAINER', 'PORT OF LOADING'])
        if has_ship and has_vessel and not is_carrier_note:
            return ('BL', None)

        # (4) 文件名兜底
        if len(full.strip()) < 80:
            u = fname.upper()
            if any(k in u for k in ['BL', 'SWB', 'TELEX']):
                return ('BL', None)
            if any(k in u for k in ['AWB', 'HAWB']):
                return ('AWB', None)

    return ('OTHER', None)
