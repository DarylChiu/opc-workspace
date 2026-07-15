#!/usr/bin/env python3
"""
doc_classify.py — v2.7.0 共享文档内容分类器
Outcome1 和 Outcome2 共用同一套判定，避免两处逻辑不一致。

Daryl 口径（2026-07-15 明确）—— 贷款材料包 = 以下 5 类，全部保留：
  1. Invoice（货物/设备的商业发票，物流/运费发票除外）
  2. Sales Contract / Sales Confirmation（货物/设备的销售合同/确认）
  3. Packing List（装箱单）
  4. B/L 或 Sea Waybill（空运用 AWB）
  5. ToKhai（已清关的 Excel 版）
不管这些是 2 个、5 个还是 10 个文件；销售合同分成几份扫描 PDF 也全部收进 Outcome2。

关键点：
  - 一份 PDF 可能同时含多类（如清关明细第1页SC+第2页Invoice+第3页装箱单，
    或 Invoice 与 B/L 合订）——按「多标签」处理，只要含任一保留类就保留。
  - 运费/物流发票、到货通知、产地证、DONG THUE 缴税单、清关资料Excel副本、
    请款/付款单等 → 排除。
"""
import os
import re

try:
    import pdfplumber
    PDF_READY = True
except ImportError:
    PDF_READY = False

try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_READY = True
except ImportError:
    OCR_READY = False

from tokhai_extract import extract_tokhai, is_tokhai_filename, _norm

# ===== 贷款材料保留类（Daryl 5类）=====
KEEP_TAGS = {'INVOICE', 'SALES_CONTRACT', 'PACKING_LIST', 'BL', 'SWB', 'AWB', 'TOKHAI_QDTQ'}
# 提单类（运输单据）
TRANSPORT_TAGS = {'BL', 'SWB', 'AWB'}


import json as _json
_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.pdftext_cache.json')
_TEXT_CACHE = None

def _cache_load():
    global _TEXT_CACHE
    if _TEXT_CACHE is None:
        try:
            _TEXT_CACHE = _json.load(open(_CACHE_PATH))
        except Exception:
            _TEXT_CACHE = {}
    return _TEXT_CACHE

def _cache_save():
    try:
        _json.dump(_TEXT_CACHE, open(_CACHE_PATH, 'w'), ensure_ascii=False)
    except Exception:
        pass


def pdf_pages_text(fp, pages=10):
    """返回逐页文本 list，清关资料明细为多页合订，需逐页看。
    扫描件（无文字层）回退 Tesseract OCR（chi_sim+eng，v2.3既有方案）。
    结果按 (路径,mtime,size) 缓存，避免 Outcome1/Outcome2 重复 OCR。"""
    if not PDF_READY:
        return []
    cache = _cache_load()
    try:
        st = os.stat(fp)
        key = f'{fp}|{st.st_mtime:.0f}|{st.st_size}|{pages}'
    except OSError:
        key = None
    if key and key in cache:
        return cache[key]
    out = []
    try:
        with pdfplumber.open(fp) as pdf:
            for p in pdf.pages[:pages]:
                out.append(p.extract_text() or '')
    except Exception:
        pass
    # OCR回退: 整份无文字层(扫描件)或pdfplumber打不开时走，控制成本
    if OCR_READY and sum(len(t.strip()) for t in out) < 40:
        try:
            imgs = convert_from_path(fp, dpi=200, first_page=1, last_page=min(pages, 5))
            ocr = [pytesseract.image_to_string(im, lang='chi_sim+eng') or '' for im in imgs]
            if sum(len(t.strip()) for t in ocr) > 40:
                out = ocr + out[len(ocr):]
        except Exception:
            pass
    # 空结果不入缓存（可能是移动硬盘I/O瞬时失败，避免毒化缓存）
    if key and sum(len(t.strip()) for t in out) >= 40:
        cache[key] = out
        if len(cache) % 20 == 0:
            _cache_save()
    return out


def pdf_text(fp, pages=10):
    return '\n'.join(pdf_pages_text(fp, pages))


# ===== 页级特征词 =====
SC_KW = ['SALES CONFIRMATION', 'SALES CONTRACT', '销售确认', '销售合同', '购销合同']
INVOICE_TITLE_KW = ['COMMERCIAL INVOICE', 'PROFORMA INVOICE', 'INVOICE NO']
PACKING_KW = ['PACKING LIST', '装箱单', 'packing list']


