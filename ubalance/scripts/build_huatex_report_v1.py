# -*- coding: utf-8 -*-
"""
越南华特经营模式 · 领导汇报稿 v1（2026-10-29）
结构遵循 workspace 小专题报告模板 v1.1：核心层「报告」一屏看完 + 模块层（对比/风险/敏感性）+ 口径与假设
数据源：work/params-excel/cfg.json（HTML v4.5 口径）+ deliverables/越南华特经营模式-销售出货与采购入库模式-v1-20261022.xlsx
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = "deliverables/越南华特经营模式-汇报稿-v1-20261029.xlsx"

DARK = "1F3864"
ACCENT = "2E5C8A"
LIGHT = "D9E2F3"
GREY = "F2F2F2"
GREEN = "C6EFCE"
AMBER = "FFEB9C"
RED = "FFC7CE"
WHITE = "FFFFFF"

FONT = "微软雅黑"

thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)


def title_row(ws, row, ncols, text, sub=None):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(name=FONT, size=15, bold=True, color=WHITE)
    c.fill = PatternFill("solid", fgColor=DARK)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[row].height = 30
    if sub:
        ws.merge_cells(start_row=row + 1, start_column=1, end_row=row + 1, end_column=ncols)
        c2 = ws.cell(row=row + 1, column=1, value=sub)
        c2.font = Font(name=FONT, size=9, italic=True, color="595959")
        c2.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws.row_dimensions[row + 1].height = 18


def section(ws, row, ncols, text):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(name=FONT, size=11, bold=True, color=WHITE)
    c.fill = PatternFill("solid", fgColor=ACCENT)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[row].height = 22


def header(ws, row, values, height=26):
    for i, v in enumerate(values, start=1):
        c = ws.cell(row=row, column=i, value=v)
        c.font = Font(name=FONT, size=9.5, bold=True, color="1F3864")
        c.fill = PatternFill("solid", fgColor=LIGHT)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDER
    ws.row_dimensions[row].height = height


def body(ws, row, values, fills=None, bold_first=False, wrap=True, size=9.5, height=None):
    for i, v in enumerate(values, start=1):
        c = ws.cell(row=row, column=i, value=v)
        c.font = Font(name=FONT, size=size, bold=(bold_first and i == 1))
        c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=wrap)
        c.border = BORDER
        if fills and i in fills:
            c.fill = PatternFill("solid", fgColor=fills[i])
    if height:
        ws.row_dimensions[row].height = height


def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w


def print_setup(ws, last_col, last_row, repeat_rows=None, landscape=True):
    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_area = f"A1:{get_column_letter(last_col)}{last_row}"
    if repeat_rows:
        ws.print_title_rows = repeat_rows
    ws.sheet_view.showGridLines = False


# ============ 数据 ============
SALES = [
    ("S1-01", "离境出口（FOB/CIF/CIP）", "Huatex（卖方/生产）→ 境外客户（买方）｜收货方＝境外，货物实际离境",
     0, "境外买方（不开给境内任何方）", "出口报关（一般贸易）",
     "① 货物实际离境 ② 合同＋非现金收汇＋报关单三件齐",
     "无真实收汇或第三方代付 → 0% 与退税双双被拒", "✅ 推荐｜最标准路径", "green"),
    ("S1-02", "四方合同 · 收货＝越南 EPE", "A 境外销售方｜B Huatex 供货｜C 境外买方｜D 越南 EPE 收货",
     0, "合同买方 C（境外）——绝不开给 D", "E62 就地出口；EPE 办就地进口",
     "买方为境外商人且无常设机构／合同书面指定交货第三方／买方经银行付款／E62 完成／SXXK 核销",
     "E62 不进核销 → 补进口税；发票开给 D ＝ 直接打成内销", "✅ 推荐｜结构最干净", "green"),
    ("S1-03", "四方合同 · 收货＝越南本地（买断）", "境外买方签约｜Huatex 生产｜越南本地企业买断收货，货权转移",
     0, "合同买方（境外）", "E62；收货方办就地进口",
     "同 S1-02 四要件；且收货方须真实买断、自行缴进口关税与 VAT、货款由境外买方支付",
     "五条任一条踩线即打成内销：票开给收货方／收货方付款／无指定交货条款／买方仅通道／非真实买断",
     "⚠️ 高风险｜凭证要求最严", "amber"),
    ("S1-04", "四方合同 · 收货＝越南代工厂", "境外买方签约｜Huatex 生产｜代工厂收货加工，货权不转移",
     0, "合同买方（境外）", "E62；代工厂按「加工 nhập gia công」办就地进口",
     "① 代工性质可证（货权不转移）② 加工后复出口 ③ 出口通关后 15 天内通报 Mẫu 22",
     "被认定为买断 → 代工厂补进口关税与 VAT；加工后未复出口 → 免税失效", "🟡 可用｜须加工合同支撑", "amber"),
    ("S1-05", "卖方直供 · 买方＝越南 EPE", "Huatex（卖方）→ 越南 EPE（买方且收货方）",
     0, "越南 EPE（买方＝收货方）", "E62；EPE 办就地进口",
     "① 货物真实进入非关税区 ② 就地进出口报关齐备 ③ 已收汇",
     "「买方是 EPE」≠ 视同出口：货未进非关税区 → 0% 不成立，全额按内销 8%", "✅ 推荐｜最常见最简单", "green"),
    ("S1-06", "买方＝EPE、收货＝本地企业", "越南 EPE 买入｜越南本地企业收货——货从不进 EPE 非关税区",
     None, "—（该结构不存在合规开票方式）", "—（EPE 无法办就地进口）",
     "—（自相矛盾）", "票货分离／过票；本地企业无报关收货＝无证进口（行政甚至刑事风险）",
     "❌ 不适用｜商业上不成立", "red"),
    ("S1-07", "内销（买方＝收货方＝本地企业）", "Huatex（卖方）→ 越南本地企业（买方＝收货方，非 EPE）",
     8, "越南本地企业（买方）", "无需报关",
     "① 买卖双方均为越南居民 ② 货物境内交付 ③ VND 结算",
     "保税/免税料件做内销未先补税 ＝ 未补税内销（稽查重点）；境内交易外币结算不合规",
     "✅ 推荐｜常规内销", "green"),
    ("S1-08", "买方本地＋收货 EPE · 结构 A", "Huatex 内销开票给 C（本地企业）→ C 报就地出口 → D EPE 收货",
     8, "C（越南本地企业买方）", "Huatex 不报关；C 报就地出口",
     "C 具备出口资质与实际出口行为；一条货只有一次出口＋一次进口报关",
     "C 无出口资质则报关链断裂，Huatex 的 8% 白付；放弃 0% 多占 8% 现金流（进项可抵则净影响有限）",
     "✅ 推荐｜报关链与商业链最对齐", "green"),
    ("S1-09", "买方本地＋收货 EPE · 结构 B", "Huatex 直接 E62 就地出口，买方须改为境外实体，C 退出链条",
     0, "境外买方（须重构合同主体）", "E62；EPE 办就地进口",
     "C 必须从商业链退出或能解释为境外买方的下家；买方为境外实体且实际付款",
     "保留四层全开票（Huatex→C→D 同时又有境外买方开票）＝报关链对不上商业链，必有一层过票",
     "⚠️ 待关务确认｜报关单出口方写谁未定", "amber"),
]

PURCHASE = [
    ("P1-01", "纱线", "本地采购", "越南境内非 EPE 纱厂", "内销/出口均可用", "—", "8%（可抵）", "—", "否",
     "税负最轻、周期最短；但供应商若为 EPE/保税则不能开 8% 发票", "✅ 内销首选", "green"),
    ("P1-02", "纱线", "一般贸易进口", "境外供应商（中国等）", "内销/出口均可用", "约 3%（待核 HS）", "8%/10%（可抵）",
     "3.57%–17.45%（按出口商分档）", "否（完税后可自由处置）",
     "关税＋反倾销刚性进成本，不可退 = 最大成本项；原产地证不全可能被套最高档", "🟡 内销时慎用", "amber"),
    ("P1-03", "纱线", "保税进口 / SXXK", "境外供应商（保税）", "必须复出口核销", "0（暂不征）", "0（暂不征）", "0（复出口不征）",
     "✅ 是",
     "出口业务最省：不占关税与 VAT 资金；但转内销必须先补税（关税＋VAT＋反倾销）", "✅ 出口首选", "green"),
    ("P1-04", "纱线", "自 EPE／非关税区采购", "越南境内 EPE 企业", "内销/出口均可用", "视同进口征（按 HS）", "8%/10%（可抵）",
     "视同进口是否计征待关务确认", "否",
     "报关类型选错（误用 A42 等）会被追税；部分代理称可免，须取关务书面确认", "⚠️ 待关务确认", "amber"),
    ("P2-01", "胚布", "本地采购", "越南境内非 EPE 织造厂", "内销/出口均可用", "—", "8%（可抵）", "—", "否",
     "税负最轻；需评估本地货源规格与产能是否满足", "✅ 内销首选", "green"),
    ("P2-02", "胚布", "一般贸易进口", "境外供应商（中国等）", "内销/出口均可用", "约 12%（待核 HS）", "8%/10%（可抵）",
     "待核（布类适用范围）", "否",
     "关税刚性进成本；进口后仅染色加工再内销，另涉工业区规定/投资执照问题", "🟡 待核", "amber"),
    ("P2-03", "胚布", "进料加工 / 保税", "境外供应商（进料加工）", "必须复出口核销", "0（暂不征）", "0（暂不征）", "0（复出口不征）",
     "✅ 是",
     "出口最省；但保税胚布染色加工后内销＝违反工业区规定/投资执照（高危）", "✅ 出口首选（内销禁用）", "green"),
    ("P2-04", "胚布", "自 EPE／非关税区采购", "越南境内 EPE 企业", "内销/出口", "视同进口征", "8%/10%（可抵）", "待核", "否",
     "同 P1-04，报关类型选择为核心风险点", "⚠️ 待关务确认", "amber"),
    ("P3-01", "成品布", "本地采购", "越南境内染整/织造厂", "内销/出口均可用", "—", "8%（可抵）", "—", "否",
     "单价通常最贵（含上游利润），但税负最轻、周期最短", "✅ 内销首选", "green"),
    ("P3-02", "成品布", "一般贸易进口", "境外供应商（中国等）", "内销/出口均可用", "约 12%（待核 HS）", "8%/10%（可抵）", "待核", "否",
     "关税＋VAT 全额先缴且关税不可退，税负最刚性；纯贸易转售毛利最薄", "⚠️ 税负最重", "red"),
    ("P3-03", "成品布", "保税进口（复出口用）", "境外供应商（保税）", "必须复出口核销", "0（暂不征）", "0（暂不征）", "0（复出口不征）",
     "✅ 是",
     "无实质加工直接保税转售，海关可能质疑保税适用性", "⚠️ 待关务确认", "amber"),
    ("P4-01", "辅料／化学品", "本地采购", "越南境内供应商", "内销/出口均可用", "—", "8%（可抵）", "—", "否",
     "供应商资质与 MSDS 合规（环保/消防）；出口退税需按单耗归集", "✅ 常规", "green"),
]

REDLINES = [
    ("发票开给越南收货方（D/C）", "S1-02/03/04 结构下把发票开给境内收货方", "出口 0% 直接被打成内销，补 8% 销项＋滞纳金罚息", "S1-02/03/04", "发票开具审批：境内收货方一律不得为受票方"),
    ("E62 未进入保税核销", "报了 E62 但未与 SXXK 料件核销配对", "补征进口关税＋VAT＋反倾销，金额可能大于省下的税", "S1-02/03/09", "关务按月核对 E62 清单与核销手册"),
    ("无真实收汇 / 第三方代付", "货款由关联方或第三方代付，与合同主体不一致", "0% 与出口退税双双被拒，全额转内销", "S1-01/02/03", "收汇水单主体＝合同买方，逐笔勾稽"),
    ("保税料件未补税即内销", "SXXK/进料加工料件直接做内销未办补税", "未补税内销＝重大稽查风险，补税＋滞纳金＋罚款", "S1-07 + P1-03/P2-03", "内销订单先查料件来源，保税料先补税"),
    ("四层全开票 / 过票", "Huatex→C→D 开票同时又有境外买方开票，报关却写 Huatex", "报关链与商业链不符，必有一层过票，属稽查必查项", "S1-09", "结构 B 前先完成合同主体重构"),
    ("票货分离（结构 S1-06）", "EPE 买入但货直接交本地企业、不进非关税区", "无证进口，行政甚至刑事风险，比补税严重", "S1-06", "该结构一律不接单；如客户要求，改走 S1-08"),
    ("代工厂未按期通报 Mẫu 22", "出口通关后 15 天内未向海关通报", "加工免税条件失效，代工厂补税连带 Huatex 举证困难", "S1-04", "加工业务设 15 天通报台账"),
    ("境内交易外币结算", "越南境内买卖用 USD 结算", "违反 TT 32/2013，外汇违规处罚", "S1-07/08", "境内合同强制 VND 计价"),
    ("原产地证不全", "进口纱线无有效原产地证或出口商不在低档名单", "反倾销被套最高档 17.45%，成本骤增", "P1-02", "进口前核 C/O 与出口商档位"),
    ("核销单耗不平", "保税进口量与出口成品单耗不匹配", "核销不通过 → 补税＋滞纳金；差额按内销处理", "P1-03/P2-03/P3-03", "每月单耗对平，异常当月解决"),
]

PENDING = [
    ("CIT 适用税率：10% 还是 20%", "参数表现在填 10%，但标准税率 20%，10% 须有优惠税率凭证（投资优惠/高新等）", "高：直接影响净利润测算口径",
     "Daryl（取优惠批文）", "汇报前"),
    ("进口关税税率按具体 HS 重核", "现用 2023 口径：纱线 3%、布类 12%，2026 现行 MFN 需按 HS 逐项核", "高：关税是刚性成本，1 个点差额即真金白银",
     "关务", "2 周内"),
    ("布类反倾销适用范围", "纱线已明确 3.57%–17.45%，布类是否适用未定", "中：影响成品布/胚布进口成本", "关务＋外部律师", "2 周内"),
    ("自 EPE 视同进口的报关类型", "P1-04/P2-04 报关类型选择未书面确认", "中：选错会被追税", "关务", "2 周内"),
    ("S1-09 报关单出口方归属", "结构 B 下 E62 报关单出口方写 Huatex 还是境外买方", "中：决定结构 B 是否可用", "关务", "2 周内"),
    ("FCT（承包商税）书面答复", "四方结构下境外买方在越是否构成常设机构、是否涉 FCT", "中：影响结构长期稳定性", "税务顾问", "1 个月内"),
]

ACTIONS = [
    ("第 1 个月", "① 出《销售出货模式 SOP》：每模式下「发票开给谁＋报关类型＋必备单证」三件套；② 四方合同模板加「买方书面指定交货第三方」条款；③ 报关类型（E62/A42/加工）书面确认", "模式 SOP v1、合同条款模板、关务确认函", "财务＋关务", "紧急"),
    ("第 2–3 个月", "④ 建 E62 与核销配对台账（月结）；⑤ 保税料件转内销先补税的前置审批；⑥ 收汇水单与合同主体逐笔勾稽机制", "核销台账、补税审批流、收汇勾稽表", "财务＋关务", "高"),
    ("第 4–6 个月", "⑦ 采购端：出口用保税 SXXK、内销用本地采购的分离管理；⑧ 反倾销原产地与出口商档位管控；⑨ 报价模型接入模式税负（含 CIT 优惠确认后重算）", "采购模式对照表、报价模型 v1", "财务＋采购", "中"),
]

BASIS = [
    ("NĐ 181/2025/NĐ-CP（增值税法实施细则）Đ18、Đ29", "S1-01/07/08", "出口 0% 的「合同＋非现金收汇＋报关单」三件齐要求；退税条件"),
    ("Luật 48/2024/QH15（增值税法 2024）Đ14.2", "S1-03", "进口环节缴税凭证可抵扣，就地进口的进项处理"),
    ("TT 38/2015/TT-BTC Đ86.1.c", "S1-02/03/04/09", "境外买方指定越南交货第三方时，销售方仍按出口处理的核心依据"),
    ("QĐ 1357/QĐ-TCHQ", "S1-02/03/04/05/09", "E62 就地出口报关类型定义与适用"),
    ("TT 103/2014/TT-BTC Đ1.2", "S1-02", "FCT（承包商税）适用判断；建议取书面答复"),
    ("NĐ 134/2016/NĐ-CP、NĐ 18/2021/NĐ-CP", "S1-04、P1-03/P2-03", "保税/进料加工/加工（nhập gia công）免税与核销要求"),
    ("NQ 204/2025/QH15 ＋ NĐ 174/2025", "S1-07/08", "内销 VAT 8% 优惠至 2026-12-31；之后若无延续回到 10%"),
    ("TT 32/2013/TT-BTC Đ3-Đ4", "S1-07/08", "境内交易原则上只能以 VND 结算"),
    ("QĐ 2652/QĐ-BCT（2026-10-13）", "P1-02", "中国产纱线反倾销 3.57%–17.45%，续期至 2031-10-15"),
    ("投资执照 / 工业区规定", "P2-02/P2-03", "胚布进口后仅染色加工再内销的合规边界"),
]

PARAMS = [
    ("VAT 出口", "0%", "出口／就地出口，须满足三件齐", "已核实"),
    ("VAT 内销", "8%（至 2026-12-31）", "NQ 204/2025＋NĐ 174/2025，到期回到 10%", "已核实"),
    ("进口关税 · 纱线", "约 3%", "2023 原表口径，须按 HS 重核", "⚠️ 待核"),
    ("进口关税 · 布类", "约 12%", "2023 原表口径，须按 HS 重核", "⚠️ 待核"),
    ("反倾销 · 纱线", "3.57%–17.45%", "按出口商档位；中枢 7.8%（参数表）", "已核实（档位待核）"),
    ("反倾销 · 布类", "待定", "适用范围需外部确认", "⚠️ 待核"),
    ("CIT 企业所得税", "20%（标准）／10%（待证）", "10% 须优惠税率凭证，未取得前按 20% 测算", "⚠️ 待 Daryl"),
    ("汇率 USD/VND", "26,200", "仅用于折算 VND 展示", "已核实"),
    ("测算基准", "每 USD 1,000,000 货值", "敏感性分析单位基数，按实际规模等比放大", "假设"),
    ("VAT 进项可抵比例", "100%", "本报告默认进项可全额抵扣；退税被拒情形见风险表", "假设"),
]

wb = openpyxl.Workbook()

# ==================== 1. 报告（一屏） ====================
ws = wb.active
ws.title = "报告"
widths(ws, {"A": 5, "B": 30, "C": 20, "D": 20, "E": 26, "F": 20})

title_row(ws, 1, 6, "越南华特经营模式梳理与税负影响 · 汇报稿",
          "编制：财务部（Balance）｜日期：2026-10-29｜版本 v1.0｜口径与依据见末页「4-口径与假设」｜内部资料，未经确认请勿外传")

r = 4
section(ws, r, 6, "一、核心结论（先看这里）")
r += 1
conclusions = [
    ("Huatex 的 VAT 率只由两件事决定：发票开给谁、货有没有进非关税区——不看最终客户是谁。",
     "所以「客户是 EPE」不等于免税；「客户是境外公司但货交越南」也不自动成立，必须靠合同条款和报关类型把链条做对。"),
    ("9 个销售模式中，7 个可稳定成立，1 个属商业上不成立，1 个待关务确认。",
     "不成立：S1-06（EPE 买入、本地企业收货，票货分离）；待确认：S1-09（买方本地＋收货 EPE 的结构 B）。"),
    ("推荐主路径：出口走 S1-05（买方即 EPE）与 S1-02（四方收货 EPE）；买方是本地企业而收货是 EPE 时走 S1-08 结构 A；常规内销走 S1-07。",
     "S1-03（本地买断收货）与 S1-04（代工收货）可以用，但凭证要求最严，建议只在客户结构无法改变时才用。"),
    ("真正吃掉利润的不是 VAT，而是进口端的关税与反倾销，以及保税料件转内销的补税。",
     "VAT 是价外税、可抵扣，影响主要是现金流占用；关税（纱线约 3%、布类约 12%）与反倾销（纱线 3.57%–17.45%）一旦发生不可退，是硬成本。"),
    ("采购端最省的组合：出口料件走保税 SXXK／进料加工，内销料件走本地采购；保税料件转内销必须先补税。",
     "13 个采购方案中，纯贸易进口成品布（P3-02）税负最重、毛利最薄，应避免作为常态路径。"),
]
for i, (main, sub) in enumerate(conclusions, start=1):
    ws.cell(row=r, column=1, value=str(i)).font = Font(name=FONT, size=10, bold=True, color=ACCENT)
    ws.cell(row=r, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
    c = ws.cell(row=r, column=2)
    c.value = main + "\n" + sub
    c.font = Font(name=FONT, size=10)
    c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True, indent=1)
    for col in range(1, 7):
        ws.cell(row=r, column=col).border = BORDER
    ws.row_dimensions[r].height = 46
    r += 1

r += 1
section(ws, r, 6, "二、关键数据一览（口径见末页）")
r += 1
header(ws, r, ["", "项目", "取值", "性质", "对决策的影响", "状态"])
r += 1
kpi = [
    ("出口／就地出口 VAT", "0%", "价外税", "凭证不齐即转内销 8%，这是最大的单点风险", "已核实", GREEN),
    ("内销 VAT", "8%（至 2026-12-31）", "价外税", "2027 年起若无延续政策回到 10%，报价需预留", "已核实", GREEN),
    ("进口关税 · 纱线", "约 3%", "刚性成本", "不可退，直接压毛利；税率须按 HS 重核", "待核", AMBER),
    ("进口关税 · 布类", "约 12%", "刚性成本", "布类是成本结构里最重的一项，优先本地替代", "待核", AMBER),
    ("反倾销 · 纱线", "3.57%–17.45%", "刚性成本", "按出口商档位取档，C/O 不全可能被套最高档", "已核实", GREEN),
    ("CIT 企业所得税", "20%（标准）", "所得税", "现参数填 10% 需优惠凭证，未取得前按 20% 测算", "待 Daryl", AMBER),
]
for name, val, nature, impact, status, color in kpi:
    ws.cell(row=r, column=1, value="")
    body(ws, r, ["", name, val, nature, impact, status], fills={6: color}, height=30)
    ws.cell(row=r, column=3).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.cell(row=r, column=6).alignment = Alignment(horizontal="center", vertical="center")
    r += 1

r += 1
section(ws, r, 6, "三、需要领导决策的事项（3 项）")
r += 1
header(ws, r, ["", "决策事项", "为什么现在要定", "选项", "财务建议", "时点"])
r += 1
decisions = [
    ("出口主结构定为 S1-05＋S1-02", "结构决定合同条款与开票规则，晚定则既有订单要返工",
     "A 维持现状按单议／B 统一主结构", "建议 B：主结构统一，S1-03/S1-04 作例外审批", "本月"),
    ("S1-09（结构 B）是否推进", "可拿回 0%，但须重构合同主体与收款路径，涉客户配合",
     "A 放弃（走结构 A 少 8%）／B 推进（须客户改合同）", "建议先取关务书面意见，再按客户逐个评估，不整体推进", "2 周内"),
    ("采购端出口/内销料件分离管理", "混用会导致保税料件未补税内销，属稽查重点",
     "A 现状混用／B 按用途分账管理", "建议 B：系统层面分库分账，成本可控、风险归零", "本季度"),
]
for i, (item, why, opt, rec, when) in enumerate(decisions, start=1):
    body(ws, r, ["", item, why, opt, rec, when], bold_first=False, height=44)
    ws.cell(row=r, column=6).alignment = Alignment(horizontal="center", vertical="center")
    r += 1

r += 1
section(ws, r, 6, "四、⚠️ 口径与限制（诚实标注）")
r += 1
notes = [
    "• 关税税率沿用 2023 原表口径（纱线 3%、布类 12%），2026 现行 MFN 税率必须按具体 HS 编码逐项核对后方可用于报价；本报告中的金额测算均属方向性判断。",
    "• CIT 参数表填 10%，但越南标准企业所得税率为 20%；10% 须有投资优惠/高新技术等凭证。在凭证未取得前，本报告一律按 20% 表述。",
    "• 反倾销税率按出口商档位取值，中国产纱线区间 3.57%–17.45%；不同供应商差异极大，必须逐笔核 C/O。",
    "• 所有测算以「每 USD 1,000,000 货值」为基数，按实际规模等比放大；未考虑资金成本、汇率波动与时间价值。",
    "• 法规解读以本次检索到的条文为准，落地前建议取关务/税务顾问书面意见（尤其 FCT 与 S1-09）。",
]
for n in notes:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    c = ws.cell(row=r, column=1, value=n)
    c.font = Font(name=FONT, size=9, color="C00000")
    c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True, indent=1)
    ws.row_dimensions[r].height = 30
    r += 1

print_setup(ws, 6, r - 1, landscape=True)

# ==================== 2. 销售模式总览 ====================
ws = wb.create_sheet("01-销售模式总览")
widths(ws, {"A": 9, "B": 26, "C": 40, "D": 8, "E": 24, "F": 24, "G": 40, "H": 42, "I": 22})
title_row(ws, 1, 9, "一、销售与出货模式总览（9 种）",
          "读法：一行＝一种交易结构。先看「发票开给谁」＋「报关类型」，再看 VAT 率；结论列＝财务建议。绿色 0%／黄色内销 8%／红色不适用或高风险。")
header(ws, 3, ["模式ID", "模式名称", "交易结构（卖方→买方｜收货方）", "Huatex开出VAT", "发票开给谁", "报关类型",
               "成立前提（缺一即失效）", "主要风险 / 红线", "结论建议"])
r = 4
for mid, name, struct, vat, inv, customs, prem, risk, concl, flag in SALES:
    vat_txt = "—" if vat is None else f"{vat}%"
    fillmap = {4: {"green": GREEN, "amber": AMBER, "red": RED}[flag],
               9: {"green": GREEN, "amber": AMBER, "red": RED}[flag]}
    body(ws, r, [mid, name, struct, vat_txt, inv, customs, prem, risk, concl], fills=fillmap)
    for col in (1, 4):
        ws.cell(row=r, column=col).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.cell(row=r, column=9).font = Font(name=FONT, size=9.5, bold=True)
    ws.cell(row=r, column=9).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[r].height = 62
    r += 1

r += 1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
c = ws.cell(row=r, column=1, value="一句话记住：Huatex 按出口 0% 处理的前提是「合同买方在境外＋买方书面指定越南交货方＋买方经银行付款」三件同时在；任缺一件，就回到内销 8%。")
c.font = Font(name=FONT, size=9.5, bold=True, color="1F3864")
c.fill = PatternFill("solid", fgColor=GREY)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
ws.row_dimensions[r].height = 26
print_setup(ws, 9, r, repeat_rows="3:3")

# ==================== 3. 采购模式总览 ====================
ws = wb.create_sheet("02-采购模式总览")
widths(ws, {"A": 9, "B": 14, "C": 20, "D": 20, "E": 16, "F": 16, "G": 14, "H": 22, "I": 8, "J": 44, "K": 20})
title_row(ws, 1, 11, "二、采购与入库模式总览（13 种 = 4 类材料 × 采购方式）",
          "读法：先看材料，再看是本地采购还是进口；进口再分「一般贸易完税」与「保税/进料加工」。进口环节的差别不在 VAT（可抵），而在关税＋反倾销是否进成本，以及料件能否核销。")
header(ws, 3, ["模式ID", "材料", "采购方式", "供应商性质", "入库后用途", "进口关税", "进口 VAT", "反倾销", "是否核销",
               "成本说明 / 风险", "结论建议"])
r = 4
for row in PURCHASE:
    mid, mat, way, sup, use, duty, ivat, ad, woff, note, concl, flag = row
    fillmap = {6: {"green": GREEN, "amber": AMBER, "red": RED}[flag],
               11: {"green": GREEN, "amber": AMBER, "red": RED}[flag]}
    body(ws, r, [mid, mat, way, sup, use, duty, ivat, ad, woff, note, concl], fills=fillmap)
    for col in (1, 6, 7, 9):
        ws.cell(row=r, column=col).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.cell(row=r, column=11).font = Font(name=FONT, size=9.5, bold=True)
    ws.cell(row=r, column=11).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[r].height = 54
    r += 1

r += 1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=11)
c = ws.cell(row=r, column=1, value="一句话记住：进口 VAT 可以抵回来，关税和反倾销抵不回来；保税料件不补税就不能内销。所以「出口用保税、内销用本地」是最省的组合。")
c.font = Font(name=FONT, size=9.5, bold=True, color="1F3864")
c.fill = PatternFill("solid", fgColor=GREY)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
ws.row_dimensions[r].height = 26
print_setup(ws, 11, r, repeat_rows="3:3")

# ==================== 4. 税负影响测算 ====================
ws = wb.create_sheet("03-税负测算")
widths(ws, {"A": 30, "B": 18, "C": 18, "D": 18, "E": 18, "F": 40})
title_row(ws, 1, 6, "三、税负影响测算（敏感性分析）",
          "基数：每 USD 1,000,000 货值；公式已内置，改 B4 基数或 C4 汇率即全表联动。假设：进项 VAT 可全额抵扣，未考虑资金成本与汇率波动。")

header(ws, 3, ["假设项", "取值", "单位", "", "", "说明"])
ws.cell(row=4, column=1, value="测算基数（货值）").font = Font(name=FONT, size=9.5)
ws.cell(row=4, column=2, value=1000000).font = Font(name=FONT, size=9.5, bold=True, color="C00000")
ws.cell(row=4, column=3, value="USD").font = Font(name=FONT, size=9.5)
ws.cell(row=4, column=6, value="红色单元格＝可改参数；下方所有金额随其联动").font = Font(name=FONT, size=9, italic=True, color="595959")
ws.cell(row=5, column=1, value="汇率 USD/VND").font = Font(name=FONT, size=9.5)
ws.cell(row=5, column=2, value=26200).font = Font(name=FONT, size=9.5, bold=True, color="C00000")
ws.cell(row=5, column=3, value="VND").font = Font(name=FONT, size=9.5)
for rr in (3, 4, 5):
    for cc in range(1, 7):
        ws.cell(row=rr, column=cc).border = BORDER
    ws.cell(row=rr, column=1).fill = PatternFill("solid", fgColor=GREY)
    ws.cell(row=rr, column=2).fill = PatternFill("solid", fgColor="FFF2CC")
    ws.cell(row=rr, column=2).alignment = Alignment(horizontal="right", vertical="center")

r = 7
section(ws, r, 6, "A. VAT：内销 8% vs 出口 0%（价外税，影响在现金流而非利润）")
r += 1
header(ws, r, ["项目", "内销 8%", "出口 0%", "差异（USD）", "差异（VND）", "说明"])
r += 1
vat_row = r
body(ws, r, ["销项 VAT", f"=$B$4*0.08", 0, f"=B{vat_row}-C{vat_row}", f"=D{vat_row}*$B$5",
             "出口 0% 不产生销项；内销 8% 须开票申报（至 2026-12-31）"])
for col in (2, 3, 4, 5):
    ws.cell(row=r, column=col).number_format = "#,##0"
    ws.cell(row=r, column=col).alignment = Alignment(horizontal="right", vertical="center")
ws.row_dimensions[r].height = 32
r += 1
body(ws, r, ["若进项全额可抵 → 净现金影响", 0, 0, 0, 0,
             "进项可抵时，VAT 为资金时点差，不构成最终成本；影响约等于 8 个点的资金占用"])
for col in (2, 3, 4, 5):
    ws.cell(row=r, column=col).number_format = "#,##0"
    ws.cell(row=r, column=col).alignment = Alignment(horizontal="right", vertical="center")
ws.row_dimensions[r].height = 32
r += 1

r += 1
section(ws, r, 6, "B. 进口关税（刚性成本，不可退）")
r += 1
header(ws, r, ["项目", "税率", "金额（USD）", "金额（VND）", "占货值", "说明"])
r += 1
duty_rows = [("纱线 · 一般贸易进口", 0.03, "2023 口径约 3%，须按 HS 重核"),
             ("布类（胚布/成品布）· 一般贸易进口", 0.12, "2023 口径约 12%，须按 HS 重核；布类是成本最重项")]
duty_first = r
for i, (name, rate, note) in enumerate(duty_rows):
    body(ws, r, [name, rate, f"=$B$4*B{r}", f"=C{r}*$B$5", rate, note])
    ws.cell(row=r, column=2).number_format = "0.0%"
    ws.cell(row=r, column=3).number_format = "#,##0"
    ws.cell(row=r, column=4).number_format = "#,##0"
    ws.cell(row=r, column=5).number_format = "0.0%"
    for col in (2, 3, 4, 5):
        ws.cell(row=r, column=col).alignment = Alignment(horizontal="right", vertical="center")
    ws.row_dimensions[r].height = 30
    r += 1

r += 1
section(ws, r, 6, "C. 反倾销税 · 纱线（按出口商档位，差异极大）")
r += 1
header(ws, r, ["情形", "税率", "金额（USD）", "金额（VND）", "较最低档多付（USD）", "说明"])
r += 1
ad_rows = [("最低档（名单内出口商）", 0.0357, "取到低档需 C/O 与出口商名单均在册"),
           ("中枢（参数表口径）", 0.078, "内部测算默认档"),
           ("最高档（名单外/凭证不全）", 0.1745, "原产地证不全最常见的后果")]
ad_first = r
ad_last = r + len(ad_rows) - 1
for i, (name, rate, note) in enumerate(ad_rows):
    body(ws, r, [name, rate, f"=$B$4*B{r}", f"=C{r}*$B$5",
                 f"=C{r}-$C${ad_first}" if i > 0 else 0, note])
    ws.cell(row=r, column=2).number_format = "0.00%"
    for col in (2, 3, 4, 5):
        ws.cell(row=r, column=col).number_format = "0.00%" if col == 2 else "#,##0"
        ws.cell(row=r, column=col).alignment = Alignment(horizontal="right", vertical="center")
    ws.row_dimensions[r].height = 30
    r += 1

r += 1
section(ws, r, 6, "D. 保税 vs 一般贸易（出口业务，纱线口径）")
r += 1
header(ws, r, ["项目", "一般贸易进口", "保税 SXXK", "差额（USD）", "差额（VND）", "说明"])
r += 1
body(ws, r, ["进口环节关税＋反倾销（现金占用）", f"=C{duty_first}+C{ad_first}", 0,
             f"=B{r}-C{r}", f"=D{r}*$B$5",
             "保税暂不征：料件复出口后关税与反倾销不构成成本；转内销须先补税"])
for col in (2, 3, 4, 5):
    ws.cell(row=r, column=col).number_format = "#,##0"
    ws.cell(row=r, column=col).alignment = Alignment(horizontal="right", vertical="center")
ws.row_dimensions[r].height = 34
r += 1

r += 1
section(ws, r, 6, "E. 结论（本页）")
r += 1
concl = [
    "1. 单看 VAT，内销 8% 与出口 0% 的差别在进项可抵时是现金流时点差（约 8 个点的资金占用），不是 8% 的利润损失；报价时不要把它当成纯成本叠加。",
    "2. 真正的利润差在进口端：同样是 USD 1,000,000 货值，布类一般贸易进口的关税（约 12%）是纱线（约 3%）的 4 倍；纱线反倾销从最低档到最高档相差约 5 倍。",
    "3. 出口业务使用保税 SXXK 料件，是把关税与反倾销「归零」的唯一合规路径；但一旦转内销必须补税，这条线要在系统里管住。",
]
for t in concl:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    c = ws.cell(row=r, column=1, value=t)
    c.font = Font(name=FONT, size=9.5)
    c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True, indent=1)
    ws.row_dimensions[r].height = 32
    r += 1
print_setup(ws, 6, r - 1)

# ==================== 5. 风险与待决 ====================
ws = wb.create_sheet("04-风险与待决事项")
widths(ws, {"A": 5, "B": 30, "C": 40, "D": 44, "E": 16, "F": 34})
title_row(ws, 1, 6, "四、风险红线与待决事项",
          "左表＝已识别的 10 条红线（按后果严重度排序）；右表＝需外部确认或领导决策的事项。红线部分建议直接转化为开票/报关的审批卡点。")
section(ws, 3, 6, "A. 风险红线（10 条）")
header(ws, 4, ["#", "风险点", "触发条件", "后果", "涉及模式", "控制动作（建议）"])
r = 5
for i, (name, trig, cons, modes, ctrl) in enumerate(REDLINES, start=1):
    body(ws, r, [i, name, trig, cons, modes, ctrl], fills={2: RED if i <= 4 else AMBER})
    ws.cell(row=r, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=r, column=2).font = Font(name=FONT, size=9.5, bold=True)
    ws.row_dimensions[r].height = 44
    r += 1

r += 1
section(ws, r, 6, "B. 待确认 / 待决策事项")
r += 1
header(ws, r, ["#", "事项", "问题描述", "影响", "责任方", "时点"])
r += 1
for i, (item, desc, impact, owner, when) in enumerate(PENDING, start=1):
    body(ws, r, [i, item, desc, impact, owner, when], fills={5: GREY, 6: GREY})
    ws.cell(row=r, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=r, column=2).font = Font(name=FONT, size=9.5, bold=True)
    ws.cell(row=r, column=5).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=r, column=6).alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[r].height = 44
    r += 1
print_setup(ws, 6, r - 1)

# ==================== 6. 行动建议 ====================
ws = wb.create_sheet("05-行动建议")
widths(ws, {"A": 14, "B": 62, "C": 32, "D": 20, "E": 10})
title_row(ws, 1, 5, "五、行动建议（分阶段落地）",
          "按「先堵红线 → 再建台账 → 后上系统」的顺序推进；前 1 个月的动作不需要额外预算，只涉及流程与审批卡点。")
header(ws, 3, ["阶段", "动作", "交付物", "责任", "优先级"])
r = 4
for phase, act, deliv, owner, pri in ACTIONS:
    body(ws, r, [phase, act, deliv, owner, pri],
         fills={5: RED if pri == "紧急" else (AMBER if pri == "高" else GREEN)})
    ws.cell(row=r, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=r, column=5).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=r, column=1).font = Font(name=FONT, size=9.5, bold=True)
    ws.row_dimensions[r].height = 86
    r += 1
print_setup(ws, 5, r - 1)

# ==================== 7. 政策依据 ====================
ws = wb.create_sheet("06-政策依据")
widths(ws, {"A": 5, "B": 52, "C": 22, "D": 70})
title_row(ws, 1, 4, "六、政策依据索引",
          "所有模式结论所引条文；落地前建议取关务/税务顾问书面意见，条文以越南官方最新版本为准。")
header(ws, 3, ["#", "政策 / 条文", "覆盖模式", "要点"])
r = 4
for i, (b, modes, note) in enumerate(BASIS, start=1):
    body(ws, r, [i, b, modes, note])
    ws.cell(row=r, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=r, column=3).alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[r].height = 34
    r += 1
print_setup(ws, 4, r - 1)

# ==================== 8. 口径与假设 ====================
ws = wb.create_sheet("4-口径与假设")
widths(ws, {"A": 30, "B": 26, "C": 52, "D": 18})
title_row(ws, 1, 4, "口径与假设（所有口径显性化）",
          "本页为全报告的唯一口径来源；任何数字与结论的假设都在这里，改这里即改全报告的解释基础。⚠️＝尚未确认，不可直接对外使用。")
header(ws, 3, ["口径 / 假设项", "取值", "依据 / 来源", "状态"])
r = 4
for item, val, src, status in PARAMS:
    flag = AMBER if ("待" in status or "假设" in status) else GREEN
    body(ws, r, [item, val, src, status], fills={4: flag})
    ws.cell(row=r, column=2).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.cell(row=r, column=4).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=r, column=1).font = Font(name=FONT, size=9.5, bold=True)
    ws.row_dimensions[r].height = 30
    r += 1
print_setup(ws, 4, r - 1, landscape=False)

wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("saved", OUT)
