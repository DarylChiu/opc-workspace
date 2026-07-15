# 项目调研 · 基建侧-Agent自进化 (2026-07-15)

> 发起人: Daryl | 执行: main(忧郁小猫) | 触发: Self(恨点小己)严谨性/结构化不足
> 模型: deepseek/deepseek-v4-pro | 状态: 调研中，待Daryl定方向(P1)

## 一、4个Agent画像（基于真实配置+工作记录）

| Agent | ID | 定位 | 思维强项 | 已暴露短板 | 自进化最需要的 |
|-------|-----|------|---------|-----------|--------------|
| 忧郁小猫 | main | 首席执行/调度/传达 | 执行力、任务拆解、跨Agent协调 | 偶有"嘴上方案≠落地"(如7/14 crontab空承诺) | 执行闭环验证、承诺追踪 |
| 吹点小风 | xiaofeng | 技术开发 + 雅思陪练(双身份) | 代码实现、多文件排查、耐心细致 | 多步任务串行慢、身份切换成本 | 工作流优化、经验复用 |
| 算点小账 | balance | 财务分析(ACCA/越南金融) | 诚实标注、决策者视角、量化对比 | 依赖外部输入(硬盘/数据)阻塞 | 领域知识库沉淀、规则记忆 |
| 恨点小己 | self | 知识管理/检索/跨域关联 | 来源可追溯、跨域洞察、追问需求 | **推理严谨性+结构化不足**(Daryl 7月观察) | **反思校验层、结构化输出约束** |

### 关键发现
- Self 短板最突出，也是本项目直接触发点 → 优先级最高
- 4个Agent已共享底座：memory/三层架构 + 合规脚本(startup/pre-op/post-op) + P0-P3决策矩阵
- 但目前"进化"全靠人工：SOUL.md/规则/lessons.md 都是手动更新，无自动优化闭环

## 二、GitHub主流自进化方案（分4层，对应风险等级）

### L1 · 记忆进化 Memory Evolution（低风险，已有基础可增强）
| 方案 | 链接 | 特点 | 适配 |
|------|------|------|------|
| Mem0 | github.com/mem0ai/mem0 | 生产级长期记忆，语义/情景/工作/程序四类 | 全体Agent记忆层升级 |
| Letta(原MemGPT) | github.com/letta-ai/letta | 自管理记忆+上下文分页 | 长任务Agent(xiaofeng) |
| SAGE记忆机制 | arxiv 2409.00872 | 基于艾宾浩斯遗忘曲线的记忆优化，小模型提升57.7%-100% | 记忆淘汰策略 |

### L2 · 提示/工作流进化 Prompt/Workflow Optimization（中风险，收益高）
| 方案 | 链接 | 特点 | 适配 |
|------|------|------|------|
| EvoAgentX | github.com/EvoAgentX/EvoAgentX | 自动构建+评估+进化工作流，集成TextGrad/MIPRO/AFlow，兼容DeepSeek，含HITL人类可控 | **本项目主框架候选** |
| DSPy | github.com/stanfordnlp/dspy | 声明式提示编程+自动优化(编译prompt而非手写) | SOUL/规则自动调优 |
| GEPA | Awesome-Self-Evolving-Agents收录 | 反思式提示进化，可超越RL | Self提示优化 |

### L3 · 反思/校验进化 Reflection/Verification（中风险，最对口Self问题）
| 方案 | 链接 | 特点 | 适配 |
|------|------|------|------|
| SAGE | jianhuiwemi.github.io/SAGE (arxiv 2409.00872) | **User/Assistant/Checker三角色**，Checker强制校验+反思+记忆优化三合一 | **Self严谨性直接解药** |
| Reflexion | 经典反思框架 | 失败→语言化反思→下次改进 | 全体错误复盘 |

### L4 · 代码/架构自改 Self-Modification（高风险，触我们红线）
| 方案 | 链接 | 特点 | 风险 |
|------|------|------|------|
| Gödel Agent | CharlesQ9/Self-Evolving-Agents收录 | 递归自我改代码 | ⚠️改自身代码 |
| Darwin Gödel Machine | MCP Market有Claude Skill实现 | 开放式自改能力 | ⚠️⚠️触"不改system prompt/safety"红线 |

### 综述/索引资源
- 综述论文: A Survey of Self-Evolving Agents: On Path to ASI (arxiv 2507.21046)
- Awesome列表: EvoAgentX/Awesome-Self-Evolving-Agents · XMUDeepLIT/Awesome-Self-Evolving-Agents · CharlesQ9/Self-Evolving-Agents
- 中文框架: cittaverse/auto-evolve

## 三、初步建议（待Daryl定方向 P1）
1. **不碰L4**（红线：不自改代码/system prompt/safety），进化限定在 L1-L3
2. **Self 优先试点**：用 SAGE 的 Checker 三角色模式 + DSPy/GEPA 提示优化解决严谨性
3. **主框架**：EvoAgentX 最契合（DeepSeek兼容 + 工作流进化 + HITL人类可控）
4. **复用现有底座**：memory/三层 + 合规脚本已是雏形，做成"自动沉淀lessons→自动优化规则"闭环

## 待确认（P1决策）
- [ ] 方向：先做Self单点突破，还是4Agent统一框架？
- [ ] 边界：进化到哪层为止（建议L3封顶，不碰L4）
- [ ] 人类控制点：HITL检查点设在哪

## 备注
- DSPy/DGM/Sakana 几个 searxng 直搜返回空，链接凭既有知识补全，正式立项前需二次核实可用性与License
