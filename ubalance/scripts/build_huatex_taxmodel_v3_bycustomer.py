#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""越南华特 · 税负测算模型 v3 —— 按【销售客户企业类型】为主维度
决策链: 客户类型 → 税负矩阵(5×5) → 最低税负路线 → 倒推采购模式(国内采购/一般贸易/保税进口)
输出: deliverables/越南华特-税负测算模型-按客户类型-v3-20261020.xlsx
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter, column_index_from_string
from openpyxl.formatting.rule import CellIsRule

OUT = "deliverables/越南华特-税负测算模型-按客户类型-v3.1-20261020.xlsx"
P = "'04-参数区'"
D = "'03-明细底稿'"

C_HEAD = "1F4E78"; C_GRP = "2E75B6"; C_IN = "FFF2CC"; C_CALC = "E2EFDA"; C_NOTE = "FCE4D6"
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
F_TITLE = Font(bold=True, size=15, color=C_HEAD)

wb = Workbook(); wb.remove(wb.active)

# ============================================================ 04 参数区
ws_p = wb.create_sheet("04-参数区")
ws_p["A1"] = "参数区 —— 只改这一页，全表公式联动"
ws_p["A1"].font = F_TITLE
ws_p["A2"] = "⚠️ 黄底 = 可改参数；绿底 = 公式。改完直接看 01-客户类型税负矩阵。"
ws_p["A2"].font = Font(size=10, color="C00000")
pm = [
    ("SEC", "一、计量与成本结构"),
    ("加工增值率（售价的增值部分占比）", 0.30, "0.0%", "⚠️ Daryl 待查实际值后改这里；原料成本占比自动 = 1 − 本值"),
    ("原料成本占比", "=1-B4", "0.0%", "公式"),
    ("成品平均售价（VND/kg，不含 VAT）", 180000, "#,##0", "⚠️ 占位值，待填实际售价"),
    ("SEC", "二、税率与费率"),
    ("VAT 现行优惠税率", 0.08, "0.0%", "NQ 204/2025/QH15 + NĐ 174/2025/NĐ-CP，适用至 2026-12-31"),
    ("VAT 标准税率", 0.10, "0.0%", "2027 起若无新延续政策即回到 10%"),
    ("企业所得税 CIT 税率", 0.10, "0.0%", "Daryl 指定 10%（法定标准 20%，依据待确认）"),
    ("资金占用成本（年化）", 0.045, "0.0%", "Daryl 指定"),
    ("退税资金占用天数", 75, "0", "原表 60–90 天取中值"),
    ("反倾销率 · 中国纱线上限", 0.1745, "0.00%", "QĐ 2652/QĐ-BCT(2026-10-13)，2026-10-16~2031-10-15，中国 3.57%–17.45% 按出口商"),
    ("反倾销率 · 中国纱线下限", 0.0357, "0.00%", "同上"),
    ("进口关税 · 成品布", 0.12, "0.0%", "原表 2023 口径，待按现行 HS 核"),
    ("进口关税 · 自 EPE 采购纱线（视同进口）", 0.03, "0.0%", "原表 2023 口径，待核"),
    ("进口关税 · 保税进口 / 进料加工", 0.00, "0.0%", "保税不征；转内销时补"),
    ("内销补关税 · 纱线（保税料件转内销）", 0.03, "0.0%", "原表 2023 口径，待核"),
    ("外商承包税率", 0.01, "0.0%", "四方协议下加工关系免、销售关系由鞋厂母公司缴（待核现行规则）"),
    ("SEC", "三、展示用汇率"),
    ("VND/USD", 26000, "#,##0", "⚠️ 占位值"),
    ("SEC", "四、国内采购价税口径"),
    ("国内采购价为含税价（0=不含税价／1=含税价）", 0, "0", "默认 0=不含税价。若取得的 VND 发票为含税价（已含 8% VAT），改为 1，进项改按 原料成本×8%/1.08 计算"),
]
r = 3
for it in pm:
    if it[0] == "SEC":
        ws_p.cell(row=r, column=1, value=it[1]).font = Font(bold=True, size=11, color=C_HEAD); r += 1; continue
    label, val, fmt, note = it
    ws_p.cell(row=r, column=1, value=label).font = Font(size=10)
    c = ws_p.cell(row=r, column=2, value=val); c.font = Font(size=10, bold=True)
    c.number_format = fmt; c.alignment = Alignment(horizontal="center"); c.border = BORDER
    c.fill = PatternFill("solid", fgColor=C_CALC if str(val).startswith("=") else C_IN)
    n = ws_p.cell(row=r, column=3, value=note); n.font = Font(size=9, color="595959")
    n.alignment = Alignment(wrap_text=True, vertical="center"); r += 1
ws_p.column_dimensions["A"].width = 42; ws_p.column_dimensions["B"].width = 14; ws_p.column_dimensions["C"].width = 76
for i in range(3, r): ws_p.row_dimensions[i].height = 28

