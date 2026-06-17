# Memory System — OPC 团队记忆架构

## L0-L4 分层架构

| 层级 | 文件 | 职责 | 写入规则 |
|------|------|------|---------|
| L0 | `memory/identity.md` | 身份、沟通规则 | 仅 Daryl 确认后改 |
| L1 | `memory/active.md` | 进行中任务、待办 | 状态变更立即更新 |
| L2 | `memory/projects.md` | 项目归档索引 | 新项目/完成时写入 |
| L3 | `memory/lessons.md` | 经验教训精华 | 犯错/学到立即提炼 |
| L4 | `memory/YYYY-MM-DD.md` | 日常事件 | 有价值事件当天写 |
| 索引 | `MEMORY.md` | 精简索引 <30行 | 不放大段内容 |

## 合规脚本 (L0-L4)

| 脚本 | 触发时机 | 功能 |
|------|---------|------|
| `startup.sh` | 每次 session 启动 | 验证记忆系统完整性 |
| `pre-op.sh` | >3步工具调用前 | 自动判定 P0-P3 危险等级 |
| `post-op.sh` | 任务完成后 | 检查日记/active/lessons 更新 |
| `audit.sh --report` | 每日 23:59 Cron | 日记完整性、归档、MEMORY.md 大小 |

## 日记规范
- 格式：YYYY-MM-DD.md
- >30天自动归档到 memory/archive/
- 禁止"mental notes"，有变化立刻写文件

## 相关规范
OPC 机制基建规范 v2.0（/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/memory/mechanism-infra-spec.md）
