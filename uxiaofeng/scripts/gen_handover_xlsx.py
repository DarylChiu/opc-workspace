#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工作交接 Excel 模板生成器 (Bryson)"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

NAVY = "1F3864"
BLUE = "2E5C8A"
LIGHT = "DCE6F1"
GREY = "F2F2F2"

thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = openpyxl.Workbook()


def title_block(ws, title, subtitle, ncols):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    c = ws.cell(row=1, column=1, value=title)
    c.font = Font(name="微软雅黑", size=14, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 30

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
    c2 = ws.cell(row=2, column=1, value=subtitle)
    c2.font = Font(name="微软雅黑", size=9, italic=True, color="595959")
    c2.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[2].height = 18


def header_row(ws, row, headers, widths):
    for i, (h, w) in enumerate(zip(headers, widths), start=1):
        c = ws.cell(row=row, column=i, value=h)
        c.font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=BLUE)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDER
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[row].height = 30


def body(ws, start_row, nrows, ncols):
    for r in range(start_row, start_row + nrows):
        ws.row_dimensions[r].height = 22
        for c in range(1, ncols + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = Font(name="微软雅黑", size=10)
            cell.alignment = Alignment(vertical="center", wrap_text=True, horizontal="left", indent=1)
            cell.border = BORDER
            if (r - start_row) % 2 == 1:
                cell.fill = PatternFill("solid", fgColor=GREY)


def sheet(name, title, subtitle, headers, widths, nrows, validations=None, freeze="A4"):
    ws = wb.create_sheet(name)
    title_block(ws, title, subtitle, len(headers))
    header_row(ws, 3, headers, widths)
    body(ws, 4, nrows, len(headers))
    ws.freeze_panes = freeze
    ws.auto_filter.ref = f"A3:{get_column_letter(len(headers))}{3 + nrows}"
    if validations:
        for col_idx, options in validations:
            dv = DataValidation(type="list", formula1='"' + ",".join(options) + '"', allow_blank=True)
            ws.add_data_validation(dv)
            L = get_column_letter(col_idx)
            dv.add(f"{L}4:{L}{3 + nrows}")
    return ws


# ---------------- 0. 交接概要 ----------------
ws = wb.active
ws.title = "① 交接概要"
title_block(ws, "工作交接清单 (Work Handover)", "Fill in → 逐项确认 → 双方签字 → 归档。灰色为说明行，可直接删除。", 4)

rows = [
    ("交接人 (Handover By)", ""),
    ("接手人 (Handover To)", ""),
    ("交接人岗位", ""),
    ("所属部门", ""),
    ("直属上级", ""),
    ("预计离职/调岗日期", ""),
    ("交接启动日期", ""),
    ("交接完成日期", ""),
    ("交接方式", "□ 面谈  □ 文档  □ 系统演示  □ 陪同实操"),
    ("交接范围概述", ""),
    ("遗留风险提示", ""),
]
r = 4
for k, v in rows:
    ws.cell(row=r, column=1, value=k).font = Font(name="微软雅黑", size=10, bold=True)
    ws.cell(row=r, column=1).fill = PatternFill("solid", fgColor=LIGHT)
    ws.cell(row=r, column=1).border = BORDER
    ws.cell(row=r, column=1).alignment = Alignment(vertical="center", indent=1)
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    c = ws.cell(row=r, column=2, value=v)
    c.font = Font(name="微软雅黑", size=10)
    c.alignment = Alignment(vertical="center", indent=1)
    c.border = BORDER
    ws.row_dimensions[r].height = 26
    r += 1
for col, w in zip("ABCD", [22, 26, 26, 26]):
    ws.column_dimensions[col].width = w

ws.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=4)
c = ws.cell(row=r + 1, column=1, value="使用说明：① 先填概要 → ② 逐表填写（职责/待办/资料/账号/联系人/风险）→ ③ 交接会上逐项打勾确认 → ④ 末页签字 → ⑤ 打印归档或存共享盘。")
c.font = Font(name="微软雅黑", size=9, color="C00000")
c.alignment = Alignment(vertical="center", wrap_text=True, indent=1)

# ---------------- 1. 职责清单 ----------------
sheet(
    "② 工作职责清单",
    "工作职责清单 (Scope of Duties)",
    "逐条列出你负责的全部工作，颗粒度到「接手人能独立执行」为止。",
    ["序号", "职责模块", "具体工作内容", "执行频率", "投入占比", "关键时间节点/截止日", "接手人", "熟练度要求", "当前状态", "备注"],
    [6, 16, 42, 12, 10, 20, 12, 12, 12, 24],
    20,
    validations=[
        (4, ["每日", "每周", "每月", "每季", "每年", "不定期", "项目制"]),
        (8, ["了解即可", "需培训", "需实操", "需独立承担"]),
        (9, ["已交接", "进行中", "未开始"]),
    ],
)

# ---------------- 2. 待办事项 ----------------
sheet(
    "③ 待办与进行中事项",
    "待办与进行中事项 (Open Items)",
    "所有「不做会出事」的事都放这里。接手人第一周就看这张表。",
    ["序号", "事项名称", "背景/来龙去脉", "当前进度", "下一步动作", "截止日期", "相关方/对接人", "风险等级", "资料存放位置"],
    [6, 24, 40, 14, 30, 14, 18, 10, 26],
    20,
    validations=[
        (4, ["未开始", "进行中", "待审批", "待回复", "已完成"]),
        (8, ["高", "中", "低"]),
    ],
)

