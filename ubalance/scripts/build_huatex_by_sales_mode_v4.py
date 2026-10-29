# -*- coding: utf-8 -*-
"""
华特经营模式 · 按销售模式逐个披露 v4（2026-10-29）
底表＝Daryl 20261022《报价测算》口径（反倾销/关税/入库成本/进口VAT/报关类型/平衡账册核销）
上区：9 个销售模式逐个披露（采购配置 + 税负 + 票流 + 单证 + 风险）
下区：采购方式 × 税负成本对照（原表口径，公式联动）
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = "deliverables/越南华特经营模式-按销售模式披露-v4-20261029.xlsx"
FONT = "微软雅黑"
DARK, ACCENT, LIGHT, GREY = "1F3864", "2E5C8A", "D9E2F3", "F2F2F2"
GREEN, AMBER, RED, WHITE, EDIT = "C6EFCE", "FFEB9C", "FFC7CE", "FFFFFF", "FFF2CC"
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

# ---------- 上区：销售模式 ----------
# 编号, 名称, 交易结构, 推荐采购, 反倾销, 关税, 入库系数, 进口VAT, 报关, 核销, 销项VAT, 发票开给谁, 单证, 风险, 错配代价, 结论, 色
SALES = [
    ("S1-01", "离境出口", "Huatex（卖方）→ 境外客户（买方＝收货方，货物实际离境）",
     "保税进口 SXXK", 0, 0, 1.000, "0（复出口不征）", "出口报关（E31 核销配对）", "必核销",
     0.0, "境外买方（不开给境内任何方）",
     "合同/PO、CI、PL、出口报关单、收汇水单、B/L",
     "无真实收汇或第三方代付 → 0% 与退税双双被拒",
     "改一般贸易进口：纱线 +20.45%／布类 +12%", "✅ 推荐·最标准", "g"),
    ("S1-02", "四方合同·收货＝EPE", "境外 A 销售｜Huatex 供货｜境外 C 购买｜越南 EPE 收货（E62）",
     "保税进口 SXXK", 0, 0, 1.000, "0（复出口不征）", "E62 就地出口（与 SXXK 核销配对）", "必核销＋E62 配对",
     0.0, "合同买方 C（境外）——绝不开给 EPE",
     "四方合同（含「买方书面指定交货第三方」）、0% 发票（备注交货地＋收货人）、CI/PL、E62 单、EPE 就地进口单、收汇水单",
     "发票开给 EPE／E62 不进核销 → 打内销或补进口税",
     "改一般贸易进口：纱线 +20.45%／布类 +12%", "✅ 推荐·结构最干净", "g"),
    ("S1-03", "四方合同·收货＝本地买断", "境外买方签约｜Huatex 供货｜越南本地企业买断收货，货权转移",
     "保税进口 SXXK", 0, 0, 1.000, "0（复出口不征）", "E62；收货方办就地进口", "必核销",
     0.0, "合同买方（境外）——不开给收货方",
     "四方合同、0% 发票、CI/PL、E62 单、收货方就地进口单、收货方缴税凭证",
     "五条任一踩线即打内销：票开收货方／收货方付款／无指定交货条款／买方仅通道／非真实买断",
     "改一般贸易进口：纱线 +20.45%／布类 +12%", "⚠️ 高风险·凭证最严", "a"),
    ("S1-04", "四方合同·收货＝本地代工", "境外买方签约｜Huatex 供货｜代工厂收货加工，货权不转移",
     "保税进口 SXXK", 0, 0, 1.000, "0（复出口不征）", "E62；代工厂按加工 nhập gia công 就地进口", "必核销",
     0.0, "合同买方（境外）",
     "四方合同、加工合同（证明货权不转移）、0% 发票、E62 单、Mẫu 22 通报（15 天内）",
     "被认定买断 → 代工厂补进口税与 VAT；未按期通报 Mẫu 22 → 免税失效",
     "改一般贸易进口：纱线 +20.45%／布类 +12%", "🟡 可用·须加工合同支撑", "a"),
    ("S1-05", "买方即 EPE（直供）", "Huatex（卖方）→ 越南 EPE（买方＝收货方）",
     "保税进口 SXXK", 0, 0, 1.000, "0（复出口不征）", "E62；EPE 办就地进口", "必核销",
     0.0, "越南 EPE（买方＝收货方）",
     "合同（注明交货至非关税区）、E62 单、EPE 就地进口单、收款凭证",
     "货未真实进入非关税区 → 0% 不成立，全额按内销 8%",
     "改一般贸易进口：纱线 +20.45%／布类 +12%", "✅ 推荐·最常见最简单", "g"),
    ("S1-06", "买方 EPE＋本地收货", "EPE 买入｜本地企业收货（货从不进非关税区）",
     "—（结构自相矛盾）", None, None, None, "—", "无法报关（EPE 无法办就地进口）", "—",
     None, "—（不存在合规开票方式）",
     "—",
     "票货分离／过票；本地企业无证进口（行政甚至刑事风险）",
     "—", "❌ 不适用", "r"),
    ("S1-07", "内销", "Huatex（卖方）→ 越南本地企业（买方＝收货方，非 EPE）",
     "本地采购（自非EPE）", 0, 0, 1.000, "8%（可抵）", "无需报关", "记录",
     0.08, "越南本地企业（买方）",
     "合同/PO、越南 VAT 发票（8%）、送货单、收款凭证",
     "保税料件未补税即内销；境内交易外币结算不合规",
     "改一般贸易进口：纱线 +20.45%／布类 +12%；保税料件转内销：补税后同一般贸易", "✅ 常规内销", "g"),
    ("S1-08", "结构 A（买方本地＋收货 EPE）", "Huatex 内销开 8% 给 C → C 报就地出口 → 越南 EPE 收货",
     "本地采购（自非EPE）", 0, 0, 1.000, "8%（可抵）", "Huatex 不报关；C 报 E62", "记录",
     0.08, "C（越南本地企业买方）",
     "Huatex↔C 合同、VAT 发票（8%）、送货单、C 侧出口报关单（供链条解释）",
     "C 无出口资质则报关链断裂，8% 白付；放弃 0% 多占 8% 现金流",
     "改一般贸易进口：纱线 +20.45%／布类 +12%", "✅ 推荐·报关链最对齐", "g"),
    ("S1-09", "结构 B（买方本地＋收货 EPE）", "Huatex 直接 E62，买方须改为境外实体、C 退出链条",
     "保税进口 SXXK", 0, 0, 1.000, "0（复出口不征）", "E62；EPE 办就地进口", "必核销",
     0.0, "境外买方（须重构合同主体）",
     "三方/四方合同（含指定交货条款）、0% 发票、E62 单、EPE 就地进口单、境外买方付款水单",
     "四层全开票 → 报关链对不上商业链，必有一层过票",
     "改一般贸易进口：纱线 +20.45%／布类 +12%", "⚠️ 待关务确认", "a"),
]

# ---------- 下区：采购方式对照（原表口径） ----------
MAT = [("纱线", 0.1745, 0.03), ("胚布", 0.0, 0.12), ("成品布", 0.0, 0.12)]
WAYS = [
    ("保税进口（SXXK）", "境外 / 越南 EPE（保税）", "E31", "必核销", 0, 0),
    ("一般贸易进口", "境外 / 越南 EPE", "A12", "记录", 1, 1),
    ("本地采购（自非EPE）", "越南境内非 EPE", "无", "记录", 0, 0),
    ("保税进口 → 转内销", "境外 / 越南 EPE（保税）", "补税后 B11/A12", "核销后转内销", 1, 1),
]

HDR1 = ["编号", "销售模式", "交易结构（卖方→买方｜收货方）", "推荐采购方式", "反倾销率", "进口关税率",
        "入库成本系数", "进口VAT", "报关类型", "平衡账册核销", "销项VAT率", "发票开给谁",
        "必备单证（核心）", "主要风险 / 红线", "采购方式错配的代价", "税负成本率", "结论"]
COLW = {"A": 8, "B": 21, "C": 34, "D": 15, "E": 9, "F": 9, "G": 10, "H": 13, "I": 24, "J": 15,
        "K": 9, "L": 22, "M": 36, "N": 36, "O": 26, "P": 10, "Q": 17}
NC = len(HDR1)

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "销售模式披露"
for c, w in COLW.items():
    ws.column_dimensions[c].width = w

ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=NC)
c = ws.cell(row=1, column=1, value="越南华特 · 按销售模式披露（9 个销售模式 × 采购配置 × 税负 × 票流 × 单证 × 风险）")
c.font = Font(name=FONT, size=13, bold=True, color=WHITE)
c.fill = PatternFill("solid", fgColor=DARK)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[1].height = 26

ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=NC)
c = ws.cell(row=2, column=1, value=(
    "底表口径沿用《报价测算》：入库成本＝采购额×(1+反倾销率+关税率)；进口VAT 出口可退、内销可抵，不计入成本；"
    "销项VAT 为价外税由客户承担。　税负成本率＝反倾销＋关税（不可退部分）。　2026-10-29 v4"))
c.font = Font(name=FONT, size=8, italic=True, color="595959")
c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
ws.row_dimensions[2].height = 22


def header_row(row, values, height=38):
    for i, v in enumerate(values, start=1):
        c = ws.cell(row=row, column=i, value=v)
        c.font = Font(name=FONT, size=8.5, bold=True, color=WHITE)
        c.fill = PatternFill("solid", fgColor=DARK)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDER
    ws.row_dimensions[row].height = height


header_row(3, HDR1, 40)

r = 4
for (mid, name, struct, buy, ad, duty, coeff, ivat, customs, woff, svat, inv, docs, risk, cost, concl, flag) in SALES:
    vals = [mid, name, struct, buy,
            ad if ad is not None else "—",
            duty if duty is not None else "—",
            coeff if coeff is not None else "—",
            ivat, customs, woff,
            svat if svat is not None else "—",
            inv, docs, risk, cost,
            0.0 if ad is not None else "—",
            concl]
    for col, v in enumerate(vals, start=1):
        c = ws.cell(row=r, column=col, value=v)
        c.border = BORDER
        c.font = Font(name=FONT, size=8, bold=(col in (1, 2)))
        c.alignment = Alignment(horizontal="center" if col in (1, 5, 6, 7, 11, 16) else "left",
                                vertical="center", wrap_text=True)
        if col in (5, 6, 11, 16):
            c.number_format = "0.00%"
        if col == 7:
            c.number_format = "0.000"
        if col == 17:
            c.fill = PatternFill("solid", fgColor={"g": GREEN, "a": AMBER, "r": RED}[flag])
            c.font = Font(name=FONT, size=8, bold=True)
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        if col == 16:
            c.fill = PatternFill("solid", fgColor=GREEN if ad is not None else RED)
            c.font = Font(name=FONT, size=8.5, bold=True)
    ws.row_dimensions[r].height = 46
    r += 1

# ---------- 下区 ----------
r += 1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NC)
c = ws.cell(row=r, column=1, value="采购方式 × 税负成本对照（底表口径，黄色格可改，改后全表联动）—— 销售模式选对采购方式，税负成本才能归零")
c.font = Font(name=FONT, size=10, bold=True, color=WHITE)
c.fill = PatternFill("solid", fgColor=ACCENT)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[r].height = 22
r += 1

HDR2 = ["原材料", "采购方式", "供应商性质", "采购金额（USD）", "反倾销率", "进口关税率", "入库成本（USD）",
        "进口VAT率", "进口VAT（USD）", "报关类型", "平衡账册核销", "税负成本（USD）", "税负成本率", "备注", "", "", ""]
header_row(r, HDR2, 34)
r += 1

start2 = r
for mat, ad_base, duty_base in MAT:
    for way, sup, customs, woff, ua, ud in WAYS:
        ad, duty = ad_base * ua, duty_base * ud
        vals = {
            1: mat, 2: way, 3: sup, 4: 1000, 5: ad, 6: duty,
            7: f"=D{r}*(1+E{r}+F{r})",
            8: 0.08, 9: f"=G{r}*H{r}", 10: customs, 11: woff,
            12: f"=D{r}*(E{r}+F{r})", 13: f"=IFERROR(L{r}/D{r},0)",
            14: ("复出口不征，税负归零" if way.startswith("保税进口（") else
                 "关税＋反倾销进成本，不可退" if way == "一般贸易进口" else
                 "进项可抵，无进口税负" if way.startswith("本地") else
                 "补税后与一般贸易同成本"),
        }
        for col in range(1, 15):
            c = ws.cell(row=r, column=col, value=vals.get(col))
            c.border = BORDER
            c.font = Font(name=FONT, size=8.5, bold=(col == 2))
            c.alignment = Alignment(horizontal="center" if col in (1, 5, 6, 8, 13) else
                                    ("left" if col in (2, 3, 10, 11, 14) else "right"),
                                    vertical="center", wrap_text=True)
            if col in (4, 5, 6):
                c.fill = PatternFill("solid", fgColor=EDIT)
            if col in (7, 9, 12):
                c.number_format = "#,##0.00"
            if col in (5, 6, 8, 13):
                c.number_format = "0.00%"
            if col == 13:
                c.fill = PatternFill("solid", fgColor=GREEN if (ad + duty) == 0 else AMBER)
                c.font = Font(name=FONT, size=9, bold=True)
        ws.row_dimensions[r].height = 22
        r += 1

# ---------- 结论 ----------
r += 1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NC)
c = ws.cell(row=r, column=1, value="结论")
c.font = Font(name=FONT, size=10, bold=True, color=WHITE)
c.fill = PatternFill("solid", fgColor=ACCENT)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[r].height = 20
r += 1

concl = [
    "1. 上表 9 个销售模式，凡是「货出境（含就地出口 E62）」，配保税 SXXK 料件，税负成本率都是 0；配一般贸易料件，成本立刻多 20.45%（纱线）或 12%（布类）——模式选对只是第一层，料件来源选对才是省钱的那一层。",
    "2. 凡是「货不出境（内销／结构 A）」，配本地采购税负为 0；用保税料件做内销必须先补税，补完等于一般贸易，白折腾一道手续还留风险。",
    "3. 7 个模式可稳定成立：S1-01／05（最标准）、S1-02（四方最干净）、S1-08（报关链最对齐）、S1-07（常规内销）、S1-03／04（可用但凭证最严）。S1-06 结构自相矛盾、不适用；S1-09 待关务确认报关单出口方。",
    "4. 所有模式的共同红线只有一条：发票开给谁，必须和报关单上的交易方一致。票走一条链、报关走另一条链，差额迟早被追问。",
]
for t in concl:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NC)
    c = ws.cell(row=r, column=1, value=t)
    c.font = Font(name=FONT, size=8.5)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
    ws.row_dimensions[r].height = 30
    r += 1

r += 1
foot = [
    "⚠️ 待核：① 布类反倾销适用范围未定，现按 0 计；② 关税 3%／12% 为 2023 口径，须按具体 HS 重核；③ 纱线反倾销取最高档 17.45%，实际按出口商名单 3.57%–17.45% 逐笔核 C/O；④ 自 EPE 视同进口未列入（报关类型待关务确认）；⑤ CIT 未纳入（标准 20%，10% 需优惠凭证）。",
    "口径说明：入库成本＝采购额×(1+反倾销率+关税率)；进口VAT 按入库成本×8%，出口可申请退税、内销可抵扣，故不计入成本；销项VAT 为价外税由客户承担，仅占现金流。上区「税负成本率」按推荐采购方式列示（保税／本地＝0）。",
]
for t in foot:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NC)
    c = ws.cell(row=r, column=1, value=t)
    c.font = Font(name=FONT, size=7.5, color="C00000" if t.startswith("⚠️") else "595959")
    c.alignment = Alignment(horizontal="left", vertical="top", indent=1, wrap_text=True)
    ws.row_dimensions[r].height = 32
    r += 1

ws.freeze_panes = "C4"
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
