# M2 报告 · CustomSystemAdapter + 数据集 + SAGE/Reflexion 对接

> 任务: gepa_self_l2b_20260718 · M2 里程碑
> 日期: 2026-07-18 22:27–22:31
> 权限: P2 PASS | 子代理: subagent-8cb27bfe

## 1. 产物清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `scripts/evolution/self_gepa_adapter.py` | 670行 | Self GEPA Adapter，实现 `evaluate()`/`make_reflective_dataset()`/约束门/Reflexion注入 |
| `scripts/evolution/gepa_training_data.json` | 20条 | 训练数据集：7条 checker-log 真实记录 + 13条手工 benchmark |

## 2. Adapter 架构

```
SelfGEPAAdapter
├── evaluate(candidate, batch)
│   ├── _inject_reflexion_hints()      # 注入相关检讨规则到 system_prompt
│   ├── _call_deepseek_generate()       # DeepSeek API 生成 Self 输出
│   └── _call_sage_checker()            # subprocess 调 checker.py → 三维分数
│       └── weighted_score = t*0.35 + s*0.30 + r*0.35 (归一化 0-1)
│
├── make_reflective_dataset(candidate, eval_batch, components)
│   └── 从 trajectory 提取 {Inputs, Generated Outputs, Feedback, Scores}
│       供 reflection LM (deepseek-v4-pro) 生成优化后的 prompt
│
├── _validate_candidate(candidate) → (passed, violations)
│   ├── 长度 ≤ 5000 字符
│   ├── 必须含来源标注指令
│   └── 禁止词: 保证/100%/绝对
│
└── 数据加载
    ├── _load_training_data() → baseline = bad样本加权均分/10
    └── _load_reflexion_journal() → 3条检讨，按 bigram 匹配 task
```

### 关键设计决策

| 决策 | 理由 |
|------|------|
| checker.py 通过 subprocess 调用 | 避免 Python 版本冲突（checker.py 的 urllib 调用需要 Python 3.12） |
| DeepSeek generate 用 `temperature=0.3` | 评估需要稳定性，非创意场景 |
| Reflexion 匹配用 CJK 字符 bigram | 比整词匹配更鲁棒，`越南纺织业趋势分析`→`越南纺织业出口趋势` 可通过 bigram 重叠匹配 |
| `capture_traces=True` 时才记录 trajectory | 节约内存，reflective mutation 时才需完整 trace |

## 3. 数据集覆盖情况

### 3.1 总体统计

| 维度 | 数值 |
|------|------|
| 总条目 | 20 |
| 真实记录 (checker-log) | 7 (35%) |
| 手工基准 (benchmark) | 13 (65%) |
| 高质量 (good) | 15 (75%) |
| 低质量 (bad) | 5 (25%) |

### 3.2 类别分布

| 类别 | 数量 | 覆盖场景 |
|------|------|---------|
| 研究报告 | 7 (2 real + 5 bench) | 纺织业趋势/AI Agent趋势/代码生成进展/RAGvs长窗口/越南电商/Prompt Engineering |
| 知识管理 | 6 (2 real + 4 bench) | 知识树汇总/Daryl方法论/Self基建架构/Daryl协作偏好/OpenClaw技术栈 |
| 跨域关联 | 4 (0 real + 4 bench) | Hallucination vs False Memory/技术债vs知识债/进化vsPrompt优化/SoC知识架构 |
| 机制回答 | 3 (3 real + 0 bench) | 基建持续执行机制（3次迭代，PASS×0 FAIL×3） |

### 3.3 SAGE 分数分布

| 质量 | traceability (avg) | structure (avg) | rigor (avg) |
|------|-------------------|-----------------|-------------|
| good (n=15) | 8.5 | 9.0 | 8.0 |
| bad (n=5) | 5.8 | 6.6 | 5.2 |
| **基线 (bad 加权)** | — | — | **0.583** (归一化) |

## 4. 约束门规则清单

| # | 规则 | 阈值 | 违规后果 |
|---|------|------|---------|
| 1 | system_prompt 长度 | ≤ 5000 字符 | BLOCK：候选不通过 |
| 2 | 来源标注指令 | 必须含"来源/标注/引用/出处/溯源"之一 | BLOCK：候选不通过 |
| 3 | 禁止绝对化词汇 | 不含"保证"/"100%"/"绝对" | BLOCK：候选不通过 |
| 4 | SAGE 总分 | ≥ baseline (0.583) | 由 GEPA 的 Pareto/acceptance 机制处理 |

### 约束门测试结果（全部通过）

| 测试用例 | 预期 | 实际 |
|---------|------|------|
| Good prompt (含来源标注+无禁用词) | PASS ✅ | PASS ✅ |
| Missing source instruction | FAIL ❌ | FAIL ❌ (缺少来源标注) |
| Contains "保证"+"100%" | FAIL ❌ | FAIL ❌ (2条违规) |
| Too long (5056 chars) | FAIL ❌ | FAIL ❌ (超长) |

## 5. SAGE/Reflexion 对接方案

### 5.1 完整数据流

```
1. GEPA优化引擎启动
2. 候选 system_prompt → SelfGEPAAdapter.evaluate()
3. evaluate() 内部流程:
   a. _inject_reflexion_hints(candidate, task)
      → 从 reflexion_journal.md 3条检讨中匹配相关条目
      → 注入反思块到 system_prompt 末尾
   b. _call_deepseek_generate(augmented_prompt, task)
      → 调用 DeepSeek API 生成 Self 回复
   c. _call_sage_checker(task, generated_output)
      → subprocess 调 checker.py
      → 返回 {verdict, scores:{t,s,r}, issues, summary}
   d. 计算加权分数 → 返回 EvaluationBatch
4. GEPA 用 evaluation 结果决定接受/拒绝候选
5. GEPA 调 make_reflective_dataset() 构建反思数据
6. Reflection LM (deepseek-v4-pro) 读取反思数据 → 生成新的 prompt 候选
7. 重复 2-6，直至达到 max_metric_calls 或收敛
```