# ============================================================ 规则数据
PURCH = [
    ("P1", "保税进口", "纱线", "境外中国公司（保税）", f"={P}!$B$15", f"={P}!$B$8", 0, 0, f"={P}!$B$8", False),
    ("P2", "进料加工 / 保税进口", "胚布", "境外中国公司（进料加工）", f"={P}!$B$16", 0, 0, f"={P}!$B$14", f"={P}!$B$8", False),
    ("P3", "一般贸易进口", "成品布", "境外中国公司（一般贸易）", f"={P}!$B$12", f"={P}!$B$8", 0, 0, f"={P}!$B$8", False),
    ("P4", "国内采购", "纱线", "越南境内非 EPE 企业", 0, 0, 0, 0, f"={P}!$B$8", True),
    ("P5", "自 EPE 采购（视同进口）", "纱线", "越南境内 EPE 企业", f"={P}!$B$13", f"={P}!$B$8", 0, 0, f"={P}!$B$8", False),
]
# 修正参数引用（成品布关税 B12? 实为 B12=反倾销上限）——按参数区实际行号重写：
PURCH = [
    # (id, 模式, 材料, 供应商, 进口关税率, 进口VAT率, 反倾销率, 内销补关税率, 内销补VAT率, 是否国内采购)
    ("P1", "保税进口", "纱线", "境外中国公司（保税）", f"={P}!$B$17", 0, f"={P}!$B$13", f"={P}!$B$18", f"={P}!$B$8", False, True),
    ("P2", "进料加工/保税进口", "胚布", "境外中国公司（进料加工）", f"={P}!$B$17", 0, 0, f"={P}!$B$15", f"={P}!$B$8", False, True),
    ("P3", "一般贸易进口", "成品布", "境外中国公司（一般贸易）", f"={P}!$B$15", f"={P}!$B$8", 0, 0, f"={P}!$B$8", False, False),
    ("P4", "国内采购", "纱线", "越南境内非 EPE 企业", 0, 0, 0, 0, f"={P}!$B$8", True, False),
    ("P5", "自EPE采购（视同进口）", "纱线", "越南境内 EPE 企业", f"={P}!$B$16", f"={P}!$B$8", 0, 0, f"={P}!$B$8", False, False),
]
SALES = [
    ("C1", "越南鞋厂 · 非 EPE（内销）", "内销", "VND", "境内交货·客户自行处理进口", 0,
     "客户是越南境内非 EPE 生产企业，境内销售，只能 VND 结算"),
    ("C2", "越南鞋厂 · EPE（出口）", "出口", "USD", "就地出口·客户自办进口手续", 0,
     "客户是出口加工企业，视同出口，可享 0% + 退税"),
    ("C3", "鞋厂母公司（境外，三方/四方）", "出口", "USD", "T/T·经 HFG 或直付鞋厂母公司", f"={P}!$B$19",
     "境外母公司签约，四方/三方协议决定承包税归属"),
    ("C4", "HFG 华特海外母公司（境外关联）", "出口", "USD", "T/T·集团内部结算", f"={P}!$B$19",
     "境外关联方，出口 0% + 退税，但须真实收汇"),
    ("C5", "越南本地第三方客户（如 Exprinta）", "出口", "USD", "就地出口·客户办就地进口", 0,
     "⚠️ 新增分类，待确认：客户性质决定走 E 系列还是 B 系列"),
]
NOTE = {
    "P1": "保税进口纱线：进口不征，但转内销须补 3% 关税+8% VAT，并按现行反倾销决定（3.57%–17.45%/出口商）计征。",
    "P2": "进料加工/保税进口胚布：进口不征，须料件核销；转内销补税。⚠️ 染色加工涉工业区规定与投资执照范围。",
    "P3": "一般贸易进口成品布：全额征 12% 关税 + 8% VAT，不可退，税负最刚性。",
    "P4": "国内采购纱线：非 EPE 华特必担 8% 进项，出口退、内销抵，资金占用 75 天。",
    "P5": "自 EPE 采购视同进口：3% 关税 + 8% VAT；「供应商出口复进口」路径原表标注待海关确认。",
}

# ============================================================ 03 明细底稿（按客户类型为外层）
ws = wb.create_sheet("03-明细底稿")
COLS = [
    ("模式ID", 10), ("客户企业类型", 26), ("出货性质", 9), ("采购模式", 22), ("采购材料", 10),
    ("供应商性质", 22), ("采购开票", 10), ("销售开票", 10), ("收付款路径", 24),
    ("进口关税率", 10), ("进口VAT率", 10), ("反倾销率", 10), ("内销补关税率", 11),
    ("内销补VAT率", 11), ("外商承包税率", 11),
    ("成品售价", 11), ("原料成本", 11), ("反倾销税额", 11), ("进口关税额", 11), ("进口VAT额", 11),
    ("内销补关税", 11), ("内销补VAT", 11), ("销项VAT", 11), ("可抵扣进项", 11),
    ("内销VAT净缴", 11), ("出口退税回流", 12), ("承包税额", 10),
    ("税负合计(不含CIT/资金)", 13), ("利润", 11), ("CIT", 11),
    ("资金占用税额", 12), ("资金占用成本", 12), ("综合税负合计(VND/kg)", 15),
    ("税负率(占售价)", 11), ("采购模式内排名", 11), ("2026 政策口径备注", 44),
]
ws["A1"] = "明细底稿 —— 25 个组合（客户类型 × 采购模式），全部公式驱动"
ws["A1"].font = F_TITLE
ws["A2"] = "这一页是计算底稿，主视图看 01-客户类型税负矩阵；决策结论看 02-采购倒推决策表"
ws["A2"].font = Font(size=9, color="C00000")
HDR = 4
for i, (n, w) in enumerate(COLS, start=1):
    c = ws.cell(row=HDR, column=i, value=n)
    c.font = Font(bold=True, size=9, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="404040")
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = BORDER
    ws.column_dimensions[get_column_letter(i)].width = w

