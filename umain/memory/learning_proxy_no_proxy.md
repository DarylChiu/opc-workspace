# 教训：ALL_PROXY 必须配 NO_PROXY（2026-11-01）

## 事件
配置 ChatGPT/Codex 桌面版走代理时，设了 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` 全指向 `127.0.0.1:7892`。
结果 Electron 主进程网络正常（ChatGPT 能对话），但 Codex 子进程的 **本地 websocket** 报 `connection_refused`，日志累计 8 次 `rendezvous unavailable`。

## 根因
`ALL_PROXY` 是「兜底全部协议」的意思，**连发往 127.0.0.1 的连接也走代理**。
Codex 执行器架构：CLI 进程 ↔ 本地 AppServer 通过 loopback websocket 通信。
→ 本地连接被送进代理 → 代理不知道如何处理 → connection refused。

## 机制（永久执行）

### 凡是设置 HTTP_PROXY / ALL_PROXY，必须同时设置 NO_PROXY
```bash
NO_PROXY="127.0.0.1,localhost,::1,0.0.0.0,*.local"
```

### Electron 应用额外还需要
```
--proxy-bypass-list="127.0.0.1;localhost;<local>"
```

### 受影响的「本地回环服务」清单（配代理时容易踩）
- 本地 API server（localhost:PORT）
- Electron 主进程 ↔ 渲染进程 / utility 进程 通信
- MCP server（多数走 stdio 或 localhost）
- 编辑器 LSP / Debug Adapter
- 数据库本地连接（127.0.0.1:5432 等）
- Docker socket 转发

## 判定「代理配好了」的正确标准（本次踩过的第二个坑）

❌ 错误标准：看到一次成功 / 界面不报错 → 宣布搞定
✅ 正确标准：**连续观察 2-3 分钟，错误计数保持 0 且不新增**，且关键日志出现 `outcome=success`（不是只有 `recovered`）

`recovered` = 重试后成功（说明之前失败过）
`success` = 首次即成功（真健康）

## 差异维度声明
本次违反的维度：**验证充分性** —— 用「出现过一次成功」替代了「持续无错误」，在重试机制掩盖下产生了假阳性。重试型系统（websocket、rendezvous、自动重连）尤其容易给出这种假信号。
