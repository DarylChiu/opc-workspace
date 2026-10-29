# -*- coding: utf-8 -*-
"""华特经营模式 · 一览表（单 Sheet，一页看完）v2 2026-10-29"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = "deliverables/华特经营模式一览-单表-v2-20261029.xlsx"
FONT = "微软雅黑"
DARK, ACCENT, LIGHT, GREY = "1F3864", "2E5C8A", "D9E2F3", "F2F2F2"
GREEN, AMBER, RED, WHITE = "C6EFCE", "FFEB9C", "FFC7CE", "FFFFFF"
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

SALES = [
    ("S1-01", "离境出口", "Huatex → 境外客户（买方＝收货方，货实际离境）", "VAT 0%", "出口报关（一般贸易）",
     "无真实收汇或第三方代付 → 0% 与退税双双被拒", "✅ 推荐·最标准", "g"),
    ("S1-02", "四方·收货＝EPE", "境外A销售｜Huatex 供货｜境外C购买｜越南EPE收货", "VAT 0%", "E62 就地出口＋EPE就地进口",
     "发票开给 EPE 或 E62 不进核销 → 打内销／补进口税", "✅ 推荐·最干净", "g"),
    ("S1-03", "四方·收货＝本地买断", "境外买方｜Huatex 供货｜越南本地企业买断收货", "VAT 0%", "E62＋收货方办就地进口",
     "五条任一踩线即打内销：票开收货方／收货方付款／无指定交货条款／买方仅通道／非真实买断", "⚠️ 高风险·凭证最严", "a"),
    ("S1-04", "四方·收货＝本地代工", "境外买方｜Huatex 供货｜越南代工厂收货加工（货权不转移）", "VAT 0%", "E62＋加工 nhập gia công 就地进口",
     "被认定买断 → 代工厂补税；出口后 15 天内未通报 Mẫu 22 → 免税失效", "🟡 可用·须加工合同", "a"),
    ("S1-05", "买方即 EPE（直供）", "Huatex → 越南 EPE（买方＝收货方）", "VAT 0%", "E62＋EPE 就地进口",
     "货未真实进入非关税区 → 0% 不成立，全额按内销 8%", "✅ 推荐·最简单", "g"),
    ("S1-06", "买方EPE＋本地收货", "EPE 买入｜本地企业收货（货从不进非关税区）", "不适用", "无法报关",
     "票货分离／过票、无证进口（行政甚至刑事风险）", "❌ 不适用", "r"),
    ("S1-07", "内销", "Huatex → 越南本地企业（买方＝收货方）", "VAT 8%", "无需报关",
     "保税料件未补税即内销；境内交易外币结算不合规", "✅ 常规内销", "g"),
    ("S1-08", "结构 A（买方本地＋收货EPE）", "Huatex 内销开 8% 给 C → C 报就地出口 → EPE 收货", "VAT 8%", "Huatex 不报关；C 报 E62",
     "C 无出口资质则报关链断裂；放弃 0% 多占 8% 现金流", "✅ 推荐·报关链最对齐", "g"),
    ("S1-09", "结构 B（买方本地＋收货EPE）", "Huatex 直接 E62，买方须改为境外实体、C 退出链条", "VAT 0%", "E62＋EPE 就地进口",
     "四层全开票 → 报关链对不上商业链，必有一层过票", "⚠️ 待关务确认", "a"),
]

PURCHASE = [
    ("P1-01", "纱线·本地采购", "越南境内非 EPE 纱厂", "VAT 8%（可抵）", "无",
     "供应商若为 EPE/保税则不能开 8% 发票", "✅ 内销首选", "g"),
    ("P1-02", "纱线·一般贸易进口", "境外供应商（中国等）", "关税约 3%＋反倾销 3.57%–17.45%", "一般贸易进口",
     "反倾销不可退；C/O 不全可能被套最高档 17.45%", "🟡 内销时慎用", "a"),
    ("P1-03", "纱线·保税 SXXK", "境外供应商（保税）", "0（复出口不征）", "保税进口＋核销配对",
     "转内销未先补税＝重大稽查风险；单耗不平 → 补税＋滞纳金", "✅ 出口首选", "g"),
    ("P1-04", "纱线·自 EPE 采购", "越南境内 EPE 企业", "视同进口征关税＋VAT 8%", "就地进口",
     "报关类型选错（如误用 A42）会被追税", "⚠️ 待关务确认", "a"),
    ("P2-01", "胚布·本地采购", "越南境内非 EPE 织造厂", "VAT 8%（可抵）", "无",
     "本地货源规格与产能是否满足（部分需进口）", "✅ 内销首选", "g"),
    ("P2-02", "胚布·一般贸易进口", "境外供应商（中国等）", "关税约 12%＋反倾销待核", "一般贸易进口",
     "关税刚性进成本；进口后仅染色再内销涉工业区/执照问题", "🟡 待核", "a"),
    ("P2-03", "胚布·进料加工/保税", "境外供应商（进料加工）", "0（复出口不征）", "手册＋进口＋核销",
     "保税胚布染色加工后内销＝违反工业区规定/投资执照（高危）", "✅ 出口首选·内销禁用", "g"),
    ("P2-04", "胚布·自 EPE 采购", "越南境内 EPE 企业", "视同进口征关税＋VAT 8%", "就地进口",
     "报关类型选择错误风险（同 P1-04）", "⚠️ 待关务确认", "a"),
    ("P3-01", "成品布·本地采购", "越南境内染整/织造厂", "VAT 8%（可抵）", "无",
     "单价最贵（含上游利润），但税负最轻、周期最短", "✅ 内销首选", "g"),
    ("P3-02", "成品布·一般贸易进口", "境外供应商（中国等）", "关税约 12%＋VAT 先缴", "一般贸易进口",
     "关税不可退，税负最刚性；纯贸易转售毛利最薄", "⚠️ 税负最重", "r"),
    ("P3-03", "成品布·保税进口", "境外供应商（保税）", "0（复出口不征）", "保税进口＋核销配对",
     "无实质加工直接保税转售，海关可能质疑保税适用性", "⚠️ 待关务确认", "a"),
    ("P4-01", "辅料／化学品·本地采购", "越南境内供应商", "VAT 8%（可抵）", "无",
     "供应商资质与 MSDS 合规；出口退税需按单耗归集", "✅ 常规", "g"),
]

COLORS = {"g": GREEN, "a": AMBER, "r": RED}
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "经营模式一览"

# ---- 标题 ----
ws.merge_cells("A1:H1")
c = ws["A1"]
c.value = "越南华特经营模式一览（销售出货 9 种｜采购入库 13 种）"
c.font = Font(name=FONT, size=14, bold=True, color=WHITE)
c.fill = PatternFill("solid", fgColor=DARK)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[1].height = 28

ws.merge_cells("A2:H2")
c = ws["A2"]
c.value = ("判断口径：VAT 率只看两件事——发票开给谁、货有没有进非关税区，不看最终客户是谁。"
          "｜真正吃利润的是进口端关税与反倾销（不可退）＋保税料件转内销补税，VAT 可抵只是现金流。"
          "｜日期 2026-10-29｜编制 Balance")
c.font = Font(name=FONT, size=8, italic=True, color="595959")
c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
ws.row_dimensions[2].height = 22

# ---- 表头 ----
HDR = ["编号", "经营模式", "交易结构 / 采购渠道", "税负", "报关类型", "主要风险 / 红线", "结论建议"]
COLW = {"A": 7, "B": 19, "C": 40, "D": 17, "E": 21, "F": 42, "G": 17}
for col, w in COLW.items():
    ws.column_dimensions[col].width = w

r = 3


def group(row, text):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(name=FONT, size=9.5, bold=True, color=WHITE)
    c.fill = PatternFill("solid", fgColor=ACCENT)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    for i in range(1, 8):
        ws.cell(row=row, column=i).border = BORDER
    ws.row_dimensions[row].height = 18


def hdr(row):
    for i, v in enumerate(HDR, start=1):
        c = ws.cell(row=row, column=i, value=v)
        c.font = Font(name=FONT, size=8.5, bold=True, color=DARK)
        c.fill = PatternFill("solid", fgColor=LIGHT)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDER
    ws.row_dimensions[row].height = 20


def row_out(row, vals, flag, h=26):
    for i, v in enumerate(vals, start=1):
        c = ws.cell(row=row, column=i, value=v)
        c.font = Font(name=FONT, size=8.5, bold=(i == 1))
        c.alignment = Alignment(horizontal="center" if i in (1,) else "left",
                                vertical="center", wrap_text=True)
        c.border = BORDER
        if i == 7:
            c.fill = PatternFill("solid", fgColor=COLORS[flag])
            c.font = Font(name=FONT, size=8.5, bold=True)
    ws.row_dimensions[row].height = h


hdr(r); r += 1
group(r, "一、销售与出货（9 种）"); r += 1
for mid, name, struct, tax, customs, risk, concl, flag in SALES:
    row_out(r, [mid, name, struct, tax, customs, risk, concl], flag)
    r += 1

group(r, "二、采购与入库（13 种 = 4 类材料 × 采购方式）"); r += 1
for mid, name, struct, tax, customs, risk, concl, flag in PURCHASE:
    row_out(r, [mid, name, struct, tax, customs, risk, concl], flag)
    r += 1

# ---- 脚注 ----
foot = [
    "图例：绿＝推荐／低风险　黄＝可用但需条件　红＝不适用或税负最重。",
    "⚠️ 关税税率沿用 2023 口径（纱线约 3%、布类约 12%），2026 现行 MFN 须按具体 HS 逐项重核后方可用于报价；"
    "CIT 按标准税率 20% 表述（参数表 10% 需优惠凭证）；反倾销按出口商档位取值，须逐笔核 C/O。",
]
for t in foot:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=7)
    c = ws.cell(row=r, column=1, value=t)
    c.font = Font(name=FONT, size=7.5, color="C00000" if t.startswith("⚠️") else "595959")
    c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True, indent=1)
    ws.row_dimensions[r].height = 16 if not t.startswith("⚠️") else 24
    r += 1

# ---- 打印：A3 横向，压成一页 ----
ws.freeze_panes = "C4"
ws.sheet_view.showGridLines = False
ws.page_setup.orientation = "landscape"
ws.page_setup.paperSize = ws.PAPERSIZE_A3
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 1
ws.print_area = f"A1:{get_column_letter(7)}{r-1}"
ws.print_title_rows = "3:4"

wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("saved", OUT, "rows", r - 1)
