---
title: SOP场景-进出口材料自动化处理（Outcome1/Outcome2）
type: card
domain: finance-ops
jurisdiction: VN
owner: Balance
version: v2.8d
updated: 2026-10-05
spec: reports/进出口材料自动化处理-工作流与操作手册.md   # v2.8d 定版（2026-10-05 Daryl 验收；旧名有兼容软链）
scripts: scripts/loan_input.py, scripts/run_loan_2026_0810.py, scripts/gen_outcome2_v2_6.py, scripts/process_v2_6.py, scripts/doc_classify.py, scripts/doc_fields.py, scripts/tokhai_extract.py
tags: [loan-materials, huatex, workflow, ocr]
---

# SOP · 进出口材料自动化处理（速查卡）

> **运行前必读本卡 + 手册**。本卡只记「口径与铁律」，实现细节看手册。

## 零、版本与输入（Daryl 2026-10-05 定）

1. **本项目一律用 v2.8d 口径** —— 凡 Daryl 说执行「进出口材料自动化处理」（旧称「贷款材料自动化整理/处理」），即按 **v2.8d** 跑；更早版本（v2.1→v2.8.0、v2.3 工作流文档）功能重复或落后的**已全部覆盖 / 标记留痕**，不得再作基准。2023 旧运行器不管（不改、也不作基准）。
2. **输入三形式皆合法**：L1 Excel ／ 发票号 txt（可多个）／ 截图。
   - 截图 → 本机 **tesseract**（云多模态不可用）；小图**前缀不可靠** → 用 RM-Database **目录名反向校正**
   - 归一化：`python3 scripts/loan_input.py --in <xlsx|txt|图片> [--rm <RM-Database/2026>]`
3. **不反向索取 L1、不产出 L1**：输入到手即开工；**Outcome1 即取数基准**（三列自行补全，缺则「待补」）。
4. **产出用途**：Outcome 交 **采购部发起请款流程**（项目也因此更名）。
5. 项目名：**进出口材料自动化处理**（旧称「贷款材料自动化整理/处理」，沿用至 2026-10-05）。

## 一、两条铁律

1. **一切从 L1 出发** —— 只遍历 L1 的发票行；RM-Database 只作查找源；**绝不新增 L1 以外的行**（L1 有、RM 无 → 标「无目录」）
2. **打开文件读内容，不看文件名** —— 通关状态 / 报关单勾稽 / Invoice 识别 / 用途分类全部内容级判定

## 二、输出口径

- **Outcome1** = 13 列 Excel（含关单号 / 报关日期 / 金额 / 五类完整性 / ToKhai 勾稽），按 STT 升序
- **Outcome2** = 每票号一个文件夹，**扁平**存放（**不建 1/2/3 分类子目录**）

> **★ v2.8d（2026-10-05 Daryl 定 · 终版交付形态）**
> 1. **Outcome2 文件夹名 = Outcome1 序号前缀 + 发票号**（如 `1-HMXCFZGYAT260042`、`10-HMXCFZK260005`；序号 = Outcome1 的 STT）
> 2. **不再生成 `材料清单.txt`**（票号文件夹里只放材料本身）
> 3. 去重留痕不丢：被丢弃件改写入 **`处理报告`** 的「去重丢弃清单」节（铁则「不静默丢件」仍有效）
> 4. 无材料票号仍建**空文件夹**（如 `3-OP26092401332`）→ Outcome2 文件夹数 = Outcome1 行数
> 5. 交付 zip **必须带 UTF-8 标志**（macOS `zip` 不带 → Windows 中文乱码/丢件；改用 Python `zipfile`）

### ★ v2.8.0 两条硬规则（2026-10-03 Daryl 定，曾犯过）

