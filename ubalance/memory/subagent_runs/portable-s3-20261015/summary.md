# 子代理执行摘要 · portable-s3-20261015（S3 · Web 骨架最小原型）

- **任务**：给两套 workflow 套本地 Web 壳（Payment 核销 / 进出口材料 v2.8d），Windows 单机单人、双击即用、页面上传/下载
- **执行时间**：2026-10-15 11:28–11:55 (Asia/Saigon)，约 **27 分钟**（预算 90 分钟，未超时）
- **工作区**：`/Users/zhaoyuzhao/.openclaw/workspace-balance`
- **模型**：**`deepseek/deepseek-v4-flash`**（本子代理运行模型，如实标注，不虚标）
- **基线（只读）**：`work/payprep-20261013/out/`、`work/loan-materials-2025-12/out/v2.8d-2025_12-20261014_1526/`

---

## 结果总览

| 项 | 结果 |
|---|---|
| **Payment 经 Web 端到端** | ✅ **PASS**：3 份交付件**逐单元格差异 0** |
| **进出口材料经 Web 接入** | ✅ **PASS**：Outcome1 差异 0；Outcome2 **20 目录 / 70 文件** md5 全等 |
| 同一 job 通道驱动两个 workflow | ✅ 同一 `/api/run` 接口 + `workflow` 参数 |
| Web 层依赖 | ✅ **零第三方**——`flask`/`waitress` 未安装（禁装包）→ 用标准库 `http.server` 实现 |
| 服务暴露面 | ✅ 仅 `127.0.0.1:8000`；**测完已停服，无遗留进程** |
| `scripts/` 改动 | ❌ **零改动**（45 个 `.py` 汇总 md5 `ab2921d264c04bc1cddfc5b150d52f40`，前后一致） |
| 写回 Toshiba / 写 `work/` | ❌ 均无（Toshiba 顶层最新仍 10-14；`work/` 今日新增 = 0） |
| API 失败 / 重试 | 0 失败 / 0 重试（全程本地执行，未联网、未装包） |

---

## 对拍读数（核心）

### Payment（job `20261015_114428_payment`，输入 = 10-13 批次明细 + 3 个 voucher zip，`--date 20261013`）

| 交付件 | 基线 vs 新（尺寸） | 逐单元格差异 | 判定 |
|---|---|---|---|
| `Payment request to Bank-20261013.xlsx` | 70×22 / 70×22（Sheet1） | **0** | PASS |
| `Payment recon ledger-20261013.xlsx` | 台账 69×15；差异清单 27×10 | **0** | PASS |
| `Payment 待人工核清单-20261013.xlsx` | 27×12；口径核对 10×6 | **0** | PASS |

* **H 合计 = 12,949,026,506**（基线 = 新）｜ 送银行表 **68 发票行** ｜ 台账 **68 发票行** ｜ 明细 **51 条**（groups：exact 41 / no-invoice 7 / ocr-inaccurate 3）｜ 非 VND 0 ｜ 待人工核 **26 条**
* `Payment request to Bank-20261013.xlsx.recon.txt`：**md5 完全相同**（`054bab47caa6ff3469c7553289da72c1`）
* `.recon.json`：**唯一差异 = `attach` 字段**（基线相对路径 vs 本 job 绝对路径，属运行隔离）
* xlsx 文件 md5 必然不同（`docProps/core.xml` 时间戳）→ 对拍一律**逐单元格取值**

### 进出口材料（job `20261015_114947_loan`，L1 20 条 + `override=config.regression-2025_12.yaml`）

| 项 | 读数 | 判定 |
|---|---|---|
| Outcome1 | **21×13**、差异 **0** | PASS |
| Outcome2（磁盘） | **20 目录 / 70 文件**（含 2 个空目录 `10-HMXCAM250001`、`19-HMFZR250008`） | PASS |
| `Outcome2.zip`（**经 HTTP 下载**） | 20 目录 / 70 文件，与基线**逐文件 md5 全等 70/70** | PASS |
| 处理报告 | 仅 7 行差异 = 时间戳 / 输出路径 / `[CFG]` 元信息；逐票明细正文一致 | 结构级 PASS |

---

## 过程偏差与处置（**不粉饰**）