row = HDR + 1
first = row
rowmap = {}
for si, (cid, cname, kind, sell_inv, pay, ctr, cnote) in enumerate(SALES):
    for pi, (pid, pmode, mat, sup, jt, kv, adm, mdt, mvt, dom, bonded) in enumerate(PURCH):
        exp = (kind == "出口")
        rid = f"{cid}-{pid}"
        rowmap[(si, pi)] = row
        vals = {
            1: rid, 2: cname, 3: kind, 4: pmode, 5: mat, 6: sup,
            7: "USD" if pi <= 3 else ("VND（含8%进项）" if pi == 4 else "USD（视同进口）"),
            8: sell_inv, 9: pay,
            10: jt, 11: kv, 12: adm, 13: mdt, 14: mvt, 15: ctr,
            16: f"={P}!$B$6",
            17: f"=P{row}*(1-{P}!$B$4)",
            18: f'=IF(C{row}="内销",Q{row}*L{row},0)',
            19: f"=Q{row}*J{row}",
            20: f"=IF(K{row}=0,0,(Q{row}+S{row})*K{row})",
            21: f'=IF(C{row}="内销",Q{row}*M{row},0)',
            22: (f'=IF(C{row}="内销",(Q{row}+U{row})*N{row},0)' if bonded else 0),
            23: f'=IF(C{row}="内销",P{row}*{P}!$B$8,0)',
            24: (f"=T{row}+V{row}+IF({P}!$B$23=1,Q{row}*{P}!$B$8/(1+{P}!$B$8),Q{row}*{P}!$B$8)" if dom else f"=T{row}+V{row}"),
            25: f"=MAX(W{row}-X{row},0)",
            26: f'=IF(C{row}="出口",X{row},0)',
            27: f"=P{row}*O{row}",
            28: f"=R{row}+S{row}+U{row}+Y{row}+AA{row}",
            29: f"=P{row}-Q{row}-R{row}-S{row}-U{row}-AA{row}",
            30: f"=MAX(AC{row},0)*{P}!$B$10",
            31: f"=Z{row}",
            32: f"=AE{row}*{P}!$B$11*{P}!$B$12/365",
            33: f"=AB{row}+AD{row}+AF{row}",
            34: f"=AG{row}/P{row}",
            35: f"=RANK(AG{row},$AG${first+si*5}:$AG${first+si*5+4},1)",
            36: NOTE[pid] + ("｜客户特征：" + cnote if cid == "C5" else ""),
        }
        for ci, v in vals.items():
            c = ws.cell(row=row, column=ci, value=v)
            c.border = BORDER; c.font = Font(size=9)
            c.alignment = Alignment(vertical="center", wrap_text=ci in (2, 4, 6, 9, 36),
                                    horizontal="center" if ci in (1, 3, 5, 7, 8, 10, 11, 12, 13, 14, 15, 35) else "left")
            if ci in (10, 11, 12, 13, 14, 15):
                c.number_format = "0.00%"; c.fill = PatternFill("solid", fgColor="DDEBF7")
            if ci in range(16, 34):
                c.number_format = "#,##0"; c.fill = PatternFill("solid", fgColor=C_CALC)
            if ci == 34:
                c.number_format = "0.00%"; c.fill = PatternFill("solid", fgColor=C_CALC)
            if ci == 33: c.font = Font(size=9, bold=True)
            if ci == 36: c.fill = PatternFill("solid", fgColor=C_NOTE)
        ws.row_dimensions[row].height = 40
        row += 1
last = row - 1
ws.freeze_panes = f"C{HDR+1}"
ws.auto_filter.ref = f"A{HDR}:AJ{last}"

# ============================================================ 01 客户类型税负矩阵（主视图）
ws1 = wb.create_sheet("01-客户类型税负矩阵")
ws1["A1"] = "按【销售客户企业类型】的税负矩阵 —— 综合税负 VND/kg 成品"
ws1["A1"].font = F_TITLE
ws1["A2"] = "读法：找一行（客户类型）→ 看 5 个采购模式哪格最低 → 该格就是「以销定产、再倒推采购」的答案。绿色 = 该客户类型下最低。"
ws1["A2"].font = Font(size=9, color="C00000")
h1 = ["客户企业类型", "出货性质", "客户特征", "推荐合同税负率",
      "P1 保税进口\n(纱线)", "P2 进料加工\n(胚布)", "P3 一般贸易进口\n(成品布)",
      "P4 国内采购\n(纱线)", "P5 自EPE采购\n(视同进口)",
      "最低综合税负", "最优采购模式", "最优税负率",
      "最高综合税负", "最优vs最差差额", "业务部接单指引"]
HG = {4: C_GRP, 5: C_HEAD, 6: C_HEAD, 7: C_HEAD, 8: C_HEAD, 9: C_HEAD, 10: C_GRP, 11: C_GRP, 12: C_GRP, 13: C_GRP, 14: C_GRP, 15: C_GRP}
for i, n in enumerate(h1, start=1):
    c = ws1.cell(row=4, column=i, value=n)
    c.font = Font(bold=True, size=9, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=HG.get(i, "404040"))
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = BORDER
ws1.row_dimensions[4].height = 42

