#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vn_invoice_parse.py — 越南发票确定性解析（水印降噪 + 多票拆分）

背景（2026-10-07 · 09015 批次）：
  第三方 OCR 引擎（expense_mvp/ocr_engine）在这批发票上出现三类问题
    ① 只取「未税」（MISA 版发票无「Tổng tiền thanh toán」行）→ 金额偏小（8%/10%）
    ② 一个 PDF 内多张发票时只取第一张
    ③ 个别文件返回**别的文件的**发票号/金额（不可解释）→ 用确定性正则替代
  本模块按发票版式直接解析文本层，输出可审计字段；失败即返回空，由上层标记「附件/待人工核」。

支持版式
  A) 越南电子发票（ASIM/MISA/VDT 等）：`Số: 00001047` + `Cộng tiền hàng` / `Tiền thuế GTGT`
     / `Tổng tiền thanh toán`（缺失时用 未税+税额 兜底）+ `Đơn vị bán hàng` + `Mã số thuế`
  B) INTERTEK 版式：`Số hóa đơn (Invoice No): VNM-T/2026/39988` + `Tổng tiền (VND) X`
     （发票号以文件名为准，文本层末位常被水印污染）

用法：
  from vn_invoice_parse import parse_pdf
  invs = parse_pdf(path)      # → [dict(invoice_number, total_amount, ...), ...]
