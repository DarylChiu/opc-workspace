# project_Self.md — 恨点小己 项目看板

> 最后更新: 2026-07-21 20:33 GMT+7 (pre-reboot backup)
> Cron 检查: 每日 07:00 / 13:00 / 19:00
> 本周进展: 7/9 大规模搭建(F2-MA/IFRS-IAS/VAS) → 7/11-13 KHOA DUNG 入库+目录重组+Plan A 重构；7/14-16 例行记忆审计+看板刷新；7/15 晚 Daryl 授权 audit.sh 自进化基建对账升级（9.5段）+ 修复全团队 JSONL 写入错位 bug；7/17 SAGE Checker 两轮FAIL→三轮PASS 周度树叶收集（4片落盘→knowledge-base +4 / ACCA Vault 169→183），Daryl 验收中，3片+1待定未落盘；7/18-20 静默期，例行 cron 审计，无新里程碑

---

## 🟢 进行中

### ACCA 知识网络维护
- **启动**: 2026-06-14 (F1 起步)
- **当前范围**: 已远超 F1 — F2-MA 22章 + IFRS/IAS 27文件 + VAS 23文件 + F1 30+文件 + Cross-Border + M&A
- **Vault**: `ACCA-Knowledge-Network/` (183 文件, Obsidian, 全英文) + `knowledge-base/` (23 文件)
- **里程碑**:
  - [x] F1-BT 全部章节（30+ 文件）
  - [x] F2-MA 全部章节（22 文件, 2026-07-09）
  - [x] IFRS/IAS 国际准则重建（27 文件, 2026-07-09）
  - [x] VAS 越南准则完整建设（23 文件, 2026-07-09）
  - [x] KHOA DUNG M&A案例入库 + Plan A 重构（7/11-7/13）
  - [ ] Daryl 深度验收 Vault
  - [ ] 心理学域子分类确认
  - [ ] 知识库共享部署（只读给所有 Agent）

### OPC看板方法论卡片集成
- **启动**: 2026-06-21
- **Workflow**: Daryl 7/5 完成 11 节点类型化流水线（两个 isCore: 提取方法轮 + Self分发 decision 节点）
- **已完成**: vault 初始化 / 2张卡片 / 技术架构确认 / Workflow 定型
- **阻塞**: ⏳ 等待 Daryl 确认方向后找 Kitty 开第6模块

---

## 🔵 已完成（2026-07-06 至今）

### 周度知识树树叶收集（2026-07-17）
- Daryl DM 指令：跨 agent 收集 Bryson + Balance 近期工作关键叶子
- SAGE Checker 三轮（两轮 FAIL→修改后 PASS 9/9/8）
- 已落盘 4 片：B1+B2(雅思移动端适配)/B3(edit工具教训)/B4(Playwright验收模板)/L2+L3+L4(越南债转股法律框架)
- 待 Daryl 确认后落盘：B5(provenance gap)/L1(PIT回写)/L5(财务负责人自保框架，待定位置)
- Knowledge-base +4 文件，ACCA Vault ~169→183
- Git: commit 73fa01e

### KHOA DUNG Plan A 重构（2026-07-13）
- Daryl 反馈知识网络两大问题：树叶细节丢失 + 关联跳转不一致
- Plan A: 190→461行，合并 Balance 4份原始报告完整内容
- 新增三阶段税负拆解/6错误完整纠正/现金安全验证/方案演进轨迹
- 链接规范标准化：🔗(树叶→树叶,8项) + 📂(Home页导航,4项)
- frontmatter 加 `type: leaf` + `parent: Home` 元数据

### KHOA DUNG 目录重组 + PIT 路径规范（2026-07-12）
- KHOA DUNG → 02-Finance/M&A/，PIT速查 → 01-Financial/Tax/PIT/PIT-Vietnam/
- 补建受托支付通道节点（02-Finance/Capital-Raising/Bank-Loan/Project-Loan/）
- Wikilink 全量修复 + 旧目录迁移说明

### KHOA DUNG M&A案例知识树入库（2026-07-11）
- Balance 3份报告 → Self 提炼 3 条可复用方法论 + 4 新文件 + 2 索引更新

### ACCA知识库大规模搭建（2026-07-09）
- F2-MA 22 章节文件 / IFRS/IAS 27 文件（16独立标准+Conceptual Framework 14.7KB）/ VAS 23 文件
- 三个子 agent 并行执行，质量对标 4-5 级知识深度

### OPC Dashboard 设计系统规范（2026-07-07）
- Daryl 派调研任务：Linear/Stripe/Vercel/GitHub Primer/Notion/Raycast 六家设计系统
- 产出 DESIGN.md → `~/WorkBuddy/Claw/opc-dashboard/DESIGN.md`
- 四维度：设计语言/设计美感/交互逻辑/数据展示