GUIDE1 = {
    "C1": "内销合同：税负与采购模式几乎无关（VAT 进项全额可抵），关键看能否拿到 8% 进项发票。保税料件转内销要先补税 → 优先国内采购。",
    "C2": "EPE 客户出口：保税/进料加工最优（仅 CIT）。但须真实收汇＋报关，且客户自办进口，合同要写清交货条件（DAP/DAT/CPT）。",
    "C3": "境外母公司签约：在最优采购基础上多 1% 承包税（销售关系下由鞋厂母公司缴）。四方协议按 RACI 确认谁缴。",
    "C4": "HFG 集团内部：同 C3，多 1% 承包税；但集团内定价需符合转让定价要求，收汇凭证必须齐。",
    "C5": "第三方客户：⚠️ 客户性质待确认（EPE/非EPE）→ 直接决定 B/E 申报系列，未确认前不签长约。",
}
r1 = 5
for si, (cid, cname, kind, sell_inv, pay, ctr, cnote) in enumerate(SALES):
    ws1.cell(row=r1, column=1, value=cname).font = Font(size=10, bold=True)
    ws1.cell(row=r1, column=2, value=kind)
    ws1.cell(row=r1, column=3, value=cnote)
    # 推荐合同税负率 = 最低税负率 = 最低综合 / 售价
    ws1.cell(row=r1, column=4, value=f"=K{r1}/{P}!$B$6")
    for pi in range(5):
        src = rowmap[(si, pi)]
        ws1.cell(row=r1, column=5 + pi, value=f"={D}!AG{src}")
    ws1.cell(row=r1, column=10, value=f"=MIN(E{r1}:I{r1})")
    ws1.cell(row=r1, column=11, value=f'=INDEX($E$4:$I$4,MATCH(MIN(E{r1}:I{r1}),E{r1}:I{r1},0))')
    ws1.cell(row=r1, column=12, value=f"=J{r1}/{P}!$B$6")
    ws1.cell(row=r1, column=13, value=f"=MAX(E{r1}:I{r1})")
    ws1.cell(row=r1, column=14, value=f"=M{r1}-J{r1}")
    ws1.cell(row=r1, column=15, value=GUIDE1[cid])
    for ci in range(1, 16):
        c = ws1.cell(row=r1, column=ci); c.border = BORDER
        if ci >= 4: c.font = Font(size=10)
        c.alignment = Alignment(vertical="center", wrap_text=ci in (1, 3, 15),
                                horizontal="center" if 4 <= ci <= 14 else "left")
        if 4 <= ci <= 14: c.number_format = "#,##0"
        if ci in (4, 12): c.number_format = "0.00%"
        if ci in (5, 6, 7, 8, 9): c.fill = PatternFill("solid", fgColor="F2F7FB")
        if ci == 10: c.fill = PatternFill("solid", fgColor="C6EFCE"); c.font = Font(size=10, bold=True)
        if ci == 11: c.fill = PatternFill("solid", fgColor="C6EFCE"); c.font = Font(size=10, bold=True)
        if ci == 12: c.fill = PatternFill("solid", fgColor="C6EFCE"); c.font = Font(size=10, bold=True)
        if ci == 15: c.fill = PatternFill("solid", fgColor=C_NOTE); c.font = Font(size=9)
    ws1.row_dimensions[r1].height = 58
    r1 += 1
# 每行最低格标绿
ws1.conditional_formatting.add(f"E5:I{r1-1}",
    CellIsRule(operator="equal", formula=[f"MIN($E5:$I5)"], fill=PatternFill("solid", fgColor="C6EFCE")))
for col, w in zip("ABCDEFGHIJKLMNO", [30, 9, 34, 13, 12, 12, 14, 12, 14, 13, 24, 11, 13, 14, 52]):
    ws1.column_dimensions[col].width = w
ws1.freeze_panes = "E5"

# 汇总
r1 += 1
ws1.cell(row=r1, column=1, value="全局结论（自动）").font = Font(bold=True, size=11, color=C_HEAD)
summ = [
    ("全表最低综合税负（VND/kg）", f"=MIN({D}!AG{first}:AG{last})"),
    ("全表最高综合税负（VND/kg）", f"=MAX({D}!AG{first}:AG{last})"),
    ("最高 / 最低 倍数", f"=MAX({D}!AG{first}:AG{last})/MIN({D}!AG{first}:AG{last})"),
    ("出口客户平均综合税负", f'=AVERAGEIF({D}!C{first}:C{last},"出口",{D}!AG{first}:AG{last})'),
    ("内销客户平均综合税负", f'=AVERAGEIF({D}!C{first}:C{last},"内销",{D}!AG{first}:AG{last})'),
    ("保税/进料加工(P1+P2)均值", f"=AVERAGE({D}!AG{first}+{D}!AG{first+1}+{D}!AG{first+2}+{D}!AG{first+3}+{D}!AG{first+4},{D}!AG{first+5}+{D}!AG{first+6}+{D}!AG{first+7}+{D}!AG{first+8}+{D}!AG{first+9})"),
]
for i, (k, f) in enumerate(summ):
    rr = r1 + 1 + i
    ws1.cell(row=rr, column=1, value=k).font = Font(size=10)
    c = ws1.cell(row=rr, column=2, value=f); c.font = Font(size=10, bold=True)
    c.number_format = "0.00" if "倍数" in k else "#,##0"
    c.fill = PatternFill("solid", fgColor=C_CALC); c.border = BORDER

