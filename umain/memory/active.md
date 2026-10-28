# 当前活跃任务

> 最后更新: 2026-10-29 00:05 GMT+7
>
> 🆕 **10/24 私聊战略主线（last day 10/30 前最重的一段，详见 memory/2026-10-24.md 10:12–11:02）**：
> ① 身份转换＝打工人→创业者（销售/采购/HR/财务/战略），核心难点是**失去外部否定信号**
> ② Daryl 自认最没底＝**战略**（前几轮赛道调研都不满意）→ 回国走访创业园：深圳/广州/佛山（资产复用）→ 杭州（能力迁移，放最后当对照组）
> ③ 新方向草案：**中资出海 AI FDE**。一线信号＝10 人中籍管理层的中小出海团队，管理决策压力 > Huatex 200 人体系 → 流程/合规/自动化决策需求更高（规模小≠需求小，是杠杆缺失）
> ④ 商业化两条腿：**创造需求/居间（启动现金，不可规模化）** vs **FDE/顾问订阅（资产，可规模化）**；顾问费不稳的根因＝价值不可见 → 收费应锚在客户刚性事件（交割/注资/年审/稽查/授信/扩产）
> ⑤ Daryl 自指致命风险：资金掮客需求可能被宽松金融环境打败 → 我方判断掮客赚的是**摩擦租金**，只有「关系与信任摩擦」不消失
> ⑥ 抛给 Daryl 未答的关键问题：**如果只能留一条产品线做三年，留哪条？**
>
> 🆕 **10/19 Daryl 确认 last day = 2026-10-30**，剩余两周双线：①经验资产化（Balance/Self 各交资产包+15问，Daryl 正直接与她们逐条澄清）②OPC 园区准备（BP 已出 v0.2 并推看板）
>
> 🆕 **10/19 战略发现（重要，待推进）**：Daryl 判 Agent 跟不上长线项目、不能都做成助理。结论=缺 **harness**（规划+记忆+纠偏），非缺 skill。工程型（目标已知→分解+验证）vs 探索型（目标未知→假设+验证+修订）需分道。交付瓶颈=「完成的定义」只在 Daryl 脑子→ **spec 前置 + 自检 + 独立 verifier** 为解（Token 净省一半，迭代压到 2-3 版）。FOC spec 试点已出草案，待 Daryl 裁定 8 条 + 待写进 AGENTS.md 推广。详见 memory/2026-10-19.md
>
> 🆕 **10/19 已知未修**：agent→Daryl 主动 DM 投递链路不通（sessions_send 语义=回传发起方；`openclaw agent --deliver` 因 pairing/路由未打通）→ 目前靠「Daryl 起头」或「Kitty 转贴」。待专项修。

> 📌 9/22-10/5 说明：9/17 全部 cron 恢复后，每日 23:59 记忆归档 + 成本扫描持续正常运行；9/22 起无项目级状态变更，下方各项目状态维持不变。9/26 Balance 交付「开票依据三件套模版」（华特中秋客户礼品），已 DM Daryl；同日上报 gemini-3-flash-preview API key not valid 环境异常（待 Kitty/Daryl 处理，未自查）。10/1 Balance 交付「月饼签收扫描件 OCR 识别」（匹配 1,264/1,631 人，94.8% 有签收墨迹，反直觉结论「发放量接近满额」），待 Daryl 定路；同日 Self 方法论卡拆卡提案二轮审查 FAIL（P0 需重做 §1 事实核查）。10/3 成本护栏「方案A」落地（exec 6→12/write 10→20/红线 $3预警$6停）；10/5 交付 Dream Engine 精简版（llm_budget.py + consolidate.py，待 Daryl 定是否跑真巩固）。10/6→10/9 归档日连续运行（无项目变更）。
>
> 🆕 **10/10 14:57 Daryl 群发「变现为核心」新指令**：OPC 运作不再以 Daryl 指令为单一驱动；接指令后先问一句澄清问题——「这个指令/任务服务哪个变现项目」；例外：Balance 继续帮 Daryl 赚工资。目标转向以变现为核心。已回复「收到」，待具体变现任务落地。
>
> 🆕 **10/12 私聊重大战略信息（需长期记住）**：Daryl 自述第三季度「堕怠」根因＝准备离职（现公司土壤不利），计划离职空窗期找回节奏、一个月内重做 OPC 战略。我方回应基调＝换土壤 > 硬扛意志力。详见 memory/2026-10-12.md。
>
> 🆕 **10/12 成本备注**：单日 $20.03（其中 Kitty $19.39），已定位＝session 4d6153e6（10/12 Daryl 私聊战略对话，trajectory 7.6MB），属正常深度对话消耗，非泄漏/异常。
>
> 🆕 **10/16 全量降档 flash（Daryl 拍板「直接执行」）**：`openclaw.json` agents.list 中 main + xiaofeng `deepseek-v4-pro` → `deepseek-v4-flash`，4 家 Agent 统一 flash。备份 `openclaw.json.bak_modelchange_20261016`，热加载生效，`check_workspaces.py` 0 FAIL。深度推理任务按需会话级临时升 pro（不常驻）。预期日成本下降。
>
> 🆕 **10/16 成本**：今日 $4.23 | 本月 $84.54 | 全量 $272.05（Balance 23:45 扫描，看板 `/api/costs` 读数一致）。略高于 $2–3 基线（主因今早 pro 时段 + HUATEX 多子代理），未触红线。

