# HUATEX Tools Windows 交付包 · v1.3.3-20261016 — 打包验收报告

- **任务**：构建 Windows 交付包 **v1.3.3-20261016**（修复「中文 Windows 默认编码 cp936」这一类 bug），验证、发布、留痕
- **执行**：Balance 子代理（huatex-v1.3.3-package）· 模型 `deepseek/deepseek-v4-flash`
- **时间**：2026-10-16 09:31 → 09:42 (GMT+7)
- **结论**：✅ **全部 PASS**（打包 PASS · 验收 全项 · **模拟 Windows 编码实测 PASS** · 回归差异 0/0/0 + 70/70 · 发布 + 公网实测通过）
- **源码**：本子代理**只读未改**（业务逻辑修改由主代理完成）

---

## 1. 本次修复（对应 Windows 真机 job `20261016_091951_payment` failed 根因）与源码 md5

| # | 修复点 | 位置 |
|---|---|---|
| 1 | `json.load(open(RECON))` **未写 encoding** → 中文 Windows 默认 cp936 读 UTF-8 的含越南语变音符 `.recon.json` → `UnicodeDecodeError: 'gbk' codec` → 退出码非 0 → 任务判 **failed**。改为 `open(RECON, encoding='utf-8')` | `workflows/payprep/manual_review.py` L39 |
| 2 | `_child_env()` 新增 `env['PYTHONUTF8'] = '1'`（子进程强制 UTF-8 模式，系统性消除此类问题） | `app/jobs.py` L369 |
| 3 | `_json.load(open(_CACHE_PATH))` / `_json.dump(..., open(_CACHE_PATH,'w'))` 补 `encoding='utf-8'`（原被 try/except 静默吞掉 → 缓存失效/写坏） | `workflows/loan_materials/doc_classify.py` L69/L76 |
| 4 | 新增**打包硬校验** `lint_text_opens()`（AST 解析，禁止文本模式 `open()` 不带 `encoding=`；命中即 `SystemExit` 中止打包）；VERSION → `v1.3.3-20261016` | `tools/build_package.py` |

**源码 md5（只读，未改动）**
```
portable/workflows/payprep/manual_review.py               bcb38e7560a2cf84d842c30e3c9cfe1b
portable/app/jobs.py                                      741c041da7a154d55a3229e4726e2ddf
portable/workflows/loan_materials/doc_classify.py         88403ae2804975d5df3bc2f6238cb981
portable/tools/build_package.py                           d916a962e5cf132984c4d164f8a3ab70
portable/tools/preflight_win.py                           1be57127d7e8b22fe576eea9fbd2bf6d
portable/config.py                                        4d2736bce08c6d05f9baa5ce4f9ae349
```

---

## 2. 交付物

| 项 | 值 |
|---|---|
| 文件 | `deliverables/HUATEX-Tools-Windows-v1.3.3-20261016.zip` |
| 字节 | **152,005,201**（144.96 MB） |
| sha256 | `43ed833b3e8e821b21f7d9b6b5a7600281f5fc2f470e08fc6e5909d66ef1c0e2` |
| 条目数 | **83** |
| 清单 | `deliverables/HUATEX-Tools-Windows-v1.3.3-20261016-MANIFEST.txt` |

打包日志关键行（`evidence/build.log`）：
```
· 文本 open() 编码校验：PASS ✅ 无裸 open()          ← 本次新增硬校验
· Windows 专属文件内嵌生成：14 个
· 内置素材（S4.2）：6 个文件逐字节校验通过
· wheels：28 个 .whl（47.7 MB）
· 自检扫描（包内客户数据）：PASS ✅ 未发现客户数据
· UTF-8 标志回读校验：83 条目中 0 条缺 0x800 → PASS ✅
```

---

## 3. 验收数据表（0 FAIL）