### 5.2 Reflexion 注入方案

- **解析器**: 正则解析 `reflexion_journal.md` 的 `## YYYY-MM-DD HH:MM · title` 条目
- **匹配算法**: CJK 字符 bigram 重叠度 ≥ 3 → 认为相关
- **注入格式**: 
  ```
  ## ⚡ 反思注入（来自过往检讨）
  1. **越南纺织业趋势分析**
     - 错误: 直接抛结论没标来源
     - 规则: 所有事实性结论必须先挂来源再写结论
  ```
- **注入时机**: 每次 evaluate() 调用前，按 task 动态注入

### 5.3 Reflective Dataset 格式

每条反思记录：
```json
{
  "Inputs": {"task": "原始任务描述"},
  "Generated Outputs": "Self 使用该 prompt 生成的输出（截断到2000字）",
  "Feedback": "审查结果 + SAGE评分 + 具体issues + 反思检讨规则",
  "Scores": {"traceability": 8, "structure": 9, "rigor": 8},
  "score": 0.730
}
```

## 6. 自我验证结果

### 6.1 单元测试（6/6 通过）

| # | 测试 | 结果 |
|---|------|------|
| 1 | Data Loading: 20训练样本 + 3检讨 + baseline=0.583 | ✅ |
| 2 | Constraint Gate: 4种违规场景全部正确拦截 | ✅ |
| 3 | Reflexion Injection: 纺织业任务匹配，天气任务不匹配 | ✅ |
| 4 | Evaluate: PASS记录生成 2360-2431 字，score 0.66-0.73 | ✅ |
| 5 | make_reflective_dataset: 正确产生产出 {Inputs, Outputs, Feedback, Scores} | ✅ |
| 6 | Dataset Validation: 20条目字段完整，分类正确 | ✅ |

### 6.2 集成验证

- **adapter + checker 链路通畅**: evaluate() 成功调 subprocess checker.py → 返回完整 JSON
- **DeepSeek API 正常**: 生成 + 审查双调用均成功
- **GEPA 接口兼容**: 返回的 EvaluationBatch 格式符合 GEPA 预期

## 7. M3 前置建议

### 7.1 优化运行参数建议

| 参数 | 推荐值 | 理由 |
|------|--------|------|
| `max_metric_calls` | 80 | 平衡探索空间与成本 |
| `target_component` | `system_prompt` | 首轮只优化 prompt |
| `task_lm` | `deepseek/deepseek-chat` | evaluate 用便宜模型 |
| `reflection_lm` | `deepseek/deepseek-v4-pro` | mutation 需更强推理 |
| `stopper` | `NoImprovementStopper(patience=5)` | 连续5次无改善自动停止 |
| 初始 seed prompt | 基于 benchmark 中 good sample 的共性特征合成 | 给一个较好的起点 |

### 7.2 初始 Seed Prompt 建议

```
你是Self，一个严谨的知识管理Agent。输出要求：
1. 所有事实性结论必须标注来源（文档名/URL/数据来源+时间）
2. 无法溯源的内容标注[推测]或[待验证]
3. 区分事实、推断、个人意见三类内容
4. 结论附置信度（高/中/低），基于证据强度
5. 引用git管理的文件需附commit hash
6. 机制/能力类陈述避免绝对化词汇，使用"理论上""依赖X机制""降低风险"等表述
7. 表格/列表结构化呈现，避免冗长段落
```

### 7.3 风险提示

| 风险 | 概率 | 缓解 |
|------|------|------|
| DeepSeek API 并发限制 | 中 | 单线程 evaluate，seq 调用 |
| checker.py subprocess 开销 | 低 | 每次约300ms fork开销，80次≈24s额外开销，可接受 |
| GEPA 对中文 prompt 优化效果未知 | 中 | 先用3-5次探索性运行确认方向正确 |
| 优化耗时过长 | 低 | 80 metric calls × ~15s/call ≈ 20分钟，在预算内 |

### 7.4 A/B 对比方案

1. **Baseline**: 当前 Self 使用的 system_prompt（从 EVOLUTION.md 或实际配置中提取）
2. **Optimized**: GEPA 优化后的 system_prompt
3. **测试集**: 从 benchmark 13条中随机抽 5条（研究报告2 + 知识管理2 + 跨域关联1）
4. **评估**: 两者分别在测试集上运行，SAGE Checker 打分，对比:
   - 加权总分变化
   - 各维度分数变化
   - PASS 率变化
   - prompt 长度变化

## 8. 决策记录

| 决策 | 级别 | 理由 |
|------|------|------|
| checker.py 通过 subprocess 而非 import 调用 | P2 | 隔离 Python 版本（checker.py 需要 Python 3.12，避免 import 污染） |
| 手工 benchmark 用 quality=good 的样本 | P2 | 让优化器学习"好"的标准，bad 样本由真实记录提供 |
| 跳过 benchmark 中跨域关联的真实数据 | P2 | checker-log 中无此类任务，但手工构造覆盖完整 |
| Reflexion 匹配阈值设为 bigram 重叠≥3 | P2 | 太严格(≥5)会漏报，太宽松(≥1)会误报；3是实测平衡点 |
| evaluate() 用 temperature=0.3 | P2 | 评估阶段追求稳定，非创意生成 |