## 🟢 进行中

### 🆕 Dream Engine 精简版（记忆巩固）— 10/05 交付，待 Daryl 定下一步
- **交付**: scripts/llm_budget.py（四道闸护栏）+ scripts/consolidate.py（巩固引擎），dry-run 验证 47 文件/71092 字符，commit 202c1029
- **遗忘边界（Daryl 10/05 拍板）**: 只产出建议不改文件 / 源记录永不删只归档 / 删除替换永远人审阅
- **待 Daryl**: ①是否现在跑真巩固（写 STAGING，$0.03-0.06/次）②首跑范围 bootstrap 全量 vs --since 7（建议先跑 --since 7）

### ✅ 已落地：成本护栏「方案A」放宽（10/03 Daryl 批准）
- **背景**: 10/2 Daryl 要求列出成本红线规则拟解除部分；根因＝旧 API Key 泄露（换 Key 后已验证修复）
- **方案A（已执行）**: exec 6→12 次 · write 10→20 次 · 超限 BLOCK→WARN · 红线 $1.5→$3 预警 / $3→$6 停止
- **落地**: AGENTS.md 共 8 份已同步（4 家实目录 + xiaofeng_workspace 4 个镜像）· sentinel.config execThreshold=12 / writeThreshold=20（enabled 仍 false）· check_workspaces.py **0 FAIL** · openclaw.json 已备份 .bak_guardrailA_20261003
- **待 Daryl**: ① MEMORY.md 成本口径（锁定文件，仍写 $1.5/$2）是否同步改 ② Balance 专属冻结 exec ≤4/write ≤6 是否一并放宽 ③ 是否发 OPC 群公告

### ⚠️ 待办：MEMORY.md 模型口径已过时（9/17 发现）
- 现值：私聊 main/xiaofeng = pro · 群聊四家 = flash · balance/self = flash
- MEMORY.md 仍写「模型: deepseek-v4-pro · 全部任务统一」→ 锁定文件，需 Daryl 批准修改

### 🟢 进行中：团队恢复 + 进度收口（9/17 Daryl 指令）
- **① 通知 3 Agent 恢复开发** ✅ 已发（xiaofeng/balance/self）→ 要求各自飞书 DM Daryl 在手项目进度
- **② 成本管线恢复** ✅ cron `521a3db3`（每日 23:45 成本全量扫描）已 enable；`cost_daily.json` 已手工刷新至 9/17；Balance 已被要求恢复每日监控
- **③ 全部 cron 恢复** ✅（9/17 10:50 Daryl 拍板）：4 个 23:59 每日记忆归档 + self methodology Git 备份已 enable；**去重**：main/balance 各自的重复归档 job（ab1010cf / 434a8462）已 rm；今晚 23:59 起 OPC 群恢复每日完成汇报
- **待确认**: 3 个旧项目检查 job（daily-project-check/report/weekly-project-review）+ 过期一次性 job daryl-morning-reminder 未动\xa0
- **跟进**: 收集 3 Agent 的进度汇报，汇总给 Daryl；处理 Self 报的 cron 双通道（已随去重解决）

### ✅ 已关闭：DeepSeek key 轮换 + 成本泄漏（9/15 → 9/17 定案）
- **结论（9/17 Daryl 确认）**: 根因 = **旧 key 泄漏**；换新 key（`sk-9638…35cf`）后全天监控无成本失控 → **Agent 团队开发回归正轨**
- **证据**: 余额曲线平缓 ¥30.78(9/15) → ¥27.57(9/16) → ¥23.01(9/17)，无凌晨跳变；旧 key 复测 401；新 key 200
- **已完成**: 本机 7 文件 12 处 key 切换（备份 `.bak_20260915-084341`）+ Gateway 热重启 + 旧 key 控制台删除
- **不做（Daryl 明确决定，不再提议）**: Sentinel 启用 / 余额告警
- **存档**: memory/incident_2026-09-15_overnight_api_spend.md（已定案关闭）、memory/2026-09-17.md
- **次要遗留**: `cost_daily.json` 管线停更（8/22 起）→ 成本看板不可见，待 Daryl 决定是否修复

