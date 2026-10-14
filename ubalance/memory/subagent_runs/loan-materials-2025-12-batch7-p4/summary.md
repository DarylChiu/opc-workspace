# 批次 p4 · 进出口材料自动化处理 v2.8d · 执行摘要

- **批次**: p4（全局 STT **159–210**，共 **52** 条）
- **输入**: `work/loan-materials-2025-12-batch7/split/L1-p4.xlsx`（列：全局STT / 形式发票号 / 供应商）
- **口径**: v2.8d（唯一有效版本）
- **执行时间**: 2026-10-14 15:58 → 16:28（GMT+7）
- **源**: `/Volumes/TOSHIBA EXT/HUATEX进出口材料/RM-Database`（全库 2023/2024/2025/2026，32 个月目录，2342 目录）
- **模型**: deepseek/deepseek-v4-flash（如实标注）
- **TS**: 20261014_1558

## 结果概览

| 项目 | 结果 |
|---|---|
| Outcome1 行数 | **52**（STT 159–210 连续，未重排） |
| Outcome2 文件夹数 | **52**（含 3 个空文件夹） |
| 命中 / 未命中 | **49 / 52** |
| 复制文件数（已去重） | **233** |
| 去重丢弃 | **3** 件（均为 md5 内容重复） |
| 五类完整性 | ✅完整 **47** ／ ⚠️缺 **5** |
| 金额合计 | **1,275,808.17 USD** |
| zip | `Outcome2-p4-v2.8d-20261014_1558.zip`，**285 条目（52 目录 + 233 文件）**，53,424,040 字节 |
| zip UTF-8 | 非ASCII 115 条目 = 带 UTF-8 标志 115 条目 ✅ |

## 命中 / 未命中（逐票）

**命中 49/52**：159–175、177–179、181–192、**189**、190–192、194–202、204–210（含 base 回退…本批 0 例 base/-N 回退，全部 exact 命中）。

**未命中 3/52**（RM 全库无该号目录 → Outcome1 行 + Outcome2 空文件夹，绝不新增行）：

| 全局STT | 发票号 | 处置 |
|---|---|---|
| 176 | HMFZK260264 | 空文件夹 `176-HMFZK260264/`，Outcome1 标「RM-Database 无该号材料」 |
| 180 | HMFZAQ260207 | 空文件夹 `180-HMFZAQ260207/` |
| 203 | HMXCM260008 | 空文件夹 `203-HMXCM260008/` |

> 另有 **193-HMFZAT260062**：目录命中但仅有提单（BL）1 类，缺 SC/Invoice/PL/ToKhai → 计入 ⚠️缺，未勾稽。
> **189-M260004**：命中目录，缺 BL_or_AWB（空运票可能无提单），其余四类齐 → ⚠️缺BL_or_AWB。

## Outcome1 三列填充（不得留空）

- **发票日期（日期列）**：52/52 全部填充（来自 Invoice PDF / ToKhai 兜底），无空白
- **供应商**：52/52 全部填充（L1 供应商列 = HUA FENG GROUP INC.）
- **采购类别**：52/52 全部填充（HS 码 + Invoice 品名交叉验证，全部「原材料」，置信度「高」）
- 「待补」出现 **4** 行：176 / 180 / 203（无目录）+ 193（仅提单）——均有备注留痕，**非空白**

## 未命中处置（不静默丢件）

3 个未命中票号 → Outcome1 保留行 + 备注留痕 + Outcome2 建**空文件夹**（对齐 Outcome1 行数）。剔除/去重清单写入「处理报告」：

- **剔除清单**：非五类件 / 他票件 / NO_MATCH（含说明）
- **去重丢弃清单**：3 件 md5 内容重复（已列明来源目录+文件名）

## 产出与交付

**本地暂存**：`work/loan-materials-2025-12-batch7/p4/out/v2.8d-p4-20261014_1558/`
- `Outcome1-p4-v2.8d-20261014_1558.xlsx`
- `Outcome2-p4-v2.8d-20261014_1558/`（52 文件夹，扁平，无子目录，无 `材料清单.txt`）
- `处理报告-p4-v2.8d-20261014_1558.txt`

**写回 Toshiba**：
- `/Volumes/TOSHIBA EXT/HUATEX进出口材料/Outcome1-p4-v2.8d-20261014_1558.xlsx`（md5 读回一致）
- `/Volumes/TOSHIBA EXT/HUATEX进出口材料/Outcome2-p4-v2.8d-20261014_1558/`（52 文件夹）

**看板静态根 + 公网直链**（实测 HTTP 200 + 字节一致）：
- `https://always-changed-reviews-material.trycloudflare.com/Outcome1-p4-v2.8d-20261014_1558.xlsx`
  - HEAD 200, content-length 10094 = 本地；下载 md5 `c0d19521c06a61d2d828dcf64f55779b` 一致
- `https://always-changed-reviews-material.trycloudflare.com/Outcome2-p4-v2.8d-20261014_1558.zip`
  - HEAD 200, content-length 53424040 = 本地；下载 sha256 `af461a10538aa74aed29eb6f3def5c6cf5b97453cd4a53e320a75ee508dab138` 一致

## 合规

- **未修改 `scripts/` 下任何既有文件**（`md5` 核对 `doc_classify.py` 副本与原件一致）；新增文件全部落在本批目录 `work/loan-materials-2025-12-batch7/p4/scripts/`
  - ⚠️ 观察：本批把 `doc_classify/doc_fields/tokhai_extract` **副本**放入 `p4/scripts/`，运行时 `DC._CACHE_PATH` 解析为**本批**缓存（已用 import 实测确认）。`scripts/.pdftext_cache.json` 于 16:25 被写入（10.07MB→12.03MB），**非本批进程所为** → 系并行兄弟子代理（p1/p2/p3/p5 均存在）在盘上共享缓存所致；`scripts/` 下**无任何代码文件被改动**（find 核验）。
- 铁律遵守：①一切从 L1 出发（只遍历 52 行，未新增行）②打开文件读内容，不看文件名
- 护栏：全程 0 次失败重试，耗时约 30 分钟（主要瓶颈 = 外盘 PDF/OCR 读取 + 4 个兄弟子代理并行 I/O 争用）

## 强制执行记录

- Trace：`memory/subagent_runs/loan-materials-2025-12-batch7-p4/execution_trace.jsonl`（10 条，verify_trace.sh **0 错误**）
- 脚本：`work/loan-materials-2025-12-batch7/p4/scripts/run_p4_v28d.py`（派生自 `scripts/run_loan_2025_12_v28d.py`，未改原件）、`deliver_p4.py`
