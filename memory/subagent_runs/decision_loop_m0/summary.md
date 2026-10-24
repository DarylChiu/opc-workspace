# decision-loop M0 · 机制冻结 — 交付总结

> 子代理执行 | 2026-08-05 17:05-17:30 (GMT+7) | 负责人: main (忧郁小猫)
> 依据: LOOP_ENGINEERING_PLAN.md 八之二开发计划 + 九原则审查
> 基准: 「只加机制，不加细节限制」

## 交付物清单（7/7 完成）

| # | 交付物 | 路径 | 验证 |
|---|--------|------|------|
| 1 | 需求分级模板 | `docs/需求分级模板.md` | 存在非空 (5138B) |
| 2 | 提问质量门禁 | `docs/提问质量门禁.md` | 存在非空 (3754B) |
| 3 | 教训病理Schema | `docs/教训病理Schema.md` | 存在非空 (5110B) |
| 4 | 错误预算规则 | `docs/错误预算规则.md` | 存在非空 (4656B) |
| 5 | AGENTS.md M0 条款 | `AGENTS.md`（追加区块，452→502 行） | 可读取，M0 条款在，只追加未改现有内容 |
| 6 | 看板 workflow 强制节点 | `opc_dashboard/data/workflows/jianji-mvp.json` | json.load 通过；gate 节点 status=blocked |
| 7 | 模式库种子病理 ×3 | `memory/evolution/failure_patterns.json` | json.load 通过；4 旧条保留 + 3 新 schema 条 |

## 关键设计决策

1. **workflow 命名**：目录下无现成剪辑MVP workflow（仅 video-analysis-pipeline），按 `data/workflows/{id}.json` 既有格式新建 `jianji-mvp.json`，id 用 ASCII 避免服务端兼容问题；方向确认节点用 `type=decision + config.mandatory=true + status=blocked` 表达「未确认禁入开发」。
2. **种子病理 reference 状态**：乱码文件名案例失败时素材命名规范尚不存在 → `artifact_state=absent`（示范三分支里 absent 分支：先建最小参考再动手）；设计语言/知识树 → `stable`。
3. **AGENTS.md 只追加**：以 `cat >>` 追加新区块，未触碰任何现有行。
4. **旧 schema 兼容**：存量 4 条 patterns（含 embeddings）数据原样保留，仅 stats 更新 4→7；schema_note 追加修订#4 说明。

## 验证结果（全部通过）

- ✅ 4 个 md 文件存在且非空
- ✅ failure_patterns.json / jianji-mvp.json / execution_trace.jsonl 全部 json.load 通过
- ✅ AGENTS.md 正常读取，含「决策自主环 M0 条款」区块
- ✅ workflow JSON 合法，方向确认=强制前置（blocked），边 e-dir-dev 门禁链完整
- ✅ trace 8 行（INIT + 7 交付物）
- ✅ 已 git commit（message 以 decision-loop M0: 开头）

## 复盘

- **顺利点**：项目文档（LOOP_ENGINEERING_PLAN.md）本身已把修订#4/#5 schema 写得很具体，落地时以机制层为准，未引入额外细节限制。
- **注意点**：任务要求用 sessions_send 通知 main session，但子代理工具集无该工具；本总结即最终消息，由系统自动回传 requester（main session）。
- **后续 M1 提示**：decide.py 分类器、error_budget.py、daily_exception_report.py 等工具实现时，本批文档是规则源；jianji-mvp workflow 可在 M2 试点时由 Bryson 按需补充实现层节点（机制已冻结，节点细节 Agent 自定）。
