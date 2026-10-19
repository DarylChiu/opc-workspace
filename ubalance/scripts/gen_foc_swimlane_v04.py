#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FOC 各部门配合节点泳道图 v0.4 (2026-10-19)
- 去掉所有角落备注
- 财务部待 A&C 回复的口径不展开，仅标注「待A&C」
- 突出流程流转 + 责任划分（RACI）
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib import font_manager, rcParams

CJK = "Hiragino Sans GB"
rcParams["font.family"] = CJK
rcParams["axes.unicode_minus"] = False

# ---------------- 数据 ----------------
PHASES = [
    "① 触发与受理",
    "② 依据文件建立",
    "③ 出库与报关",
    "④ 单证归集",
    "⑤ 开票与账务",
    "⑥ 申报与归档",
]

LANES = [
    ("业务部", "#EAF2FB", "#2C6FB5"),
    ("法务部", "#F4ECF9", "#7B4FA0"),
    ("关务部", "#EAF6EC", "#2E7D46"),
    ("财务部", "#FDF3E3", "#B57514"),
    ("外部 / 客户 / 海关", "#F1F1F1", "#5F5F5F"),
]

# node: key, phase, lane, title, detail(list), raci, pending(bool), node_h
NODES = [
    ("N1", 0, 0, "① 客诉受理", ["环思开客诉单", "客诉确认邮件 CC 财务"],
     "R", False),
    ("N2", 0, 0, "② 送样需求", ["开发组提出送样", "环思登记 sample·免费"],
     "R", False),

    ("N3", 1, 0, "③ 责任判定", ["品管/生产/客户邮件确认"],
     "R/A", False),

    ("N4", 2, 0, "④ 补料·送样出库", ["原PO + `-Re`｜sample 免费", "→ 出库单"],
     "R", False),

    ("N5", 3, 0, "⑤ 结案与补件", ["客诉：OA核销+环思结案单", "送样：开发组审批/签字件"],
     "R", False),

    ("N6", 1, 1, "⑥ 补货协议 / 合同补充协议",
     ["不合格品数量·价值·责任·补偿方式", "加工费调整机制 → 协议定稿"], "A", False),

    ("N7", 4, 1, "⑦ 对价调整（条件触发）",
     ["HFGI 承担 → 补充协议＋调整发票", "HUATEX 自担 → 不调加工费"], "A", False),

    ("N8", 2, 2, "⑧ 报关类型判定", ["按客户在越性质：B系列 / E系列"],
     "R", False),
    ("N9", 2, 2, "⑨ 报关", ["就地出口 / 进口；合并报关按性质标记行项"],
     "R", False),
    ("N10", 3, 2, "⑩ 单证交付",
     ["报关单 · 按性质拆分FOC清单", "DHL代报关记录（≥60USD）"], "C", False),
    ("N11", 5, 2, "11  核销·决算资料", ["消耗定额 ＝ 实际用量 ＝ 出口数量"],
     "C", False),

    ("N12", 0, 3, "12  知情登记", ["客诉邮件 CC 本邮箱", "仅建索引，不判定"], "I", False),
    ("N13", 3, 3, "13  单证完整性核对",
     ["客诉单号 → 出库单 → 报关单 → 发票号"], "R", False),
    ("N14", 4, 3, "14  开 FOC 发票",
     ["商业发票 Amount=FOC", "非商业发票 NO PAYMENT"], "R", True),
    ("N15", 4, 3, "15  账务处理", ["成本结转 / 费用科目"], "R", True),
    ("N16", 5, 3, "16  申报与归档", ["VAT / CIT 申报", "三口径台账（报关值/票面价/成本）"],
     "R", True),

    ("N17", 2, 4, "客户 Sintex / Exprinta", ["就地进口手续（Exprinta 办）"],
     "C", False),
    ("N18", 5, 4, "海关 → 税局 月度通报", ["01/TB-XNKTC/GSQL 清单"], "C", False),
]

# 流转箭头：from, to, 连线样式
EDGES = [
    ("N1", "N12"), ("N1", "N6"), ("N3", "N6"), ("N6", "N9"),
    ("N3", "N4"), ("N4", "N8"), ("N8", "N9"), ("N9", "N10"),
    ("N10", "N13"), ("N5", "N13"), ("N13", "N14"),
    ("N14", "N15"), ("N15", "N16"), ("N16", "N18"), ("N11", "N16"),
    ("N9", "N17"),
]

RACI = {
    "R": ("执行", "#2E7D46"),
    "R/A": ("执行+定责", "#1F6FB2"),
    "A": ("定责/签发", "#7B4FA0"),
    "C": ("配合提供", "#B57514"),
    "I": ("知情", "#6E6E6E"),
}


