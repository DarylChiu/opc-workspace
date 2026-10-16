# 子代理执行摘要 · huatex-v1.3-20261016（HUATEX Tools Windows 交付包 v1.3 重建 · 验证 · 发布 · 留痕）

- **任务**：重建 Windows 交付包 **v1.3-20261016**（已含 Balance 的三处源码修复），验收、发布、留痕。
- **执行时段**：2026-10-16 08:23–08:28 (Asia/Saigon)，约 **5 分钟**
- **工作区**：`/Users/zhaoyuzhao/.openclaw/workspace-balance`
- **模型**：**`deepseek/deepseek-v4-flash`**（本子代理运行模型，如实标注，不虚标）
- **边界**：本次**只读打包**——`portable/config.py`、`portable/tools/preflight_win.py`、`portable/tools/build_package.py` 的业务逻辑**一行未改**（源码 md5 见 evidence/02）。

---

## 1. 本次打进包里的修复（源码已由主代理完成）

| # | 修复点 | 验证证据（包内文件内容） |
|---|---|---|
| 1 | selftest 第 5 项：「缺依赖」手工命令改为 `cd /d "<程序目录>"` + 绝对路径写法 | 包内 `tools/preflight.py` 含 `cd /d` ✅ |
| 2 | selftest 第 6 项：Tesseract 找不到 → 新增环境变量 `HUATEX_TESSERACT` + 8 个自定义目录候选（`D:\Tools for Huatex\…`）+ 自定义目录限深扫描（≤3 层）；`config.py` 同规则 | 包内 `tools/preflight.py` 含 `HUATEX_TESSERACT`、`Tools for Huatex`；包内 `config.py` 含 `WIN_TESS_SCAN_ROOTS`、`scan_tesseract` ✅ |
| 3 | `一键安装.bat` 第 3 步先扫自定义目录里的 `tesseract.exe`，找到即跳过安装 | 包内 `一键安装.bat` 含 `D:\Tools for Huatex\tesseract.exe` 扫描行 ✅ |
| 4 | 版本号 → `v1.3-20261016`（文档同步） | 包内 `tools/preflight.py` 含 `v1.3-20261016` ✅ |

---

## 2. 交付物

| 交付物 | 路径 | 读数 |
|---|---|---|
| **交付包 v1.3** | `deliverables/HUATEX-Tools-Windows-v1.3-20261016.zip` | **151,999,887 B（144.96 MB）**，**81 条目** |
| 包 sha256 | 同上 | `3b42e64a0ed592abf8b03ecc21bb3c4cc0cdf8d5ae7351865d5c8b552701966c` |
| 内容清单 | `deliverables/HUATEX-Tools-Windows-v1.3-20261016-MANIFEST.txt` | 15,524 B（逐文件 sha256 + 素材 sha256 + 排除清单） |
| 打包器 | `portable/tools/build_package.py` | 未改（md5 `a01153c9…`） |
| Trace | `memory/subagent_runs/huatex-v1.3-20261016/execution_trace.jsonl` | 14 条，单调递增，`verify_trace.sh` PASS |
| 证据 | `memory/subagent_runs/huatex-v1.3-20261016/evidence/` | 27 份（含可复现 `f_regression.sh`、`04_verify_zip.py`） |

---

## 3. 验收数据表（全部 PASS ✅）

| 验收项 | 期望 | 实测 | 判定 |
|---|---|---|---|
| zip 字节数 | — | 151,999,887 B | ✅ |
| zip sha256 | — | `3b42e64a…2701966c` | ✅ |
| 条目数 | — | 81 | ✅ |
| `testzip()` | None | None | ✅ |
| UTF-8 文件名标志 `0x800` | 100% | **81/81 带标志**（缺 0 条） | ✅ |
| Tesseract 安装器 | 50,175,248 B | 50,175,248 B | ✅ |
| Poppler zip | 43,709,956 B | 43,709,956 B | ✅ |
| tessdata eng | 4,113,088 B | 4,113,088 B | ✅ |
| tessdata osd | 10,562,727 B（见备注） | 10,562,727 B | ✅ |
| tessdata vie | 531,275 B | 531,275 B | ✅ |
| tessdata chi_sim | 2,469,156 B | 2,469,156 B | ✅ |
| `wheels/*.whl` | 28 个 | 28 个（47.7 MB） | ✅ |
| 包内 `tools/preflight.py` 含 4 标识 | v1.3-20261016 / HUATEX_TESSERACT / Tools for Huatex / cd /d | 全命中 | ✅ |
| 包内 `config.py` 含 2 标识 | WIN_TESS_SCAN_ROOTS / scan_tesseract | 全命中 | ✅ |
| 包内 `一键安装.bat` 含扫描行 | `D:\Tools for Huatex\tesseract.exe` | 命中 | ✅ |
| 客户数据扫描（scan_zip） | 0 命中 | 0 命中 PASS | ✅ |

