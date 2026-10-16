# HUATEX Tools Windows 交付包 · v1.3.4-20261016 — 打包验收报告

- **任务**：构建 Windows 交付包 **v1.3.4-20261016**（修复「页面 ⓪ 保存数据文件夹把 config.yaml 写坏」），验证、发布、留痕
- **执行**：Balance 子代理（`huatex-v1.3.4-package`）· 模型 `deepseek/deepseek-v4-flash`
- **时间**：2026-10-16 10:01 → 10:20 (GMT+7)
- **结论**：✅ **全部 PASS**（打包 PASS · 验收全项 · **本场景实测精确复现真机报错并自愈** · 双流程回归 0/0/0 + 70/70 · 发布 + 公网实测通过）
- **源码**：业务逻辑修改由主代理完成，本子代理**未改逻辑**；⚠️ **唯一偏离**见 §0

---

## 0. ⚠️ 与任务书的一处偏离（请主代理复核）

任务书写「源码修改已由主代理完成，只读不写」，但**版本串未提升**：`tools/build_package.py`、`tools/preflight_win.py` 内仍为 `v1.3.3-20261016`（共 11 处），而交付名与验收项均要求 `v1.3.4-20261016`（验收项明列「包内 `preflight.py` 含 `v1.3.4-20261016`」）。

处理：**仅把显示用版本串 `v1.3.3-20261016` → `v1.3.4-20261016` 全局替换**（`build_package.py` 7 处 + `preflight_win.py` 2 处），**业务逻辑、修复代码零改动**。原始文件已备份至 `evidence/build_package.py.prebump-bak` / `evidence/preflight_win.py.prebump-bak`，可一键回退或复核。
> 理由：若版本串不升，Windows 端 `preflight.py --selftest` 会打印「包版本 v1.3.3」，用户可能误判为「旧包/未含修复」而拒绝升级 → 修复不生效。此项为发布工程问题（非业务逻辑），故按交付名要求补齐并**明示留痕**。

---

## 1. 本次修复（Windows 真机「进出口材料」起不来的根因）

真机现象（job 日志）：
```
yaml.scanner.ScannerError: while scanning a double-quoted scalar ...
  found unknown escape character 'T'      (config.yaml line 27)
```
根因：`app/server.py::save_source_root()` 把数据文件夹路径写进 **YAML 双引号**；Windows 路径 `D:\Tools for Huatex\...` 的 `\T` 是非法转义 → 整个 `config.yaml` 解析失败（Payment 流程不读该字段，故不受影响）。

| # | 修复点 | 位置 |
|---|---|---|
| 1 | 写回改**单引号**标量（内部单引号转义为两个 `''`） | `app/server.py` L72/L75 |
| 2 | 新增 `repair_yaml_quotes()` + `load_yaml_tolerant()`；`load()` 失败时自动修复并写回，原文件备份 `.bak` | `config.py` L152/L163 |
| 3 | `_load_yaml()` 改走 `config.load_yaml_tolerant()`（job 不再直接崩） | `app/jobs.py` L246-249 |

**源码 md5（本子代理只读，未改逻辑）**
```
portable/config.py                            39f66709c178c9e01c2ae0a7f4ffaf4f
portable/app/server.py                        2e5a4700304ed60de8713d22b9e5bde5
portable/app/jobs.py                          cfd67fdc34b697294c28ba73fbb9afe9
portable/tools/build_package.py               d916a962e5cf132984c4d164f8a3ab70   (版本串已升 v1.3.4)
portable/tools/preflight_win.py               1be57127d7e8b22fe576eea9fbd2bf6d   (版本串已升 v1.3.4)
portable/workflows/payprep/manual_review.py   bcb38e7560a2cf84d842c30e3c9cfe1b
```

---

## 2. 交付物

