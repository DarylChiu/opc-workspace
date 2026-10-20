#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""越南华特经营模式 .xls → 结构化 workbook v1
输入: work/huatex-model/越南华特经营模式23041101.xls
输出: deliverables/越南华特经营模式-整理版-v1-20261020.xlsx
原则: 原始数据零丢失（原 6 个 sheet 原样归档）+ 主表规范化 + 参数单点 + 风险/待核台账
"""
import xlrd, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SRC = "work/huatex-model/越南华特经营模式23041101.xls"
OUT = "deliverables/越南华特经营模式-整理版-v1-20261020.xlsx"

C_HEAD = "1F4E78"; C_HEAD2 = "2E75B6"; C_ALT = "EAF1F8"
C_HIGH = "FFC7CE"; C_MID = "FFEB9C"; C_OK = "C6EFCE"
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

wb_src = xlrd.open_workbook(SRC, formatting_info=True)


def grid(sheet):
    """返回 fill-forward 后的二维值网格（合并单元格取左上角值）"""
    g = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
    for rlo, rhi, clo, chi in sheet.merged_cells:
        v = sheet.cell_value(rlo, clo)
        for r in range(rlo, rhi):
            for c in range(clo, chi):
                if r < sheet.nrows and c < sheet.ncols:
                    g[r][c] = v
    out = []
    for row in g:
        out.append([s(v) for v in row])
    return out


def s(v):
    if isinstance(v, float) and v == int(v):
        v = int(v)
    t = str(v).strip()
    # 短值（主体名/税率等）去掉 excel 手工换行，保证可筛选
    if len(t) < 30:
        t = " ".join(t.split())
    return t


wb = Workbook()
wb.remove(wb.active)


def style_header(ws, ncol, row=1, color=C_HEAD):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(bold=True, color="FFFFFF", size=10)
        cell.fill = PatternFill("solid", fgColor=color)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def style_body(ws, nrow, ncol, start=2, wrap_cols=()):
    for r in range(start, nrow + 1):
        for c in range(1, ncol + 1):
            cell = ws.cell(row=r, column=c)
            cell.border = BORDER
            cell.font = Font(size=10)
            cell.alignment = Alignment(vertical="center",
                                       wrap_text=(c in wrap_cols),
                                       horizontal="left")
    for c in range(1, ncol + 1):
        ws.cell(row=start - 1, column=c).alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True)


def set_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ---------------------------------------------------------------- 00 说明
ws = wb.create_sheet("00-说明")
ws["A1"] = "越南华特 经营模式 · 整理版 v1"
ws["A1"].font = Font(bold=True, size=16, color=C_HEAD)
rows = [
    ("", ""),
    ("源文件", "越南华特经营模式23041101.xls"),
    ("源文件属性", "作者 (SHC-B29) Diep Phi｜创建 2022-05-06｜最后保存 2023-04-13｜6 个 sheet"),
    ("整理日期", "2026-10-20"),
    ("整理原则", "① 原始 6 个 sheet 原样归档（90~95），零丢失 ② 主矩阵拆成「一行一个模式」可筛选 ③ 税率/周期集中到参数表，主表不再散落 ④ 表内已标注的风险单独成台账 ⑤ 2023 口径与 2026 现行政策的差异单列待核清单"),
    ("", ""),
    ("表结构", ""),
    ("01-模式主表", "源 VN sheet → 5 组主体组合 × 7 行 = 35 个模式单元，一行一个；组合类型/主体角色已取消合并单元格、逐行填实"),
    ("02-采购经营销售", "源 采购经营销售模式 sheet → 采购模式 × 经营销售模式，合并单元格已填实"),
    ("03-采购生产销售", "源 采购生产销售模式 sheet → 25 行材料来源 × 销售模式笛卡尔积"),
    ("04-税率与政策参数", "全表出现的税率/周期/税费项目集中，附「2026 是否需要重核」标记"),
    ("05-风险台账", "源表备注中已明确标注的稽查风险/合规风险，含原文依据"),
    ("06-待核清单", "2023 口径 → 2026 现行政策待核项 + 表内待确认项"),
    ("07-数据缺口", "逐列空值统计 + 关键税负字段全空的可疑行"),
    ("90~95-原始", "源文件 6 个 sheet 原样归档，只读参考，勿改"),
    ("", ""),
    ("图例", "「-」= 原表填「-」，表示不适用/无；空白 = 原表未填，需补；「待核」= 需按 2026 现行政策确认"),
    ("风险分级规则", "备注原文含「稽查风险」→ 高；含「待确认」→ 中；其余留空（原表未标注风险，不代表无风险）"),
    ("", ""),
    ("原表备注（原文保留）", ""),
    ("备注 1", "越南实行增值税税率为10%，之前疫情期间优惠政策为8%，23年预计会调整回10%"),
    ("备注 2", "越南华特公司目前是非EPE企业，是生产销售一体化公司，出口业务执行免抵退政策，与目前国内的产销分离有所不同。与越南企业交易只能适用越南盾结算，后续有出口执行免抵退。"),
    ("总结", "越南华特因是产销一体的非EPE企业，所以从越南国内任何企业采购纱线，均要先承担增值税后，再根据出口则退税、内销则抵税的规则来处理。"),
    ("", ""),
    ("⚠️ 遗留", "源文件含 sheet「生管異常工時明細」（38 行，生产异常工时），与经营模式主题无关，疑为跨文件残留 → 已原样归档在 95，建议确认后剔除"),
    ("模型", "deepseek/deepseek-v4-flash（整理脚本化，未做政策解读改写）"),
]
r = 2
for a, b in rows:
    ws.cell(row=r, column=1, value=a).font = Font(bold=True, size=10)
    ws.cell(row=r, column=2, value=b).font = Font(size=10)
    ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")
    if a in ("表结构", "原表备注（原文保留）"):
        ws.cell(row=r, column=1).font = Font(bold=True, size=12, color=C_HEAD)
    r += 1
ws.column_dimensions["A"].width = 22
ws.column_dimensions["B"].width = 118

# ---------------------------------------------------------------- 01 模式主表
sh = wb_src.sheet_by_name("VN")
g = grid(sh)
COLS = [
    ("模式ID", 0), ("协议方（组合类型）", 1), ("下单主体", 2), ("接单主体", 3),
    ("生产主体", 4), ("对外销售主体", 5), ("付款主体", 6), ("收货主体", 7),
    ("采购项目", 8), ("供应方主体性质", 9), ("贸易方式", 10), ("采购发票币别", 11),
    ("材料采购·反倾销税率", 12), ("材料采购·关税率", 13), ("材料采购·增值税率", 14),
    ("成品出货·发票币种", 15), ("成品出货·是否报关", 16), ("成品出货·增值税率", 17),
    ("内销补料·关税率", 18), ("内销补料·增值税率", 19),
    ("退抵税·关税退税率", 20), ("退抵税·增值税退税率", 21),
    ("退抵税·关税退税周期", 22), ("退抵税·增值税退税周期", 23),
    ("其他·外商承包税率", 24), ("其他税费", 25),
    ("产地归属", 26), ("越南产地资料要求", 27), ("越南产地证条件", 28),
    ("风险等级", None), ("风险说明（原文）", 29), ("备注（原文）", None),
]
# 源列索引: 0=A ... 29=AD ; 备注在 AD = idx 29 → 已用于 风险说明
# 重新对应：idx28=AC 产地证条件, idx29=AD 备注
COLS = [
    ("模式ID", None), ("协议方（组合类型）", 1), ("下单主体", 2), ("接单主体", 3),
    ("生产主体", 4), ("对外销售主体", 5), ("付款主体", 6), ("收货主体", 7),
    ("采购项目", 8), ("供应方主体性质", 9), ("贸易方式", 10), ("采购发票币别", 11),
    ("材料采购·反倾销税率", 12), ("材料采购·关税率", 13), ("材料采购·增值税率", 14),
    ("成品出货·发票币种", 15), ("成品出货·是否报关", 16), ("成品出货·增值税率", 17),
    ("内销补料·关税率", 18), ("内销补料·增值税率", 19),
    ("退抵税·关税退税率", 20), ("退抵税·增值税退税率", 21),
    ("退抵税·关税退税周期", 22), ("退抵税·增值税退税周期", 23),
    ("其他·外商承包税率", 24), ("其他税费", 25),
    ("产地归属", 26), ("越南产地资料要求", 27), ("越南产地证条件", 28),
    ("风险等级", None), ("备注（原文）", 29),
]

ws = wb.create_sheet("01-模式主表")
hdr = [c[0] for c in COLS]
ws.append(hdr)

DATA_RANGES = [(4, 11), (11, 18), (18, 25), (25, 32), (32, 39)]  # 0-based [lo,hi)
blocks = []
for bi, (lo, hi) in enumerate(DATA_RANGES, start=1):
    for r in range(lo, hi):
        blocks.append((bi, r))

data_rows = []
for bi, r in blocks:
    row = ["" for _ in COLS]
    row[0] = f"M{bi}-{(r - DATA_RANGES[bi-1][0]) + 1:02d}"
    for ci, (name, src_i) in enumerate(COLS):
        if src_i is None:
            continue
        row[ci] = g[r][src_i]
    note = g[r][29]
    if "稽查风险" in note:
        lvl = "高"
    elif "待确认" in note or "风险" in note:
        lvl = "中"
    else:
        lvl = ""
    row[[c[0] for c in COLS].index("风险等级")] = lvl
    # 组合类型 = B + "·" + C
    row[1] = g[r][1] + "·" + g[r][2]
    data_rows.append(row)
    ws.append(row)

nrow = len(data_rows) + 1
style_header(ws, len(hdr))
style_body(ws, nrow, len(hdr), wrap_cols=(2, 9, 28, 29, 31))
ws.freeze_panes = "C2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(hdr))}{nrow}"
set_widths(ws, [9, 20, 14, 12, 10, 12, 12, 12, 10, 20, 14, 20,
                16, 14, 12, 14, 12, 12, 14, 10, 12, 12, 16, 10, 10,
                30, 10, 40, 40, 9, 60])
for r in range(2, nrow + 1):
    lvl = ws.cell(row=r, column=30).value
    fill = {"高": C_HIGH, "中": C_MID}.get(lvl)
    if fill:
        ws.cell(row=r, column=30).fill = PatternFill("solid", fgColor=fill)
    ws.cell(row=r, column=30).alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[r].height = 30
    for c in (13, 14, 15, 18, 19, 20, 21, 22, 25):
        cell = ws.cell(row=r, column=c)
        if isinstance(cell.value, (int, float)):
            cell.number_format = "0.00%"
        cell.alignment = Alignment(horizontal="center", vertical="center")

# ---------------------------------------------------------------- 02 / 03 规范化
def normalize_sheet(sheet_name, out_name, header_rows, data_from, width_hint=None):
    sh = wb_src.sheet_by_name(sheet_name)
    gg = grid(sh)
    names, seen = [], {}
    for c in range(sh.ncols):
        parts = []
        for hr in header_rows:
            v = gg[hr - 1][c]
            if v and (not parts or parts[-1] != v):
                parts.append(v)
        nm = "·".join(parts) if parts else ("行号" if c == 0 else f"列{get_column_letter(c+1)}")
        nm = nm.replace(" ", "")
        if nm in seen:
            seen[nm] += 1
            nm = f"{nm}#{seen[nm]}"
        else:
            seen[nm] = 1
        names.append(nm)
    w = wb.create_sheet(out_name)
    w.append(names)
    n = 0
    for r in range(data_from - 1, sh.nrows):
        vals = gg[r]
        if not any(vals):
            continue
        # 表尾说明行（仅首两列有内容且以「说明/备注/总结」开头）→ 不进数据区
        first = next((v for v in vals if v), "")
        nonempty = [i for i, v in enumerate(vals) if v]
        if nonempty and max(nonempty) <= 2 and any(first.startswith(k) for k in ("说明", "备注", "总结", "1、", "2、", "3、", "4、", "5、")):
            continue
        w.append(vals)
        n += 1
    style_header(w, len(names))
    style_body(w, n + 1, len(names), wrap_cols=tuple(range(1, len(names) + 1)))
    w.freeze_panes = "B2"
    w.auto_filter.ref = f"A1:{get_column_letter(len(names))}{n+1}"
    set_widths(w, width_hint or [16] * len(names))
    return n


normalize_sheet("采购经营销售模式", "02-采购经营销售", [3, 4], 5,
                [10, 22, 24, 14, 12, 10, 12, 12, 10, 14, 10, 10, 10, 26, 20])
normalize_sheet("采购生产销售模式", "03-采购生产销售", [3, 4, 5], 6,
                [6, 18, 10, 10, 12, 26, 12, 10, 14, 12, 10, 10, 10, 10, 10, 14, 10, 10, 10, 10, 10, 10])

# ---------------------------------------------------------------- 04 参数
ws = wb.create_sheet("04-税率与政策参数")
ws.append(["参数ID", "参数项", "原表口径（2023）", "主表出现位置", "2026 是否需重核", "现行口径（待填/待核）", "依据 / 备注"])
params = [
    ("P01", "增值税率（越南，标准）", "10%（疫情期间优惠 8%，表内注「23年1月恢复10%」）", "M/N/O/R/T/S/V 列", "是", "", "原表备注 1"),
    ("P02", "增值税率（期间优惠）", "8%", "采购经营销售模式 sheet", "是", "", "优惠是否延续需核"),
    ("P03", "进口关税·成品布", "12%", "01 主表 材料采购·关税率", "是", "", "按 HS 编码确定"),
    ("P04", "进口关税·纱线（自 EPE 采购）", "3%", "01 主表 材料采购·关税率", "是", "", "非 EPE 企业自 EPE 采购视同进口"),
    ("P05", "进口关税·胚布（保税进口/进料加工）", "免税", "01 主表 材料采购·关税率", "是", "", "保税进口"),
    ("P06", "反倾销税率·纱线（中国来源）", "17.45%", "01 主表 材料采购·反倾销税率", "是", "17.45%", "按现行反倾销决定与出口商/HS 核定"),
    ("P07", "外商承包税率", "1%", "01 主表 其他·外商承包税率", "是", "", "四方协议下加工关系免、销售关系由 T1 母公司缴"),
    ("P08", "关税退税周期", "一年一次（自 EPE 采购 3% 部分）", "01 主表 退抵税·关税退税周期", "是", "", "原表另注「目前未确认是否需要余料核销」"),
    ("P09", "增值税退税周期", "60–90 天（退税产生日 → 到账日）", "01 主表 退抵税·增值税退税周期", "否（操作口径）", "", "正常按月申请，未达最低申请额则累积，现实际 2 个月申请一次"),
    ("P10", "出口增值税率", "0%（出口适用 0%）", "01 主表 成品出货·增值税率", "是", "", "需按现行 VAT 法确认"),
    ("P11", "内销补料增值税率", "8%–10%", "01 主表 内销补料·增值税率", "是", "", "随 P01/P02 变动"),
    ("P12", "企业所得税率", "20%（初稿V2 未列，表内 FOC 行有 0.2）", "初稿V2（归档）", "是", "", "按现行 CIT 法"),
    ("P13", "EPE 企业性质认定", "EPE=出口加工企业；华特=非 EPE", "全表", "是", "", "影响「视同进口」「免抵退」全部判断"),
    ("P14", "出口退税机制", "非 EPE 产销一体 → 出口免抵退；国内采购先担 VAT 后退/抵", "全表", "是", "", "法条体系 2026 已换：Luật 67/2025 + NĐ 181/2025 + TT 20/2026（待正式核验）"),
    ("P15", "产地证条件（越南原产）", "最后加工阶段制成 + HS 转换 + 境内新增价值比率 ≥30%", "01 主表 越南产地证条件", "是", "", "须按现行原产地规则与 LVC 计算口径核验"),
]
for p in params:
    ws.append(list(p))
style_header(ws, 7)
style_body(ws, len(params) + 1, 7, wrap_cols=(2, 3, 4, 6, 7))
ws.freeze_panes = "A2"
set_widths(ws, [8, 30, 42, 30, 14, 24, 46])
for r in range(2, len(params) + 2):
    ws.row_dimensions[r].height = 32

# ---------------------------------------------------------------- 05 风险台账
ws = wb.create_sheet("05-风险台账")
ws.append(["风险ID", "涉及模式ID", "风险类型", "风险描述（原表原文）", "触发条件", "财务/税务影响", "建议动作", "状态"])
risks = [
    ("R-01", "M4-01、M4-02（双方·T1工厂(非EPE)）", "反倾销 + 税务稽查",
     "双方协议（华特-T1工厂），原料纱线来源于中国，会产生 17.45%。此模式若长期存在，会有税务稽查风险，即同类产品越南国内有材料，但一直进口反倾销材料。而且采购的反倾销材料用于越南国内销售",
     "① 非 EPE 主体 ② 中国来源纱线 ③ 不报关 + 内销开 VND 发票",
     "反倾销税 17.45% + 关税 3% + 内销 VAT 10%；长期「进口反倾销材料用于内销」易被认定规避反倾销措施，涉追缴+罚款",
     "① 改用可在越南国内采购的纱线 ② 若必须进口，走正规报关并单独核算内销部分 ③ 留存「境内无同类材料」的举证（供应商询价记录、同类产品比对）", "开放"),
    ("R-02", "M4-04（双方·T1工厂(非EPE)·胚布）", "投资执照 / 工业区合规",
     "双方协议（华特-T1工厂），进口胚布业务加工成品再销售，属于染色加工业务，目前违反工业区规定（投资执照调整），存在稽查风险，如果越南境内销售存在连带稽查风险。",
     "保税进口胚布 → 染色加工 → 境内销售",
     "投资执照经营范围与园区环保规定不符；境内销售环节可能被连带追溯",
     "① 确认投资执照/环保许可是否含染色加工 ② 内销部分单独评估 ③ 必要时调整经营范围或改为委外加工（须同步处理保税料件核销）", "开放"),
    ("R-03", "M2-04~M2-07、M3-04~M3-07", "贸易可行性未确认",
     "一般贸易 / 供应商需出口复进口，待确认是否可行",
     "自越南境内 EPE 企业采购纱线",
     "若不可行，该路径下的 3% 关税 + 10% VAT 成本模型失效",
     "向海关/供应商确认 EPE 出口复进口路径的合法性与单证要求", "待确认"),
    ("R-04", "全表（华特为非 EPE）", "资金占用 / 现金流",
     "华特公司目前登记为非 EPE 企业，与越南企业交易只能适用越南盾结算，后续有出口执行免抵退",
     "从越南境内任何企业采购纱线",
     "先全额承担 10% VAT，退税 60–90 天（实际 2 个月申请一次）→ 持续占用营运资金",
     "按月度采购额测算 VAT 资金占用规模，纳入资金预算；跟踪退税申请额下限避免累积", "开放"),
    ("R-05", "M2-01、M1-01 等保税/进料加工行", "保税料件核销",
     "越南境内 EPR 企业进口纱线，先缴后退税（1年1申报），目前未确认是否需要余料核销",
     "进料加工 / 保税进口料件",
     "余料未核销可能被追补关税与 VAT",
     "确认保税料件余料核销义务与周期，建立料件台账", "待确认"),
]
for x in risks:
    ws.append(list(x))
style_header(ws, 8)
style_body(ws, len(risks) + 1, 8, wrap_cols=(2, 3, 4, 5, 6, 7))
ws.freeze_panes = "A2"
set_widths(ws, [8, 26, 20, 60, 30, 42, 50, 10])
for r in range(2, len(risks) + 2):
    ws.row_dimensions[r].height = 90

# ---------------------------------------------------------------- 06 待核清单
ws = wb.create_sheet("06-待核清单")
ws.append(["编号", "待核事项", "原表口径（2023-04）", "2026 需确认的点", "影响范围", "优先级", "状态", "结论/来源"])
todo = [
    ("T-01", "增值税标准税率", "10%（疫情优惠 8% 已到期）", "2026 年 10% 是否仍为标率、是否有阶段性 8% 延续政策、适用范围与期限", "01 主表 N/O/R/S/T/V 列 + 02/03 表", "P1", "待核", ""),
    ("T-02", "出口退税法条体系", "未写法条号（仅「免抵退」表述）", "2026 适用 Luật 67/2025/QH15 + NĐ 181/2025 + TT 20/2026；旧 TT 78/2014 + 96/2015 条号不可照搬；非 EPE 产销一体企业的退税条件与收汇要求", "全表退税逻辑", "P1", "待核", ""),
    ("T-03", "反倾销税率 17.45%", "纱线（中国来源）17.45%", "现行反倾销决定是否变动、按出口商/HS 是否分档、有效期", "M4-01/M4-02 + R-01", "P1", "待核", ""),
    ("T-04", "进口关税 12% / 3% / 0%", "成品布 12%、自 EPE 采购纱线 3%、胚布保税免税", "按现行 HS 编码与 MFN/ACFTA 优惠税率重核；产地证能否减按 7%/5%/0%", "01 主表 关税率列", "P2", "待核", ""),
    ("T-05", "EPE 认定与视同进口规则", "EPE=出口加工企业；非 EPE 自 EPE 采购视同进口", "现行 EPE 管理办法、区内区外交易规则是否有变", "全表交易结构", "P1", "待核", ""),
    ("T-06", "外商承包税判定规则", "四方协议：加工关系→双方免；销售关系→T1 母公司缴（1%）", "现行 NĐ/Thông tư 下判定标准是否变化；1% 是否仍适用", "M1/M2/M5 组合", "P2", "待核", ""),
    ("T-07", "原产地规则 30% 增值", "最后加工 + HS 转换 + LVC ≥30%", "现行原产地规则（LVC 计算口径、累计规则）是否调整", "产地证条件列", "P2", "待核", ""),
    ("T-08", "自 EPE 采购「出口复进口」可行性", "标注「待确认是否可行」", "海关是否认可该路径、单证要求", "M2/M3 的 EPE 行", "P2", "待确认", ""),
    ("T-09", "保税料件余料核销义务", "标注「目前未确认是否需要余料核销」", "是否需余料核销、周期、罚则", "保税进口/进料加工行", "P2", "待确认", ""),
    ("T-10", "增值税退税周期现状", "60–90 天，实际 2 个月申请一次", "现行退税办理时效与最低申请额", "现金流测算", "P3", "待确认", ""),
    ("T-11", "业务量基数缺失", "全表只有税率，无金额/数量基数", "补充基准量（如月度出口额、纱线采购额）→ 才能做税负量化对比", "税负测算", "P1", "需 Daryl 提供", ""),
    ("T-12", "生管異常工時明細 sheet", "与经营模式无关", "是否为本文件内容、是否剔除", "文件结构", "P3", "待确认", ""),
]
for x in todo:
    ws.append(list(x))
style_header(ws, 8)
style_body(ws, len(todo) + 1, 8, wrap_cols=(2, 3, 4, 5, 8))
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:H{len(todo)+1}"
set_widths(ws, [8, 30, 34, 56, 26, 8, 12, 30])
for r in range(2, len(todo) + 2):
    ws.row_dimensions[r].height = 54

# ---------------------------------------------------------------- 07 数据缺口
ws = wb.create_sheet("07-数据缺口")
ws.append(["检查项", "说明", "数量", "明细"])
total = len(data_rows)
na, blank = {}, {}
for row in data_rows:
    for ci, (name, _) in enumerate(COLS):
        if row[ci] == "-":
            na[name] = na.get(name, 0) + 1
        elif row[ci] == "":
            blank[name] = blank.get(name, 0) + 1

ws.append(["总模式行", "01-模式主表 数据行数", total, ""])

key_idx = [12, 13, 14, 18, 19, 20, 21]
sus = [f"{r[0]}（{r[1]}·{r[8]}·{r[10]}）" for r in data_rows
       if all(r[i] in ("", "-") for i in key_idx)]
ws.append(["⚠️ 关键税负字段全空", "反倾销/关税/VAT/退税率 7 个字段全为「-」或空 → 该模式税负未定义",
           len(sus), "；".join(sus) if sus else "无"])

s2 = [r[0] for r in data_rows
      if (r[20] not in ("", "-") or r[21] not in ("", "-"))
      and r[22] in ("", "-") and r[23] in ("", "-")]
ws.append(["⚠️ 有退税率无周期", "已填退税率但未填退税周期", len(s2), "；".join(s2) if s2 else "无"])

whole = [n for n, c in blank.items() if c == total]
ws.append(["⚠️ 整列为空", "该列 35 行全部未填 → 输出了表头但无内容", len(whole), "；".join(whole) if whole else "无"])

for name, cnt in blank.items():
    ws.append([f"⚠️ 未填·{name}", "原表空白，需补", f"{cnt}/{total}", ""])
for name, cnt in na.items():
    ws.append([f"不适用·{name}", "原表填「-」= 该环节无此税种/不适用", f"{cnt}/{total}", ""])

style_header(ws, 4)
style_body(ws, ws.max_row, 4, wrap_cols=(2, 4))
ws.freeze_panes = "A2"
set_widths(ws, [30, 46, 12, 90])

# ---------------------------------------------------------------- 90~95 归档
ARCH = ["VN", "采购经营销售模式", "采购生产销售模式", "初稿V2", "初稿V1", "生管異常工時明細"]
for i, name in enumerate(ARCH, start=90):
    sh = wb_src.sheet_by_name(name)
    w = wb.create_sheet(f"{i}-原始-{name}"[:31])
    gg = grid(sh)
    for row in gg:
        w.append(row)
    set_widths(w, [14] * sh.ncols)
    w.freeze_panes = "A1"

os.makedirs("deliverables", exist_ok=True)
wb.save(OUT)
print("saved:", OUT)
print("模式行数:", len(data_rows))
print("sheets:", [x.title for x in wb.worksheets])
