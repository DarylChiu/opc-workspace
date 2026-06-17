# 项目成本监控 SOP + 工具 — 归档文档

> 来源：Balance (算点小账) 与 Daryl 2026-06-10 实战验证
> 交付：知识管理体系 Self，用于归纳归档
> 版本：v1.0

---

## 一、背景

Daryl需要跟踪AI Agent协同开发项目的API调用成本。2026-06-10以**Bryson（xiaofeng）开发项目**为实战验证，跑通了从「启动→每小时汇报→停止→复盘」的完整流程。

### 实战数据摘要

| 指标 | 数值 |
|------|------|
| Agent | xiaofeng (Bryson/吹点小风) |
| 模型 | deepseek/deepseek-v4-pro |
| 项目周期 | 10:30→22:16（707分钟） |
| 总调用 | 292次 |
| 总Token | 29,238,787 |
| 总成本 | $10.03 |
| 烧钱速率 | $0.84/h |

---

## 二、标准操作流程 (SOP)

```
Step 1: Daryl说「启动XX项目成本监控」
Step 2: 确认 agent名、起始时间、监控窗口
Step 3: 运行启动命令：
   bash start_project_monitor.sh start \
     --agent xiaofeng \
     --project 'Bryson开发' \
     --start '10:30' \
     --hours '12-23'
Step 4: 脚本自动执行：
   → 验证agent存在
   → 测试数据可读
   → 发送测试消息给Daryl
   → 安装系统cron
Step 5: 回复「✅ XX项目成本监控已启动，X:00起每小时汇报」
Step 6: Daryl说停 → bash start_project_monitor.sh stop --agent xiaofeng
Step 7: 出最终汇总报告
```

---

## 三、工具清单

| 文件 | 路径 | 用途 |
|------|------|------|
| `project_cost.py` | `~/.openclaw/workspace/cost_tracker/` | 数据提取引擎：读取session jsonl，按时间/agent聚合成本 |
| `start_project_monitor.sh` | `~/.openclaw/workspace/cost_tracker/` | 管理脚本：start/stop/status，自动装cron |

### 使用示例

```bash
# 启动
bash start_project_monitor.sh start \
  --agent xiaofeng \
  --project 'Bryson开发' \
  --start '10:30' \
  --hours '12-23'

# 查看状态
bash start_project_monitor.sh status

# 停止
bash start_project_monitor.sh stop --agent xiaofeng
```

---

## 四、流程复盘：5个问题 + 4项改进

### 实战中暴露的问题

| # | 问题 | 根因 | 
|---|------|------|
| 1 | 查错agent目录（bryson→xiaofeng） | agent别名未确认 |
| 2 | 12:00报告发送失败 | openclaw二进制路径写错 |
| 3 | 13:00报告发送失败 | 缺--target参数 |
| 4 | 监控窗口不够（只到20:00） | 未确认Daryl期望窗口 |
| 5 | 无验证机制 | 部署前未测试 |

**根因**：部署前没测试，失败后没报警，全部赖Daryl主动发现。

### 改进措施（已落地）

| 改进 | 实现 |
|------|------|
| 架构：守护进程→系统cron | 更可靠，$0 API成本，进程死不影响 |
| 流程：启动前checklist | 验证agent→测试数据→测试发送→装cron→发确认 |
| 通知：主动确认 | 启动/停止都发消息给Daryl |
| 工具化：参数化脚本 | 一句命令启动，零手动干预 |

---

## 五、关键经验教训

1. **agent名称映射**：Daryl用的英文名（Bryson）≠ 系统agent_id（xiaofeng），启动前必须确认
2. **openclaw路径**：Mac上用homebrew安装的在`/opt/homebrew/bin/openclaw`，不是nvm路径
3. **消息发送参数**：feishu发送必须带`--target user:ou_xxx`，缺了就静默失败
4. **监控窗口**：一定要和Daryl确认到几点，留buffer
5. **测试先行**：部署后立刻验证发送，不等Daryl追问

---

## 六、后续方向

与项目成本归集模型（见 project-cost-allocation-discussion.md）联动：
- 按项目维度聚合，而非按agent
- 支持多agent协同项目（Kitty设计→Bryson开发→Kitty验收）
- session级别的项目标签机制

---

*2026-06-10 | Balance (算点小账) ⚖️ | model: deepseek-v4-pro*