| 项 | 值 |
|---|---|
| 文件 | `deliverables/HUATEX-Tools-Windows-v1.3.4-20261016.zip` |
| 字节 | **152,006,308**（144.96 MB） |
| sha256 | `403006b7223f3fad4f38bf2d2b7ded36acdfb8d47d9922ca7e39760ec061990b` |
| 条目数 | **83** |
| 清单 | `deliverables/HUATEX-Tools-Windows-v1.3.4-20261016-MANIFEST.txt` |
| 可重复性 | 二次打包（`/tmp/huatex-rebuild.zip`）sha256 **完全一致** ✅ |

打包日志关键行（`evidence/build.log`）：
```
· Windows 专属文件内嵌生成：14 个
· 内置素材（S4.2）：6 个文件逐字节校验通过
· wheels：28 个 .whl（47.7 MB）
· 文本 open() 编码校验：PASS ✅ 无裸 open()
· zip：83 条目 → 152,006,308 bytes
· zip sha256 = 403006b7…1990b
· 自检扫描（包内客户数据）：PASS ✅ 未发现客户数据
· UTF-8 标志回读校验：83 条目中 0 条缺 0x800 → PASS ✅
```

---

## 3. 验收数据表（**0 FAIL**）

| 检查组 | 检查项 | 期望 | 实测 | 结果 |
|---|---|---|---|---|
| 基础 | zip 字节 | — | 152,006,308 | ✅ |
| 基础 | sha256 | — | `403006b7…1990b` | ✅ |
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
| 内容 | `config.default.yaml` == `config.yaml` 逐字节 | 相同 | **True** | ✅ |
| **修复** | 包内 `app/server.py` 单引号写回 `'{safe}'` | 是 | 是 | ✅ |
| **修复** | 包内 `config.py` 含 `load_yaml_tolerant` | 是 | 是 | ✅ |
| **修复** | 包内 `config.py` 含 `repair_yaml_quotes` | 是 | 是 | ✅ |
| **修复** | 包内 `app/jobs.py` 含 `load_yaml_tolerant` | 是 | 是 | ✅ |
| 内容 | 包内 `tools/preflight.py` 含 `v1.3.4-20261016` | 是 | 是 | ✅ |
| 合规 | 客户数据扫描（83 条目逐条 + 关键词） | 0 命中 | **0 命中** | ✅ |

原始证据：`evidence/zip_verify.json`（全量 JSON）、`evidence/customer_data_scan.txt`（83 条目逐条清单 + 关键词扫描）

---

## 4. 本场景实测（本次核心 · **PASS**）

解压包到 `/tmp/huatex-v134-scenario`，**用包内代码**走真机路径（原文 `evidence/scenario_yaml_fix.txt`）：

**A) 复现真机报错** — 把 `config.yaml` 的 source_root 写成双引号 Windows 路径：
```
line 27: source_root: "D:\Tools for Huatex\HUATEX进出口材料"
裸 yaml.safe_load → ScannerError: while scanning a double-quoted scalar
                    found unknown escape character 'T'   ← 与真机逐字一致（line 27, col 20）
```

**B) 包内 `config.load_yaml_tolerant()` 自愈**：
```
[config] config.yaml 解析失败（ScannerError）→ 已自动修正 1 处「双引号路径→单引号」（原文件已备份为 .bak）
✅ 解析出 source_root = 'D:\Tools for Huatex\HUATEX进出口材料'
✅ 写回行： source_root: 'D:\Tools for Huatex\HUATEX进出口材料'     （单引号）
✅ .bak 保留原双引号行；修复后裸 yaml 可正常解析
```

**C) 包内 `app/server.py::save_source_root()`（目录名**真实含反斜杠**）**：
```
target = '/tmp/.../D:\Tools for Huatex\HUATEX进出口材料'   (存在=True, 含反斜杠=True)
✅ save_source_root -> True
✅ 写回行： source_root: '..../D:\Tools for Huatex\HUATEX进出口材料'   （单引号）
✅ 裸 yaml 可解析 & 往返一致 & 幂等二次 True
```

