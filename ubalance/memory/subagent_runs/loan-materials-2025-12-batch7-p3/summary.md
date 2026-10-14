# 子代理执行摘要 · loan-materials-2025-12-batch7-p3

**任务**：执行「进出口材料自动化处理」workflow（唯一口径 **v2.8d**）—— **批次 p3**（全局 STT **107–158**，52 条）
**执行时间**：2026-10-14 15:55–16:28 (Asia/Saigon)
**运行器（新增，未改 scripts/）**：`work/loan-materials-2025-12-batch7/p3/scripts/run_p3_v28d.py`（派生自 scripts/run_loan_2025_12_v28d.py）+ `deliver_p3.py`
**源盘**：`/Volumes/TOSHIBA EXT/HUATEX进出口材料`（已挂载；`RM-Database` 含 2023/2024/2025/2026）
**RM 搜索范围**：**四年全搜** 2023 + 2024 + 2025 + 2026（本批票号跨 2025+2026，全搜以防漏）
**模型**：deepseek/deepseek-v4-flash（如实标注）

---

## 交付结果（对照任务 10 项返回）

| # | 项 | 结果 |
|---|---|---|
| ① | **命中/未命中（逐票）** | **命中 49 / 未命中 3**。未命中（RM 四年全库无目录）：`HMFZAW260005`(STT117)、`HMFZAW260011`(STT118)、`HMFZAK260243`(STT129)。其余 49 票均 **exact 命中**（base / `-N` 兄弟回退**均未触发**，见处理报告未决问题②③=无） |
| ② | **Outcome1 行数** | **52 行**（+表头）；13 列；**序号列直接取「全局STT」= 107–158 连续**（未重排、未从 1 重编） |
| ③ | **Outcome2 文件夹数** | **52**（= Outcome1 行数）；全部**扁平**（0 个 1/2/3 子目录）；**0 个 `材料清单.txt`**；落盘文件 **240** | 
| ④ | **三列填充情况** | 发票日期 / 供应商 / 采购用途分类 **0 空白**；49 票实填 + 3 未命中票按铁律写 `待补 / 待补 / ⚠️待确认`。分类分布：原材料 48、混合(待拆分) 1、⚠️待确认 3 |
| ⑤ | **未命中处置** | 按铁律「一切从 L1 出发」：保留 Outcome1 行 + 建 **空文件夹**（`117-HMFZAW260005`、`118-HMFZAW260011`、`129-HMFZAK260243`），**绝不新增 L1 外行、绝不删行**；五类标 ⚠️缺全类，ToKhai勾稽 ❌未匹配，金额「待补」 |
| ⑥ | **zip 大小 / 条目数** | `Outcome2-p3-v2.8d-20261014_1557.zip` = **60,588,070 B**；**292 条目**（52 目录条目 + 240 文件）；非 ASCII 条目 **91**，**全部带 UTF-8 标志**（91/91 ✅） |
| ⑦ | **两个公网直链** | 基础 URL：`https://always-changed-reviews-material.trycloudflare.com`（取自 `cf.log`/`.current_tunnel_url`，实测 200 且字节一致）<br>· Outcome1：`.../Outcome1-p3-v2.8d-20261014_1557.xlsx`（HTTP 200，**10,225 B** = 本地一致）<br>· Outcome2：`.../Outcome2-p3-v2.8d-20261014_1557.zip`（HTTP 200，**60,588,070 B** = 本地一致） |
| ⑧ | **trace 绝对路径** | `/Users/zhaoyuzhao/.openclaw/workspace-balance/memory/subagent_runs/loan-materials-2025-12-batch7-p3/execution_trace.jsonl`（13 步） |
| ⑨ | **估算成本** | 约 **$0.4–0.7**（单批：1 次全盘目录索引 + 52 票分类 + 扫描件 OCR 为主；deepseek-v4-flash 单价低，无失败重试） |
| ⑩ | **模型名** | **deepseek/deepseek-v4-flash**（如实） |

---

## 关键数据

