# 项目成本归集模型 — 讨论纪要

> 来源：Balance (算点小账) 与 Daryl 2026-06-10 讨论记录
> 交付：知识管理体系 Self，用于归纳归档
> 状态：框架讨论阶段，待后续落地设计

---

## 一、背景与问题定义

Daryl 提出公司内部项目（AI Agent协同开发）需要一个**按项目维度归集API调用成本**的模型，目标是：
- 知道每个项目花多少钱
- 能对比同类项目成本
- 能分析优化方向

**核心痛点**：Daryl 之前在传统软件公司用过「员工工时→项目分配」的成本归集模式，认为**准确性不够，后续分析会南辕北辙**。

---

## 二、传统软件上市公司成本归集模式

### 三种主流方法

| 模式 | 原理 | 典型场景 | 核心缺陷 |
|------|------|---------|---------|
| **工时法** | 员工填timesheet → 工资费率×工时 → 分配到项目 | 传统外包（Infosys、中软国际） | 填8h≠有效8h；归属靠人记忆；无法区分有效/无效工作 |
| **作业成本法(ABC)** | 识别「活动」→ 找成本动因 → 按实际资源消耗分配 | 产品型SaaS公司 | 实施复杂，需要设计成本动因体系 |
| **R&D资本化法(IAS 38)** | 研究阶段费用化 / 开发阶段资本化 | 自研产品型（微软、用友） | 分界线判断主观（技术可行性标准） |

### 公共信息支撑

- **Activity-Based Costing**："assigns the cost of each activity to all products and services according to the actual consumption by each. Therefore, this model assigns more indirect costs (overhead) into direct costs compared to conventional costing." (CIMA)
- **Job Costing**："tracks the costs and revenues by 'job' and enables standardized reporting of profitability by job."
- **Cost Driver**："any factor which causes a change in the cost of an activity" — ABC的核心是找到正确的成本动因，而不是用时间做代理变量

---

## 三、工时法为什么对AI Agent工作场景完全失效

| 工时法的假设 | AI Agent的现实 | 结论 |
|------------|--------------|------|
| 工时∝成本 | Token消耗与成本直接相关，与时长无关 | **维度错误** |
| 人能准确回忆归属 | 人无法记住agent在哪个session做了什么事 | **归因不可靠** |
| 同类任务效率相近 | 不同模型、不同prompt策略成本差异巨大 | **不可比** |
| 事后填报可行 | 应该系统级自动标记 | **方法落后** |

**Daryl的判断**：用旧的工时分配框架去套AI agent的成本数据，是用模糊代理指标替代可精确测量的实际消耗。

---

## 四、AI Agent场景的独特优势

传统软件公司做不到我们能做到的：

| 能力 | 传统公司 | 我们 |
|------|---------|------|
| 成本数据来源 | 人工填报（主观） | 系统日志（客观） |
| 数据粒度 | 0.5小时/1小时 | 单次API调用级 |
| 可追溯性 | 不可回溯 | 完整jsonl可审计 |
| 归属准确性 | ±30-50% | 理论上±5% |
| 分析维度 | 只知道花了多久 | 知道token量、模型、调用意图 |

**核心insight**：我们每一笔成本都有完整的数字足迹——timestamp、agent_id、session_id、tokens_in、tokens_out、model、cost。这是传统工时法做梦都想要的数据基础。

---

## 五、建议的成本归集三层模型

```
Layer 1: 原始数据层 (already exists)
  └─ 每笔API调用: {timestamp, agent, model, tokens, cost, session_id}

Layer 2: 活动标记层 (需要设计)
  └─ session → project 映射
  └─ 调用意图分类（分析/执行/沟通/纠错）
  └─ 阶段标记（需求/设计/开发/验收/迭代）

Layer 3: 项目归集层 (需要构建)
  └─ 按项目聚合cost + token
  └─ 按阶段/agent/模型 多维拆解
  └─ 同类型项目横向对比
```

### 关键设计挑战（已识别）

1. **项目触发时点难判断**：Kitty讨论需求算是项目成本吗？何时算「启动」？
2. **跨项目并行**：同一个agent在同一时段可能服务多个任务
3. **归因颗粒度**：session级别的标记能否覆盖所有场景？
4. **验收边界**：迭代修改到第几轮算完成？

---

## 六、实战验证：Bryson项目成本监控

当前正在运行的实时监控实验，作为成本归集模型的实战数据源：

| 项目 | 详情 |
|------|------|
| 监控对象 | Bryson (xiaofeng)，使用 deepseek/deepseek-v4-pro |
| 监控窗口 | 10:30 起，12:00 开始每小时正点汇报 |
| 当前快报(10:30→11:29) | 23次调用 / 1,436,332 tokens / $0.4449 |
| 烧钱速率 | ~$0.45/小时 |
| 停止方式 | Daryl手动指令 |

对比数据：Kitty (main) 09:00-11:00 使用 claude-sonnet-4.5，71次调用 / 6,447,535 tokens / $9.8218（烧钱速率 $4.91/h）。

**结论**：不同模型价格差10倍以上（DeepSeek vs Claude Sonnet），同一个项目不同阶段用不同agent/模型，成本差异巨大——这正是需要精细归因的原因。

---

## 七、下一步方向

1. 跑完Bryson项目的完整监控数据
2. 基于真实数据设计 session→project 标记机制
3. 设计项目成本对比的指标体系（不仅看总金额，还看token效率、模型选择策略等）
4. 再与Self协作做知识归档和方案文档化

---

## 八、关键引用

- Daryl：「我之前做过软件开发公司的成本，员工成本按工时来分配到各个项目，我认为是准确性不够的，后续分析会变成南辕北辙」
- Balance：「工时法的假设在AI agent场景下全部失效——我们明明有更精细的数据，却用一个更粗糙的代理指标，确实会南辕北辙」
- Daryl：「比较复杂的是，项目成本的触发时点、交叉协作的剥离、并行任务的隔离——需要一整套成本核算方案」
- Balance：「最难的确实不是算钱，是归因」

---

*2026-06-10 | Balance (算点小账) ⚖️ | model: deepseek-v4-pro*
