#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""越南华特 · 税负测算模型 + 内部操作指引 v2
口径: 单位 = VND/kg（每 1 公斤成品）；全流程包括 关税/反倾销/进口VAT/内销补税/销项VAT/出口退税/承包税/CIT/资金占用成本
Daryl 指定: 原料成本占比由「加工增值率」参数驱动(默认30%)、CIT 10%、资金成本年化 4.5%
输出: deliverables/越南华特-税负测算模型与操作指引-v2-20261020.xlsx
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter, column_index_from_string

OUT = "deliverables/越南华特-税负测算模型与操作指引-v2-20261020.xlsx"
P = "'02-参数区'"

C_HEAD = "1F4E78"; C_GRP = "2E75B6"; C_IN = "FFF2CC"; C_CALC = "E2EFDA"; C_NOTE = "FCE4D6"
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
F_TITLE = Font(bold=True, size=15, color=C_HEAD)
F_SEC = Font(bold=True, size=11, color="FFFFFF")

wb = Workbook()
wb.remove(wb.active)

# ------------------------------------------------------------------ 02 参数区（先建，供引用）
ws_p = wb.create_sheet("02-参数区")
ws_p["A1"] = "参数区 —— 只改这一页，01-总表全部公式联动"
ws_p["A1"].font = F_TITLE
ws_p["A2"] = "⚠️ 黄底格 = 可改参数；绿底 = 公式自动算。改完立刻看 01-总表 的「综合税负合计」列。"
ws_p["A2"].font = Font(size=10, color="C00000")

pm = [
    ("SEC", "一、计量与成本结构（Daryl 待查后可改）"),
    ("B4", "加工增值率（售价的增值部分占比）", 0.30, "0.0%", "⚠️ Daryl 待查实际值后直接改这里；原料成本占比 = 1 - 本值"),
    ("B5", "原料成本占比", "=1-B4", "0.0%", "公式：1 − 加工增值率"),
    ("B6", "成品平均售价（VND/kg，不含 VAT）", 180000, "#,##0", "⚠️ 占位值，待填实际售价；按 kg 计量"),
    ("SEC", "二、税率与费率"),
    ("B8", "VAT 现行优惠税率", 0.08, "0.0%", "已核：NQ 204/2025/QH15 + NĐ 174/2025/NĐ-CP，10%→8% 适用至 2026-12-31"),
    ("B9", "VAT 标准税率", 0.10, "0.0%", "2027-01-01 起回到 10%（若无新延续政策）"),
    ("B10", "企业所得税 CIT 税率", 0.10, "0.0%", "Daryl 指定 10%（非法定标准 20%，属优惠/约定口径，待确认依据）"),
    ("B11", "资金占用成本（年化）", 0.045, "0.0%", "Daryl 指定 4.5%"),
    ("B12", "退税资金占用天数", 75, "0", "原表 60–90 天，取中值 75"),
    ("B13", "反倾销率 · 中国纱线上限", 0.1745, "0.00%", "已核：QĐ 2652/QĐ-BCT(2026-10-13)，2026-10-16~2031-10-15，中国 3.57%–17.45% 按出口商分档"),
    ("B14", "反倾销率 · 中国纱线下限", 0.0357, "0.00%", "同上，按实际出口商/生产商适用"),
    ("B15", "进口关税 · 成品布", 0.12, "0.0%", "原表 2023 口径，待按现行 HS 核"),
    ("B16", "进口关税 · 自 EPE 采购纱线（视同进口）", 0.03, "0.0%", "原表 2023 口径，待核"),
    ("B17", "进口关税 · 保税进口 / 进料加工", 0.00, "0.0%", "保税，不征；转入内销时补"),
    ("B18", "内销补关税 · 纱线（保税料件转内销）", 0.03, "0.0%", "原表 2023 口径，待核"),
    ("B19", "外商承包税率", 0.01, "0.0%", "原表 1%；四方协议下加工关系免、销售关系由鞋厂母公司缴（待核现行规则）"),
    ("SEC", "三、展示用汇率"),
    ("B21", "VND/USD", 26000, "#,##0", "⚠️ 占位值，仅用于 USD/kg 参考列"),
]
r = 3
for item in pm:
    if item[0] == "SEC":
        ws_p.cell(row=r, column=1, value=item[1]).font = Font(bold=True, size=11, color=C_HEAD)
        r += 1
        continue
    addr, label, val, fmt, note = item
    ws_p.cell(row=r, column=1, value=label).font = Font(size=10)
    c = ws_p.cell(row=r, column=2, value=val)
    c.font = Font(size=10, bold=True)
    c.number_format = fmt
    c.fill = PatternFill("solid", fgColor=C_IN if not (isinstance(val, str) and str(val).startswith("=")) else C_CALC)
    c.alignment = Alignment(horizontal="center")
    c.border = BORDER
    n = ws_p.cell(row=r, column=3, value=note)
    n.font = Font(size=9, color="595959")
    n.alignment = Alignment(wrap_text=True, vertical="center")
    r += 1

