# Agent Report Protocol v1.0

各 Agent 通过写入共享目录向 Gosh 汇报状态。

## 汇报文件位置

```
/Users/zhaoyuzhao/WorkBuddy/Claw/reports/{agent}/YYYY-MM-DD.json
```

## 汇报 JSON 格式

```json
{
  "agent": "balance",
  "timestamp": "2026-06-01T22:55:00+07:00",
  "status": "working",
  "current_task": "Q2 成本差异分析 - 纺织原材料",
  "progress": 65,
  "tasks_completed": ["1月对账完成", "VAS折旧调整"],
  "blockers": ["等待 Daryl 提供 3 月出库明细"],
  "decisions_needed": ["是否将染料成本从制造费用重分类为直接材料？"],
  "notes": "毛利率波动 2% 疑似汇率因素，明天深挖"
}
```

## 字段说明

| 字段 | 必填 | 说明 |
|------|:--:|------|
| agent | ✅ | 固定值: balance / self / yueyu |
| timestamp | ✅ | ISO 8601 |
| status | ✅ | idle / working / blocked / done |
| current_task | - | 当前正在处理的任务简述 |
| progress | - | 0-100 百分比 |
| tasks_completed | - | 已完成任务列表 |
| blockers | - | 阻塞项（需要外部输入才能继续） |
| decisions_needed | - | 需要 Daryl 决策的事项 |
| notes | - | 自由备注 |

## 何时写汇报

1. 完成一个阶段性任务后
2. 遇到阻塞需要 Daryl 介入时
3. Daryl 主动要求查看进度时
4. 每天结束时写当日总结

## Dashboard 读取逻辑

- 读取所有 Agent 最新汇报文件
- 聚合 status / progress / blockers / decisions_needed
- 10 秒轮询更新