def _page_is_sales_contract(page_text):
    """单页是否为 Sales Contract/Confirmation（合同页）"""
    tu = page_text.upper()
    return any(k.upper() in tu for k in SC_KW)


def _page_is_packing_list(page_text):
    """单页是否为 Packing List（装箱单）"""
    tu = page_text.upper()
    if 'PACKING LIST' in tu:
        return True
    if '装箱单' in page_text:
        return True
    return False


def _page_is_invoice(page_text):
    """单页是否为货物/设备商业发票（SC页、装箱单页不算）"""
    tu = page_text.upper()
    # SC 标题页且无明确 Invoice 标题 → 合同页，不是发票页
    if _page_is_sales_contract(page_text) and not any(k in tu for k in INVOICE_TITLE_KW):
        return False
    if any(k in tu for k in INVOICE_TITLE_KW):
        return True
    # 中文发票页: 含"发票" + 金额USD
    if '发票' in page_text and 'USD' in tu:
        return True
    # 发票结构三要素(≥3个,且必须有 UNIT PRICE 等产品清单特征)
    struct = sum(1 for k in ['CONTRACT NO', 'UNIT PRICE', 'COMMODITY CODE',
                             'DESCRIPTION AND SPECIFICATION', 'NAME OF COMMODITY'] if k in tu)
    if struct >= 3 and 'UNIT PRICE' in tu:
        return True
    return False


def _strip_bl_refs(tu):
    """去掉引用性字样: SC页的"SHIPPER ON BILL OF LADING(提单指定发货人)"、"BILL OF LADING NO:"等
    （真提单有独立标题，不止是引用）"""
    import re as _re
    tu = _re.sub(r'SHIPPER\s+ON\s+BILL\s+OF\s+LADING', ' ', tu)
    tu = _re.sub(r'BILL\s+OF\s+LADING\s+(NO|NUMBER)\b', ' ', tu)
    return tu


def _page_is_bl(page_text):
    tu = _strip_bl_refs(page_text.upper())
    return any(k in tu for k in ['BILL OF LADING', 'SEA WAYBILL', 'NON-NEGOTIABLE',
                                 'TELEX RELEASE', 'AIR WAYBILL', 'HAWB', 'MAWB'])


def _bl_type(pages, tu, n, fname, allow_weak=True):
    """判定运输单据类型: 'BL' / 'SWB' / 'AWB' / None（承运人通知/到货单不算）"""
    tu = _strip_bl_refs(tu)   # 去引用性字样，只认真标题
    is_carrier_note = any(k in tu for k in ['FREE TIME', 'EST. ARRIVAL',
                          'AS AGENT FOR THE CARRIER', 'ALL AS ARRANGED',
                          'REVISED ETA', 'EST. ISSUE DATE']) \
                      or any(k in n for k in ['han lenh', 'so lenh'])
    if 'BILL OF LADING' in tu:
        return 'BL'
    if 'SEA WAYBILL' in tu or 'NON-NEGOTIABLE' in tu:
        return 'SWB'
    if any(k in tu for k in ['AIR WAYBILL', 'HAWB', 'MAWB', 'AWB NO']):
        return 'AWB'
    # 空运单弱判: 文件名含HAWB/MAWB/AWB(辅助线索)+内容含空运特征(航司排版常无AIR WAYBILL字样)
    import re as _re
    fu = fname.upper()
    if ('HAWB' in fu or 'MAWB' in fu or _re.search(r'\bAWB\b', fu)) \
            and any(k in tu for k in ['AIRPORT', 'FREIGHT PREPAID', 'FREIGHT COLLECT', 'CONSIGNEE']):
        return 'AWB'
    if ('TELEX RELEASE' in tu or 'SURRENDER' in tu) and not is_carrier_note:
        return 'BL'
    # 航运特征兜底：有船务信息但无提单标题，且非承运人通知 → B/L
    if allow_weak:
        has_ship = any(k in tu for k in ['SHIPPER', 'CONSIGNEE'])
        has_vessel = any(k in tu for k in ['VESSEL', 'VOYAGE', 'CONTAINER', 'PORT OF LOADING'])
        if has_ship and has_vessel and not is_carrier_note:
            return 'BL'
    return None