r += 1
ws_p.cell(row=r, column=1, value="四、待你补充的参数（填完模型即完整）").font = Font(bold=True, size=11, color=C_HEAD)
r += 1
for t in ["① 加工增值率实际值（B4）—— 你查出来后直接改，全表联动",
          "② 成品平均售价 VND/kg（B6）—— 建议按纱线 / 胚布 / 成品布 分档，可拆成三行后我把公式改成查找",
          "③ 纱线实际反倾销档位（B13/B14 之间）—— 取决于中国出口商/生产商",
          "④ 2027 年 VAT 是否仍 8%（B8/B9）"]:
    ws_p.cell(row=r, column=1, value=t).font = Font(size=9, color="7F7F7F")
    r += 1

ws_p.column_dimensions["A"].width = 44
ws_p.column_dimensions["B"].width = 14
ws_p.column_dimensions["C"].width = 78
for row in range(3, r):
    ws_p.row_dimensions[row].height = 30

# ------------------------------------------------------------------ 01 总表
ws = wb.create_sheet("01-总表")
GROUPS = [
    ("A", "I", "模式识别 / 交易结构", C_HEAD),
    ("J", "P", "政策口径（引用参数区）", C_GRP),
    ("Q", "AB", "税额计算（VND/kg）", C_HEAD),
    ("AC", "AI", "汇总对比", C_GRP),
    ("AJ", "AL", "2026 政策口径 / 操作指引", C_HEAD),
]
COLS = [
    ("模式ID", 11), ("采购材料", 10), ("交易模式", 22), ("供应商性质", 18),
    ("销售路径（对象）", 26), ("出货性质", 9), ("采购开票", 9), ("销售开票", 9), ("收付款路径", 18),
    ("进口关税率", 10), ("进口VAT率", 10), ("反倾销率", 10), ("内销补关税率", 11),
    ("内销补VAT率", 11), ("出口退税率", 10), ("外商承包税率", 11),
    ("成品售价", 11), ("原料成本", 11), ("反倾销税额", 11), ("进口关税额", 11),
    ("进口VAT额", 11), ("内销补关税", 11), ("内销补VAT", 11), ("销项VAT", 11),
    ("可抵扣进项", 11), ("内销VAT净缴", 11), ("出口退税回流", 12), ("承包税额", 10),
    ("税负合计\n(不含CIT/资金)", 13), ("利润", 11), ("CIT", 11),
    ("资金占用税额", 12), ("资金占用成本", 12), ("综合税负合计\n(VND/kg)", 14),
    ("税负率\n(占售价)", 11), ("成本排名", 9),
    ("2026 政策口径备注", 46), ("操作指引要点", 46),
]

ws["A1"] = "越南华特 · 全流程税负测算总表（单位：VND/kg 成品）"
ws["A1"].font = F_TITLE
ws["A2"] = "行 = 交易模式 × 销售对象（25 个真实组合）｜J–P 列引用 02-参数区｜改参数 → 全表自动重算｜⚠️ 带【待填】的基准值未确认前，绝对金额仅供比较，不作对外申报依据"
ws["A2"].font = Font(size=9, color="C00000")

ws.merge_cells("A3:A3")  # placeholder
hdr_row = 4
# 组标题行
gstart = {}
for g in GROUPS:
    c1 = column_index_from_string(g[0]); c2 = column_index_from_string(g[1])
    ws.merge_cells(start_row=3, start_column=c1, end_row=3, end_column=c2)
    cell = ws.cell(row=3, column=c1, value=g[2])
    cell.font = Font(bold=True, size=11, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor=g[3])
    cell.alignment = Alignment(horizontal="center", vertical="center")
for i, (name, w) in enumerate(COLS, start=1):
    c = ws.cell(row=hdr_row, column=i, value=name)
    c.font = Font(bold=True, size=9, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="404040")
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = BORDER
    ws.column_dimensions[get_column_letter(i)].width = w

