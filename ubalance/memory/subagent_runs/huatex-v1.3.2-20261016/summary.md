# HUATEX Tools Windows 交付包 · v1.3.2-20261016 — 打包验收报告

- **任务**：构建 Windows 交付包 **v1.3.2-20261016**（新增 `config.default.yaml` + `恢复配置.bat` + preflight `--restore-config` 自愈能力），验证、发布、留痕
- **执行**：Balance 子代理（huatex-v1.3.2-package）· 模型 `deepseek/deepseek-v4-flash`
- **时间**：2026-10-16 08:55 → 09:01 (GMT+7)
- **结论**：✅ **全部 PASS**（打包 PASS · 验收 全项 · 自愈实测 PASS · 回归差异 0/0/0 · 发布 + 公网实测通过）

---

## 1. 本次新增（v1.3.2）与源码 md5（本子代理只读，未改任何源码）

| # | 新增 |
|---|---|
| 1 | 包内新增 **`config.default.yaml`** = 包内 `config.yaml`（Windows 定稿版）的逐字节副本，由 `build_package.py` 在 `write_windows_config()` 之后自动复制 |
| 2 | 包内新增 **`恢复配置.bat`**（GBK/cp936 编码）→ 调 `python tools\preflight.py --restore-config` |
| 3 | `tools/preflight.py` 新增 **`--restore-config`**：`config.default.yaml` → `config.yaml`，损坏件另存 `config.yaml.broken-<时间戳>`；`[3/12]` 解析失败时新增**乱码诊断**（`looks_mojibake()`，命中 `搴/鍙/鎿` 类乱码或 U+FFFD）并提示双击 `恢复配置.bat` |
| 4 | 文档补「不要用 PowerShell 改 config.yaml / 用恢复配置.bat」说明；VERSION → `v1.3.2-20261016` |

**源码 md5（只读，未改动）**
```
portable/config.py                       4d2736bce08c6d05f9baa5ce4f9ae349
portable/tools/preflight_win.py          a3cca961f0d2bfca6e18ee045aab96f6
portable/tools/build_package.py          6d929b1a788d52700201d8e9b11bb994
```

---

## 2. 交付物

| 项 | 值 |
|---|---|
| 文件 | `deliverables/HUATEX-Tools-Windows-v1.3.2-20261016.zip` |
| 字节 | **152,004,902**（144.96 MB） |
| sha256 | `9cbd4a4df99ff321e358ee7dbf96e377edc553b6290aecb19e88f8629e3ddf97` |
| 条目数 | **83** |
| 清单 | `deliverables/HUATEX-Tools-Windows-v1.3.2-20261016-MANIFEST.txt` |

打包日志要点：dev 树复制保留 33 文件 / 排除 14 条目；Windows 专属文件内嵌生成 **14 个**（新增 `恢复配置.bat`）；**新增「包内原版配置备份：config.default.yaml」**；包内 config.py 定点修正 `PORTABLE_ROOT = HERE`；6 内置素材逐字节校验通过；28 wheels。

---

## 3. 验收数据表（0 FAIL）

| 检查组 | 检查项 | 期望 | 实测 | 结果 |
|---|---|---|---|---|
| 基础 | zip 字节 | — | 152,004,902 | ✅ |
| 基础 | sha256 | — | `9cbd4a4d…3ddf97` | ✅ |
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
| **新增** | **5 个 `.bat`（一键安装/start/stop/selftest/恢复配置）cp936 解码** | 全成功 | 5/5 | ✅ |
| **新增** | 5 个 `.bat` 含 `chcp 936` | 全部 | 5/5 | ✅ |
| **新增** | 5 个 `.bat` 不含 `❌`/`⚠` | 全部 | 5/5 无 | ✅ |
| **新增** | `恢复配置.bat` 含 `--restore-config` | 是 | 是 | ✅ |
| **新增** | **`config.default.yaml` 与包内 `config.yaml` 逐字节相同** | 相同 | sha256 均 `66e9e09e…20c8e1` | ✅ |
| 内容 | `tools/preflight.py` 含 `v1.3.2-20261016` | 是 | 是 | ✅ |
| 内容 | `tools/preflight.py` 含 `--restore-config` | 是 | 是 | ✅ |
| 内容 | `tools/preflight.py` 含 `looks_mojibake` | 是 | 是 | ✅ |
| 内容 | `tools/preflight.py` 含 `HUATEX_TESSERACT` | 是 | 是 | ✅ |
| 内容 | `tools/preflight.py` 含 `Tools for Huatex` | 是 | 是 | ✅ |
| 内容 | `config.py` 含 `WIN_TESS_SCAN_ROOTS` | 是 | 是 | ✅ |
| 合规 | 客户数据扫描 | 0 命中 | **0 命中** | ✅ |

原始日志：`evidence/verify_pack.txt`（JSON 全量结果）

---

## 4. 自愈功能实测（新增必做 · PASS）

解压到 `/tmp/huatex-heal-test/HUATEX-Tools`（**脱离 dev 树**），故意把 `config.yaml` 改坏：
- 注入乱码注释 `# 搴忓彿乱码`
- 破坏 `source_root` 引号 → `source_root: "D:/HUATEX`