### audit.sh 自进化基建对账升级（2026-07-15）
- Daryl 授权：新增 9.5 段两项对账（checker 执行率 / FAIL≥2 vs 当日检讨条目），JSONL 增 3 字段
- 修复原有 bug：步骤10 Git 备份 cd 缓存仓库后未切回，全团队审计 JSONL 长期写错位置（已加 cd $WORKSPACE）
- Kitty 独立核实：无下游读取受影响，bugfix 安全保留；117条错位历史待 Daryl 拍板

### 记忆系统 v3 — project 文件部署（2026-07-06）
- Kitty 宣布 v3 上线，Self 创建 project_Self.md
- Cron 每日 07:00/13:00/19:00 检查新鲜度

---

## ⚪ 归档

### 关联方与股东借款 — 跨体系知识树
- **完成**: 2026-07-02～07-03 (Daryl marked Done)
- **产出**: IAS 24 / IFRS 9 / IAS 32 / VAS 26 四节点 + Cross-Border Hub + 案例链接
- **Git**: commit 988cd48 (Desktop clone)，push 失败（Gitea 未运行）
- **方法论**: 乔木（财务准则锚点）vs 藤蔓（技术无统一锚点）

### VAS 知识树 + 跨境对比网络
- **完成**: 2026-06-22～07-04 (Daryl marked Done via OPC Dashboard)
- **产出**: VAS 5 节点 + 跨境对比 6 节点 + FS-税务耦合度模型
- Daryl 四条核心结论全部纳入，已向 OPC 群聊汇报

### 03-AI-Tech 知识树全貌汇报
- **完成**: 2026-07-03
- **产出**: 完整树结构 + 藤蔓交叉点 + 43 文件汇总

### 视频分析交互Workflow 归档
- **完成**: 2026-06-29
- **来源**: Bryson 完整项目归档 (v1.0.0→v1.1.2, 6轮迭代)

### 贷款材料自动化处理 归档 (v2 完整版 + v3 方法论)
- **完成**: 2026-06-28 → 06-29
- **来源**: Balance 完整项目归档
- **产出**: 5 文件 + 8 个可复用方法论

### 知识系统架构设计
- **完成**: 2026-06-07
- **产出**: 五领域架构、Obsidian Vault 方案、双树对比网络设计

### 合规系统部署 (L0-L4)
- **完成**: 2026-06-15
- **产出**: startup.sh / pre-op.sh / post-op.sh / audit.sh + LaunchAgent plist

---

## 🟡 规划中

### 五大领域 — 心理学域初始化
- **优先级**: 中 | **依赖**: Daryl 确认子分类

### 五大领域 — 音乐域初始化
- **优先级**: 低 | **依赖**: 心理学域完成后

### 方法论去重合并
- FutureTextile-Wellname 案例 6 条可复用方法论 → lessons.md | **优先级**: 低

### 知识库共享部署
- 知识库完善后共享给所有Agent（只读）| **依赖**: Daryl 验收通过

---

## 📊 知识网络规模

| 模块 | 文件数 | 状态 |
|:---|:---:|:---|
| F1-BT | 30+ | ✅ 含考试结构/理论索引/课程衔接图 |
| F2-MA | 22 | ✅ 含 Mermaid/计算示例/考试热点 |
| IFRS/IAS | 27 | ✅ 16独立标准 + CF 14.7KB |
| VAS | 23 | ✅ 完整越南准则体系 |
| Cross-Border | 9 | ✅ 跨境对比网络 + 案例 |
| Tax/PIT | 2+ | ✅ PIT速查 + 受托支付 |
| M&A | 3+ | ✅ KHOA DUNG 案例 |
| 03-AI-Tech (Vault内) | 8+ | ✅ 视频分析 + 贷款自动化 |
| knowledge-base | 23 | ✅ 含树叶收集+跨agent经验沉淀 |
| **合计** | **206** | |

**五大领域**: 财务 / 金融 / AI技术 / 音乐 / 心理学 ← Daryl 确认替代健身

---

## 💰 成本归集

> 数据源: 每日审计仪表盘 (memory/2026-07-16.md, 7/16 00:07 审计)；7/17 无新审计（Cron 23:59 触发）

| 维度 | 金额 (USD) |
|:---|---:|
| 当日 (7/20 00:05) | $0.94 |
| 本月 | $28.67 |
| 全量累计 | $88.27 |

- ⚠️ 月预算 $20，本月已超支 $8.67（143.4%），需向 Daryl 报备超预算原因
- 7/18 单日 $10.94 异常高（已入账本月），7/19 $3.39，7/20 $0.94（截至 00:05 Cron）
- 主要消耗: 7/9-7/13 知识库大规模搭建 + KHOA DUNG 重构 + 7/17 SAGE Checker 三轮 + 7/18 异常日耗
- 口径结论（Balance 7/15 核实）: 累计读数以 append-only 台账为准，今日/本月以 live 自扫为准