def main():
    fig_w, fig_h = 19.2, 10.2
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=170)
    ax = fig.add_axes([0.045, 0.03, 0.945, 0.855])
    ax.set_xlim(-0.72, 6)
    ax.set_ylim(0, 5.52)
    ax.axis("off")

    lane_h = 1.0
    # 泳道底
    for i, (name, bg, br) in enumerate(LANES):
        y = 5 - (i + 1) * lane_h
        ax.add_patch(Rectangle((0, y), 6, lane_h, facecolor=bg, edgecolor="white",
                               linewidth=2.2, zorder=1))
    # 阶段分隔线
    for p in range(1, 6):
        ax.plot([p, p], [0, 5], color="white", lw=1.6, zorder=2)

    # 阶段表头
    for p, name in enumerate(PHASES):
        ax.add_patch(FancyBboxPatch((p + 0.03, 5.06), 0.94, 0.40,
                                    boxstyle="round,pad=0.012,rounding_size=0.04",
                                    facecolor="#20456B", edgecolor="none", zorder=4))
        ax.text(p + 0.5, 5.26, name, ha="center", va="center",
                fontsize=12.5, color="white", fontweight="bold", zorder=5)

    # 泳道标签
    for i, (name, bg, br) in enumerate(LANES):
        y = 5 - (i + 1) * lane_h
        ax.text(-0.66, y + lane_h / 2, name, ha="left", va="center",
                fontsize=11.5, color=br, fontweight="bold", zorder=4,
                rotation=0)
        ax.plot([0, 6], [y + lane_h, y + lane_h], color="white", lw=2.0, zorder=2)

    # 节点布局
    pos = {}
    from collections import defaultdict
    cells = defaultdict(list)
    for n in NODES:
        cells[(n[1], n[2])].append(n)

    for (p, l), items in cells.items():
        y_c = 5 - l * lane_h - lane_h / 2
        n = len(items)
        if n == 2:
            heights = [0.40, 0.40]
            ys = [y_c + 0.225, y_c - 0.225]
        else:
            heights = [0.60]
            ys = [y_c]
        for it, h, yy in zip(items, heights, ys):
            key, ph, ln, title, details, raci, pending = it
            w = 0.90
            x0 = p + 0.05
            ec = "#C0392B" if pending else LANES[ln][2]
            ls = (0, (4, 2.2)) if pending else "solid"
            ax.add_patch(FancyBboxPatch((x0, yy - h / 2), w, h,
                                        boxstyle="round,pad=0.008,rounding_size=0.03",
                                        facecolor="white", edgecolor=ec,
                                        linewidth=1.5, linestyle=ls, zorder=6))
            # 标题
            ty = yy + h / 2 - 0.055
            ax.text(x0 + 0.02, ty, title, ha="left", va="top",
                    fontsize=8.6 if n == 2 else 9.6, color="#1A1A1A",
                    fontweight="bold", zorder=7)
            # 明细
            dy = ty - (0.135 if n == 2 else 0.165)
            for d in details:
                ax.text(x0 + 0.02, dy, d, ha="left", va="top",
                        fontsize=7.0 if n == 2 else 7.9, color="#3A3A3A", zorder=7)
                dy -= 0.108 if n == 2 else 0.135
            if pending:
                ax.text(x0 + 0.02, yy - h / 2 + 0.035, "〔口径待 A&C 书面回复〕",
                        ha="left", va="bottom", fontsize=6.6,
                        color="#C0392B", style="italic", zorder=7)
            # RACI 标记
            lbl, col = RACI[raci]
            ax.add_patch(FancyBboxPatch((x0 + w - 0.135, yy + h / 2 - 0.115), 0.125, 0.10,
                                        boxstyle="round,pad=0.004,rounding_size=0.02",
                                        facecolor=col, edgecolor="none", zorder=8))
            ax.text(x0 + w - 0.0725, yy + h / 2 - 0.065, raci, ha="center", va="center",
                    fontsize=5.8, color="white", fontweight="bold", zorder=9)
            pos[key] = (x0, yy, w, h)

    # 箭头
    for a, b in EDGES:
        x0, y0, w0, h0 = pos[a]
        x1, y1, w1, h1 = pos[b]
        # 起点：右中 或 下中；终点：左中/上中
        if abs(x0 - x1) < 1e-6:  # 同列
            sx, sy = x0 + w0 * 0.5, y0 - h0 / 2
            ex, ey = x1 + w1 * 0.5, y1 + h1 / 2
        else:
            sx, sy = x0 + w0, y0 + (0.10 if y0 > y1 else -0.10)
            ex, ey = x1, y1 + (0.08 if y0 > y1 else -0.08)
        ax.add_patch(FancyArrowPatch((sx, sy), (ex, ey),
                                     arrowstyle="-|>", mutation_scale=11,
                                     linewidth=1.15, color="#6B7A8C",
                                     connectionstyle="arc3,rad=0.06", zorder=3,
                                     shrinkA=1, shrinkB=1))

    # 标题 + 图例（顶部，不做页脚备注）
    fig.text(0.045, 0.955, "FOC 各部门配合节点泳道图", fontsize=20.5,
             fontweight="bold", color="#14304A", ha="left")
    fig.text(0.045, 0.925,
             "流程流转 + 责任划分｜v0.4 · 2026-10-19｜财务虚线框＝口径待 A&C 书面回复，不展开具体要求",
             fontsize=9.6, color="#5A6B7B", ha="left")

    lx = 0.62
    for code in ["R", "R/A", "A", "C", "I"]:
        lbl, col = RACI[code]
        fig.text(lx, 0.928, code, fontsize=8.0, color="white", fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.28", facecolor=col, edgecolor="none"))
        fig.text(lx + 0.022, 0.928, lbl, fontsize=8.6, color="#3A3A3A", va="center")
        lx += 0.075

    out = "deliverables/FOC配合节点泳道图-v0.4-20261019.png"
    fig.savefig(out, facecolor="white")
    print("saved:", out)


if __name__ == "__main__":
    main()