- **金额合计**：**1,573,409.48 USD**（49 票；取自 ToKhai「Tổng trị giá hóa đơn」；3 未命中票「待补」）
- **报关日期区间**：2026/04/03 ~ 2026/05/28（跨 2025-12 批次标签，票号实为 2026 系列，四年全搜命中 2026/THÁNG 04–05）
- **五类完整性**：49 命中票中 **40 ✅完整 / 9 ⚠️缺**（详见处理报告「五类完整性汇总」）；缺项多为 SalesConfirmation/PackingList（部分目录本身不含该件，属内容级判定）
- **去重丢弃**：**6 件**（md5 一致），已逐条写入处理报告「去重丢弃清单」（不静默丢件）
- **剔除清单**：ARRIVAL_NOTICE 36 / CUSTOMS_LIST 49 / DELIVERY_ORDER 5 / FREIGHT 30 / OTHER 299 / OTHER_TICKET 12 / TOKHAI_OTHER 46（详见报告）
- **RM 快照**：全库最新 mtime = **2026-10-13**

## 交付物落盘

- work：`work/loan-materials-2025-12-batch7/p3/out/v2.8d-p3-20261014_1557/`
- 回写 Toshiba：`.../HUATEX进出口材料/Outcome1-p3-v2.8d-20261014_1557.xlsx` + `Outcome2-p3-v2.8d-20261014_1557/` + 处理报告（xlsx md5 读回一致；目录文件 240/240）
- 看板：`~/WorkBuddy/Claw/opc-dashboard/Outcome1-p3-v2.8d-20261014_1557.xlsx`、`Outcome2-p3-v2.8d-20261014_1557.zip`

## ⚠️ 需主代理注意（诚实标注，未擅自改引擎）

1. **引擎边缘个案（`doc_classify.py` 既有逻辑，本批未改脚本）**：`122-HMXCAC260357` 目录内含
   - `EDO_202688...pdf`（正文 = 越南语 **GIẤY ỦY QUYỀN GIAO HÀNG**「交货授权单」）→ 应属排除类 **EDO/D.O.**，但被弱兜底按 AWB 收下；
   - `HMXCAC260357 CO draft revised.pdf`（正文 = **CERTIFICATE OF ORIGIN** 原产地证）→ 应属排除类 **CO_CERT**，但被弱兜底按 BL 收下。
   该票五类被标 ⚠️缺 SalesConfirmation/Invoice/PackingList（该目录缺商业单据）。
   **处置建议**：此为既有引擎（v2.8d）在「弱兜底 + 仅首 400 字符判 D/O」下的已知边缘，非本批特有；**按 SOP 口径应收紧**（待 Daryl/主代理确认是否触发 workflow「修改」流程）。
2. **3 张未命中票**（117/118/129）：RM 四年全库无目录。已核 `HMFZAW*` 系列在 RM 中不存在（RM 仅有 HMFZA**G/K/M/N/P/Q/V/X**，无 **W**）；`HMFZAK260243` 在 260233/260250 之间缺号。**疑为 RM 快照未覆盖（L1 已入库、材料未上盘）**，按铁律保留空文件夹。
3. **未改 `scripts/` 任何既有文件**；新增脚本置于本批次目录 `p3/scripts/`。运行期 `doc_classify` 会写共享缓存 `scripts/.pdftext_cache.json`（属运行时数据文件、引擎自带行为，非脚本改动）。

## 自检清单（v2.8d §10）

- [x] Outcome1 行数 = L1 行数 = 52
- [x] Outcome2 文件夹数 = 52 = Outcome1 行数（含 3 空文件夹）
- [x] 文件夹名 = `<全局STT>-<发票号>`（序号与 Outcome1 序号一致）
- [x] 无 `材料清单.txt`
- [x] 每个票号文件夹扁平、无 1/2/3 子目录
- [x] md5 去重生效（丢弃 6 件已留痕）
- [x] 五类齐全判定（缺项显式标 ⚠️）
- [x] Outcome1 三列无空白（缺写「待补」）
- [x] 处理报告含「剔除清单」+「去重丢弃清单」（不静默丢件）
- [x] zip 中文条目全带 UTF-8 标志（91/91）
- [x] 跑前确认 Toshiba 已挂载；写回 md5 读回校验一致
