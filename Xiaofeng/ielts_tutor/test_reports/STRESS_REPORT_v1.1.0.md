# IELTS Tutor v1.1.0 压力测试报告

> 日期: 2026-07-16 16:21 | 执行: Bryson | 脚本: stress_test_v110.py
> 判定: ✅ 四模块 × 5轮 全部通过（0 错误，数据完整性 ok，测试数据已清理）

## 结果汇总

| 模块 | 每轮负载 | 5轮错误 | p50 | p95 | 备注 |
|------|---------|--------|-----|-----|------|
| M1 数据层 | 20并发线程全链路写(create+transcript+评估+灌队列+统计) | **0/100** | 41-98ms | 235-431ms | SQLite WAL, integrity_check=ok, 100/100条精确落库 |
| M2 Dashboard API | 50并发×3端点 | **0/250** | 34-87ms | 61-116ms | stats/reviews/history |
| M3 跟读闭环 | tts×2 + attempt×3 并发(真实音频回灌) | **0/25** | - | attempt 5.7-6.0s | WER全部=0(范音回灌), 无异常打分 |
| M4 页面串联 | 30并发×3页面 | **0/150** | - | 6-25ms | /, /dashboard, /shadow |

## 压测发现并修复的问题 🐛
**首轮压测 M3 第2轮 5/5 请求失败**
- 根因: `/attempt` 的 STT 推理是同步调用，阻塞 FastAPI 事件循环最长 9s → 并发请求的 keep-alive 连接被拒 + 期间所有 API 卡死
- 修复: STT 挪入线程池 (`asyncio.to_thread`)，事件循环不再阻塞
- 复测: 5轮 0 错误，attempt p95 从 ~9s 降至 ~6s，且压测期间其他 API 不受影响

## 已知边界（非缺陷）
- attempt 延迟 ~2s/次(串行) — STT模型共享锁，跟读是单人交互场景，3并发为压测超载工况
- M3 并发场景下多个 attempt 同时通过会重复 mark_consolidated — 幂等操作无副作用
