# 统一规范文档 & Hooks 机制自检系统

> 版本: v1.0 | 创建: 2026-06-14 | 最后更新: 2026-06-17
> 负责人: Bryson（吹点小风）

## 一、系统概述

参考 Claude Code 四层架构，实现了一套自建的合规执行系统，通过 Shell 脚本实现等效的合规闭环，确保数字资产安全、记忆系统完整、工作流程可审计。

## 二、四层合规架构

### L0 · 启动验证 (`scripts/compliance/startup.sh`)
**触发时机**: 每次 Session 启动时

**检查项**:
- ✅ identity.md 存在且非空
- ✅ active.md 存在且非空
- ✅ workflow-rules.md 存在且非空
- ✅ AGENTS.md 存在且非空
- ✅ 今日日记存在
- ✅ active.md 新鲜度（<24h）
- ✅ 目录结构完整（memory/、scripts/compliance/）
- ✅ 所有合规脚本就绪

**输出**: `memory/compliance-status.json`（含 pass/issue 清单）

**失败处理**: 有 error 必须先修复再继续工作

---

### L1 · 模型分级路由 (`memory/model-routing.md`)
**触发时机**: 按任务复杂度自动选择

| 模型 | 适用场景 | Token 成本 |
|------|---------|-----------|
| DeepSeek V2.5 | 日常对话、简单查询 | 极低 |
| DeepSeek V3 | 代码生成、中等复杂度 | 低 |
| DeepSeek V4 Pro | 复杂架构、深度分析 | 中等 |

---

### L2 · 操作前分级 (`scripts/compliance/pre-op.sh`)
**触发时机**: 涉及 >3 步工具调用时必须先跑

**分级标准**:
| 级别 | 定义 | 处理方式 |
|------|------|---------|
| P0 | 删除/销毁/资金操作 | BLOCK → 必须请示 Daryl |
| P1 | 修改核心配置/外部发送 | CONFIRM → 提供方案后请示 |
| P2 | 创建/修改项目文件 | PASS → 自主执行 |
| P3 | 只读/查询/搜索 | PASS → 自主执行 |

**用法**: `bash scripts/compliance/pre-op.sh "<操作描述>" "[涉及文件]" "[影响范围]"`

---

### L3 · 操作后验证 (`scripts/compliance/post-op.sh`)
**触发时机**: 任务完成时

**检查项**:
- active.md 是否需要更新（有新任务/状态变更）
- 日记是否需要写入（有值得记录的事件）
- lessons.md 是否需要提炼（犯错了或学了新东西）
- 关键文件完整性（0-5分评分）

**用法**: `bash scripts/compliance/post-op.sh "<任务描述>" "[产出文件]"`

---

### L4 · 收尾自检 + 每日审计

#### 4a. 收尾自检（每次回复涉及实质工作后）
自问 3 个问题:
1. 产生了新任务/新决策/状态变更？→ 更新 `memory/active.md`
2. 有值得记录的事件或成果？→ 更新 `memory/YYYY-MM-DD.md`
3. 犯了错或学到了新东西？→ 更新 `memory/lessons.md`

#### 4b. 每日 23:59 Cron 兜底审计 (`scripts/compliance/audit-cron.sh`)
**触发**: launchd 定时任务 + 系统 cron

**检查项**:
| # | 检查项 | 自动修复 |
|---|--------|---------|
| 1 | 今日日记存在 | ❌ |
| 2 | 昨天日记存在 | ❌ |
| 3 | active.md 新鲜度 <24h | ❌ |
| 4 | lessons.md 覆盖 | ❌ |
| 5 | >30天日记归档 | ✅ 自动移入 archive/ |
| 6 | MEMORY.md <40行 | ❌ |
| 7 | Git pull + commit + push | ✅ 自动执行 |

**完成后**: 自动发送汇报到 OPC 群聊

---

## 三、Hooks 机制自检系统

### 与 OpenClaw 内置 Hooks 的关系

| 层级 | OpenClaw 内置 | 自建合规脚本 |
|------|-------------|-------------|
| session-memory hook | 自动保存对话摘要 | startup.sh 验证初始状态 |
| command-logger hook | 自动记录命令执行 | audit.sh 验证日志完整性 |
| - | - | pre-op.sh 风险分级拦截 |
| - | - | post-op.sh 任务后验证 |

