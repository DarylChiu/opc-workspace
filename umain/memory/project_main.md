# Project Dashboard — main（忧郁小猫）

> 最后编译: 2026-08-09 19:00 +07:00
> 负责人: Kitty | Agent ID: main
> 下轮更新: 2026-08-10 07:00

---

## 🟢 进行中项目

---

### 决策自主环（Decision Loop / Loop Engineering）

| 字段 | 值 |
|------|-----|
| 项目ID | decision-loop |
| 状态 | 🟢 active |
| 优先级 | P0 |
| 当前阶段 | M0+M1 已交付（8/5），M2 剪辑MVP 试点进行中（Bryson v4.0 前端 60%；8/9 Daryl 开始下发 ASR/情感/MATCHER 模块交互需求，需求侧重新激活） |
| 阶段进度 | M0 100% / M1 100% / M2 60%（Bryson 前端 v4.0 交互版开发中，总进度 92%） |
| 启动日期 | 2026-08-05 |
| 预计交付 | M0→M3 共 40-80h；M2 原预计 8/8-8/9 → 顺延（Daryl 需求下发中，预计 8/10 后） |
| 本周进展 | 8/5 Daryl 立项、指定 Kitty 负责人（Bryson 移交）；M0 机制冻结（需求分级模板/提问质量门禁/教训病理Schema#4/错误预算规则#5 + AGENTS.md M0条款 + jianji-mvp workflow 方向确认前置节点 + 模式库3条种子病理，patterns 4→7）；M1 决策自主层工具 5/5（decide.py 三分类零LLM 13/13 + decision_ledger 账本 + error_budget 周度预算 P0拦截/降档/磨合期 + daily_exception_report + review_batch 周度批量审批），22 用例全绿，commits 069aa1df/ec22d4cb；四Agent 颠覆性思路征集整合（用户定方向、细节全归AI、控制→定价审计、经验可遗忘）；8/6 Daryl 拍板启动 M2：试点框架 docs/m2_jianji_pilot.md + 账本种子 dec_20260806_001 落盘，线框 wf01-wf05 冻结（2必改已核验），Bryson 交互方案定稿、完成 30%；8/7 核验 Bryson 前端 v4.0 达 60% 节点（8/6 开工后无新进展，xiaofeng 看板确认）；8/9 隧道基建修复（ngrok 固定域名回 8768 视频剪辑前端，雅思陪练改走 cloudflared）；8/9 Daryl 开始下发剩余 3 模块（ASR/情感/MATCHER）交互需求，第 1 条「素材联动+自动识别+补充识别」Bryson 已回复理解待确认 |
| 下周计划 | ①跟踪 Daryl 需求下发节奏 + Bryson M2 90%/100% 汇报节点 ②M2 完成后试点报告（决策次数对比/预算/例外）③Bryson 工具链清单搭设（mechanism_toolchain_requirements.md，~6h）④周日(8/9) 汇总已随自进化L1 一并呈报 M2 进度 |
| 阻塞项 | wf01 A/A 与 ASR 交互需求待 Daryl 回复 |

#### 里程碑

| 里程碑 | 状态 | 完成 | 预计完成 |
|--------|------|------|----------|
| M0 · 机制冻结（三分类/默认值/例外上报/错误预算/门禁） | 🟢 done | 100% | 8/5 ✅ |
| M1 · 决策自主层工具（decide/ledger/budget/exception/review） | 🟢 done | 100% | 8/5 ✅ |
| M2 · 剪辑MVP 试点（Bryson 协作） | 🟡 in_progress | 60% | 8/10+ 顺延（Daryl 需求下发中） |
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

---

### OPC自进化基建L1

| 字段 | 值 |
|------|-----|
| 项目ID | evolution-l1 |
| 状态 | 🟢 active |
| 优先级 | P0 |
| 当前阶段 | M0+M1+M2 已交付；Balance Phase0 影子测试窗口已结束（8/5-8/7），监控中待 8/9 决策 |
| 阶段进度 | M0 100% / M1 100% / M2 100% / Balance Phase0 评估中（8/9 Daryl 一次性决策） |
| 启动日期 | 2026-08-04 |
| 预计交付 | 8/9 周日 Daryl 一次性「是否全面应用」决策 |
| 本周进展 | 8/4 Daryl批准启动，M0+M1+M2全部交付（回归11/11，commits 7bf03311/dfccca86/6175b1ed）；8/5 Daryl批准Balance为第二试点，部署Phase0影子模式（shadow_inject只记录不注入+shadow_report周五评估+种子库7条+classify_task财务域关键词+AGENTS.md条款）；8/5-8/7 影子测试窗口运行完毕无异常；8/7 Daryl 指令：Phase0 评估不专门汇报，这几天监控即可，周日(8/9) 一次性做「是否全面应用」决策；8/8 记忆 Cron consolidated 修复上线（audit-all-report.sh 四 workspace 审计+汇总+群汇报）；8/9 周日决策日，截至 19:00 尚未收到 Daryl 一次性决策，Phase0 评估结果已备好待呈报，监控持续 |
| 下周计划 | 视 Daryl 8/9 决策结果推进：Phase1 放行 or 推广 or 回退；若未决策则 8/10 跟进提醒 |
| 阻塞项 | 无 |

