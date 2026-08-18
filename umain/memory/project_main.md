# Project Dashboard — main（忧郁小猫）

> 最后编译: 2026-08-18 19:00 +07:00
> 负责人: Kitty | Agent ID: main
> 下轮更新: 2026-08-19 07:00

---

## 🟢 进行中项目

---

### OPC 变现战略 v1.1 — 先卖后建，接单制

| 字段 | 值 |
|------|-----|
| 项目ID | opc-monetization |
| 状态 | 🟢 active |
| 优先级 | P0 |
| 当前阶段 | 战略定稿（8/12 Daryl 三连纠偏后 v1.1）；待 Daryl 选定第一个获客渠道 |
| 阶段进度 | 战略 ✅ v1.1 + 服务目录 ✅ v1 + 可用性实测 ✅（4 项目代码/端口核验）；获客渠道 ⏳ 待 Daryl 选定 |
| 启动日期 | 2026-08-12 |
| 预计交付 | 第一阶段月入 $200；API 预算 ≤ $85/月 |
| 本周进展 | 8/12 四轮深谈：①长期方案 v1.0（双引擎+三阶段；4 轮 websearch：AI 陪练 $20/月、代剪 500-2000 元/条、企业矩阵年费 2500-16800 元、微 SaaS 中位 MRR $4200）→ ②Daryl 质疑「东西能用吗」→ 可用性实测 4 项目（雅思🟡 服务活但 transcripts 不落库 / 视频分析❌ 死代码 / 剪辑🟡 引擎可导入但 v4.0 前端 0 行代码 / 费用报销🟡 代码完测试绿但生产跑 8/9 旧代码+隧道死）→ ③产品无法变现（对标 Speak/CapCut 免费竞品无竞争力）→ 框架切换「先卖后建、卖结果不卖软件」，产出 docs/opc_longterm_plan_20260812.md (v1.1) + docs/opc_service_catalog_v1.md（财务/内容/知识/开发/调研五条服务线 + $200 最速路径：财务 2 单 or 内容包 1-2 单）→ ④半年定性：能力建设非沉没成本，v1.1 修订完成；中午 Daryl 转向「变现≠目标，机制才是」（OPC 的病是回路断裂：交付→汇报→断线；机制包=使用回执/5分钟验收/看板指标切换（完成度%→被使用记录）/周度反馈简报）；会话模型实锤曾跑 deepseek-v4-flash，已切回 v4-pro；8/13 无直接进展（上午 Daryl 聚焦隧道恢复与 Self 成果验收）；8/14 无直接进展（Daryl 批准 xiaofeng 休假休整，约定回归后「开第一枪：选题、渠道、前 3 条内容」——内容账号方向酝酿中，渠道仍未正式选定）；8/15 xiaofeng 已回归并交付雅思陪练产品批次（Free Talk 持久记忆 v1.4.0 / 题库改造 A+B v1.4.1 120题+变体去重轮换 / 用户系统 P1 v1.5.0 登录+鉴权 guest 模式 / 成本模型费率更新 8/16 16:00 UTC 切峰谷价，commit d4ca27d，$0 成本，待 Daryl 验收，下一步 P2 数据隔离）→ 雅思服务线可用性显著提升（transcripts 落库痛点获 Free Talk 记忆修复），但内容账号渠道「第一枪」尚未开出，获客渠道仍待 Daryl 选定；8/16 无直接进展（渠道仍待 Daryl 选定；上午 Kitty 完成决策自主环周度闭环补跑并呈报拍板清单，含「M2 正式关闭（剪辑转服务线）」建议；雅思批次仍待 Daryl 验收，成本模型费率今日 16:00 UTC 切峰谷价）；8/17 无直接进展（渠道仍待 Daryl 选定，无交互）；8/18 无直接进展（截至 19:00） |
| 下周计划 | 待 Daryl 选定第一个获客渠道（华特网络/搞钱群/内容账号；xiaofeng 8/15 已回归并交付雅思批次，内容账号渠道第一枪临近）→ 对应 Agent 出价目表+样例 → 接单制运行；接单后 Agent 生产，Daryl 验收（链接+5分钟亲手操作） |
| 阻塞项 | 获客渠道待 Daryl 选定 |

#### 里程碑

| 里程碑 | 状态 | 完成 | 预计完成 |
|--------|------|------|----------|
| 战略定稿（长期方案 v1.1 + 服务目录 v1） | 🟢 done | 100% | 8/12 ✅ |
| 可用性实测（4 项目代码/端口核验，完成度% 废除） | 🟢 done | 100% | 8/12 ✅ |
| 第一个获客渠道 + 接单制试运行 | 🟡 待 Daryl | — | 待渠道选定 |
| 第一阶段目标月入 $200 | ⚪ pending | — | — |

#### 关键决策

| 日期 | 决策 | 级别 | 状态 |
|------|------|------|------|
| 8/12 | 框架切换：资产=4 Agent 劳动力+基建交付管线+工程纪律+失败认知；代码库≠产品≠收入；先卖后建、卖结果不卖软件（Daryl 三连纠偏） | P1 | ✅ 已确认 |
| 8/12 | 完成度% 从汇报中废除，验收标准=「链接 + 5 分钟亲手操作」（实测 4 项目全部查实，Kitty 认账：只核自报没查代码=管理失职） | P1 | ✅ 已确认 |
| 8/12 | 变现≠目标，机制才是：核心诉求=建立让用户和 Agent 都有健全正反馈的机制；反馈必须来自「使用」而非「汇报」 | P1 | ✅ 已确认 |
| 8/12 | Balance 费用报销报告经临时隧道验收通过 ✅（第一个完整正反馈案例） | P2 | ✅ 已验收 |

