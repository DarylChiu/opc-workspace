# HUATEX Tools Windows 交付包 · v1.3.1-20261016 — 重建验收报告

- **任务**：重建 Windows 交付包（修复中文 Windows 两个编码坑），验收、发布、留痕
- **执行**：Balance 子代理（huatex-v1.3.1-package）· 模型 `deepseek/deepseek-v4-flash`
- **时间**：2026-10-16 08:46 → 08:51 (GMT+7)
- **结论**：✅ **全部 PASS**（打包 PASS · 验收 38/38 · 回归差异 0/0/0 · 发布 + 公网实测通过）

---

## 1. 本次修复点（源码由主代理改，本子代理只读）

| # | 坑 | 修复 |
|---|---|---|
| 1 | `requirements.txt` 含中文注释 → pip 以 GBK(cp936) 解码失败（`UnicodeDecodeError: 'gbk' codec can't decode byte 0xac`），7 个依赖装不上（自检 5/12） | requirements.txt 改纯 ASCII + PEP263 coding 行；`一键安装.bat` 第 2 步新增「直接列包名」兜底重试（不读 requirements.txt 亦能装） |
| 2 | 4 个 `.bat` 为 UTF-8 + `chcp 65001` → 中文 Windows(cp936) cmd 误拆行（`The filename, directory name, or volume label syntax is incorrect.` / `'...' is not recognized`） | 改为 **GBK(cp936) 写出 + `chcp 936`**；打包器加硬校验 `_bat_text()`：GBK 不可表示符号自动替换（❌→`[x]`、⚠→`[!]`），仍有不可编码字符则 `SystemExit` 中止打包 |
| 3 | （v1.3 已含）selftest 5/12 打印 `cd /d` + 绝对路径；6/12 新增自定义目录探测 + 限深扫描 |

**源码 md5（本子代理未改动）**
```
portable/config.py                       4d2736bce08c6d05f9baa5ce4f9ae349
portable/tools/preflight_win.py          c556a3db6cfd218f95bc80a3727751fd
portable/tools/build_package.py          6ce0509e546519175662843a3f7f91be
```

---

## 2. 交付物

| 项 | 值 |
|---|---|
| 文件 | `deliverables/HUATEX-Tools-Windows-v1.3.1-20261016.zip` |
| 字节 | **151,999,991**（144.96 MB） |
| sha256 | `92fcee1987caaab455a7ad2e337f1bbb609206de161dd691c4a8787b60940e0a` |
| 条目数 | **81** |
| 清单 | `deliverables/HUATEX-Tools-Windows-v1.3.1-20261016-MANIFEST.txt` |

打包日志要点：dev 树复制保留 33 文件/排除 14 条目；Windows 专属文件内嵌生成 13 个；包内 config.py 定点修正 `PORTABLE_ROOT = HERE`；config.yaml 按 Windows 默认值 5 处定点替换（tesseract_cmd→`C:\Program Files\Tesseract-OCR\tesseract.exe`、output_root→`D:\HUATEX\work` 等）。

---

## 3. 验收数据表（38 项，0 FAIL）

