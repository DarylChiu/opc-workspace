# 第二期确定性基建开发 — 开发计划

> 创建: 2026-07-25 | 负责人: Kitty (main) | 级别: P2 自主
> 命名: 第二期确定性基建（Phase 2 Ops Infrastructure）
> 第一期: watchdog.sh / keepalive.sh / cost_scan / audit.sh / proj-update cron / 生活提醒

---

## 一、项目总览

| 字段 | 值 |
|------|-----|
| 项目ID | ops-center-phase2 |
| 状态 | 🟡 规划中 |
| 优先级 | P2 |
| 启动日期 | 2026-07-25 |
| 预计交付 | 2026-07-28 |
| 技术栈 | bash + python3 + markdown正则解析 + json解析 + cron |
| 部署位置 | `scripts/ops_center/` |
| 输出渠道 | OPC群聊（飞书）|

### 四个模块

| # | 模块 | 功能 | 触发 | 工时 |
|---|------|------|------|------|
| 1 | **阻塞扫描器** | 解析4 Agent project文件阻塞表格，按天数分级推送 | 每日08:00 | 3h |
| 3 | **成本越狱预警** | 单日>$3或月预算>80%自动预警 | 每日08:00 | 2h |
| 4 | **project新鲜度检查** | 任一project文件>24h未更新→提醒 | 每日08:00 | 0.5h |
| 6 | **搜索质量监控** | 预设query测试SearXNG，低于阈值告警 | 每日08:00 | 2h |

> 总计: **7.5h** | 成本: **<$0.50**（全部本地执行，无外部API调用）

---

## 二、模块详细设计

### 模块1 · 阻塞扫描器 `block_scanner.py`

**输入**:
```
~/.openclaw/workspace/memory/project_main.md
~/.openclaw/xiaofeng_workspace/memory/project_xiaofeng.md
~/.openclaw/workspace-balance/memory/project_Balance.md
~/.openclaw/workspace-self/memory/project_Self.md
```

**解析逻辑**:
1. 在每个文件中定位 `#### 风险/问题` 或类似的阻塞表格
2. 提取 `| 日期 | 风险/阻塞项 | 影响 | 措施 |` 格式的表格行
3. 计算阻塞天数 = 当前日期 - 记录日期
4. 分级: 🟢 <3天 / 🟡 3-5天 / 🟠 5-7天 / 🔴 ≥7天
5. 汇总输出

**输出格式**:
```
🔍 阻塞扫描 | 2026-07-26

🔴 紧急 (≥7天):
  • Xiaofeng·Loop Engineering — 阻塞14天, 等待Daryl发起讨论
  • Self·树叶收集 — 阻塞8天, 等待Daryl确认落盘

🟠 关注 (5-7天):
  • Xiaofeng·洗稿MVP — 7天无需求输入

🟡 提醒 (3-5天):
  • Balance·差旅费 — 3天等待Daryl二次修改
  • Balance·贷款v-next — 3天等待规则

📊 统计: 总计16项阻塞 | 🔴2 🟠1 🟡3 🟢10
```

**验证标准**: 手动改某项目文件阻塞日期为8天前 → 脚本输出🔴 → 通过

---

### 模块3 · 成本越狱预警 `cost_alert.py`

**输入**: `cost_daily.json` (Balance cron维护的最新快照)

**规则**:
```
IF 今日成本 > $3:
  → ⚠️ 单日成本预警: 今日$X.XX，超过$3阈值

IF 月成本 > (总月预算 × 0.8):
  → ⚠️ 月度预算预警: 本月$X.XX/$XX.XX预算 (XX%)

IF 今日成本 > $5:
  → 🔴 严重越狱: 今日$X.XX，请立即检查
```

**月预算配置** (从openclaw.json或硬编码):
```
Kitty:  $15 | Bryson: $20 | Balance: $10 | Self: $10 | 合计: $55
```

**输出**: 正常时不输出，异常时追加到日报。

**验证标准**: 手动将cost_daily.json今日改为$10 → 脚本输出🔴 → 通过

---

### 模块4 · project新鲜度检查 `freshness_check.sh`

**逻辑**:
```bash
for each project_file; do
  age_hours = (now - file_mtime) / 3600
  if age_hours > 24:
    alert "⚠️ {agent} project文件 {age_hours}h未更新"
  if age_hours > 48:
    alert "🔴 {agent} project文件 {age_hours}h未更新，Cron可能失效"
done
```

**输出**: 全部新鲜时不输出，异常时追加到日报。

**验证标准**: touch一个文件为26小时前 → 脚本输出⚠️ → 通过

---

### 模块6 · 搜索质量监控 `search_quality_monitor.py`

**预设测试query** (来自M2搜索基准的39条query中选5条代表性):
```
1. "Python asyncio gather vs wait difference"  (常规-技术)
2. "越南 Circular 200 固定资产折旧 最新修订"   (冷门-越南法规)
3. "2026年7月 越南 个人所得税 累进税率表"       (时效性-越南)
4. "Cloudflare Workers Durable Objects SQLite"  (常规-技术)
5. "site:arxiv.org multi-agent orchestration"    (精确-学术)
```

**评估逻辑**:
1. 对每条query调用 SearXNG API (`http://localhost:8888/search?q=...&format=json`)
2. 检查: 返回结果数 ≥ 3? 结果相关性（标题/摘要不包含明显无关词）
3. 统计: 5条中几条有问题

**分级**:
```
5/5 正常 → ✅ 搜索正常
3-4/5 → ⚠️ 搜索质量下降
0-2/5 → 🔴 搜索严重异常
```