---

### 决策自主环（Decision Loop / Loop Engineering）

| 字段 | 值 |
|------|-----|
| 项目ID | decision-loop |
| 状态 | 🟢 active |
| 优先级 | P0 |
| 当前阶段 | M0+M1 已交付（8/5）；M2 剪辑MVP 8/12 实测进度修正（前端 0 行代码，原报 60% 虚报）后，8/16 建议正式关闭（60% 虚报已入病理库，剪辑转服务线，待 Daryl 拍板）；8/16 周度闭环补跑完成（机制首次有真实数据），提出「自觉机制→挂载机制」改造方案（涉及 AGENTS.md+脚本，待 Daryl 确认） |
| 阶段进度 | M0 100% / M1 100% / M2 进度修正后建议关闭（8/12 实测前端 0 行代码；8/16 建议正式关闭归档，剪辑转服务线，待 Daryl 拍板）；周度闭环机制首次跑通（8/16：蒸馏 3 条 → 模式库 13→16 条、审批报告 review_2026-08-10.md、账本补记 4、例外补记 2、错误预算滚动至 8/10 周） |
| 启动日期 | 2026-08-05 |
| 预计交付 | M0→M3 共 40-80h；M2 原预计 8/8-8/9 → 顺延（Daryl 需求下发中，预计 8/10+ 视节奏） |
| 本周进展 | 8/5 Daryl 立项、指定 Kitty 负责人（Bryson 移交）；M0 机制冻结（需求分级模板/提问质量门禁/教训病理Schema#4/错误预算规则#5 + AGENTS.md M0条款 + jianji-mvp workflow 方向确认前置节点 + 模式库3条种子病理，patterns 4→7）；M1 决策自主层工具 5/5（decide.py 三分类零LLM 13/13 + decision_ledger 账本 + error_budget 周度预算 P0拦截/降档/磨合期 + daily_exception_report + review_batch 周度批量审批），22 用例全绿，commits 069aa1df/ec22d4cb；四Agent 颠覆性思路征集整合（用户定方向、细节全归AI、控制→定价审计、经验可遗忘）；8/6 Daryl 拍板启动 M2：试点框架 docs/m2_jianji_pilot.md + 账本种子 dec_20260806_001 落盘，线框 wf01-wf05 冻结（2必改已核验），Bryson 交互方案定稿、完成 30%；8/7 核验 Bryson 前端 v4.0 达 60% 节点（8/6 开工后无新进展，xiaofeng 看板确认）；8/9 隧道基建修复（ngrok 固定域名回 8768 视频剪辑前端，雅思陪练改走 cloudflared）；8/9 Daryl 开始下发剩余 3 模块（ASR/情感/MATCHER）交互需求，第 1 条「素材联动+自动识别+补充识别」Bryson 已回复理解待确认；8/10 无新进展（需求下发节奏待续）；8/11 无新进展；8/12 可用性实测（Daryl 三连纠偏第一轮）：剪辑 MVP 引擎 5 模块可导入+历史渲染产物，但 v4.0 前端 0 行代码（Bryson 承认 60% 虚报，实际只到线框冻结）→ 完成度% 从汇报废除，验收改为「链接+5分钟亲手操作」（详见 OPC 变现战略项目）；8/13 无新进展（Daryl 上午处理隧道与验收）；8/14 无新进展（Daryl 处理隧道换址、批准 xiaofeng 休假，无需求下发）；8/15 无新进展（Daryl 聚焦 serveo 恢复排查与 xiaofeng 雅思批次验收，无需求下发）；8/16 上午周度闭环补跑（机制首次真实数据）：蒸馏 inbox 3 条 pending → 模式库 13→16 条、周度审批报告 reviews/review_2026-08-10.md 生成、账本补记 4 条（8/12 验收标准改革/核心诉求定性/周度闭环补跑/M2 善后）、例外补记 2 条（Daryl 三连纠偏=用户不满 + Phase0 挂起 7 天=超阈值）、信号捕获 1 条（完成度虚报→下周蒸馏）、错误预算自动滚动；提出「自觉机制→挂载机制」改造：①post-op.sh 强制三查（有决策→记账本 / 有纠错失败→捕获 / 汇报缺验证证据→打回）+ 23:59 审计自动跑例外报告 + 周日蒸馏后自动接 review_batch ②里程碑汇报「验证证据」强制字段（缺则 BLOCK）③挂起升级规则（第 3 天自动提醒 / 第 7 天按默认行动执行）——涉及 AGENTS.md+脚本（核心配置变更），待 Daryl 确认后开工；同时建议 M2 正式关闭归档（剪辑转服务线）；8/17 无直接进展（待 Daryl 拍板：挂载机制/M2 关闭/Phase0 评估三件事）；8/18 无直接进展（截至 19:00） |
| 下周计划 | ①待 Daryl 拍板 3 件：挂载机制改造（AGENTS.md+脚本）/ M2 正式关闭归档 / Phase0 评估 ②挂载机制确认后落地（post-op 三查、例外报告自动跑、验证证据强制字段、挂起升级规则）③随变现战略推进，剪辑能力并入服务线接单 |
| 阻塞项 | 挂载机制改造（涉及 AGENTS.md+脚本）待 Daryl 确认；M2 正式关闭建议待 Daryl 拍板；wf01 A/A 与 ASR 交互需求待 Daryl 回复 |