"""
import os
import re
import unicodedata

# 水印字符区（康熙部首 U+2E80–2FFF / 兼容区）+ CJK 统一表意
WATERMARK_CHARS = re.compile(r'[\u2e80-\u2fff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')

# 明显不是发票的文件名特征（附件/证明/报告/对账单）
NON_INVOICE_HINT = re.compile(
    r'(?i)(statement|report|trf|certificate|audit|审核|盖章|bank|debit|advice|'
    r'declaration|bảng\s*kê|bangkê|'
    r'申请单|订单|价格分析|验收单|确认单|结算单|入库单|签呈|送货单|账单|清单|通知书|报告|合同|预算)',
)

# VN 版式里「卖方/买方」分界附近的字段标签
RE_INV_NO = re.compile(r'(?<![àa]i kho[ảa]n\s)S[ốo]\s*(?:h[óo]a\s*đ[ơo]n)?\s*(?:\([^)]{0,25}\))?\s*[:：]?\s*(\d{3,10})(?![\dA-Za-zÀ-ỹ])', re.I)
# ⚠ 2026-10-07 短号变体：越南发票号常见 1–2 位（#4 / #40 / #57 / #65 / #77 / #78）
# 必须带「(No.)」标签才认，否则会误吞地址里的「Đường số 06」（这是上一版的 bug）
RE_INV_NO_SHORT = re.compile(r'S[ốo]\s*\(\s*No\.?\s*\)\s*[:：]?\s*(\d{1,4})(?!\d)', re.I)
# 变体：号码在标签上一行（ASIM 版式会把数字提到前一行，如 “40424\nSo (No.):”）
RE_INV_NO_ALT = re.compile(r'(\d{3,10})\s*S[ốo]\s*\(?\s*No\.?\s*\)?\s*[:：]?', re.I)
# 序列号：容忍「Ký hiệu (Serial No): 1C26TYE」「Ký hiệu (Serial); 1C26TLP」等夹标签/分号写法
# ⚠ 2026-10-07 回归覆盖：大小写混排序列号（1C26TLA / C26TDP / 1C26TYT）→ 命中后统一 upper()
RE_SERIAL = re.compile(
    r'K[ýy]\s*hi[ệe]u[^\nA-Za-z0-9]{0,3}(?:\([^)\n]{0,30}\))?[^\nA-Za-z0-9]{0,3}[:：;]\s*'
    r'([0-9A-Za-z]{4,12})(?![A-Za-z0-9])', re.I)
# ⚠ 2026-10-07 OCR 变体（回归目录 4/10 暴露）：扫描件常把「tiền→tiên」「Tổng→Tông」「thuế→thuê」「Mã→Ma」
# 认成近形元音 → 元音字符类必须同时包含 ề/ê/e、ổ/ô/o 等变体，否则标签行整行失配、金额读不出来。
RE_EXCL = re.compile(r'(?:C[ộôọo]ng|T[ổôốo]ng)\s*(?:ti[ềêe]n\s*)?h[àâa]ng(?:\s*\([^)]{0,50}\))?\s*[:：]?\s*([-−]?\s*[\d.,]{5,})', re.I)
RE_VAT = re.compile(r'Ti[ềêe]n\s*thu[ếêe]\s*GTGT(?:\s*\([^)]{0,50}\))?\s*[:：]?\s*([-−]?\s*[\d.,]{3,})', re.I)
RE_TOTALS = [
    re.compile(r'T[ổôốo]ng\s*(?:c[ộôọo]ng\s*)?(?:ti[ềêe]n\s*)?thanh\s*to[áâa]n(?:\s*\([^)]{0,50}\))?\s*[:：]?\s*([-−]?\s*[\d.,]{5,})', re.I),
    re.compile(r'S[ốôo]\s*ti[ềêe]n\s*thanh\s*to[áâa]n(?:\s*\([^)]{0,50}\))?\s*[:：]?\s*([-−]?\s*[\d.,]{5,})', re.I),
    # 变体：「Tổng cộng (Equivalent amount paid): 6.090.000」/ OCR「Tông cộng」
    re.compile(r'T[ổôốo]ng\s*c[ộôọo]ng(?:\s*\([^)]{0,50}\))?\s*[:：]?\s*([-−]?\s*[\d.,]{5,})', re.I),
]
RE_TOTAL = RE_TOTALS[0]
# 变体（Viettel vInvoice 等）：「TỔNG CỘNG (Total): 168.638.400 13.491.072 182.129.472」→ 未税 / VAT / 合计
RE_TOTAL3 = re.compile(r'T[ỔÔỐO]NG\s*C[ỘÔỌO]NG(?:\s*\([^)]{0,50}\))?\s*[:：]?\s*([\d.,]{5,})\s+([\d.,]{3,})\s+([\d.,]{5,})', re.I)
# 文件名明确不是发票的文档（合同/订单/验收/账单/签呈…）→ 不浪费 OCR
_NON_INV_NAME = re.compile(r'(申请单|订单|价格分析|验收|结算单|送货|账单|入库单|签呈|进度支付|入库|说明|合同|h[ợo]p\s*đ[ồo]ng|bi[êe]n\s*b[ảa]n|đơn\s*h[àa]ng)', re.I)
_INV_NAME = re.compile(r'(发票|ho[áa]\s*đ[ơo]n|invoice|C26|1C2\d|H[ĐD]\s*\d|HD\s*\d)', re.I)


def _find_total(region):
    for rx in RE_TOTALS:
        m = rx.search(region)
        if m:
            return m
    return None


RE_RATE = re.compile(r'Thu[ếêe]\s*su[ấâa]t\s*GTGT[^\d%]{0,40}(\d{1,2})\s*%', re.I)
RE_SELLER = re.compile(r'[ĐD][ơơn]\s*v[ịi]\s*b[áâa]n\s*h[àâa]ng(?:\s*\([^)]{0,40}\))?\s*[:：]?\s*([^\n]{5,140})', re.I)
RE_MST = re.compile(r'M[ãâa]\s*s[ốôo]\s*thu[ếêe](?:\s*\([^)]{0,30}\))?\s*[:：]?\s*(\d{10,13})', re.I)
# ASCII 标签兑底：部分 PDF 字体把「Mã số thuế / Đơn vị bán hàng」渲染成不带声调的字
# （如 Mã so thue / Đơn vi ̣bán hàng），此时靠括号里的英文标签抓取
RE_SELLER_ASCII = re.compile(r'\(Seller\)\s*[:：]\s*([^\n]{5,140})', re.I)
RE_MST_ASCII = re.compile(r'\(Tax\s*Code\)\s*[:：]?\s*(\d{10,13}(?:\s*[-–]\s*\d{1,3})?)', re.I)
RE_DATE_VN = re.compile(r'Ng[àa]y\s+(\d{1,2})\s*th[áa]ng\s*(\d{1,2})\s*n[ăa]m\s*(\d{4})')
RE_DATE_SIGN = re.compile(r'K[ýy]\s*ng[àa]y\s*[:：]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})')

# 容错版日期（用于**未降噪**原文：水印数字插进日期里，如 Ngày(Date)03tháng(month)095năm(year)2026）
RE_DATE_VN_TOL = re.compile(
    r'Ng[àa]y[^\d\n]{0,30}(\d{1,2})\s*th[áa]ng[^\d\n]{0,30}(\d{1,2})[^\n]{0,25}?n[ăa]m[^\d\n]{0,20}(\d{4})', re.I)
RE_DATE_SIGN_TOL = re.compile(
    r'(?:K[ýy]\s*ng[àa]y|Ng[àa]y\s*k[ýy]|Signing\s*Date)[^\d]{0,25}(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?!\d)', re.I)

# INTERTEK 版式
RE_IT_INV = re.compile(r'VNM-?T[-/](\d{4})[-/](\d{3,6})')
RE_IT_VND = re.compile(r'T[ổo]ng\s*ti[ềe]n\s*\(\s*VND\s*\)\s*([\d.,]+)')
RE_IT_USD = re.compile(r'T[ổo]ng\s*ti[ềe]n\s*\(\s*USD\s*\)\s*([\d.,]+)')
# INTERTEK/HÓA ĐƠN 版式：表头 (Invoice date) 下一行首列即发票日期（dd/mm/yyyy）
RE_DATE_HD = re.compile(r'\(Invoice\s*date\)[^\n]*\n\s*(\d{1,2})/(\d{1,2})/(\d{4})', re.I)
# INTERTEK 表头：Invoice date 列值形如 04-Jun-26，后跟付款条件列（Pre-payment / 30 days）
RE_DATE_IT = re.compile(
    r'(\d{1,2})-([A-Za-z]{3})-(\d{2,4})\s+(?:\d{1,3}\s*days?|Pre-?payment|Prepayment)', re.I)

# 通用日期（英文）: Date: Aug 17, 2026
RE_DATE_EN = re.compile(r'(?:Date|Ngày)[^\d]{0,12}(\d{1,2})\s*[/\-\s]\s*([A-Za-z]{3,9})[\s,/-]+(\d{4})')
MONTHS = {m: i + 1 for i, m in enumerate(
    ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}


def clean_text(t):
    """水印降噪 + Unicode 归一。
    ⚠️ 部分 PDF（如 INTERTEK 真发票/HÓA ĐƠN 子目录）文本层是 **NFD**（组合音符）
    → 带声调的正则全部失配，必须先 NFC 归一（2026-10-07 踩坑）。"""
    t = WATERMARK_CHARS.sub('', unicodedata.normalize('NFC', t or ''))
    # 部分 PDF 用 NUL/控制字符代替缺失字形（如 'So\x00 (No.):'）→ 不清掉会破坏正则
    t = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', t)
    # 只清理「粘在字母里的水印数字」，且**仅在含小写字母的词内**清理 —— 否则会把真号码/序列号打碎：
    #   水印风格: "C5ông"→"Công" / "03tháng"→"tháng" ✓ ；真号码: "1C26TDN" / "1C26TLP-78" ✗（必须保留）
    def _deg(m):
        tok = m.group(0)
        if not re.search(r'[a-zà-ỹ]', tok):
            return tok
        return re.sub(r'(?<=[A-Za-zÀ-ỹ])[0-9]+|[0-9]+(?=[A-Za-zÀ-ỹ])', '', tok)
    t = re.sub(r'\S+', _deg, t)
    LBL = re.compile(r'(?i)S[ốo]|No\.|Serial|Ng[àa]y|date|th[áa]ng|n[ăa]m|K[ýy]\s*hi[ệe]u|h[óo]a\s*đ[ơo]n|T[ỔO]NG|C[ỘO]NG|thu[ếe]')
    keep = []
    for ln in t.split('\n'):
        if LBL.search(ln):      # 带标签的行（Số/Ngày/Serial/合计…）原样保留 → 不打碎 1–2 位发票号/日期
            keep.append(ln)
            continue
        toks = [x for x in ln.split() if not re.fullmatch(r'\d{1,2}', x)]
        if toks:
            keep.append(' '.join(toks))
    return '\n'.join(keep)


def num(s):
    if s is None:
        return 0
    s = str(s)
    neg = bool(re.search(r'[-−]', s))
    # VN 金额书写常带小数位（如 `95 040.000,00` / `88.000.000.00`）→ 末段恰为 1–2 位数字时视为小数位丢弃
    # （VND 金额为整数；不处理会把 95,040,000 读成 9,504,000,000 —— 2026-10-07 回归目录 38 踩到）
    _m = re.search(r'^(.*?)[.,]\s*(\d{1,2})$', s.strip())
    if _m and len(re.sub(r'[^0-9]', '', _m.group(1))) >= 4:
        s = _m.group(1)
    d = re.sub(r'[^0-9]', '', s)
    if not d:
        return 0
    v = int(d)
    return -v if neg else v


def _date(m):
    if not m:
        return None
    g = m.groups()
    if len(g) == 3 and g[1].isalpha():
        mo = MONTHS.get(g[1][:3].lower())
        if not mo:
            return None
        return f'{g[2]}-{mo:02d}-{int(g[0]):02d}'
    d, mo, y = int(g[0]), int(g[1]), int(g[2])
    if y < 100:
        y += 2000
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return f'{y}-{mo:02d}-{d:02d}'


def _seller(region):
    m = RE_SELLER.search(region)
    if not m:
        return None
    txt = m.group(1).strip()
    # 折行续接：下一行若不含量词冒号且长度适中，则拼上
    tail = region[m.end():].split('\n')
    for nxt in tail[:2]:
        nxt = nxt.strip()
        if nxt and ':' not in nxt and re.search(r'[A-ZĐ]', nxt) and len(nxt) > 8:
            txt = (txt + ' ' + nxt).strip()
            break
    return re.sub(r'\s+', ' ', txt)[:120]


def _seller_global(text):
    """全文级「卖方名称 / 卖方税号」：卖方信息总在买方栏（Tên đơn vị / Họ tên người mua hàng）之前。
    部分版式无「Đơn vị bán hàng」标签（卖方名就是页首第一行），故两者都要兜底。
    返回 (name, mst, buyer_msts)"""
    mb = re.search(r'(?:T[êe]n\s*đ[ơo]n\s*v[ịi]|H[ọo]\s*t[êe]n\s*ng[ưu][ờo]i\s*mua\s*h[àa]ng)', text, re.I)
    head = text[:mb.start()] if mb else text
    tail = text[mb.start():] if mb else ''
    name = None
    m = RE_SELLER.search(head) or RE_SELLER_ASCII.search(head)
    if m:
        name = m.group(1).strip()
    if not name:
        for ln in head.split('\n'):
            s = ln.strip()
            if re.match(r'(C[ÔO]NG\s*TY|CHI\s*NH[ÁA]NH|BRANCH|V[ĂA]N\s*PH[ÒO]NG)', s, re.I) and len(s) > 8:
                name = s
                break
    buyer_msts = set(RE_MST.findall(tail))
    head_msts = RE_MST.findall(head)
    if not head_msts:
        head_msts = [re.sub(r'\s', '', x) for x in RE_MST_ASCII.findall(head)]
    if not head_msts:
        head_msts = [re.sub(r'\s', '', x) for x in RE_MST_ASCII.findall(text)]
    mst = head_msts[0] if head_msts else (RE_MST.findall(text) or [None])[0]
    return (re.sub(r'\s+', ' ', name)[:120] if name else None), mst, buyer_msts


def extract_date(raw, text):
    raw = unicodedata.normalize('NFC', raw or '')
    raw = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', raw)
    text = unicodedata.normalize('NFC', text or '')
    """发票日期提取（优先级：VN 年月日 → INTERTEK 表头 → 签署日 → 英文日期）。
    raw = 未降噪原文（容忍水印数字，如 095năm → 09）；text = 降噪文本。取不到返回 None（宁可空，不猜错）。"""
    for src in (raw, text):
        m = RE_DATE_VN_TOL.search(src) or RE_DATE_VN.search(src)
        if m:
            d = _date(m)
            if d:
                return d
    for src in (raw, text):
        m = RE_DATE_HD.search(src)
        if m:
            d = _date(m)
            if d:
                return d
    for src in (raw, text):
        m = RE_DATE_IT.search(src)
        if m:
            mo = MONTHS.get(m.group(2)[:3].lower())
            if mo:
                y = int(m.group(3))
                y += 2000 if y < 100 else 0
                return f'{y}-{mo:02d}-{int(m.group(1)):02d}'
    m = RE_DATE_SIGN_TOL.search(raw) or RE_DATE_SIGN_TOL.search(text)
    if m:
        return _date(m)
    return _date(RE_DATE_EN.search(text))


def _vn_invoices(text, path):
    """版式 A：按 `Số: <发票号>` 出现位置切块，每块独立解析（支持一文件多票）。"""
    spans = []
    for m in RE_INV_NO.finditer(text):
        # 排除「引用型」号（贷项通知单「Điều chỉnh hóa đơn số …」/ 替换发票「Thay thế cho hóa đơn … số …」）
        pre = text[max(0, m.start() - 45):m.start()].lower()
        if re.search(r'(?:h[óo]a\s*đ[ơo]n|ch[ứu]ng\s*t[ừu]|h[ợo]p\s*đ[ồo]ng)\s*$', pre):
            continue
        if re.search(r'(thay\s*th[ếe]|đi[ềe]u\s*ch[ỉi]nh)', pre):
            continue
        spans.append((m.start(), m.end(), m.group(1)))
    for m in RE_INV_NO_ALT.finditer(text):
        pre = text[max(0, m.start() - 45):m.start()].lower()
        if re.search(r'(thay\s*th[ếe]|đi[ềe]u\s*ch[ỉi]nh)', pre):
            continue
        spans.append((m.start(), m.end(), m.group(1)))
    for m in RE_INV_NO_SHORT.finditer(text):
        pre = text[max(0, m.start() - 45):m.start()].lower()
        if re.search(r'(thay\s*th[ếe]|đi[ềe]u\s*ch[ỉi]nh)', pre):
            continue
        spans.append((m.start(), m.end(), m.group(1)))
    if not spans:
        # 扫描件：标签被 OCR 认花（`Số /moieAo): 00000223`）→ 定向兜底（Q3 前导 0 原样保留）
        spans = _ocr_inv_no_spans(text)
    # 若有「Số (No.):」严格锚点 → 只用它（否则会把货物行的「số 20260319/YHF」当发票号，
    # 并把真正的区域切碎 → 2026-10-07 目录 31 踩到）
    if spans:
        _strict = [m for m in spans if re.search(r'S[ốo]\s*\(\s*No\.?\s*\)', text[m[0]:m[1]])]
        if _strict:
            spans = _strict
    seen, uniq = set(), []
    for s in sorted(spans):
        if s[2] in seen:
            continue
        seen.add(s[2])
        uniq.append(s)
    spans = uniq
    out = []
    for i, (s, e, inv) in enumerate(spans):
        end = spans[i + 1][0] if i + 1 < len(spans) else len(text)
        region = text[s:end]
        excl, vat = num(RE_EXCL.search(region).group(1)) if RE_EXCL.search(region) else 0, \
            num(RE_VAT.search(region).group(1)) if RE_VAT.search(region) else 0
        m3 = RE_TOTAL3.search(region)   # 三数行：未税 VAT 合计
        if m3:
            excl = num(m3.group(1)) or excl
            vat = num(m3.group(2)) or vat
        mt = _find_total(region)
        total = (num(m3.group(3)) if m3 else 0) or (num(mt.group(1)) if mt else 0)
        if not total and excl and vat:
            total = excl + vat
        if not total and excl:                      # 只有未税 → 按税率补
            r = RE_RATE.search(region)
            rate = int(r.group(1)) if r else 0
            total = excl + excl * rate // 100
        if not total:
            continue
        cands = []
        if mt:
            cands.append(total)
        if excl and vat and excl + vat > 0:
            cands.append(excl + vat)
        r0 = RE_RATE.search(region)
        rr = int(r0.group(1)) if r0 else 0
        if excl and rr:
            cands.append(excl + excl * rr // 100)
        if excl and excl not in cands:
            cands.append(excl)
        sr = RE_SERIAL.search(region) or RE_SERIAL.search(text)
        _ser = sr.group(1).upper() if sr else None
        # 序列号必须「字母+数字」混排（越南发票 Ký hiệu 形如 1C26TLA/C26TDP）
        if _ser and not (re.search(r'\d', _ser) and re.search(r'[A-Z]', _ser)):
            _ser = None
        mst = RE_MST.findall(region)
        _cur = 'VND'
        _mc = re.search(r'(?i)\b(USD|EUR|VND)\b', region)
        if _mc and _mc.group(1).upper() != 'VND':
            _cur = _mc.group(1).upper()
        # 调整发票/贷项通知单识别（负数金额 或 票面 `điều chỉnh`/credit note 标记）
        # ⚠ OCR 可能把负号读丢（目录 56 调整票同一文件两次 OCR 一正一负）
        #   → 票面存在「điều chỉnh + giảm」语义且金额为正时，强制按扣减额（负数）计
        _adjmark = re.search(r'(?i)đi[ềe]u\s*ch[ỉi]nh|dieu\s*chinh|credit\s*note', region)
        _negmark = re.search(r'(?i)gi[ảa]m|giam\s*gi|credit\s*note', region)
        _incmark = re.search(r'(?i)đi[ềe]u\s*ch[ỉi]nh\s*t[ăa]ng|dieu\s*chinh\s*tang', region)
        if total and total > 0 and _adjmark and _negmark and not _incmark:
            total = -total
            if excl:
                excl = -excl
            cands = [-c for c in cands]
        _adj = bool(total < 0) or bool(_adjmark) or bool(
            re.search(r'(?i)(h[óo]a\s*đ[ơo]n\s*đi[ềe]u\s*ch[ỉi]nh|credit\s*note|gi[ảa]m\s*gi[áa])',
                      region))
        out.append(dict(
            invoice_number=inv,
            invoice_serial=_ser,
            _adjust=_adj,
            invoice_date=None,
            total_amount=total, excl=excl or None, vat=vat or None,
            vat_rate=rr or None,
            vendor_name=_seller(region),
            vendor_tax_code=(mst[0] if mst else None),
            line_items=[],
            _cands=cands,
            _src='vn_einvoice',
            _num_src='body',          # 号码来自发票正文（文本层）
            _currency=_cur,           # Q5 前置：币别（默认 VND）
        ))
    return out


def _intertek_invoice(text, path, clean):
    """版式 B：INTERTEK（发票号取自文件名，文本层末位易被水印污染）。"""
    base = os.path.basename(path)
    m = RE_IT_INV.search(base) or RE_IT_INV.search(text)
    if not m:
        return []
    inv = f'VNM-T/{m.group(1)}/{m.group(2)}'
    mv = RE_IT_VND.search(clean)
    if mv:
        total = num(mv.group(1))
        cur = 'VND'
    else:
        mu = RE_IT_USD.search(clean)
        if not mu:
            return []
        total = num(mu.group(1))
        cur = 'USD'
    return [dict(invoice_number=inv, invoice_serial='VNM-T',
                 invoice_date=None,
                 total_amount=total, excl=None, vat=None, vat_rate=8,
                 vendor_name='INTERTEK VIETNAM', vendor_tax_code=None,
                 line_items=[], _cands=[total], _src='intertek', _currency=cur,
                 _num_src='body')]


# ═════════ 发票号来源/归一/左补零 + 正式发票判定（Daryl 2026-10-07 口径补充 3 条）═════════
RE_TAXCODE = re.compile(r'M[ãa]\s*c[ủu]a\s*c[ơo]\s*quan\s*thu[ếe]', re.I)


def norm_digits(s):
    """数字归一（口径补充 3.b）：去掉数字之间的空格/点/换行
    （水印/低清 OCR 常见 `0 0 0 0 0 2 3 5` / `000.002.35`）→ `00000235`。"""
    return re.sub(r'(?<=\d)[\s.]+(?=\d)', '', str(s or ''))


def _digits(s):
    return re.sub(r'[^0-9]', '', str(s or ''))


# ⛔ pad_inv_no() 已于 2026-10-07 16:2x **整函数删除**（Daryl 口径：越南发票号并非统一 8 位，
#   不得补零/不得臆造位数）。删除而非 no-op —— 从源头消除任何「补 0」调用路径；
#   号码来源只有三种：正文文本层 body / 扫描件页眉 OCR ocr-header / 文件名兜底 filename。

RE_HDR_NO = re.compile(r'\(\s*[^\n\)]{0,12}No\.?\s*\)\s*[:.]?\s*([0-9][0-9\s.]{0,18})', re.I)
RE_HDR_NO2 = re.compile(r'\b(?:invoice\s*)?No\.?\s*[:.]\s*([0-9][0-9\s.]{0,18})', re.I)
RE_HDR_NO3 = re.compile(r'S[ốoôò6$]\s*[:.]\s*([0-9][0-9\s.]{0,18})', re.I)
_HDR_PATS = (RE_HDR_NO, RE_HDR_NO2, RE_HDR_NO3)
_HDR_KW = re.compile(r'(?i)h[óo]a\s*đ[ơo]n|invoice|VAT|gi[áa]\s*tr[ịi]|thu[ếe]|ng[àa]y|t[ổo]ng|k[ýy]\s*hi[ệe]u|s[ốo]|ti[ềe]n')


def _pick_no(txt):
    """从 OCR 文本里按「(Invoice No)」→「No:」→「Số:」三类带标签形式取发票号（数字已归一）。
    仅认带括号/冒号的标签 —— 避免把垃圾文本里的偶发 “SO 66313” 当号码（扫件质量差时尤其重要）。"""
    ct = clean_text(txt or '')
    for rx in _HDR_PATS:
        for m in rx.finditer(ct):
            d = _digits(norm_digits(m.group(1)))
            if 1 <= len(d) <= 10:
                return d
    return None


def _kw_score(t):
    return len(_HDR_KW.findall(t or ''))


def _binarize(im):
    """二值化去噪（口径再修正 §1：页眉 OCR 前做去噪），提升扫描件号段落识别率。"""
    try:
        from PIL import ImageOps
        g = ImageOps.grayscale(im)
        g = ImageOps.autocontrast(g, cutoff=2)
        return g.point(lambda p: 255 if p > 150 else 0)
    except Exception:
        return im


def _digits(s):
    """纯数字提取（仅用于号码归一，不做任何位数补全）。"""
    return re.sub(r'[^0-9]', '', str(s or ''))


def ocr_header_invoice_no(path):
    """扫描件二次定向 OCR（口径补充 3.a / 再修正 §1）：仅裁第 1 页页眉（上 25%）、
    300–400 DPI、多旋转 0/180 择优 + 二值化去噪，专取「Số (No.)」号码。
    返回 (号码 or None, 依据文本)。"""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return None, ''
    ext = os.path.splitext(path)[1].lower()
    imgs = []
    try:
        if ext == '.pdf':
            from pdf2image import convert_from_path
            imgs = convert_from_path(path, dpi=400, first_page=1, last_page=1)
        else:
            imgs = [Image.open(path).convert('RGB')]
    except Exception:
        return None, ''
    if not imgs:
        return None, ''
    fallback = ''
    for rot in (0, 180):
        im = imgs[0]
        im = im.rotate(rot, expand=True) if rot else im
        w, h = im.size
        for frac in (0.25, 0.35):                          # 页眉：上 25%（套全 35% 兑底）
            base_crop = im.crop((0, 0, w, int(h * frac)))
            for crop in (base_crop, _binarize(base_crop)):
                cc = crop.convert('RGB')
                for psm in ('--psm 6', '--psm 4'):
                    try:
                        t = pytesseract.image_to_string(cc, lang='vie+eng', config=psm)
                    except Exception:
                        continue
                    if not t.strip():
                        continue
                    d = _pick_no(t)
                    if d and _kw_score(t) >= 2:        # 质量门：垃圾扫描件不认
                        return d, t
                    if _kw_score(t) >= 2:
                        fallback = fallback or t
    return None, fallback


# 扫描件 OCR 噪声下的发票号兜底（Q3）：`Số /moieAo): 00000223`（「(No.)」被认花）等变体。
# 只认两种高置信写法：① 日期行锚定（Ngày … năm … Số …）② 行内 Số 标签（排除账号/电话/税号行）。
_OCR_NO_BAD = re.compile(
    r'(?i)t[àa]i\s*kho[ảa]n|đi[ệe]n\s*tho[ạa]i|ng[âa]n\s*h[àa]ng|account|\btel\b|fax|'
    r'm[ãâa]\s*s[ốôo]\s*thu[ếêe]|hotline|website|tra\s*c[ứu]')


def _ocr_inv_no_spans(text):
    """扫描件 OCR 噪声下的发票号兜底：返回 [(start, end, number)]。
    号码**原样返回**：前导 0 全保留（00000223），不补零、不 strip。"""
    out, t = [], text or ''
    m = re.search(
        r'Ng[àa]y[^\n]{0,140}?n[ăa]m[^\n]{0,70}?S[ốo]\s*[^\n\d]{0,30}?[\)\]\}:：.]\s*'
        r'(\d{2,10})(?!\d)', t, re.I)
    if m:
        out.append((m.start(1), m.end(1), m.group(1)))
        return out
    pos = 0
    for ln in t.split('\n'):
        if not _OCR_NO_BAD.search(ln):
            m = re.search(r'(?:^|\s)S[ốo]\s*[\(\[{]?[^\n\d]{0,28}?[\)\]}]?\s*[:：.]\s*'
                          r'(\d{2,10})(?!\d)', ln, re.I)
            if m:
                out.append((pos + m.start(1), pos + m.end(1), m.group(1)))
                return out
        pos += len(ln) + 1
    return out


_RE_CHECKMARK = re.compile(r'[\u2713\u2714\u2611\u221a\u2705]|\(\s*[xX]\s*\)|\u2610\s*[xX]|\b[xX]\s*:?\s*$', re.M)


def is_official_einvoice(path, text=None):
    """Q8：判定「正式电子发票」（草稿件无税务机关代码、右下角无打钩）。
    返回 (bool, 依据)。无法确认时上层「照常写号 + 备注 cần kiểm tra thủ công」。
    判定：① 文本含「Mã của cơ quan thuế」；② 最后一页右下角（宽 25%×高 30%）有
    勾选笔画/记号（pdfplumber curves+lines+rects 计数；扫描件对右下调 OCR 找 ✓/☑/√/x）。"""
    t = text or ''
    if RE_TAXCODE.search(t):
        return True, 'tax-code'
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            last = pdf.pages[-1]
            if not t:
                lt = last.extract_text() or ''
                if RE_TAXCODE.search(lt):
                    return True, 'tax-code'
            x0, y0 = last.width * 0.75, last.height * 0.70
            box = last.crop((x0, y0, last.width, last.height))
            strokes = len(getattr(box, 'curves', []) or []) + len(getattr(box, 'rects', []) or [])
            if strokes >= 3 and RE_TAXCODE.search(t + (last.extract_text() or '')):
                return True, 'checkmark+tax-code'
            # 扫描件：右下调 OCR 找勾选记号
            if not (text or '').strip():
                try:
                    import pytesseract
                    from pdf2image import convert_from_path
                    im = convert_from_path(path, dpi=300, first_page=len(pdf.pages), last_page=len(pdf.pages))[0]
                    w, h = im.size
                    crop = im.crop((int(w * 0.75), int(h * 0.70), w, h))
                    if crop.width < 900:
                        f = 900.0 / crop.width
                        crop = crop.resize((int(crop.width * f), int(crop.height * f)))
                    ot = pytesseract.image_to_string(crop, lang='vie+eng', config='--psm 6')
                    if RE_TAXCODE.search(ot):
                        return True, 'tax-code(ocr)'
                    if _RE_CHECKMARK.search(ot):
                        return True, 'checkmark(ocr)'
                except Exception:
                    pass
            if strokes >= 6:
                return True, 'checkmark-lines(%d)' % strokes
    except Exception:
        pass
    return False, 'unconfirmed'


def _invoice_no_from_filename(base):
    """从文件名兜底取发票号：1C26TNT_00001044_3603695597.pdf → 00001044；
    优先 5-8 位数字组（排除 9-10 位税号、13 位流水号），再退到通配。"""
    groups = re.findall(r'\d{3,13}', base)
    for want in ((5, 8), (4, 4), (3, 3)):
        for g in groups:
            if want[0] <= len(g) <= want[1]:
                return g
    for pat in (r'_(\d{6,10})_', r'-(\d{6,10})-', r'([A-Z]{2}\d{6,9})(?=\D|$)'):
        m = re.search(pat, base)
        if m:
            return m.group(1)
    return None


def _generic_amounts(text):
    """从（可能是 OCR 噪声的）文本里收集所有「像金额」的数：千分位串或长数字。
    用于 OCR 版式标签残缺的情况 —— 由上层用「明细金额」做硬约束择一。"""
    out = []
    for m in re.finditer(r'\d{1,3}(?:[.,]\d{3}){1,}(?:[.,]\d{2})?|\d{6,}', text or ''):
        v = num(m.group(0))
        if v >= 100000 and v not in out:
            out.append(v)
    return out


def _invoice_no_from_text(text):
    """文本层兜底：最后一个 `Số/No: <5-9 位>`（发票号常在正文尾部出现）"""
    hits = re.findall(r'(?:S[ốo]|No\.?)\s*(?:\([^)]{0,20}\))?\s*[:：]?\s*(\d{5,9})\b', text or '')
    return hits[-1] if hits else None


def _statement_dates(path):
    """同目录汇总表（如 '22692315 VND.pdf'）→ {金额: ISO 日期}。
    用于发票 PDF 本身取不到日期时的补充（如 INTERTEK 版式的 Invoice date 列）。"""
    out = {}
    d = os.path.dirname(os.path.abspath(path))
    import glob as _glob
    for f in _glob.glob(os.path.join(d, '*.pdf')):
        b = os.path.basename(f)
        if f == path or not re.search(r'(VND|USD)\s*\.pdf$', b, re.I):
            continue
        try:
            import pdfplumber
            with pdfplumber.open(f) as pdf:
                txt = '\n'.join((pg.extract_text() or '') for pg in pdf.pages)
        except Exception:
            continue
        for m in re.finditer(r'(20\d{2})[/-](\d{1,2})[/-](\d{1,2})([^\n]{0,200}?)([\d][\d,]{6,})', txt):
            amt = num(m.group(5))
            if amt and amt not in out:
                out[amt] = f'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'
    return out


def _ocr_text(path, max_pages=None):
    """无文字层 PDF / 图片 → 本机 tesseract OCR（vie+eng）。失败返回空串。
    还处理一个常见坑：**扫描件方向不对**（180°/90°）→ 试多个旋转，按关键词命中数取最优。"""
    try:
        import pytesseract
    except ImportError:
        return ''

    KW = re.compile(r'(?i)h[óo]a\s*đ[ơo]n|t[ổo]ng|c[ộo]ng|s[ốo]|ti[ềe]n|thu[ếe]|ng[àa]y')

    def _best(im):
        best, bs = '', -1
        for rot in (0, 180, 90, 270):
            img = im.rotate(rot, expand=True) if rot else im
            t = pytesseract.image_to_string(img, lang='vie+eng')
            s = len(KW.findall(t))
            if s > bs:
                best, bs = t, s
            if s >= 4:
                break
        return best

    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.pdf':
            from pdf2image import convert_from_path
            imgs = convert_from_path(path, dpi=200)
            if max_pages:
                imgs = imgs[:max_pages]
            return '\n'.join(_best(im) for im in imgs)
        from PIL import Image
        return _best(Image.open(path).convert('RGB'))
    except Exception:
        return ''


def parse_pdf(path, engine_result=None):
    """解析一个 PDF → 发票列表（可能多张）。engine_result 为第三方引擎结果（可选，仅作兜底）。

    优先级：确定性解析（A/B 版式） > 页眉定向 OCR（扫描件） > 引擎结果 > 文件名兜底（左补 0）。
    """
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            raw = '\n'.join((pg.extract_text() or '') for pg in pdf.pages)
    except Exception:
        raw = ''
    _scanned = False
    # 文字层过少（扫描件/拍照件）→ OCR 兜底
    if len(re.sub(r'\s', '', raw)) < 80 and os.path.splitext(path)[1].lower() in ('.pdf', '.jpg', '.jpeg', '.png', '.tif', '.tiff'):
        # 文件名已明确是合同/订单/验收单等非发票文档 → 跳过 OCR（省时；发票名含「发票/HÓA ĐƠN/1C26…」仍会 OCR）
        _bn = os.path.basename(path)
        if _NON_INV_NAME.search(_bn) and not _INV_NAME.search(_bn):
            return []
        _scanned = True
        ocr = _ocr_text(path)
        if ocr.strip():
            raw = ocr
    text = clean_text(raw)
    base = os.path.basename(path)
    invs = _vn_invoices(text, path) or _intertek_invoice(text, path, text)
    if invs:
        sname, smst, bmsts = _seller_global(text)
        dg = extract_date(raw, text)
        need = [iv for iv in invs if not iv.get('invoice_date')]
        smap = _statement_dates(path) if need else {}
        for iv in invs:
            if not iv.get('vendor_name'):
                iv['vendor_name'] = sname
            if not iv.get('vendor_tax_code') or iv.get('vendor_tax_code') in bmsts:
                iv['vendor_tax_code'] = smst
            if not iv.get('invoice_date'):
                # Daryl 2026-10-07：以**发票 PDF 自身**为准，汇总表只做最后兑底
                iv['invoice_date'] = dg or smap.get(int(iv.get('total_amount') or 0))
                if iv['invoice_date'] and not dg:
                    iv['_date_src'] = 'statement'
            # Q3 号码来源三分类：body（文本层正文）/ ocr-header（扫描件 OCR）/ filename（文件兜底）
            if not iv.get('_num_src') or iv.get('_num_src') not in ('filename', 'ocr-header'):
                iv['_num_src'] = 'ocr-header' if _scanned else 'body'
            if iv.get('invoice_number'):
                iv.pop('_need_check_no', None)
            _mark_official(iv, path, raw, text, _scanned)
        return invs

    if NON_INVOICE_HINT.search(base):
        return []

    # 扫描件：先做「页眉定向 OCR」（仅页首 25% + 高 DPI），专取 Số (No.) —— 比全页 OCR 可靠
    hdr_no, hdr_txt = ('', '')
    if _scanned:
        try:
            hdr_no, hdr_txt = ocr_header_invoice_no(path)
        except Exception:
            hdr_no, hdr_txt = ('', '')

    # 引擎兜底：有金额但缺发票号 → 用页眉 OCR / 文件名补
    if engine_result and (engine_result.get('total_amount') or 0) > 0:
        e = dict(engine_result)
        e.setdefault('_src', 'engine')
        if not e.get('invoice_number'):
            if hdr_no:
                e['invoice_number'], e['_num_src'] = hdr_no, 'ocr-header'
            else:
                # 再修正 §2：读不出 → 不补零，写文件名兜底值 + 备注待核
                e['invoice_number'] = _invoice_no_from_filename(base) or _invoice_no_from_text(text)
                e['_num_src'] = 'filename'
                e['_need_check_no'] = True
        e['_filename_fallback'] = True
        e['_cands'] = [int(e.get('total_amount') or 0)]
        e.setdefault('_currency', 'VND')
        _mark_official(e, path, raw, text, _scanned)
        return [e] if e.get('invoice_number') else []
    # 兑底：OCR 版式标签残缺 → 给通用金额候选，由上层用明细金额仲裁
    amts = _generic_amounts(text)
    if amts:
        sname, smst, _bm = _seller_global(text)
        if hdr_no:
            _no, _src, _chk = hdr_no, 'ocr-header', False
        elif _invoice_no_from_text(text):
            # 扫描件正文 OCR 已读出号码（如 `Số (No.): 00000090`）→ 原样保留前导 0
            _no, _src, _chk = _invoice_no_from_text(text), 'ocr-header', False
        else:
            # 正文读不出 → 不补零，用文件名兜底值 + 备注待核
            _no = _invoice_no_from_filename(base) or ''
            _src, _chk = 'filename', bool(_no)
        rec = dict(invoice_number=_no,
                   invoice_serial=None,
                   invoice_date=extract_date(raw, text),
                   total_amount=max(amts), _cands=amts,
                   vendor_name=sname, vendor_tax_code=smst,
                   line_items=[], _src='generic',
                   _num_src=_src, _need_check_no=_chk, _currency='VND')
        _mark_official(rec, path, raw, text, _scanned)
        return [rec]
    return []


def _mark_official(iv, path, raw, text, scanned=False):
    """Q8：标注是否「正式电子发票」。
    口径（规格 §1.1）：**只对「无文本层 → 走 OCR」的发票**做该判定（文本层发票不参与）；
    无法确认（False）→ 号码照填 + 上层加备注待人工核；文本层发票未命中税代码 → 置 None（不加备注）。"""
    try:
        found = bool(RE_TAXCODE.search(raw or text or ''))
        if not scanned:
            iv['_official'] = True if found else None
            iv['_official_src'] = 'tax-code' if found else 'n/a(text-layer)'
            return iv
        ok, why = is_official_einvoice(path, raw or text)
    except Exception:
        ok, why = False, 'error'
    iv['_official'] = bool(ok)
    iv['_official_src'] = why
    return iv
