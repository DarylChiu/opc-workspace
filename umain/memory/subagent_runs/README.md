# 子代理 Trace 协议 · 接入说明

> **版本**: v1.0 | **上线日期**: 2026-07-17 | **最后更新**: 2026-07-18  
> **维护者**: 忧郁小猫 (main Agent) | **适用范围**: 全 Agent 团队

---

## 协议概述

### 什么是 Trace？

Trace（执行轨迹）是子代理（subagent）在执行任务过程中产生的 **结构化操作日志**。每条记录包含时间戳、步骤编号、操作类型和结果摘要。

### 为什么需要 Trace？

| 问题 | Trace 提供的能力 |
|------|----------------|
| 子代理跑了什么？ | 完整的步骤清单，按时间排序 |
| 哪个步骤失败了？ | 精确定位出错点和上下文 |
| 结果可信吗？ | 每步可验证，支持回溯审查 |
| 能复现吗？ | 完整操作序列 = 可复现执行方案 |
| 效率如何？ | 步骤计数、耗时分析、瓶颈识别 |

### 协议层级

```
Trace 协议
├── definition:     TRACE_TEMPLATE.jsonl  （格式定义）
├── verification:   verify_trace.sh       （验收脚本）
└── documentation:  README.md              （本文档）
```

---

## 接入步骤 Checklist

- [ ] 阅读 TRACE_TEMPLATE.jsonl 了解标准格式
- [ ] 在 AGENTS.md 中添加 Trace 条款（见下方各 Agent 定制模板）
- [ ] 在 spawn 子代理的 task 指令中加入 trace 写入要求
- [ ] 子代理完成后运行 verify_trace.sh 验收
- [ ] 验收通过后将 trace + summary.md 一起 git commit 归档

---

## verify_trace.sh 使用说明

### 基本用法

```bash
bash verify_trace.sh <trace文件路径>
```

### 返回值

| 返回值 | 含义 | 典型场景 |
|--------|------|----------|
| `PASS` (exit 0) | 全部检查通过 | trace 完整合规，可直接归档 |
| `WARN` (exit 1) | 存在轻微问题 | 缺字段、缺 summary.md，建议修复 |
| `FAIL` (exit 2) | 存在严重问题 | JSON 非法、时间戳乱序、文件不存在 |

### 检查项目

| # | 检查项 | 级别 |
|---|--------|------|
| ① | 文件存在且非空 | FAIL |
| ② | 每行是合法 JSON | FAIL |
| ③ | 每行含 ts/step/action/result 四字段 | WARN（部分缺） |
| ④ | ts 时间戳单调递增 | FAIL（倒退） |
| ⑤ | summary.md 同时存在于同一目录 | WARN（缺失） |

### 验收决策指南

```
验收流程:
  verify_trace.sh 返回 → 
    PASS → ✅ 验收通过，归档
    WARN → ⚠️ 人工判断（字段不全通常接受早期trace，缺summary.md则补写）
    FAIL → ❌ 子代理重跑（JSON非法=已损坏，需重新生成）
```

---

## TRACE_TEMPLATE.jsonl 模板说明

```jsonl
{"ts":"ISO8601时间戳","step":"步骤标识","action":"操作类型","result":"结果摘要(≤200字符)"}
```

### 字段规范

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `ts` | string | ✅ | ISO 8601 带时区 | `2026-07-18T12:00:00+07:00` |
| `step` | string | ✅ | 步骤标识，建议格式 `{里程碑}-{序号}` | `M3-01`, `BAL-03`, `DEV-12` |
| `action` | string | ✅ | 操作类型，用大写下划线 | `INIT`, `CREATE_FILE`, `WEB_SEARCH`, `RUN_TEST`, `COMPLETE` |
| `result` | string | ✅ | 结果摘要，≤200字符 | `验证脚本创建完成，已chmod +x` |

### 记录时机

以下操作 **必须** 写入 trace：
- 子代理启动（INIT）
- 文件创建/修改/删除
- 外部 API 调用（搜索、数据查询等）
- 代码执行、测试运行
- 重要决策（含决策理由）
- 子代理完成/失败（COMPLETE/FAILED）

---

## 各 Agent 接入状态

| Agent | 文件 | 状态 | 定制方向 |
|-------|------|------|---------|
| main (忧郁小猫) | `AGENTS.md` | ✅ 已接入 (7/17 M2) | 分流规则+回传协议 |
| Balance (算点小账) | `workspace-balance/AGENTS.md` | ✅ 已接入 (7/18 M3) | 财务审计可追溯 |
| xiaofeng (吹点小风) | `xiaofeng_workspace/AGENTS.md` | ✅ 已接入 (7/18 M3) | CI/CD 质量门 |
| Self (恨点小己) | `workspace-self/AGENTS.md` | ✅ 已接入 (7/18 M3) | 自我审计+SAGE 双重审查 |

---

## 常见问题

**Q: 早期 trace 文件格式不兼容怎么办？**  
A: WARN 级别可接受，verify_trace.sh 不会阻止。后续子代理必须按新格式生成。

**Q: 子代理忘记写 trace 怎么办？**  
A: 验收时 verify_trace.sh 返回 FAIL（文件不存在），子代理必须重跑。

**Q: summary.md 应该写什么？**  
A: 至少包含：任务状态（✅完成/⚠️部分/❌失败）、执行步骤数、关键成果、遗留问题。

**Q: trace 文件在哪里？**  
A: 每个子代理任务的 `memory/subagent_runs/{task_id}/execution_trace.jsonl`