# ============================================================ 02 采购倒推决策表
ws2 = wb.create_sheet("02-采购倒推决策表")
ws2["A1"] = "以销定产 · 采购倒推决策表"
ws2["A1"].font = F_TITLE
ws2["A2"] = "链路：客户类型（合同条款）→ 最低税负采购模式 → 供应商性质 / 贸易方式 / 报关 → 采购部动作。数字引自 01 矩阵，改参数自动变。"
ws2["A2"].font = Font(size=9, color="C00000")
h2 = ["客户企业类型", "推荐采购模式（自动取最低）", "该模式综合税负\n(VND/kg)", "税负率", "次优模式", "与次优差额",
      "采购部落地动作", "供应商要求", "报关与单证", "红线 / 风险", "客户性质变化时的替代方案"]
for i, n in enumerate(h2, start=1):
    c = ws2.cell(row=4, column=i, value=n)
    c.font = Font(bold=True, size=9, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=C_HEAD)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = BORDER
ws2.row_dimensions[4].height = 40
PLAN = {
    "C1": ("优先 P4 国内采购纱线：境内提货、VND 结算、8% 进项可抵，无补税动作；保税料件转内销需先补 3% 关税+8% VAT，且反倾销 3.57%–17.45% 一并计征，最不划算",
           "越南境内非 EPE 纱厂，能开 8% VAT 发票的供应商",
           "境内交货、无需报关；进项发票必须齐全",
           "🔴 若用保税料件做内销，须先补税再做，否则 = 未补税内销（稽查重点）",
           "客户若转 EPE → 立即切 P1/P2 保税路线，税负可降 60% 以上"),
    "C2": ("优先 P1 保税进口纱线或 P2 进料加工胚布：进口不征，出口 0%，仅承担 CIT + 退税资金占用",
           "境外中国公司（集团内或指定贸易商），须能提供保税进口/进料加工单证",
           "出口报关（E62 等），料件核销，合同 + 非现金收汇 + 报关单三件齐",
           "🔴 料件必须核销；单耗=实际用量=出口数量须对平",
           "客户若转非 EPE 内销 → 转 P4 国内采购"),
    "C3": ("优先 P1/P2 保税路线；差额来自 1% 外商承包税（销售关系下由鞋厂母公司缴）",
           "境外中国公司 + 鞋厂母公司（四方协议签署方）",
           "出口报关 + 四方/三方协议；承包税判定按加工关系 vs 销售关系",
           "⚠️ 承包税归属若无书面协议，存在被追缴风险",
           "改为直供 HFG 可去掉鞋厂母公司环节"),
    "C4": ("优先 P1/P2 保税路线 + 1% 承包税；集团内部结算须符合转让定价",
           "境外中国公司（集团内）；关联交易定价文档必备",
           "出口报关 + 收汇凭证（集团内 T/T）+ 转让定价同期资料",
           "🔴 无真实收汇 → 不满足 0%/退税条件（NĐ 181/2025 Đ18）",
           "若无法收汇 → 该路线不成立，须改直供第三方"),
    "C5": ("⚠️ 待定：客户性质未知前不做采购承诺；若为 EPE → 走 P1/P2；若为非 EPE → 走 P4",
           "视客户性质确定",
           "就地出口/进口，B 系列 vs E 系列待关务判定",
           "🔴 客户性质未确认即签长约 = 报关类型可能错配",
           "签约前先取得客户企业性质证明"),
}
r2 = 5
for si, (cid, cname, kind, sell_inv, pay, ctr, cnote) in enumerate(SALES):
    col_letter = get_column_letter(5)
    rng = f"'01-客户类型税负矩阵'!$E${5+si}:$I${5+si}"
    ws2.cell(row=r2, column=1, value=cname).font = Font(size=10, bold=True)
    ws2.cell(row=r2, column=2, value=f"=INDEX('01-客户类型税负矩阵'!$E$4:$I$4,MATCH(MIN({rng}),{rng},0))")
    ws2.cell(row=r2, column=3, value=f"=MIN({rng})")
    ws2.cell(row=r2, column=4, value=f"=C{r2}/{P}!$B$6")
    ws2.cell(row=r2, column=5, value=f"=SMALL({rng},2)")
    ws2.cell(row=r2, column=6, value=f"=E{r2}-C{r2}")
    p = PLAN[cid]
    for j, v in enumerate(p, start=7):
        ws2.cell(row=r2, column=j, value=v)
    for ci in range(1, 12):
        c = ws2.cell(row=r2, column=ci); c.border = BORDER
        c.font = Font(size=9, bold=(ci in (2, 3)))
        c.alignment = Alignment(vertical="center", wrap_text=True,
                                horizontal="center" if ci in (3, 4, 5, 6) else "left")
        if ci in (3, 5, 6): c.number_format = "#,##0"
        if ci == 4: c.number_format = "0.00%"
        if ci in (2, 3): c.fill = PatternFill("solid", fgColor="C6EFCE")
        if ci == 10: c.fill = PatternFill("solid", fgColor=C_NOTE)
    ws2.row_dimensions[r2].height = 74
    r2 += 1