| # | 规则 | 反面教训 |
|---|---|---|
| **1** | **合订本只存一份**：清关资料 PDF 常是「SC+Invoice+PL 合订本」，**不得**按多标签复制成 3 份塞进 1/2/3 子目录（v2.8d 起连 `材料清单.txt` 也不再生成，覆盖类别看 `处理报告`） | 2026-10-03 我按多标签拷贝 → 同一 PDF 在 3 个子目录重复出现 |
| **2** | **必须去重**：①内容 md5 一致只留一份 ②**归一化文件名**同文档多版本（去 `--已盖章`/`(1)`/尾部空格/`__N`）优先保留带「盖章」者；被丢弃者在 `材料清单.txt` 列明，**不静默丢件** | 提单 `X.pdf` / `X--已盖章.pdf` / `X(1).pdf` 重复堆叠 |

- **递归扫描**：2026 起票号目录下按「胚布/纱线/机织/成品」子目录分装 → 脚本必须递归
- **精准匹配**：业务单据（Inv/SC/PL）须匹配 L1 票号，引用他票的剔除；运输单据未读到票号 → 视为该批次船务共享单据保留
- **ToKhai**：只收**已通关**（状态标题 `(thông quan)`；`thông báo kết quả phân luồng` 分流通知 / `In thử` 草稿不收），并按金额勾稽选中；归属可用 `extract_tokhai` 的 `so_hoa_don`
- **`-N` 兄弟票**：RM 常不为 `X-1` 单建目录 → 回退到 base `X` 的目录

## 三、图片票号（L1）识别

- **OCR 一律用本机 Tesseract**（云多模态不可用）；`--psm 6` 清单 / `--psm 11` 稀疏
- 小图（~200px）**数字可靠、前缀不可靠** → 用 **RM-Database 目录名反向校正**

## 四、Outcome1 字段来源（★ L1 只有票号时怎么补）

> Daryl 2026-10-03 指出：就算只给一张票号图（无 L1），**发票日期 / 供应商 / 采购类别也必须填上**，不能留空。

| 列 | 优先级 1 | 优先级 2（无 L1 时） | 优先级 3（兜底） |
|---|---|---|---|
| 金额(USD) | L1 | ToKhai `Tổng trị giá hóa đơn` | 写「待补」 |
| 报关日期 | L1 | ToKhai `Ngày đăng ký` | 写「待补」 |
| **发票日期** | L1 | **清关资料/Invoice PDF 的 Invoice Date** | ToKhai 报关日期（**标注为兜底**） |
| **供应商** | L1 | **Invoice PDF 的 Seller/Exporter/Beneficiary** | 已知名录扫描（HUA FENG / FUJIAN CYCLONE / SUMEC…） |
| **采购类别** | HS 码（ToKhai `Mã số hàng hóa đại diện`） | Invoice 品名关键词 | 写「⚠️待确认」+ 低置信度 |
| 分类依据 | Invoice 品名 + HS 码**交叉验证**（互证→高 / 仅一源→中/高 / 打架→存疑低） | | |

- 实现：`scripts/doc_fields.py`（`classify_by_hs` / `classify_by_goods` / `cross_validate` /
  `extract_invoice_date` / `extract_supplier` / `fill_fields`）
- 已接入 `process_v2_6.py`（L1 缺字段时自动补）与 `run_loan_2026_0810.py`
- **铁则：拿不到就写「待补」并计入备注，不留空、不静默**



## 五、数据位置与交付

- 源：`/Volumes/TOSHIBA EXT/HUATEX贷款材料/RM-Database/<年>/<THÁNG nn>/`
- 出：直接写回 Toshiba（Daryl 2026-10-03 定），命名沿用 `Outcome1-v2.x-<批次>-<时间戳>`
- ⚠️ **驱动器可能被拔走** → 跑前先确认 `/Volumes/TOSHIBA EXT` 存在，否则会空跑（2026-10-03 踩过）

## 六、自检清单（交付前逐项打勾）

- [ ] 每个票号文件夹**扁平**、无 1/2/3 子目录
- [ ] 文件夹名 = **`<序号>-<发票号>`**（序号与 Outcome1 STT 一致）
- [ ] **无 `材料清单.txt`**（v2.8d 起取消）
- [ ] 同一 PDF 未重复出现（md5 去重生效）；提单无同文档多版本堆叠
- [ ] 五类齐全（缺项显式标 ⚠️）
- [ ] Outcome1 行数 = L1 行数 = Outcome2 文件夹数（含无材料空文件夹）
