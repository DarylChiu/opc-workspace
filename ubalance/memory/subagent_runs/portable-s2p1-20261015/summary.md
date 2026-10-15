# 子代理执行摘要 · portable-s2p1-20261015（S2.1 · 4 项拍板调整 + override 回归复现）

- **任务**：按 Daryl 2026-10-15 拍板的 4 项调整改配置化产物，并用 override 复跑 20 条批次与 10-14 基线做**内容级对拍**
- **执行时间**：2026-10-15 10:57–11:16 (Asia/Saigon)
- **工作目录**：`/Users/zhaoyuzhao/.openclaw/workspace-balance`
- **回归基线（只读）**：`work/loan-materials-2025-12/out/v2.8d-2025_12-20261014_1526/`
- **复跑产出**：`portable/runs/20261015_1100/`（对拍报告 `regression_diff.txt`）
- **模型**：**`deepseek/deepseek-v4-flash`**（如实标注）

---

## 结果

| 项 | 结果 |
|---|---|
| **回归对拍** | ✅ **4/4 全 PASS**（Outcome1 逐单元格差异 **0** / Outcome2 70 文件 md5 差异 **0** / 基线 zip 90 条目成员 md5 差异 **0** / 处理报告差集 **0**） |
| **`l1_file` 留空报错路径** | ✅ 实测有效：中文报错 + `EXIT=1` + **零写盘** |
| **`scripts/` 改动** | ❌ **零改动**（37 个 .py 汇总 md5 `ab2921d264c04bc1cddfc5b150d52f40`，改造前后一致） |
| **写回 Toshiba** | ❌ **无**（顶层最新文件仍 = 10-14） |
| **写 `work/`** | ❌ **无**（今日新增/修改 = 0 条） |
| **`md2docx.py`** | ❌ 未改动（md5 `ce75c32f7922509c54737e1aa7e97f6f`） |
| API 调用 | 0 失败 / 0 重试（纯本地执行） |

### 回归对拍明细（基线 vs 复跑，内容级）

| # | 对拍项 | 读数 | 判定 |
|---|---|---|---|
| 1 | Outcome1 | `Outcome1` sheet、`21×13`、7,498 B；**差异单元格 = 0**（文件 md5 不同属预期：`docProps` 时间戳） | PASS |
| 2 | Outcome2 文件集 | 20 目录 / 70 文件；仅基线 0 / 仅复跑 0 / **同路径 md5 不同 0** | PASS |
| 3 | 基线 zip 交叉核对 | 条目 90（夹 20 / 件 70，子目录 0）；成员 md5 差异 0 | PASS |
| 4 | 处理报告 | 逐票明细 95 / 剔除 173 / 去重丢弃 4，**差集全 0**；L1 20 行、RM 271 目录、复制 70 件、RM 快照 2026-10-06、未匹配 `HMXCAM250001, HMFZR250008` | PASS |

---

## 三处改动 diff 摘要

### 1) `portable/config.yaml`（主配置，默认值口径 → 当前批次 2026_10）
```diff
-# 规则：默认值 = 2026-10-14 Mac 侧现值；删掉本文件行为也不变
+# 规则：**默认值 = 当前批次（2026_10）**；删掉本文件行为也不变
+# ⚠️ 口径变更（Daryl S2.1）：原「默认值 = 现值 = 2025_12」已作废；回归请用 config.regression-2025_12.yaml
-  batch_dir: "loan-materials-2025-12"
-  l1_file: "work/loan-materials-2025-12/in/L1-成品采购入库补单测试20条.xlsx"
+  batch_dir: "loan-materials-2026-10"
+  l1_file: ""      # 留空 → runner 明确报错并提示填写
 run:
-  tag: "2025_12"
-  months: [["2025","THÁNG 12"], ["2026","THÁNG 01"]]
+  tag: "2026_10"
+  months: [["2026","THÁNG 10"], ["2026","THÁNG 11"]]   # ⚠️ 推断值，待确认
```
- `paths.source_root`（Toshiba）/ `paths.source_root_hint` **保持不变**；配置键命名**保持原名**（`paths.runs_dir` / `paths.batch_dir` / `paths.l1_file` / `paths.source_root_hint`）。
- **连带修正**：`portable/config.py` 的 `DEFAULTS` 同步为 2026_10 口径（tag / months / batch_dir / `l1_file=''`），否则「误删 config.yaml」会回落到 2025_12、与新口径冲突。**此项超出「只改 config.yaml」字面范围，已在交付物 §⑤ 标注待确认。**

