# M1 里程碑报告：成本数据不一致根因排查与修复

**任务**: `infra_longline_20260718` M1  
**日期**: 2026-07-18  
**权限**: P2（自主决策）  
**状态**: ✅ 完成

---

## 1. 根因分析

### 1.1 核心发现

通过编写 `compare_costs.py` 模拟双方扫描逻辑，发现：

| 维度 | Dashboard (live scan) | Balance (ledger) |
|------|----------------------|-------------------|
| 扫描范围 | `agents/*/sessions/` 1396个文件 | 全量 `.openclaw` walk 1444个文件 |
| 去重 | ❌ 无 | ✅ responseId 去重 |
| 数据持久化 | 仅当前文件 | append-only ledger (cost_ledger.jsonl) |
| 历史调整 | $20 Sentinel 事故 | 无 |

**关键结论: 当扫描同一组当前文件时，两个系统产生**完全一致**的结果**（$71.63, 7,946 calls）。差异来自两个叠加因素：

### 1.2 差异来源（按影响力排序）

1. **$20 Sentinel 调整**（Dashboard-only）  
   - 2026-07-07 Sentinel 误触发导致整夜调用 Claude Opus 4.8
   - 本地 JSONL 仅残留 2 条 cost=0 记录，被扫描规则丢弃
   - Dashboard 通过 `cost_adjustments.json` 手动登记 $20（Daryl 报备金额）
   - Balance 台账未包含此项

2. **Balance 的 append-only 台账**  
   - Balance 的 `cost_ledger.jsonl` 保留已删除/轮转的 session 文件中的成本记录
   - 目前台账多出 ~2,200 条已从磁盘消失的历史调用
   - 造成 Balance 台账总数（$84.62）> 双方实时扫描结果（$71.63）

3. **cost_daily.json 路径不一致**（基础架构问题）  
   - 运行中的 Dashboard: `/Users/zhaoyuzhao/WorkBuddy/Claw/opc-dashboard/`
   - Balance 写入 cost_daily.json: `/Users/zhaoyuzhao/opc-workspace/Kitty/opc-dashboard/data/`
   - 两个 Dashboard 副本，Balance 写入旧副本，运行中的 Dashboard 从未读取

### 1.3 数字拆解（7/18 11:00 GMT+7）

```
Dashboard 实时扫描（仅当前文件）:           $71.63
  + Sentinel 调整 ($20)                    $91.63  ← Dashboard 显示

Balance 台账（append-only ledger）:        $84.62  ← Balance 显示
  - 历史已删除文件中的条目 (~$12.99)        $71.63  （与 Dashboard 实时扫描一致）
  + Sentinel 调整 ($20)                    $104.62  ← 真正权威的全量成本
```

**七月月度**:  
- Balance 台账七月: $25.02  
- Dashboard 实时七月: $12.52 (JSONL-only)  
- Dashboard 显示七月: $25.02 + $20 = **$45.02**（台账基础 + 调整）

---

## 2. 修复内容

### 2.1 修改的文件

**`/Users/zhaoyuzhao/WorkBuddy/Claw/opc-dashboard/server.js`**

1. 新增 `COST_DAILY_BALANCE_FILE` 常量 — 指向 Balance 输出的 cost_daily.json
2. 新增 `loadBalanceCostDaily()` 函数 — 读取并映射 Balance 台账数据到 Dashboard agent ID
3. 新增 `BALANCE_AGENT_TO_DASHBOARD` 映射表 — 转换 Balance agent 名（含 emoji）到 Dashboard ID
4. 修改 `monthly[]` 构建逻辑:
   - **优先使用 Balance 台账的 month_cost**（更完整，含已删除文件的成本）
   - **叠加 cost_adjustments 中本月调整**（外部账单）
   - 台账数据超过 24h 旧时回退到实时扫描
   - 新增 `_liveUsage` 字段标注差异
5. API 响应新增 `_balanceLedger` 字段 — 提供 Balance 台账交叉参考

### 2.2 验证结果

```
Dashboard 显示本月: $43.70
  = Balance 台账本月 ($23.69) + Sentinel 调整 ($20.00) + 浮点舍入 ($0.01)
  ✅ MATCH！

Agent 明细:
  kitty:    $24.05 = 台账 $4.05 + 调整 $20.00
  xiaofeng: $12.09 = 台账 $12.09
  balance:  $4.63  = 台账 $4.63
  self:     $2.93  = 台账 $2.93
```

### 2.3 Git 提交

```
9254000 fix(M1): 成本数据一致性 — Dashboard 使用 Balance 台账+调整作为权威月度数据
82d79e9 pre-M1: snapshot before cost alignment fix
```

---

## 3. 遗留事项

### 3.1 🔴 高优先级

- **cost_daily.json 路径不一致**: Balance 的 `generate_cost_daily.py` 写入旧 Dashboard 副本路径，导致 Dashboard 读取的台账数据有 ~12h 延迟。
  - **建议**: 将 Balance 输出路径改为当前 Dashboard 的 `data/` 目录，或由 Dashboard 在每次刷新时主动运行 Balance 扫描（需要 Daryl 授权修改 Balance workspace）
  - **临时方案**: Dashboard 使用 cost_daily.json 但标注 age，超 24h 自动回退实时扫描

### 3.2 🟡 中优先级（待确认项）

- **Sentinel $20 调整确认**: 此金额基于 Daryl 口头报备，未与 OpenRouter 官网账单精确对账。建议 Daryl 确认 OpenRouter 7/7 实际支出后更新 `cost_adjustments.json`
- **调整金额是否应纳入 Balance 台账**: 若未来 Balance 也纳入外部账单登记，Dashboard 的调整可移除，完全以台账为准

### 3.3 ⚪ 低优先级

- Dashboard 的 `_scanStats.totalCost` 仍然报告实时扫描结果（含调整），未反映台账总数。这是有意的 — 实时扫描作为台账的交叉验证保留
- Dashboard 日志现在同时输出实时扫描和 Balance 台账对比，便于运维排查

---

## 4. 执行追溯

详见 `execution_trace.jsonl`，关键步骤:
1. 读取双方扫描代码 → 识别三种差异来源
2. 编写 `compare_costs.py` 对照统计 → 确认同数据源结果完全一致
3. 发现 Dashboard 双副本架构问题
4. 修改 server.js 集成 Balance 数据源 → 验证一致性 ✅
5. Git commit 前置快照 + 修复提交

---

**结论**: 成本不一致的根因是 **Balance 使用 append-only ledger（更完整）+ Dashboard 使用实时扫描（更即时）+ 外部调整未同步**。修复后 Dashboard 以 Balance 台账为基础、叠加调整项，数字直接可追溯。剩余路径不一致问题需 Daryl 授权后续修复。