| 检查组 | 检查项 | 期望 | 实测 | 结果 |
|---|---|---|---|---|
| 基础 | zip 字节 | 151999991 | 151999991 | ✅ |
| 基础 | sha256 | `92fcee19…40e0a` | 一致 | ✅ |
| 基础 | 条目数 | 81 | 81 | ✅ |
| 基础 | `testzip()` | None | None | ✅ |
| UTF-8 | 每条目带 0x800 | 81/81 | 81/81，缺 0 | ✅ |
| 素材 | Tesseract 安装器 | 50,175,248 | 50,175,248（逐字节读） | ✅ |
| 素材 | Poppler Release-26.09.0-0.zip | 43,709,956 | 43,709,956 | ✅ |
| 素材 | tessdata eng | 4,113,088 | 4,113,088 | ✅ |
| 素材 | tessdata osd | 10,562,727 | 10,562,727 | ✅ |
| 素材 | tessdata vie | 531,275 | 531,275 | ✅ |
| 素材 | tessdata chi_sim | 2,469,156 | 2,469,156 | ✅ |
| 素材 | wheels/*.whl | 28 个 | 28 个 | ✅ |
| **坑1** | `requirements.txt` `decode('ascii')` | 成功 | 成功（676 B / 14 行） | ✅ |
| **坑2** | 4 × `.bat` cp936 解码 | 全部成功 | 4/4 成功 | ✅ |
| **坑2** | 4 × `.bat` 含 `chcp 936` | 全部 | 4/4 | ✅ |
| **坑2** | 4 × `.bat` 不含 `❌`/`⚠` | 全部 | 4/4 无 | ✅ |
| **坑2** | 非纯 UTF-8 中文（深检） | 是 | UTF-8 严格解码 4/4 失败（@104/@104/@104/@137）；cp936 往返一致；cp936 出真实中文 133/285/105/730 CJK | ✅ |
| 内容 | `tools/preflight.py` 含 `v1.3.1-20261016` | 是 | 是 | ✅ |
| 内容 | `tools/preflight.py` 含 `HUATEX_TESSERACT` | 是 | 是 | ✅ |
| 内容 | `tools/preflight.py` 含 `Tools for Huatex` | 是 | 是 | ✅ |
| 内容 | `config.py` 含 `WIN_TESS_SCAN_ROOTS` | 是 | 是 | ✅ |
| 内容 | `一键安装.bat` 含 `D:\Tools for Huatex\tesseract.exe` | 是 | 是 | ✅ |
| 内容 | `一键安装.bat` 含兜底重试行 | 是 | 是（「requirements.txt 方式失败，改用『直接列包名』重试（v1.3.1 兜底）」） | ✅ |
| 合规 | 客户数据扫描 | 0 命中 | 0 命中 | ✅ |

原始日志：`evidence/verify_checks.log`、`evidence/bat_encoding_deep.log`、`evidence/huatex-v131-verify.json`

---

## 4. 冒烟回归（脱离 dev 树 · 纯 HTTP 驱动）

- 解压到 `/tmp/huatex-v131-test`，**脱离 dev 树**；服务 `127.0.0.1:8000`
- 包内 `tools/preflight.py --selftest` → `rc=3`（12 项中仅 2 项警告：数据文件夹未填、输出根 `D:\HUATEX\work` 盘不存在→回落程序目录；均为 macOS 上的**预期**行为，非缺陷）
- **Payment 核销**（10-13 批次 4 文件：`10-12华特明细待确认.xlsx` + `voucher-a1013.zip` + `voucher-b1013.zip` + `voucher-c1013.zip`，参数 `date=20261013`）
  - job `20261016_084739_payment` · status **done** · elapsed ≈ 29 s
- **对拍基线** `work/payprep-20261013/out`（逐单元格）

| 产出文件 | 差异总数 |
|---|---|
| Payment request to Bank-20261013.xlsx | **0** |
| Payment recon ledger-20261013.xlsx | **0** |
| Payment 待人工核清单-20261013.xlsx | **0** |

**差异 0/0/0** ✅ · `Payment request to Bank-20261013.xlsx.recon.txt` md5：base = new = `054bab47caa6ff3469c7553289da72c1` ✅

- 测后：停服 → `lsof -ti :8000` = **0 占用** ✅
- 临时目录 `/tmp/huatex-v131-test`（含客户数据）已 **trash** 清理（未用 `rm`）✅
- Loan 流程按指令跳过

---

## 5. 发布 + 公网实测

- 发布目录：`~/WorkBuddy/Claw/opc-dashboard/`
  - `HUATEX-Tools-Windows-v1.3.1-20261016.zip`（151,999,991 B，sha256 与 deliverables 一致 ✅）
  - `HUATEX-Tools-Windows-v1.3.1-20261016-MANIFEST.txt`
- 旧版下架：`HUATEX-Tools-Windows-v1.3-20261016.zip` 与 `-MANIFEST.txt` 已 **trash**（其余文件未动）

**公网链接（当前隧道，`cf.log`）**
```
https://phase-partial-renew-juan.trycloudflare.com/HUATEX-Tools-Windows-v1.3.1-20261016.zip
```

| 实测项 | 结果 |
|---|---|
| `curl -sI` | **HTTP/2 200** · `content-type: application/zip` · `content-length: 151999991` · `server: cloudflare` · `cf-ray: a4b3673dafa70f24-HKG` |
| Range 取前 1 MB | 206 · 1.11 s · ~942 KB/s |
| 完整下载 | 200 · size 151,999,991 · **69.69 s** |
| 下载件 sha256 | `92fcee1987caaab455a7ad2e337f1bbb609206de161dd691c4a8787b60940e0a` → **与包一致** ✅ |
| 临时下载文件 | 已 trash ✅ |

---

## 6. 遗留风险 / 备注

1. **Windows 真机复测未在本轮执行**：本轮为 macOS 上的「脱离 dev 树 + 纯 HTTP」回归，证明包自包含性无回归；但两个坑（pip GBK 解码、cmd 拆行）**本质上只在中文 Windows 上才复现**，最终仍需 Daryl 在 Windows 真机跑一遍 `一键安装.bat` + `selftest.bat` 确认「自检 12/12」。
2. **隧道为临时 trycloudflare 地址**：随时可能失效/变更；如需长期链接应改固定域名或 Named Tunnel。
3. `cf.log` 为多次隧道运行叠加输出，含历史行；本次以 `ps` 确认的活跃进程（PID 44644，→ localhost:8765）为准，URL 经 curl 实测有效。
4. 打包器仍会在遇到 GBK 不可表示字符时 `SystemExit` 中止——若后续新增 emoji/特殊符号到 `.bat`，打包会直接失败（这是**设计意图**，非缺陷），须改用 `[x]`/`[!]` 类替代符号。
