# -*- coding: utf-8 -*-
"""
华特经营模式 · 按销售模式披露 v5（2026-10-29）
v5 变更（Daryl 10-29 确认「销售方 HFGI / Huatex 自购料」情景 A）：
  1. 新增两列真正的驱动因子：「Huatex 角色（是否出口报关方）」「保税料件可否使用」
  2. 结构 A（S1-08）显式标注为例外：Huatex 是内销方 → 保税料件不可用 → 若须进口料，税负 20.45%／12%
  3. 新增「销售方＝HFGI」专项说明块（发票两段/收款主体/转让定价/FCT）
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = "deliverables/越南华特经营模式-按销售模式披露-v5-20261029.xlsx"
FONT = "微软雅黑"
DARK, ACCENT, LIGHT, GREY = "1F3864", "2E5C8A", "D9E2F3", "F2F2F2"
GREEN, AMBER, RED, WHITE, EDIT = "C6EFCE", "FFEB9C", "FFC7CE", "FFFFFF", "FFF2CC"
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

# 编号, 名称, 交易结构, Huatex角色, 保税料件, 推荐采购, 反倾销, 关税, 入库系数, 进口VAT,
# 报关, 核销, 销项VAT, 发票开给谁, 单证, 风险, 税负成本率(文本), 结论, 色
SALES = [
    ("S1-01", "离境出口", "Huatex → 境外客户（买方＝收货方，货实际离境）",
     "出口方（自报出口报关）", "可用", "保税进口 SXXK", 0, 0, 1.000, "0（复出口不征）",
     "出口报关（E31 核销配对）", "必核销", 0.0, "境外买方（不开给境内任何方）",
     "合同/PO、CI、PL、出口报关单、收汇水单、B/L",
     "无真实收汇或第三方代付 → 0% 与退税双双被拒",
     "0%（保税料）｜+20.45%·12%（改一般贸易料）", "✅ 推荐·最标准", "g"),
    ("S1-02", "四方合同·收货＝EPE（销售方可为 HFGI）", "境外 A 销售（如 HFGI）｜Huatex 供货｜境外 C 购买｜越南 EPE 收货（E62）",
     "供货方，但出口报关主体仍是 Huatex（E62）", "可用", "保税进口 SXXK", 0, 0, 1.000, "0（复出口不征）",
     "E62 就地出口（与 SXXK 核销配对）", "必核销＋E62 配对", 0.0, "合同买方（境外 A／HFGI）——绝不开给 EPE",
     "四方合同（含「买方书面指定交货第三方」）、0% 发票（备注交货地＋收货人）、CI/PL、E62 单、EPE 就地进口单、A 的付款水单",
     "发票开给 EPE／E62 不进核销 → 打内销或补进口税；A 仅为通道 → 被质疑",
     "0%（保税料）｜+20.45%·12%（改一般贸易料）", "✅ 推荐·结构最干净", "g"),
    ("S1-03", "四方合同·收货＝本地买断", "境外买方签约｜Huatex 供货｜越南本地企业买断收货，货权转移",
     "供货方，但出口报关主体仍是 Huatex（E62）", "可用", "保税进口 SXXK", 0, 0, 1.000, "0（复出口不征）",
     "E62；收货方办就地进口", "必核销", 0.0, "合同买方（境外）——不开给收货方",
     "四方合同、0% 发票、CI/PL、E62 单、收货方就地进口单、收货方缴税凭证",
     "五条任一踩线即打内销：票开收货方／收货方付款／无指定交货条款／买方仅通道／非真实买断",
     "0%（保税料）｜+20.45%·12%（改一般贸易料）", "⚠️ 高风险·凭证最严", "a"),
    ("S1-04", "四方合同·收货＝本地代工", "境外买方签约｜Huatex 供货｜代工厂收货加工，货权不转移",
     "供货方，但出口报关主体仍是 Huatex（E62）", "可用", "保税进口 SXXK", 0, 0, 1.000, "0（复出口不征）",
     "E62；代工厂按加工 nhập gia công 就地进口", "必核销", 0.0, "合同买方（境外）",
     "四方合同、加工合同（证明货权不转移）、0% 发票、E62 单、Mẫu 22 通报（15 天内）",
     "被认定买断 → 代工厂补进口税与 VAT；未按期通报 Mẫu 22 → 免税失效",
     "0%（保税料）｜+20.45%·12%（改一般贸易料）", "🟡 可用·须加工合同支撑", "a"),
    ("S1-05", "买方即 EPE（直供）", "Huatex → 越南 EPE（买方＝收货方）",
     "出口方（自报 E62）", "可用", "保税进口 SXXK", 0, 0, 1.000, "0（复出口不征）",
     "E62；EPE 办就地进口", "必核销", 0.0, "越南 EPE（买方＝收货方）",
     "合同（注明交货至非关税区）、E62 单、EPE 就地进口单、收款凭证",
     "货未真实进入非关税区 → 0% 不成立，全额按内销 8%",
     "0%（保税料）｜+20.45%·12%（改一般贸易料）", "✅ 推荐·最常见最简单", "g"),
    ("S1-06", "买方 EPE＋本地收货", "EPE 买入｜本地企业收货（货从不进非关税区）",
     "—（结构自相矛盾，无合规路径）", "不可用", "—", None, None, None, "—",
     "无法报关（EPE 无法办就地进口）", "—", None, "—（不存在合规开票方式）",
     "—",
     "票货分离／过票；本地企业无证进口（行政甚至刑事风险）",
     "—", "❌ 不适用", "r"),
    ("S1-07", "内销", "Huatex → 越南本地企业（买方＝收货方，非 EPE）",
     "内销方（无报关，非出口方）", "不可用（保税料件不得流入内销）", "本地采购（自非EPE）", 0, 0, 1.000, "8%（可抵）",
     "无需报关", "记录", 0.08, "越南本地企业（买方）",
     "合同/PO、越南 VAT 发票（8%）、送货单、收款凭证",
     "保税料件未补税即内销；境内交易外币结算不合规",
     "0%（本地料）｜+20.45%·12%（须进口料，含保税转内销补税）", "✅ 常规内销", "g"),
    ("S1-08", "结构 A（买方本地＋收货 EPE）★例外", "Huatex 内销开 8% 给 C → C 报就地出口 → 越南 EPE 收货",
     "内销方（出口由 C 申报，Huatex 不是出口方）", "不可用 ★这是全表唯一例外", "本地采购（自非EPE）", 0, 0, 1.000, "8%（可抵）",
     "Huatex 不报关；C 报 E62", "记录", 0.08, "C（越南本地企业买方）",
     "Huatex↔C 合同、VAT 发票（8%）、送货单、C 侧出口报关单（供链条解释）",
     "货最终出境，但 Huatex 这层是内销 → 保税料件不能用；本地料供不上就得进口，税负立刻上来",
     "0%（本地料）｜+20.45%·12%（须进口料）★成本分水岭", "✅ 推荐·报关链最对齐", "a"),
    ("S1-09", "结构 B（买方本地＋收货 EPE）", "Huatex 直接 E62，买方须改为境外实体、C 退出链条",
     "出口方（自报 E62，须重构合同主体）", "可用", "保税进口 SXXK", 0, 0, 1.000, "0（复出口不征）",
     "E62；EPE 办就地进口", "必核销", 0.0, "境外买方（须重构合同主体）",
     "三方/四方合同（含指定交货条款）、0% 发票、E62 单、EPE 就地进口单、境外买方付款水单",
     "四层全开票 → 报关链对不上商业链，必有一层过票",
     "0%（保税料）｜+20.45%·12%（改一般贸易料）", "⚠️ 待关务确认", "a"),
]

MAT = [("纱线", 0.1745, 0.03), ("胚布", 0.0, 0.12), ("成品布", 0.0, 0.12)]
WAYS = [
    ("保税进口（SXXK）", "境外 / 越南 EPE（保税）", "E31", "必核销", 0, 0),
    ("一般贸易进口", "境外 / 越南 EPE", "A12", "记录", 1, 1),
    ("本地采购（自非EPE）", "越南境内非 EPE", "无", "记录", 0, 0),
    ("保税进口 → 转内销", "境外 / 越南 EPE（保税）", "补税后 B11/A12", "核销后转内销", 1, 1),
]

HDR1 = ["编号", "销售模式", "交易结构（卖方→买方｜收货方）", "Huatex 角色（是否出口报关方）", "保税料件可否使用",
        "推荐采购方式", "反倾销率", "进口关税率", "入库成本系数", "进口VAT", "报关类型", "平衡账册核销",
        "销项VAT率", "发票开给谁", "必备单证（核心）", "主要风险 / 红线", "税负成本率（按料件）", "结论"]
COLW = {"A": 8, "B": 22, "C": 30, "D": 26, "E": 15, "F": 15, "G": 9, "H": 9, "I": 10, "J": 13,
        "K": 22, "L": 14, "M": 9, "N": 22, "O": 32, "P": 32, "Q": 24, "R": 16}
NC = len(HDR1)

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "销售模式披露"
for c, w in COLW.items():
    ws.column_dimensions[c].width = w

ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=NC)
c = ws.cell(row=1, column=1, value="越南华特 · 按销售模式披露 v5（驱动因子：Huatex 是否出口报关方 ＋ 保税料件可否使用）")
c.font = Font(name=FONT, size=13, bold=True, color=WHITE)
c.fill = PatternFill("solid", fgColor=DARK)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[1].height = 26

ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=NC)
c = ws.cell(row=2, column=1, value=(
    "核心判断：成本由「保税料件能不能用」决定（＝Huatex 是不是出口报关方），风险由「合同结构与收货方性质」决定。"
    "　VAT 0%/8% 是价外税，影响现金流与报价口径，不构成利润差异。　入库成本＝采购额×(1+反倾销+关税)。　2026-10-29 v5"))
c.font = Font(name=FONT, size=8, italic=True, color="595959")
c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
ws.row_dimensions[2].height = 22


def header_row(row, values, height=40, color=DARK):
    for i, v in enumerate(values, start=1):
        c = ws.cell(row=row, column=i, value=v)
        c.font = Font(name=FONT, size=8.5, bold=True, color=WHITE)
        c.fill = PatternFill("solid", fgColor=color)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDER
    ws.row_dimensions[row].height = height


header_row(3, HDR1, 42)

r = 4
for (mid, name, struct, role, bonded, buy, ad, duty, coeff, ivat, customs, woff, svat, inv,
     docs, risk, costrate, concl, flag) in SALES:
    vals = [mid, name, struct, role, bonded, buy,
            ad if ad is not None else "—",
            duty if duty is not None else "—",
            coeff if coeff is not None else "—",
            ivat, customs, woff,
            svat if svat is not None else "—",
            inv, docs, risk, costrate, concl]
    for col, v in enumerate(vals, start=1):
        c = ws.cell(row=r, column=col, value=v)
        c.border = BORDER
        c.font = Font(name=FONT, size=8, bold=(col in (1, 2)))
        c.alignment = Alignment(horizontal="center" if col in (1, 7, 8, 9, 13) else "left",
                                vertical="center", wrap_text=True)
        if col in (7, 8, 13):
            c.number_format = "0.00%"
        if col == 9:
            c.number_format = "0.000"
        if col == 4:
            c.font = Font(name=FONT, size=8, bold=True)
            c.fill = PatternFill("solid", fgColor=GREEN if "出口方" in str(role) or "报关主体" in str(role) else AMBER)
        if col == 5:
            c.font = Font(name=FONT, size=8, bold=True)
            c.fill = PatternFill("solid", fgColor=RED if str(bonded).startswith("不可用") else GREEN)
        if col == 17:
            c.font = Font(name=FONT, size=7.5)
            c.fill = PatternFill("solid", fgColor=AMBER if "+20.45%" in str(costrate) else GREEN)
        if col == 18:
            c.fill = PatternFill("solid", fgColor={"g": GREEN, "a": AMBER, "r": RED}[flag])
            c.font = Font(name=FONT, size=8, bold=True)
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[r].height = 52
    r += 1

# ---------- HFGI 专项 ----------
r += 1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NC)
c = ws.cell(row=r, column=1, value="专项：销售方＝HFGI、Huatex 为生产商（Huatex 自购料 → 卖给 HFGI）")
c.font = Font(name=FONT, size=10, bold=True, color=WHITE)
c.fill = PatternFill("solid", fgColor=ACCENT)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[r].height = 22
r += 1

hfg = [
    ("① 出口报关主体", "仍然是 Huatex", "境外公司无越南法人资格，不能以自己名义报关出口。HFGI 只是合同链条上的销售方，报关与核销仍落 Huatex。"),
    ("② 发票链", "两段，不能合并", "Huatex → HFGI → 最终客户。Huatex 不得直接开票给终端客户，否则与报关单交易方不一致。"),
    ("③ 收款主体", "必须是 HFGI 付款", "0% 要求买方经银行付款。水单付款人＝合同买方（HFGI）；由越南收货方代付，0% 与退税都保不住。"),
    ("④ 转让定价", "关联转手价须有支撑", "HFGI 为关联方，低价转手可能被按独立交易原则调增 Huatex 的 CIT。税负表里看不到，但会实际发生。"),
    ("⑤ FCT／常设机构", "需书面意见", "HFGI 在越是否构成常设机构、是否涉承包商税（FCT），要税务顾问出书面答复，不能靠口头。"),
    ("⑥ 料件来源", "Huatex 自购 → 税负落在 Huatex", "若改为 HFGI 客供料（来料加工），反倾销与关税不落在 Huatex，本表全部不适用，需另做加工费模型。"),
]
for tag, key, note in hfg:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NC)
    c = ws.cell(row=r, column=1, value=f"{tag}　{key}　—　{note}")
    c.font = Font(name=FONT, size=8.5)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
    c.border = BORDER
    ws.row_dimensions[r].height = 24
    r += 1

# ---------- 下区：采购对照 ----------
r += 1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NC)
c = ws.cell(row=r, column=1, value="采购方式 × 税负成本对照（底表口径，黄色格可改，改后本区联动）")
c.font = Font(name=FONT, size=10, bold=True, color=WHITE)
c.fill = PatternFill("solid", fgColor=ACCENT)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[r].height = 22
r += 1

HDR2 = ["原材料", "采购方式", "供应商性质", "采购金额（USD）", "反倾销率", "进口关税率", "入库成本（USD）",
        "进口VAT率", "进口VAT（USD）", "报关类型", "平衡账册核销", "税负成本（USD）", "税负成本率", "备注"]
for i, v in enumerate(HDR2, start=1):
    c = ws.cell(row=r, column=i, value=v)
    c.font = Font(name=FONT, size=8.5, bold=True, color=WHITE)
    c.fill = PatternFill("solid", fgColor=DARK)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = BORDER
ws.row_dimensions[r].height = 34
r += 1

for mat, ad_base, duty_base in MAT:
    for way, sup, customs, woff, ua, ud in WAYS:
        ad, duty = ad_base * ua, duty_base * ud
        note = ("复出口不征，税负归零" if way.startswith("保税进口（") else
                "关税＋反倾销进成本，不可退" if way == "一般贸易进口" else
                "进项可抵，无进口税负" if way.startswith("本地") else
                "补税后与一般贸易同成本")
        vals = {1: mat, 2: way, 3: sup, 4: 1000, 5: ad, 6: duty,
                7: f"=D{r}*(1+E{r}+F{r})", 8: 0.08, 9: f"=G{r}*H{r}",
                10: customs, 11: woff, 12: f"=D{r}*(E{r}+F{r})",
                13: f"=IFERROR(L{r}/D{r},0)", 14: note}
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
    "1. 真正决定成本的不是「几方合同」也不是「收货方性质」，而是「保税料件能不能用」——也就是 Huatex 在这一票货上是不是出口报关方。9 个模式里 8 个 Huatex 都是出口方，所以成本都归零；只有结构 A（S1-08）不是。",
    "2. 结构 A 是唯一例外：买方是本地 C，Huatex 这层按内销处理，保税料件不能用。货虽然最终出境，但 Huatex 的料件必须完税——本地采购能供上则税负仍为 0，供不上就得进口，成本立刻 +20.45%（纱线）／+12%（布类）。这是选 A 还是选 B 的真正分水岭。",
    "3. 销售模式不影响成本，但影响三件事：VAT 销项率（0%/8%，影响现金流与报价口径）、凭证链强度（决定 0% 会不会被打回内销）、操作复杂度（E62 配对、Mẫu 22、四方合同条款）。",
    "4. 销售方为 HFGI 时，报关、核销、成本仍在 Huatex 身上；变化的是发票两段、收款必须是 HFGI、以及转让定价与 FCT 两项表外风险。",
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
    "口径：入库成本＝采购额×(1+反倾销率+关税率)；进口VAT 按入库成本×8%，出口可退、内销可抵，不计入成本；销项VAT 为价外税由客户承担。「税负成本率（按料件）」按推荐料件列示，括号内为改用一般贸易料件时的成本增量。",
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
