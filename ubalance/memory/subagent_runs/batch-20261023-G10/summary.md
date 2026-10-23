# G10 批次执行摘要（v2.8e）

- 批次: G10（HT_TAG=G10），输入 L1-G10.xlsx，32 票
- 月份范围: 2025/THÁNG 12 + 2026/THÁNG 01~10（11 个月）
- 脚本: scripts/run_loan_2025_12_v28d.py（未做任何修改）
- 日志: work/loan-materials-2026-10/logs/run-G10.log（80 行，含 ===SUMMARY===）
- 耗时: 17:04 启动 → 17:11 完成（约 7 分钟）

## STAGE 路径
- Outcome1: work/loan-materials-2025-12/out/v2.8d-2025_12-G10-20261023_1704/Outcome1-v2.8d-2025_12-20261023_1704.xlsx
- Outcome2: 同目录 Outcome2/（32 个子目录，161 个文件）
- 处理报告: 同目录 处理报告-v2.8d-2025_12-20261023_1704.txt

## 内容标签审计（audit_outcome2_from_report.py 原样输出）
`=== v2.8d-2025_12-G10-20261023_1704 (32 票): {'成对': 29, '空夹(源盘无目录)': 3}`
- 成对 29｜只有PDF 0｜只有Excel 0｜空夹 3
- 空夹: HMXCAW260099 / HMXCP260070 / HMXCP260072

## 未决问题
- ① 未匹配到目录的票号: HMXCAW260099, HMXCP260070, HMXCP260072
- ② base 回退: 无；③ -N 兄弟目录回退: 无

## 异常
- 无 ERROR / COPY-ERR / Traceback
- DEDUP-DROP 7 条（HMXCFZK260005×3、HMFZAZ260027×1、HMXCFZK260007×3），均已留痕不静默丢件
- 完整性缺口（非异常，材料缺失待补）: 缺 ToKhai 6 票（HMFZK260470/471/472、HMFZAR260031、IV260912149）；缺 BL_or_AWB 1 票（HMFZAZ260038）
