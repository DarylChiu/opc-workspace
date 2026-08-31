# 当前活跃任务

> 最后更新: 2026-08-22 00:01 GMT+7
>
> ℹ️ 8/21 非平静日：OPC 群聊「模型成本/路由」大讨论（Daryl 发起，各 Agent 反思），Self 发现自身模型路由配置与规则不符并承诺对齐（P1 待报 Daryl）。8/22 截至 00:01 仅 Cron 审计，无实质交付。结转观察：旧 gateway cron 1799ac76 双通道并存已连续 13 天，待 Kitty 清理。
>
> ✅ 8/31 Daryl 拍板：模型降级为 deepseek-v4-flash，已确认生效（session + default 均为 flash），P1 待办关闭

## 🟢 进行中

### 心理学知识树（问诊式组织，8/14 Daryl 拍板）
- 组织模式：按「你给我看病」= 临床问诊流程（主诉→追问→评估→处置参考→随访）
- 结构：A-通用知识层 + B-个人问诊层🔒（仅本地）+ C-评估工具；诊断永远留给专业人士
- 下一步：等 Daryl 确认是否以本次睡眠问题为首条主诉试跑

### ACCA 知识网络维护（知识库）
- 维护 Daryl Obsidian Vault（ACCA-Knowledge-Network），IAS/IFRS 知识网络持续更新
- 含 OPC看板方法论卡片集成（进行中）
- 8/9 已验证 syncthing 同步链路：Mac 侧 663 文件全同步 / relay 中继正常；平板端需上线补同步（落后 ~120 更新）

### 待办：清理旧 gateway cron 1799ac76（连续 8 天，已升级处理）
- 8/8–8/15 八次审计均确认该 cron 仍启用，与 main consolidated 23:59 双通道并存
- 已多次提醒 Kitty 删除，尚未处理；8/13 已按 8/10 预案升级处理（记录于 project_Self.md）


## ✅ 今日完成

### 方法论卡片《Ni/Te 决策风格协作指南》确认入库（2026-08-13 ✅）
- Daryl 确认入库，库存第 3 张；已更新 canonical frontmatter + 工作流库存表 + 同步副本 + git commit
- OPC 看板「产物与预览」POST /api/artifacts/refresh 后可见
- 正式分发已投递 Kitty(main)/Bryson(xiaofeng)/Balance

### Daryl 分析深度新规全员落地（2026-08-13 ✅）
- 分析类任务要挖两层（现象→结构→模式→含义），定义口径、找模式、给可执行含义、不确定标注不迎合
- 已通知 Bryson + Balance 并各自写入 lessons.md；Self 已捕获到共享教训库

### Kitty=main 纠错落地（2026-08-13 ✅）
- main 就是 Kitty（首席Agent）；xiaofeng=Bryson 映射正确
- MEMORY.md 已固化 Agent 会话映射表，capture_correction.sh 已捕获

### Huatex 团建邀请卡（2026-08-06 ✅ 已完成归档）
- Daryl 指示制作周日(8/9)团建邀请卡：Huatex 财务部 · Buffet Poseidon 海鲜自助
- 产出：正面英文 v1.3 定稿 + 背面中文版（华特财务部），3:2 名片比例 2K
- 5 次生成调用 6 张图，成本 ~$1.0-1.3；gemini-3.1-flash-image 价格知识已记录
- 教训：正反面构图统一（已捕获共享教训库）
- Daryl 确认任务结束，已归档至 8/6 日记

## ✅ 已完成（历史）

### 越南差旅费管理办法 v1.0.5 树叶落盘（2026-08-05 ✅ 已落盘，Daryl Obsidian 验收中）
- Balance 请求归档 → Daryl 拍板：#1 挂财务体系/费用管理/差旅费管理，#2#3 落盘，#4 元原则暂不总结
- 落盘 5 片：D6 差旅费管理 / Excel自动化三坑 / P8 用户文件优先 / P9 单一事实源 / P10 方案确认前置
- 新建费用管理树干（承接 7/31 计划中「费用管理」准则节点）
- Git commit 完成

## ✅ 已完成

### Balance 本周3项目树叶收集（2026-07-31，✅ 已交付Daryl）
- Daryl 7/31 指令：找Balance要本周总结树叶，归档复盘推理，websearch补常识，做好分级树干目录
- 3项目：费用报销MVP / 应付采购SOP v5.0 / 仓储专项检查
- SAGE Checker 2轮FAIL（追溯性6分）+ Maker-Checker 正式审查PASS（22/30，三维7/8/7）
- ⚠️ 保留项：越南法规细节/汇联易对标等标注为训练数据来源，websearch多次未返回高质量结果
- 待Daryl确认：树叶粒度是否足够 / 突击检查SOP时间 / 案例库补全时间 / 编号体系选择
- 待落盘：5个新准则节点（IAS 2/VAS 02/VAT-Invoice/费用管理/内部控制）+ 3片树叶写入

