# M1 报告 · GEPA 安装 + DeepSeek 兼容性验证

> 任务: gepa_self_l2b_20260718 · M1 里程碑
> 日期: 2026-07-18 22:15–22:25
> 权限: P2 PASS | 子代理: subagent-12d445d7

## 1. 安装结果

| 项目 | 状态 | 详情 |
|------|------|------|
| `pip install gepa` | ✅ 成功 | 版本 0.1.4，MIT license |
| `import gepa` | ✅ 成功 | API: `gepa.optimize()`, `GEPAAdapter`, `optimize_anything` |
| 额外依赖 | ⚠️ 需手动安装 | `pip install litellm`（gepa 未自动安装） |
| Python 版本 | ⚠️ 注意 | gepa 装在 Python 3.12；系统 `python3` 是 3.14 |

**安装命令完整版**：
```bash
/Library/Frameworks/Python.framework/Versions/3.12/bin/pip install gepa litellm
```

## 2. DeepSeek 兼容性测试

### 测试配置

- **数据集**: 3条 QA（2+2, Paris capital, sky color）
- **Seed prompt**: "You are a helpful assistant. Answer questions concisely and accurately."
- **max_metric_calls**: 15

### 结果

| 测试 | 模型 | 状态 | 耗时 | Best Score | Reflective Mutation |
|------|------|------|------|------------|---------------------|
| 1 | `deepseek/deepseek-chat` | ✅ PASS | 8.2s | 1.0 | 无（seed已满分） |
| 2 | `deepseek/deepseek-v4-pro` | ✅ PASS | 42.6s | 1.0 | ✅ 生成了一条优化prompt |

### LiteLLM 识别结果

| 模型名 | LiteLLM Provider | 可用 |
|--------|-----------------|------|
| `deepseek/deepseek-chat` | deepseek | ✅ |
| `deepseek/deepseek-v4-pro` | deepseek | ✅ |
| `deepseek/deepseek-reasoner` | deepseek | ✅ |
| `deepseek/deepseek-v3` | deepseek | ✅ |

## 3. DeepSeek Prompt Engineering 灵敏度分析

### v4-pro 的 Reflective Mutation 输出

在迭代 2 中，`deepseek-v4-pro` 作为 reflection_lm 生成了以下优化提示：

```
You are a helpful assistant that answers questions by producing only the exact answer string.  
- Do not add any surrounding words, explanations, punctuation, or formatting unless they are part of the answer itself.  
- The answer must match the expected canonical form exactly, including correct capitalization and spelling.  
- For example, if asked "What color is the sky?", you must output "blue" (all lowercase), not "Blue" or "Blue.".
```

**分析**:
- ✅ DeepSeek 对 prompt engineering **有响应** — 能产生有意义的结构化改进
- ✅ Mutation 质量不错 — 增加了输出格式约束 + 具体示例
- ⚠️ 数据集太简单（3条 QA，seed 已 100%），未能触发多轮进化
- **建议**: M2 使用真实复杂的 checker-log 数据时，预期 GEPA + DeepSeek 能正常产生有意义的 prompt 迭代

## 4. 首选配置

| 角色 | 推荐模型 | 替代方案 |
|------|---------|---------|
| task_lm | `deepseek/deepseek-v4-pro` | `deepseek/deepseek-chat`（便宜但能力弱） |
| reflection_lm | `deepseek/deepseek-v4-pro` | `deepseek/deepseek-chat`（预算紧张时） |
| API Key | 环境变量 `DEEPSEEK_API_KEY`（已配置，35字符） | - |

### 成本估算

- `deepseek/deepseek-chat`: ~$0.27/M input, ~$1.10/M output tokens
- `deepseek/deepseek-v4-pro`: 比 chat 贵约 2-5x
- M2 阶段预算可控（80 metric calls × 短 prompt）

## 5. 遇到的问题及解决

| # | 问题 | 原因 | 解决 |
|---|------|------|------|
| 1 | `ModuleNotFoundError: No module named 'gepa'` | pip 装到 Python 3.12，但系统 python3→3.14 | 用全路径 `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3` |
| 2 | `ModuleNotFoundError: No module named 'litellm'` | gepa 不自动安装 litellm | `pip install litellm` |
| 3 | `AttributeError: module 'gepa' has no attribute '__version__'` | gepa 0.1.4 无 `__version__` | 改用 `pip show gepa` 查版本 |

## 6. 结论

### 兼容性结论: ✅ 完全兼容

DeepSeek 可以正常作为 GEPA 的 task_lm 和 reflection_lm。两个测试模型均可调用，LiteLLM 正确路由 API 请求，reflective mutation 机制正常工作。

### 对 M2（Adapter 开发）的前置建议

1. **Python 解释器锁定**: 务必使用 Python 3.12 解释器，在脚本开头加 shebang
2. **依赖管理**: 确保 `gepa + litellm` 都安装在同一个 Python 版本
3. **数据集构造**: 用真实 checker-log 数据（≥20条），避免 seed 直接满分
4. **Adapter 开发**: 基于 `GEPAAdapter` 基类，在 `evaluate()` 中调用 SAGE Checker，返回 score + ASI feedback
5. **reflection_lm 选择**: 用 `deepseek/deepseek-v4-pro`（已验证可生成高质量 mutation）
6. **task_lm 选择**: 用 `deepseek/deepseek-chat` 即可（成本低，evaluation 不需要太强推理）
7. **注意**: DeepSeek API 可能有并发限制，`max_litellm_workers` 设 3-5 比较安全

## 7. 产物

| 文件 | 说明 |
|------|------|
| `M1_report.md` | 本报告 |
| `M1_results.json` | 原始测试结果 JSON |
| `test_gepa_deepseek.py` | 测试脚本（可复现） |
| `execution_trace.jsonl` | 执行跟踪日志 |
