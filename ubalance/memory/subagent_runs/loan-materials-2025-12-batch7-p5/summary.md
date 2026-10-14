# 进出口材料自动化处理 · 批次 p5（全局 STT 211–262）· v2.8d

- **执行时间**：2026-10-14 15:53–16:30（GMT+7）
- **模型**：deepseek/deepseek-v4-flash（如实标注）
- **L1**：`work/loan-materials-2025-12-batch7/split/L1-p5.xlsx`（52 行，全局STT 211–262）
- **RM 源**：`/Volumes/TOSHIBA EXT/HUATEX进出口材料/RM-Database`（2023/2024/2025/2026 四年全库，2342 目录）
- **脚本**：`work/loan-materials-2025-12-batch7/p5/scripts/run_p5_v28d.py`（新增；未改 `scripts/` 下任何既有文件）

## 结果

| 项目 | 值 |
|---|---|
| L1 行数 = Outcome1 行数 | 52 |
| Outcome2 文件夹数 | 52（含 3 个空文件夹） |
| 命中 / 未匹配 | **49 / 3** |
| 未匹配票号 | `HMXCM260011`、`HMFZAX260043`、`HMXCM260009`（四年全库均无目录） |
| 复制文件（去重后） | 245 |
| 去重丢弃件 | 见「处理报告」去重丢弃清单节 |
| Outcome1 三列（发票日期/供应商/采购类别）空白数 | 0 / 0 / 0（全部填充） |
| 供应商 | 全部 `HUA FENG GROUP INC.`（取自 L1） |
| 分类 | 全部「原材料」（HS 50–63 / 品名互证为主） |
| zip | 248 条目 / 49,509,505 bytes（92 非 ASCII 条目全带 UTF-8 标志） |

## 产出物

- `work/loan-materials-2025-12-batch7/p5/out/Outcome1-p5-v2.8d-20261014_1559.xlsx`
- `work/loan-materials-2025-12-batch7/p5/out/Outcome2-p5-v2.8d-20261014_1559.zip`
- `work/loan-materials-2025-12-batch7/p5/out/处理报告-p5-v2.8d-20261014_1559.txt`
- 写回 Toshiba：`/Volumes/TOSHIBA EXT/HUATEX进出口材料/Outcome1-p5-v2.8d-20261014_1559.xlsx`（md5 读回一致）+ `Outcome2-p5-v2.8d-20261014_1559/`

## 公网直链（实测 200 + md5 一致）

- https://always-changed-reviews-material.trycloudflare.com/Outcome1-p5-v2.8d-20261014_1559.xlsx  （10104 B, md5 `f2dc9b506f451e1bcddae4c2780aa50a`）
- https://always-changed-reviews-material.trycloudflare.com/Outcome2-p5-v2.8d-20261014_1559.zip  （49509505 B, md5 `057a423e89d7dc188d16dffe7ddccc7d`）

## 五类完整性（⚠️ 缺项）

- `225-HMFZV260066`：⚠️缺 SalesConfirmation/Invoice/PackingList（RM 该目录仅 BL + ToKhai）
- `226-HMXCFZAT260083`：⚠️缺 ToKhai（合订目录 92.HMXCFZAT260082,-1,…(GỘP …260083,-1)，内无该票 ToKhai）
- `236-HMFZAZ260012`：⚠️缺 ToKhai
- `239-HMFZK260405`：⚠️缺 ToKhai
- `262-7058931375`：⚠️缺 SalesConfirmation/PackingList（纯数字 DHL 单号票）

其余 47 票五类 ✅完整。

## 非标准票号处置

- `IV2607…/IV2608…` 系列 7 票（240/256–261）：exact 命中，正常处理
- `7058931375`（纯数字 DHL）：exact 命中目录 `79.7058931375 DHL A12`，按内容判定 AWB+Invoice+ToKhai
- `HMXCFZAZ260001 / -1 / -2`：各自 exact 命中独立目录

## 未决问题

- 3 票（HMXCM260011 / HMFZAX260043 / HMXCM260009）RM 四年全库无目录 → Outcome1 行 + 空文件夹，备注「目录缺失」。疑为 RM 尚未归档；待 RM 更新后可按时间戳目录安全重跑。
