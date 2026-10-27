# G09 批次执行摘要（v2.8e）

- 批次：G09，32 票
- 输入：work/loan-materials-2026-10/in/L1-G09.xlsx
- 月份：2025-12 + 2026-01 ~ 2026-10（11 个月）
- 启动：2026-10-23 17:04，耗时约 7 分钟，exit 0

## STAGE 路径
work/loan-materials-2025-12/out/v2.8d-2025_12-G09-20261023_1704/
- Outcome1-v2.8d-2025_12-20261023_1704.xlsx（32 票，33 行含表头，13 列）
- Outcome2/（32 个票号目录）
- 处理报告-v2.8d-2025_12-20261023_1704.txt

## 内容标签审计（audit_outcome2_from_report.py）
32 票：成对 28｜只有PDF 0｜只有Excel 0｜空夹(源盘无目录) 4

非成对 4 票（全部为源盘无目录空夹）：
- HMFZAX260043
- HMXCM260009
- HMXCP260060
- HMXCP260063

## 未决问题
① 未匹配到目录的票号：HMFZAX260043, HMXCM260009, HMXCP260060, HMXCP260063
② 经 base 回退定位：无
③ 经 -N 兄弟目录回退定位：无

## 异常
- 日志 ERROR / COPY-ERR / Traceback：0 条
- 单次 5 处 "Could not get FontBBox..." 为 pdfminer 字体警告，不影响结果

## 抽检
- 30-HMFZAZ260028：INV.pdf 首段含 "Invoice No."/HUA FENG GROUP INC.；PKL.pdf 首段 "PACKING LIST"；扫描件无文本层属预期
- 23-HMXCFZK260001：4 文件 = 明细 xlsm/pdf + SWB.pdf + ToKhai xlsx，与报告 4 件一致