for col, w in zip("ABCDEFGHIJK", [28, 26, 13, 9, 11, 12, 60, 34, 36, 40, 42]):
    ws2.column_dimensions[col].width = w
ws2.freeze_panes = "B5"

r2 += 1
ws2.cell(row=r2, column=1, value="怎么用（三步）").font = Font(bold=True, size=11, color=C_HEAD)
steps = [
    "① 业务部接单前：确认客户企业类型（境外 / 越南 EPE / 越南非 EPE）→ 在 01 矩阵找对应行",
    "② 看该行哪一格最低 → 那格就是这份合同应有的采购模式；同时看「推荐合同税负率」报给客户/定价用",
    "③ 把 02 表对应行的「采购部落地动作 / 供应商要求 / 报关单证」直接转给采购与关务执行",
]
for i, t in enumerate(steps):
    ws2.cell(row=r2 + 1 + i, column=1, value=t).font = Font(size=10)

# ============================================================ 05 口径与来源
ws3 = wb.create_sheet("05-口径与来源")
ws3["A1"] = "政策口径与法条来源（2023 原表 vs 2026 现行）"
ws3["A1"].font = F_TITLE
ws3["A2"] = "Brave 联网检索 2 轮（2026-10-20）。「已核」= 找到官方/权威来源；「待核」= 未取得原文或适用存在不确定性，不作结论用。"
ws3["A2"].font = Font(size=9, color="C00000")
h3 = ["编号", "政策项", "原表 2023 口径", "2026 现行口径", "依据 / 来源", "状态"]
for i, x in enumerate(h3, start=1):
    c = ws3.cell(row=4, column=i, value=x)
    c.font = Font(bold=True, size=10, color="FFFFFF"); c.fill = PatternFill("solid", fgColor=C_HEAD)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = BORDER
R3 = [
    ("S01", "增值税标准税率", "10%（注「23年1月恢复10%」）", "10% 减征 2% → 实际 8%，适用 2025-07-01 至 2026-12-31",
     "Nghị quyết 204/2025/QH15 + Nghị định 174/2025/NĐ-CP", "已核"),
    ("S02", "VAT 法体系", "未列法条", "Luật 48/2024/QH15 + Nghị định 181/2025/NĐ-CP（2026-01-01 起）",
     "vanban.chinhphu.vn / minvoice.vn / luatvietnam.vn", "已核"),
    ("S03", "VAT 8% 适用范围", "未区分", "适用原 10% 货物/服务，部分行业排除；纺织纱线/布是否在排除清单内需逐项核",
     "NĐ 174/2025/NĐ-CP Điều 1 + Phụ lục", "待核"),
    ("S04", "企业所得税法", "未列法条", "Luật 67/2025/QH15（CIT 法）",
     "vanban.chinhphu.vn docid=214607", "已核（法名）"),
    ("S05", "CIT 税率", "20%", "Daryl 指定按 10% 建模（法定标准 20%）", "Daryl 2026-10-20 指令", "待确认依据"),
    ("S06", "出口适用 0% 条件", "未列", "合同 + 非现金支付凭证 + 报关单（三者齐备）", "NĐ 181/2025/NĐ-CP Điều 18", "已核"),
    ("S07", "增值税退税情形", "「出口则退税」", "Điều 29 列明可退情形", "NĐ 181/2025/NĐ-CP Điều 29", "已核（条文）"),
    ("S08", "反倾销 · 中国纱线", "17.45% 单一值", "按出口商分档 3.57%–17.45%；2026-10-16 续期 5 年至 2031-10-15",
     "Quyết định 2652/QĐ-BCT（2026-10-13）", "已核"),
    ("S09", "进口关税 成品布 12% / 自EPE采购 3% / 保税 0%", "12% / 3% / 免税", "未取得现行 HS 税率原文", "—", "待核"),
    ("S10", "内销补关税 3%", "3%", "未取得现行原文", "—", "待核"),
    ("S11", "外商承包税 1%", "1%，四方协议按加工/销售关系判定", "未取得现行规则原文", "—", "待核"),
    ("S12", "退税到账周期 60–90 天", "60–90 天，实际 2 个月申请一次", "未核（操作口径）", "原表备注", "待核"),
    ("S13", "资金成本年化 4.5% / CIT 10%", "原表未计", "Daryl 指定", "Daryl 2026-10-20 指令", "已定"),
    ("S14", "越南原产地 30% 增值", "最后加工 + HS 转换 + LVC ≥30%", "未取得现行 LVC 规则原文", "—", "待核"),
]
for i, x in enumerate(R3, start=5):
    for j, v in enumerate(x, start=1):
        c = ws3.cell(row=i, column=j, value=v); c.font = Font(size=9); c.border = BORDER
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if j == 6:
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.fill = PatternFill("solid", fgColor="C6EFCE" if v.startswith("已") else ("FFEB9C" if v == "待核" else "FCE4D6"))
    ws3.row_dimensions[i].height = 42
for col, w in zip("ABCDEF", [8, 30, 30, 54, 36, 13]):
    ws3.column_dimensions[col].width = w
ws3.freeze_panes = "A5"

