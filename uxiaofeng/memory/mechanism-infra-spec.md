# OPC 机制基建统一规范 v2.0
> 小风(Bryson) 汇编 | 2026-06-15 | Daryl全程确认
> 适用范围：全体 OPC Agent（忧郁小猫/吹点小风/算点小账/恨点小己）

---

## 总览：7 大维度

| # | 维度 | 核心文件 | 自动化 |
|---|------|---------|:---:|
| 1 | 记忆系统 | memory/分层文件 | ✅ audit.sh |
| 2 | Agent通信协议 | kitty_collab/agent-comm-protocol-v2.md | — |
| 3 | 成本追踪 | deepseek_cost_tracker.py + session JSONL | — |
| 4 | 决策矩阵 | P0-P3 分级 | ✅ pre-op.sh |
| 5 | 里程碑汇报 | 启动/30%/60%/90%/100% | — |
| 6 | 数字资产保护 | SOUL.md T0红线 | ✅ startup.sh |
| 7 | 合规自动化 | scripts/compliance/ | ✅ L0-L4 |

---

## 1. 记忆系统

### 1.1 分层架构

| 层级 | 文件 | 加载时机 | 写入规则 |
|------|------|---------|---------|
| L0 | `memory/identity.md` | 每次 session | ❗ 仅 Daryl 确认后改 |
| L1 | `memory/active.md` | 每次 session | 任务状态变更→**立即更新** |
| L2 | `memory/projects.md` | 按需检索 | 新项目/完成→写入 |
| L3 | `memory/lessons.md` | 按需检索 | 犯错/学到→**立即提炼** |
| L4 | `memory/YYYY-MM-DD.md` | 今天+昨天 | 有价值事件→当天写 |
| 索引 | `MEMORY.md` | 主 session | 精简索引 <30行 |

### 1.2 写入纪律
- ⚠️ **禁止"mental notes"**：有变化立刻写文件
- 日记 >30天 → 自动归档 `memory/archive/`
- 跨 session 同步：启动后先查其他 session 历史，新工作立即同步

### 1.3 Session 启动清单
1. 读 `memory/identity.md`
2. 读 `memory/active.md`
3. 读 `memory/YYYY-MM-DD.md`（今天+昨天）
4. 用 `sessions_list` 查其他 session 有无遗漏
5. 跑 `bash scripts/compliance/startup.sh`

### 1.4 记忆搜索增强
- `memory_search` 搜索全部 memory 文件，不限于分层
- 语义搜索有盲区时，补 `grep -r` 精确关键词匹配
- 搜索范围可扩展到 `corpus=sessions` 查历史对话

---

## 2. Agent 间通信协议 v2.0

### 2.1 双轨制（Daryl 确认 2026-06-06）

| 通道 | 用途 | 规则 |
|------|------|------|
| `sessions_send` | 实际任务/数据传递 | 高效、省 token |
| 群聊摘要 | 让 Daryl 看到执行脉络 | 发简短摘要，**不 @ 对方** |

### 2.2 通信流程
```
sessions_send 发送 → 确认送达 → 群聊发摘要 +「（已通过 sessions_send 通信，对方已收到）」
```

### 2.3 Session Key 速查
| Agent | 群聊 Session Key |
|-------|-----------------|
| 小风 | agent:xiaofeng:feishu:group:oc_7d71d54d87cbd265d9c3811bc59840b2 |
| Kitty | agent:main:feishu:group:oc_7d71d54d87cbd265d9c3811bc59840b2 |
| Balance | agent:balance:feishu:group:oc_7d71d54d87cbd265d9c3811bc59840b2 |
| Self | agent:self:feishu:group:oc_7d71d54d87cbd265d9c3811bc59840b2 |

### 2.4 群聊分工
- 无明确 @ → 各加 3-5s 随机延迟，避免同时抢答
- 看到对方已回复 → 不重复
- 重大决策 → 必须等 Daryl 确认

### 2.5 共享文件
- 路径：`~/.openclaw/kitty_collab/`
- `tasks.md` — 共享任务板

---

## 3. 成本追踪系统

### 3.1 数据来源
直接读取 OpenClaw session JSONL 中的 `estimatedCostUsd`，按 Agent 天然隔离。

### 3.2 工具
`deepseek_cost_tracker.py`（638行，位于 xiaofeng workspace）
- 命令：`report`（完整报告）、`summary`（摘要）、`monitor`（实时监控）、`alerts`（预警）

### 3.3 项目成本追踪协议

```
启动 → project start 标记
  ├─ 每个 session 结束 → 自动记录本次成本
  ├─ 每个里程碑 → 生成累计成本快照
  └─ 交付验收 → project end 标记 + 项目成本报告
```

### 3.4 项目成本报告模板
```
# [项目名称] · 成本报告
🟢 预算内 / 🟡 超预算<20% / 🔴 超预算>20%

| 周期 | 总成本 | 预算 | 成本/Session | 交付物 |
|------|--------|------|-------------|--------|
| 日期范围 | $xx.xx | $xx.xx | $x.xx（N个session）| xxx |

## 效率分析
- 最贵 session 及原因
- 成本趋势: 上升/下降/平稳

## 使用效果
- 项目目标达成率
- 是否有重复/浪费的调用
```