### 2) `portable/workflows/loan_materials/run_loan_2025_12_v28d.py`（仅加 L1 校验，判定逻辑未动）
```diff
+_L1_REL = (CFG.get('paths.l1_file') or '').strip()
+if not _L1_REL:
+    raise SystemExit('❌ paths.l1_file 未配置（当前为空）… 请填写 …')
+L1_XLSX = os.path.join(WS, _L1_REL)
+if not os.path.isfile(L1_XLSX):
+    raise SystemExit(f'❌ L1 文件不存在：{L1_XLSX} …')
```
- 位置在任何写盘动作（`STAGE` / `Outcome2` / `logs` 建目录）**之前** → 不静默、不落盘、不产空结果。

### 3) `.gitignore`（3 条细分 → 1 条整体排除）
```diff
-# HUATEX 便携包：运行留痕含客户数据，不入库；缓存不入库
-portable/runs/
-portable/**/.pdftext_cache.json
-portable/**/__pycache__/
+# HUATEX 便携包 portable/ 为交付产物（运行留痕含客户数据），通过 zip 归档交付，整体不入 git。
+portable/
```
- 实测：`git check-ignore -v portable/config.yaml` → `.gitignore:2:portable/`；`git ls-files portable` 为空。

### 新增文件
- `portable/config.regression-2025_12.yaml`（回归专用 override：tag=2025_12 / months=12月+次年1月 / batch_dir=loan-materials-2025-12 / l1_file=2025_12 L1 / output_root+runs_dir=runs）
- `deliverables/HUATEX本地部署-S2配置化落实表-v1.1-20261015.md` + `.docx`

---

## `l1_file` 留空报错路径实测
```
$ python3 portable/workflows/loan_materials/run_loan_2025_12_v28d.py --dry-run
❌ paths.l1_file 未配置（当前为空）
   请在 portable/config.yaml 的 paths.l1_file 填写本批 L1 输入文件
   （相对 workspace 的路径，例如 work/loan-materials-2026-10/in/L1-….xlsx），
   或在前端页面上传 / 选择 L1 文件后再运行。
   ※ 若要做 2025_12 回归复现，请改用 override：WF_CONFIG=portable/config.regression-2025_12.yaml
EXIT=1
```
**零写盘证据**：跑前/跑后 `portable/runs` 文件数 75→75、`work` 文件数 2891→2891、`portable/runs/` 无新增时间戳目录。

---

## 偏差 / 未决（请 Daryl 拍板）

1. **⚠️ `run.months` 跨月范围 = 我的推断**：2026_10 批真实跨月范围未知，按 2025_12 批次口径（当月+次月）类比推断为 `[["2026","THÁNG 10"],["2026","THÁNG 11"]]`。**若实际不同（只搜 10 月 / 或跨 2027-01），请改这一行**（config.yaml 行内已同款注释）。
2. `paths.batch_dir` = `loan-materials-2026-10`（按命名规则**预期**值）。
3. `config.py` DEFAULTS 连带同步（见上）—— 超出字面范围，请确认。
4. 10-14 两份改造清单（v1.1 / v1.2）**未下架、未改动**（按拍板「无需动作」）。
5. `portable/` 现已整目录排除 git；交付仍走 zip 归档。

## 硬约束自检证据

| 约束 | 证据 |
|---|---|
| `scripts/` 一行不改 | 37 个 .py 汇总 md5 `ab2921d264c04bc1cddfc5b150d52f40` 改造前后**完全一致** |
| 不写回 Toshiba | 顶层 mtime 最新仍为 `Outcome1-v2.8d-ALL262-20261014.xlsx`（10-14 16:33） |
| 不往 `work/` 新增运行目录 | `find work -newermt "2026-10-15 00:00"` 计数 = **0** |
| 改动落点 | 仅 `portable/`、`.gitignore`、`memory/subagent_runs/portable-s2p1-20261015/`、`deliverables/*v1.1*` |
| 无残留硬编码 | `grep 2025_12 / TOSHIBA` 命中的全部是**注释 / docstring / 回归 override / 有意保留的 source_root 默认值**，无生效硬编码 |
| 不联网安装 / 不跑支付 | 全程本地 python3，无 pip / 无网络 / 无支付 |

## 产出路径

- 对拍报告：`portable/runs/20261015_1100/regression_diff.txt`
- 回归 override：`portable/config.regression-2025_12.yaml`
- 交付物：`deliverables/HUATEX本地部署-S2配置化落实表-v1.1-20261015.md` / `.docx`
- Trace：`memory/subagent_runs/portable-s2p1-20261015/execution_trace.jsonl`（12 条）
- 运行原始日志：`/tmp/portable-s2p1/real.out`

## 模型 / 成本

- 模型：`deepseek/deepseek-v4-flash`（本子代理运行模型，如实标注，不虚标）
- API 失败 0 次 / 重试 0 次；估算成本 约 **$0.20**