| 检查组 | 检查项 | 期望 | 实测 | 结果 |
|---|---|---|---|---|
| 基础 | zip 字节 | — | 152,005,201 | ✅ |
| 基础 | sha256 | — | `43ed833b…1c0e2` | ✅ |
| 基础 | 条目数 | — | 83 | ✅ |
| 基础 | `testzip()` | None | **None** | ✅ |
| UTF-8 | 每条目带 0x800 标志 | 83/83 | 缺 **0** 条 | ✅ |
| 素材 | Tesseract 安装器 | 50,175,248 | 50,175,248 | ✅ |
| 素材 | Poppler Release-26.09.0-0.zip | 43,709,956 | 43,709,956 | ✅ |
| 素材 | tessdata eng | 4,113,088 | 4,113,088 | ✅ |
| 素材 | tessdata osd | 10,562,727 | 10,562,727 | ✅ |
| 素材 | tessdata vie | 531,275 | 531,275 | ✅ |
| 素材 | tessdata chi_sim | 2,469,156 | 2,469,156 | ✅ |
| 素材 | wheels/*.whl | 28 | **28** | ✅ |
| 内容 | `requirements.txt` `decode('ascii')` | 成功 | 成功 | ✅ |
| 内容 | 5 个 `.bat` cp936 解码 | 全成功 | 5/5 | ✅ |
| 内容 | 5 个 `.bat` 含 `chcp 936` | 全部 | 5/5 | ✅ |
| 内容 | 5 个 `.bat` 不含 `❌`/`⚠` | 全部 | 5/5 无 | ✅ |
| 内容 | `config.default.yaml` 与 `config.yaml` 逐字节相同 | 相同 | sha256 均 `66e9e09e…20c8e1` | ✅ |
| **修复** | 包内 `workflows/payprep/manual_review.py` 含 `open(RECON, encoding='utf-8')` | 是 | 是 | ✅ |
| **修复** | 包内 `workflows/loan_materials/doc_classify.py` 含 `encoding='utf-8'` | 2 处 | **2** 处 | ✅ |
| **修复** | 包内 `app/jobs.py` 含 `PYTHONUTF8` | 是 | 是 | ✅ |
| 内容 | `tools/preflight.py` 含 `v1.3.3-20261016` | 是 | 是 | ✅ |
| 合规 | 客户数据扫描（83 条目独立复核） | 0 命中 | **0 命中** | ✅ |

原始证据：`evidence/verify_pack.txt`（全量 JSON）、`evidence/customer_data_scan.txt`（83 条目逐条清单 + 关键词扫描）

---

## 4. 模拟 Windows 编码环境实测（本次核心 · PASS）

> 本机 macOS 无 cp936，用 **`locale=US-ASCII`** 作为「默认编码非 UTF-8」的等价代理：
> `env PYTHONUTF8=0 PYTHONCOERCECLOCALE=0 LC_ALL=C` → `locale.getpreferredencoding(False)` = **US-ASCII**
> （即 `open()` 不写 encoding 时按 ASCII 解码 → 与 Windows 上按 cp936 解码属**同一类失败**）

**A) 修复版（包内原样 `workflows/payprep/manual_review.py`）**
```
✅ 待人工核清单已生成: /tmp/mr_fixed.xlsx | 条目: 26
RC_FIXED=0        → 生成 9,896 B xlsx
```

**B) 控制组（同一文件仅把 `open(RECON, encoding='utf-8')` 回退为 `open(RECON)`，放 /tmp 不改包）**
```
UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3 in position 238: ordinal not in range(128)
RC_OLD=1
```
→ 精确复现「默认编码非 UTF-8 时旧写法必崩、修复后正常」的因果链 ✅

**C) 步骤 4b：用包内 `runs/` 自产的 `*.recon.json` 复跑**
```
recon: runs/<job>/out/Payment request to Bank-20261013.xlsx.recon.json（包内自产）
✅ 待人工核清单已生成: /tmp/mr_pkg.xlsx | 条目: 26
RC_PKG_RECON=0    → 生成 9,897 B xlsx
```

> **执行说明（口径偏离）**：交付包 `runs/` 目录只含 `说明.txt`（打包器按设计排除 runs 内容），故「包内 runs 里已有的 `*.recon.json`」在打包时并不存在。处理方式：
> ① 步骤 A/B 用 **10-13 批次真实 `.recon.json`**（`work/payprep-20261013/out/`，含越南语变音符，正是触发 bug 的同类文件）；
> ② 步骤 C 先跑完 Payment 回归，用**本包自己产出的** `recon.json` 再验证一次。两条路径均 PASS。

原文：`evidence/winenc_manual_review.txt`

---

## 5. 冒烟回归（脱离 dev 树 · 纯 HTTP 驱动 · 双流程）

解压到 `/tmp/huatex-v133-test`，**脱离 dev 树**；`python3 app/server.py` → `127.0.0.1:8000`

**Payment 核销**（10-13 批次 4 文件：`10-12华特明细待确认.xlsx` + `voucher-a1013.zip` + `voucher-b1013.zip` + `voucher-c1013.zip`，`date=20261013`）
- job `20261016_093233_payment` · status **done**
- 对拍基线 `work/payprep-20261013/out`（逐单元格，`tools/compare_xlsx.py`）：

| 产出文件 | 差异总数 |
|---|---|
| Payment request to Bank-20261013.xlsx | **0** |
| Payment recon ledger-20261013.xlsx | **0** |
| Payment 待人工核清单-20261013.xlsx | **0** |

**差异 0/0/0** ✅ · `…recon.txt` md5：base = new = `054bab47caa6ff3469c7553289da72c1` ✅

- **`[jobs]` 日志行确认**：服务端改用 `python3 -u app/server.py` 重跑一次（原 `nohup` 为块缓冲，SIGTERM 时 `[jobs]` 行丢失）→ job `20261016_093944_payment` status **done**，服务端日志出现：
  ```
  [jobs] payprep to-bank rc=0 (54.4s)
  [jobs] 待人工核清单 rc=0 (0.3s)      ← 本次修复的直接观测点
  ```

**进出口材料 loan**（2025_12 批次 · `override=config.regression-2025_12.yaml`，沿用 S4.2 跑法）
- job `20261016_093332_loan` · status **done**
- Outcome1：base 21×13 / new 21×13，**差异总数 = 0** ✅
- Outcome2：base 70 文件 / new 70 文件 → **70/70 md5 全等**（仅基线有 0 / 仅新件有 0 / md5 不同 0）✅
- `Outcome2.zip` 通过 `/api/download` 取回 19,186,175 B ✅

**测后收尾**
- 停服 → `lsof -ti :8000` = **0 占用** ✅（两次均 0）
- 临时目录 `/tmp/huatex-v133-test`（含客户数据）、`/tmp/mr_fixed.xlsx`、`/tmp/mr_pkg.xlsx`、`/tmp/old_manual_review.py`、`/tmp/dl_v133.zip`、`/tmp/huatex-pkg-stage` 全部 **trash** 清理 ✅（未用 `rm`）

---

## 6. 发布 + 公网实测

- 发布目录：`~/WorkBuddy/Claw/opc-dashboard/`
  - `HUATEX-Tools-Windows-v1.3.3-20261016.zip`（152,005,201 B，sha256 与 deliverables 一致 ✅）
  - `HUATEX-Tools-Windows-v1.3.3-20261016-MANIFEST.txt`
- 旧版下架：`HUATEX-Tools-Windows-v1.3.2-20261016.zip` 与 `-MANIFEST.txt` 已 **trash**（目录其余文件未动）

**公网链接（当前隧道，`cf.log` / pid 44644 → localhost:8765）**
```
https://phase-partial-renew-juan.trycloudflare.com/HUATEX-Tools-Windows-v1.3.3-20261016.zip
```

| 实测项 | 结果 |
|---|---|
| `curl -sI` | **HTTP/2 200** · `content-type: application/zip` · `content-length: 152005201` · `server: cloudflare` · `cf-ray: a4b3b3aea9977164-HKG` |
| 完整下载 | 200 · size 152,005,201 · **72.1 s**（~2.0 MB/s） |
| 下载件 sha256 | `43ed833b3e8e821b21f7d9b6b5a7600281f5fc2f470e08fc6e5909d66ef1c0e2` → **与包一致** ✅ |
| 临时下载文件 | 已 trash ✅ |

---

## 7. 遗留风险 / 备注

1. **Windows 真机复测未在本轮执行**：本轮为 macOS 上的「脱离 dev 树 + 纯 HTTP + `US-ASCII` 模拟非 UTF-8 默认编码」回归。修复方向已被**正向（rc=0）+ 反向（旧写法 rc=1）**双向验证，但仍建议 Daryl 在 Windows 真机跑 `一键安装.bat` + `selftest.bat`（自检 12/12）并把 job 页面跑通确认。
2. **`PYTHONUTF8=1` 的双保险**：`manual_review.py` 与 `doc_classify.py` 已显式写 encoding，`_child_env()` 又强制子进程 UTF-8 模式，属两层防护；`lint_text_opens()` 在打包期再做静态兜底。
3. **`[jobs]` 日志采集**：`nohup python3 app/server.py` 为块缓冲，SIGTERM 停机时未刷盘的 stdout 会丢失；若后续需长期留痕 `[jobs]`，建议服务端加 `-u` 或日志落文件。本次已用 `-u` 补采。
4. **隧道为临时 trycloudflare 地址**（pid 44644）：随时可能失效/变更。
5. 打包器遇到 GBK 不可表示字符时仍会 `SystemExit` 中止（设计意图，非缺陷）；本次新增的裸 `open()` 校验亦为**硬中止**。

---

## 8. 留痕清单

```
memory/subagent_runs/huatex-v1.3.3-20261016/
├── execution_trace.jsonl      # 22 行，verify_trace.sh PASS（0 error）
├── summary.md                 # 本文件
└── evidence/
    ├── build.log                     # 打包全程（含「文本 open() 编码校验：PASS」）
    ├── verify_pack.py / verify_pack.txt   # 验收脚本 + 全量 JSON 结果
    ├── customer_data_scan.txt        # 83 条目逐条 + 关键词扫描
    ├── winenc_manual_review.txt      # ★ 模拟 Windows 编码实测（修复版 rc=0 / 旧写法 rc=1 / 4b rc=0）
    ├── f_regression_v133.sh / pkg_drive.py / regression.log   # 回归脚本与总日志
    ├── payment_run.log / payment_run2.log / payment_job.json / payment_diff.txt
    ├── payment_diff_pass.txt / payment_recon_txt_md5.txt / payment_mr_rc.txt / payment_status.txt
    ├── loan_run.log / loan_job.json / loan_outcome1_diff.txt / loan_outcome2_compare.txt
    ├── loan_download.txt / loan_status.txt
    ├── api_state.json / page0_save_source_root.txt / pkg_test_preflight.log / pkg_test_server.log
    ├── server_stop.txt / public_head.txt / public_download.txt / MANIFEST.txt
```

> **模型如实标注**：本子代理执行模型 = `deepseek/deepseek-v4-flash`（默认模型，未切换）。