**验证标准**: 故意断掉SearXNG → 脚本输出🔴 → 通过

---

## 三、集成方案

### 主脚本 `opc_ops_center.sh`

```bash
#!/bin/bash
# OPC运营中枢 - 每日08:00由cron触发
# 按序执行4个模块，汇总输出到OPC群

WORKSPACE=/Users/zhaoyuzhao/.openclaw/workspace
SCRIPTS=$WORKSPACE/scripts/ops_center

# 1. 阻塞扫描
BLOCK_OUT=$($SCRIPTS/block_scanner.py)

# 2. project新鲜度
FRESH_OUT=$($SCRIPTS/freshness_check.sh)

# 3. 成本预警
COST_OUT=$($SCRIPTS/cost_alert.py)

# 4. 搜索质量
SEARCH_OUT=$($SCRIPTS/search_quality_monitor.py)

# 汇总 → 仅当有异常时才推送
if [ -n "$BLOCK_OUT" ] || [ -n "$COST_OUT" ] || [ -n "$FRESH_OUT" ] || [ -n "$SEARCH_OUT" ]; then
  MESSAGE="📊 OPC运营日报 | $(date +%Y-%m-%d)
$BLOCK_OUT
$COST_OUT
$FRESH_OUT
$SEARCH_OUT"
else
  MESSAGE="📊 OPC运营日报 | $(date +%Y-%m-%d)
✅ 全部正常，无异常项"
fi

openclaw message send --channel feishu --account default \
  --target chat:oc_7d71d54d87cbd265d9c3811bc59840b2 \
  --message "$MESSAGE"
```

### 文件结构
```
scripts/ops_center/
├── opc_ops_center.sh          # 主脚本（cron入口）
├── block_scanner.py           # 模块1: 阻塞扫描
├── cost_alert.py              # 模块3: 成本预警
├── freshness_check.sh         # 模块4: 新鲜度检查
├── search_quality_monitor.py  # 模块6: 搜索质量
├── test_queries.json          # 搜索质量测试query配置
└── README.md                  # 部署说明
```

### Cron条目
```
0 8 * * * bash /Users/zhaoyuzhao/.openclaw/workspace/scripts/ops_center/opc_ops_center.sh >> /tmp/ops_center.log 2>&1
```

---

## 四、里程碑

| 里程碑 | 内容 | 交付物 | 预计完成 |
|--------|------|--------|----------|
| M1 · 核心开发 | 4个模块脚本编写+单元测试 | 4个脚本 .py/.sh | 7/26 |
| M2 · 集成测试 | 主脚本集成+人工构造异常场景验证 | 测试报告 | 7/27 |
| M3 · 部署上线 | crontab安装+3天空跑观察 | 零误报确认 | 7/28 |

---

## 五、验证清单（每个模块上线前必须通过）

| 模块 | 测试场景 | 预期输出 | 通过标准 |
|------|---------|---------|---------|
| 1 阻塞扫描 | 构造8天前阻塞项 | 输出🔴 | 误报=失败 |
| 1 阻塞扫描 | 构造1天前阻塞项 | 输出🟢/不显示 | 误报=失败 |
| 3 成本预警 | 今日成本改为$8 | 输出🔴严重越狱 | 不漏报 |
| 3 成本预警 | 今日成本改为$1.50 | 无输出 | 不误报 |
| 4 新鲜度 | 文件mtime改为26h前 | 输出⚠️ | 不漏报 |
| 4 新鲜度 | 文件全部新鲜 | 无输出 | 不误报 |
| 6 搜索质量 | SearXNG正常运行 | 输出✅ | 不漏报 |
| 6 搜索质量 | SearXNG断掉 | 输出🔴 | 不漏报 |

**铁律**: 任意一个场景不通过 → 不上线，修好再测。

---

## 六、与GEPA的本质区别

| 维度 | GEPA ❌ | 第二期确定性基建 ✅ |
|------|--------|-------------------|
| 技术 | LLM评估LLM输出 | bash+python正则解析 |
| 确定性 | 输出不可预测 | 固定规则，给定相同输入永远相同输出 |
| 验证 | 需要在生产中观察数天 | 5分钟构造测试用例，即时验证 |
| 失败成本 | ~$30-50开发成本 | ~$0.50全部开发成本 |
| 依赖 | 依赖模型质量变化 | 零外部依赖 |
| 回滚 | 难回滚，影响Agent行为 | 删掉cron条目即可回滚 |
| 类比 | 类似「让AI自己优化自己」 | 和watchdog.sh同级别 |

---

## 七、风险

| 风险 | 概率 | 影响 | 措施 |
|------|------|------|------|
| project文件格式不统一 | 中 | 阻塞扫描解析失败 | 先跑一遍4个文件确认解析兼容 |
| cost_daily.json路径变更 | 低 | 成本预警失效 | 读取Dashboard server.js中的路径常量 |
| SearXNG API间歇不可用 | 中 | 搜索质量误报 | 增加retry逻辑(3次)+网络超时5s |
| crontab PATH问题 | 低 | 脚本静默失败 | crontab头部已加PATH修复(7/15已修) |
| OPC群消息刷屏 | 低 | 干扰 | 仅在异常时推送，正常日一条汇总 |

---

## 八、成功指标

| 指标 | 目标 |
|------|------|
| 上线3天零误报 | 必须达成 |
| Daryl每日只需看1条消息替代翻4个文件 | 主要价值 |
| 任何阻塞≥7天自动被标记🔴 | 不再遗漏 |
| 成本异常当日发现（而非月底回溯） | 早发现早处理 |
