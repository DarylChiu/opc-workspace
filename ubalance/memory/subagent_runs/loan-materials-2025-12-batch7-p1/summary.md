# loan-materials-2025-12-batch7 · p1 · 执行摘要

- **批次**：进出口材料自动化处理 v2.8d · batch7 · **p1**（全局 STT 1–53）
- **L1**：`work/loan-materials-2025-12-batch7/split/L1-p1.xlsx`（53 行，全局STT 1–53，供应商列已含 HUA FENG GROUP INC.）
- **时间戳**：20261014_1558
- **模型**：deepseek/deepseek-v4-flash（如实标注）
- **硬约束遵守**：未修改 `scripts/` 下任何既有文件；本批所需运行器/模块/缓存/索引**全部为本批次新增副本**，落在 `work/loan-materials-2025-12-batch7/p1/scripts/`

## 结果
| 项 | 值 |
|---|---|
| 命中 / 未命中 | **52 / 1** |
| 未命中票号 | `HMXCFZA260011`（全局 STT 49）→ 全库四年无该号 → Outcome2 建**空文件夹** `49-HMXCFZA260011`；备注「疑似近号 HMXCFZAT260011（2026/THÁNG 01）非精确 token 匹配，待人工复核」 |
| Outcome1 | **53 行 × 13 列**，STT 直接取「全局STT」(1–53，未重排) |
| 三列（发票日期/供应商/采购类别） | **无空白**；STT49 日期/金额「待补」；STT48(HMFZAG260006) 无 ToKhai→金额「待补」 |
| Outcome2 | **53 个文件夹**，**扁平**（无 1/2/3 子目录），**无 `材料清单.txt`**；仅 49 为空文件夹 |
| 复制文件数（已去重） | 236（md5 完全相同丢弃 11 件，逐条写入处理报告「去重丢弃清单」） |
| 五类完整性 | 51/53 ✅完整；STT48 ⚠️缺ToKhai；STT49 无材料 |
| ToKhai 勾稽 | 51/53 ✅金额已核对；2 票 ❌未匹配(STT48/49) |

## RM 搜索范围
四年全搜（2023/2024/2025/2026），共 **2342** 个目录（预建索引 `p1/scripts/rm_dir_index.json` 复用，避免反复全盘扫描）。
本批实际命中来源：**2026/THÁNG 01（18 票）、02（26 票）、03（2 票）、04（3 票）**；2025/THÁNG 12 无命中。
RM 快照（数据截止）：全库最新目录 mtime = **2026-10-13**。

## 交付
- **Toshiba 回写**（`/Volumes/TOSHIBA EXT/HUATEX进出口材料/`）：
  - `Outcome1-p1-v2.8d-20261014_1558.xlsx`（md5 读回一致 `33f7eb29...`）
  - `Outcome2-p1-v2.8d-20261014_1558/`（236 文件）
  - `处理报告-p1-v2.8d-20261014_1558.txt`
- **zip（Python `zipfile`，UTF-8 标志）**：`Outcome2-p1-v2.8d-20261014_1558.zip`
  - **63,325,542 字节 / 237 条目（236 文件 + 1 空目录）**；非 ASCII 106 条，缺 UTF-8 标志 **0**
- **看板静态根** `~/WorkBuddy/Claw/opc-dashboard/`，隧道 `https://always-changed-reviews-material.trycloudflare.com`
  - `https://always-changed-reviews-material.trycloudflare.com/Outcome1-p1-v2.8d-20261014_1558.xlsx` → **HTTP 200 / 10,283 B**（=本地字节）
  - `https://always-changed-reviews-material.trycloudflare.com/Outcome2-p1-v2.8d-20261014_1558.zip` → **HTTP 200 / 63,325,542 B**（=本地字节）

## 技术说明
- pdftext 缓存迁移：旧路径 `HUATEX贷款材料/`→`HUATEX进出口材料/` 键改写（抽样 200/200 文件 mtime+size 一致），显著降低重跑 OCR 成本。
- 全程按 v2.8d 铁律：一切从 L1 出发（不新增行）、打开文件读内容（不看文件名）。
- 失败重试：0 次（一次跑通）。

## 估算成本
约 **$0.15–0.35**（deepseek-v4-flash；主要为多轮工具调用 + 一次 28 分钟含 OCR 的运行器执行，未含硬盘 I/O 的本地算力成本）。