# ---------------- 3. 文档资料索引 ----------------
sheet(
    "④ 文档与资料索引",
    "文档与资料索引 (Documents & Files)",
    "路径必须能被接手人直接打开，禁止写「在我电脑里」。",
    ["序号", "资料名称", "类型", "存储路径 / 链接", "访问权限", "负责人", "更新频率", "是否已确认可访问"],
    [6, 30, 14, 44, 14, 12, 12, 18],
    20,
    validations=[
        (3, ["制度文件", "合同协议", "财务台账", "报表模板", "操作手册", "邮件记录", "其他"]),
        (8, ["是", "否"]),
    ],
)

# ---------------- 4. 系统与账号 ----------------
sheet(
    "⑤ 系统与账号权限",
    "系统与账号权限 (Systems & Access)",
    "账号密码切勿明文写入本表，只写「存放位置」。交接后应立即改密或回收权限。",
    ["序号", "系统/平台名称", "用途", "账号持有人", "权限级别", "密码存放方式", "权限回收/移交方式", "已处理"],
    [6, 24, 26, 14, 14, 22, 26, 12],
    15,
    validations=[
        (5, ["管理员", "普通用户", "只读", "审批权限"]),
        (8, ["是", "否", "不适用"]),
    ],
)

# ---------------- 5. 联系人 ----------------
sheet(
    "⑥ 关键联系人与对接方",
    "关键联系人与对接方 (Key Contacts)",
    "内外部对接人都列出来，含沟通习惯与注意事项。",
    ["序号", "姓名", "单位/部门", "职务", "负责事项", "联系方式", "沟通频率", "注意事项/雷区"],
    [6, 12, 20, 14, 30, 22, 12, 30],
    20,
)

# ---------------- 6. 风险与注意事项 ----------------
sheet(
    "⑦ 风险与注意事项",
    "风险与注意事项 (Risks & Watch-outs)",
    "写清楚「为什么这么做」，避免接手人踩同样的坑。",
    ["序号", "风险点 / 历史坑", "触发条件", "潜在影响", "缓解措施 / 应对方式", "责任人", "严重程度"],
    [6, 34, 22, 26, 34, 12, 10],
    15,
    validations=[(7, ["高", "中", "低"])],
)

# ---------------- 7. 交接确认 ----------------
ws = wb.create_sheet("⑧ 交接确认签署")
title_block(ws, "交接确认签署 (Sign-off)", "双方逐项确认后签字，扫描件随本表归档。", 4)

conf = [
    "清单内工作职责已逐项讲解，接手人可独立执行",
    "待办事项已确认责任人与时间节点",
    "文档资料已确认可正常访问",
    "系统账号权限已完成移交/回收",
    "关键联系人已引荐完成",
    "在办项目状态已同步至相关方",
    "遗留风险与注意事项已书面知会",
]
ws.cell(row=3, column=1, value="确认项").font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
ws.cell(row=3, column=1).fill = PatternFill("solid", fgColor=BLUE)
ws.cell(row=3, column=2, value="交接人确认").font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
ws.cell(row=3, column=2).fill = PatternFill("solid", fgColor=BLUE)
ws.cell(row=3, column=3, value="接手人确认").font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
ws.cell(row=3, column=3).fill = PatternFill("solid", fgColor=BLUE)
ws.cell(row=3, column=4, value="备注").font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
ws.cell(row=3, column=4).fill = PatternFill("solid", fgColor=BLUE)
for c in range(1, 5):
    ws.cell(row=3, column=c).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=3, column=c).border = BORDER

rr = 4
for item in conf:
    ws.cell(row=rr, column=1, value=item)
    ws.cell(row=rr, column=2, value="□")
    ws.cell(row=rr, column=3, value="□")
    for c in range(1, 5):
        cell = ws.cell(row=rr, column=c)
        cell.font = Font(name="微软雅黑", size=10)
        cell.border = BORDER
        cell.alignment = Alignment(vertical="center", wrap_text=True, horizontal="center" if c in (2, 3) else "left", indent=0 if c in (2, 3) else 1)
    ws.row_dimensions[rr].height = 24
    rr += 1

rr += 1
sign = [
    ("交接人签字：", "日期："),
    ("接手人签字：", "日期："),
    ("监交人 (上级) 签字：", "日期："),
]
for a, b in sign:
    ws.cell(row=rr, column=1, value=a).font = Font(name="微软雅黑", size=11, bold=True)
    ws.merge_cells(start_row=rr, start_column=3, end_row=rr, end_column=4)
    ws.cell(row=rr, column=3, value=b).font = Font(name="微软雅黑", size=10)
    ws.row_dimensions[rr].height = 34
    rr += 2

for col, w in zip("ABCD", [44, 14, 14, 26]):
    ws.column_dimensions[col].width = w

out = "/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/output/工作交接清单_模板_v1.xlsx"
import os
os.makedirs(os.path.dirname(out), exist_ok=True)
wb.save(out)
print("saved:", out)
print("sheets:", wb.sheetnames)
