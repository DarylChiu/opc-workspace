# 子代理任务摘要 — kb-mode-research (2026-10-15)

- **任务**: 调研主流 AI 知识库搭建模式 vs 我们的 ACCA 知识树；近几个月新技术路线；是否跟进
- **靶心（Daryl 定）**: 知识库能让使用人（Daryl + 其他 Agent）快速理解并引用
- **产出**: `memory/projects/KB-模式调研/00-调研报告-v1.md`（8 节 / 223 行）
- **检索**: 15 轮 web_search（12 英 + 3 中）+ 3 次 web_fetch（1 次 404）；40 条来源带 URL + 抓取日期 + 置信度
- **核心结论**: 跟进一条——把 Markdown 五域树升级为「编译式知识库 + 显式寻址契约」（index.md/log.md + 稳定节点 id + 四行契约 + 只读取数接口）；不跟进 GraphRAG 建图 / 独立向量库 / 托管记忆服务
- **两个关键发现**: ① Google OKF（2026-06-12 v0.1 / 07-24 v0.2）与我们现有形态同构，缺的是寻址契约不是技术栈；② 多源共识 + Anthropic 文件系统 just-in-time 检索 + Karpathy LLM-Wiki 均指向：219 文件规模上失败点不在检索算法，在取数路径（解释 4 个月 0 次 query_node）
- **低置信 4 条**: OKF 版本日期细节 / Mem0-Zep 基准数字 / 语义层降本 60% 预测 / llms.txt 有效性争议
- **推测 3 条**: 不上图与向量库无增益 / 补接口后 Agent 会来查 / 事件驱动嫁接优于先长齐树
- **trace**: `execution_trace.jsonl` 20 行，verify_trace.sh PASS（1 WARN：本文件曾缺失，已补）
