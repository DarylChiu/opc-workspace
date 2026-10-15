# 子代理执行摘要 · portable-s2-20261015（S2 · 配置化改造 + 回归对拍）

- **任务**：按 Daryl 批准的方案 B 实施顺序，完成 **S2 = 建 `portable/` 副本 + config 抽离 + 回归对拍**
- **执行时间**：2026-10-15 10:33–10:51 (Asia/Saigon)
- **工作目录**：`/Users/zhaoyuzhao/.openclaw/workspace-balance`
- **冻结基线**：`baseline/scripts-freeze-20261014/`（含 `MANIFEST-md5.txt`，与 `scripts/` 现行 md5 完全一致）
- **回归基线**：`work/loan-materials-2025-12/out/v2.8d-2025_12-20261014_1526/`（**只读，未改动**；mtime 仍 10-14）
- **复跑产出**：`portable/runs/20261015_1044/`

---

## 结果

| 项 | 结果 |
|---|---|
| **回归对拍** | ✅ **4/4 PASS**（Outcome1 / Outcome2 / 基线 zip / 处理报告） |
| **Mac `scripts/` 改动** | ❌ **零改动**（37 文件汇总 md5 = 冻结快照 `23ca32f668fd9bf5b26dfd0941aac095`；13 个被复制脚本逐个 md5 全等） |
| **写回 Toshiba** | ❌ **无**（顶层最新文件仍为 10-14） |
| **写 `work/`** | ❌ **无**（`work/` 今日零新增/修改） |
| `portable/` 骨架 | ✅ `config.yaml` `config.py` `workflows/{loan_materials,payprep}` `app/`（README 占位）`tools/regress_compare.py` `runs/` |
| 配置项 | ✅ **12/12 全部落实**（表见 deliverables 落实表 §1）；另加 3 个留痕/定位键 |
| 复制脚本 | 13 个（loan_materials 5 + payprep 8），副本 md5 与源全等 |
| API 调用 | 0 次失败、0 次重试（纯本地执行） |
| 估算成本 | 约 **$0.30**（≈ 30 次 exec + 3 次全量运行 + 1 次对拍） |

### 回归对拍明细（内容级）

| # | 对拍项 | 关键数字 | 判定 |
|---|---|---|---|
| 1 | Outcome1 逐单元格 | sheet `Outcome1`、`21×13`、**差异单元格 0** | **PASS** |
| 2 | Outcome2 文件集 | 20 目录 / 70 文件；仅基线 0、仅复跑 0、**md5 不同 0**；子目录 0；材料清单.txt 0 | **PASS** |
| 3 | 基线 zip 交叉核对 | 条目 **90** / 文件夹 **20** / 文件 **70**（子目录条目 0）；成员 md5 差异 0 | **PASS** |
| 4 | 处理报告 | 逐票明细 95 行 / 剔除清单 173 行 / 去重丢弃 4 行，**差集全 0**；未匹配票号 `HMXCAM250001, HMFZR250008` 一致 | **PASS** |

**注**：Outcome1 文件 md5 **必然不同**（`docProps/core.xml` 内含创建/修改时间戳：base `2c9b62…` / new `a1b2bb…`），故对拍采用**逐单元格取值**而非文件哈希；zip 成员 md5 则与复跑文件**完全相同**（内容未变）。

---

## ⚠️ S1 文档修订（Daryl 2026-10-15 拍板，覆盖 S1 §6.1 与 §7）

> **S1 §6.1「数据本地化的一个硬约束 / RM-Database 同步方式」与 §7「仍待你拍：RM-Database 同步方式」—— 已作废，不再实现。**

- **不做任何同步机制**：不写 `robocopy`、不做增量同步、不在 `portable/` 内放任何同步逻辑。
- **数据来源**：使用该工具的同事**自己**从公司共享盘把资料复制到本机，各人本地一份。
- **设计要求**：`paths.source_root`（含 RM-Database 根）就是一个**普通的可配置路径字段**；
  **S3 的 Web 前端留一个输入框**让用户填本地文件夹地址（并可保存回 `config.yaml`）。
