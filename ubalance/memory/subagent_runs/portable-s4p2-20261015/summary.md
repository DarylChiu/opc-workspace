# 子代理执行摘要 · portable-s4p2-20261015（S4.2 · 全离线一键安装包 v1.2）

- **任务**：把「用户需要自己上网下载的东西」（7 个 pip 依赖 / Tesseract / Poppler / 语言包）**全部内置进交付包**，
  包根新增 `一键安装.bat`；程序侧新增 Windows 自动探测（不改判定逻辑、不改 Mac 行为）；重打包 v1.2 并做脱离 dev 树的自包含回归。
- **执行时段**：2026-10-15 17:31–17:52 (Asia/Saigon)，约 **21 分钟**（预算 90 分钟，未超时）
- **工作区**：`/Users/zhaoyuzhao/.openclaw/workspace-balance`
- **模型**：**`deepseek/deepseek-v4-flash`**（本子代理运行模型，如实标注，不虚标）
- **基线（只读）**：`work/payprep-20261013/out/`、`work/loan-materials-2025-12/out/v2.8d-2025_12-20261014_1526/`

---

## 1. 交付物

| 交付物 | 路径 | 读数 |
|---|---|---|
| **交付包 v1.2** | `deliverables/HUATEX-Tools-Windows-v1.2-20261015.zip` | **151,997,295 B（144.96 MB）**，**81 个文件** |
| 包 sha256 | 同上 | `a61792c0b8b92f383bfd3ea13a26cb3cdfb35374b6bea55b0043a69efb7cbdec` |
| 内容清单 | `deliverables/HUATEX-Tools-Windows-v1.2-20261015-MANIFEST.txt` | 逐文件 sha256 + 内置素材 sha256 + 排除清单 |
| S4.2 说明 | `deliverables/HUATEX本地部署-S4.2-一键安装包说明-v1-20261015.md` + `.docx` | 69 段 / 12 表 |
| 打包器（扩展） | `portable/tools/build_package.py` | 幂等（另存重建 → 同 sha256） |
| 自检脚本源 | `portable/tools/preflight_win.py` → 包内 `tools/preflight.py` | 12 项 ✅/❌ |
| Trace | `memory/subagent_runs/portable-s4p2-20261015/execution_trace.jsonl` | 25 条，时间戳单调递增，`verify_trace.sh` PASS |
| 证据 | `memory/subagent_runs/portable-s4p2-20261015/evidence/` | 23 份（含可复现的 `f_regression.sh`） |

## 2. 内置素材（§A · 下载 0 失败、逐字节校验）

| 素材 | 字节 | sha256（前 16） |
|---|---|---|
| Tesseract 5.4.0 安装器 | 50,175,248 | `c885fff6998e0608…` |
| Poppler 26.09.0 包 | 43,709,956 | `7a6f256a0ddf7536…` |
| tessdata eng / osd / vie / chi_sim | 4,113,088 / 10,562,727 / 531,275 / 2,469,156 | `7d4322bd…` / `9cf5d576…` / `79df64ca…` / `a5fcb6f0…` |
| wheels ×28（win_amd64 · cp310/311/312/313） | 49,990,270（47.67 MB） | 逐文件见 MANIFEST |

## 3. `一键安装.bat`（§B）

