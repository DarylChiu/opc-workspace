# 事故报告 · 2026-11-05 全天无法回复

## 一、现象
- 11-05 全天 Daryl 在飞书私聊发消息，我（main/Kitty）无任何回复
- 当日无实质会话记录，日记只有 23:59 cron 自动创建的骨架（"内容待记录"）
- 当日业务侧：0 交付、0 汇报、0 会议纪要

## 二、时间线（证据链）

| 时间（CST） | 事件 | 证据 |
|---|---|---|
| 11-05 20:29:58 | Daryl 发消息，session `0e5c8a6c` 启动，prompt 提交成功 | trajectory `prompt.submitted` |
| 11-05 20:32:37 | 模型**成功返回**（input 21,623 / output 3,288，cost 记录，finalStatus=success） | `model.completed` |
| 11-05 20:32:37 | **回复未送达** —— session 正常结束，但飞书侧无消息 | `session.ended` + Daryl 反馈 |
| 11-05 23:59:00 | 23:59 记忆归档 cron 触发 | cron run |
| 11-05 23:59:01 | LLM 立即报 `Connection error`（1.5s 内失败），`FailoverError: network connection error` | `56d03d36.jsonl` |
| 11-06 10:47 | Daryl 追问"人呢" | 当前 session |

## 三、根因

### 主因：代理配置指向一个没有服务监听的端口

`~/.openclaw/openclaw.json`:
```json
"proxy": { "enabled": true, "proxyUrl": "http://127.0.0.1:7892" }
```
实测（11-06 10:50）：
- `lsof -iTCP -sTCP:LISTEN | grep 7892` → **无任何进程监听 7892**
- 当前 shell env 仍 export `HTTPS_PROXY=http://127.0.0.1:7892`
- 但 `curl https://api.deepseek.com/` **直连正常**（401 = 接通，仅缺 key）→ **本机不需要代理就能访问 DeepSeek**

→ 网关所有出站 LLM 请求被塞进一个空端口。DeepSeek 在国内可直连，代理纯属多余，且代理挂了以后把正常链路一起拖死。

### 次因：失败被静默吞掉，无告警

1. **LLM 层**：`Connection error` 只写进 session jsonl，不通知任何人。连续 4 天出现同类错误（11-01、11-02、11-04 两次、11-05），从未升级。
2. **投递层**：20:32 那次是**模型答完了、消息没发出去**，系统判定 `finalStatus=success` → 计费 + 记成功，无人知道 Daryl 没收到。
3. **cron 层**：归档 job 状态 `error`、`deliveryStatus=unknown`，只写 run history，不发告警。
4. **心跳/审计层**：23:59 审计本该发现"今天 0 会话"，但它自己就死在 LLM 连接上，形成死锁 —— 唯一的守夜人跟失效组件共用同一条死链路。

### 附带损害
- 11-05 日记空壳；11-06 日记至今未建
- 11-01、11-02、11-04 归档 cron 同样全部 `Connection error` 失败，历史日记存在断层
- 回复内容本身（微风 API 故障实测分析）已生成但未送达，需 Daryl 重新索取

## 四、为什么连续 4 天没被发现
失败路径全部指向"日志"，没有任何一条指向"人"。而且 4 天里 cron 都失败在 1.5-16s 内的网络层，耗时太短，连超时告警都触发不了。

## 五、修复方案

| 优先级 | 动作 | 状态 |
|---|---|---|
| P0 | 关闭多余代理：`proxy.enabled=false`（DeepSeek 直连已验证可用）| 待 Daryl 批准 |
| P0 | 重启网关让配置生效，实测一次 LLM 调用 | 待执行 |
| P1 | 加「LLM 连续失败告警」：同 session 2 次或全局 3 次/小时 `Connection error` → 直接飞书推 Daryl | 待建 |
| P1 | 加「投递失败告警」：`model.completed` success 但 outbound 无 messageId → 记录并告警 | 待建 |
| P2 | 归档 cron 加 fallback：本地脚本兜底（不依赖 LLM）+ 失败直接推群 | 待建 |
| P2 | 补 11-05 / 11-06 日记 + 核对 11-01/02/04 断层 | 执行中 |

## 六、结论
不是"我没理你"，是**出口被一个空代理端口堵死了，而且堵死时没有任何人被告知**。改配置 30 秒能修，告警机制才是真正的缺口。

*记录：忧郁小猫 | 2026-11-06*