- **默认值**：Mac 回归仍保留现值（保证逐位对拍）；**Windows/徒弟版默认留空或提示用户填写**
  （已落 `paths.source_root` 留空提示语 `paths.source_root_hint`，并在 runner 加**缺失自检**：不可用即报错并提示填写）。
- 因此：S1 §3「S3/S4/S5」范围不变，但 **S3 前端多一项「数据根路径输入框 + 保存」**。

---

## 关键偏差与处置

1. **S1 项 10（批次 tag）默认值与 S1 文本不一致 → 有意偏离**：S1 写「默认值 = 无（必填）」，本阶段设 `run.tag: "2025_12"`（= 10-14 现值）。
   **理由**：S2 铁律要求「默认值必须等于现值」，留空则误删 `config.yaml` 无法复现 10-14 行为。Win 版可由 Web 层要求必填。**待 Daryl 认可。**
2. **交付/端口/时区三项（S1 项 7/8/9）的消费方是 S3 的 `app/`**：本阶段只把键落到 `config.yaml`（默认 = S1 约定值：`local` / `8000` / `Asia/Saigon`），`app/` 仅 README 占位。
3. **OCR 语言「各脚本不一」**：为不改行为，**逐脚本保留现值**（`vie+eng` / `vie+eng+chi_sim` / `chi_sim+eng`），集中为 4 个键（`ocr.lang` / `lang_vn` / `lang_vn_chi` / `lang_scanned_fallback`），Win 落地时统一改。
4. **改造缺陷（已修）**：`rules.dedup_same_doc_version` 开关重构漏 `picked = []` 初始化 → 首次 dry-run 抛 `NameError`。
   **由 `--dry-run` 在写盘前挡下，未产生任何错误产物**（同日同时证实 dry-run 全程零写盘）。
   教训已记：**开关式重构必须两种取值都跑一遍**。
5. **S1 文档形态**：`deliverables/HUATEX本地部署-配置化改造清单-v1.1-20261014.md` 在磁盘上**不存在**（只有 `.docx`），本任务以 docx 提取文本为准。

---

## 产出路径

- 落表：`deliverables/HUATEX本地部署-S2配置化落实表-v1-20261015.md`
- 便携包：`portable/`（说明见 `portable/README.md`）
- 配置：`portable/config.yaml`（唯一入口）/ `portable/config.py`（读取器 + DEFAULTS）
- 对拍器：`portable/tools/regress_compare.py`
- 复跑留痕：`portable/runs/20261015_1044/{in,logs,Outcome1,Outcome2,处理报告,regression_diff.txt}`
- 对拍报告：`portable/runs/20261015_1044/regression_diff.txt`
- 运行原始日志：`tmp/portable-s2/dryrun2.out`、`tmp/portable-s2/real.out`
- Trace：`memory/subagent_runs/portable-s2-20261015/execution_trace.jsonl`

## 未决 / 移交 S3

1. `paths.runs_dir` / `paths.batch_dir` / `paths.l1_file` / `paths.source_root_hint` 四个新增键命名是否认可。
2. `run.tag` 默认值沿用现值（见偏差 1）是否认可；Win 版是否改为必填。
3. S3 启动顺序：**先跑通 Payment（`workflows/payprep/`）→ 再加 进出口材料**；并新增「数据根路径输入框 + 保存到 config」。
4. S3 前建议：对 `rules.*` 8 个开关各跑一次 `--dry-run`。
5. `portable/` 是否纳入版本库（目前未被 `.gitignore` 排除）。

## 模型 / 成本

- 模型：`deepseek/deepseek-v4-flash`（本子代理运行模型，如实标注）
- 估算成本：约 **$0.30**；API 失败 0 次 / 重试 0 次