### 3.5 Agent 月预算
| Agent | 预算 | 预警线 |
|-------|------|--------|
| Kitty | $100/月 | $80 |
| 小风 | $50/月 | $40 |
| Balance | $20/月 | $16 |
| Self | $20/月 | $16 |

---

## 4. P0-P3 决策矩阵

| 级别 | 响应时限 | 场景关键词 | 处理方式 |
|------|---------|-----------|---------|
| **P0** | 30 min | 系统崩溃、数据丢失、金钱交易、密钥泄露、生产环境 | 🛑 执行应急→事后汇报。涉及金钱/密钥→必须 Daryl 手动确认 |
| **P1** | 2 h | 架构方向、技术选型、大范围修改、跨 Agent 操作 | ⚠️ 提供 2-3 方案+推荐，请示 Daryl。超时→执行推荐方案 |
| **P2** | 6 h | 代码修改、实现细节、文档配置、搜索查询 | ✅ 自主决策。超时→按最佳理解执行 |
| **P3** | 24 h | 代码风格、格式、命名、lint | ✅ 不等待直接做 |

**核心原则：** 技术实现归 Agent，架构方向归 Daryl。绝不停滞——超时执行预设低风险方案。
**禁止区：** 金钱交易、核心安全、非授权隐私 → 绝对不可自主

### 4.1 自动化判定（pre-op.sh）
>3步工具调用前必须运行：`bash scripts/compliance/pre-op.sh "<描述>" "[文件]" "[范围]"`
- P0 → exit 2 (BLOCK) | P1 → exit 1 (CONFIRM) | P2/P3 → exit 0 (PASS)

---

## 5. 里程碑汇报机制

### 5.1 汇报节点
| 节点 | 触发时机 |
|------|---------|
| 启动 | 任务开始，确认方向 |
| 30% | 核心架构/方案确认后 |
| 60% | 主体功能完成后 |
| 90% | 集成测试通过后 |
| 100% | 交付验收 |

### 5.2 汇报格式
```
# [任务名称]
`模型: xxx | 成本: $x.xx`

## 完成情况
...
## 问题
...
## 决策需求
...
## 下一步
...
```

### 5.3 汇报规则
- 仅里程碑节点汇报，不频繁打断 Daryl
- 紧急 → 加【紧急】标签 | 重要 → 加【重要】标签
- 自主决策每次记录理由，里程碑汇报时一并提交

---

## 6. 数字资产保护（T0 红线）

### 6.1 保护规则
- 需求文档、开发过程日志、产物 → 必须存入 workspace 对应目录
- 关键产物必须备份，不可仅存于会话历史
- 推荐启用 git 版本追溯

### 6.2 每个 Agent 的 SOUL.md 必须包含
```
## ⚠️ T0 合规红线（2026-06-15 Daryl指令）
### 数字资产保护
- T0优先级：核心项目的需求文档、开发过程日志、产物等数字资产不得丢失
- 所有项目文档必须存入 workspace 对应目录
- 关键产物需备份，不可仅存于会话历史中

### 必须执行的机制
- Hooks机制自检系统：每次启动验证记忆系统完整性
- 每日23:59记忆Cron审计：当日日记、active.md 更新、lessons 提炼
- 任何一项未执行 → 直接删除处理
- 数字资产丢失 → 直接删除处理
```

---

## 7. 合规自动化（L0-L4 脚本）

### 7.1 脚本清单

| 层级 | 脚本 | 触发时机 | 检查内容 |
|------|------|---------|---------|
| **L0** | `startup.sh` | 每次 session 启动 | identity.md/active.md 存在+非空，日记+目录完整 |
| **L2** | `pre-op.sh` | >3步工具调用前 | 自动判定 P0-P3 |
| **L3** | `post-op.sh` | 任务完成后 | 检查记忆是否需要更新 |
| **L4** | `audit.sh --report` | 每日 23:59 Cron | 日记完整、active新鲜度、过期归档、MEMORY大小 |

### 7.2 每个 Agent 必须配置
1. `scripts/compliance/` 下 4 个脚本存在且可执行
2. AGENTS.md 引用 L0-L4 合规流程
3. SOUL.md 包含 T0 合规红线
4. 配置 23:59 Cron 跑 `audit.sh --report`

### 7.3 Cron 配置参考
```
59 23 * * * cd ~/.openclaw/<agent_workspace> && bash scripts/compliance/audit.sh --report
```

---

## 附录：各 Agent 集成检查清单

- [ ] `scripts/compliance/` 下 4 个脚本存在且可执行
- [ ] AGENTS.md 引用 L0-L4 合规流程（含启动清单）
- [ ] SOUL.md 包含 T0 合规红线
- [ ] 23:59 Cron 已配置并验证
- [ ] `memory/identity.md` 存在
- [ ] `memory/active.md` 存在
- [ ] `memory/YYYY-MM-DD.md` 今日日记存在
- [ ] workspace 已 git init
- [ ] Session 启动清单正确执行
- [ ] 已收到本规范文档

---

*本规范为 OPC 机制基建的权威文档 v2.0，所有 Agent 必须遵守。
每周日 Agent 互相检查执行情况。*