> 修复前：写双引号 → 整份 `config.yaml` 崩；修复后：**写入即单引号**，且历史已被写坏的文件也能在下次加载时**自动修复并备份**。

---

## 5. 冒烟回归（脱离 dev 树 · 纯 HTTP 驱动 · 双流程）

解压到 `/tmp/huatex-v134-test`，**脱离 dev 树**；`python3 app/server.py` → `127.0.0.1:8000`

**Payment 核销**（10-13 批次 4 文件：`10-12华特明细待确认.xlsx` + `voucher-{a,b,c}1013.zip`，`date=20261013`）
- job `20261016_100436_payment` · status **done**（elapsed 49.6s）
- 对拍基线 `work/payprep-20261013/out`（逐单元格，`portable/tools/compare_xlsx.py`）：

| 产出文件 | 差异总数 |
|---|---|
| Payment request to Bank-20261013.xlsx | **0** |
| Payment recon ledger-20261013.xlsx | **0** |
| Payment 待人工核清单-20261013.xlsx | **0** |

**差异 0/0/0** ✅ · `…recon.txt` md5：base = new = `054bab47caa6ff3469c7553289da72c1` ✅
- **`[jobs]` 日志行确认**：`nohup` 块缓冲会丢 `[jobs]` 行，故以 `python3 -u app/server.py` 重跑（job `20261016_101255_payment` status **done**），服务端日志捕获：
```
[jobs] payprep to-bank rc=0 (51.0s)
[jobs] 待人工核清单 rc=0 (0.3s)      ← 本次修复的直接观测点
```
- 4b) 附：`LC_ALL=C`（非 UTF-8 默认编码）下用**包内自产** `.recon.json` 复跑 v1.3.3 编码修复 → `RC_PKG_RECON=0`（旧修复未被回归破坏）

**进出口材料 loan**（2025_12 批次 · `override=config.regression-2025_12.yaml`）
- job `20261016_100529_loan` · status **done**（elapsed 312.1s）
- Outcome1：base 21×13 / new 21×13，**差异总数 = 0** ✅
- Outcome2：base 70 文件 / new 70 文件 → **70/70 md5 全等**（仅基线有 0 / 仅新件有 0 / md5 不同 0）✅
- `Outcome2.zip` 经 `/api/download` 取回 **19,186,175 B** ✅
- 页面 ⓪ `POST /api/save-source-root` 亦在 HTTP 层跑通（`evidence/page0_save_source_root.txt` → `{"ok": true, ...}`）；保存后包内 `config.yaml` L27 = `source_root: '/Volumes/TOSHIBA EXT/HUATEX进出口材料'`（**单引号**，裸 yaml 可解析）→ `evidence/http_save_root_single_quote.txt`

**测后收尾**
- 停服 → `lsof -ti :8000` = **0 占用** ✅
- 临时目录（含客户数据）`/tmp/huatex-v134-test`、`/tmp/huatex-v134-scenario`、`/tmp/huatex-rebuild.zip`、`/tmp/mr_pkg.xlsx`、`/tmp/dl_v134.zip`、`/tmp/huatex-pkg-stage` 全部 **trash** 清理 ✅（未用 `rm`）

---

## 6. 发布 + 公网实测

- 发布目录：`~/WorkBuddy/Claw/opc-dashboard/`
  - `HUATEX-Tools-Windows-v1.3.4-20261016.zip`（152,006,308 B，sha256 与 deliverables **一致** ✅）
  - `HUATEX-Tools-Windows-v1.3.4-20261016-MANIFEST.txt`
- 旧版下架：`HUATEX-Tools-Windows-v1.3.3-20261016.zip` 与 `-MANIFEST.txt` 已 **trash**（目录其余文件未动；`HUATEX-hotfix-v1.3.3/v1.3.4` 未动）

**公网链接（当前隧道，`cf.log` / pid 44644 → localhost:8765）**
```
https://phase-partial-renew-juan.trycloudflare.com/HUATEX-Tools-Windows-v1.3.4-20261016.zip
```