PURCH = [
    # (材料, 交易模式, 供应商, 关税率, 进口VAT, 反倾销率, 内销补关税率, 内销补VAT率, 国内采购进项标识)
    ("成品布", "一般贸易进口", "境外中国公司", f"={P}!$B$15", f"={P}!$B$8", 0, 0, f"={P}!$B$8", False),
    ("胚布", "保税进口 / 进料加工", "境外中国公司", f"={P}!$B$17", 0, 0, f"={P}!$B$15", f"={P}!$B$8", False),
    ("纱线", "保税进口（原料）", "境外中国公司", f"={P}!$B$17", 0, f"={P}!$B$13", f"={P}!$B$18", f"={P}!$B$8", False),
    ("纱线", "国内采购", "越南境内非EPE企业", 0, 0, 0, 0, f"={P}!$B$8", True),
    ("纱线", "一般贸易（自 EPE 采购，视同进口）", "越南境内EPE企业", f"={P}!$B$16", f"={P}!$B$8", 0, 0, f"={P}!$B$8", False),
]
SALES = [
    ("华特 → HFG → 鞋厂母公司 → 鞋厂（四方）", "出口", "USD", "USD", "T/T 银行转款", 0),
    ("华特 → HFG → 鞋厂母公司（三方）", "出口", "USD", "USD", "T/T 银行转款", f"={P}!$B$19"),
    ("华特 → HFG（华特海外母公司）", "出口", "USD", "USD", "T/T 银行转款", f"={P}!$B$19"),
    ("华特 → 鞋厂（EPE）", "出口", "USD", "USD", "T/T 银行转款", 0),
    ("华特 → 鞋厂（非EPE，内销）", "内销", "VND / USD", "VND", "T/T 银行转款", 0),
]
NOTE_2026 = {
    "一般贸易进口": "进口征 12% 关税 + 8% VAT（2026-12-31 前优惠税率；2027 起或回 10%）。关税按现行 HS 核。",
    "保税进口 / 进料加工": "保税不征，但须料件核销；转内销时补关税+VAT。",
    "保税进口（原料）": "保税不征；转内销时补 3% 关税 + 8% VAT，并按现行反倾销决定（3.57%–17.45%/出口商）计征反倾销。",
    "国内采购": "华特为非 EPE → 采购必担 8% VAT（进项），出口退、内销抵；资金占用 75 天。",
    "一般贸易（自 EPE 采购，视同进口）": "自 EPE 采购视同进口，征 3% 关税 + 8% VAT；「供应商出口复进口」路径可行性原表标注待确认。",
}
GUIDE = {
    ("一般贸易进口", "出口"): "① 报关单 E11/E15 ② 商业发票 USD ③ 装箱单 ④ 提单 ⑤ 原产地证（争取 ACFTA 减让）⑥ 合同。开 USD 发票，出口 VAT 0%。",
    ("一般贸易进口", "内销"): "① 开 VND 发票（含 8% VAT）② 送货单 ③ 合同/订单 ④ 进口报关单留档。注意：进口环节已缴关税不得再抵。",
    ("保税进口 / 进料加工", "出口"): "① 保税料件台账 ② 出口报关单（E62 等）③ 单耗/损耗记录 ④ 核销表。严禁内销未补税。",
    ("保税进口 / 进料加工", "内销"): "① 转内销报关/补税申报 ② 补缴关税+VAT 凭证 ③ 开 VND 发票 ④ 料件核销账。属高风险：工业区规定与投资执照经营范围须先核。",
    ("保税进口（原料）", "出口"): "① 保税进口报关 ② 出口报关单 ③ 单耗核销 ④ 出口退税申报（合同+非现金收汇凭证+报关单，NĐ 181/2025 Đ18）。",
    ("保税进口（原料）", "内销"): "① 补 3% 关税 + 8% VAT ② 反倾销税按出口商档位计 ③ 开 VND 发票 ④ 单独台账。⚠️ 高风险：境内有同类料却长期进口反倾销料用于内销 → 稽查重点。",
    ("国内采购", "出口"): "① 取得 VND 进项发票（8%）② 出口报关单 ③ 收汇凭证 ④ 退税申报。资金占用 75 天须纳入资金预算。",
    ("国内采购", "内销"): "① 销项 8% − 进项 8% 抵扣 ② 开 VND 发票 ③ 送货单。与非 EPE 交易只能 VND 结算。",
    ("一般贸易（自 EPE 采购，视同进口）", "出口"): "① EPE 出口报关 + 华特进口报关（视同进口）② 缴 3% 关税 + 8% VAT ③ 出口退税申报（3% 关税部分 1 年 1 报）。路径可行性待海关确认。",
    ("一般贸易（自 EPE 采购，视同进口）", "内销"): "① 视同进口补 3% 关税 + 8% VAT ② 开 VND 发票 ③ 承包商税判定（四方协议关系）。",
}

