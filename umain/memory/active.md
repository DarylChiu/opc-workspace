# 当前活跃任务

> 最后更新: 2026-07-21 10:30 GMT+7

## 🟢 进行中
### SearXNG搜索质量迭代 — M1+M2+P0+P1 已交付 (7/17)
- **M1 SearXNG修复**: Brave API上线 + 6引擎精简 ✅
- **M2 子代理中断协议**: 4Agent config+AGENTS.md 更新 ✅
- **P0 自动重启**: keepalive.sh + launchd 守护 ✅
- **P1 搜索方法论**: methodology.md + 4Agent同步 ✅
- **验收状态**: 7/18 Daryl 验收通过，基线报告已提交
- **归档**: 任务闭环

### 基建长线任务 — M1+M2+M3 全部完成 ✅ (7/18)
- **M1 成本根因**: Dashboard ↔ Balance 数据口径统一，Balance台账接入Dashboard API ✅
- **M2 搜索基准**: 39条基准query + Python自动评分器 + 基线均分67.0 + weekly_check脚本 ✅
- **M3 trace协议**: verify_trace.sh + README.md + Balance/Xiaofeng/Self 三个Agent AGENTS.md 接入trace条款 ✅
- **交付**: memory/subagent_runs/infra_longline_20260718/ 完整trace链路
- **遗留**: crontab周度抽检安装待手动操作（macOS非交互式权限阻塞）
- **cost_daily.json路径修正**: ✅ 7/19 Balance已修复，generate_cost_daily.py 输出从废弃死副本改为 ~/WorkBuddy/Claw/opc-dashboard/data/cost_daily.json

### Agent自进化基建 — ⚪ 暂停 (7/21 Daryl指令)
- **全部暂停**: 项目整体暂停，不再推进任何自进化相关开发
- **GEPA禁令**: GEPA类项目（提示自动进化/模型自我优化）严禁再开发
- **保留物**: SAGE Checker + Reflexion 反思机制仍可用（非自进化，仅校验用途）
- **调研文档**: memory/research_agent_self_evolution.md（归档参考）
- **教训**: 基建应聚焦效率和质量提升，不好高骛远

### OPC Dashboard v1.5 → v1.6 — 运行中
- **地址**: http://localhost:8765
- **当前版本**: v1.6 · M3 项目总线集成完成 ✅ (commit: 690decf)
- **M3 完成**: 项目总线面板 + 成本项目拆分 + 产物项目分组
- **管理**: `cd /Users/zhaoyuzhao/WorkBuddy/Claw/opc-dashboard && bash manage.sh {start|stop|restart|status|logs}`

### Maker-Checker 审查协议 — Self试点 ✅ (7/21 上线)
- **范围**: 仅 Self(恨点小己)，其他Agent不动
- **交付**: `scripts/evolution/reviewer.md` (对抗性审查员prompt) + AGENTS.md/EVEVOLUTION.md 更新
- **流程**: Self起草 → spawn审查子Agent(Gemini Flash) → 三维打分 → PASS通过/FAIL修改重审(最多2轮)
- **与SAGE Checker关系**: 重要交付先Checker快速自检再Maker-Checker深度审查，轻量交付仅Checker
- **Git**: workspace-self commit e72722d

## ✅ 已完成
### 生活提醒 crontab 安装 (7/15)
- crontab 已安装并验证通过 ✅，4 个生活提醒 (07:20/20:00/23:00/23:30) + 审计 + 看门狗 + 项目通知均已就位

### 记忆系统v3 cron 安装 (7/15)
- crontab 安装完成 ✅，7/15 起 07:00/13:00/19:00 正常触发（见 /tmp/project_cron.log）

### 记忆系统v3 — project文件开发 (7/6)
- 模板+API+Cron 全部完成 ✅
- project_main/xiaofeng/Balance/Self.md 创建 ✅
- GET /api/projects/milestones 上线 ✅
- Agent 群内通知已发送 ✅

### OPC看板持久化修复 (7/6)
- Agent 状态面板：30s→30min 刷新 + 磁盘持久化 ✅
- 成本仪表盘：启动加载快照 + 过期自动刷新 ✅
- 任务数据源：CLI→active.md ✅

### OPC看板 v1.4 (7/5)
- 主次优先级视觉分层 ✅
- Bryson 雅思陪练产物补全 ✅
- symlink 重复清理 ✅

### M2 成本仪表盘验收 (7/5)
- 柱状图+饼图布局、字体对比度 ✅
- DeepSeek V4 Pro 定价修正 ✅

### M2 Workflow可视化编辑器验收 (7/5)
- 交互协议 v1.0 ✅

### M2 Agent状态面板验收 (7/4)
- WebSocket + 飞书DM + 实时推送 ✅

## 🔵 待办
### Agent版本变更通知（并入 Dashboard M4）
- OPC看板Agent卡片增加「约定版本」字段
- 机制变更时自动通知对应Agent

## ⚪ 搁置
### Sentinel 合规哨兵 v1.0 — 暂停
- **原因**: Daryl与Bryson讨论后认为当前方案风险较大，先搁置
- **状态**: 插件配置保留但未激活，无需Gateway重启
- **参考**: `plugins.entries.sentinel.config` in `openclaw.json`