# ============================================================ 06 操作指引
ws4 = wb.create_sheet("06-操作指引")
ws4["A1"] = "内部操作指引 —— 按客户类型 × 采购模式执行"
ws4["A1"].font = F_TITLE
ws4["A2"] = "「照着做」版本：谁开票、开什么币、报不报关、要哪些单据。🔴 = 风险项。"
ws4["A2"].font = Font(size=9, color="C00000")
h4 = ["序号", "客户类型", "采购模式", "谁开采购票", "谁开销货票", "开票币别", "是否报关", "必备单据", "关键控制点 / 风险"]
for i, x in enumerate(h4, start=1):
    c = ws4.cell(row=4, column=i, value=x)
    c.font = Font(bold=True, size=10, color="FFFFFF"); c.fill = PatternFill("solid", fgColor=C_HEAD)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = BORDER
G4 = [
    ("越南鞋厂 · 非 EPE（内销）", "P4 国内采购", "越南境内非 EPE 纱厂（VND 含 8%）", "华特开 VND 发票（8%）", "VND", "否", "进项发票、销项发票、送货单", "销项 8% − 进项 8%，无退税；非 EPE 之间只能 VND 结算"),
    ("越南鞋厂 · 非 EPE（内销）", "P1 保税进口", "境外中国公司（USD）", "华特开 VND 发票", "VND", "是（转内销补税）", "补 3% 关税 + 8% VAT 凭证、反倾销计征凭证、核销台账", "🔴🔴 反倾销 3.57%–17.45% 全额进成本；「境内有同类料却长期进口反倾销料用于内销」= 稽查重点"),
    ("越南鞋厂 · EPE（出口）", "P1 保税进口", "境外中国公司（USD）", "华特开 USD 发票", "USD", "是", "保税进口报关、出口报关单、单耗表、核销表、收汇凭证", "出口 0% 需合同+非现金收汇+报关单三件齐"),
    ("越南鞋厂 · EPE（出口）", "P2 进料加工", "境外中国公司（USD）", "华特开 USD 发票", "USD", "是", "进料加工手册、出口报关单、核销表", "🔴 单耗=实际用量=出口数量须对平"),
    ("鞋厂母公司（境外）", "P1/P2 保税", "境外中国公司（USD）", "华特开 USD 发票", "USD", "是", "四方/三方协议、出口报关单、收汇凭证", "⚠️ 1% 承包税按协议判定由谁缴，无书面协议有被追缴风险"),
    ("HFG 华特海外母公司", "P1/P2 保税", "境外中国公司（USD）", "华特开 USD 发票", "USD", "是", "关联交易合同、收汇凭证、转让定价同期资料", "🔴 无真实收汇 → 不满足 0%/退税（NĐ 181/2025 Đ18）"),
    ("越南本地第三方客户", "待定", "视客户性质", "华特/客户", "USD 或 VND", "待关务判定", "客户企业性质证明、报关单", "🔴 性质未确认前不签长约"),
]
for i, x in enumerate(G4, start=5):
    ws4.cell(row=i, column=1, value=i - 4).alignment = Alignment(horizontal="center", vertical="center")
    for j, v in enumerate(x, start=2):
        c = ws4.cell(row=i, column=j, value=v); c.font = Font(size=9); c.border = BORDER
        c.alignment = Alignment(wrap_text=True, vertical="top")
    ws4.row_dimensions[i].height = 58
for col, w in zip("ABCDEFGHI", [6, 26, 18, 30, 24, 12, 16, 44, 48]):
    ws4.column_dimensions[col].width = w
ws4.freeze_panes = "C5"

