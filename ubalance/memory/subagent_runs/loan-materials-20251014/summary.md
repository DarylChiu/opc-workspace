# 子代理执行摘要 · loan-materials-20251014（进出口材料自动化处理 v2.8d · L1 首批 20 条）

- **任务**：执行「进出口材料自动化处理」workflow（唯一口径 v2.8d），处理 `L1-成品采购入库补单测试20条.xlsx`（Sheet1，20 行）
- **执行时间**：2026-10-14 15:15–15:35 (Asia/Saigon)
- **工作目录**：`/Users/zhaoyuzhao/.openclaw/workspace-balance`
- **源盘**：`/Volumes/TOSHIBA EXT/HUATEX进出口材料`（已挂载；顶层目录由旧 `HUATEX贷款材料` 改名）
- **RM 搜索范围**：`2025/THÁNG 12` + `2026/THÁNG 01`（跨年，共 271 个票号目录）
- **运行器**：`scripts/run_loan_2025_12_v28d.py`（由 `run_loan_v29_20261013.py` 引擎派生；只做环境修正 + 输入形态改造）

## 结果

| 项 | 结果 |
|---|---|
| L1 行数 | 20 |
| RM 命中 / 未命中 | **18 / 2**（`HMXCAM250001`、`HMFZR250008` 全库无目录） |
| Outcome1 | 13 列 × 20 行（STT 升序），`Outcome1-v2.8d-2025_12-20261014_1526.xlsx` |
| Outcome2 | **20 个文件夹**（= Outcome1 行数），扁平、无 1/2/3 子目录、无 `材料清单.txt`；落盘文件 **70** 个 |
| 空文件夹 | 2 个：`10-HMXCAM250001`、`19-HMFZR250008`（无目录票号，保留空文件夹对齐 Outcome1 行） |
| 三列（发票日期/供应商/采购类别） | **0 空白**；18 票实填，2 票未命中票号按铁律写 `待补 / ⚠️待确认` |
| 五类完整性 | 15/18 ✅完整；`9-HMFZR250007` ⚠️缺 BL_or_AWB（该目录内无提单类文件，唯一疑似 `MV8010KL.pdf` 内容判定为海关集装箱监管清单→排除）；`13-HMXCAR250004` ⚠️缺 SalesConfirmation（明细内仅 invoice+packing）；（未命中 2 票另计） |
| 金额合计 | **518,500.10 USD**（18 票；金额取自 ToKhai「Tổng trị giá hóa đơn」） |
| 报关日期区间 | 2025/12/08 ~ 2026/01/07 |
| 去重丢弃 | 3 件（md5 一致）：`HAWB_731-8451.pdf`、`BIL 131-1.pdf`、`BIL 425.pdf`，已写入处理报告「去重丢弃清单」 |
| 写回 Toshiba | ✅ `Outcome1-v2.8d-2025_12-20261014_1526.xlsx` + `Outcome2-v2.8d-2025_12-20261014_1526/` + 处理报告 + zip（md5 读回一致；目录 20、文件 70 一致） |
| 交付 zip | `HUATEX-Outcome2-v2.8d-2025_12-20261014_1526.zip`，**18.30 MB / 90 条目**（70 文件 + 20 目录条目）；非 ASCII 条目 32 = 带 UTF-8 标志 32 ✅ |
| 公网直链 | 见下，本地 + 隧道均 HTTP 200 且字节数一致 |

## 关键偏差与处置

1. **主代理预核 vs 实际（HMFZR250002）**：预核称「RM 内仅有 `-1` 兄弟目录」→ **脚本独立复核不成立**：`2025/THÁNG 12/70.HMFZR250002 成品 （空运）` 为 base 自有目录；`HMFZR250002-1` 另有 `62.HMFZR250002-1`。两者均 **exact 命中**，**无需 base↔-N 回退**（回退逻辑已实现但本批未触发，见处理报告「未决问题」②③=无）。
2. **实现级修正（非口径变更）**：`doc_fields.extract_invoice_date` 无中文日期模式「2025年12月10日」→ 标签命中后仍回退全文首个 `M/D/Y`（如 `12/17/2025`）被按 `D/M/Y` 解析 → 第 1 次运行产出非法月（`2025/17/12`、`2025/26/12`、`2025/09/12`、`2025/10/12`）。**修正**：`DATE_PAT` 增加最高优先模式 `(\d{4})年(\d{1,2})月(\d{1,2})日`。**口径不变**（发票日期仍取 Invoice Date，优先级不变）。重跑后 4 处非法值全部修正（第 5/7/14/15 行），第 13 行亦由 12/31 修正为 12/30。
3. **跨年票**：`HMFZV250003` 位于 `2026/THÁNG 01/25.`（报关日 2026/01/07），跨年搜索生效。
4. **第 1 次运行作废**：`out/_superseded/v2.8d-2025_12-20261014_1519/`（日期缺陷版，留痕未删）。

## 交付链接（看板隧道）

基础 URL（取自 `~/WorkBuddy/Claw/opc-dashboard/.current_tunnel_url` 且与 `cf.log` 一致）：
`https://always-changed-reviews-material.trycloudflare.com`

- Outcome1：`https://always-changed-reviews-material.trycloudflare.com/Outcome1-v2.8d-2025_12-20261014_1526.xlsx`（7,498 B）
- Outcome2 zip：`https://always-changed-reviews-material.trycloudflare.com/HUATEX-Outcome2-v2.8d-2025_12-20261014_1526.zip`（19,188,099 B）

实测：本地 `http://127.0.0.1:8765/` 与隧道 URL 均 **HTTP 200**，`size_download` 与本地字节数一致。

## 产出路径

- 暂存：`work/loan-materials-2025-12/out/v2.8d-2025_12-20261014_1526/`
- 运行日志：`work/loan-materials-2025-12/out/run_v28d_r2.log`
- Toshiba：`/Volumes/TOSHIBA EXT/HUATEX进出口材料/`（xlsx + 处理报告 + Outcome2 目录 + zip）
- Trace：`memory/subagent_runs/loan-materials-20251014/execution_trace.jsonl`
- 看板副本：`~/WorkBuddy/Claw/opc-dashboard/`（含业务单据 → 对方确认后应删除）

## 模型 / 成本

- 模型：`deepseek/deepseek-v4-flash`（本子代理运行时模型，如实标注）
- 估算成本：约 **$0.35**（≈ 20 次工具调用 + 2 次全量运行 + 2 轮 PDF 解析；无重试风暴，失败重试 0 次）