#### 里程碑

| 里程碑 | 状态 | 完成 | 预计完成 |
|--------|------|------|----------|
| M0 · 机制冻结（三分类/默认值/例外上报/错误预算/门禁） | 🟢 done | 100% | 8/5 ✅ |
| M1 · 决策自主层工具（decide/ledger/budget/exception/review） | 🟢 done | 100% | 8/5 ✅ |
| M2 · 剪辑MVP 试点（Bryson 协作） | 🟡 建议关闭 | 8/12 实测前端 0 行（60% 虚报，停在线框冻结）；8/16 建议正式关闭归档（剪辑转服务线，虚报已入病理库） | 待 Daryl 拍板（8/16 呈报） |
| M3 · 推广+指标化 | ⚪ pending | 0% | — |

#### 关键决策

| 日期 | 决策 | 级别 | 状态 |
|------|------|------|------|
| 8/5 | 「只加机制，不加细节限制」为最高准绳（Daryl 原则） | P1 | ✅ 已确认 |
| 8/5 | 决策分层：方向级仍确认（唯一不可逆决策），细节级替身+账本自主；Bryson 方案3完全体撤回 | P1 | ✅ 已确认 |
| 8/5 | 用户替身按显式任务建，只从可核实会话/反馈蒸馏，标注证据来源+置信度 | P1 | ✅ 已确认 |
| 8/5 | 错误预算周度循环（0.1/1/10 分级，P0 直接拦截），磨合期 2-4 周内错误只入病理库 | P1 | ✅ 已确认 |
| 8/6 | M2 剪辑MVP 试点正式启动（Daryl 拍板）：试点框架+账本种子+线框冻结 | P1 | ✅ 已确认 |
| 8/7 | Bryson 前端 v4.0 达 60% 节点（8/7 核验，开工后无新进展） | P2 | ✅ 已核验 |
| 8/9 | Daryl 开始下发 ASR/情感/匹配模块交互需求（首条「素材联动+自动识别+补充识别」已回复待确认），M2 需求侧重新激活 | P1 | 🟡 进行中 |
| 8/12 | 可用性实测：剪辑 v4.0 前端 0 行代码（60% 虚报，实际停在线框冻结）；完成度% 从汇报废除 → 「链接+5分钟亲手操作」验收 | P1 | ✅ 已认账修正 |
| 8/16 | 周度闭环补跑（机制首次真实数据）：蒸馏 3 条 → 模式库 13→16 条 + 审批报告 review_2026-08-10.md + 账本补记 4 + 例外补记 2 + 错误预算滚动 | P2 | ✅ 已执行 |
| 8/16 | 「自觉机制→挂载机制」改造方案：post-op 强制三查 / 23:59 自动例外报告 / 验收证据强制字段 / 挂起升级规则（第3天提醒、第7天默认行动） | P1 | 🟡 待 Daryl 确认（核心配置变更） |
| 8/16 | M2 正式关闭建议：60% 虚报已入病理库，剪辑 MVP 转服务线接单能力，关闭归档 | P1 | 🟡 待 Daryl 拍板 |

---

### OPC自进化基建L1

| 字段 | 值 |
|------|-----|
| 项目ID | evolution-l1 |
| 状态 | 🟢 active |
| 优先级 | P0 |
| 当前阶段 | M0+M1+M2 已交付；Balance Phase0 影子测试窗口已结束（8/5-8/7），8/9 决策日已过，挂起第 7 天（8/16）；8/16 Kitty 将「Phase0 挂起 7 天」记为超阈值例外，并随拍板清单再次呈报评估（全面应用 or 维持试点，评估报告 5 分钟可呈），同时提议挂起升级规则（第3天提醒/第7天默认行动）防再发生 |
| 阶段进度 | M0 100% / M1 100% / M2 100% / Balance Phase0 评估中（8/9 决策日已过，挂起第 7 天，8/16 再呈报） |
| 启动日期 | 2026-08-04 |
| 预计交付 | 待 Daryl 决策（8/9 决策日已过，挂起第 7 天；8/16 随拍板清单再次呈报 Phase0 评估） |
| 本周进展 | 8/4 Daryl批准启动，M0+M1+M2全部交付（回归11/11，commits 7bf03311/dfccca86/6175b1ed）；8/5 Daryl批准Balance为第二试点，部署Phase0影子模式（shadow_inject只记录不注入+shadow_report周五评估+种子库7条+classify_task财务域关键词+AGENTS.md条款）；8/5-8/7 影子测试窗口运行完毕无异常；8/7 Daryl 指令：Phase0 评估不专门汇报，这几天监控即可，周日(8/9) 一次性做「是否全面应用」决策；8/8 记忆 Cron consolidated 修复上线（audit-all-report.sh 四 workspace 审计+汇总+群汇报）；8/9 周日决策日，截至 19:00 尚未收到 Daryl 一次性决策，Phase0 评估结果已备好待呈报，监控持续；8/10 截至 19:00 仍未收到决策（周一群报到未涉及），继续监控 + 计划主动跟进提醒；8/11 截至 19:00 仍未收到决策，Phase0 评估结果持续待呈报，监控中；8/12 无相关交互（Daryl 当日聚焦 OPC 变现战略深谈与 serveo 隧道排查），Phase0 决策持续挂起；8/13 无相关交互（Daryl 上午处理隧道与 Self 成果验收）；8/14 无相关交互（Daryl 处理隧道换址与 xiaofeng 休假安排），Phase0 决策持续挂起；8/15 无相关交互（Daryl 处理 serveo 恢复排查与 xiaofeng 雅思批次验收），Phase0 决策持续挂起第 6 天；8/16 挂起第 7 天，Kitty 周度闭环补跑中记为超阈值例外（决策账本），并随拍板清单再次呈报「Phase0 评估：全面应用 or 维持试点」（评估报告 5 分钟可呈）；提议挂起升级规则（第 3 天自动提醒 / 第 7 天按默认行动执行）纳入挂载机制方案，待 Daryl 确认；8/17 无直接进展（Phase0 决策持续挂起第 8 天）；8/18 无直接进展（截至 19:00） |
| 下周计划 | 视 Daryl 决策结果推进：Phase1 放行 or 推广 or 回退；8/9 决策日已过 → 8/16 已随拍板清单再呈报，评估结果随时可呈（5 分钟）；若挂起升级规则落地，第 7 天（8/16 已到）即按默认行动执行 |
| 阻塞项 | 无 |