> **备注（口径差异）**：任务书写的 osd 期望值 `10,627,727`，磁盘实际与包内实际均为 **`10,562,727`**（`63`↔`56` 数位颠倒），且与 v1.2 交付时记录值一致（素材未变）。以磁盘/包内实测为准，判定 PASS。

---

## 4. 冒烟回归（Payment 核销 · 10-13 批次 · 4 文件）

- 方式：zip 解压至 `/tmp/huatex-v13-test`，**脱离 dev 树**，`app/server.py` 起于 `127.0.0.1:8000`，纯 HTTP 页面级驱动（`pkg_drive.py`：upload → run → 轮询）。
- job：`20261016_082414_payment`，status=`done`，约 30 s。
- 包内自检：`tools/preflight.py --selftest` rc=3（macOS 预期，内置素材 7/7 ✅）。

| 交付件 | 与 baseline 差异 |
|---|---|
| Payment request to Bank-20261013.xlsx | **差异总数 = 0** ✅ |
| Payment recon ledger-20261013.xlsx | **差异总数 = 0** ✅ |
| Payment 待人工核清单-20261013.xlsx | **差异总数 = 0** ✅ |

- `recon.txt` md5：base = new = `054bab47caa6ff3469c7553289da72c1` ✅
- H 合计：**12,949,026,506**（发票行 68），两侧一致 ✅
- OCR 降级警告：**0** 条 ✅
- Loan 回归：按任务书本次跳过。

**收尾**：停服 → 端口 8000 **0 listeners**；`/tmp/huatex-v13-test`（含客户数据）与 `/tmp/huatex-pkg-stage` 均用 **`trash`** 清理（未用 `rm`）✅

---

## 5. 发布与公网实测

- 发布路径：`~/WorkBuddy/Claw/opc-dashboard/`（zip + `-MANIFEST.txt`）
- 下架：`HUATEX-Tools-Windows-v1.2-20261015.zip` → `trash`（看板内无 v1-/v1.1- 版本文件，无可下架项）
- **公网链接**：`https://phase-partial-renew-juan.trycloudflare.com/HUATEX-Tools-Windows-v1.3-20261016.zip`

| 实测 | 结果 |
|---|---|
| `curl -sI`（HEAD） | **HTTP/2 200**；`content-length: 151,999,887`；TTFB **0.73 s**；cf-ray `a4b3460e9aa85ddd-HKG` |
| 整包下载（GET） | HTTP 200；**151,999,887 B**；**65.18 s**（≈2.33 MB/s） |
| 下载件 sha256 | `3b42e64a…2701966c` **= 本地 sha256** ✅ |
| 下载临时文件 | 已 `trash` |

---

## 6. 遗留风险

1. **Windows 真机未实测**：静默装 Tesseract、自定义目录扫描命中、`HUATEX_TESSERACT` 环境变量生效、离线装 wheel、中文名不乱码等仍需在 Windows 上按 R1–R12 逐项确认（承接 v1.2 说明 §7）。
2. **任务书 osd 期望值存在数位笔误**（10,627,727 vs 实际 10,562,727），已按实测判定；建议后续文档统一为 10,562,727。
3. **隧道为 trycloudflare 临时域名**：重启后会变更，链接需随用随取（本次取自 `.current_tunnel_url`，cf.log 末条 2026-10-16T00:10:36Z 与之自洽）。
4. `git diff --stat portable/` **无输出属预期**：`portable/` 在 `.gitignore` 中整体忽略，修改以源码 md5 + 标识 grep 佐证（非 git 跟踪）。

---

## 7. 成本 / 模型

- 模型：**`deepseek/deepseek-v4-flash`**（如实标注，不虚标）
- API 失败 0 次 / 重试 0 次；打包 1 次、验收 1 次、回归 1 次、公网下载 1 次
- 未触碰 `.env` / `openclaw.json` / API key / launchd / 成本台账；未 commit