**结论**: 自建合规脚本是对 OpenClaw 内置 Hooks 的**补充和强化**，提供内置 Hooks 不具备的：风险分级拦截、操作后验证、定时审计、自动归档功能。

### 合规状态文件

| 文件 | 用途 |
|------|------|
| `memory/compliance-status.json` | L0 启动验证结果 |
| `memory/compliance-audit.jsonl` | L4 每日审计日志（JSONL） |

---

## 四、记忆系统架构

### 分层设计

| 层级 | 文件 | 加载时机 | 职责 |
|------|------|---------|------|
| L0-身份 | `memory/identity.md` | 每次 session | 身份、用户、沟通规则 |
| L1-活跃 | `memory/active.md` | 每次 session | 进行中任务、待办事项 |
| L2-项目 | `memory/projects.md` | 按需检索 | 项目归档索引 |
| L3-经验 | `memory/lessons.md` | 按需检索 | 经验教训精华 |
| L4-日记 | `memory/YYYY-MM-DD.md` | 今天+昨天 | 日常事件记录 |
| 索引 | `MEMORY.md` | 主 session | 精简索引，<30行 |

### 跨 Session 同步

每次新 Session 启动后:
1. 用 `sessions_list` 列出其他可见 session
2. 取最近 1-2 天的其他 session 历史
3. 检查是否有未写入 memory/ 的新工作
4. 如有发现，立即更新 `memory/active.md` 和日记

---

## 五、数字资产保护（T0 红线）

- 核心项目的需求文档、开发过程日志、产物等数字资产不得丢失
- 所有项目文档必须存入 workspace 对应目录
- 关键产物需备份到 Git 仓库（opc-workspace）
- 每日 23:59 自动 Git commit + push

---

## 六、Git 仓库自动化

### 仓库结构
```
opc-workspace/
├── Bryson/          # 吹点小风
│   ├── video-analyzer/
│   ├── voice-mvp/
│   ├── compliance/  ← 合规系统文档
│   ├── memory/      ← 记忆文件
│   └── ...
├── Kitty/           # 主 Agent
├── Balance/         # 成本控制
├── Self/            # 知识管理
└── Shared/          # 共享资源
```

### 自动化流程
- **每日 23:59**: `git pull --rebase && git add -A && git commit -m "auto: 每日记忆备份 YYYY-MM-DD" && git push`
- **launchd 调度**: `~/Library/LaunchAgents/com.xiaofeng.audit-cron.plist`
- **日志**: `/tmp/audit-cron.log`

---

## 七、部署清单

### 文件清单
| 文件 | 状态 |
|------|------|
| `scripts/compliance/startup.sh` | ✅ |
| `scripts/compliance/pre-op.sh` | ✅ |
| `scripts/compliance/post-op.sh` | ✅ |
| `scripts/compliance/audit.sh` | ✅ |
| `scripts/compliance/audit-cron.sh` | ✅ |
| `memory/compliance-status.json` | ✅ (自动生成) |
| `memory/compliance-audit.jsonl` | ✅ (自动生成) |
| `memory/model-routing.md` | ✅ |
| `memory/workflow-rules.md` | ✅ |
| `memory/identity.md` | ✅ |
| `memory/active.md` | ✅ |
| `memory/lessons.md` | ✅ |
| `memory/projects.md` | ✅ |
| `AGENTS.md` | ✅ |
| `SOUL.md` | ✅ |
| `HEARTBEAT.md` | ✅ |
| `REPO_RULES.md` | ✅ |

### Cron / launchd
| 任务 | 调度方式 | 状态 |
|------|---------|------|
| 23:59 记忆审计 + Git 备份 + 群聊汇报 | launchd | ✅ |
| 07:20 涂软膏提醒 | crontab | ✅ |
| 20:00 花青素提醒 | crontab | ✅ |
| 23:00 睡前准备提醒 | crontab | ✅ |
| 23:30 确认就寝提醒 | crontab | ✅ |
