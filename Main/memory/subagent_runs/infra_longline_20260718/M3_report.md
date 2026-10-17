# M3 里程碑报告：子代理 Trace 协议标准化推广

> **任务**: infra_longline_20260718 / M3  
> **日期**: 2026-07-18  
> **执行 Agent**: 忧郁小猫(main) 子代理  
> **状态**: ✅ 完成  
> **模型**: deepseek/deepseek-v4-pro

---

## 里程碑目标

将 M2 阶段建立的子代理 trace 协议从「文档级标准」推广为「全 Agent 团队执行标准」：
1. 创建自动化验收脚本
2. 接入全部 4 个 Agent（main 已在 M2 接入，M3 接入 Balance/Xiaofeng/Self）
3. 编写接入文档
4. 端到端验证

---

## ✅ 已完成

### 1. verify_trace.sh — 验收脚本

**路径**: `memory/subagent_runs/verify_trace.sh`  
**语言**: Bash + Python3（JSON 验证）  
**权限**: 已 `chmod +x`

**5 项检查**：

| # | 检查项 | 级别 | 实现方式 |
|---|--------|------|---------|
| ① | 文件存在且非空 | FAIL | `[[ -s "$FILE" ]]` |
| ② | 每行合法 JSON | FAIL | `python3 -c "json.loads()"` 逐行 |
| ③ | ts/step/action/result 四字段 | WARN | `python3 -c "d['ts']"` 逐字段 |
| ④ | ts 时间戳单调递增 | FAIL | ISO 8601 字典序比较 |
| ⑤ | summary.md 同时存在 | WARN | `[[ -f "$DIR/summary.md" ]]` |

**退出码**: PASS=0, WARN=1, FAIL=2

### 2. Agent AGENTS.md 接入

| Agent | 文件路径 | 插入位置 | 定制方向 | 条款数 |
|-------|---------|---------|---------|--------|
| **Balance** | `workspace-balance/AGENTS.md` | Red Lines 之前 | 财务审计可追溯，trace=审计底稿 | 5条规则+定制说明 |
| **Xiaofeng** | `xiaofeng_workspace/AGENTS.md` | Make It Yours 之前 | CI/CD 质量门，FAIL=CI失败 | 5条规则+定制说明 |
| **Self** | `workspace-self/AGENTS.md` | Red Lines 之前 | 自我审计+SAGE 双重审查 | 5条规则+定制说明 |
| **main** | `workspace/AGENTS.md` | 已在 M2 接入 | 分流规则+回传协议 | 已在 M2 完成 |

**定制措辞差异**:
- Balance: "trace 是财务分析的审计链...确保分析结果经得起复核查验"
- Xiaofeng: "trace 是代码交付的质量门...确保交付物可复现、可回溯、可审计"
- Self: "trace 是知识生产的认知链...配合 SAGE Checker 形成执行链+质量门双保险"

### 3. README.md — 接入说明

**路径**: `memory/subagent_runs/README.md`  
**内容**: 协议概述、接入 checklist、verify_trace.sh 使用说明、TRACE_TEMPLATE 字段说明、各 Agent 接入状态表、FAQ（4 条）

### 4. 端到端验证

| 测试目标 | 文件 | 结果 | 说明 |
|---------|------|------|------|
| M1 trace | test_20260717/execution_trace.jsonl | **WARN** | 3行用 `result_summary` 替代 `result`，早期痕迹，可接受 |
| M2 trace | infra_longline/execution_trace.jsonl | **PASS** | 8行全部合规（补写 summary.md 后） |
| M3 trace | infra_longline/execution_trace.jsonl | **PASS** | 本任务自身 11 步全部合规 |

---

## 🔄 进行中

无。

---

## ⚠️ 已知限制和后续优化建议

### 限制
1. **verify_trace.sh 依赖 python3**: JSON 验证使用了 Python，若环境无 python3 会失败。可考虑改用 `jq`（若安装）做 fallback
2. **M1 迹格式不兼容**: 早期迹用 `result_summary` 代替 `result`，verify_trace.sh 给出 WARN 但不阻止验收
3. **TRACE_TEMPLATE.jsonl 字段不一致**: 模板用 `timestamp` 而实际标准用 `ts`，模板需后续对齐

### 优化建议（纳入 M4 或后续里程碑）
1. **jq fallback**: verify_trace.sh 增加 `jq` 作为 JSON 验证备选方案
2. **TRACE_TEMPLATE 对齐**: 更新 TRACE_TEMPLATE.jsonl 与 verify_trace.sh 字段名一致
3. **批量验收**: 增加 `verify_trace.sh --all` 扫描所有子代理目录并汇总报告
4. **Git hook**: 在 pre-commit 中集成 verify_trace.sh，阻止未通过验收的 trace 提交
5. **Dashboard 集成**: trace 统计（步骤数/耗时/通过率）纳入项目 dashboard

---

## 📝 自主决策记录

| 决策 | 级别 | 理由 |
|------|------|------|
| 使用 python3 而非 jq 做 JSON 验证 | P2 | python3 在 macOS 默认安装，jq 需额外安装 |
| ③字段缺失定为 WARN 而非 FAIL | P2 | 兼容早期迹，避免阻塞历史归档。新迹缺字段+无 summary.md = 建议重跑 |
| Trace 条款插入位置（各 Agent 不同） | P3 | Balance 放 Red Lines 前（审计优先），Xiaofeng 放 Make It Yours 前（工具性规则），Self 放 Red Lines 前（审计优先） |
| M1 trace 的 result_summary WARN 可接受 | P3 | 早期迹先于协议，不要求修补。后续子代理须严格按 t/step/action/result |