row = hdr_row + 1
first = row
for pi, (mat, mode, sup, jt, kv, adm, mdt, mvt, dom_input) in enumerate(PURCH, start=1):
    for si, (path, out_kind, buy_inv, sell_inv, pay, ctr) in enumerate(SALES, start=1):
        rid = f"T{pi}-{si:02d}"
        exp = (out_kind == "出口")
        vals = {
            1: rid, 2: mat, 3: mode, 4: sup, 5: path, 6: out_kind,
            7: buy_inv, 8: sell_inv, 9: pay,
            10: jt, 11: kv, 12: adm, 13: mdt, 14: mvt,
            15: 1.0 if exp else 0, 16: ctr,
            17: f"={P}!$B$6",
            18: f"=Q{row}*(1-{P}!$B$4)",
            19: f"=IF(F{row}=\"内销\",R{row}*L{row},0)",
            20: f"=R{row}*J{row}",
            21: f"=IF(K{row}=0,0,(R{row}+T{row})*K{row})",
            22: f"=IF(F{row}=\"内销\",R{row}*M{row},0)",
            23: f"=IF(F{row}=\"内销\",(R{row}+V{row})*N{row},0)",
            24: f"=IF(F{row}=\"内销\",Q{row}*{P}!$B$8,0)",
            25: (f"=U{row}+W{row}+R{row}*{P}!$B$8" if dom_input else f"=U{row}+W{row}"),
            26: f"=MAX(X{row}-Y{row},0)",
            27: f"=IF(F{row}=\"出口\",Y{row},0)",
            28: f"=Q{row}*P{row}",
            29: f"=S{row}+T{row}+V{row}+Z{row}+AB{row}",
            30: f"=Q{row}-R{row}-S{row}-T{row}-V{row}-AB{row}",
            31: f"=MAX(AC{row},0)*{P}!$B$10",
            32: f"=AA{row}",
            33: f"=AF{row}*{P}!$B$11*{P}!$B$12/365",
            34: f"=AC{row}+AE{row}+AG{row}",
            35: f"=AH{row}/Q{row}",
            36: f"=RANK(AH{row},$AH${first}:$AH${first+24},1)",
            37: NOTE_2026[mode],
            38: GUIDE[(mode, out_kind)],
        }
        for ci, v in vals.items():
            c = ws.cell(row=row, column=ci, value=v)
            c.border = BORDER
            c.font = Font(size=9)
            c.alignment = Alignment(vertical="center", wrap_text=ci in (3, 5, 37, 38),
                                    horizontal="center" if ci in (1, 2, 6, 7, 8, 15, 36) else "left")
            if ci in (10, 11, 12, 13, 14, 15, 16):
                c.number_format = "0.00%"
                c.fill = PatternFill("solid", fgColor="DDEBF7")
            if ci in (17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34):
                c.number_format = "#,##0"
                c.fill = PatternFill("solid", fgColor=C_CALC)
            if ci == 35:
                c.number_format = "0.00%"
                c.fill = PatternFill("solid", fgColor=C_CALC)
            if ci == 34:
                c.font = Font(size=9, bold=True)
            if ci in (37, 38):
                c.fill = PatternFill("solid", fgColor=C_NOTE)
        ws.row_dimensions[row].height = 44
        row += 1

last = row - 1
ws.freeze_panes = "F5"
ws.auto_filter.ref = f"A{hdr_row}:AL{last}"

