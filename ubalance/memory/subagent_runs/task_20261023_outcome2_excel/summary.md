# v2.8e 回归：SC/INV/PL 的 Excel 版是否收进 Outcome2

- 任务号：task_20261023_outcome2_excel
- 执行时间：2026-10-23 10:45:55 → 10:47:29（94 秒，全跑完）
- STAGE：`work/loan-materials-2025-12/out/v2.8d-2025_12-20261023_1045/`
- 基线：`work/loan-materials-2025-12/out/v2.8d-2025_12-20261014_1526/`

## 结论
**达标**。18 张有清关资料的票，全部同时拿到「清关资料中英文明细」的 PDF 版 + Excel 版（xlsx/xlsm），Excel 工作簿内含 合同/发票/装箱 三表 → SC/INV/PL 三标签齐备。0 票只有 PDF，0 票只有 Excel，0 误收兄弟票。

## 数据
- Outcome2 文件数：70 → 88（+18，增量恰为 18 份清关资料 Excel，无删减）
- Outcome1 唯一变化：HMXCAR250004 `⚠️缺SalesConfirmation` → `✅完整`
  - 原因：该票 PDF 的 OCR 只识别出 INVOICE+PACKING_LIST；Excel 提供 SALES_CONTRACT（工作表「合同」）补齐
- 剔除清单 158 行中，仍含「清关资料」的仅 2 条，均为兄弟票 NHFMYAT250029-1（非 L1 票，正确剔除为 OTHER_TICKET）
- 空目录票：HMXCAM250001、HMFZR250008（RM 盘无目录，与基线一致，非本次回归问题）

## 遗留风险
`excel_doc_tags()` / `excel_text()` 只支持 `.xlsx/.xlsm`；legacy `.xls`（BIFF）返回空集 → 若某票清关资料明细只存 .xls 会被判 OTHER。本批未发生（本批明细全为 .xlsx/.xlsm）。
