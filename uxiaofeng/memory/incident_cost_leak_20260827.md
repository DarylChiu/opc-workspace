# 事故记录 · 2026-08-27 成本泄漏（¥150 一天烧光）

## 级别: P0（资金泄漏）

## 时间线
- 08-26 下午：已有一次成本事故讨论（Balance 侦探模式 60 次工具调用 + 重试风暴 + 心跳），声称"止血全完成"
- 08-26 23:45/23:59：4 个 cron 触发 → **402 Insufficient Balance**（账户已空）
- 08-27 上午：Daryl 充值 ¥150 后又被烧 ~¥115，现余额 ¥34.89
- 08-27 10:00-10:15：Kitty 全面排查 + 关停

## 根因（三层）
1. **"止血"未真正落地**：声称 cron 全停，实际 4 个 enabled（含限时 4 分钟的成本扫描会话）。口头宣称 ≠ 配置变更，缺验证步骤。
2. **共享 API key 无隔离**：IELTS 等服务继承同一 DEEPSEEK_API_KEY，直连 api.deepseek.com，完全绕过 OpenClaw 账本/护栏。
3. **账本失真**：OpenClaw estimatedCostUsd 只反映会话侧消耗（$0.1 级），真实消耗（¥115+）不可见 → 成本看板失去预警意义。

## 机制教训（可复用）
- 教训 = 机制 + 参考物指针：
  1. **停用必须验证**：disable 后必须重新读取配置确认 0 残留（本次 4 个 cron 第一次没停干净）
  2. **进程必须查 launchd 复活链**：kill 进程前先查 plist/KeepAlive/守护脚本（searxng 有 launchd + keepalive while 循环双重复活）
  3. **API key 必须按服务隔离**：任何服务直连 LLM API 都必须独立 key + 独立账本，禁止继承 OpenClaw 主 key
  4. **共享 key 是账本盲区**：账本只能证明 OpenClaw 侧消耗，不能证明总额

## 行动清单（已完成）
- 4 cron disable 验证 0 残留 ✓
- 9 个 launchd 自启项 → .disabled ✓
- IELTS(871)/video_editor(865)/searxng(891,866,51703...)/cloudflared(1129)/ngrok 全部杀净 ✓
- 保留: expense_mvp + opc-dashboard（零 API）✓

## 遗留
- [ ] Daryl 查 DeepSeek 用量页，锁定真正烧钱源
- [ ] 决策：IELTS/video_editor/searxng 重开方式（独立 key / 不开）
- [ ] 提议 MEMORY.md 增补：图像识别本地 OCR 政策
