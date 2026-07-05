# Deepseek成本跟踪系统

## 简介
Bryson专属的Deepseek API成本跟踪系统，提供精确的token级别成本计算和项目分段追踪。

## 核心特性
- ✅ **精确成本计算**: 基于Deepseek官方费率 ($0.14/1M输入, $0.28/1M输出)
- ✅ **项目分段追踪**: 自动识别项目标签 (project_, teaching_, feature_)
- ✅ **实时监控**: 支持日/月成本阈值警报
- ✅ **详细报告**: Markdown格式报告，适合飞书卡片展示
- ✅ **集成就绪**: 可与OpenClaw Gateway无缝集成

## 系统架构
```
├─ deepseek_cost_tracker.py     # 核心成本追踪器
├─ deepseek_tracker_service.py  # 长期运行服务
├─ test_deepseek_integration.py # 集成测试
└─ start_deepseek_tracker.sh    # 启动脚本
```

## 快速开始

### 1. 生成成本报告
```bash
./start_deepseek_tracker.sh report
```

### 2. 启动长期服务
```bash
./start_deepseek_tracker.sh service
```

### 3. 实时监控模式
```bash
./start_deepseek_tracker.sh monitor
```

### 4. 检查成本警报
```bash
./start_deepseek_tracker.sh alerts
```

## 成本计算示例
```
输入tokens: 10,000
输出tokens: 5,000

成本计算:
输入成本 = (10,000 / 1,000,000) × $0.14 = $0.0014
输出成本 = (5,000 / 1,000,000) × $0.28 = $0.0014
总成本 = $0.0028
```

## 项目标签系统
系统会自动识别以下项目前缀：
- `project_` - 项目开发相关 (如: project_voice_mvp)
- `teaching_` - 教学相关 (如: teaching_ielts)
- `feature_` - 功能开发 (如: feature_cost_tracking)
- `debug_` - 调试相关 (如: debug_system)
- `test_` - 测试相关 (如: test_integration)

## 成本警报阈值
- **日成本警报**: $1.0 (警告: $0.8)
- **月成本警报**: $15.0 (警告: $12.0)

## 集成到OpenClaw

### 手动集成
在OpenClaw API调用前后添加追踪代码：

```python
from deepseek_cost_tracker import DeepseekCostTracker

tracker = DeepseekCostTracker()
tracker.set_current_project("ielts_teaching")

# API调用前...
# 调用完成后记录使用量
tracker.record_usage(
    input_tokens=response.usage.prompt_tokens,
    output_tokens=response.usage.completion_tokens
)
```

### 自动集成（未来计划）
计划修改OpenClaw Gateway的API调用链，自动拦截所有Deepseek API请求。

## 报告格式示例
```markdown
# 📊 Deepseek成本报告 - Bryson专属

## 📈 今日总览 (2026-04-10)
- **总成本**: $0.000680 USD
- **输入tokens**: 2,340 (65.0%)
- **输出tokens**: 1,260 (35.0%)
- **API调用次数**: 12次
- **平均每次成本**: $0.000057

## 🛠️ 项目分解
- **debug_system**: $0.000239 (35.1%)
- **feature_cost_tracking**: $0.000193 (28.4%)
- **teaching_ielts**: $0.000147 (21.6%)
- **project_voice_mvp**: $0.000101 (14.9%)
```

## 维护说明

### 数据库管理
- 主数据库: `deepseek_cost.db`
- 备份脚本: 每日自动备份到 `backup/` 目录

### 日志文件
- 服务日志: `deepseek_tracker_service.log`
- 成本记录: 存储在SQLite数据库中

### 性能考虑
- 异步IO处理，最小化性能影响
- 批量写入优化，减少数据库压力
- 内存缓存频繁查询结果

## 故障排除
1. **数据库锁定**: 重启服务或删除锁文件
2. **权限问题**: 确保对工作目录有写入权限
3. **导入失败**: 检查Python依赖 (sqlite3, aiohttp)

## 未来扩展计划
1. ✅ Web仪表板界面
2. ✅ 多用户支持
3. ✅ 与其他提供商对接 (OpenAI, Anthropic等)
4. ✅ 预算规划和预测

## 相关链接
- Deepseek官方费率: https://platform.deepseek.com/pricing
- OpenClaw文档: /Users/zhaoyuzhao/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/docs

---
*系统版本: 1.0.0 (开发中)*  
*最后更新: 2026-04-10*  
*维护者: Bryson / 吹点小风*
