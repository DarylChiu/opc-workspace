# 搜索方法论 · Search Methodology v2.0

> 适用: 全体Agent | 更新: 2026-07-29 | 引擎: SearXNG(google+ddg+bing) + Brave API(web_search/web_fetch)

---

## 一、搜索引擎分层策略

```
搜索请求 → 查询类型判定 → 按路由规则选择引擎 → 结果后处理 → 输出
```

### 引擎路由表

| 查询类型 | 主引擎 | 兜底 | 说明 |
|----------|--------|------|------|
| 🔵 英文技术/编程 | Brave API (language=en) | SearXNG | API文档、框架、StackOverflow |
| 🟢 中文内容分析 | SearXNG (language=zh-CN) | Brave API(zh) | 影评、文学、人文分析 |
| 🟡 金融/政策法规 | Brave API(en) + site:限定 | SearXNG+site: | 法规原文、汇率、政策 |
| 🟠 越南本地信息 | SearXNG (language=vi) | Brave API(en) | 本地新闻、特产、行政 |
| 🔴 关键决策依赖 | SearXNG + Brave API 双搜 | 交叉验证合并 | 架构选型、合规、口径 |

### 各引擎定位

- **SearXNG**（google+duckduckgo+bing 3引擎）: 主力量搜索，覆盖中英越
- **Brave API（web_search）**: 英文技术首选，高相关性排序
- **Brave API（web_fetch）**: 深度内容提取，markdown转换后喂给模型

---

## 二、场景化搜索模板（6种）

### 1. 技术文档搜索
```
标准: [精确关键词] [版本号/年份] site:[官方域名]
示例: "Cloudflare Tunnel" "API configuration" 2026 site:developers.cloudflare.com
降级1: 去掉site限定 → 加 "tutorial" / "guide" / "documentation"
降级2: 引擎切换 Brave API
降级3: 仅关键词，取前5条 web_fetch 提取
```

### 2. 政策法规搜索
```
标准: [法规编号/名称] [年份] site:[gov域名/法律库]
示例: "Circular 12/2022/TT-NHNN" "foreign borrowing" site:sbv.gov.vn
降级1: site:thuvienphapluat.vn (越南法律库)
降级2: 英文翻译名搜 Brave API → web_fetch 提取
降级3: 直接访问官网手动检索
```

### 3. 创意/人文分析搜索
```
标准: "[作品名]" "[分析维度]" site:[优质平台]
示例: "寄生虫" "空间隐喻" "电影分析" site:zhihu.com
降级1: 去掉 site: 限定
降级2: 中→英翻译，搜 Google Scholar / academia.edu
降级3: "[作品名]" "review" "analysis"
```

### 4. 金融数据搜索
```
标准: [指标英文名] [时间范围] [单位]
示例: "USD/VND exchange rate" "July 2026" "SBV official"
降级1: 去单位 → 加 "latest" / "today"
降级2: 越南语关键词搜 SearXNG
降级3: 直接访问 SBV/XE.com/Bloomberg
```

### 5. 通用百科/生活搜索
```
标准: [核心问题] -百科 -广告 -推广
示例: "咖啡豆选择指南" -baike -tmall -jd.com
降级1: 简化到核心词 2-3 个
降级2: 英文搜 → 翻译回中文结果
```

### 6. 本地/越南信息搜索
```
标准: [关键词 vi] [地点限定]
示例: "làng nghề truyền thống" "Hà Nội"
降级1: 英文翻译搜
降级2: Google Maps / 本地论坛
降级3: 标注「信息不足」
```

---

## 三、搜索执行规范

### 3.1 执行流程

```
1. 判定查询类型 → 选引擎 + 场景模板
2. 构造 2-3 组不同维度关键词
3. 每组中英文各搜一次（关键决策加双引擎交叉验证）
4. 每次取前 10 条
5. 合并去重 → 后处理过滤 → 打分排序
6. 取 top 5-10 高分结果
7. 必要时 web_fetch 提取 top 3 全文
```

### 3.2 后处理规则

#### 黑名单自动过滤
| 类型 | 域名/关键词 | 处理 |
|------|------------|------|
| 百科无分析价值 | wikipedia, baike, MBA智库 | 过滤 |
| 付费墙 | medium.com(paywall), 付费内容 | 过滤 |
| 广告推广 | taobao, jd.com, 广告, 推广 | 过滤 |
| 低质洗稿站 | 360doc, 百文网, 瑞文网, m.fx361.com | 过滤 |
| AI垃圾站 | 无署名、无评论区的自动生成站 | 过滤 |
| 词典翻译 | cidian, dict, 翻译 | 过滤 |

#### 时效性加权
```
< 1年: +3
< 2年: +1
> 5年或无日期: -2
```

#### 白名单提权（按场景不同）
| 场景 | 白名单域名 | 权重 |
|------|-----------|------|
| 技术 | developers.cloudflare.com, docs.python.org, stackoverflow.com | +3 |
| 创意 | zhihu.com, douban.com, cinephilia.net | +3 |
| 金融 | sbv.gov.vn, bloomberg.com, reuters.com, thuvienphapluat.vn | +3 |
| 学术 | scholar.google.com, arxiv.org, cnki.net | +3 |

### 3.3 降级阶梯（通用）

| 轮次 | 动作 | 说明 |
|------|------|------|
| 第1轮 | 完整关键词 + 场景模板 + 引擎路由 | 最精确 |
| 第2轮 | 去修饰词，保留核心名词 + 扩大范围 | 降维 |
| 第3轮 | 切换语言 + 切换引擎 | 跨语言/跨引擎 |
| 第4轮 | 只用主体词 + web_fetch 深度提取 | 最大召回 |
| 第5轮 | 放弃，标注「信息不足」 | 诚实告知 |

---

## 四、质量自检清单

搜索完成后必做：

```
□ 搜索结果 ≥ 3 条相关结果？
  NO → 启动降级策略（至少2轮）

□ 前3条结果有时效性吗？（< 2年或标注日期）
  NO → 加时间限定重新搜

□ 有没有黑名单域名混进来？
  YES → 手动过滤

□ 结果覆盖了中英文两个语言吗？（关键查询）
  NO → 补搜另一个语言

□ 有没有更好的引擎组合应该试？
  考虑 → 关键决策类必须双引擎交叉验证
```

---

## 五、反馈与迭代

### 搜索失败记录
搜索质量差（3轮降级后仍无满意结果）→ 写入 `memory/search_feedback.jsonl`:
```json
{"ts":"ISO时间戳","agent":"Agent名","query":"原始query","engine":"引擎","issue":"失败原因","rating":1-5}
```

### 每周汇报
Agent周报附带：
- 搜索次数 + 引擎分布
- 质量评价（有无「完全没法用」的搜索）
- 如有搜索失败记录，汇总分析

---

## 六、快速参考卡片

| 你搜索的是... | 用什么引擎 | 关键词策略 |
|-------------|-----------|-----------|
| API/框架用法 | Brave API (en) | 精确关键词 + site:官方 |
| 中文影评/文学分析 | SearXNG (zh) | 作品+维度+site:知乎/豆瓣 |
| 越南法律/金融 | Brave API → SearXNG (vi) | 法规编号+site:gov |
| 汇率/市场数据 | Brave API (en) | 指标英文+时间+source |
| 技术选型对比 | SearXNG + Brave 双搜 | 多方案+多关键词 |
| 通用问题 | SearXNG | 去百科+去广告 |
