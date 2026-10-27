# G08 批次执行汇总（v2.8e / run_loan_2025_12_v28d.py）

- 执行时间：2026-10-23 17:03 → 17:11（约 8 分钟）
- 输入：`work/loan-materials-2026-10/in/L1-G08.xlsx`（32 票）
- 月份范围：2025-THÁNG 12 + 2026-01~10（11 个月），RM 目录 1236 个
- 未修改任何脚本（纯执行）

## STAGE 路径
```
work/loan-materials-2025-12/out/v2.8d-2025_12-G08-20261023_1704/
├── Outcome1-v2.8d-2025_12-20261023_1704.xlsx   (33 行含表头 × 13 列)
├── 处理报告-v2.8d-2025_12-20261023_1704.txt
└── Outcome2/  (32 个票号目录)
```

## 内容标签审计（audit_outcome2_from_report.py 原样输出）
```
=== v2.8d-2025_12-G08-20261023_1704 (32 票): {'成对': 30, '只有Excel': 1, '空夹(源盘无目录)': 1}
    只有Excel          HMFZV260066  BIL HUATEX77.pdf | SKM_28726081416400.pdf | 0813-HMFZV260066-成品空运清关资料中英文明细xlsm -.xlsm | ToKhaiHQ7N_Q
    空夹(源盘无目录)        HMXCM260011
```
- 成对 30 / 只有 PDF 0 / 只有 Excel 1 / 空夹 1

## 未决问题（处理报告原文）
- ① 未匹配到目录的票号：**HMXCM260011**
- ② 经 base 回退定位：无
- ③ 经 -N 兄弟目录回退定位：无

## 抽检
- 32-HMXCFZAZ260001：4 件（BIL HUATEX21.pdf / 出货资料 xlsm / 出货资料 pdf / ToKhaiHQ7N_QDTQ_108559617500.xls）— 与 SUMMARY 4 件一致
- 16-HMFZV260066：2 PDF + 1 xlsm + 1 ToKhai xlsx（审计判为「只有Excel」，非成对）
- 18-HMXCM260011：目录为空，确认空夹

## 异常
- 日志 ERROR=0、COPY-ERR=0、Traceback=0
- 仅有 pypdf 字体告警：`Could not get FontBBox from font descriptor`（不影响产出）
