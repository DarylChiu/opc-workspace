#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_bank_book_template.py — 银行会计「每日记账」Excel 模板生成器

目标（Daryl 2026-10-05）: 用费用报销 MVP 的 OCR 能力，产出方便银行会计每日记账的 Excel。
- 模式 1（空模板）:   python3 scripts/gen_bank_book_template.py
- 模式 2（OCR 填充）: python3 scripts/gen_bank_book_template.py --ocr <文件...> [--dept 财务部]
- 可选: --out <xlsx路径>  --bank "VCB-0071000xxxxx"  --no-example

工作簿 5 个 Sheet
  ① 使用说明      流程 / 口径 / 复核要求
  ② 记账凭证      ★主表★ 一行一条分录（BIP 兼容 + 银行/审计扩展列），带下拉校验与借贷平衡校验
  ③ 单据台账      一行一张原始单据（OCR 结果落点，便于对账与查漏）
  ④ 字典          科目（越南 TT200/2014）/ 费用类别 / 币种 / 状态 / 银行账户 / 部门
  ⑤ OCR留痕       每个文件的 OCR 方式/语言/长度/内容摘要哈希（审计链）

口径（与 expense_mvp v3.0 对齐）
  科目体系 = 越南 Thông tư 200/2014/TT-BTC：1121 银行存款(VND) / 1122 外币存款 /
             1111 现金 / 1331 进项税 / 641 销售费用 / 642 管理费用 / 627 生产费用
  发票类型 = HÓA ĐƠN GTGT（有进项税，可抵扣）vs HÓA ĐƠN BÁN HÀNG（无进项税，全额进费用）
  金额三位 = 税前 / 税额 / 价税合计；币种 VND / USD / CNY（外币行需填汇率）