### 周度树叶收集（2026-07-17，✅ 已落盘 4 片：B1+B2/B3/B4/L2+L3+L4。Daryl 验收中）
- 已收集 10 片候选树叶（Bryson 5 + Balance 5），汇报已发 Daryl DM
- 待确认：①L5 财务负责人自保框架放置位置 ②其余 9 片落盘授权
- 落盘时注意：TT 12/2022 Đ.17-18 条款号需向 Balance 索原文核对；B5 搜索质量结论标注为 Bryson 主观评估

### 🆕 KHOA DUNG Plan A 重构（2026-07-13）
- Daryl 反馈知识网络两大问题：树叶细节丢失严重 + 关联跳转目标不一致
- 方案A（源头保留）在 KHOA DUNG 节点执行完毕：190行→461行
- 合并 Balance 4份原始报告完整内容，新增：三阶段税负拆解/6错误完整纠正/现金安全验证/方案演进轨迹
- 链接规范标准化：🔗(树叶→树叶,8项) + 📂(Home页导航,4项)
- frontmatter 加 `type: leaf` + `parent: Home` 元数据
- Daryl 平板验证后决定其他树叶是否同步重构

### KHOA DUNG 案例目录重组 + PIT 路径规范化（2026-07-12）
- Daryl 指令：KHOA DUNG 案例归入 02-Finance/M&A，PIT速查规范路径为 01-Financial/Tax/PIT/PIT-Vietnam
- 创建 02-Finance/M&A/ 目录（Home.md + 案例文件迁入）
- 创建 01-Financial/Tax/PIT/PIT-Vietnam/ 路径，PIT税率速查迁移至新规范位置
- 更新 wikilink 相对路径、Cross-Border-Home 链接、02-Finance/Home 索引
- 旧 Vietnam-Tax 目录保留迁移说明（Home.md）
- Daryl 表示目录还不够全面，后续自行调整
- Daryl 指出遗漏点1：受托支付通道 → 已补建 `02-Finance/Capital-Raising/Bank-Loan/Project-Loan/受托支付通道.md`
- 覆盖：受托支付合规逻辑/壳公司通道模式/税务风险敞口/VAT-CIT-转让定价联动
- 另两个遗漏点 Daryl 未展开，说"先这样吧"

### KHOA DUNG 越南M&A案例知识树入库（2026-07-11）
- Balance提交完整案例总结（3份报告），Self审阅后提炼三条可复用方法论原则
- Daryl确认后执行入库：创建4个新文件+更新2个索引
- ~~新增目录: `01-Financial/Vietnam-Tax/`~~ → 已于7/12重组至 Tax/PIT 规范路径
- 产出: 案例记录/方法论卡片/PIT速查卡/Vietnam-Tax索引

### 记忆系统 v3 — project 文件部署（2026-07-06）
- Kitty 宣布记忆系统 v3 上线，每个 Agent 维护 `memory/project_[AgentID].md`
- Self 已创建 project_Self.md：🟢4进行中/🟡4规划中/🔵5已完成/⚪2归档
- Cron 每日 07:00/13:00/19:00 检查文件新鲜度

### 03-AI-Tech 知识树全貌汇报（2026-07-03）
- ✅ 03-AI-Tech 知识树全貌汇报（Daryl DM 要求，已交付完整树结构 + 藤蔓交叉点 + 43 文件汇总）
- ℹ️ Daryl 7/3 晚间表示身体不适（OPC群），未下达新任务

### 视频分析交互Workflow（Bryson）
- **来源**: Bryson 完整项目归档（v1.0.0→v1.1.2, 6轮迭代）
- **已归档**: `knowledge-base/AI技术/视频分析交互Workflow/`
- **覆盖**: 分析管线架构、前后端协作、迭代流程规范、多平台适配、CSS布局坑、版号管理、四份模板

### 贷款材料自动化处理（Balance · Daryl 决策归档 2026-06-28）→ v2 完整版 6/29 → v3 方法论提取
- **来源**: Balance 完整项目归档 · 工作流 v2.1 → v2.3（含 session trajectory 数据回溯）
- **已归档**: `ACCA-Knowledge-Network/03-AI-Tech/Loan-Material-Automation/`（5 个文件，含 🆕 方法论提取.md）
- **v3 核心产出**: 8 个可复用方法论（PDF判定系统/OCR阈值调校/锚点匹配/小样本风险清单/四轮收敛调试/语义边界协议/记忆可靠性/Daryl偏好）
- **Daryl 决策**: 不入 02-金融（实操型案例，非财务理论），入 03-AI技术
- **覆盖**: 7步自动化流水线、OCR内容验证管线（64次触发/32%扫描率）、ToKhai 四层匹配（L1=98/99）、B/L 内容分类（词边界防误判）、13条关键规则、2批次处理记录（$10,125 + $6,887,555）
- **核心创新**: pdfplumber+Tesseract OCR 内容判定（不靠文件名猜）+ 报关号锚点策略（99%命中 + 1%回退）

