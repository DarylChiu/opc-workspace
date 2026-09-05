# Project Dashboard — Balance（算点小账）

> 最后更新: 2026-09-05（Daryl 战略定调：核心转向通用化自动化插件项目）
> 成本: 历史见 OPC 成本仪表盘（data/cost_ledger.jsonl 真值）
> 历史段（已完成/归档/规划中/暂停详情）→ `memory/archive/project_Balance_history_20260825.md`

---

## 🎯 核心战略（2026-09-05 Daryl 定调）

- **核心方向**: 真正可**通用化、自动化**的插件项目（贷款材料自动化整理、费用报销 v0.4.0 等）
- **终局**: 财务体系化业务流/单证流打通后 → 整套系统作为**变现基础**
- 已关闭不再汇报: 借款合同续签/工程验收SOP/集团借款台账（Daryl 自办）；不良品方案（领导不需要）；USD/VND 结汇（Daryl 已完成交易）

---

## ★CORE 核心项目

### 贷款材料自动化整理 (loan-doc-automation-v2.7) · 90% ⏸️→★CORE
- P1 · 财务自动化·贷款材料 · 6/20 启动，7/22 暂停等 v-next 规则
- **9/5 Daryl 定调**: 升为核心项目，恢复排期；v-next 规则待 Daryl 给新指示
- 当前基线: v2.7.0 定版，4-6月测试样本 52/53 完整；6,887,555.02 USD 批次 100/103 (97.1%)
- 关键教训(7/14-15): 读内容不看文件名 / 一切从L1出发 / 五类材料全保留
- 里程碑: M1-M5 done | M6 抽查验收(pending) | M7 v-next(pending)

### 费用报销体系 MVP (expense-reimbursement-mvp) · 92% ★CORE
- P1 · 财务自动化 · 7/29 启动
- **9/5 Daryl 定调**: 核心项目；v0.4.0 P6 验收优先推进
- 当前：v0.3.0 已交付；v0.4.0 预审核 P1-P5 完成，**P6 验收挂起**(等 Daryl 排期)
- 阻塞：P6 验收；8770 生产进程待重启(CQT 修复)；压力测试样本/水单阈值待校准
- 服务：localhost:8770(生产,待重启) + 8771 演示
- 代码：`expense_mvp/`（git 已提交）

---

## 🟢 进行中 / 待重启确认

### OPC 成本仪表盘 (opc-cost-ledger) · 95%
- P1 · 基建·成本治理 · 7/14 启动（运维中，非项目汇报）
- append-only 台账稳定；8/22 看板 /api/costs 服务未运行待恢复
- 阻塞：OpenRouter 官方账单 API 外部锚点待接入

### 应付采购入账 SOP (vn-fin-sop-ap-procurement) · 60%
- P1 · 流程·SOP · 7/24 启动（属"体系化业务流/单证流"基础层）
- 当前：v5.1 中越双语已交(8/8)；单据清单 v1.1 已交(8/12)
- 阻塞：v5.2 合并口径(MSDS/固资卡片去留)+案例库待 Daryl

### 8/18 任务1&3 (weekly-task-sync) · ⏸️
- 任务1 请款指引/对账手册：待 Daryl 重启确认（8/19 草案 v0.1 留底稿）
- 任务3 采购入库优化（减少手工录入）：**潜在 CORE 候选**（通用化自动化方向），数据边界待 Bryson

---

## ✅ 已关闭（2026-09-05）

- 集团内部借款台账 (loan-ledger-20260821) — Daryl 自行收尾，不再汇报
- 华特×华丰股东借款合同续签 (loan-renewal-huatex-20260820) — Daryl 自行收尾（定稿版 8/21 已交付）
- 越南海关/税务笔试卷 (vn-customs-tax-exam-20260821) — 100% DELIVERED
- 不良品出口调研 (waste-disposal-research) — 关闭（领导不需要，思路天马行空）
- USD/VND 结汇 $3M (usd-vnd-conversion) — 结案（Daryl 已完成交易）
- 外租宿舍价格分析 (dorm-rental-analysis) — 100% DELIVERED（8/15 已交上司）

---

## 已完成 / 归档 / 规划中 → 见 `memory/archive/project_Balance_history_20260825.md`