"""
import os
import re
import sys
import json
import argparse
import hashlib
import datetime

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MVP = os.path.join(WS, 'expense_mvp')

# ═══════════════ 字典 ═══════════════
ACCOUNTS = [
    ("1121", "Tiền gửi ngân hàng (VND)", "银行存款-越南盾", "资产"),
    ("1122", "Tiền gửi ngân hàng (ngoại tệ)", "银行存款-外币", "资产"),
    ("1111", "Tiền mặt (VND)", "库存现金", "资产"),
    ("1331", "Thuế GTGT được khấu trừ", "进项税额-可抵扣", "资产"),
    ("1332", "Thuế GTGT hàng nhập khẩu", "进项税额-进口", "资产"),
    ("131", "Phải thu khách hàng", "应收账款", "资产"),
    ("331", "Phải trả cho người bán", "应付账款", "负债"),
    ("3331", "Thuế GTGT phải nộp", "应交增值税(销项)", "负债"),
    ("3334", "Thuế TNDN", "应交企业所得税", "负债"),
    ("3335", "Thuế TNCN", "应交个人所得税", "负债"),
    ("334", "Phải trả người lao động", "应付职工薪酬", "负债"),
    ("141", "Tạm ứng", "其他应收款-备用金", "资产"),
    ("242", "Chi phí trả trước", "长期待摊/预付费用", "资产"),
    ("152", "Nguyên liệu, vật liệu", "原材料", "资产"),
    ("153", "Công cụ, dụng cụ", "工具用具", "资产"),
    ("156", "Hàng hóa", "库存商品", "资产"),
    ("211", "Tài sản cố định hữu hình", "固定资产", "资产"),
    ("627", "Chi phí sản xuất chung", "制造费用(生产)", "费用"),
    ("632", "Giá vốn hàng bán", "主营业务成本", "费用"),
    ("635", "Chi phí tài chính", "财务费用(含银行手续费)", "费用"),
    ("641", "Chi phí bán hàng", "销售费用", "费用"),
    ("642", "Chi phí quản lý doanh nghiệp", "管理费用", "费用"),
    ("811", "Chi phí khác", "营业外支出", "费用"),
    ("515", "Doanh thu hoạt động tài chính", "财务收益(利息收入)", "收入"),
    ("711", "Thu nhập khác", "营业外收入", "收入"),
    ("511", "Doanh thu bán hàng", "主营业务收入", "收入"),
]
EXPENSE_TYPES = ["差旅费-住宿", "差旅费-交通", "差旅费-补贴", "业务招待费", "办公费",
                 "通讯费", "培训费", "会议费", "水电费", "租金", "运输费", "服务费-检测",
                 "银行手续费", "利息支出", "采购-原材料", "采购-设备", "其他"]
CURRENCIES = ["VND", "USD", "CNY"]
DIRECTIONS = ["付款", "收款", "手续费", "利息收入", "银行间转账", "结汇/购汇"]
STATUSES = ["待复核", "已复核", "已入账", "作废"]
DOC_TYPES = ["HÓA ĐƠN GTGT(增值税票)", "HÓA ĐƠN BÁN HÀNG(销售票)", "收据", "Debit note",
             "银行回单", "银行对账单", "其他"]
VOUCHER_WORDS = ["记", "银收", "银付", "银转"]
DEPARTMENTS = ["财务部", "行政部", "人事部", "采购部", "销售部", "市场部", "生产部", "管理层"]

# ═══════════════ 列定义 ═══════════════
VOUCHER_COLS = [
    ("序号", 6), ("日期", 12), ("凭证字", 8), ("凭证号", 11), ("摘要", 40),
    ("科目编码", 12), ("科目名称", 30), ("借方金额", 15), ("贷方金额", 15),
    ("部门", 10), ("项目/合同号", 14), ("币种", 8), ("原币金额", 15), ("汇率", 10),
    ("收付方向", 10), ("对方单位", 30), ("对方税号", 14), ("单据类型", 20),
    ("发票号", 12), ("发票序列号", 12), ("附件文件名", 26), ("OCR置信度", 10),
    ("复核状态", 10), ("备注", 34),
]
DOC_COLS = [
    ("序号", 6), ("单据日期", 12), ("单据类型", 22), ("对方单位", 34), ("对方税号", 14),
    ("币种", 8), ("含税金额", 15), ("税前金额", 15), ("税额", 13), ("税率", 8),
    ("发票号", 12), ("发票序列号", 12), ("费用类别", 14), ("科目编码", 12),
    ("附件文件名", 26), ("OCR置信度", 10), ("是否需复核", 11), ("复核原因", 30), ("关联凭证号", 12),
]
THIN = Side(style='thin', color='BFBFBF')
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def hdr_style(ws, ncols, row=1, fill='DDEBF7'):
    for c in range(1, ncols + 1):
        cell = ws.cell(row, c)
        cell.font = Font(bold=True, size=10)
        cell.fill = PatternFill('solid', fgColor=fill)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = BORDER


def write_table(ws, cols, rows, num_fmt_cols=(), date_cols=()):
    for i, (name, width) in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = width
        ws.cell(1, i, name)
    hdr_style(ws, len(cols))
    for r, row in enumerate(rows, 2):
        for c, val in enumerate(row, 1):
            cell = ws.cell(r, c, val)
            cell.border = BORDER
            cell.font = Font(size=10)
            cell.alignment = Alignment(vertical='top', wrap_text=(cols[c - 1][0] in ('摘要', '科目名称', '对方单位', '备注', '复核原因')))
            if c in num_fmt_cols:
                cell.number_format = '#,##0'
            if c in date_cols:
                cell.number_format = 'yyyy-mm-dd'
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f'A1:{get_column_letter(len(cols))}{max(2, len(rows) + 1)}'


def add_dv(ws, col_letter, source, first=2, last=500):
    dv = DataValidation(type='list', formula1=source, allow_blank=True, showDropDown=False)
    ws.add_data_validation(dv)
    dv.add(f'{col_letter}{first}:{col_letter}{last}')


# ═══════════════ OCR 填充 ═══════════════
def mst_from_raw(raw: str) -> str:
    """从 OCR 原文回填税号（OCR 常把数字排成 '0 3 1 4 3 4 1 4 2 7'）"""
    if not raw:
        return ''
    for pat in (r'Mã số thuế\s*\(Tax code\)\s*:?\s*([0-9][0-9 \-]{7,})',
                r'MST\s*:?\s*([0-9][0-9 \-]{7,})',
                r'Tax code\)\s*:?\s*([0-9][0-9 \-]{7,})'):
        m = re.search(pat, raw, re.I)
        if m:
            d = re.sub(r'[^0-9]', '', m.group(1))
            if 10 <= len(d) <= 14:
                return d
    return ''


def ocr_rows(files, dept='财务部', bank_acct=''):
    """跑 expense_mvp 的 OCR+分类，产出 (凭证行, 台账行, 留痕行)"""
    sys.path.insert(0, MVP)
    from ocr_engine import ocr_with_classify  # type: ignore

    v_rows, d_rows, t_rows = [], [], []
    for i, fp in enumerate(files, 1):
        try:
            r = ocr_with_classify(fp, department=dept)
        except Exception as ex:
            r = {'ok': False, 'error': f'{type(ex).__name__}: {ex}'}
        name = os.path.basename(fp)
        if not r.get('ok'):
            d_rows.append([i, '', '', '', '', '', '', '', '', '', '', '', '',
                           '', name, '', '是', f"OCR失败: {r.get('error','')}"[:30], ''])
            continue
        c = r['classification']
        e = c['extracted']
        ocr = r['ocr']
        txt = ocr.get('text', '') or ''
        t_rows.append([i, name, ocr.get('source_format', ''), ocr.get('language', ''),
                       ocr.get('text_length', 0), hashlib.sha1(txt.encode('utf-8')).hexdigest()[:12],
                       datetime.datetime.now().strftime('%Y-%m-%d %H:%M')])
        # 字段
        code = (c.get('expense_type_code') or '642-99').replace('*', '')
        etype = c.get('expense_type') or '其他'
        vendor = (e.get('vendor_name') or '').strip()
        tax = e.get('vendor_tax_code') or mst_from_raw(e.get('raw_text_snippet', ''))
        pretax = e.get('amount_pretax') or 0
        vat = e.get('vat_amount') or 0
        total = e.get('total_amount') or (pretax + vat)
        cur = e.get('currency') or 'VND'
        rates = e.get('vat_rates') or []
        rate = (f"{int(rates[0]*100)}%" if rates and rates[0] else '')
        inv, ser, date = e.get('invoice_number') or '', e.get('invoice_serial') or '', e.get('invoice_date') or ''
        conf = c.get('confidence') or 0
        needs = '是' if (c.get('needs_review') or conf < 0.7) else '否'
        reason = c.get('review_reason') or ('置信度<70%' if conf < 0.7 else '')
        vno = f'记-{i:04d}'
        summary = f"{etype} | {vendor[:32]}" + (f" | 发票{ser}-{inv}" if inv else '')
        credit_acct = '1122' if cur != 'VND' else '1121'
        credit_name = 'Tiền gửi ngân hàng (VND)' if cur == 'VND' else 'Tiền gửi ngân hàng (ngoại tệ)'
        note = []
        if needs == '是':
            note.append('⚠️需人工确认分类/字段')
        if not tax:
            note.append('税号缺失待补')
        elif e.get('vendor_tax_code'):
            pass
        else:
            note.append('税号取自OCR原文，待核')
        if not date:
            note.append('日期缺失待补')
        base = dict(direction='付款', department=dept, project='', currency=cur, rate=1 if cur == 'VND' else '',
                    vendor=vendor, tax=tax, dtype='HÓA ĐƠN GTGT(增值税票)' if vat > 0 else 'HÓA ĐƠN BÁN HÀNG(销售票)',
                    inv=inv, ser=ser, file=name, conf=round(conf, 2), status='待复核',
                    note='；'.join(note), date=date)
        # 借方：费用科目
        v_rows.append([0, base['date'], '记', vno, summary, code,
                       f"{code} - {etype}", pretax, '', dept, '', cur, total, base['rate'],
                       '付款', vendor, tax, base['dtype'], inv, ser, name, base['conf'], '待复核', base['note']])
        # 借方：进项税（仅 GTGT）
        if vat > 0:
            v_rows.append([0, base['date'], '记', vno, f"VAT {rate} | {vendor[:24]}", '1331',
                           '1331 - Thuế GTGT được khấu trừ (进项税)', vat, '', dept, '', cur, '', '',
                           '付款', vendor, tax, base['dtype'], inv, ser, name, base['conf'], '待复核', '进项税可抵扣'])
        # 贷方：银行
        v_rows.append([0, base['date'], '记', vno, summary, credit_acct, f"{credit_acct} - {credit_name}",
                       '', total, dept, '', cur, total, base['rate'], '付款', vendor, tax, base['dtype'],
                       inv, ser, name, base['conf'], '待复核', bank_acct])
        d_rows.append([i, base['date'], base['dtype'], vendor, tax, cur, total, pretax, vat, rate,
                       inv, ser, etype, code, name, base['conf'], needs, reason[:30], vno])
    for j, r in enumerate(v_rows, 1):
        r[0] = j
    return v_rows, d_rows, t_rows


def build(path, v_rows, d_rows, t_rows, blank_example=True, bank_acct=''):
    wb = openpyxl.Workbook()

    # ① 使用说明
    ws0 = wb.active
    ws0.title = '使用说明'
    ws0.column_dimensions['A'].width = 110
    lines = [
        "银行会计 · 每日记账 Excel 模板  v1（2026-10-05）",
        "",
        "【用途】把每日的银行收款/付款单据，整理成可直接记账（或导入 ERP）的凭证行 + 台账。",
        "",
        "【怎么用】",
        "  1) 把当天单据（发票/收据/Debit note/银行回单）发给 Balance → 走「费用报销 MVP OCR」",
        "  2) 得到本工作簿：Sheet「记账凭证」= 逐条分录（借方费用/进项税 + 贷方银行）",
        "     Sheet「单据台账」= 一行一张单据（对账、查漏用）",
        "     Sheet「OCR留痕」= 每个文件的 OCR 方式/语言/内容哈希（审计链，不可省）",
        "  3) 会计复核：核对金额三位（税前/税额/价税合计）与发票号、序列号、税号",
        "  4) 复核通过 → 把「复核状态」改为「已复核 / 已入账」",
        "",
        "【已内置的口径】",
        "  · 科目体系：越南 Thông tư 200/2014/TT-BTC（1121 越盾存款 / 1122 外币存款 / 1331 进项税 / 641 / 642 / 627…）",
        "  · 有 GTGT（增值税票）→ 进项税单列 1331；HÓA ĐƠN BÁN HÀNG（销售票/收据）→ 全额进费用",
        "  · 金额三位：税前金额 + 税额 = 价税合计（不合并，便于核对与抵扣）",
        "  · 外币（USD/CNY）：填「汇率」，原币金额×汇率 = 本币金额（VND 行汇率=1）",
        "",
        "【复核纪律（必须守）】",
        "  · 低置信度（<70%）或 needs_review=是 → 必须人工核对后才可入账，不得直接过账",
        "  · OCR 结果只是「草稿」：发票号/税号/金额必须与原件比对；原文留痕见 Sheet「OCR留痕」",
        "  · 借贷必须平衡：右上方有 SUM 校验（合计借方 / 合计贷方 / 差额），差额≠0 不得提交",
        "",
        "【列说明】记账凭证前 10 列与 voucher_gen 的 BIP 兼容 CSV 表头一致（日期/凭证字/摘要/科目编码/科目名称/借方金额/贷方金额/部门/项目/币种），",
        "后续列为本模板扩展（币种明细、对方单位/税号、发票号、附件、置信度、复核状态），便于对账与审计追溯。",
        "",
        f"【默认银行账户】{bank_acct or '（请在字典 Sheet「银行账户」列维护，凭证行可下拉选择）'}",
        "",
        "维护：Balance ⚖️ ｜ 依赖：expense_mvp（ocr_engine + classifier v3.0）",
    ]
    for i, t in enumerate(lines, 1):
        cell = ws0.cell(i, 1, t)
        cell.alignment = Alignment(wrap_text=False, vertical='center')
        if i == 1:
            cell.font = Font(bold=True, size=13)
        elif t.startswith('【'):
            cell.font = Font(bold=True, size=10)

    # ② 记账凭证
    ws1 = wb.create_sheet('记账凭证')
    example = []
    if blank_example and not v_rows:
        example = [
            [1, '2026-10-05', '银付', '记-0001', '业务招待费 | CÔNG TY TNHH NHÀ HÀNG SEND | 发票1C26MOO-838',
             '642-02', '642-02 - Chi phí QLDN (业务招待费)', 2666000, '', '财务部', '', 'VND', 2925360, 1,
             '付款', 'CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ NHÀ HÀNG SEND', '0314341427', 'HÓA ĐƠN GTGT(增值税票)',
             '838', '1C26MOO', 'fed6e4c631a6.pdf', 0.9, '待复核', '示例行：请核对原件后使用'],
            [2, '2026-10-05', '银付', '记-0001', 'VAT 10% | NHÀ HÀNG SEND', '1331',
             '1331 - Thuế GTGT được khấu trừ (进项税)', 259360, '', '财务部', '', 'VND', '', '',
             '付款', 'CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ NHÀ HÀNG SEND', '0314341427', 'HÓA ĐƠN GTGT(增值税票)',
             '838', '1C26MOO', 'fed6e4c631a6.pdf', 0.9, '待复核', '进项税可抵扣'],
            [3, '2026-10-05', '银付', '记-0001', '业务招待费 | CÔNG TY TNHH NHÀ HÀNG SEND | 发票1C26MOO-838',
             '1121', '1121 - Tiền gửi ngân hàng (VND)', '', 2925360, '财务部', '', 'VND', 2925360, 1,
             '付款', 'CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ NHÀ HÀNG SEND', '0314341427', 'HÓA ĐƠN GTGT(增值税票)',
             '838', '1C26MOO', 'fed6e4c631a6.pdf', 0.9, '待复核', '示例行：贷方=银行存款'],
        ]
    rows = v_rows or example
    write_table(ws1, VOUCHER_COLS, rows, num_fmt_cols=(8, 9, 13))
    for c in (8, 9, 13):
        for r in range(2, max(3, len(rows) + 2)):
            ws1.cell(r, c).number_format = '#,##0'
    n = len(rows)
    last = max(2, n + 1)
    ws1.cell(1, 26, '借贷平衡校验').font = Font(bold=True)
    ws1.cell(2, 26, '合计借方')
    ws1.cell(2, 27, f'=SUM(H2:H{last})').number_format = '#,##0'
    ws1.cell(3, 26, '合计贷方')
    ws1.cell(3, 27, f'=SUM(I2:I{last})').number_format = '#,##0'
    ws1.cell(4, 26, '差额(须=0)')
    ws1.cell(4, 27, f'=ROUND(SUM(H2:H{last})-SUM(I2:I{last}),0)').number_format = '#,##0'
    ws1.cell(4, 28, '≠0 说明分录不平，禁止提交').font = Font(size=9, color='C00000')
    add_dv(ws1, 'C', '=字典!$D$2:$D$5')
    add_dv(ws1, 'F', '=字典!$A$2:$A$60')
    add_dv(ws1, 'J', '=字典!$F$2:$F$20')
    add_dv(ws1, 'L', '=字典!$C$2:$C$4')
    add_dv(ws1, 'O', '=字典!$H$2:$H$8')
    add_dv(ws1, 'R', '=字典!$E$2:$E$9')
    add_dv(ws1, 'W', '=字典!$I$2:$I$6')

    # ③ 单据台账
    ws2 = wb.create_sheet('单据台账')
    write_table(ws2, DOC_COLS, d_rows, num_fmt_cols=(7, 8, 9))
    add_dv(ws2, 'C', '=字典!$E$2:$E$9')
    add_dv(ws2, 'F', '=字典!$C$2:$C$4')
    add_dv(ws2, 'M', '=字典!$B$2:$B$20')
    add_dv(ws2, 'Q', '=字典!$I$2:$I$6')

    # ④ 字典
    ws3 = wb.create_sheet('字典')
    ws3.cell(1, 1, '科目编码').font = Font(bold=True)
    ws3.cell(1, 2, '科目名称(VN)').font = Font(bold=True)
    ws3.cell(1, 3, '币种').font = Font(bold=True)
    ws3.cell(1, 4, '凭证字').font = Font(bold=True)
    ws3.cell(1, 5, '单据类型').font = Font(bold=True)
    ws3.cell(1, 6, '部门').font = Font(bold=True)
    ws3.cell(1, 7, '科目名称(CN)').font = Font(bold=True)
    ws3.cell(1, 8, '收付方向').font = Font(bold=True)
    ws3.cell(1, 9, '复核状态').font = Font(bold=True)
    ws3.cell(1, 11, '费用类别').font = Font(bold=True)
    ws3.cell(1, 12, '银行账户').font = Font(bold=True)
    for i, (code, vn, cn, kind) in enumerate(ACCOUNTS, 2):
        ws3.cell(i, 1, code)
        ws3.cell(i, 2, vn)
        ws3.cell(i, 7, cn)
    for i, v in enumerate(CURRENCIES, 2):
        ws3.cell(i, 3, v)
    for i, v in enumerate(VOUCHER_WORDS, 2):
        ws3.cell(i, 4, v)
    for i, v in enumerate(DOC_TYPES, 2):
        ws3.cell(i, 5, v)
    for i, v in enumerate(DEPARTMENTS, 2):
        ws3.cell(i, 6, v)
    for i, v in enumerate(DIRECTIONS, 2):
        ws3.cell(i, 8, v)
    for i, v in enumerate(STATUSES, 2):
        ws3.cell(i, 9, v)
    for i, v in enumerate(EXPENSE_TYPES, 2):
        ws3.cell(i, 11, v)
    ws3.cell(2, 12, bank_acct or '')
    for col, w in ((1, 12), (2, 40), (3, 8), (4, 10), (5, 26), (6, 10), (7, 28), (8, 12), (9, 10), (11, 16), (12, 24)):
        ws3.column_dimensions[get_column_letter(col)].width = w

    # ⑤ OCR留痕
    ws4 = wb.create_sheet('OCR留痕')
    cols = [("序号", 6), ("文件名", 34), ("OCR方式", 20), ("语言", 8), ("文本长度", 10),
            ("内容SHA1(前12)", 14), ("抽取时间", 18)]
    write_table(ws4, cols, t_rows)

    wb.save(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ocr', nargs='+', default=None, help='要 OCR 的文件（PDF/JPG/PNG）')
    ap.add_argument('--out', default=None)
    ap.add_argument('--dept', default='财务部')
    ap.add_argument('--bank', default='')
    ap.add_argument('--no-example', action='store_true')
    a = ap.parse_args()

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    dl = os.path.join(WS, 'deliverables')
    os.makedirs(dl, exist_ok=True)
    if a.ocr:
        v, d, t = ocr_rows(a.ocr, dept=a.dept, bank_acct=a.bank)
        out = a.out or os.path.join(dl, f'银行会计每日记账-OCR填充-{ts}.xlsx')
        build(out, v, d, t, blank_example=False, bank_acct=a.bank)
        print(f'✅ OCR 填充版: {out}')
        print(f'   单据 {len(d)} 张 | 凭证行 {len(v)} 条 | 留痕 {len(t)} 条')
    else:
        out = a.out or os.path.join(dl, f'银行会计每日记账-Excel模板-v1-{ts}.xlsx')
        build(out, [], [], [], blank_example=not a.no_example, bank_acct=a.bank)
        print(f'✅ 空模板: {out}')


if __name__ == '__main__':
    main()