#### 里程碑

| 里程碑 | 状态 | 完成 | 预计完成 |
|--------|------|------|----------|
| M0 · 信号捕获（纠错/失败/审计/复盘→inbox→周度蒸馏） | 🟢 done | 100% | 8/4 ✅ |
| M1 · 失败模式库（JSON+规则表+embedding+三层检索） | 🟢 done | 100% | 8/4 ✅ |
| M2 · 任务级注入（任务边界触发检索→注入上下文） | 🟢 done | 100% | 8/4 ✅ |
| Balance试点 Phase0（影子模式8/5-8/7，只记录不注入） | 🟡 评估中 | — | 8/9 Daryl 决策 |

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
| 本周进展 | 8/2-8/5 运行平稳；8/5 成本端点核查+preview修复（ea47ba2）+产物模块 v1.7.0（fbcd813）；8/7 M4 收官：③约定版本变更自动DM通知（M4c，commit 09e38ea），至此 M4 三项全完成（①override过期清理✅ ②系统消息过滤✅ ③约定版本变更通知✅）；Daryl 拍板 v1.7 整合「Sidebar项目总线 → 平移到 Agent状态和任务的 project milestone 模块」；8/7 21:40 全 Agent 看板初始化（Daryl 指令）：通知 xiaofeng/Balance/Self 清过时任务+成本自查，Self 已回复（清理5个过时项目+发现 8/6 团建卡生图 ~$1.0-1.3 未进台账），待 xiaofeng/Balance 回复；8/8 记忆 Cron consolidated 修复上线（audit-all-report.sh 四 workspace 审计+汇总+群汇报，00:16 手动跑通）；8/9 ~08:10 serveo.net 服务端宕机（DNS 可达但 22/443 超时，非映射问题）→ 固定域名 opc-darylchiu.serveousercontent.com 失联；应急上线 cloudflared 备用隧道 searched-chip-belly-consolidation.trycloudflare.com → 8765（公网 HTTP 200 / 0.87s），autossh 持续重连待 serveo 恢复；Balance 顺手修复 .current_tunnel_url 文件 grep 误写 |
| 下周计划 | v1.7 整合开发（Sidebar 项目总线平移到 project milestone 模块，8/7 拍板待启动）；汇总三 Agent 看板初始化结果给 Daryl；Brave 接回主搜索路由待 Daryl 确认；8/8 起逐项清理四 workspace 审计遗留问题；serveo 恢复后验证固定域名回归、评估 cloudflared 应急隧道持久化 |
| 阻塞项 | Daryl决策阻塞：Self阻塞(OPC看板/卡片审核/ACCA Vault等) + Balance SOP审阅（音乐文件/车辆费用/JGL 8/5已取消）；Brave接回主搜索路由待确认（C15基准8/5归档：SearXNG 39.9坍塌/Brave 65.9持平）；xiaofeng/Balance 看板初始化回复待收；Self 建议删除其侧旧 gateway cron（1799ac76 禁用态）待处理 |

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
| 2026-08 | 待定 | $17.86 | 8/9 止（10天，Balance 台账） |
| 累计 | — | ~$143.64 | 🔴 7月超支20.0% |

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

#### 风险/问题

| 日期 | 风险 | 影响 | 措施 |
|------|------|------|------|
| 7/16 | status_overrides 无过期机制 | 已消失任务残留为鬼数据（红框/绿框） | M4 加入 override 自动过期逻辑 + 系统消息过滤 |
| 7/16 | 成本 API 数据差异 | dashboard 与 Balance 月份统计不一致 | ✅ 7/18 M1已修复：数据源统一为Balance台账+调整 |
| 7/18 | cost_daily.json 路径不一致 | Balance写入旧Dashboard副本，运行中Dashboard读不到 | ✅ 7/19 Balance已修复 |
| 8/5 | /api/preview ReferenceError（server.js:1085 project未定义） | 看板产物预览崩溃 | ✅ 已修复 commit ea47ba2 |
| 8/7 | 8/6 团建邀请卡 6 张图 OpenRouter 生图 ~$1.0-1.3 未进成本台账（Self 发现） | 看板成本统计低估 | 待 Balance 排查图片生成成本纳入扫描 |
| 8/9 | serveo.net 服务端宕机（8/9 ~08:10，DNS 可达但 22/443 超时） | OPC 看板固定公网域名失联，平板验收受阻 | ✅ cloudflared 备用隧道已上线（HTTP 200）；autossh 重连中，serveo 恢复后固定域名自动回归 |

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

---

## ⚪ 归档

| 项目名 | 归档日期 | 最终状态 | 备注 |
|--------|----------|----------|------|
| Sentinel 合规哨兵 v1.0 | 2026-07-15 | ⏸️ 搁置 | Daryl 与 Bryson 评估后认为风险较大；插件配置保留未激活 |
| Agent自进化基建 | 2026-07-21 | ⏸️ 搁置 | Daryl 指令暂停全部自进化开发；GEPA禁开；SAGE Checker + Reflexion 保留（非自进化，仅校验） |