# 底部汇总
row += 1
ws.cell(row=row, column=1, value="全表口径校验（改参数后自动变）").font = Font(bold=True, size=11, color=C_HEAD)
chk = [
    ("最低综合税负（VND/kg）", f"=MIN(AH{first}:AH{last})"),
    ("最高综合税负（VND/kg）", f"=MAX(AH{first}:AH{last})"),
    ("最低税负率", f"=MIN(AI{first}:AI{last})"),
    ("最高税负率", f"=MAX(AI{first}:AI{last})"),
    ("最高/最低倍数", f"=MAX(AH{first}:AH{last})/MIN(AH{first}:AH{last})"),
    ("出口模式平均税负", f"=AVERAGEIF(F{first}:F{last},\"出口\",AH{first}:AH{last})"),
    ("内销模式平均税负", f"=AVERAGEIF(F{first}:F{last},\"内销\",AH{first}:AH{last})"),
]
for i, (k, f) in enumerate(chk):
    rr = row + 1 + i
    ws.cell(row=rr, column=1, value=k).font = Font(size=10)
    c = ws.cell(row=rr, column=2, value=f)
    c.font = Font(size=10, bold=True)
    c.number_format = "0.00%" if "率" in k or "倍数" in k else "#,##0"
    c.fill = PatternFill("solid", fgColor=C_CALC)
    c.border = BORDER

# ------------------------------------------------------------------ 03 口径与来源
ws3 = wb.create_sheet("03-口径与来源")
ws3["A1"] = "政策口径与法条来源（2023 原表 vs 2026 现行）"
ws3["A1"].font = F_TITLE
ws3["A2"] = "核验方式：Brave 联网检索 2 轮（2026-10-20）。「已核」= 找到官方/权威二手来源；「待核」= 未取得原文或存在适用不确定性。不改写为确定结论。"
ws3["A2"].font = Font(size=9, color="C00000")
h = ["编号", "政策项", "原表 2023 口径", "2026 现行口径", "依据 / 来源", "状态", "对模型的影响"]
for i, x in enumerate(h, start=1):
    c = ws3.cell(row=4, column=i, value=x)
    c.font = Font(bold=True, size=10, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=C_HEAD)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = BORDER
rows3 = [
    ("S01", "增值税标准税率", "10%（备注「23年1月恢复10%」）",
     "10% 标率下减征 2% → 实际 **8%**，适用期 2025-07-01 至 **2026-12-31**",
     "Nghị quyết 204/2025/QH15（2025-06-17）+ Nghị định 174/2025/NĐ-CP", "已核",
     "参数区 B8=8%；B9=10%（2027 起或回 10%）"),
    ("S02", "VAT 法体系", "未列法条",
     "Luật Thuế GTGT（48/2024/QH15）+ **Nghị định 181/2025/NĐ-CP**，2026-01-01 起施行",
     "vanban.chinhphu.vn / minvoice.vn / luatvietnam.vn", "已核",
     "旧 TT 219/2013、TT 78/2014+96/2015 口径不可照搬"),
    ("S03", "VAT 8% 适用范围", "未区分", "适用原 10% 的货物/服务；电信、金融银行、房地产、金属制品等被排除；**纺织纱线/布料是否在附录排除清单内需逐项核**",
     "NĐ 174/2025/NĐ-CP Điều 1 + Phụ lục", "待核", "若纱线/布被排除 → B8 改 10%，全表变动"),
    ("S04", "企业所得税法", "未列法条", "**Luật 67/2025/QH15（CIT 法）**",
     "vanban.chinhphu.vn docid=214607", "已核（法名）",
     "⚠️ 上一版我误记为「67/2025=VAT 法」，此处更正：67/2025 是 CIT 法"),
    ("S05", "CIT 税率", "初稿V2 列 20%；FOC 行见 0.2", "Daryl 指定按 **10%** 建模",
     "Daryl 2026-10-20 指令", "待确认依据",
     "参数区 B10；若实际为 20% → 改 B10 即全表联动"),
    ("S06", "出口适用 0% 的条件", "未列", "须同时具备：① 合同 ② 非现金支付凭证（收汇）③ 报关单（NĐ 181/2025 Điều 18）",
     "NĐ 181/2025/NĐ-CP Điều 18", "已核",
     "FOC / 无偿出货**无收汇 → 不满足 0% 与退税条件**，本模型对出口行的退税结论以此为边界"),
    ("S07", "增值税退税情形", "「出口则退税」笼统表述", "NĐ 181/2025 Điều 29 列明可退情形（含委托出口、加工结转、境外工程等）",
     "NĐ 181/2025/NĐ-CP Điều 29", "已核（条文）", "支持「出口退税回流」列的建模假设"),
    ("S08", "反倾销 · 中国纱线", "17.45%（单一值）",
     "**按出口商/生产商分档 3.57%–17.45%**；续期 5 年，2026-10-16 至 2031-10-15",
     "Quyết định 2652/QĐ-BCT（2026-10-13）", "已核",
     "参数区 B13=17.45%（上限，保守）/ B14=3.57%"),
    ("S09", "进口关税 · 成品布 12%", "12%", "未取得现行 HS 税率原文",
     "—", "待核", "参数区 B15"),
    ("S10", "进口关税 · 自 EPE 采购纱线 3%", "3%", "未取得现行原文；「供应商出口复进口」路径可行性原表即标注待确认",
     "—", "待核", "参数区 B16"),
    ("S11", "保税 / 进料加工免税", "免税", "保税制度框架未变；须料件核销与单耗申报",
     "原表 + 实务", "待核（细则）", "参数区 B17=0"),
    ("S12", "内销补关税（保税料件转内销）3%", "3%", "未取得现行原文",
     "—", "待核", "参数区 B18"),
    ("S13", "外商承包税 1%", "1%；四方协议按加工/销售关系判定由谁缴", "未取得现行判定规则原文",
     "—", "待核", "参数区 B19；四方（S1）按 0 建模"),
    ("S14", "越南原产地 30% 增值", "最后加工 + HS 转换 + LVC ≥30%", "未取得现行 LVC 规则原文",
     "—", "待核", "影响 ACFTA 优惠税率，本模型未计优惠"),
    ("S15", "退税到账周期 60–90 天", "60–90 天，实际 2 个月申请一次", "未核（操作口径）",
     "原表备注", "待核", "参数区 B12=75 天"),
    ("S16", "资金成本年化 4.5%", "原表未计", "Daryl 指定",
     "Daryl 2026-10-20 指令", "已定", "参数区 B11"),
]
for i, x in enumerate(rows3, start=5):
    for j, v in enumerate(x, start=1):
        c = ws3.cell(row=i, column=j, value=v)
        c.font = Font(size=9)
        c.border = BORDER
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if j == 6:
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.fill = PatternFill("solid", fgColor="C6EFCE" if v.startswith("已") else ("FFEB9C" if v == "待核" else "FCE4D6"))
    ws3.row_dimensions[i].height = 46