| 实测项 | 结果 |
|---|---|
| `curl -sI` | **HTTP/2 200** · `content-type: application/zip` · `content-length: 152006308` · `server: cloudflare` · `cf-ray: a4b3e42cebf5858e-HKG` |
| 完整下载 | 200 · size 152,006,308 · **66.4 s**（~2.3 MB/s） |
| 下载件 sha256 | `403006b7223f3fad4f38bf2d2b7ded36acdfb8d47d9922ca7e39760ec061990b` → **与包一致** ✅ |
| 临时下载文件 | 已 trash ✅ |

---

## 7. 遗留风险 / 备注

1. **Windows 真机复测未在本轮执行**：本轮为 macOS 上的「脱离 dev 树 + 纯 HTTP」回归；YAML 修复已按**真机同款输入**（双引号 `D:\...\T`）正向复现 + 自愈验证。仍建议 Daryl 在 Windows 真机跑 `一键安装.bat` + `selftest.bat`，并在页面 ⓪ 保存 `D:\Tools for Huatex\...` 后确认「进出口材料」job 跑通。
2. **版本串偏离**（见 §0）：如需回退，`evidence/*.prebump-bak` 覆盖回 `portable/tools/` 即可（但会导致包内版本显示为 v1.3.3）。
3. **`config.py` DEFAULTS 仍含本机路径** `/Volumes/TOSHIBA EXT/HUATEX进出口材料`（dev 默认值兜底）；包内 `config.yaml` 已把 `source_root` 置空串，Windows 端以页面 ⓪ 填值为准 → 不影响交付，但删除 `config.yaml` 后 DEFAULTS 兜底会给出 macOS 路径（**既有设计，非本次引入**）。
4. 包内注释含 `Daryl 拍板` 等内部人名（`config.yaml` 2 处）——非客户数据，但对外交付略随意，可按需清理（P3 装饰项）。
5. **隧道为临时 trycloudflare 地址**（pid 44644）：随时可能失效/变更。
6. `[jobs]` 日志采集依赖 `python3 -u`（打包器未改服务端缓冲策略）；若需长期留痕建议服务端日志落文件。

---

## 8. 留痕清单

```
memory/subagent_runs/huatex-v1.3.4-20261016/
├── execution_trace.jsonl              # 13 行（verify_trace.sh PASS）
├── summary.md                         # 本文件
└── evidence/
    ├── build.log                              # 打包全程（含「文本 open() 编码校验：PASS」/ 二次打包同 sha）
    ├── verify_zip.py / zip_verify.json        # 验收脚本 + 全量 JSON 结果
    ├── scenario_test.py / scenario_yaml_fix.txt   # ★ 本场景实测（复现 ScannerError → 自愈 → 写回单引号）
    ├── customer_data_scan.txt                 # 83 条目逐条 + 关键词扫描
    ├── f_regression_v134.sh / pkg_drive.py / regression.log  # 回归脚本（HTTP 驱动）与总日志
    ├── payment_run.log / payment_run2.log / payment_job.json / payment_diff.txt
    ├── payment_diff_pass.txt / payment_recon_txt_md5.txt / payment_mr_rc.txt / payment_status.txt
    ├── loan_run.log / loan_job.json / loan_outcome1_diff.txt / loan_outcome2_compare.txt
    ├── loan_download.txt / loan_status.txt
    ├── http_save_root_single_quote.txt          # 页面 ⓪ 经真实 HTTP 保存后，config.yaml 写成单引号
    ├── api_state.json / page0_save_source_root.txt / pkg_test_server.log / pkg_test_server_u.log
    ├── server_stop.txt / public_head.txt / public_download.txt
    └── build_package.py.prebump-bak / preflight_win.py.prebump-bak   # 版本串改动前原始文件
```

> **模型如实标注**：本子代理执行模型 = `deepseek/deepseek-v4-flash`（默认模型，未切换）。
