# decision-loop M1 · 决策自主层工具 — 交付总结

> 子代理执行 | 2026-08-05 17:14-17:25 (GMT+7) | 负责人: main (忧郁小猫)
> 依据: LOOP_ENGINEERING_PLAN.md 八之二开发计划 M1 + 九全部小节
> 规则源: docs/ 4 份 M0 文档（需求分级模板 / 提问质量门禁 / 教训病理Schema / 错误预算规则）
> 基准: 「只加机制，不加细节限制」——工具只实现机制，字段/输出保持最小必要

## 交付物清单（5/5 完成）

| # | 交付物 | 路径 | 验证 |
|---|--------|------|------|
| 1 | 决策三分类器 | `scripts/decision_loop/decide.py` | 13 用例 100%（红线≥85%） |
| 2 | 决策账本 | `scripts/decision_loop/decision_ledger.py` + `decision_ledger.jsonl` | 3 用例全过 |
| 3 | 周度错误预算 | `scripts/decision_loop/error_budget.py` + `error_budget_ledger.jsonl` + `error_budget_state.json` | 6 用例全过 |
| 4 | 每日例外上报 | `scripts/decision_loop/daily_exception_report.py` + `exception_events.jsonl` | 冒烟+模块测试全过 |
| 5 | 周度批量审批 | `scripts/decision_loop/review_batch.sh`（输出 `reviews/review_<周一>.md`） | 两轮冒烟（空账本/种子数据） |

回归测试: `test_decide.py`（13 用例）/ `test_error_budget.py`（6 用例）/ `test_ledger.py`（3 用例）——**全部通过**

## 工具机制要点（对应规则源）

1. **decide.py** — 确定性关键词表零 LLM：三分类关键词分档计分（强=2/弱=1），最高分胜出；**平分按优先级 方向型>规则型>执行型**（上报/确认优先，安全优先）；无命中保守默认规则型（查模式库不停摆）。对接状态机：方向型→上报 Daryl，规则型→查模式库，执行型→自主+记日志。
2. **decision_ledger.py** — append-only JSONL；9 字段最小 schema（ts/agent/task/decision_type/chosen/alternatives/why/rejected/is_exception）；必填校验+类型白名单；查询按 agent/时间范围（含边界），损坏行跳过不中断。
3. **error_budget.py** — 按 docs/错误预算规则.md：分级 0.1/1/10（**10=P0 直接拦截：cost=0+blocked+退出码 3，不进预算**）；周一周期制跨周自动重置（归零+回升 L3）；**周累计≥预算才降档 L3→L2**（单错误不降档）；磨合期 `--grace` 只记账不耗预算；周度预算默认 2.0（占位常量可调）。
4. **daily_exception_report.py** — 三类例外白名单（超阈值风险/首次情境/用户明确不满）；事件 append 到 exception_events.jsonl；report 生成 markdown（标题+分组清单+建议动作），无例外输出「今日无例外」；`--since/--until` 范围汇总供周度复用。
5. **review_batch.sh** — 汇总本周 决策账本（按类型统计+明细表）+ 错误预算（消耗/剩余/档位/降档+明细）+ 例外汇总；生成 `reviews/review_<周一>.md`；**待确认区=方向型决策+例外**；**纠正入口提示**：capture_correction.sh → corrections_inbox → 周度蒸馏 → 模式库（闭环）。

## 验收红线对照

| docs 验收红线 | 落地 |
|---|---|
| 分类准确率 ≥85% | ✅ 100%（13/13） |
| 单错误从不直接惩罚/降档（10 级 P0 拦截除外） | ✅ test 2/6 验证 |
| 只有周总量超支才降档，下周自动重置 | ✅ test 3/4 验证 |
| 例外每天汇总上报一次，无实时打断 | ✅ 按日 report，无例外输出 |
| 磨合期内错误不耗预算 | ✅ test 5 验证 |
| 无任何「自报信心决定自主权」逻辑 | ✅ 工具零 LLM、零信心字段 |
| 纠正自动入病理库 | ✅ review 文档纠正入口→corrections_inbox |

## 关键设计决策（记入决策账本规范）

1. **分类裁决用权重计分+平分优先级，不用纯计数**：纯计数在「技术选型怎么取舍」（规则2 vs 执行2）会误判；计分+优先级在复合关键词冲突下稳定（用例 3/5/7 覆盖）。
2. **无命中默认规则型而非执行型**：宁可多一次带默认方案的确认，不可漏报方向（安全优先），与「方向型永远上报」呼应。
3. **P0 拦截用退出码 3 表达**（record 时 exit 3），便于上层脚本/cron 捕获直接上报；blocked 记录留痕供周度 review 汇总。
4. **review_batch.sh 用 python heredoc 聚合**（直接 import 三个工具模块复用查询函数），避免 bash 里解析 JSON 的脆弱性；shell 只负责路径/日期/输出与纠正入口提示。
5. **数据文件保持空文件交付**（decision_ledger/error_budget_ledger/exception_events 均为 0 行合法 JSON），运行数据由工具 append 生成，不留测试污染；error_budget_state.json 为初始状态（当前周/消耗 0/L3）。

## 复盘

- **顺利点**：M0 文档（尤其错误预算规则.md）把机制写得足够具体，五个工具都能直接对应到规则条款；沿用 scripts/evolution/ 的确定性关键词+权重计分模式，风格一致。
- **踩坑 2 处（已修复）**：①argparse 子命令场景下 `--ledger/--events/--budget` 放在顶层解析器导致子命令后传参报错——改为每个子命令注册公共参数；②review_batch 统计文案「执行型型」重复字。
- **测试发现的 1 处自测脚本 bug**：test_ledger 三用例共享同一临时文件导致计数断言失败——改为每用例独立临时账本。
- **给 M2 的提示**：review_batch.sh 的 `--week` 参数已支持指定周（供补跑）；例外上报与 error_budget 的 `--exception` 标记相互独立，试点时按「例外=三类事件」口径走 daily_exception_report.py；M2 剪辑MVP 接入时可用 `--grace jianji-mvp` 开磨合期。