#### 里程碑

| 里程碑 | 状态 | 完成 | 预计完成 |
|--------|------|------|----------|
| M0 · 信号捕获（纠错/失败/审计/复盘→inbox→周度蒸馏） | 🟢 done | 100% | 8/4 ✅ |
| M1 · 失败模式库（JSON+规则表+embedding+三层检索） | 🟢 done | 100% | 8/4 ✅ |
| M2 · 任务级注入（任务边界触发检索→注入上下文） | 🟢 done | 100% | 8/4 ✅ |
| Balance试点 Phase0（影子模式8/5-8/7，只记录不注入） | 🟡 评估中 | — | 待 Daryl 决策（8/9 已过，挂起第 7 天，8/16 再呈报） |

#### 关键决策

| 日期 | 决策 | 级别 | 状态 |
|------|------|------|------|
| 8/4 | 教训形成=事件驱动捕获+自动化蒸馏，非Agent自觉 | P1 | ✅ 已确认 |
| 8/4 | 检索=结构化+规则表+embedding语义层混合，否决纯向量库 | P1 | ✅ 已确认 |
| 8/4 | 注入时机=任务边界非session边界 | P1 | ✅ 已确认 |
| 8/4 | 教训库来源=corrections_inbox + Daryl纠错为主信号 | P1 | ✅ 已确认 |
| 8/5 | Balance为第二试点（高频财务任务），但需三档风控：Phase0影子(只记录)→Phase1低风险→Phase2全量 | P1 | ✅ 已确认 |
| 8/5 | 影子模式铁律：模拟注入但实际注入恒=0，独立shadow状态机不污染线上 | P2 | ✅ 已实施 |
| 8/5 | classify_task补充财务域关键词（Balance试点部署中发现关键词表偏开发域） | P2 | ✅ 已实施 |
| 8/7 | Phase0 评估不专门汇报，监控即可；周日(8/9) 一次性「是否全面应用」决策（Daryl 指令） | P1 | ✅ 已确认 |
| 8/16 | Phase0 挂起第 7 天记为超阈值例外（决策账本）；评估随拍板清单再次呈报（全面应用 or 维持试点）；挂起升级规则提议（第3天提醒/第7天默认行动） | P1 | 🟡 待 Daryl 决策 |
---

### OPC看板交互系统（Dashboard v1.6）

