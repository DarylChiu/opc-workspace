# -*- coding: utf-8 -*-
"""
华特经营模式 · 报价税负测算 v3.1（2026-10-29）
沿用 Daryl 20261022 表口径，补「销售对象」维度，一个 Sheet 看完全部经营模式。
分组：出口（3 种采购方式）｜内销（3 种采购方式），每组各 3 类材料。
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = "deliverables/越南华特经营模式-报价税负测算-v3-20261029.xlsx"
FONT = "微软雅黑"
DARK, ACCENT, LIGHT, GREY = "1F3864", "2E5C8A", "D9E2F3", "F2F2F2"
GREEN, AMBER, RED, WHITE, EDIT = "C6EFCE", "FFEB9C", "FFC7CE", "FFFFFF", "FFF2CC"
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

MAT = [
    ("纱线", 0.1745, 0.03),
    ("胚布", 0.0, 0.12),
    ("成品布", 0.0, 0.12),
]

# (采購方式, 报关类型, 核销, 是否计反倾销, 是否计关税, 供应商性质)
EXPORT_WAYS = [
    ("保税进口（SXXK）", "E31", "必核销", 0, 0, "境外 / 越南 EPE（保税）"),
    ("一般贸易进口", "A12", "记录", 1, 1, "境外 / 越南 EPE"),
    ("本地采购（自非EPE）", "无", "记录", 0, 0, "越南境内非 EPE"),
]
DOMESTIC_WAYS = [
    ("本地采购（自非EPE）", "无", "记录", 0, 0, "越南境内非 EPE"),
    ("一般贸易进口", "A12", "记录", 1, 1, "境外 / 越南 EPE"),
    ("保税进口 → 转内销", "补税后 B11 / A12", "核销后转内销", 1, 1, "境外 / 越南 EPE（保税）"),
]

HDR = ["原材料", "采购方式", "供应商性质", "采购金额（USD）", "反倾销率", "进口关税率", "入库成本（USD）",
       "进口VAT率", "进口VAT（USD）", "进口VAT处理", "报关类型", "平衡账册核销",
       "销项VAT率", "销项VAT（USD）", "不可退税负成本", "税负成本率", "每USD100采购的税负"]
COLW = {"A": 9, "B": 21, "C": 22, "D": 13, "E": 10, "F": 10, "G": 13, "H": 10, "I": 13, "J": 13,
        "K": 17, "L": 15, "M": 10, "N": 12, "O": 14, "P": 11, "Q": 13}
NC = len(HDR)

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "经营模式税负测算"
for c, w in COLW.items():
    ws.column_dimensions[c].width = w

# 标题
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=NC)
c = ws.cell(row=1, column=1, value="越南华特 · 经营模式税负测算（出口 3 种 × 内销 3 种 × 材料 3 类 = 18 个模式）")
c.font = Font(name=FONT, size=13, bold=True, color=WHITE)
c.fill = PatternFill("solid", fgColor=DARK)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[1].height = 26

ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=NC)
c = ws.cell(row=2, column=1, value=(
    "税负成本 ＝ 反倾销 ＋ 进口关税（不可退，进成本）；进口VAT 出口可退、内销可抵，不计成本只占现金流；销项VAT 为价外税由客户承担。"
    "　黄色格＝可改（采购金额/税率），改一处全表联动。　每 USD 采购额口径，售价另计。　2026-10-29 v3.1"))
c.font = Font(name=FONT, size=8, italic=True, color="595959")
c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
ws.row_dimensions[2].height = 22

r = 3
for i, v in enumerate(HDR, start=1):
    c = ws.cell(row=r, column=i, value=v)
    c.font = Font(name=FONT, size=8.5, bold=True, color=WHITE)
    c.fill = PatternFill("solid", fgColor=DARK)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = BORDER
ws.row_dimensions[r].height = 36

r = 4


def group(row, text):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=NC)
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(name=FONT, size=9.5, bold=True, color=WHITE)
    c.fill = PatternFill("solid", fgColor=ACCENT)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    for i in range(1, NC + 1):
        ws.cell(row=row, column=i).border = BORDER
    ws.row_dimensions[row].height = 19


def make_row(row, mat, ad, duty, way, customs, woff, use_ad, use_duty, sup, sell_vat, ivat_treat):
    ad_r = ad * use_ad
    duty_r = duty * use_duty
    vals = {
        1: mat, 2: way, 3: sup, 4: 1000, 5: ad_r, 6: duty_r,
        7: f"=D{row}*(1+E{row}+F{row})",
        8: 0.08, 9: f"=G{row}*H{row}", 10: ivat_treat,
        11: customs, 12: woff, 13: sell_vat,
        14: f"=G{row}*M{row}",
        15: f"=D{row}*(E{row}+F{row})",
        16: f"=IFERROR(O{row}/D{row},0)",
        17: f"=IFERROR(O{row}/D{row}*100,0)",
    }
    for col in range(1, NC + 1):
        c = ws.cell(row=row, column=col, value=vals[col])
        c.border = BORDER
        c.font = Font(name=FONT, size=8.5, bold=(col == 1))
        c.alignment = Alignment(horizontal="left" if col in (1, 2, 3, 10, 11, 12) else "right",
                                vertical="center", wrap_text=True)
        if col in (4, 5, 6):
            c.fill = PatternFill("solid", fgColor=EDIT)
        if col in (7, 9, 14, 15, 17):
            c.number_format = "#,##0.00"
        if col in (5, 6, 8, 13, 16):
            c.number_format = "0.00%"
    zero = (ad_r + duty_r) == 0
    c16 = ws.cell(row=row, column=16)
    c16.font = Font(name=FONT, size=9, bold=True)
    c16.fill = PatternFill("solid", fgColor=GREEN if zero else AMBER)
    ws.row_dimensions[row].height = 23
    return row + 1


group(r, "一、出口（销售对象：境外客户 / 越南 EPE）—— 保税进口最省，税负成本为 0")
r += 1
for mat, ad, duty in MAT:
    for way, customs, woff, ua, ud, sup in EXPORT_WAYS:
        r = make_row(r, mat, ad, duty, way, customs, woff, ua, ud, sup, 0.0, "可退")

group(r, "二、内销（销售对象：越南本地客户）—— 料件来源决定税负，本地采购为 0")
r += 1
for mat, ad, duty in MAT:
    for way, customs, woff, ua, ud, sup in DOMESTIC_WAYS:
        r = make_row(r, mat, ad, duty, way, customs, woff, ua, ud, sup, 0.08, "可抵")

# 结论
r += 1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NC)
c = ws.cell(row=r, column=1, value="结论（选模式看这里）")
c.font = Font(name=FONT, size=10, bold=True, color=WHITE)
c.fill = PatternFill("solid", fgColor=ACCENT)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[r].height = 20
r += 1

concl = [
    ("出口", "保税进口（SXXK）｜税负成本 0", "一般贸易进口要多付 20.45%（纱线）／12%（布类），且不可退", "→ 出口订单优先走 E31 保税，前提是能核销"),
    ("内销", "本地采购｜税负成本 0", "一般贸易进口 = 20.45%（纱线）／12%（布类）；保税料件转内销补税后同样成本，还多一道手续", "→ 内销优先本地采购；保税料件不要流入内销"),
    ("共同", "反倾销是最贵的单项", "纱线按出口商档位 3.57%–17.45%，最高与最低差 13.9 个点——比谈价格更值钱的是核 C/O 与出口商名单", "→ 每批进口前核原产地与档位"),
]
for tag, key, diff, act in concl:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NC)
    c = ws.cell(row=r, column=1, value=f"【{tag}】{key}　｜　差距：{diff}　｜　{act}")
    c.font = Font(name=FONT, size=9)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
    ws.row_dimensions[r].height = 26
    r += 1

r += 1
foot = [
    "⚠️ 待核（直接影响上表数字，核实后改黄格即可）：① 布类反倾销适用范围未定，现按 0 计；② 关税 3%／12% 为 2023 口径，须按具体 HS 重核；③ 纱线反倾销取最高档 17.45%，实际按出口商档位 3.57%–17.45%；④ 自 EPE 视同进口未列入（报关类型待关务确认）；⑤ CIT 未纳入（按标准 20% 表述，10% 需优惠凭证）。",
    "说明：进口VAT 按入库成本×8% 计。出口情形可申请退税、内销情形可抵扣，故不计入成本；销项VAT（内销 8%）为价外税由客户承担，仅占现金流。保税转内销须先补关税与反倾销，故成本等同一般贸易。",
]
for t in foot:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NC)
    c = ws.cell(row=r, column=1, value=t)
    c.font = Font(name=FONT, size=7.5, color="C00000" if t.startswith("⚠️") else "595959")
    c.alignment = Alignment(horizontal="left", vertical="top", indent=1, wrap_text=True)
    ws.row_dimensions[r].height = 32
    r += 1

ws.freeze_panes = "D4"
ws.sheet_view.showGridLines = False
ws.page_setup.orientation = "landscape"
ws.page_setup.paperSize = ws.PAPERSIZE_A3
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 1
ws.print_area = f"A1:{get_column_letter(NC)}{r-1}"
ws.print_title_rows = "3:3"

wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("saved", OUT, "last row", r - 1)
