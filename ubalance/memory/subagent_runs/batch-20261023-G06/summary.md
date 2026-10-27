# G06 批次执行总结（进出口材料自动化处理 v2.8e）

- **执行时间**：2026-10-23 17:04 → 17:11（约 7 分钟，本机 Tesseract OCR；同期多批并行 load≈7）
- **输入**：`work/loan-materials-2026-10/in/L1-G06.xlsx`（Sheet1，32 行）
- **月份范围**：2025/THÁNG 12 + 2026/THÁNG 01–10（11 个月）
- **脚本**：`scripts/run_loan_2025_12_v28d.py`（未做任何修改）
- **HT_TAG**：G06

## 产出 STAGE 路径
```
/Users/zhaoyuzhao/.openclaw/workspace-balance/work/loan-materials-2025-12/out/v2.8d-2025_12-G06-20261023_1704/
  ├─ Outcome1-v2.8d-2025_12-20261023_1704.xlsx     (13 列, 33 行 = 表头 + 32 票)
  ├─ Outcome2/                                      (32 个文件夹, 共 173 个文件)
  └─ 处理报告-v2.8d-2025_12-20261023_1704.txt      (46.9KB)
```

## Outcome2 内容标签审计（audit_outcome2_from_report.py 原样输出）
```
=== v2.8d-2025_12-G06-20261023_1704 (32 票): {'只有PDF': 1, '成对': 30, '空夹(源盘无目录)': 1}
    只有PDF            YNHT20261309-1  YNHT20261309-1  箱单发票-华特（晟威）-越南清关--COSCO(1).pdf | COAU7268996830-SWB.pdf | ToKhaiHQ7N_QDTQ_1082868373
    空夹(源盘无目录)        HMFZK260264
```
- 成对 30 / 只有 PDF 1 / **只有 Excel 0** / 空夹 1
- 非成对票号明细：`YNHT20261309-1`（箱单+发票合并在单一 PDF，无独立 Excel）、`HMFZK260264`（源盘无目录，空夹）

## 未决问题（报告原文）
- ① 未匹配到目录的票号：**HMFZK260264**（唯一）
- ② 经 base 回退定位：无
- ③ 经 -N 兄弟目录回退定位：无

## 完整性（报告「五类完整性汇总」）
- ✅ 完整 30 票
- ⚠️ `YNHT20261309-1` 缺 SalesConfirmation（3 件）
- ⚠️ `HMFZAP260131` 缺 BL_or_AWB（文件名为「成品陆运清关资料」→ 陆运无海运提单，属合理缺失）

## 异常
- 日志无 `ERROR` / `COPY-ERR` / `Traceback`
- 复制文件数（去重）173 = Outcome2 实际文件数 173（一致）
- STAGE 实际落在 `work/loan-materials-2025-12/out/`（脚本内 BATCH 目录命名沿用 2025_12，与历史批次一致，非异常）

## 抽检
| 文件夹 | 文件 | 结论 |
|---|---|---|
| 1-YNHT20261309-1 | SWB.pdf / 箱单发票合并.pdf / ToKhai.xlsx = 3 | 只有 PDF 成立（无独立 Excel 箱单发票） |
| 29-HMFZV260040 | xlsm + contract/inv/pkl pdf + HAWB + HCMAD + SKM + ToKhai xlsx = 8 | 成对成立 |
| 32-HMFZK260264 | 0 | 空夹成立（源盘无该目录） |