def classify_keep(fp):
    """
    内容级多标签判定。返回 (keep: bool, tags: set, extract_result)
      tags ⊆ {INVOICE, SALES_CONTRACT, PACKING_LIST, BL, SWB, AWB, TOKHAI_QDTQ}
            或排除原因 {FREIGHT, ARRIVAL_NOTICE, CO_CERT, TOKHAI_OTHER, OTHER}
      keep = tags 与 KEEP_TAGS 有交集
    一份文件可含多类（合订PDF）。extract_result 仅 ToKhai 有值。
    """
    fname = os.path.basename(fp)
    ext = os.path.splitext(fp)[1].lower()

    # ===== Excel: 只有已通关 ToKhai QDTQ 保留 =====
    if ext in ('.xls', '.xlsx', '.xlsm'):
        if is_tokhai_filename(fname):
            r = extract_tokhai(fp)
            if r['is_cleared']:
                return (True, {'TOKHAI_QDTQ'}, r)
            return (False, {'TOKHAI_OTHER'}, r)   # 未通关/DONG THUE缴税单等
        return (False, {'OTHER'}, None)            # 清关资料Excel副本/临时文件等

    # ===== PDF: 多标签 =====
    if ext == '.pdf':
        pages = pdf_pages_text(fp)
        full = '\n'.join(pages)
        tu = full.upper()
        n = _norm(full)
        tags = set()

        # 排除信号（整份判定）
        is_arrival = any(k in tu for k in ['ARRIVAL NOTICE', 'NOTICE OF ARRIVAL']) \
            or 'thong bao hang den' in n or 'ARRIVALNOTICE' in fname.upper()
        is_freight = any(k in tu for k in ['FREIGHT NOTE', 'FREIGHT INVOICE',
                          'CƯỚC VẬN CHUYỂN', 'CƯỚC TÀU', 'CƯỚC BIỂN',
                          'PHÍ VẬN CHUYỂN']) \
            or any(k in n for k in ['cuoc van chuyen', 'cuoc tau', 'cuoc bien',
                     'phi van chuyen', 'hoa don van tai', 'hoa don cuoc',
                     'hoa don gia tri gia tang'])   # 越南VAT发票=物流/本地费用发票(Daryl:物流发票除外)
        is_co = any(k in tu for k in ['CERTIFICATE OF ORIGIN', 'FORM E', 'FORM D']) \
            or '产地证' in full or 'chung nhan xuat xu' in n
        first = pages[0] if pages else ''
        fu = first.upper()
        fn_ = _norm(first)
        # 交货单 D/O ≠ 提单（标题区判定；Daryl 7/14: D/O 不是B/L）
        # 注: 真提单条款细则也含"delivery order"字样(如中谷SWB@2549字符处)，只认前400字符标题区
        _tz = fu[:400]
        is_do = 'DELIVERY ORDER' in _tz or 'D/O NO' in _tz or 'lenh giao hang' in fn_
        # 海关集装箱监管清单 ≠ 提单（Daryl 6/26: DANH SÁCH CONTAINER GIÁM SÁT 不是B/L）
        is_customs_list = 'danh sach container' in fn_ or 'giam sat hai quan' in fn_

        # 逐页保留类
        for pg in pages:
            if _page_is_invoice(pg):
                tags.add('INVOICE')
            if _page_is_sales_contract(pg):
                tags.add('SALES_CONTRACT')
            if _page_is_packing_list(pg):
                tags.add('PACKING_LIST')

        # 运费/物流发票不算货物 Invoice（Daryl: 物流发票除外）
        if is_freight:
            tags.discard('INVOICE')

        # 运输单据（到货通知/交货单D-O/海关监管清单 即使套用提单格式也不算提单——Daryl 7/14规则）
        # 运费单据只封弱兜底：真提单常含 FREIGHT PREPAID 字样，强标题(B/L,SWB,AWB)仍然有效
        if not (is_do or is_customs_list or is_arrival):
            bt = _bl_type(pages, tu, n, fname, allow_weak=not is_freight)
            if bt:
                tags.add(bt)
            # 弱兜底2: 提单无标题文字（如电放提单正本）——集装箱号模式+重量/体积，且无其他保留类和排除信号
            if not (tags & KEEP_TAGS) and not (is_freight or is_arrival or is_co):
                if re.search(r'\b[A-Z]{4}\d{7}\b', full) and ('KGS' in tu or 'CBM' in tu):
                    tags.add('BL')
                elif ('提单' in fname or '电放' in fname) and len(full.strip()) >= 80:
                    tags.add('BL')

        # 命中保留类 → 保留
        if tags & KEEP_TAGS:
            return (True, tags, None)

        # 无保留类 → 归排除原因
        if is_arrival:
            return (False, {'ARRIVAL_NOTICE'}, None)
        if is_do:
            return (False, {'DELIVERY_ORDER'}, None)
        if is_customs_list:
            return (False, {'CUSTOMS_LIST'}, None)
        if is_freight:
            return (False, {'FREIGHT'}, None)
        if is_co:
            return (False, {'CO_CERT'}, None)

        # 文件名兜底（内容读不全）
        if len(full.strip()) < 80:
            u = fname.upper()
            if any(k in u for k in INVOICE_TITLE_KW) or '清关' in fname or '中英文明细' in fname:
                return (True, {'INVOICE'}, None)
            if any(k in u for k in ['SEA WAYBILL', 'SWB']):
                return (True, {'SWB'}, None)
            if any(k in u for k in ['BL', 'TELEX']):
                return (True, {'BL'}, None)
            if any(k in u for k in ['AWB', 'HAWB', 'MAWB']):
                return (True, {'AWB'}, None)
            if any(k in u for k in ['PACKING']):
                return (True, {'PACKING_LIST'}, None)
            if any(k in u for k in ['CONTRACT', 'CONFIRMATION']):
                return (True, {'SALES_CONTRACT'}, None)

    return (False, {'OTHER'}, None)