管理员探测 → `py -3`/`python` 双探测 → **pip 离线装依赖**（`--no-index --find-links=wheels`）→ **Tesseract 静默装**
（`/VERYSILENT /NORESTART /SUPPRESSMSGBOXES`，已装跳过）→ **PowerShell 解压 Poppler** 到 `tools\poppler\` → **复检**（`preflight --selftest`）→ 汇总 + `pause`。
幂等、每步中文输出、失败给补救；CRLF + `chcp 65001`。**不写系统环境变量**（POPPLER_PATH / TESSDATA_PREFIX 由程序注入）。

## 4. 自动探测（§C · 仅 Windows，Mac 行为不变）

- **tesseract**：config 值 → `C:\Program Files\Tesseract-OCR\` → `C:\Program Files (x86)\...` → 包内 `tools\tesseract\`（命中即改写内存配置并打印 `[detect]`）。
- **POPPLER_PATH**：包内 `tools\poppler\*\Library\bin` → 注入环境变量 + `jobs.py` 传给子进程 + **7 处 `convert_from_path` 显式传 `poppler_path=`**。
- **TESSDATA_PREFIX**：包内 `tessdata\` → 注入环境变量（语言包不依赖安装器勾选）。
- 自检新增：tesseract **实际路径+来源**、`--list-langs` 实测、`POPPLER_PATH`/`TESSDATA_PREFIX` **实际值**、**内置素材三件套**逐文件字节数。

## 5. 自包含回归（§F · 脱离 dev 树，纯 HTTP）

| 流程 | job | 耗时 | 结果 |
|---|---|---|---|
| Payment（10-13 批次） | `20261015_174049_payment` | 29.8 s | 三份交付件 **差异 0 / 0 / 0**；`recon.txt` md5 全等；**H 合计 12,949,026,506 · 68 行**；OCR 降级警告 0 |
| Loan（L1 20 条 + 2025_12 等价 override） | `20261015_174120_loan` | 199.5 s | `Outcome1` **21×13 差异 0**；`Outcome2` **70/70 md5 全等**、空目录 2 个一致；页面 ④ 下载 `Outcome2.zip` 19,186,175 B |

→ 既证明包自包含，也**反证「新增探测在 macOS 上不改变行为」**（Mac 下探测全为空值，走的还是旧路径）。

## 6. UTF-8 标志（§E 关键）

- 首轮 FAIL：**72/81 条目缺 `0x800`**（根因：`zipfile` 只给非 ASCII 名置位，且自设 flag 会被 `open(mode='w')` 清零）。
- 处置：**覆写 `ZipInfo._encodeFilenameFlags`**（不碰压缩数据）→ 重打包后 **81/81 全部带标志**，`testzip()` 通过，读回内容一致。

## 7. 偏差与 Windows 待实测

- 偏差：① UTF-8 标志首轮 FAIL（已修）；② `一键安装.bat` 变量延迟展开（已改 `!FAILED!`）；③ 临时目录出现 macOS AppleDouble 边车文件（不影响交付，已清理）；④ 开发树自检在 macOS 退 3（属预期，包内自检素材 7/7 ✅）。
- **Windows 待实测 R1–R12**（见 S4.2 说明 §7）：静默安装是否无交互、非管理员提示、Expand-Archive、探测命中 Program Files、
  `TESSDATA_PREFIX`/`POPPLER_PATH` 生效、离线装 wheel、扫描件 OCR 不报 Poppler 错、中文名不乱码、杀毒放行等。

## 8. 红线自检

| 约束 | 证据 | 结果 |
|---|---|---|
| `scripts/` 一行未改 | `find scripts -newermt "2026-10-15 00:00" -type f` → **0** | ✅ |
| 不写 Toshiba | 顶层最新仍 = `Outcome1-v2.8d-ALL262-20261014.xlsx`（10-14 16:33） | ✅ |
| dev 树 `portable/config.yaml` 未改 | md5 `7eaa441edfd0786fa855ecdf0a0b6c05`（无 Windows 横幅） | ✅ |
| 不执行 Windows 安装器 / 不装新依赖 | 仅下载+搬运；`pip download` 只下载 | ✅ |
| 包内无客户数据 | 打包器自动扫描 PASS；素材目录按设计豁免 | ✅ |
| 测完停服 + 清临时目录 | `0 listeners left`；`/tmp/huatex*` 已清空 | ✅ |
| 不声称 Windows 已实测 | S4.2 说明 §7 明确列出 R1–R12 | ✅ |
| 如实标注模型 | 全文标注 `deepseek/deepseek-v4-flash` | ✅ |

## 9. 成本 / 模型

- 模型：**`deepseek/deepseek-v4-flash`**（如实标注，不虚标）
- API 失败 0 次 / 重试 0 次；本地流程运行 2 次（Payment ×1、Loan ×1）+ 打包 4 次（含幂等复验）
- 下载：约 108 MB 安装素材 + 47.7 MB wheel = **≈ 156 MB**（0 失败）；总耗时约 21 分钟（预算 90 分钟）
