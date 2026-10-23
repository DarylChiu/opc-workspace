# HUATEX Tools Windows 交付包 v1.3.6-20261023 — 打包验收 + 端到端回归

- **执行**：Balance 子代理 `huatex-v136-build`
- **时间**：2026-10-23 11:42 → 11:52 (+07)
- **被测对象**：`deliverables/HUATEX-Tools-Windows-v1.3.6-20261023.zip`（打包产物本身，非 dev 树）

---

## 1. 交付物

| 项 | 值 |
|---|---|
| ZIP 路径 | `deliverables/HUATEX-Tools-Windows-v1.3.6-20261023.zip` |
| 大小 | 152,007,965 bytes（144.97 MB） |
| SHA256 | `a027e1610d184a0d5949b23e16e357583761871320c87cd9a7e3ab04376260fd` |
| MANIFEST | `deliverables/HUATEX-Tools-Windows-v1.3.6-20261023-MANIFEST.txt` |
| 包内文件数 | 83 |
| 解压后总字节 | 162,108,558 |

## 2. 包内验收 5 项

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1 | `workflows/loan_materials/doc_classify.py` 含 `def excel_doc_tags` / `def excel_text`，Excel 分支调用 `excel_doc_tags(fp)` | **PASS** | 行 230 / 258 / 310；`python3 -m py_compile` 通过 |
| 2 | 包内无 `.pdf` / 客户 xlsx / 图片 / `runs` 留痕 | **PASS** | 全包仅 1 个 xlsx = `templates/Payment核销-模板.xlsx`（实测仅 1 行表头，0 数据行，空白模板）；pdf/图片 0 个；`runs/`、`work/` 仅各 1 个 `说明.txt` |
| 3 | 包内 `tools/preflight.py` 版本串 = `v1.3.6-20261023` | **PASS** | 行 477、585 均为 `v1.3.6-20261023` |
| 4 | MANIFEST 文件数 / sha256 与解压后实际一致 | **PASS** | 83/83 文件逐字节 sha256 + size 全匹配，文件集合 diff 为空 |
| 5 | 打包器自校验 | **PASS** | 「未发现客户数据」PASS；「文本 open() 无裸编码」PASS；UTF-8 标志 83/83 无缺失 |

> 说明：初次解压实测 84 个文件，多出的 1 个是我自己跑 `py_compile` 产生的 `__pycache__/doc_classify.cpython-314.pyc`；删除后 83 个 / 162,108,558 B，与 MANIFEST 完全一致。**包本身无冗余文件。**

## 3. 端到端回归（在打包产物上跑）

- 方式：解压包 → 起包内 `app/server.py`（127.0.0.1:8000）→ 纯 HTTP 驱动（`pkg_drive.py`：`/api/save-source-root` → `/api/upload` → `/api/run` → 轮询 `/api/job` → `/api/download`），**不碰 dev 树、不走 CLI**
- 输入：`work/loan-materials-2025-12/in/L1-成品采购入库补单测试20条.xlsx`（只读）
- 口径：`config.regression-2025_12.yaml`（override，回 2025_12 基线口径），source_root = `/Volumes/TOSHIBA EXT/HUATEX进出口材料`（只读）
- 结果：`status=done`，**341.2 秒**
- 产出目录：`/tmp/hv136/unzip/HUATEX-Tools/runs/20261023_114427_loan/out/20261023_1144/`
  - `Outcome1-v2.8d-2025_12-20261023_1144.xlsx` (7,493 B)
  - `Outcome2.zip` (25,552,063 B) / `Outcome2/` 20 票
  - `处理报告-v2.8d-2025_12-20261023_1144.txt` (27,199 B)

### 3.1 硬验收：Outcome2 每票 PDF + Excel 成对

| 指标 | 要求 | 实测 | 判定 |
|---|---|---|---|
| 同时含 `清关资料中英文明细.pdf` **和** `.xlsx/.xlsm` 的票数 | ≥15 | **18** | **PASS** |
| 只缺一边的票 | 0 | **0** | **PASS** |
| 空票（源盘无目录） | 2 | **2**（`10-HMXCAM250001`、`19-HMFZR250008`） | **PASS** |
| 总票数 | 20 | 20 | — |

逐票文件清单见 `evidence/loan_outcome2_pairs.txt`。

### 3.2 防串票核查（v2.8e 的 Excel 票号归属）