# ============================================================ 00 使用说明
ws0 = wb.create_sheet("00-使用说明", 0)
ws0["A1"] = "越南华特 · 税负测算模型 v3 —— 按【销售客户企业类型】分类"
ws0["A1"].font = F_TITLE
L = [
    ("", ""),
    ("版本", "v3 / 2026-10-20 / Balance"),
    ("与 v2 的差别", "v2 以【采购模式】为主维度（成本视角）；v3 改为以【销售客户企业类型】为主维度（销售决策视角）—— 因为业务部要回答的第一个问题是「这类客户的合同税负是多少」，不是「我采购走哪条路」。"),
    ("决策链路", "客户企业类型 → 01 矩阵查该行 5 种采购模式的税负 → 取最低 → 02 倒推表给出采购部动作 → 采购/关务执行"),
    ("", ""),
    ("四张表怎么配合", ""),
    ("01-客户类型税负矩阵", "主视图。行 = 客户企业类型（5 类），列 = 5 种采购模式。每行自动标出最低组合（绿色）。看这一页做定价与接单决策。"),
    ("02-采购倒推决策表", "一行一个客户类型：推荐采购模式（自动）、次优、差额、采购部动作、供应商要求、报关单证、红线。这一页可以直接转给采购和关务。"),
    ("03-明细底稿", "25 个组合的全部计算过程（VND/kg、VAT、退税、CIT、资金成本）。公式都在这里，改参数从这层开始传导。"),
    ("04-参数区", "唯一输入页。加工增值率、售价、税率、资金成本、退税天数。"),
    ("05-口径与来源", "14 条政策口径，2023 vs 2026 逐条对照 + 法条 + 状态（已核 / 待核）。"),
    ("06-操作指引", "按客户类型 × 采购模式组合出的执行清单。"),
    ("", ""),
    ("客户类型定义（5 类）", ""),
    ("C1 越南鞋厂 · 非 EPE", "越南境内、非出口加工企业 → 交易构成内销，只能 VND 结算，无法享受出口退税。"),
    ("C2 越南鞋厂 · EPE", "出口加工企业 → 视同出口，可享 0% + 退税，客户自办进口手续。"),
    ("C3 鞋厂母公司（境外）", "签署三方/四方协议的境外母公司 → 出口，但多一道 1% 外商承包税的归属问题。"),
    ("C4 HFG 华特海外母公司", "境外关联方 → 出口 + 集团内结算，须满足转让定价与收汇要求。"),
    ("C5 越南本地第三方客户", "⚠️ 新增分类（对应 Exprinta 之类就地进口客户），客户性质待确认。"),
    ("", ""),
    ("计算逻辑（与 v2 相同）", ""),
    ("原料成本", "= 成品售价 ×（1 − 加工增值率）；增值率在 04-参数区 B4，Daryl 查出真值直接改。"),
    ("反倾销税", "= 原料成本 × 反倾销率（仅内销时发生；出口复出口不征）"),
    ("进口关税", "= 原料成本 × 关税率（保税 / 进料加工 = 0）"),
    ("进口 VAT", "= （原料成本 + 关税）× VAT 率；保税 = 0"),
    ("内销补税", "= 原料成本 × 补关税率 + （原料成本 + 补关税）× 补 VAT 率（仅内销）"),
    ("内销 VAT 净缴", "= MAX（售价 × 8% − 可抵扣进项，0）"),
    ("出口退税回流", "= 可抵扣进项（出口行按全额退建模）"),
    ("承包税", "= 售价 × 1%（四方协议行按 0）"),
    ("CIT", "= MAX（售价 − 原料成本 − 不可抵扣税费，0）× 10%"),
    ("资金占用成本", "= 退税额 × 4.5% × 75 / 365"),
    ("综合税负", "= 反倾销 + 关税 + 内销补税 + 内销VAT净缴 + 承包税 + CIT + 资金占用成本  ← 比较用的单位税负"),
    ("", ""),
    ("诚实边界", ""),
    ("⚠️ 1", "成品售价 180,000 VND/kg 是占位值；填入真值前，金额只能做模式间相对比较，不能对外报价或申报。"),
    ("⚠️ 2", "CIT 10% 是 Daryl 指定（法定 20%），依据未核。"),
    ("⚠️ 3", "VAT 按 8%（至 2026-12-31）；纺织纱线/布是否适用 8%，NĐ 174 排除清单未逐项核 → 05 表标「待核」。"),
    ("⚠️ 4", "反倾销取 17.45% 上限（实际按出口商 3.57%–17.45% 分档），属保守假设。"),
    ("⚠️ 5", "6 项 2023 税率/规则（关税、补税、承包税、原产地、退税周期等）未核到现行原文，全部标「待核」。"),
    ("⚠️ 6", "CIT 利润为简化口径（未扣人工/折旧/期间费用）→ CIT 偏高，属保守。"),
    ("⚠️ 7", "C5 客户类型在原表不存在，是我按 FOC 泳道图里 Exprinta「就地进口」推断补的，需你确认是否成立。"),
    ("", ""),
    ("v3.1 校正记录（2026-10-20）", "Daryl 质询「国内采购进项税为什么是 0」→ 复核发现两个问题并已修正：①「进口VAT率/进口VAT额」两列只表示进口环节，国内采购确为 0（不是没有进项税），进项税记在「可抵扣进项」列 ②真 bug：「内销补VAT」对 P3/P4/P5 也计了一遍（应仅保税料件 P1/P2 转内销才补），导致这三类内销行进项被虚增、内销VAT净缴被算成 0 → C1 行金额低估。已加「是否保税料件补税」标志位修正。③新增 B23「采购价含税/不含税」开关。"),
    ("下一步（等你定）", "A. 填真实售价 + 增值率 → 出可对外数字  B. 核 05 表「待核」项  C. 做 HTML 交互版（选客户类型即出推荐路线）  D. 按实际月销量做年度税负预测与采购预算联动"),
]
r = 2
for a, b in L:
    ca = ws0.cell(row=r, column=1, value=a); ca.font = Font(bold=True, size=10)
    cb = ws0.cell(row=r, column=2, value=b); cb.font = Font(size=9 if b else 10)
    cb.alignment = Alignment(wrap_text=True, vertical="top")
    if a in ("四张表怎么配合", "客户类型定义（5 类）", "计算逻辑（与 v2 相同）", "诚实边界", "下一步（等你定）"):
        ca.font = Font(bold=True, size=11, color=C_HEAD)
    r += 1
ws0.column_dimensions["A"].width = 26; ws0.column_dimensions["B"].width = 118

wb._sheets = [wb["00-使用说明"], wb["01-客户类型税负矩阵"], wb["02-采购倒推决策表"],
              wb["03-明细底稿"], wb["04-参数区"], wb["05-口径与来源"], wb["06-操作指引"]]
os.makedirs("deliverables", exist_ok=True)
wb.save(OUT)
print("saved:", OUT)
print("明细行:", last - first + 1)
print("sheets:", wb.sheetnames)
