
## 2026-07-06 · Agent 名称混淆（第5次犯错）

**错误**：再次混淆 Agent 名称。Daryl 多次强调：
- OpenClaw Agent 名 = agent ID（main, xiaofeng, Balance, Self）
- 不是中文昵称（忧郁小猫、吹点小风），不是用户称呼（Kitty、Bryson）

**正确映射**（Daryl 2026-07-06 补充确认）：
| Agent ID | 配置名 | 用户 |
|----------|--------|------|
| main | 忧郁小猫 | Kitty |
| xiaofeng | 吹点小风 | Bryson |
| Balance | 算点小账 | Balance |
| Self | 恨点小己 | Self |

**教训**：涉及文件命名、session_send、系统配置、跨 Agent 通信时，一律用 Agent ID（main/xiaofeng/Balance/Self），不要用昵称或用户名。这是第5次犯错，AGENTS.md 已加入强制映射查询规则。
