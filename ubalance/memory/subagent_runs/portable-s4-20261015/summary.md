# 子代理执行摘要 · portable-s4-20261015（S4 · Windows 交付打磨 + 打包）

- **任务**：把 S3 的 `portable/` Web 原型打成**一个能拷到 Windows 直接双击跑的 zip**，交给 Daryl 做 Windows 实测
- **执行时段**：2026-10-15 13:06–13:28 (Asia/Saigon)，约 **22 分钟**（预算 90 分钟，未超时）
- **工作区**：`/Users/zhaoyuzhao/.openclaw/workspace-balance`
- **模型**：**`deepseek/deepseek-v4-flash`**（本子代理运行模型，如实标注，不虚标）
- **基线（只读）**：`work/payprep-20261013/out/`、`work/loan-materials-2025-12/out/v2.8d-2025_12-20261014_1526/`

---

## 1. 交付物

| 交付物 | 路径 | 读数 |
|---|---|---|
| **Windows 交付包** | `deliverables/HUATEX-Tools-Windows-v1-20261015.zip` | **196,001 B（0.19 MB）**，45 个文件 |
| 包 sha256 | 同上 | `ba15d96e1546deb1c92339d90ca163cb61a32e8ddab6197406d3a5e5f0ec277d` |
| 内容清单（逐文件 sha256） | `deliverables/HUATEX-Tools-Windows-v1-20261015-MANIFEST.txt` | 9,038 B |
| 打包器 | `portable/tools/build_package.py` | 幂等（同输入同 sha256）、打包后自动扫客户数据 |
| 包内文档 | `README-先读我.md` / `手册-徒弟操作.md` / `自查表-常见报错.md`（22 条）/ `安装清单-Windows.md` / `requirements.txt` | 均随包 |
| 包内脚本 | `start.bat` / `stop.bat` / `selftest.bat` / `tools/preflight.py` | CRLF + chcp 65001 + py/python 双探测 |
| S4 说明 | `deliverables/HUATEX本地部署-S4-交付包说明-v1-20261015.md` + `.docx` | 83 段 / 12 表 |
| Trace | `memory/subagent_runs/portable-s4-20261015/execution_trace.jsonl` | 18 条，时间戳单调递增 |

---

## 2. 包自包含性实测（核心验收，**脱离 dev 树**）

方法：zip 解压到 `/tmp/huatex-pkg-test/` → 起服务 → **纯 HTTP**（`/api/save-source-root`→`/api/upload`→`/api/run`→`/api/job`→`/api/download`，与页面同款接口）→ 与只读基线对拍；驱动 = `evidence/pkg_drive.py`。

### 2.1 Payment（job `20261015_131421_payment`，耗时 46.0s）

| 交付件 | 尺寸（基线 / 包内） | 逐单元格差异 | 判定 |
|---|---|---|---|
| `Payment request to Bank-20261013.xlsx` | 70×22 / 70×22 | **0** | ✅ PASS |
| `Payment recon ledger-20261013.xlsx` | 台账 69×15；差异清单 27×10 | **0** | ✅ PASS |
| `Payment 待人工核清单-20261013.xlsx` | 27×12；口径核对 10×6 | **0** | ✅ PASS |

- **H 合计 = 12,949,026,506** ｜ **68 发票行** ｜ 待人工核 **26 条**（与基线一致）
- `…recon.txt` md5 `054bab47caa6ff3469c7553289da72c1` **全等**
- OCR 降级警告 **0 条**

### 2.2 进出口材料（job `20261015_131522_loan`，耗时 281.5s）

| 项 | 读数 | 判定 |
|---|---|---|
| `Outcome1` | **21×13、差异 0** | ✅ PASS |
| `Outcome2.zip`（页面 ④ HTTP 下载） | **70/70 文件 md5 全等**；空目录 2 个一致（`10-HMXCAM250001`、`19-HMFZR250008`）；19,186,175 B | ✅ PASS |
| 文件名集合 | 70 = 70，无多无少 | ✅ PASS |
| `处理报告` | 仅时间戳/输出路径/`[CFG]` 元信息行差异 | ✅ 结构级 PASS |

> override 用**临时复制**到 `/tmp/huatex-pkg-test/` 的文件（绝对路径传入），包不依赖 dev 树路径。

---

## 3. 排除清单（实际执行；写死在打包器 `EXCLUDE_*` 常量）

`runs/**`（含客户 PDF 与 470MB 留痕）｜`in/**`、`out/**`、`evidence/**`｜`**/__pycache__/**`、`*.pyc`、`*.pyo`｜`**/.pdftext_cache.json`、`.DS_Store`、`*.log`、`*.tmp`、`~$*`｜`config.regression-*.yaml`｜`start.command`、`stop.command`｜散落 `*.zip`｜`tools/build_package.py`

- 本次实际排除 **10 条**（5 个 `__pycache__`、`runs/`、2 个 `.command`、回归配置、`.pdftext_cache.json`、打包器本身）
- **保留的例外**：`runs/说明.txt`、`work/说明.txt`（占位说明）、`workflows/expense_mvp/`（§4.2 自包含修正）—— 均在 MANIFEST 注明
- **包内唯一表格文件** = `templates/Payment核销-模板.xlsx`；打包后扫描：**无 pdf/图片/客户 xlsx/runs 留痕/回归配置** ✅

