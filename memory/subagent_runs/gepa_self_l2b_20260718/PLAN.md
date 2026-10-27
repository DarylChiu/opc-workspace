# GEPA 适配 Self · L2b 自进化基建

> 发起: Daryl 2026-07-18 22:15 | 权限: P2 PASS | 试点: Self | 框架: gepa-ai/gepa (MIT, 5.7k⭐, ICLR 2026 Oral)

## 架构设计

```
SAGE Checker ──→ 评估函数 (metric)
Reflexion检讨 ──→ ASI反思燃料
checker-log.jsonl ──→ 训练数据
约束门 ──→ 退化防护
```

## 里程碑

### M1 · GEPA 安装 + DeepSeek 兼容性验证 (1-2h)
- `pip install gepa` + import 验证
- 跑最简示例（DefaultAdapter, task_lm=deepseek/deepseek-chat）
- 验证 DeepSeek 对 system_prompt 修改的响应（prompt engineering 灵敏度）
- 确认 LiteLLM deepseek 模型名 + API key 配置路径
- 交付: M1_report.md + 兼容性结论

### M2 · CustomSystemAdapter + 数据集构造 + SAGE/Reflexion 对接 (2-3h)
- 基于 `optimize_anything` API 写 Self 专用 Adapter
- Adapter.evaluate(): 调 SAGE Checker 三维打分 → 输出 score + ASI feedback
- Adapter 读 Reflexion 检讨日志，注入相关条目为反思燃料
- 构造训练集 (20条): 7条 checker-log 真实记录 + 13条手工 benchmark
- 约束门实现: 总分≥基线 / 长度≤5KB / 必须含来源标注 / 禁用绝对化词汇
- 交付: self_gepa_adapter.py + training_dataset.json

### M3 · 首次优化运行 + A/B 效果对比 + 交付报告 (1-2h)
- 选 Self 最弱的场景（研究报告类输出）作为优化目标
- 跑 GEPA 优化（max_metric_calls=80, budget ~$2-5）
- A/B 对比: 优化前 prompt vs 优化后 prompt 分别产出→SAGE打分
- 写最终报告: 优化前后分数变化、GEPA 生成的变化分析、后续迭代规划
- 交付: optimized_prompt.json + M3_report.md

## 约束
- 不碰 Self 的 SOUL.md / IDENTITY.md（L4 红线）
- 只优化任务 prompt 模板（EVOLUTION.md 同级目录）
- 首次优化范围限定：研究报告类输出 prompt（测试成功后再推广到其他场景）