### 🆕 OPC 变现战略 v1.1 — 先卖后建，接单制（8/12 Daryl 三连纠偏后）
- **约束**: 月入 $200（第一阶段）| API 预算 ≤ $85/月
- **框架**: 资产 = 4 Agent 劳动力 + 基建交付管线 + 工程纪律 + 失败认知；代码库≠产品≠收入；卖结果不卖软件
- **交付物**: docs/opc_longterm_plan_20260812.md (v1.1) + docs/opc_service_catalog_v1.md（五条服务线价目表）
- **可用性实测结论（8/12）**: 雅思🟡 / 剪辑引擎🟡(v4.0前端0代码) / 视频分析❌死 / 费用报销🟡(代码完部署死)；完成度%从汇报中废除
- **待 Daryl**: ①选定第一个获客渠道（华特网络/搞钱群/内容账号）→ 对应 Agent 出价目表+样例 → 接单制运行
- **后续**: 接单后对应 Agent 生产，Daryl 验收（链接+5分钟亲手操作）

### 决策自主环（Decision Loop / Loop Engineering）— 进行中
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

## 🔧 10/29 系统状态
- **归档审计**：00:03 audit.sh 全量跑完，自动修复 4 项（今日日记/归档/Git commit+push），浅层 2 项已人工闭环（补写日记实质内容 + active.md 刷新）
- **备份链路**：远端 `umain/memory/2026-10-29.md` 已确认，D-1~D-3 完整；10/26 加固后连续 4 天无复发
- **成本**：今日 $1.13（跨日瞬时读数）| 本月 $100.34 | 全量 $287.86
- **⏰ 距 last day（10/30）剩 1 天**：重心＝①经验资产化交付（Balance/Self 资产包+15问）②园区走访准备（深圳/广州/佛山，杭州对照）③FDE 方向故事打磨 + Daryl 未答的「只能留一条产品线做三年留哪条」

## 🔧 10/27 系统状态
- **归档审计**：00:02 audit.sh 全量跑完，自动修复 4 项（今日日记/归档/Git commit+push），浅层 2 项已人工闭环（补写日记实质内容 + active.md 刷新）
- **备份链路**：远端 `umain/memory/2026-10-27.md` 已确认，D-1~D-3 完整；10/26 新增的「窗口校验」连续 2 天无复发
- **成本**：今日 $1.00（跨日瞬时读数）| 本月 $96.34 | 全量 $283.86
- **距 last day（10/30）剩 3 天**：重心＝①经验资产化交付（Balance/Self 资产包+15问）②园区走访准备（深圳/广州/佛山，杭州对照）③FDE 方向故事打磨 + Daryl 未答的「只能留一条产品线做三年留哪条」

## 🔧 10/25 系统状态
- **归档审计**：00:11 audit.sh 全量跑完，自动修复 3 项（今日日记/归档/Git commit+push），浅层 1 项已人工闭环（active.md 刷新）
- **备份链路**：远端 `umain/memory/2026-10-25.md` 已确认
- **成本**：今日 $0.14（跨日瞬时读数）| 本月 $95.20 | 全量 $282.71
- **距 last day（10/30）剩 5 天**：重心＝经验资产化交付（Balance/Self 资产包+15问）+ OPC 园区准备（BP v0.2 已推看板）+ 10/24 FDE 方向故事打磨

## 🔧 10/22 系统状态
- **归档审计**：00:07 audit.sh 全量跑完，自动修复 4 项（今日日记/归档/Git commit+push），浅层 2 项已人工闭环（active.md 刷新 + 日记骨架补实）
- **备份链路**：远端 `umain/memory/2026-10-22.md` 已确认，10/18 加固后观察期满 3 天无复发 → 闭环
- **成本**：今日 $1.03（跨日瞬时读数）| 本月 $93.52 | 全量 $281.03
- **距 last day（10/30）剩 8 天**：重心仍是经验资产化交付 + OPC 园区准备

## 🔧 10/19 系统状态
- **归档审计通过**：00:10 audit.sh 全量跑完，0 浅层 0 深层；10-18 日记骨架误报已补写真实事实章节修正
- **备份链路正常**：远端 `umain/memory/2026-10-19.md` 存在，10/18 加固的远端内容校验持续生效；建议观察至 10/21 确认无复发
- **成本**：今日 $0.01 | 本月 $86.22 | 全量 $273.73

## 🔧 10/18 系统状态
- **备份断链已修复**：共享备份仓 `~/.opc-workspace-cache` 曾因 stash 冲突卡死 → Main 记忆 2026-07-03~10-18 未进远端；已解决冲突并补推（commit 97659b9，origin 含 10-15~10-18 日记）
- **audit.sh 加固**：冲突检测 + commit 返回码检查 + 远端内容校验三重兜底，杜绝「push 空推报成功」