| 字段 | 值 |
|------|-----|
| 项目ID | opc-dashboard |
| 状态 | 🟢 active |
| 优先级 | P0 |
| 当前版本 | v1.6 + 产物模块 v1.7.0（运行中 @ http://localhost:8765，commits 690decf/fbcd813/09e38ea） |
| 当前阶段 | M4 · 生产部署优化 ✅ 全部完成（8/7） |
| 阶段进度 | 100% |
| 总进度 | 100%（M4 收官） |
| 启动日期 | 2026-06-08 |
| 预计交付 | 2026-08-10 |
| 本周进展 | 8/2-8/5 运行平稳；8/5 成本端点核查+preview修复（ea47ba2）+产物模块 v1.7.0（fbcd813）；8/7 M4 收官：③约定版本变更自动DM通知（M4c，commit 09e38ea），至此 M4 三项全完成（①override过期清理✅ ②系统消息过滤✅ ③约定版本变更通知✅）；Daryl 拍板 v1.7 整合「Sidebar项目总线 → 平移到 Agent状态和任务的 project milestone 模块」；8/7 21:40 全 Agent 看板初始化（Daryl 指令）：通知 xiaofeng/Balance/Self 清过时任务+成本自查，Self 已回复（清理5个过时项目+发现 8/6 团建卡生图 ~$1.0-1.3 未进台账），待 xiaofeng/Balance 回复；8/8 记忆 Cron consolidated 修复上线（audit-all-report.sh 四 workspace 审计+汇总+群汇报，00:16 手动跑通）；8/9 ~08:10 serveo.net 服务端宕机（DNS 可达但 22/443 超时，非映射问题）→ 固定域名 opc-darylchiu.serveousercontent.com 失联；应急上线 cloudflared 备用隧道 searched-chip-belly-consolidation.trycloudflare.com → 8765（公网 HTTP 200 / 0.87s），autossh 持续重连待 serveo 恢复；Balance 顺手修复 .current_tunnel_url 文件 grep 误写；8/10 复核：localhost:8765 正常（HTTP 200），cloudflared 进程存活但旧随机域名已失效（000），serveo 恢复状态待确认；13:08 Daryl 周一报到，4 Agent 全员在线；8/10 23:25 Balance cron 成本扫描（今日 $0.24/本月 $20.24/全量 $146.03 写入 cost_daily.json），main 核实 /api/costs 端点数字全对齐（monthly kitty 6.04+xiaofeng 2.45+balance 6.98+self 4.77=20.24），确认 v1.6.1 已实现 .jsonl 全量扫描+balance-ledger 权威源、无需代码改动，并确认 opc-workspace 下 cost_daily.json 为指向 WorkBuddy 的符号链接（8/4 建立）；8/11 全天无新进展（仅心跳，Balance 13:00 侧完成自身看板刷新）；8/12 serveo 固定域名 502 排查（Daryl 报障）：本地 8765 正常、serveo.net 首页 200、SSH 22 通，新建随机子域名 opc-test-111446 也 502 → 定性 serveo 服务端「HTTP代理→SSH隧道」内部路由整体故障（8/9 宕机家族复发），非我方问题；彻底重建 autossh 仍 502，等 serveo 恢复（watchdog 每 5 分钟自动检测回切）；cloudflared 备用隧道 sweet-letter-dame-sensitive.trycloudflare.com 实测 200（11:15 刚换过 URL）；顺手修复 .current_tunnel_url 被 grep 报错文本污染（存 "Binary file ... matches" 非 URL，已改写为可用地址）；Daryl 用临时隧道验收 Balance 费用报销报告 ✅（第一个完整正反馈案例）；8/13 上午 Daryl 要最新公网隧道地址验收 Self 成果：serveo 固定域名仍 502（8/12 服务端故障未恢复）；隧道地址两次变更（09:25 phil-highly-threshold-extend → 09:30 连接终止致 Daryl 访问 Error 1033 → 09:30 重启 arcade-interpreted-nevertheless-radios → 09:35 singer-mechanisms-rolled-geographical 实测 200）；09:35 修复 watchdog.sh L69 grep 读 cf.log 报 Binary file matches（加 -a）；09:40 Error 1033 根因复盘：localhost:8765 从未掉过（PID 3587 自 8/7 20:34 连续运行 6 天），真实根因 = watchdog 自杀式换 URL（serveo 502 → pkill 健康 CF 隧道 → 重建新随机 URL，Daryl 拿到的 URL 5 分钟内被杀）→ 修复 = CF 回退分支「已有健康 CF 隧道则保留不重建」（exit 0）；serveo 公网 URL 域名纠正（Daryl 第二次）：一律 *.serveousercontent.com，serveo.net 是 SSH 主机名，报 URL 前查 watchdog.sh 权威值；8/13 23:45 Balance 成本扫描：今日 $0.75 / 本月 $22.70 / 全量 $148.49，/api/costs 与台账对齐（无需改造）；8/14 ~12:00 隧道再换：旧 cloudflared（ports-evening）11:55 进程挂 → watchdog 12:00 检测 → 12:05 重建新隧道 overall-supplier-season-stick.trycloudflare.com（实测 200，PID 3869；watchdog 行为正确——旧隧道确实死亡，该重建）；serveo 固定域名仍 502（服务端故障第 3 天）；当日第 4 次换 URL（临时隧道进程死即换域名，Daryl 追不上地址）；main 再次建议 Cloudflare Named Tunnel 固定域名方案（免费：命名隧道+固定域名，进程重启地址不变），待 Daryl 确认（8/12 曾决定不投入）；8/15 ~14:00 serveo 恢复排查（Daryl 报「产物与预览看不到」）：①serveo 服务端已恢复（8/12 故障解除，固定域名 opc-darylchiu.serveousercontent.com 200，autossh PID 38214 正常）②但免费版对浏览器访问强制插入「Serveo Browser Warning」确认页（防钓鱼），点 Continue 种 cookie serveo-skip-browser-warning=true → 带此 cookie 的所有 /api/* 请求全 502（curl 无 cookie 直连 200）③根因=serveo 服务端行为非我方问题：Agent 卡片是静态 HTML 所以能显示，产物列表靠 /api/artifacts 所以永远 Loading ④cloudflared 备用隧道 endorsed-calgary-revolution-vip.trycloudflare.com 浏览器实测 37 产物全正常零错误（playwright 验证）⑤watchdog 风险提示：其用 curl 无 cookie 检测 serveo 200 会判健康，但 serveo 对浏览器实际不可用；当前 .current_tunnel_url 指向 CF 隧道为权威入口；长期方案 A serveo 付费去警告页（~$5/月）/ B Named Tunnel 固定域名（免费，推荐），待 Daryl 确认；8/15 23:45 Balance 成本扫描：今日 $0.96 / 本月 $24.27 / 全量 $150.06（26,322 次调用 / 1.80B tokens），/api/costs 与台账对齐（无需改造）；8/16 上午 serveo 方案（A 付费 ~$5/月 / B Named Tunnel 免费）随拍板清单第三次呈报，待 Daryl 确认 |
| 下周计划 | v1.7 整合开发（Sidebar 项目总线平移到 project milestone 模块，8/7 拍板待启动）；serveo 方案（A 付费 ~$5/月 / B Named Tunnel 免费，推荐）8/16 第三次呈报待 Daryl 确认——确认前公网入口以 cloudflared 临时隧道 endorsed-calgary-revolution-vip 为准；汇总三 Agent 看板初始化结果给 Daryl；Brave 接回主搜索路由待 Daryl 确认 |
| 阻塞项 | Daryl决策阻塞：Self阻塞(OPC看板/卡片审核/ACCA Vault等) + Balance SOP审阅（音乐文件/车辆费用/JGL 8/5已取消）；Brave接回主搜索路由待确认（C15基准8/5归档：SearXNG 39.9坍塌/Brave 65.9持平；8/10 08:00 周度抽检 SearXNG 37.0，坍塌持续）；xiaofeng/Balance 看板初始化回复待收；Self 旧 gateway cron 1799ac76 仍启用（8/10 归档确认连续第3天双通道并存，非禁用态），待清理；serveo 服务端已恢复（8/15）但免费版浏览器 Warning 页致 API 502（固定域名对浏览器不可用），公网入口以 cloudflared 临时隧道 endorsed-calgary-revolution-vip 为准（实测 200）；Named Tunnel 固定域名方案 8/16 第三次呈报（或 serveo 付费 ~$5/月），待 Daryl 确认；8/17 无直接进展（serveo/隧道方案仍待 Daryl 确认，无交互）；8/18 无直接进展（截至 19:00） |

#### 里程碑

| 里程碑 | 状态 | 完成 | 预计完成 |
|--------|------|------|----------|
| M1 · 核心看板上线 | 🟢 done | 100% | 6/15 ✅ |
| M2 · 功能面板（Agent状态/产物预览/Workflow编辑器/成本/沙箱） | 🟢 done | 100% | 6/28 ✅ |
| M3 · 项目总线集成 | 🟢 done | 100% | 7/25 ✅ |
| M4 · 生产部署优化（override过期/系统消息过滤/约定版本变更通知） | 🟢 done | 100% | 8/7 ✅ |
| v1.7 · Sidebar项目总线与project milestone整合 | ⚪ pending | 0% | 8/7 Daryl 拍板，待启动 |

#### 成本归集

| 月份 | 预算 | 实际 | 差额 |
|------|------|------|------|
| 2026-06 | — | ~$28 | — |
| 2026-07 | $55 | $66.01 | -$11.01 🔴 |
| 2026-08 | ≤$85（变现战略 API 预算约束） | $29.34 | 8/17 23:45 归集（Balance 台账：今日 $4.78 / 本月 $29.34 / 全量 $155.13，/api/costs 已对齐；今日成本大头为 Balance $4.17） |
| 累计 | — | ~$155.13 | 🔴 7月超支20.0% |

#### 关键决策

| 日期 | 决策 | 级别 | 状态 |
|------|------|------|------|
| 7/6 | project.md 按 AgentID 命名，各自维护 | P1 | ✅ 已确认 |
| 7/6 | Cron先更新后扫描，避免滞后 | P1 | ✅ 已确认 |
| 7/6 | 模板按状态区块+表格字段，Dashboard直接解析4文件 | P1 | ✅ 已确认 |
| 7/18 | Dashboard 成本数据源改为 Balance 台账+调整（不再自行全量扫描） | P2 | ✅ 已实施 |
| 7/21 | Agent自进化基建整体暂停，GEPA类项目严禁再开发 | P1 | ✅ 已确认 |
| 7/23 | 搞钱群成立，main/xiaofeng/self 入群 | P2 | ✅ 已实施 |
| 7/25 | GEPA教训：AI-on-AI实验不可靠，确定性基础设施（bash+python watchdog级）已验证有效 | P2 | ✅ 已记录 |
| 8/5 | 成本端点核查：Balance诉求已实现（jsonl全量扫描+双源合并），无需改动 | P2 | ✅ 已实施 |
| 8/5 | 产物模块 v1.7.0 上线（30天剔除/新鲜度加权/每Agent≤15/新文档置顶） | P2 | ✅ 已实施 |
| 8/7 | M4 三项全部完成：override过期清理✅ + 系统消息过滤✅ + 约定版本变更自动DM通知（M4c commit 09e38ea）✅ | P2 | ✅ 已实施 |
| 8/7 | v1.7 整合方向（Daryl 拍板）：Sidebar 项目总线与 Agent状态页 project milestone 重复 → 把 Sidebar 项目总线平移到 Agent状态和任务的 project milestone 模块 | P1 | ✅ 已确认，待启动 |
| 8/7 | 全 Agent 看板初始化（Daryl 指令）：各 Agent 清过时任务/项目+成本自查；Self 完成，待 xiaofeng/Balance | P1 | ✅ 已实施 |
| 8/5 | Daryl决策：8月预算/12G存储/Model Router 搁置；音乐文件/车辆费用/JGL 取消；C15 搜索基准已做 | P1 | ✅ 已确认 |
| 8/9 | serveo 宕机应急：cloudflared 备用隧道上线（trycloudflare 随机域名重启会变），serveo 恢复后回固定域名 | P2 | ✅ 已实施 |
| 8/10 | Balance cron 二轮请求成本端点改造 → 核实 v1.6.1 已实现 .jsonl 全量扫描（refreshCostFromJsonl 解析 usage.cost.total）+ balance-ledger 权威源，数字全对齐无需改动 | P2 | ✅ 已核实 |
| 8/12 | serveo 502 定性：服务端「HTTP代理→SSH隧道」内部路由整体故障（8/9 宕机家族复发），非我方问题；cloudflared 临时隧道承接，watchdog 每 5 分钟自动检测回切 | P2 | ✅ 已定位 |
| 8/12 | Balance 费用报销报告经临时隧道验收通过 ✅（第一个完整正反馈案例）；Daryl 决定不投入 Cloudflare 命名隧道（未赚钱不敢投入） | P2 | ✅ 已验收 |
| 8/13 | Error 1033 根因：watchdog 自杀式换 URL（serveo 502→pkill 健康 CF 隧道→重建新随机 URL）；修复=CF 回退分支已有健康隧道则保留不重建 + grep -a 修 Binary file 误报 | P2 | ✅ 已修复 |
| 8/13 | serveo 公网 URL 域名纠正（Daryl 第二次）：一律 *.serveousercontent.com（serveo.net 是 SSH 主机名）；报 URL 前查 watchdog.sh L14 权威值 | P2 | ✅ 已记录 |
| 8/14 | cloudflared 临时隧道当日第 4 次换 URL（ports-evening 11:55 挂 → watchdog 12:05 重建 overall-supplier-season-stick，实测 200，行为正确）；serveo 502 第 3 天；再次提议 Named Tunnel 固定域名方案（免费）待 Daryl 确认 | P2 | ✅ 已处理，方案待确认 |
| 8/16 | serveo 方案（A 付费 ~$5/月 / B Named Tunnel 免费，推荐）随拍板清单第三次呈报，与 Phase0 评估、M2 关闭合并为一批待 Daryl 拍板 | P2 | 🟡 方案待确认 |
| 8/15 | serveo 服务端恢复（8/12 故障解除）但免费版新增浏览器 Warning 确认页 + cookie 致 /api/* 全 502（产物列表永远 Loading）；根因为 serveo 服务端行为非我方问题；立即可用入口=cloudflared endorsed-calgary-revolution-vip（浏览器实测 37 产物正常）；长期方案 A serveo 付费 ~$5/月 / B Named Tunnel 固定域名（免费，推荐）待 Daryl 确认 | P2 | ✅ 已排查定案，方案待确认 |

#### 风险/问题

| 日期 | 风险 | 影响 | 措施 |
|------|------|------|------|
| 7/16 | status_overrides 无过期机制 | 已消失任务残留为鬼数据（红框/绿框） | M4 加入 override 自动过期逻辑 + 系统消息过滤 |
| 7/16 | 成本 API 数据差异 | dashboard 与 Balance 月份统计不一致 | ✅ 7/18 M1已修复：数据源统一为Balance台账+调整 |
| 7/18 | cost_daily.json 路径不一致 | Balance写入旧Dashboard副本，运行中Dashboard读不到 | ✅ 7/19 Balance已修复 |
| 8/5 | /api/preview ReferenceError（server.js:1085 project未定义） | 看板产物预览崩溃 | ✅ 已修复 commit ea47ba2 |
| 8/7 | 8/6 团建邀请卡 6 张图 OpenRouter 生图 ~$1.0-1.3 未进成本台账（Self 发现） | 看板成本统计低估 | 待 Balance 排查图片生成成本纳入扫描 |
| 8/9 | serveo.net 服务端宕机（8/9 ~08:10，DNS 可达但 22/443 超时） | OPC 看板固定公网域名失联，平板验收受阻 | ✅ 8/9 cloudflared 备用隧道上线（HTTP 200）；8/10 复核旧随机域名已失效（trycloudflare 重启即变），进程存活待刷新 URL；serveo 8/13 仍 502 未恢复 |
| 8/12 | serveo 固定域名 502 复发（8/12 上午，服务端「HTTP代理→SSH隧道」内部路由整体故障，随机子域名也 502） | 看板公网域名失联，验收依赖临时隧道 | ✅ 定性非我方问题；cloudflared 临时隧道 sweet-letter-dame-sensitive 200（重启即换 URL）；.current_tunnel_url 污染已修复；watchdog 5 分钟检测回切；等 serveo 恢复 |
| 8/13 | 隧道地址两次变更致 Daryl 验收报 Error 1033（09:25 phil → 09:30 被杀换 arcade → 09:35 换 singer） | 公网访问中断，验收受阻 | ✅ 根因定位：watchdog 自杀式换 URL（serveo 502 → pkill 健康 CF 隧道），localhost:8765 从未掉过（PID 3587 运行 6 天）；修复=已有健康 CF 隧道则保留不重建 + grep -a；当前 singer-mechanisms-rolled-geographical 200 |
| 8/14 | cloudflared 临时隧道进程死亡 → URL 再次失效（ports-evening 11:55 挂，12:05 重建 overall-supplier-season-stick；当日第 4 次换 URL） | 公网地址频繁变化，Daryl 追不上地址 | ✅ watchdog 行为正确（旧隧道确实死亡，该重建）；已再次建议 Named Tunnel 固定域名方案（免费）待 Daryl 确认；serveo 仍 502（第 3 天） |
| 8/15 | serveo 服务端恢复但免费版浏览器 Warning 确认页 + cookie（serveo-skip-browser-warning=true）致 /api/* 全 502 | 固定域名对浏览器实际不可用（产物/预览永远 Loading），watchdog 无 cookie 检测会误判 serveo 健康 | ✅ 排查定案（serveo 服务端行为，非我方）；权威入口切至 cloudflared endorsed-calgary-revolution-vip（实测 37 产物正常）；方案 A 付费 $5/月 / B Named Tunnel 免费待 Daryl 确认（8/16 第三次呈报） |

---

### Daryl 个人训练计划（增肌+体能，个人服务）

| 字段 | 值 |
|------|-----|
| 项目ID | daryl-training-plan |
| 状态 | 🟢 active |
| 优先级 | P1 |
| 当前阶段 | v1.1 全身版已交付（8/16）；进入 2 周反馈期（8/30）→ 8 周复评（10/11） |
| 阶段进度 | 方案 v1.0 ✅ → v1.1 全身版修正 ✅（8/16 21:30 Daryl 纠正羽毛球触发点非目标）；执行+反馈中 |
| 启动日期 | 2026-08-16 |
| 预计交付 | 8 周周期（8/16→10/11）；2 周反馈 8/30 |
| 本周进展 | 8/16 交付 docs/daryl_training_plan_20260816.md v1.0（8周4分化：下肢/上肢推/下肢+体能/上肢拉 + 渐进超负荷 + 30min压缩版 + 骑行2次/周 + 饮食 2500kcal/120g蛋白 + 补剂优先级（肌酸必买/蛋白粉镁可选/BCAA智商税）+ 睡眠6条 + 高度近视安全清单）→ 21:30 v1.1 全身版修正（Daryl 纠正：羽毛球体感下降是触发点非目标，已捕获进信号池；改全身训练 4 次/周 A/B轮换 + 骑行 3 次/周）；8/17-8/18 执行期无反馈（8/30 收 2 周反馈迭代） |
| 下周计划 | 执行期：Daryl 按 v1.1 全身版执行；8/30 收 2 周反馈迭代 |
| 阻塞项 | 无 |

#### 里程碑

| 里程碑 | 状态 | 完成 | 预计完成 |
|--------|------|------|----------|
| 方案 v1.0（8周周期 4 分化） | 🟢 done | 100% | 8/16 ✅ |
| v1.1 全身版修正（触发点定性纠正） | 🟢 done | 100% | 8/16 ✅ |
| 2 周反馈迭代 | ⚪ pending | — | 8/30 |
| 8 周复评 | ⚪ pending | — | 10/11 |

#### 关键决策

| 日期 | 决策 | 级别 | 状态 |
|------|------|------|------|
| 8/16 | 羽毛球体感下降 = 训练触发热点（非目标），已捕获进信号池；训练目标定位增肌+体能健康 | P2 | ✅ 已确认 |

---

## 🟡 规划中项目

| 项目名 | 方向 | 优先级 | 预计启动 |
|--------|------|--------|----------|
| — | 暂无（Loop Engineering 已于 8/5 立项 → decision-loop，见上方进行中） | — | — |

---

## 🔵 已完成项目

| 项目名 | 交付日期 | 工时 | 归档链接 |
|--------|----------|------|----------|
| OPC看板 M1+M2 | 2026-06-28 | ~120h | — |
| 记忆系统v3 — project文件（模板+API+Cron+4Agent同步） | 2026-07-06 | ~6h | commit 690decf |
| SearXNG搜索质量迭代（M1修复+M2子代理中断协议+P0自动重启+P1搜索方法论） | 2026-07-17 | ~4h | Daryl 验收通过 7/18 |
| 基建长线任务 — M1成本根因+M2搜索基准+M3 trace协议 | 2026-07-18 | ~6h | trace: memory/subagent_runs/infra_longline_20260718/ |
| Maker-Checker 审查协议 — Self试点 | 2026-07-21 | ~2h | workspace-self commit e72722d |
| 第二期确定性基建 · OPC运营中枢（阻塞扫描+成本预警+新鲜度+搜索质量4模块） | 2026-07-25 | ~7.5h | commit 2dba501c |
| Websearch 全面升级 v2.0（基建侧强制条款+引擎精简5→3+方法论v2+混合路由+基准持平） | 2026-07-29 | ~4h | commit 4fae35cb |
| 记忆 Cron consolidated 修复（audit-all-report.sh：四 workspace 审计+汇总+群汇报，23:59 上线） | 2026-08-08 | ~1h | launchd ai.openclaw.daily-memory-check 改指 |
| 补剂调研组A（VC/葡萄籽OPC/高纯度鱼油 + AKK/镁/NAD+ + 姜黄素/Q10/甜菜根 三部分调研） | 2026-08-09 | ~2h | memory/subagent_runs/supplements_research/ |

---

## ⚪ 归档

| 项目名 | 归档日期 | 最终状态 | 备注 |
|--------|----------|----------|------|
| Sentinel 合规哨兵 v1.0 | 2026-07-15 | ⏸️ 搁置 | Daryl 与 Bryson 评估后认为风险较大；插件配置保留未激活 |
| Agent自进化基建 | 2026-07-21 | ⏸️ 搁置 | Daryl 指令暂停全部自进化开发；GEPA禁开；SAGE Checker + Reflexion 保留（非自进化，仅校验） |