**① `python3 tools/preflight.py --selftest`** → `[3/12]` 关键输出：
```
❌ [3/12] config.yaml 无法解析：while parsing a block mapping …
      诊断：config.yaml 里中文已**乱码**——典型原因是用 PowerShell/记事本以"非 UTF-8"
            方式保存过（Get-Content 默认按 GBK 读，再 Set-Content -Encoding UTF8 写回）
      最快修复：双击包根 `恢复配置.bat`（恢复原版 + 把损坏件另存为 config.yaml.broken-时间戳）
      等价命令：… -u tools\preflight.py --restore-config
```
→ **乱码诊断 ✅ + 提示 `恢复配置.bat` ✅**

**② `python3 tools/preflight.py --restore-config`**：
```
已把当前 config.yaml 另存为：config.yaml.broken-20261016_085730
✅ 已恢复原版 config.yaml（= 包内 config.default.yaml）。
```
- 恢复后 `config.yaml` 与 `config.default.yaml` **逐字节一致**（sha256 = `66e9e09e…20c8e1`，`cmp` 无差异）✅
- 损坏件 `config.yaml.broken-20261016_085730` 保留原乱码 ✅

原文：`evidence/selftest_broken_config.txt`、`evidence/selftest.out`

---

## 5. 冒烟回归（脱离 dev 树 · 纯 HTTP 驱动）

- 解压到 `/tmp/huatex-v132-test`，**脱离 dev 树**；`python3 -u app/server.py` → `127.0.0.1:8000`
- **Payment 核销**（10-13 批次 4 文件：`10-12华特明细待确认.xlsx` + `voucher-a1013.zip` + `voucher-b1013.zip` + `voucher-c1013.zip`，参数 `date=20261013`）
  - job `20261016_085826_payment` · status **done**
- **对拍基线** `work/payprep-20261013/out`（逐单元格，`tools/compare_xlsx.py`）

| 产出文件 | 差异总数 |
|---|---|
| Payment request to Bank-20261013.xlsx | **0** |
| Payment recon ledger-20261013.xlsx | **0** |
| Payment 待人工核清单-20261013.xlsx | **0** |

**差异 0/0/0** ✅ · `Payment request to Bank-20261013.xlsx.recon.txt` md5：base = new = `054bab47caa6ff3469c7553289da72c1` ✅

- 测后：停服 → `lsof -ti :8000` = **0 占用** ✅
- 临时目录 `/tmp/huatex-v132-test`、`/tmp/huatex-heal-test`、`/tmp/huatex-pkg-stage`（含客户数据）已 **trash** 清理 ✅
- Loan 流程按指令跳过

> 驱动过程备注：首次驱动因脚本漏传 `X-Token` 头 → 4 文件落入 4 个 token 目录 → job failed（未找到明细 Excel）；**修正调用方脚本后重跑成功**，**未改动包内任何代码**。

---

## 6. 发布 + 公网实测

- 发布目录：`~/WorkBuddy/Claw/opc-dashboard/`
  - `HUATEX-Tools-Windows-v1.3.2-20261016.zip`（152,004,902 B，sha256 与 deliverables 一致 ✅）
  - `HUATEX-Tools-Windows-v1.3.2-20261016-MANIFEST.txt`
- 旧版下架：`HUATEX-Tools-Windows-v1.3.1-20261016.zip` 与 `-MANIFEST.txt` 已 **trash**（其余文件未动）

**公网链接（当前隧道，`cf.log` / PID 44644 → localhost:8765）**
```
https://phase-partial-renew-juan.trycloudflare.com/HUATEX-Tools-Windows-v1.3.2-20261016.zip
```

| 实测项 | 结果 |
|---|---|
| `curl -sI` | **HTTP/2 200** · `content-type: application/zip` · `content-length: 152004902` · `server: cloudflare` · `cf-ray: a4b37793eded5cbc-HKG` · 耗时 **0.44 s** |
| 完整下载 | 200 · size 152,004,902 · **97.26 s**（~1.49 MB/s） |
| 下载件 sha256 | `9cbd4a4df99ff321e358ee7dbf96e377edc553b6290aecb19e88f8629e3ddf97` → **与包一致** ✅ |
| 临时下载文件 | 已 trash ✅ |

---

## 7. 遗留风险 / 备注

1. **Windows 真机复测未在本轮执行**：本轮为 macOS 上的「脱离 dev 树 + 纯 HTTP」回归，证明包自包含性无回归；但 GBK/pip 编码等坑**本质上只在中文 Windows 上才复现**，最终仍需 Daryl 在 Windows 真机跑 `一键安装.bat` + `selftest.bat` 确认「自检 12/12」。
2. **自愈能力已在本机实测通过**，但 `恢复配置.bat` 的 cp936 双击行为仍建议在 Windows 真机点一次确认。
3. **隧道为临时 trycloudflare 地址**（PID 44644）：随时可能失效/变更。
4. 打包器仍会在遇到 GBK 不可表示字符时 `SystemExit` 中止（设计意图，非缺陷）。