for col, w in zip("ABCDEFG", [8, 24, 30, 52, 34, 12, 40]):
    ws3.column_dimensions[col].width = w
ws3.freeze_panes = "A5"

# ------------------------------------------------------------------ 04 操作指引
ws4 = wb.create_sheet("04-操作指引")
ws4["A1"] = "内部操作指引 —— 按交易模式 × 出货性质执行"
ws4["A1"].font = F_TITLE
ws4["A2"] = "这一页是「照着做」的版本；金额与税负看 01-总表。风险项标 🔴。"
ws4["A2"].font = Font(size=9, color="C00000")
h4 = ["序号", "交易模式", "出货性质", "谁开采购票", "谁开销货票", "开票币别", "是否报关", "报关类型（待关务确认）", "必备单据", "关键控制点 / 风险"]
for i, x in enumerate(h4, start=1):
    c = ws4.cell(row=4, column=i, value=x)
    c.font = Font(bold=True, size=10, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=C_HEAD)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = BORDER
g4 = [
    ("成品布 一般贸易进口", "出口", "境外中国供应商（USD 商业发票）", "华特开 USD 发票给 HFG", "USD", "是", "E11 / E15（一般贸易出口）", "合同、进口报关单、出口报关单、装箱单、提单、原产地证", "进口已缴 12% 关税不可退；出口退 VAT；产地证可争取减按 7%/5%/0%"),
    ("成品布 一般贸易进口", "内销", "境外中国供应商（USD）", "华特开 VND 发票（含 8% VAT）", "VND", "否（境内交货）", "—", "合同/订单、发票、送货单、进口报关单留档", "🔴 内销不得再抵进口关税；注意境内销售与「保税料件」混用"),
    ("胚布 保税进口/进料加工", "出口", "境外中国公司（USD）", "华特开 USD 发票", "USD", "是", "E62（保税/加工出口，待关务确认）", "保税进口报关、出口报关单、单耗表、核销表", "🔴 料件必须核销；严禁未补税内销"),
    ("胚布 保税进口/进料加工", "内销", "境外中国公司（USD）", "华特开 VND 发票", "VND", "是（转内销补税）", "转内销补税申报", "补关税+VAT 凭证、核销台账、投资执照与环保许可", "🔴🔴 原表已标：染色加工违反工业区规定/投资执照经营范围，存在连带稽查风险"),
    ("纱线 保税进口", "出口", "境外中国公司（USD）", "华特开 USD 发票", "USD", "是", "E62 / 保税加工出口", "保税进口报关、出口报关单、单耗、核销、收汇凭证", "出口 0% 需「合同+非现金收汇+报关单」三件齐（NĐ 181/2025 Đ18）"),
    ("纱线 保税进口", "内销", "境外中国公司（USD）", "华特开 VND 发票", "VND", "是（补税）", "转内销补 3% 关税 + 8% VAT", "补税凭证、反倾销税计征凭证、内销台账", "🔴🔴 反倾销 3.57%–17.45% 按出口商计；「境内有同类料却长期进口反倾销料用于内销」= 稽查重点"),
    ("纱线 国内采购", "出口", "越南境内非 EPE 企业（VND 含 8% 进项）", "华特开 USD 发票", "USD", "是", "E11 / E15", "VND 进项发票、出口报关单、收汇凭证、退税申报表", "非 EPE 与境内企业交易只能 VND 结算；退税 75 天资金占用须进预算"),
    ("纱线 国内采购", "内销", "越南境内非 EPE 企业（VND）", "华特开 VND 发票（8%）", "VND", "否", "—", "进项发票、销项发票、送货单", "销项 8% − 进项 8%，无退税；现金流最健康"),
    ("纱线 自 EPE 采购（视同进口）", "出口", "越南境内 EPE 企业（视同进口）", "华特开 USD 发票", "USD", "是", "EPE 出口报关 + 华特进口报关", "双向报关单、3% 关税缴款书、收汇凭证、退税申报（3% 关税部分 1 年 1 报）", "🔴 原表标「供应商需出口复进口，待确认是否可行」→ 未获海关确认前不落地"),
    ("纱线 自 EPE 采购（视同进口）", "内销", "越南境内 EPE 企业（视同进口）", "华特开 VND 发票", "VND", "是", "视同进口报关 + 内销", "进口报关单、3% 关税+VAT 缴款书、销项发票", "四方协议下承包商税判定：加工关系免 / 销售关系由鞋厂母公司缴（待核现行规则）"),
]
for i, x in enumerate(g4, start=5):
    ws4.cell(row=i, column=1, value=i - 4)
    for j, v in enumerate(x, start=2):
        c = ws4.cell(row=i, column=j, value=v)
        c.font = Font(size=9)
        c.border = BORDER
        c.alignment = Alignment(wrap_text=True, vertical="top")
    ws4.cell(row=i, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[i].height = 62
for col, w in zip("ABCDEFGHIJ", [6, 24, 10, 26, 24, 10, 14, 22, 44, 46]):
    ws4.column_dimensions[col].width = w
ws4.freeze_panes = "C5"

# ------------------------------------------------------------------ 00 使用说明
ws0 = wb.create_sheet("00-使用说明", 0)
ws0["A1"] = "越南华特 · 税负测算模型 + 内部操作指引 v2"
ws0["A1"].font = F_TITLE
lines = [
    ("", ""),
    ("版本", "v2 / 2026-10-20 / Balance"),
    ("口径确认（Daryl 2026-10-20）", "① 单位口径 = VND/kg（每 1 公斤成品）② 成本结构留在参数区、由「加工增值率」一个参数驱动（默认 30%，待查实际值）③ CIT 按 10%、资金占用成本按年化 4.5%，两者都计入单位税负"),
    ("结构与 v1 的差别", "v1 是「整理版」（14 个 sheet 做归档）；v2 是「模型版」—— 一张总表、主维度 = 交易模式 × 销售对象、全部金额用公式驱动，改参数即联动。原文件 2023 版仅作参考，未再归档进本文件。"),
    ("", ""),
    ("三步上手", ""),
    ("第 1 步", "打开 02-参数区，看黄底格。当前是占位值：成品售价 180,000 VND/kg、VND/USD 26,000。"),
    ("第 2 步", "把 Daryl 查出的「加工增值率」填到 B4（默认 30%）。原料成本占比自动 = 1 − B4。"),
    ("第 3 步", "回到 01-总表，看 Q–AI 列自动重算；看「成本排名」列找最省 / 最贵的模式。"),
    ("", ""),
    ("工作表说明", ""),
    ("01-总表", "25 行 = 5 种交易模式 × 5 种销售路径。列分 5 组：模式识别｜政策口径（引用参数区）｜税额计算｜汇总对比｜2026 政策备注 + 操作指引。底部有全表校验（最低/最高/出口均值/内销均值）。"),
    ("02-参数区", "唯一输入页。税率、售价、增值率、资金成本、退税天数全在这里。"),
    ("03-口径与来源", "16 条政策口径，逐条给「2023 原表口径 vs 2026 现行口径 + 法条/来源 + 状态」。标「待核」的我没查实，不当结论用。"),
    ("04-操作指引", "照着做的版本：谁开票、开什么币、报不报关、要哪些单据、控制点。🔴 标风险项。"),
    ("", ""),
    ("计算逻辑（透明化）", ""),
    ("原料成本", "= 成品售价 ×（1 − 加工增值率）"),
    ("反倾销税", "= 原料成本 × 反倾销率（仅内销时实际发生；出口复出口不征）"),
    ("进口关税", "= 原料成本 × 关税率（保税 / 进料加工 = 0）"),
    ("进口 VAT", "= （原料成本 + 关税）× VAT 率；保税 = 0"),
    ("内销补税", "= 原料成本 × 补关税率 ＋ （原料成本 + 补关税）× 补 VAT 率（仅内销）"),
    ("销项 VAT", "= 售价 × 8%（仅内销；出口 0%）"),
    ("内销 VAT 净缴", "= MAX（销项 − 可抵扣进项，0）"),
    ("出口退税回流", "= 可抵扣进项（出口行全退，按 100% 退税建模）"),
    ("承包税", "= 售价 × 1%（四方协议行按 0）"),
    ("税负合计", "= 反倾销 + 进口关税 + 内销补关税 + 内销 VAT 净缴 + 承包税"),
    ("CIT", "= MAX（售价 − 原料成本 − 上述不可抵扣税费，0）× 10%"),
    ("资金占用成本", "= 退税额 × 4.5% × 75 / 365"),
    ("综合税负", "= 税负合计 + CIT + 资金占用成本  ← 这是横向比较用的「单位税负金额」"),
    ("", ""),
    ("诚实边界（必须看）", ""),
    ("⚠️ 1", "成品售价 180,000 VND/kg 是**占位值**，不是实际售价。绝对金额在填入真值前不能对外用，只能做「模式间相对比较」。"),
    ("⚠️ 2", "CIT 10% 是你指定，非法定标准 20%。法定标准与优惠适用条件未核，如需我核请说一声。"),
    ("⚠️ 3", "VAT 目前按 8%（NQ 204/2025/QH15 + NĐ 174/2025/NĐ-CP，至 2026-12-31）。但**纺织纱线/布是否在 174 号法令的排除清单内，我还没逐项核** → 03 表标「待核」。"),
    ("⚠️ 4", "反倾销 17.45% 是**上限**，实际按中国出口商分档 3.57%–17.45%。模型暂取上限（保守）。"),
    ("⚠️ 5", "8 项税率/规则（关税 12%/3%、承包税 1%、原产地 30%、退税周期等）为 2023 原表口径，现行未逐条核到原文 → 03 表全部标「待核」。"),
    ("⚠️ 6", "CIT 用「售价 − 原料成本 − 不可抵扣税费」简化利润，未含人工/折旧/期间费用 → CIT 金额偏高，属保守估计。"),
    ("", ""),
    ("下一步（等你定）", "A. 你给真售价 + 增值率 → 出正式数字  B. 我逐条核 03 表「待核」项（需更多检索轮次）  C. 做 HTML 交互版（改参数实时出图）  D. 加「按实际业务量×月」的年度税负预测"),
]
r = 2
for a, b in lines:
    ca = ws0.cell(row=r, column=1, value=a)
    ca.font = Font(bold=True, size=10)
    cb = ws0.cell(row=r, column=2, value=b)
    cb.font = Font(size=9 if b else 10)
    cb.alignment = Alignment(wrap_text=True, vertical="top")
    if a in ("工作表说明", "计算逻辑（透明化）", "诚实边界（必须看）", "三步上手", "下一步（等你定）"):
        ca.font = Font(bold=True, size=11, color=C_HEAD)
    r += 1
ws0.column_dimensions["A"].width = 24
ws0.column_dimensions["B"].width = 122

# 顺序: 00 说明 / 01 总表 / 02 参数区 / 03 口径 / 04 指引
wb._sheets = [wb["00-使用说明"], wb["01-总表"], wb["02-参数区"], wb["03-口径与来源"], wb["04-操作指引"]]

os.makedirs("deliverables", exist_ok=True)
wb.save(OUT)
print("saved:", OUT)
print("总表行:", last - first + 1)
print("sheets:", wb.sheetnames)
