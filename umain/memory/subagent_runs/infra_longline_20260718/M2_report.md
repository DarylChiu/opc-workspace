# M2 里程碑报告：SearXNG 质量基准测试集 + 每周自动抽检

**日期**: 2026-07-18  
**执行者**: 忧郁小猫子代理 (infra_longline_20260718)  
**状态**: ✅ 完成

---

## 一、基准测试集覆盖范围

### 测试集结构

| 维度 | Query数 | 语言分布 | 目标 |
|------|---------|---------|------|
| 常规 (normal) | 15 | 10 EN + 5 ZH | 验证主流技术/事件搜索质量 |
| 冷门 (cold) | 12 | 10 VI + 1 EN + 1 ZH | 验证小众话题/越南本地召回能力 |
| 陷阱 (trap) | 12 | 7 ZH + 5 EN | 验证对抗百科/广告/AI垃圾站过滤能力 |
| **合计** | **39** | | |

### 各类别典型 query

- **常规**: Kubernetes调度优化、Rust async对比、React Server Components原理、寄生虫电影分析等
- **冷门**: 越南行政改革、特产美食、传统工艺（nón lá làng Chuông、gốm Bát Tràng）、TempleOS哲学、荻上直子电影
- **陷阱**: "最好的手机"、"什么是区块链"、"免费VPN"、"how to make money online fast"、"SEO tips"等

### 每条 query 字段
- `id` — 唯一标识 (N/C/T前缀)
- `query` — 搜索词
- `category` — normal/cold/trap
- `language` — zh/en/vi
- `expected_domains` — 期望出现的优质域名（用于白名单评分）
- `min_relevance` — 最低期望相关性 1-5

---

## 二、评分规则 (v1.1)

### 评分维度（总分 0-100）

| 维度 | 分值 | 计算方式 |
|------|------|---------|
| 白名单命中 | 0-30 | 匹配query特定 expected_domains，每个+10，上限30 |
| 黑名单扣分 | ≤0 | 百科/广告/洗稿站，每个-15 |
| 相关性 | 0-30 | Top-5结果标题关键词匹配+snippet长度 |
| 结果数量 | 0-15 | ≥15→15, ≥10→12, ≥5→8, ≥3→5, 1-2→3 |
| 摘要质量 | 0-10 | 实质性摘要计数(>80字符)，每个+2，上限10 |
| 来源多样性 | 0-15 | 唯一域名×2，上限15 |

### 质量阈值
- **优秀** ≥80 | **良好** ≥60 | **可接受** ≥40 | **差** <40
- **告警触发**: 本周均分 < 基线均分的 85%

### v1.0 → v1.1 修复
初始版所有query得分100，原因是：摘要质量未设上限(20结果×5=100)、相关性对所有结果累加而非只看top-5。修复后区分度正常。

---

## 三、首次基线测试结果 (2026-07-18)

### 总体指标

| 指标 | 值 |
|------|----|
| 总Query数 | 39 |
| 总体均分 | **67.0** / 100 |
| 最高分 | 100 (N12: React Server Components 原理解析) |
| 最低分 | 27 (T05: 减肥最有效的方法, T07: 什么是人工智能) |
| 错误数 | 0 |

### 分类统计

| 类别 | 均分 | 最高 | 最低 | 域名命中率 | 分布 |
|------|------|------|------|-----------|------|
| 🔵 常规 | **76.7** | 100 | 37 | 86.7% | 0-20:0, 21-40:1, 41-60:1, 61-80:8, 81-100:5 |
| 🟡 冷门 | **63.3** | 80 | 40 | 50.0% | 0-20:0, 21-40:1, 41-60:4, 61-80:7, 81-100:0 |
| 🔴 陷阱 | **58.7** | 90 | 27 | 75.0% | 0-20:0, 21-40:2, 41-60:4, 61-80:4, 81-100:2 |

### Top 10 来源域名

| 域名 | 出现次数 | 类型 |
|------|---------|------|
| zhuanlan.zhihu.com | 30 | 中文问答/专栏 |
| medium.com | 26 | 英文技术博客 |
| reddit.com | 24 | 英文社区 |
| dev.to | 8 | 开发者社区 |
| blog.csdn.net | 8 | 中文技术博客 |
| postgresql.org | 7 | 技术官方 |
| developers.cloudflare.com | 6 | 技术官方 |
| vi.wikipedia.org | 6 | ⚠️ 黑名单域名 |
| m.fx361.com | 5 | 中文转载站 |
| cnblogs.com | 5 | 中文技术博客 |

---

## 四、引擎质量特征分析

### Brave API 表现