# ===== 向后兼容: 返回单一主类别 =====
_PRIMARY_ORDER = ['INVOICE', 'SALES_CONTRACT', 'PACKING_LIST', 'BL', 'SWB', 'AWB', 'TOKHAI_QDTQ']


def classify_file(fp):
    """向后兼容旧接口。返回 (category, extract_result)。
    多标签时取优先主类别；含 Invoice+提单合订 → 'INVOICE_BL'。"""
    keep, tags, r = classify_keep(fp)
    if not keep:
        # 排除原因原样返回（TOKHAI_OTHER/ARRIVAL_NOTICE/FREIGHT/CO_CERT/OTHER）
        cat = next(iter(tags)) if tags else 'OTHER'
        return (cat, r)
    if 'INVOICE' in tags and (tags & TRANSPORT_TAGS):
        return ('INVOICE_BL', r)
    if 'INVOICE' in tags:
        return ('INVOICE_PDF', r)
    for c in _PRIMARY_ORDER:
        if c in tags:
            return (c, r)
    return ('OTHER', r)


# ===== 发票号/金额 精准归属（Daryl 7/15: 材料必须匹配L1发票号+金额，防兄弟票/共享目录干扰）=====

def classify_keep_ex(fp):
    """同 classify_keep，额外返回全文文本（PDF含OCR，供发票号归属判定用）。"""
    keep, tags, r = classify_keep(fp)
    text = ''
    if os.path.splitext(fp)[1].lower() == '.pdf':
        text = '\n'.join(pdf_pages_text(fp))
    return keep, tags, r, text


def _contains_inv_token(hay, inv):
    """精确token匹配发票号: 前后不能是字母数字；后面不能紧跟 -数字（防 X 匹配到 X-1 兄弟票）"""
    import re as _re
    pat = r'(?<![0-9A-Za-z])' + _re.escape(inv) + r'(?![0-9A-Za-z])(?!-\d)'
    return _re.search(pat, hay, _re.IGNORECASE) is not None


def attribute_file(text, fname, target, l1_invs):
    """判定文件归属: 'match'=引用目标发票号 | 'other:<票号>'=只引用其他票(干扰,剔除)
       | 'neutral'=未读到任何发票号(船务共享单据等)"""
    import re as _re
    hay = (fname or '') + '\n' + (text or '')
    if _contains_inv_token(hay, target):
        return 'match'
    others = sorted({i for i in l1_invs if i != target and _contains_inv_token(hay, i)})
    if others:
        return 'other:' + ','.join(others[:3])
    # 非L1兄弟票: 含 target-数字 后缀（如目标 X 但文件是 X-1）
    if _re.search(r'(?<![0-9A-Za-z])' + _re.escape(target) + r'-\d', hay, _re.IGNORECASE):
        return 'other:' + target + '-N(兄弟票)'
    return 'neutral'


def amount_in_text(text, fname, amount):
    """L1金额是否出现在文件内容中（1,234.56 / 1234.56 两种格式）"""
    if amount is None:
        return False
    hay = (fname or '') + '\n' + (text or '')
    a1 = f'{amount:,.2f}'
    a2 = f'{amount:.2f}'
    return a1 in hay or a2 in hay
