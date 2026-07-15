# HEARTBEAT.md — Balance

## 周期性任务

### 每日成本扫描 (23:45 Cron)
- **触发**: `openclaw cron` 每日23:45 GMT+7
- **流程**:
  1. 运行 `scripts/full_cost_scan.py` 全量.jsonl扫描
  2. 写兜底文件到本 workspace `data/cost_daily.json`（审计留档;live看板不读此文件）
  3. sessions_send 给 Kitty (agent:main, 30s超时)
  4. 若超时→降级：文件已就位，Kitty自行读取
  5. 快速验证 `curl --max-time 5 http://localhost:8765/api/costs`
  6. 23:59记忆审计汇报中包含成本仪表盘更新状态（确认/降级/异常）
- **⚠️ 超时保护**: Cron总预算240s，步骤1+2<60s，sessions_send 30s即放弃，不烧余额
- **⚠️ 端口确认**: OPC看板在 localhost:8765（node server）
- **⚠️ 路径确认(2026-07-15 Kitty核实)**: live看板=~/WorkBuddy/Claw/opc-dashboard (PID认cwd);
  ~/opc-workspace/Kitty/opc-dashboard 是**废弃死副本**,勿再写入/修改
- **口径(2026-07-15对账)**: 累计真值=data/cost_ledger.jsonl(append-only,只增不减);
  live自扫现存文件适合今日/本月窗口; 零成本调用两边均不计入cost/tokens/calls

### 汇率监控
- 工作日检查SBV中间价变动
- VND/USD大幅波动(>0.5%)时主动通知Daryl

### 报告生成
- 收到Daryl敞口数据后，24h内出分析框架
- 重大事项及时汇报，日常不打扰

## 提醒
当心跳触发时：检查是否有Daryl的待处理问题未回复。