**优势**:
1. **英文技术搜索出色** — 常规英文query均分~80，域名命中率86.7%。Kubernetes、Rust、React等主流技术栈结果精准
2. **中文中等偏上** — 知乎、CSDN、掘金覆盖好，但专业中文站点(如cinephilia.net)出现频率低
3. **越南语可用** — 12条越南语query全部返回结果，Cold类均分63.3。但期望域名命中率仅50%，多依赖vnexpress.net等大站
4. **结果量充足** — 几乎所有query返回15-20条，无0结果情况

**劣势**:
1. **百科污染** — vi.wikipedia.org 出现在6条冷门query中（每次-15分）。中文query中百度百科也被触发黑名单
2. **陷阱query保护不足** — "什么是人工智能"、"减肥最有效的方法"等中文陷阱query得分低(27-28)，被百科和广告站淹没
3. **广告/低质站** — 部分query中出现 m.fx361.com(5次)、360doc(2次) 等转载/洗稿站
4. **冷门话题召回** — 荻上直子(日本小众导演)仅40分，3个黑名单域名扣分-45，说明对非主流文化话题召回质量差

### 评分系统敏感度
- N03(Paris Olympics): 命中olympics.com(+30)但wikipedia(-15)→85分，合理
- N14(LLM幻觉综述): 期望arxiv.org但大量vi.wikipedia(-30)→37分，精准反映质量
- T05(减肥): 百度百科+360doc(-30)+低相关性(7)→27分，陷阱检测有效

### 潜在改进方向
1. Brave API + Bing双引擎对比：当前只用Brave，无法评估Bing对越南语/中文的补充效果
2. 期望域名列表可扩展：如添加更多越南本地媒体(tuoitre.vn, thanhnien.vn, znews.vn)
3. 陷阱query可增加"医疗健康"类（当前只有减肥，可加"感冒吃什么药""最好的降压药"等）

---

## 五、周度抽检配置

### 文件
- **脚本**: `benchmark/weekly_check.sh`
- **逻辑**: 每周一08:00 GMT+7 运行 `run_benchmark.py`，结果存档到 `results_YYYYMMDD.json`
- **劣化检测**: 本周均分 < 基线67.0的85%(即<57.0)时，生成 `ALERT_YYYYMMDD.json` 并输出stderr
- **自愈**: 如SearXNG未运行，自动尝试启动

### Crontab 安装 ⚠️ 待执行
```
# SearXNG 周度质量抽检 (每周一 08:00 GMT+7)
0 8 * * 1 bash /Users/zhaoyuzhao/.openclaw/workspace/searxng-deploy/benchmark/weekly_check.sh >> /tmp/searxng_weekly_check.log 2>&1
```

**需主Agent执行**：按MEMORY.md规则，crontab系统级操作需先在OPC群发通知。安装命令已就绪，通知后执行:
```bash
(crontab -l 2>/dev/null; echo '0 8 * * 1 bash /Users/zhaoyuzhao/.openclaw/workspace/searxng-deploy/benchmark/weekly_check.sh >> /tmp/searxng_weekly_check.log 2>&1') | crontab -
```

---

## 六、后续优化建议

### 短期 (本周)
1. **安装crontab** — 发OPC群通知后立即安装
2. **扩展陷阱query** — 增加医疗健康类(感冒药、降压药)、金融类(最佳理财产品)
3. **添加Bing对比** — 修改run_benchmark.py支持双引擎对比模式

### 中期 (M3里程碑)
1. **自动化告警集成** — 优>15%时飞书通知
2. **期望域名自动更新** — 根据实际搜索结果动态调整白名单
3. **时间序列分析** — 连续多周结果作图，识别趋势性劣化

### 长期
1. **自适应阈值** — 根据历史数据动态调整告警阈值
2. **引擎A/B测试** — 同一query对比不同引擎组合的结果质量

---

## 七、文件清单

```
searxng-deploy/benchmark/
├── queries.json              # 39条基准query (v1.0)
├── scores.json               # 评分规则 (v1.1, 含基线数据)
├── run_benchmark.py          # 基准测试执行器 (v1.1)
├── run_benchmark.sh          # Shell入口（含自启动SearXNG逻辑）
├── weekly_check.sh           # 周度抽检脚本
└── results_20260718.json     # 基线测试结果
```

---

**决策记录**:
- [P3] 选择Python而非纯bash实现评分器 — bash处理JSON复杂度过高
- [P3] v1.0评分全100后重写v1.1 — 区分度是核心价值，必须修
- [P3] cold类query越南语为主(10/12) — Brave API对vi支持尚可，后续可扩展
- [P2] crontab安装需主Agent通知OPC群 — 系统级操作遵守MEMORY.md规则
