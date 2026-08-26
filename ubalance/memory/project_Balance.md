# Project Dashboard — Balance（算点小账）

> 最后编译: 2026-08-25（Kitty 瘦身） · 成本: Balance 全量 $45.34 | 本月 $49.25 | 8/22 单日 $9.90（⚠️ 已超 $20 红线，见成本治理）
> 历史段（已完成/归档/规划中/暂停详情）→ `memory/archive/project_Balance_history_20260825.md`

---

## 🟢 进行中项目

### 集团内部借款台账 (loan-ledger-20260821) · 70%
- P1 · 财务·集团资金·合同台账 · 8/21 启动
- 当前：台账v1.0已交付(3 Sheet)；华特旧合同 **8/31 到期🔴剩 8 天**；drawdown 明细待 Daryl 补银行放款流水
- 阻塞：①「已提款金额/drawdown 明细」缺失→额度提醒待补 ②Wellname 与华峰持股关系待确认
- 里程碑：M1 台账v1.0✅ / M2 额度提醒(pending) / M3 华特续签归档(80%)
- 产出：`reports/集团内部借款台账-20260821.xlsx` + `work/loan-ledger/build_loan_ledger.py`
- 合同：①华丰香港→华特 USD1000万 4%/360天(8/31到期) ②Wellname→Future Textile USD3000万 4%/365天(2027-07-30到期)

### 华特×华丰股东借款合同续签 (loan-renewal-huatex-20260820) · 90%
- P1 · 合同拟制 · 8/20 启动
- 当前：定稿版已交付（10M/365天/4%/FCT借方/02正本），仅剩签署日待填
- 阻塞：①签署日待填 ②两处疑点待 Daryl 核实（借方地址 Long Tho Commune vs 章程 Phước An；成立证书号 68898950 vs 2648928）
- 里程碑：M1 草案✅ / M2 定稿✅ / M3 签署+疑点核实(90%)
- 产出：`reports/华特×华丰股东借款合同-英越双语-定稿版-20260821.docx`

### 越南海关/税务笔试卷 (vn-customs-tax-exam-20260821) · 100% 🟡 DELIVERED
- 8/22 Daryl「我改完了」闭环；4 题全改定
- 产出：`reports/越南海关税务笔试卷-4题-20260821.md` + `.docx`
- ⚠️ 遗留矛盾已标待 Daryl 核对：法规"建设含料 VAT3%+CIT0.4%" vs FCT"安装 VAT5%+4.75%"

### 本周新任务同步 (weekly-task-sync-20260818) · 50%
- P1 · 流程优化·SOP · 8/18 启动
- 当前：任务1 请款指引 v0.1 已推看板验收；任务2 工程验收 SOP 草案待验收；任务3 单独排期下周
- 阻塞：①月末供应商对账手册待范围 ②双语 docx 待验收后转 ③任务3 数据边界待 Bryson
- 里程碑：M1 排期+澄清✅ / M2 任务1(50%) / M3 任务2(45%) / M4 任务3(pending)

### 费用报销体系 MVP (expense-reimbursement-mvp) · 92%
- P1 · 财务自动化 · 7/29 启动
- 当前：v0.3.0 已交付；v0.4.0 预审核 P1-P5 完成，**P6 验收挂起**(8/12 启动→8/13 结转，等 Daryl)
- 阻塞：P6 验收挂起；8770 生产进程待重启(CQT 修复需重启)；压力测试样本/水单阈值待校准
- 服务：localhost:8770(生产,待重启) + 8771 演示(隧道 mice-lone-ghz-favorites.trycloudflare.com)
- 代码：`expense_mvp/`（git 已提交）

### 外租宿舍价格分析 (dorm-rental-analysis) · 100% 🟡 DELIVERED
- 8/15 终版 v2 含税口径 1.53 倍，Daryl 已交上司
- 沉淀：小专题报告模板 v1.0/v1.1 + 接任务模式 v1.0（1 天 SLA）

### 不良品出口调研 (waste-disposal-research) · 40% ⏸️
- P1 · 8/15 启动，8/18 挂起等领导采纳方向
- 当前：定性框架 + 完整版 + Excel 已交付；定量(HS级精算)待重启
- 阻塞：领导是否采纳方向（唯一真开关）

### USD/VND 结汇 $3M (usd-vnd-conversion) · 70%
- P1 · 8/17 启动，挂起等继续讨论
- 策略：不锁远期；分段止盈 26,300/26,500/26,700 各 $1M + 手工止损 26,000(3 扳机)

### 应付采购入账 SOP (vn-fin-sop-ap-procurement) · 60%
- P1 · 7/24 启动
- 当前：v5.1 中越双语已交(8/8)；单据清单 v1.1 流程图版已交(8/12)
- 阻塞：v5.2 合并口径(MSDS/固资卡片去留)+案例库待 Daryl
- 产出：`reports/应付采购入账SOP框架-v5.1-中越双语-20260808.docx`

### OPC 成本仪表盘 (opc-cost-ledger) · 95%
- P1 · 基建·成本治理 · 7/14 启动
- 当前：append-only 台账稳定(每日 23:45 扫描)；8/22 看板 /api/costs 服务未运行(curl 超时)待恢复
- 阻塞：OpenRouter 官方账单 API 外部锚点待接入
- 台账：`data/cost_ledger.jsonl`（真值，只增不减）· 脚本 `scripts/full_cost_scan.py`

---

## 已完成 / 归档 / 规划中 → 见 `memory/archive/project_Balance_history_20260825.md`
