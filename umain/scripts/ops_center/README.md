# OPC 运营中心 (Ops Center)

自动化脚本集，用于 OPC 群聊运营日报生成。全部采用确定性解析，不依赖 LLM/API 调用。

## 脚本清单

| 脚本 | 类型 | 功能 |
|------|------|------|
| `block_scanner.py` | Python3 | 扫描4个project文件中的阻塞/风险项，按天数分级(🟢🟡🟠🔴) |
| `cost_alert.py` | Python3 | 检查cost_daily.json日/月成本，超过阈值报警 |
| `freshness_check.sh` | Bash | 检查4个project文件是否超24h/48h未更新 |
| `search_quality_monitor.py` | Python3 | 用5条预设query测试SearXNG搜索质量 |
| `opc_ops_center.sh` | Bash | 主集成脚本，串联以上4模块并发送OPC群聊日报 |

## 依赖

- **Python 3.9+** — 标准库即可，无额外pip依赖
- **Bash 3.2+** — macOS/Linux
- **openclaw CLI** — 用于发送群聊消息（`opc_ops_center.sh` 需要）
- **SearXNG** — 运行在 `localhost:8888`（仅 `search_quality_monitor.py` 需要）

## 项目文件路径

脚本中硬编码以下路径，修改时需同步更新：

```
main:     /Users/zhaoyuzhao/.openclaw/workspace/memory/project_main.md
xiaofeng: /Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/memory/project_xiaofeng.md
Balance:  /Users/zhaoyuzhao/.openclaw/workspace-balance/memory/project_Balance.md
Self:     /Users/zhaoyuzhao/.openclaw/workspace-self/memory/project_Self.md
成本数据:  /Users/zhaoyuzhao/WorkBuddy/Claw/opc-dashboard/data/cost_daily.json
```

## 安装

```bash
# 赋予执行权限
chmod +x /Users/zhaoyuzhao/.openclaw/workspace/scripts/ops_center/*.py
chmod +x /Users/zhaoyuzhao/.openclaw/workspace/scripts/ops_center/*.sh
```

## Crontab 安装

建议每天 09:00 和 21:00 各运行一次：

```bash
# 编辑 crontab
crontab -e

# 添加以下行
0 9 * * * /Users/zhaoyuzhao/.openclaw/workspace/scripts/ops_center/opc_ops_center.sh
0 21 * * * /Users/zhaoyuzhao/.openclaw/workspace/scripts/ops_center/opc_ops_center.sh
```

**注意**: crontab 首次安装时，取消 `opc_ops_center.sh` 末尾的 `openclaw message send` 注释行。

## 手动测试

```bash
cd /Users/zhaoyuzhao/.openclaw/workspace/scripts/ops_center

# 测试阻塞扫描
python3 block_scanner.py

# 测试成本预警
python3 cost_alert.py

# 测试文件新鲜度
bash freshness_check.sh

# 测试搜索质量（需要 SearXNG 在 localhost:8888）
python3 search_quality_monitor.py

# 测试主集成脚本（测试模式，不发送消息）
bash opc_ops_center.sh
```

## 输出说明

- **正常状态**: 各模块无异常时不输出任何内容
- **异常状态**: 按分级格式输出（🔴严重 🟠警告 🟡注意）
- **主集成**: 汇总所有模块输出，正常时显示"✅ 全部正常"

## 阻塞分级规则

| 天数 | 级别 | 含义 |
|------|------|------|
| < 3天 | 🟢 | 正常（不显示） |
| 3-5天 | 🟡 | 需关注 |
| 5-7天 | 🟠 | 需处理 |
| ≥ 7天 | 🔴 | 严重阻塞 |

## 成本预警规则

| 条件 | 级别 | 含义 |
|------|------|------|
| 今日 > $5 | 🔴 | 严重越狱 |
| 今日 > $3 | ⚠️ | 单日预警 |
| 月度 > 80% 总预算 | ⚠️ | 预算预警 |
| 月度 > 总预算 | 🔴 | 已超预算 |
| 个人月度 > 个人预算×80% | ⚠️ | 个人预算预警 |
| 个人月度 > 个人预算 | 🔴 | 已超个人预算 |

### 月预算配置

| Agent | 月预算 |
|-------|--------|
| Kitty | $15 |
| Bryson | $20 |
| Balance | $10 |
| Self | $10 |
| **合计** | **$55** |

修改预算：编辑 `cost_alert.py` 中的 `BUDGETS` 和 `TOTAL_BUDGET` 变量。
