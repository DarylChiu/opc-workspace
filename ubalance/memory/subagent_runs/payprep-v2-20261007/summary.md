# 任务 summary · payprep-v2-20261007

- **任务**：按《改造规格 v2（Payment 核销工作流·银行受托支付）》实现 9 条 Daryl 口径 + 3 条补充/修正，
  跑回归 + 1005 批次试跑，回报 Balance ⚖️（**未覆盖任何已交付文件**）
- **时间**：2026-10-07 15:53–16:35（Asia/Saigon）
- **结果**：回归全绿 **34/34**；1005 试跑 VND 表 H 合计 = **9,799,973,728**（逐位一致），0 占位符摘要

## 产出物
| 类型 | 路径 |
|---|---|
| 交付候选（VND 表） | `work/Mai岗位效率优化专案/out/preview-v2/Payment request to Bank-20261005.xlsx` |
| 非 VND 表（Q5） | `.../Payment request to Bank-20261005-nonVND.xlsx` |
| 发票级台账（D3/F2） | `.../Payment recon ledger-20261005.xlsx` |
| 卷级对账报告 | `.../Payment request to Bank-20261005.xlsx.recon.txt` |
| 台账 sidecar（审计底稿） | `.../Payment request to Bank-20261005.xlsx.recon.json` |
| 回归日志 | `.../regress_invoices-20261007.log`（34/34） |
| 中间稿（保留，不删） | `.../_superseded/`（-r2 / -r3） |
| 流程文档 v2 | `work/Mai岗位效率优化专案/Payment核销流程-银行受托支付-v2-20261007.md` |

## 脚本改动
`vn_invoice_parse.py`（号码来源 body/ocr-header/filename + 数字归一 + 页眉定向 OCR + Q8 正式 e-invoice 判定·仅 OCR 票）
`gen_payment_recon_v2.py`（plan_group 5 级金额优先序 + note_group 越语备注 + 币别分流 + 碎行保护 + .recon.json sidecar）
`payment_recon_finalize.py`（--submit 提交版净化 + --hdr-currency）
`payprep.py`（-rN 唯一命名 / --rev / 非 VND 表 / 默认提交净化 / 行缓冲日志 / 异常退出码）
新增 `recon_ledger.py`、`regress_invoices.sh` + `regress_invoices.py` + fixtures（16 样本 + 卷级用例）

## 未决 / 风险
1. 目录 28：卷内 512/514，明细只对应 514 → 走「只取全额=付款额的票」单行，备注说明 512 未计入（如要机械部分付款口径，一句开关）。
2. 目录 44/48：附件与请款不符（44 = 合同+订单无发票；48 = 344.pdf 而事由要 444）→ 建议退业务补票。
3. 目录 38：文本层 9.504.000.000 vs 候选 95.040.000（== 明细）→ 按「OCR 不准」备注，待人工核。
4. 期间有并行会话同步修改同一批脚本（已对最终态重新验收，结论一致）。
