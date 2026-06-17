---
title: AI Project Cost Monitoring & Operations
created: 2026-06-14
tags: [ai, cost-monitoring, cross-ref]
source: Balance + Daryl discussion 2026-06-10
project: 抖音视频分析MVP
dev_agent: Bryson (xiaofeng)
monitoring_agent: Balance
---

# AI Project Cost Monitoring & Operations

> ⚡ **首次按项目口径监控成本** | Balance 实战验证  
> 🔗 **Cross-ref**: ACCA F5 ABC成本法 → 项目成本归集 → AI Agent session成本追踪器

---

## 📊 实战案例：抖音视频分析MVP 成本监控

| 维度 | 数据 |
|:---|:---|
| **项目** | 抖音视频分析MVP |
| **开发 Agent** | Bryson (xiaofeng) |
| **成本监控 Agent** | Balance |
| **模型** | deepseek/deepseek-v4-pro |
| **周期** | 10:30 → 22:16 (707 min) |
| **总调用** | 292 次 |
| **总 Token** | 29,238,787 |
| **总成本** | $10.03 |
| **烧钱速率** | $0.84/h |

> 对比数据：Kitty (main) 使用 claude-sonnet-4.5，烧钱速率 $4.91/h — **模型选择决定成本量级**

---

## 🏗️ 成本归集三层模型

```mermaid
graph TB
    L1[Layer 1: Raw Data<br/>"每笔API调用<br/>{timestamp, agent, model, tokens, cost, session_id}"]
    L2[Layer 2: Activity Tagging<br/>"session→project映射<br/>意图分类 阶段标记"]
    L3[Layer 3: Project Aggregation<br/>"按项目聚合<br/>多维拆解 横向对比"]
    
    L1 --> L2 --> L3
    
    classDef layer fill:#d5f5e3,stroke:#27ae60
    class L1,L2,L3 layer
```

| Layer | 状态 | 说明 |
|:---|:---|:---|
| L1 原始数据层 | ✅ 已存在 | 每笔API调用有完整数字足迹 |
| L2 活动标记层 | 🔧 需设计 | session→project映射、调用意图分类 |
| L3 项目归集层 | 🔧 需构建 | 按项目聚合、多维拆解、横向对比 |

---

## ⚠️ 为什么传统工时法在 AI Agent 场景完全失效

| 工时法假设 | AI Agent 现实 | 结论 |
|:---|:---|:---|
| 工时 ∝ 成本 | Token 消耗与成本直接相关，与时长无关 | **维度错误** |
| 人能准确回忆归属 | 人无法记住 agent 在哪个 session 做了什么 | **归因不可靠** |
| 同类任务效率相近 | 不同模型/prompt 策略成本差异巨大 | **不可比** |
| 事后填报可行 | 应系统级自动标记 | **方法落后** |

> 💬 Daryl 的判断："用旧的工时分配框架去套 AI agent 的成本数据，是用模糊代理指标替代可精确测量的实际消耗"

---

## 🛠️ 监控工具链

| 工具 | 路径 | 用途 |
|:---|:---|:---|
| `project_cost.py` | `~/.openclaw/workspace/cost_tracker/` | 数据提取：读取 session jsonl，按时间/agent 聚合成本 |
| `start_project_monitor.sh` | `~/.openclaw/workspace/cost_tracker/` | 管理脚本：start/stop/status，自动装 cron |

### 启动命令

```bash
bash start_project_monitor.sh start \
  --agent xiaofeng \
  --project '项目名' \
  --start '10:30' \
  --hours '12-23'
```

---

## 📋 实战教训（5 问题 + 4 改进）

| # | 问题 | 根因 |
|---|------|------|
| 1 | 查错 agent 目录（bryson→xiaofeng） | agent 别名未确认 |
| 2 | 报告发送失败 | openclaw 二进制路径写错 |
| 3 | 报告发送失败 | 缺 --target 参数 |
| 4 | 监控窗口不够 | 未确认期望窗口 |
| 5 | 无验证机制 | 部署前未测试 |

**改进**：守护进程→系统 cron / 启动前 checklist / 主动确认通知 / 参数化脚本

---

## 🔗 Cross-References

- **ACCA F5 (Performance Management)**: Activity-Based Costing (ABC) → [[../../../01-Financial/ACCA/F1-BT/F1-Home|F1 Home]]
  - 成本动因 (Cost Driver) 识别
  - Job Costing 按项目追踪成本
  - ABC 与传统成本法的对比
- **IFRS-IAS**: [[../../../01-Financial/IFRS-IAS/Cost-Allocation/Cost-Allocation-Basics|Cost Allocation Basics]]
- **传统软件成本归集模式**: 工时法 / ABC法 / R&D资本化(IAS 38)

---

## 🔍 缺口诊断

1. **工具代码未入库**：`project_cost.py` 和 `start_project_monitor.sh` 存储在外部 `cost_tracker/` 目录，知识树中仅有引用路径
2. **样本量不足**：目前只有一个项目（抖音视频分析MVP）+ 一个 Agent（Bryson）的监控数据
3. **多 Agent 协同场景未覆盖**：Kitty设计→Bryson开发→Kitty验收的跨 agent 成本如何归集？
4. **session→project 标记机制**：Layer 2 的活动标记层尚未设计

> 📌 **后续更新方向**：积累多项目多 Agent 样本后补充对比数据

---

> Created: 2026-06-14 | Source: Balance project-monitoring-sop.md / project-cost-allocation-discussion.md
