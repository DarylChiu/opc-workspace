#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""越南华特经营模式 v4：Sheet1 销售出货模式 / Sheet2 采购入库模式
口径来源：2026-10-21 FCT/Incoterms 备忘（问1–问6 定稿）+ v3.1 税负模型
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

OUT = "/Users/zhaoyuzhao/.openclaw/workspace-balance/deliverables/越南华特经营模式-销售出货与采购入库模式-v1-20261022.xlsx"

# ---------- 样式 ----------
HDR_FILL = PatternFill("solid", fgColor="1F3864")
HDR_FONT = Font(name="Microsoft YaHei", size=10, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Microsoft YaHei", size=14, bold=True, color="1F3864")
NOTE_FONT = Font(name="Microsoft YaHei", size=9, color="404040")
BODY_FONT = Font(name="Microsoft YaHei", size=9)
BOLD = Font(name="Microsoft YaHei", size=9, bold=True)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
FILL_EXPORT = PatternFill("solid", fgColor="E2EFDA")   # 0% 出口
FILL_DOM = PatternFill("solid", fgColor="FFF2CC")      # 内销 8%
FILL_RISK = PatternFill("solid", fgColor="FCE4E4")     # 高风险
FILL_NA = PatternFill("solid", fgColor="EDEDED")       # 不适用
FILL_HEAD2 = PatternFill("solid", fgColor="D9E1F2")
FILL_BOND = PatternFill("solid", fgColor="DEEBF7")     # 保税/进料加工
FILL_IMPORT = PatternFill("solid", fgColor="FFF2CC")   # 一般贸易进口
FILL_EPE = PatternFill("solid", fgColor="E4DFEC")      # 自 EPE 视同进口

# ---------- Sheet1 ----------
S1_HDR = ["模式ID", "模式名称", "交易结构（卖方→买方｜收货方）", "出货性质",
          "购买方身份", "收货方身份", "货物流向", "Huatex 开票对象",
          "销项发票与 VAT 率", "报关类型", "收付款路径", "Huatex 侧税负",
          "买方／收货方侧税负", "必备单证包", "成立前提（缺一即失效）",
          "红线 / 风险", "结论与评价", "政策依据", "状态"]

S1_ROWS = [
    ["S1-01", "离境出口（一般贸易 FOB／CIF／CIP）",
     "Huatex（卖方/生产）→ 境外客户（买方）｜收货方＝境外，货物实际离境",
     "出口（离境）", "境外企业", "境外（境外买方或其指定境外方）",
     "Huatex 工厂 → 出口口岸 → 境外（货物出境）", "境外买方",
     "越南电子发票，VAT 0%（税率栏填 0%）",
     "出口报关（一般贸易 loại hình，按实际申报）", "境外买方 T/T 付 Huatex（USD）",
     "VAT 0%；CIT 20% 或适用优惠；出口税 0；FCT 不涉及（Huatex 为越南居民）",
     "—（进口国关税/税由买方在境外承担）",
     "合同/PO＋商业发票 CI＋装箱单 PL＋出口报关单＋收汇水单＋提单 B/L",
     "① 货物实际离境 ② 合同＋非现金收汇＋报关单三件齐（NĐ 181/2025 Đ18）",
     "🟡 无真实收汇或第三方代付 → 0% 与退税被拒",
     "最标准路径，凭证最简单，FCT 与就地进出口问题全部不涉及",
     "NĐ 181/2025 Đ18、Đ29；Luật 48/2024/QH15", "已定稿"],

    ["S1-02", "四方合同 · 收货方＝越南 EPE（就地出口 E62）",
     "A HFGI（境外·销售方）｜B Huatex（供货/生产）｜C 境外买方（Sintex 等）｜D 越南 EPE（收货方）；货物全程不经过买方，Huatex 直发 D",
     "出口（就地出口）", "境外企业（在越无常设机构）", "越南 EPE（非关税区，自收货）",
     "Huatex 工厂 → EPE 厂区（境内直发，不经越南境内市场）", "合同买方（境外 Sintex／HFGI）——不开给 D",
     "越南电子发票 VAT 0%；备注栏注明实际交货地＋收货人",
     "Huatex 报 E62 就地出口；EPE 侧办就地进口",
     "境外买方经银行付 Huatex（USD 或 VND 均可）",
     "VAT 0%；CIT 20%/优惠；出口税 0；FCT 不涉及",
     "EPE 生产用物资通常免进口关税与 VAT；改变用途/转内销 → A42 补缴",
     "四方合同（含“买方书面指定交货给越南第三方”条款）＋0% 电子发票＋CI/PL＋E62 报关单＋EPE 就地进口单＋境外买方付款水单",
     "① 买方为境外商人且无常设机构 ② 合同书面指定交货第三方 ③ 买方经银行付款 ④ E62 报关完成 ⑤ SXXK 料件核销",
     "🔴 E62 不进核销 → 补进口税，金额可能大于 FCT；🔴 发票开给越南收货方＝直接被打成内销；🔴 DAP 下 TT 103/2014 Đ1.2③ 有援引空间（建议取税局书面答复）",
     "目前最干净的非离境出口结构。0% 与收货方是否 EPE 无关，只看买方三条件",
     "TT 38/2015 Đ86.1.c；QĐ 1357/QĐ-TCHQ（E62）；TT 103/2014 Đ1.2",
     "已定稿（FCT 建议取书面答复）"],

    ["S1-03", "四方合同 · 收货方＝越南本地企业（买断）",
     "境外买方签约｜Huatex 生产｜越南本地企业（非 EPE）买断收货，货权转移给收货方",
     "出口（就地出口）", "境外企业", "越南本地企业（非 EPE，买断）",
     "Huatex 工厂 → 收货方厂区（境内）", "合同买方（境外）——不开给收货方",
     "越南电子发票 VAT 0%",
     "Huatex 报 E62；收货方办就地进口（一般贸易类）",
     "境外买方付款（不能由越南收货方付）",
     "VAT 0%；CIT 20%/优惠；出口税 0；FCT 不涉及",
     "收货方缴进口关税（按 HS）＋进口 VAT 8%/10%，凭缴税凭证可抵扣（Luật GTGT 2024 Đ14.2）",
     "同 S1-02 ＋收货方就地进口报关单＋缴税凭证＋收货方与境外买方的买卖合同/PO",
     "同 S1-02 四要件；且收货方须真实买断",
     "🔴🔴 五条打成内销：① 发票开给越南收货方 ② 货款由收货方支付 ③ 合同无指定交货条款 ④ 买方仅为通道无实质功能 ⑤ 收货方与买方无实质交易关系",
     "0% 可以成立，但稽查风险明显高于 EPE 场景（凭证要求更严）",
     "TT 38/2015 Đ86.1.c；Luật GTGT 2024 Đ14.2", "已定稿"],

    ["S1-04", "四方合同 · 收货方＝越南本地企业（代工/受托加工）",
     "境外买方签约｜Huatex 生产｜越南代工厂收货加工，货权仍属境外买方（非买断）",
     "出口（就地出口）", "境外企业", "越南本地企业（代工，非买断）",
     "Huatex 工厂 → 代工厂（加工后由境外买方处置复出口）", "合同买方（境外）",
     "越南电子发票 VAT 0%",
     "Huatex 报 E62；代工厂按“加工（nhập gia công）”类型办就地进口",
     "境外买方付款",
     "VAT 0%；CIT 20%/优惠；出口税 0；FCT 不涉及",
     "代工厂免进口关税、免进口 VAT（加工后复出口）；须在出口通关后 15 天内向海关通报对应出口报关单（Mẫu 22 Phụ lục VII）",
     "同 S1-03 ＋加工合同＋加工类型就地进口单＋Mẫu 22 通报",
     "① 代工性质可证（货权不转移） ② 加工后复出口 ③ 15 天内通报",
     "🟡 被认定为买断则代工厂须补进口税；🟡 加工后未复出口＝免税条件失效",
     "代工情形下收货方几乎无进口税负，“收货方拿不到发票”这个问题自动消失",
     "NĐ 134/2016／NĐ 18/2021；TT 38/2015", "已定稿"],

    ["S1-05", "卖方直供 · 购买方＝越南 EPE（EPE 自收货）",
     "Huatex（卖方/生产）→ 越南 EPE（买方且收货方）",
     "出口（就地出口，进非关税区）", "越南 EPE", "越南 EPE 自己",
     "Huatex 工厂 → EPE 非关税区厂区", "越南 EPE（买方）",
     "越南电子发票 VAT 0%（就地出口）",
     "Huatex 报 E62；EPE 办就地进口",
     "EPE 付款给 Huatex（VND 或 USD）",
     "VAT 0%；CIT 20%/优惠；出口税 0；FCT 不涉及",
     "EPE 享非关税区免税待遇；其后续委外加工（送出厂区再运回）由 EPE 自办手续",
     "合同（注明交货至非关税区）＋E62 报关单＋EPE 就地进口单＋收款凭证＋EPE 企业性质证明",
     "① 货物真实进入非关税区 ② 就地进出口报关齐备",
     "🔴 “买方是 EPE”≠视同出口；货未进非关税区则 0% 不成立 → 按内销 8%/10%",
     "成立且常见。Huatex 举证边界＝货交 EPE＋E62 完成＋已收汇；越界解释 EPE 之后如何处置反而扩大风险",
     "TT 38/2015；NĐ 134/2016", "已定稿"],

    ["S1-06", "购买方＝越南 EPE，收货方＝越南本地企业",
     "越南 EPE（买方）｜越南本地企业（收货）——货从不进 EPE 非关税区",
     "❌ 不成立", "越南 EPE", "越南本地企业（非关税区外）",
     "Huatex 工厂 → 本地企业厂区（不进非关税区）", "越南 EPE（但收不到货）",
     "—（该结构下不存在合规开票方式）",
     "—（货不进非关税区，EPE 无法办就地进口）",
     "—",
     "若强行按内销处理：VAT 8%/10%",
     "—",
     "—",
     "—（自相矛盾，无合规路径）",
     "🔴🔴🔴 C 收票不收货＝票货分离/过票；D 直接收货无报关＝无证进口（行政甚至刑事风险），比补税严重",
     "❌ 不适用（商业上不成立）：EPE 享受非关税区待遇的前提就是货物进入其厂区，故 EPE 作为买方必然自己收货。矩阵中标“不适用＋原因”，不留空",
     "推论依据：0% 须货进非关税区", "不适用"],

    ["S1-07", "内销 · 买方与收货方均为越南本地企业",
     "Huatex（卖方）→ 越南本地企业（买方＝收货方，非 EPE）",
     "内销", "越南本地企业（非 EPE）", "越南本地企业（非 EPE）",
     "Huatex 工厂 → 客户工厂（境内交付）", "越南本地企业（买方）",
     "越南电子发票 VAT 8%（至 2026-12-31；之后若无延续政策回到 10%）",
     "无需报关（境内销售）",
     "客户付 VND（境内交易原则上只能 VND）",
     "销项 VAT 8%；进项可全额抵扣；CIT 20%/优惠；无退税；FCT 不涉及",
     "客户取得 8% 进项可抵扣",
     "合同/PO＋越南 VAT 发票＋送货单＋收款凭证",
     "① 买卖双方均为越南居民 ② 货物在境内交付",
     "🔴 用保税/免税进口料件做内销而未先补税 → 未补税内销，稽查重点；🔴 外币结算境内交易不合规（TT 32/2013 Đ3-Đ4）",
     "最常规路径。税负高低几乎完全取决于采购模式（见 Sheet2），VAT 进项能抵则中性",
     "NQ 204/2025/QH15＋NĐ 174/2025；TT 32/2013 Đ3-Đ4", "已定稿"],

    ["S1-08", "买方＝本地企业、收货＝EPE ·【结构A】Huatex 内销 + C 出口",
     "Huatex（卖方）→ C 越南本地企业（买方）→（C 报就地出口）→ D 越南 EPE（收货）",
     "内销（Huatex 环节）", "越南本地企业（非 EPE）", "越南 EPE（由 C 交货）",
     "Huatex 工厂 → C → EPE 厂区", "C（越南本地企业）",
     "越南电子发票 VAT 8%/10%",
     "C 报就地出口（出口方写 C）；Huatex 不报关",
     "C 付 Huatex（VND）；C 向 D 收款",
     "Huatex 缴 8%/10% 销项（进项可抵）；无退税；CIT 20%/优惠",
     "C 出口享 0%；D 按 EPE 规则免进口税",
     "Huatex↔C 买卖合同＋VAT 发票＋送货单；C 侧出口报关单（供链条解释）",
     "C 具备出口资质与实际出口行为",
     "🟡 Huatex 放弃 0%，多承担 8% 的现金流（进项可抵则净影响有限）",
     "【推荐】一条货只有一次出口报关＋一次进口报关 → 报关链必须在 C 这一层，商业链与报关链才对齐；最干净",
     "TT 38/2015；NĐ 181/2025 Đ18", "已定稿"],

    ["S1-09", "买方＝本地企业、收货＝EPE ·【结构B】Huatex 直接就地出口",
     "Huatex（卖方）→（E62 就地出口，买方为境外实体并指定交货 D）→ 越南 EPE（收货）；C 退出链条",
     "出口（就地出口）", "境外实体（须重新安排合同主体）", "越南 EPE（收货）",
     "Huatex 工厂 → EPE 厂区", "境外买方",
     "越南电子发票 VAT 0%",
     "Huatex 报 E62；EPE 办就地进口",
     "境外买方付款给 Huatex",
     "VAT 0%；CIT 20%/优惠；出口税 0；FCT 不涉及",
     "EPE 按非关税区规则通常免税",
     "四方/三方合同（含指定交货条款）＋E62 报关单＋EPE 就地进口单＋境外买方付款水单",
     "① C 必须从商业链退出或能解释为境外买方的下家 ② 买方为境外实体且付款",
     "🔴🔴 若保留四层全开票（Huatex→C→D 同时又有境外买方开票）＝报关链对不上商业链，必有一层过票",
     "Huatex 可拿 0%，但前提是合同主体与收款路径重构；不能“发票照开给 C、报关却写 Huatex”",
     "TT 38/2015 Đ86.1.c；QĐ 1357/QĐ-TCHQ", "待关务确认（报关单出口方写谁）"],
]

# ---------- Sheet2 ----------
S2_HDR = ["模式ID", "采购材料", "采购方式", "供应商性质", "入库后用途",
          "进口关税率", "进口 VAT", "反倾销税", "是否需要核销",
          "开票与币别", "入库成本构成", "单证要点", "红线 / 风险",
          "适用销售场景", "政策依据", "状态"]

S2_ROWS = [
    ["P1-01", "纱线", "本地采购（越南境内非 EPE 供应商）", "越南境内非 EPE 纱厂",
     "内销 / 出口均可用", "—", "8%（进项可抵）", "—", "否",
     "供应商开越南 VAT 发票 8%，VND 结算",
     "货价（含 8% 进项，内销可抵、出口可退）",
     "VAT 进项发票＋送货单＋合同",
     "🟡 供应商为 EPE/保税则不能开 8% 发票，须按视同进口处理；🟡 出口退税需进项发票与出口报关单勾稽",
     "S1-07（内销）、S1-01（出口，可退税）、S1-02~04（出口）",
     "Luật GTGT 2024；NĐ 181/2025 Đ29", "已定稿"],

    ["P1-02", "纱线", "一般贸易进口", "境外供应商（中国等）",
     "内销 / 出口均可用", "按 HS（原表口径 3%，⚠️待核）", "8%/10%（进口环节缴，可抵）",
     "🟡 中国产纱线 3.57%–17.45%（按出口商分档）", "否（已完税，自由处置）",
     "境外供应商开 CI，USD 结算",
     "货价＋进口关税＋反倾销税＋进口 VAT（可抵）",
     "进口报关单＋CI/PL＋原产地证＋缴税凭证＋反倾销税率适用证明",
     "🔴 反倾销税进成本不可退，是最大刚性成本项；🔴 原产地证不全可能被适用最高档 17.45%",
     "S1-07（内销）、S1-01（出口）",
     "QĐ 2652/QĐ-BCT（2026-10-13，至 2031-10-15 续期 5 年）", "已定稿（税率档待按供应商核）"],

    ["P1-03", "纱线", "保税进口 / SXXK（加工出口用）", "境外供应商（保税）",
     "必须用于出口（复出口核销）", "0（暂不征）", "0（暂不征）",
     "0（复出口不征；若转内销则追征）", "✅ 是（SXXK 核销）",
     "境外供应商开 CI，USD 结算；无越南 VAT 发票",
     "货价；资金不占 VAT",
     "保税进口报关＋单耗表＋核销表＋出口报关单配对",
     "🔴🔴 转内销须先补税（关税＋VAT＋反倾销），未补即内销＝重大稽查风险；🔴 单耗＝实际用量＝出口数量必须对平",
     "S1-02~05（出口）、S1-07（若转内销须先补税）",
     "NĐ 134/2016／NĐ 18/2021；NĐ 181/2025", "已定稿"],

    ["P1-04", "纱线", "自 EPE／非关税区采购（视同进口）", "越南境内 EPE 企业",
     "内销 / 出口均可用", "按 HS（视同进口征税）", "8%/10%（凭缴税凭证可抵）",
     "🟡 视同进口时是否计征反倾销须关务确认", "否",
     "EPE 开票（非越南 VAT 发票），VND 或 USD",
     "货价＋视同进口关税＋进口 VAT",
     "EPE 出口报关单＋本方就地进口报关单＋缴税凭证",
     "🟡 “供应商出口再进口”路径若报关类型选错（如误用 A42）会被追税；🟡 部分代理称可免，需关务书面确认",
     "S1-07、S1-01",
     "NĐ 134/2016；TT 38/2015", "待关务确认"],

    ["P2-01", "胚布（坯布）", "本地采购（越南境内非 EPE 供应商）", "越南境内非 EPE 织造厂",
     "内销 / 出口均可用", "—", "8%（进项可抵）", "—", "否",
     "8% 越南 VAT 发票，VND",
     "货价（含 8% 进项）",
     "VAT 进项发票＋送货单＋品质单",
     "🟡 本地货源是否能满足规格/产能（华特为产销一体，部分胚布需进口）",
     "S1-07、S1-01", "Luật GTGT 2024", "已定稿"],

    ["P2-02", "胚布（坯布）", "一般贸易进口", "境外供应商（中国等）",
     "内销 / 出口均可用", "按 HS（原表口径 12%，⚠️待核）", "8%/10%（可抵）",
     "⚠️ 待核（布类反倾销适用范围）", "否",
     "CI，USD",
     "货价＋进口关税＋（如适用）反倾销＋进口 VAT（可抵）",
     "进口报关单＋CI/PL＋原产地证＋缴税凭证",
     "🔴 关税刚性进成本、不可退；🔴 若进口后仅做染色加工再内销，涉工业区规定/投资执照问题（原表已自标高风险）",
     "S1-07、S1-01", "NĐ 134/2016；投资执照/工业区规定", "待核"],

    ["P2-03", "胚布（坯布）", "进料加工 / 保税进口（SXXK）", "境外供应商（进料加工）",
     "必须复出口核销", "0（暂不征）", "0（暂不征）",
     "0（复出口不征）", "✅ 是（手册/核销）",
     "CI，USD；无越南 VAT 发票",
     "货价；无进口税资金占用",
     "进料加工手册＋进口报关＋单耗表＋出口报关单＋核销表",
     "🔴🔴 保税胚布染色加工后内销＝违反工业区规定/投资执照（原表自标高危）；🔴 核销不配对→补税＋滞纳金",
     "S1-02~05（出口）", "NĐ 134/2016／NĐ 18/2021", "已定稿"],

    ["P2-04", "胚布（坯布）", "自 EPE／非关税区采购（视同进口）", "越南境内 EPE 企业",
     "内销 / 出口", "按 HS（视同进口）", "8%/10%（可抵）", "⚠️ 待核", "否",
     "EPE 开票，VND 或 USD",
     "货价＋视同进口关税＋进口 VAT",
     "EPE 出口报关＋本方就地进口报关＋缴税凭证",
     "🟡 报关类型选择错误风险（同 P1-04）",
     "S1-07、S1-01", "NĐ 134/2016；TT 38/2015", "待关务确认"],

    ["P3-01", "成品布", "本地采购（越南境内非 EPE 供应商）", "越南境内非 EPE 染整/织造厂",
     "内销 / 出口均可用", "—", "8%（进项可抵）", "—", "否",
     "8% 越南 VAT 发票，VND",
     "货价（含 8% 进项）",
     "VAT 进项发票＋送货单",
     "🟡 成品布本地采购通常最贵（含上游利润），但税负最轻、周期最短",
     "S1-07、S1-01", "Luật GTGT 2024", "已定稿"],

    ["P3-02", "成品布", "一般贸易进口", "境外供应商（中国等）",
     "内销 / 出口均可用", "按 HS（原表口径 12%，⚠️待核）", "8%/10%（可抵）",
     "⚠️ 待核", "否",
     "CI，USD",
     "货价＋关税＋进口 VAT（可抵）",
     "进口报关单＋CI/PL＋原产地证＋缴税凭证",
     "🔴🔴 关税＋VAT 全额先缴且关税不可退，税负最刚性；作为纯贸易转售毛利最薄",
     "S1-07、S1-01", "NĐ 134/2016", "待核"],

    ["P3-03", "成品布", "保税进口（复出口用）", "境外供应商（保税）",
     "必须复出口核销", "0（暂不征）", "0（暂不征）", "0（复出口不征）", "✅ 是",
     "CI，USD",
     "货价",
     "保税进口报关＋核销＋出口报关配对",
     "🔴 直接进口成品布做保税转售，若无实质加工，海关可能质疑保税适用性；🔴 核销不配对补税",
     "S1-02~05（出口）", "NĐ 134/2016", "待关务确认"],

    ["P4-01", "辅料／化学品（油墨、助剂等）", "本地采购（非 EPE）", "越南境内供应商",
     "内销 / 出口均可用", "—", "8%（可抵）", "—", "否",
     "8% VAT 发票，VND",
     "货价（含 8% 进项）",
     "VAT 发票＋送货单＋MSDS",
     "🟡 化学品供应商资质与 MSDS 合规（环保/消防）；🟡 出口退税需能按单耗归集",
     "S1-01~07 全部", "Luật GTGT 2024", "已定稿"],
]

# ---------- 写文件 ----------
wb = Workbook()
wb.remove(wb.active)


def pick_fill(kind, key):
    k = str(key)
    if "不适用" in k or "不成立" in k:
        return FILL_NA
    if kind == "sales":
        if k.startswith("出口"):
            return FILL_EXPORT
        if k.startswith("内销"):
            return FILL_DOM
    else:
        if "本地采购" in k:
            return FILL_EXPORT
        if "自 EPE" in k or "自EPE" in k:
            return FILL_EPE
        if "保税" in k or "进料加工" in k:
            return FILL_BOND
        if "一般贸易进口" in k:
            return FILL_IMPORT
    return None


def build_sheet(ws, title, subtitle, legend, hdr, rows, widths, fills_col=None, kind="sales"):
    ncol = len(hdr)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncol)
    c = ws.cell(row=1, column=1, value=title)
    c.font = TITLE_FONT
    c.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 26

    for i, txt in enumerate(subtitle, start=2):
        ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=ncol)
        cc = ws.cell(row=i, column=1, value=txt)
        cc.font = NOTE_FONT
        cc.alignment = Alignment(vertical="center", wrap_text=True)
        ws.row_dimensions[i].height = 18

    lr = 2 + len(subtitle)
    ws.merge_cells(start_row=lr, start_column=1, end_row=lr, end_column=ncol)
    cc = ws.cell(row=lr, column=1, value=legend)
    cc.font = Font(name="Microsoft YaHei", size=9, bold=True, color="C00000")
    cc.fill = FILL_HEAD2
    cc.alignment = Alignment(vertical="center")
    ws.row_dimensions[lr].height = 20

    hr = lr + 1
    for j, h in enumerate(hdr, start=1):
        cell = ws.cell(row=hr, column=j, value=h)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[hr].height = 34

    for i, row in enumerate(rows, start=hr + 1):
        fill = pick_fill(kind, row[fills_col[0]]) if fills_col else None
        est = 1
        for j, v in enumerate(row, start=1):
            cell = ws.cell(row=i, column=j, value=v)
            cell.font = BOLD if j == 1 else BODY_FONT
            cell.alignment = Alignment(vertical="top", wrap_text=True,
                                       horizontal="center" if j == 1 else "left")
            cell.border = BORDER
            if fill and j > 1:
                cell.fill = fill
            txt = str(v)
            w = widths[j - 1] if j - 1 < len(widths) else 20
            # 中文按 1.8 字宽估算每行字数
            cpl = max(4, w / 1.8)
            lines = sum(max(1, -(-len(seg) // int(cpl))) for seg in txt.split("\n"))
            est = max(est, lines)
        ws.row_dimensions[i].height = min(260, max(66, (est + 0.6) * 15))

    for j, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(j)].width = w

    ws.freeze_panes = ws.cell(row=hr + 1, column=2)
    ws.auto_filter.ref = f"A{hr}:{get_column_letter(ncol)}{hr + len(rows)}"
    return hr, len(rows)


# Sheet1
ws1 = wb.create_sheet("Sheet1-销售与出货模式")
hr1, n1 = build_sheet(
    ws1,
    "Sheet1 · 销售与出货（出口／内销）模式　—— 越南华特（HUATEX VIET NAM）",
    ["读法：一行＝一种交易结构。先看【购买方身份＋收货方身份】，再看【出货性质】和【VAT 率】；红线列＝该结构最容易踩的那条。",
     "核心判断句：Huatex 的 VAT 率取决于「它开票给谁」＋「货是否进非关税区」，不取决于最终客户是谁。卖方是越南居民 → 永远不涉 FCT。",
     "口径来源：2026-10-21 四方/三方场景定稿（问 1–问 6）＋ 2026-10-20 税负模型 v3.1。所有法条为现行 2026 口径。"],
    "图例　🟢 绿＝出口/就地出口 0%　　🟡 黄＝内销 8%（至 2026-12-31）　　🔴 红字行＝不适用/高风险　　⚠️＝待核项",
    S1_HDR, S1_ROWS,
    [9, 24, 40, 12, 14, 18, 26, 20, 22, 24, 20, 26, 26, 34, 30, 38, 34, 24, 16],
    fills_col=(3,), kind="sales",
)

# Sheet2
ws2 = wb.create_sheet("Sheet2-采购与入库模式")
hr2, n2 = build_sheet(
    ws2,
    "Sheet2 · 采购与入库（进口／本地采购）模式　—— 原材料：纱线 / 胚布 / 成品布",
    ["读法：一行＝一种「材料 × 采购方式」。先看材料，再看是【本地采购】还是【进口】；进口再分【一般贸易完税】【保税/进料加工免税但须核销】【自 EPE 视同进口】四种。",
     "核心判断句：进口环节的税负差别不在 VAT（可抵），而在【关税＋反倾销是否进成本】以及【料件能否核销】。保税料件转内销必须先补税。",
     "⚠️ 关税税率沿用 2023 原表口径（纱线 3%、布类 12%），2026 现行 MFN 税率需按具体 HS 编码核对，勿直接用于报价。"],
    "图例　🟢 绿＝本地采购（8% 进项可抵/可退）　　🟡 黄＝一般贸易进口（关税刚性进成本）　　🔵 蓝＝保税/进料加工（免税但须核销）　　🟣 紫＝自 EPE 视同进口（须报关缴税）",
    S2_HDR, S2_ROWS,
    [9, 16, 30, 22, 16, 22, 18, 24, 16, 24, 30, 32, 40, 26, 26, 20],
    fills_col=(2,), kind="purchase",
)

wb.save(OUT)
print("saved:", OUT, "| sheet1 rows:", n1, "| sheet2 rows:", n2)
