# 当前活跃任务

> 最后更新: 2026-08-05 13:00 GMT+7

## 🟢 进行中
### 🆕 决策自主环（Decision Loop / Loop Engineering）— 已立项，负责人 Kitty (8/5)
- **项目ID**: decision-loop | 发起: Daryl 8/5 | 负责人/开发权: Kitty (Daryl指定, Bryson移交) | 模型: deepseek-v4-pro
- **定位**: 决策自主层（建在自进化基建L1之上），减少长线项目对管理决策的依赖
- **设计基准**: 「只加机制，不加细节限制」（Daryl 8/5 原则，最高准绳）
- **问题实证**: Bryson 剪辑MVP 三次对齐复盘（含 Daryl 两处纠正）→ 机制缺口五条
- **核心机制四件套**: 决策状态机(decide.py三分类) + 上报必带默认值 + 周度批量审批 + 需求分层前置节点 + 提问质量门禁
- **里程碑 M0→M3 (40-80h)**: M0机制冻结(10-14h) → M1决策自主层工具(12-20h) → M2剪辑MVP试点(16-30h) → M3推广+指标化(8-12h)
- **状态**: 🚀 M0+M1 完成（8/5），M2 剪辑MVP 试点已启动（8/6 Daryl 拍板）
- **M2 进展 (8/6)**: 试点框架 docs/m2_jianji_pilot.md + 账本种子 dec_20260806_001 已落；线框 wf01-wf05 冻结（2必改已核验）；Bryson 已完成 30%（交互方案定稿）→ 开发 v4.0 前端中（60% 节点预计 8-12h 后）
- **待办**: ①M2 试点跟踪（Bryson 60%/90%/100% 汇报节点）②M2 完成后试点报告（决策次数对比/预算/例外）③Bryson 工具链清单（~6h，试点中可搭）
- **文档**: LOOP_ENGINEERING_PLAN.md（详见该文件）

### 🆕 OPC自进化基建L1 — M0+M1+M2 已交付 (8/4) + Balance试点Phase0影子模式 (8/5)
- **⏸️ 汇报节奏调整 (8/7 Daryl指令)**: Phase0 评估报告不用专门汇报，这几天监控着即可；**周日(8/9) Daryl 一次性做「是否全面应用」决策** → 周日汇总时需备好 Phase0 评估结果 + 决策自主环 M2 进度
- **M0 信号捕获** ✅: capture_correction.sh(4类信号) + distill_patterns.py(周度LLM蒸馏) + launchd周日22:00
- **M1 失败模式库** ✅: failure_patterns.json(trigger+embedding) + rules_table.json(4规则) + embed_patterns.py(1536维) + retrieve_patterns.py(三层检索)
- **种子数据**: 4条模式(设计语言/git/搜索/数据来源)，来自Daryl历史纠错
- **回归测试**: 11/11通过 · **commit**: 7bf03311/dfccca86/6175b1ed
- **⚠️ 试点范围**: Self(8/4指令) + Balance Phase0影子模式(8/5批准)；main/balance已回退注入
- **⚠️ 成本红线**: 注入≤500tokens/任务，检索<1s，单任务API$0 → bench_evolution.py周度基准(实测37ms/50tokens/$0)
- **M2 任务级注入** ✅: classify_task.py(三层信号+状态机) + inject_lessons.py(全量/轻量注入) + task_state.json，11/11回归通过
- **🆕 Balance Phase0影子模式 (8/5部署, 测试窗口8/5→8/7)**: shadow_inject.py(只记录不注入+独立shadow状态机+fail-open) + shadow_report.py(周五评估) + 种子库7条(4条Balance域蒸馏/补录+3条共享通用) + rules_table含财务路径口径rule-005 + classify_task补充财务域关键词(做/入账/申报/台账等) + AGENTS.md条款；**评估通过才开Phase1低风险任务**

### Websearch 全面升级 v2.0 — M0+M1+M2+M3 全部完成 ✅ (7/29)
- **M0 基建侧**: 4Agent AGENTS.md 新增搜索强制条款 ✅
- **M1 引擎精简**: SearXNG 5→3引擎(google+ddg+bing)，Brave独立API路由 ✅
- **M2 方法论**: search_methodology.md v2.0（6场景模板+路由表+后处理）✅
- **M3 部署**: 基准测试66.8(原67.0持平)，crontab周度抽检运行中 ✅
- **commit**: 4fae35cb

### 🆕 第二期确定性基建 · OPC运营中枢 (7/25)
- **M1 开发**: 4模块(阻塞扫描/成本预警/新鲜度/搜索质量) ✅
- **M2 集成**: 主脚本集成+测试 ✅
- **M3 部署**: crontab 每日08:00 ✅
- **交付**: `scripts/ops_center/` 6文件 | **状态**: ✅ 已上线
- **commit**: 2dba501c

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

### 🆕 Dashboard M4 · Agent版本变更通知 — 🟡 进行中 (8/4)
- OPC看板Agent卡片增加「约定版本」字段，机制变更时自动通知对应Agent
- Daryl 已推入 In Progress，制定开发计划中

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
### ~~Agent版本变更通知（并入 Dashboard M4）~~ → 🟡 进行中 (8/4 Daryl 推入)

### Daryl 8/5 决策：A7/8/9搁置 + B组取消 + C15已做
- 8月预算调整 / 12G存储清理 / Model Router 提案 → ⚪ 搁置不处理
- 音乐文件/车辆费用/JGL → ❌ 全部取消
- C15 搜索基准 → ✅ 已做（8/5：SearXNG路39.9引擎坍塌 + Brave路65.9持平，报告已归档）
- 🔴 待Daryl确认: Brave接回主搜索路由

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