---

## 4. 实测暴露并修复的两个**真缺陷**（S3 未发现）

| # | 缺陷 | 后果 | 修复（**dev 树脚本零改动**） |
|---|---|---|---|
| 1 | `config.py` 便携根启发式依赖目录名 `portable` → 交付包（`HUATEX-Tools`）下 `runs/`、`work/` 落到**包外上一级** | 留痕/输出位置不符合设计，可能写到盘根 | 打包器定点改**包内** `config.py` 1 行：`PORTABLE_ROOT = HERE` |
| 2 | **Payment OCR 引擎在包内找不到** → `[warn] OCR 引擎不可用` 静默降级 | 待人工核 26→**43**、差异清单 27→**33**、分类列劣化，**产出全错但不报错** | 包内补 `workflows/expense_mvp/`（逐字节复制）+ **解析预检**（不通过则打包中止）；重跑回到 **0 差异** |

> 根因说明：S3 的 Payment 验证之所以"通过"，是因为引擎备用候选恰好落在**开发树** `workspace-balance/expense_mvp` —— 属自包含漏洞。**不做 §2 这一步，Windows 上会拿到"能跑但结果错"的包。**

---

## 5. Windows 待实测清单（本机 macOS，**无法验证**，必须真机确认）

1. `start.bat` 双探测 + 起服务 + 自动开浏览器 ｜ 2. `chcp 65001` 中文不乱码 ｜ 3. `selftest.bat` 10 项输出正常
4. 7 依赖 + Poppler（`pdf2image`）在真机可达 ｜ 5. Tesseract + `vie/eng/chi_sim` 语言包 ｜ 6. **输出根回落**（无 D 盘 → `work\`）
7. **YAML 引号坑**（填 `D:\HUATEX` → 自检自动修单引号）｜ 8. 端口占用自动 +1 ｜ 9. 越南语变音目录名可读
10. 杀毒/Defender 不拦截 ｜ 11. `stop.bat` 收工（taskkill /T /F）｜ 12. 260 字符长路径 ｜ 13. 真机重跑 Payment 与 10-13 基线对拍（期望 0 差异 / H=12,949,026,506 / 68 行）

---

## 6. 过程偏差（不粉饰）

| # | 现象 | 处置 |
|---|---|---|
| 1 | 首版打包把 `runs/说明.txt` 占位件误判为"runs 留痕" | 扫描加占位白名单 |
| 2 | 首版把 `tools/build_package.py` 打进包 | 加入排除清单 |
| 3 | 临时目录删不掉（`Operation not permitted`） | 包内产出继承了源文件的 macOS `uchg`(immutable) 标志（`copy2` 保留）→ `chflags -R nouchg` 后清理；**Windows 无此概念，不影响交付** |
| 4 | 8000 端口被上一轮遗留服务占用（首轮复现时跑到 8001） | 按 pid 清理后重跑；端口 +1 兜底逻辑顺带得到验证 |
| 5 | trace 第 15 条出现一个错别字（`loан`） | 已就地修正，时间戳未变（仍单调递增） |

---

## 7. 红线自检

| 约束 | 证据 | 结果 |
|---|---|---|
| `scripts/` 一行未改 | 45 `.py` 汇总 md5 `ab2921d264c04bc1cddfc5b150d52f40`（前后一致，同 S3）；`md2docx.py` md5 `ce75c32f7922509c54737e1aa7e97f6f` 未变 | ✅ |
| dev 树 `portable/` 仅新增 1 个文件 | `find portable -newermt 12:50` → 仅 `tools/build_package.py`；`portable/config.yaml` 仍为 Mac 现值、无 Windows 横幅 | ✅ |
| 不写 Toshiba | 顶层最新 = `Outcome1-v2.8d-ALL262-20261014.xlsx`（10-14 16:33） | ✅ |
| dev 树 `work/` 不新增运行目录 | `find work -newermt "2026-10-15 12:35"` → **0** | ✅ |
| 包内无客户数据 | 打包器自动扫描 PASS + zip 独立复核（无 pdf/图片/客户 xlsx/runs 留痕/回归配置） | ✅ |
| 不对外发布 | 落点仅 `deliverables/`、`memory/subagent_runs/portable-s4-20261015/`、`portable/tools/build_package.py` | ✅ |
| 不联网安装 / 不跑支付 | 全程本地 `python3`；`pip` 0 次 | ✅ |
| 不声称 Windows 已实测 | 说明文档 §7/§9/§10.1 明确标注 | ✅ |
| 测完停服 + 清临时目录 | `lsof :8000` 空；`/tmp/huatex*` 已清空（evidence 已留档 22 份） | ✅ |

---

## 8. 模型 / 成本

- 模型：**`deepseek/deepseek-v4-flash`**（如实标注，不虚标）
- API 失败 0 次 / 重试 0 次；本地流程运行 3 次（Payment ×2、Loan ×1）+ 打包 9 次（含 3 轮幂等复验）
- 耗时：约 **22 分钟**（预算 90 分钟）