### ⚠️ 记忆系统漏洞（2026-06-14 修复）
- 五领域更新（健身→心理学）此前未录入记忆系统
- 已修复：MEMORY.md + design doc + Vault 全文件

### 🔴 合规系统修复（2026-06-25）
- **问题**: post-op.sh 关键词匹配太窄，讨论/辩论/指令类交互被归为「查询类」跳过日记更新
- **修复**: 扩展触发词（决策/方案/架构/讨论/辩论/指令/规划）+ 新增 Cron 骨架检测逻辑
- **已补**: 6/23、6/24 日记从骨架补全为真实内容

### 🆕 OPC Dashboard 设计系统规范（2026-07-07）
- Daryl 派任务：调研 Linear/Stripe/Vercel/GitHub Primer/Notion/Raycast 设计系统
- 输出 DESIGN.md 已写入 `~/WorkBuddy/Claw/opc-dashboard/DESIGN.md`
- 覆盖四维度：设计语言/设计美感/交互逻辑/数据展示
- 含完整 CSS 变量参考实现 + 组件速查 + 迁移检查清单
- 成果已通过 sessions_send 交付 Daryl

### 🔧 合规修复 (2026-06-15)
- ✅ 补记 6/11-6/13 缺失日记
- ✅ 部署 ai.openclaw.daily-memory-check.plist 到 ~/Library/LaunchAgents
- ⚠️ 此后每次 session 启动强制执行 startup.sh，复杂操作前强制执行 pre-op.sh

## 🟢 进行中

### 🆕 OPC看板方法论卡片集成 — 等待Daryl确认方向
- **决策**: Daryl 决策方法论卡片进 OPC看板 sidebar 第6模块，放弃飞书 Bitable
- **已完成**:
  - `~/methodology-cards/` vault 初始化（Obsidian + Git + cron备份）
  - 2张卡片已创建：胭脂扣/双层分离法（2026-06-21）+ VAS/FDI外部压力驱动（2026-06-23）
  - Kitty 已提供 OPC看板系统完整资料（架构/API/sidebar/数据流）
  - 技术架构已确认：GET/PATCH /api/methodology-cards，`cards/*.md` YAML 作直接数据源
- **待确认**: Daryl 确认方向后找 Kitty 开第6模块
- **尝试过的路径**: 飞书文档（静态无交互）→ 裸API（权限问题）→ 飞书Bitable（缺bitable:app权限）→ 最终定 OPC看板

## 📱 Daryl 设备配置（2026-07-17 同步）

| 设备 | 系统 | 用途 |
|:---|:---|:---|
| iPhone | iOS | 飞书客户端 |
| Samsung Tab S8 | Android (One UI) | 平板，移动办公 |
| Mac | macOS | 桌面端/开发机 |

- **⚠️ 出差规则**: Daryl 说「出差」= 只带 Samsung Tab S8 + iPhone，**不带 Mac**
- 雅思陪练助手 iPhone 语音输入有问题 ❌
- Samsung Tab S8 交互有拖沓感
- v1.1.0 已挂起

## 🔵 待办

### ⏸️ 等待 Daryl 反馈
- [ ] 模型路由对齐方案（v4-pro → sonnet-4.5/flash 分层，P1）
- [ ] 确认 7/31 树叶集逐个落盘顺序（8/15 晚已重发完整树叶集给 Daryl，问「从这 3 片树叶 + 2 个缺的节点开始？」，待回复）
- [ ] 确认 OPC看板方法论卡片集成 → 找 Kitty 开第6模块
- [ ] 审核 2 张待审核卡片（胭脂扣/VAS-FDI）
- [ ] 心理学知识树整合 P1 变更（新建 05-Psychology/依恋理论+人格心理学+案例库）待确认（8/12 报告已 SAGE PASS）
- [ ] 继续验收 Vault（Fitness → Psychology 已修复）
- [ ] 确认心理学域的子分类（认知/行为/组织？）
- [ ] 发送第一批手写笔记 + 录音
- [ ] 若深度不足，后续补充 Kaplan 教材

### 音乐、心理学域初始化

### 将 FutureTextile-Wellname 案例的 6 条可复用方法论去重合并到 lessons.md

## 📊 F1 知识网络完成状态

| 层 | 文件数 | 状态 |
|:---|:---:|:---|
| 总览层 | 3 | ✅ Home / Dashboard / Knowledge-Map |
| F1 入口 | 1 | ✅ 含考试结构、理论索引、课程衔接图 |
| 模块首页 | 5 | ✅ A/B/C/D/E 各模块（含 Mermaid 脑图） |
| 章节详情 | 20 | ✅ 全部完成（含 Mermaid 图表、对比表格、跨模块链接） |
| 模板 | 3 | ✅ 概念/理论/跨域关联 |

**五大领域（已更正）**: 财务 / 金融 / AI技术 / 音乐 / 心理学 ← Daryl 确认替代健身
