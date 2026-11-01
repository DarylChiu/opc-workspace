# 国内程序员代理 / Codex / Claude Code 接入方案研究

> 研究日期: 2026-11-01 | 触发: Daryl 问「国内程序员一般用什么梯子、怎么用 Codex / Claude Code、GitHub 是否需要梯子」
> 环境: Mac mini · 联通广东 · 出口 112.96.112.68

## 一、实测结论先行（本机联通网络，2026-11-01 18:5x）

| 目标 | 结果 | 判定 |
|---|---|---|
| github.com | 200 · 0.94s · ip 20.205.243.166 | ✅ 可直连 |
| api.github.com | 200 · 0.45s | ✅ 可直连 |
| raw.githubusercontent.com | 200 · 5.9KB/s（小文件） | ✅ 可直连但慢 |
| codeload.github.com | 301 · 0.89s | ✅ 可直连 |
| git clone (github) | exit=0 成功 | ✅ 可直连 |
| Release 资产下载 | 200 · 3.5MB/s · 11MB/3s | ✅ 速度良好 |
| registry.npmjs.org | 200 · 2.57s | ✅ 可直连 |
| api.githubcopilot.com | 400（TCP+TLS 通，仅缺参数） | ✅ **Copilot 可用** |
| api.anthropic.com | 403 `Request not allowed` | ❌ 地区封禁 |
| claude.ai | 302 → `/app-unavailable-in-region` | ❌ 地区封禁 |
| api.openai.com | 8s/30s 超时 | ❌ 网络层阻断 |
| chatgpt.com | 8s/12s 超时 | ❌ 网络层阻断 |

**关键结论：GitHub 不需要梯子。** 这是国内最大误解之一——GitHub 本身未被墙，只是 DNS 解析常被污染/路由抖动，导致"时好时坏"。实测 clone / release 下载均正常。
**真正被封的是：OpenAI 全系（网络层超时）+ Anthropic 全系（地区封禁 403/302）。**

## 二、国内程序员代理工具栈（主流）

1. **Clash Verge Rev**（mihomo 内核 + GUI）— 当前最主流，跨平台
2. **mihomo（Clash.Meta）裸内核** — 服务器/CI 场景，本次给 Mac mini 装的就是这个
3. **sing-box** — 新一代，协议全，配置原生
4. **Shadowrocket（小火箭）** — iOS 侧
5. **Surge** — 付费精品，老牌 Mac 用户
6. **v2rayN / v2rayNG** — Windows / Android 传统派

节点来源两派：
- **机场（订阅）**：¥15-40/月，IPLC/IEPL 专线，省事，但有跑路/降级风险
- **自建 VPS**：RackNerd / BandwagonHost / Vultr，年付 $10-30，出口自控；缺点——**机房 IP 被 OpenAI/Anthropic 风控**，网页端容易弹验证，且 IP 可能整段被封

## 三、Claude Code / Codex 的三条接入路

### 路线 A · 代理 + 官方账号（原汁原味）
- 需要节点出口在支持地区（美/日/新等），且 IP 干净
- Claude Code: `npm i -g @anthropic-ai/claude-code`，登录走 claude.ai
- Codex: `npm i -g @openai/codex`，登录走 chatgpt.com
- ⚠️ 国内手机号/支付仍是坎：Claude 需外卡，OpenAI 需外卡或代充
- ⚠️ 风险：账号风控、封号、订阅费打水漂

### 路线 B · 第三方 API 中转站（国内最流行，无需梯子）
原理：中转站提供国内可达域名 + OpenAI/Anthropic 兼容协议，帮你转发到官方。
- **Claude Code**：改环境变量即可，无需代理
  ```
  export ANTHROPIC_BASE_URL=https://<中转站域名>
  export ANTHROPIC_AUTH_TOKEN=<中转站 key>
  ```
  注意：官方还有 `ANTHROPIC_API_KEY`；两者区别——AUTH_TOKEN 走 Bearer，API_KEY 走 x-api-key。中转站多用 AUTH_TOKEN。
- **Codex CLI**：改 `~/.codex/config.toml` 的 `model_provider` + `base_url`，指向 OpenAI 兼容端点
- ✅ 优点：国内直连、按量付费、可开发票、无封号风险
- ⚠️ 坑（务必注意）：
  1. **逆向接口**：部分站点用逆向/池化账号，模型不是真官方，质量与隐私都有问题
  2. **跑路风险**：小站随时消失，别大额充值
  3. **数据安全**：代码全部过第三方，商业项目慎用
  4. **计费不透明**：有的按 token 加价 3-10 倍
- 筛选原则：能开票 > 能看明细 > 能设限额 > 能退款 > 有无 IP 白名单；先小额试

### 路线 C · 国产模型替代（零门槛，无需任何网络手段）
Claude Code 与 Codex 都支持改 base_url 指向任意 Anthropic/OpenAI 兼容端点，因此可直接接国产模型：
- 实测国内端点全部秒通（2026-11-01）：open.bigmodel.cn 200/0.22s · api.deepseek.com 401/0.21s · ark.cn-beijing.volces.com 401/0.54s · api.moonshot.cn 200/0.40s
- 优点：完全合规、便宜、稳定、无风控
- 缺点：能力与 Claude Opus / GPT 顶配仍有差距，尤其是长任务 agent 场景

## 四、给 Daryl 的建议排序（Mac mini 场景）

1. **GitHub 不用管** — 实测正常，最多配 hosts 兜底 DNS
2. **Claude Code → 路线 B 或 C**：先用国内中转站小额试 Claude，或直接接 DeepSeek/GLM（成本极低）
3. **Codex → 只能路线 A 或 B**：OpenAI 网络层封死，没有第三条捷径
4. **梯子仍建议装**（本次已装 mihomo）—— 但它的价值在于「网页端 ChatGPT/Claude」和「npm/GitHub 偶发卡顿」，不是 GitHub 本身

## 五、反常识提醒
- 网上大量「GitHub 打不开 → 加 hosts」教程是**过时经验**（DNS 污染时代）。当前 GitHub 直连正常，hosts 反而可能因 IP 过期变慢
- 「机场推荐榜」几乎全是联盟推广，排名与佣金挂钩，不能当客观测评
