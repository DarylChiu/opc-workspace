# main 看板历史归档（2026-08-25 瘦身剥离）

> 说明：project_main.md 瘦身时剥离的「已完成 / 归档 / 关键决策」历史段。
> 逐日「无进展」流水与多周进展详情在 daily diaries（memory/YYYY-MM-DD.md）+ git history + session transcripts 可完整追溯，不再重复存看板。

---

## 🔵 已完成项目

| 项目名 | 交付日期 | 工时 | 归档 |
|--------|----------|------|------|
| OPC看板 M1+M2 | 2026-06-28 | ~120h | — |
| 记忆系统v3 — project文件（模板+API+Cron+4Agent同步） | 2026-07-06 | ~6h | commit 690decf |
| SearXNG搜索质量迭代（M1修复+M2子代理中断+P0重启+P1方法论） | 2026-07-17 | ~4h | 7/18 验收通过 |
| 基建长线任务（成本根因+搜索基准+trace协议） | 2026-07-18 | ~6h | memory/subagent_runs/infra_longline_20260718/ |
| Maker-Checker 审查协议 — Self试点 | 2026-07-21 | ~2h | commit e72722d |
| 第二期确定性基建 · OPC运营中枢（4模块） | 2026-07-25 | ~7.5h | commit 2dba501c |
| Websearch 全面升级 v2.0 | 2026-07-29 | ~4h | commit 4fae35cb |
| 记忆 Cron consolidated 修复（audit-all-report.sh） | 2026-08-08 | ~1h | launchd 改指 |
| 补剂调研组A（VC/鱼油/镁/NAD+/姜黄素等） | 2026-08-09 | ~2h | memory/subagent_runs/supplements_research/ |

## ⚪ 归档

| 项目名 | 归档日期 | 状态 | 备注 |
|--------|----------|------|------|
| Sentinel 合规哨兵 v1.0 | 2026-07-15 | ⏸️ 搁置 | 风险较大；插件配置保留未激活 |
| Agent自进化基建 | 2026-07-21 | ⏸️ 搁置 | Daryl 暂停；GEPA 禁开；SAGE Checker + Reflexion 保留（仅校验） |

## 关键决策（P1 精华，全文在 git + 决策账本）

- 8/12 OPC 变现战略三连纠偏：资产=劳动力+管线+纪律+失败认知；代码库≠产品≠收入；先卖后建、卖结果不卖软件
- 8/12 完成度% 从汇报废除，验收标准=「链接+5分钟亲手操作」
- 8/12 变现≠目标，机制才是（回路断裂是 OPC 的病根）
- 8/5 decision-loop 立项：只加机制不加细节；方向级仍确认、细节级账本自主；错误预算周度循环
- 8/16 「自觉机制→挂载机制」改造（post-op 三查 / 验收证据字段 / 挂起 3天提醒 7天默认行动）——待 Daryl 确认
- 8/16 建议 M2 正式关闭（60% 虚报入病理库，剪辑转服务线）——待 Daryl 拍板
- 8/9 serveo 宕机 → cloudflared 备用隧道；长期方案 A 付费 $5/月 / B Named Tunnel 免费（推荐）——待 Daryl 确认
