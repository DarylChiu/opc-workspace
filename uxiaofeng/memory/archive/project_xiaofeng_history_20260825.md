# xiaofeng 看板历史归档（2026-08-25 瘦身剥离）

> 说明：project_xiaofeng.md 瘦身时剥离的「已完成 / 归档 / 关键决策 / 风险」历史段。
> 多周进展流水与逐日状态在 daily diaries + git history 可追溯，此处保留决策/风险精华。

---

## 🔵 已完成项目

| 项目名 | 交付日期 | 状态 |
|--------|----------|------|
| 洗稿MVP v1.2.0 | 2026-07-18 | ✅ 内核卡 M1-M3 |
| IELTS 陪练 v2.0 M2 | 2026-07-16 | ✅ 延时优化达标 |
| IELTS 陪练 v2.0 M1 | 2026-07-05 | ✅ 双管线 90% |
| 视频分析交互 Workflow v1.x | 2026-07-04 | ✅ 三代迭代 |
| OPC 机制基建统一规范 v2.0 | 2026-06-15 | ✅ 同步 4 Agent |
| 成本追踪系统 | 2026-06-06 | ✅ 全 Agent 部署 |

## ⚪ 归档

| 项目名 | 归档日期 | 状态 |
|--------|----------|------|
| OPC总控看板 | 2026-06-14 | 已移交 Kitty |
| 视频分析 10fps Vision 管线 | 2026-07-04 | 被 Gemini V3 替代 |
| Agent自进化 | 2026-07-16 | 非现存任务移除 |
| ngrok 备用隧道 | 2026-07-16 | 非现存任务移除 |
| 洗稿MVP v1.2.0 | 2026-08-07 | standby（23天无输入） |
| Loop Engineering | 2026-08-05 | 移交 Kitty（决策自主环） |
| 视频分析交互 Workflow | 2026-08-07 | maintenance |

## 关键决策（P1 精华）

- 8/12 可用性实测：剪辑 v4.0 前端 0 行（60% 虚报，Bryson 认账）；完成度% 废除 → 「链接+5分钟操作」验收
- 8/14 Daryl 低谷对话闭环：三项目系统观（剪辑=工厂/雅思+Balance=产品/自媒体=渠道）+「先变小」战略 + 新痛点=找测试用户
- 8/15 Free Talk 持久记忆方案：单条持久会话（256K 上限 + 230K 软阈值压缩），否定多层记忆（烧 token）
- 8/15 DeepSeek 峰谷计价：8/16 16:00 UTC 生效（off-peak $0.22/$0.66，peak $0.44/$1.32）
- 8/15 题库改造：手写 120 题种子库省 LLM 生成费（实际 ~$0.05 vs 预算 $3）
- 8/17 DeepSeek V4-Pro vs V4-Flash 对比报告（Pro GA 8/13，价格 3x）；待决策是否任务分级切换
- 8/5 Loop Engineering 移交 Kitty；8/5 用户思维三层检查清单入 workflow-rules

## 关键教训（入 lessons.md）

- 8/8 DeepSeek v4 Thinking 模式吞 max_tokens → JSON 输出必须显式 `thinking disabled`
- 8/5 launchd 极简 PATH 致素材时长/ASR 空 → 补 PATH + shutil.which 绝对路径
- 7/24 git rebase 事故（dashboard.html 丢失）→ PROJECT_MANIFEST.md 权威版本标记