18 票的 Excel 版文件名**全部**含本票票号，**归属异常 = 0**。兄弟票场景已实测对上：

- `14-HMFZR250001-3` → `HMFZR250001-3 305件…xlsx`
- `15-HMFZR250002-1` → `HMFZR250002-1 131件…xlsx`
- `16-HMFZR250003-1` → `HMFZR250003-1 80件…xlsx`

（即 run_loan_2025_12_v28d.py 改读工作表文本后，未出现 -1/-3 串票。清单见 `evidence/loan_ticket_attribution.txt`。）

### 3.3 Excel 内容真伪抽检（确认不是随便抓的杂表）

用**包内** `doc_classify` 回测 3 票的 Excel 版：

| 票 | 文件 | `excel_doc_tags()` | 工作表 |
|---|---|---|---|
| 2-NHFMYV250158 | `…清关资料中英文明细.xlsm` | INVOICE / PACKING_LIST / SALES_CONTRACT | 合同 / 发票 / 装箱 / 明细 |
| 14-HMFZR250001-3 | `…清关资料中英文明细.xlsx` | INVOICE / PACKING_LIST / SALES_CONTRACT | 合同 / 发票 / 装箱 / 明细 |
| 20-HMFZV250003 | `…清关资料中英文明细.xlsm` | INVOICE / PACKING_LIST / SALES_CONTRACT | 合同 / 发票 / 装箱 / 明细 |

即「合同(SC) + 发票(INV) + 装箱(PL)」三表齐全，符合 v2.8e 设计语义。

### 3.4 Outcome1 与 10-14 基线对拍

```
差异总数 = 1
  ✗ Outcome1!R14C11: base='⚠️缺SalesConfirmation'  new='✅完整'
```

**这是 v1.3.6 的预期改善**，不是回归：该票的 Sales Confirmation 原本只存在于 Excel 版（PDF 里没有），v1.3.4 判为「缺 SC」，v1.3.6 识别 Excel 版 SC 后判为「完整」。其余 20×13 单元格完全一致。

## 4. 包内自检（`tools/preflight.py --selftest`）

rc=3（有警告），**无 ❌ 项**，12/12 检查通过。警告全部是 macOS 运行环境的必然差异，与包质量无关：

- `[6/12]` `tesseract_cmd` 指向 Windows 路径 `C:\Program Files\Tesseract-OCR\tesseract.exe` → 已自动探测改用 `/opt/homebrew/bin/tesseract`，vie/eng/chi_sim 齐全
- `[8/12]` `TESSDATA_PREFIX` 未设置（Windows 由 `一键安装.bat` 接上，包内 tessdata 4 个语言包齐全）
- `[11/12]` 自检时 source_root 尚未填写（随后经页面 ⓪ 写入成功）

包内 7/7 内置素材、28 个 wheel、Poppler/Tesseract 安装器字节数全部校验通过。

## 5. 结论

**v1.3.6-20261023 打包验收 5/5 PASS，端到端回归 PASS。** 可外发。

- 核心变更（Excel 版 SC+INV+PL 进 Outcome2）在**打包产物**上实测生效：18/18 有料票均成对，0 半对，0 串票
- Outcome1 仅 1 处改善性差异（R14C11），无退化

## 6. 证据清单（`memory/subagent_runs/huatex-v1.3.6-20261023/evidence/`）

| 文件 | 内容 |
|---|---|
| `f_regression_v136.sh` | 回归脚本全文（可复跑） |
| `regression.log` | 回归全程日志 |
| `pkg_test_preflight.log` | 包内自检 12 项输出 |
| `api_state.json` | 服务 `/api/state` |
| `page0_save_source_root.txt` | 页面 ⓪ 写 source_root 返回 |
| `loan_run.log` | 逐票处理明细 + artifacts |
| `loan_status.txt` | `done` |
| `loan_out_dir.txt` | 产出目录绝对路径 |
| `loan_outcome1_diff.txt` | Outcome1 对拍结果 |
| `loan_outcome2_pairs.txt` | **逐票文件清单 + 成对统计** |
| `loan_ticket_attribution.txt` | **逐票防串票核查** |
| `loan_download.txt` | Outcome2.zip 下载回读 |
| `pkg_test_server.log` | 包内 server 日志 |
| `server_stop.txt` | 收尾（0 listeners） |