| # | 现象 | 根因 | 处置 |
|---|---|---|---|
| 1 | Web 跑 Payment 首战直接 `ModuleNotFoundError: summary_text` | S2 只复制 8 个 payprep 脚本，**漏 `summary_text.py`**；S2 回归只覆盖 loan，未暴露 | 从 `scripts/` 1:1 复制（md5 全等） |
| 2 | 修 1 后产出与基线**大面积不一致**（93 单元格差异 / 待人工核 26→43 / 分类列全变「其他（待指定）」） | `gen_payment_recon_v2` 用 `WS/expense_mvp` 定位 `ocr_engine`；便携包内 workflow 深一层 → 引擎**静默不可用**并退化 | `expense_mvp` 最小三模块落到 `portable/expense_mvp/` + 便携副本补 2 行便携根解析（逻辑未改）→ **0 差异** |
| 3 | 「完成」瞬间产物清单偶发缺 `recon ledger` | worker 先翻 `done` 再收产物 → 前端读中间态 | 先收产物再翻状态；终态以磁盘为准 |
| 4 | `Outcome2.zip` 丢 2 个空目录（20→18） | 打包只写文件 | `_zip_dir` 补写空目录条目 |
| 5 | 产物清单重复列出目录 zip | 把刚生成的 `<dir>.zip` 当孤儿文件 | 先算待打包目录，同名 zip 跳过 |

> 全部修复**只动 `portable/`**；Mac 侧 `scripts/` 一行未改。

---

## 交付物

| 交付物 | 路径 |
|---|---|
| Web 骨架 | `portable/app/{server.py,jobs.py,index.html}` |
| 启停脚本 | `portable/start.command` `stop.command` `start.bat` `stop.bat` |
| 待人工核清单生成器（便携版） | `portable/workflows/payprep/manual_review.py` |
| 付款模板 / OCR 引擎最小集 | `portable/templates/` `portable/expense_mvp/` |
| 内容级对拍器 | `portable/tools/compare_xlsx.py` |
| 说明文档 | `deliverables/HUATEX本地部署-S3-Web原型说明-v1-20261015.md` + `.docx` |
| 证据 | `memory/subagent_runs/portable-s3-20261015/evidence/`（见其 `README.md`） |
| Trace | `memory/subagent_runs/portable-s3-20261015/execution_trace.jsonl`（**23 条**） |

---

## 未决 / 建议交 S4

1. **鉴权**：当前仅回环地址、无 token（单人机定位）；多用户机需加 token/白名单。
2. **并发=1** 是设计约束（避免抢数据盘）；多人排队需 S4 排期。
3. **`runs/` 无清理策略**：本次产生 623 MB 留痕，交付前建议裁剪或加「保留最近 N 次」。
4. **页面未提供「模板上传」入口**（Payment 模板目前固定 `portable/templates/`，可在 job 参数覆盖）。
5. `run.months` 跨月范围仍为推断值（S2.1 遗留，待 Daryl 确认 2026_10 实际范围）。
6. `start.bat` / `stop.bat` **在 Windows 上未实测**（本机为 macOS）；已按 CRLF + `chcp 65001` + `py`/`python` 双探测编写，建议在目标机首次落地时留 10 分钟回归。
7. `scripts/` 与 `portable/` 已分叉（S2 起）→ 需定同步纪律（S2 建议「以 portable 为准、Mac 侧不再改」）。

---

## 红线自检证据

| 约束 | 证据 | 结果 |
|---|---|---|
| `scripts/` 一行不改 | 45 个 `.py` 汇总 md5 `ab2921d264c04bc1cddfc5b150d52f40`（前后一致）；`md2docx.py` md5 未变 | ✅ |
| 不写回 Toshiba | `ls -lt "/Volumes/TOSHIBA EXT/HUATEX进出口材料"` 顶层最新 = `Outcome1-v2.8d-ALL262-20261014.xlsx`（10-14 16:33） | ✅ |
| 不写 `work/` 新运行目录 | `find work -newermt "2026-10-15 00:00"` → **0** | ✅ |
| 不对外暴露 | `lsof` → `TCP 127.0.0.1:8000 (LISTEN)`；`--bind` 非回环直接拒启 | ✅ |
| 零外链 | `index.html` 扫描：`http(s)://` 0 / `//` 0 / `script src`·`link href`·`@import`·`url(` 0 | ✅ |
| 测完停服 | `kill` → `lsof` 8000 空、`ps` 无常驻 | ✅ |
| 不跑支付 / 不装包 / 不联网 | 全程本地 `python3`；`pip` 0 次 | ✅ |
| 交付落点 | 仅 `portable/**`、`memory/subagent_runs/portable-s3-20261015/**`、`deliverables/**` | ✅ |

## 模型 / 成本

- 模型：**`deepseek/deepseek-v4-flash`**（如实标注）
- API 失败 0 次 / 重试 0 次；估算成本 **约 $0.45**（≈ 55 次工具调用 + 6 轮全流程运行 + 4 轮对拍）
