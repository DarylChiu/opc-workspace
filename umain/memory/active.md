# 当前活跃任务

> 最后更新: 2026-07-25 00:03 GMT+7

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
- **cost_daily.json路径修正**: ✅ 7/19 Balance已修复

### Agent自进化基建 — ⚪ 暂停 (7/21 Daryl指令)
- **全部暂停**: 项目整体暂停，不再推进任何自进化相关开发
- **GEPA禁令**: GEPA类项目（提示自动进化/模型自我优化）严禁再开发
- **保留物**: SAGE Checker + Reflexion 反思机制仍可用（非自进化，仅校验用途）
- **调研文档**: memory/research_agent_self_evolution.md（归档参考）

### OPC Dashboard v1.5 → v1.6 — 运行中
- **地址**: http://localhost:8765
- **当前版本**: v1.6 · M3 项目总线集成完成 ✅ (commit: 690decf)
- **M3 完成**: 项目总线面板 + 成本项目拆分 + 产物项目分组
- **管理**: `cd /Users/zhaoyuzhao/WorkBuddy/Claw/opc-dashboard && bash manage.sh {start|stop|restart|status|logs}`

## ✅ 已完成
### Maker-Checker 审查协议 — Self试点 ✅ (7/21 上线)
- **范围**: 仅 Self(恨点小己)，其他Agent不动
- **交付**: `scripts/evolution/reviewer.md` (对抗性审查员prompt) + AGENTS.md/EVEVOLUTION.md 更新
- **流程**: Self起草 → spawn审查子Agent(Gemini Flash) → 三维打分 → PASS通过/FAIL修改重审(最多2轮)

### 生活提醒 crontab 安装 (7/15)
- crontab 已安装并验证通过 ✅，4 个生活提醒 (07:20/20:00/23:00/23:30) + 审计 + 看门狗 + 项目通知均已就位

### 记忆系统v3 cron 安装 (7/15)
- crontab 安装完成 ✅，7/15 起 07:00/13:00/19:00 正常触发

### 记忆系统v3 — project文件开发 (7/6)
- 模板+API+Cron 全部完成 ✅

### OPC看板持久化修复 (7/6)
- Agent 状态面板：30s→30min 刷新 + 磁盘持久化 ✅
- 成本仪表盘：启动加载快照 + 过期自动刷新 ✅

## 🔵 待办
### Agent版本变更通知（并入 Dashboard M4）
- OPC看板Agent卡片增加「约定版本」字段
- 机制变更时自动通知对应Agent

### Self · Daryl 决策阻塞项 (7/24)
- OPC看板方法论卡片集成方向确认
- 2张卡片审核（胭脂扣/VAS-FDI）
- 心理学域子分类确认
- 树叶收集剩余5片落盘确认
- ACCA Vault深度验收

### Balance · Daryl 审阅待办 (7/24)
- 应付采购入账SOP v2.0 审阅

### Xiaofeng · 等待 Daryl 提供文件 (7/24)
- 404Hz/Sova1 "I NEED YOU" 音乐文件（QQ音乐下载）

## ⚪ 搁置
### Sentinel 合规哨兵 v1.0 — 暂停
- **原因**: Daryl与Bryson讨论后认为当前方案风险较大，先搁置
- **状态**: 插件配置保留但未激活
