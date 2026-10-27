#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交接清单增量填写工具
用法:
  python3 handover_tool.py append "② 工作职责清单" rows.json
rows.json = {"rows": [[...], [...]]}
"""
import json
import sys
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

XLSX = "/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/output/工作交接清单_赵毓钊_正式版.xlsx"
GREY = "F7F7F7"
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)


def append(sheet_name, rows):
    wb = openpyxl.load_workbook(XLSX)
    ws = wb[sheet_name]
    ncols = ws.max_column
    # 找最后一行有内容的行（A列）
    last = 3
    for r in range(4, ws.max_row + 1):
        if ws.cell(row=r, column=1).value not in (None, ""):
            last = r
    start = last + 1
    # 序号中文化连续
    for i, row in enumerate(rows):
        r = start + i
        ws.row_dimensions[r].height = 34
        # row[0] 对应第2列（第1列固定为序号），自动右移一格
        for ci in range(2, ncols + 1):
            val = row[ci - 2] if ci - 2 < len(row) else None
            cell = ws.cell(row=r, column=ci, value=val)
            cell.font = Font(name="微软雅黑", size=10)
            cell.alignment = Alignment(vertical="center", wrap_text=True,
                                       horizontal="left", indent=1)
            cell.border = BORDER
            if (r - 4) % 2 == 1:
                cell.fill = PatternFill("solid", fgColor=GREY)
        c1 = ws.cell(row=r, column=1, value=r - 3)
        c1.font = Font(name="微软雅黑", size=10)
        c1.alignment = Alignment(vertical="center", horizontal="center")
        c1.border = BORDER
        if (r - 4) % 2 == 1:
            c1.fill = PatternFill("solid", fgColor=GREY)
    # 刷新筛选范围
    ws.auto_filter.ref = f"A3:{get_column_letter(ncols)}{start + len(rows) - 1}"
    wb.save(XLSX)
    print(f"appended {len(rows)} rows to [{sheet_name}], now last row = {start + len(rows) - 1}")


if __name__ == "__main__":
    sheet = sys.argv[1]
    with open(sys.argv[2], encoding="utf-8") as f:
        data = json.load(f)
    append(sheet, data["rows"])
