# Lancer / Muse / Grok Bot 调研 + 工作流"外壳"架构判断

- 时间：2026-11-02
- 提问人：Daryl
- 数据分级：🟢 官方/实测　🟡 二手可信　🔴 存疑
- 模型：deepseek/deepseek-v4-flash

---

## 零、先校准一个前提（最重要）

Daryl 原话：
> "目前 openclaw 的 Agent 们没法获取社交身份，他们可以"

**这句话需要拆成两半看，因为「拿不到社交身份」和「LLM 能力不够」是两件不相干的事。**

| 能力 | 决定它的东西 | 换 LLM 能否解决 |
|---|---|---|
| 推理/写作/生成质量 | LLM 本身 | ✅ 能 |
| **拥有社交身份** | **账号凭证 + 登录会话的托管方式** | ❌ **完全不能** |

Muse / Grok Bot 之所以"能"用社交身份，**不是因为它背后的模型更强，而是因为它们拿到了你授权的账号登录态。**

- Grok Bot：官方原文 "Connect your X account in Grok Bot" —— **是你把你的 X 账号交给了它**
- Muse：官方定位是接入你的 email / calendar / payments —— **是你把你的个人账号交给了它**

**结论：这是「授权 + 会话托管」问题，不是「模型选型」问题。**
搞错这个前提，会去买一个根本不解决该问题的产品。

---

## 一、Lancer 是什么（有一半概率是你记错名字了）

**⚠️ 存在两个不同产品都叫 Lancer，都不是"LLM 工作流外壳"：**

### 1. `lancer.app` —— Upwork AI Agent
🟢 官网原文：
> "Lancer is an AI agent that finds perfect Upwork jobs and submits personalized proposals automatically"
> "Trusted by 400+ freelancers and agencies"

- 自动扫 Upwork 职位 → 10 分钟内投提案 → 个性化
- 官方宣称数据：60% 开信率 / 21.8% 回复率 / 12.5% 成交率，$12.02 per meeting（对比人工 $98.08）
- 30 天内帮用户发起 2,884 个 Upwork 客户对话
- **本质：一个垂直场景的自动化应用，不是通用外壳**

### 2. `lancer.work` —— AI Business Lifecycle Platform
🟢 官网定位："Automate business operations with AI. Connect founders with skilled freelancers."
- 连接创始人和自由职业者
- **本质：撮合平台 + AI 工具**

### 判断
🔴 **没找到任何叫 Lancer 的"LLM 工作流编排外壳"产品。**
你要找的那个东西，名字可能不是 Lancer（可能是 LangChain / Langflow / n8n / Dify / Flowise 这一类）。

**这个要跟你确认，不然调研方向全偏。**

---

## 二、Muse（Meta，2026-09-08 发布）

🟢 官方定位（about.fb.com）：
> "Muse is a secure, private personal AI agent that proactively helps people meet their goals"

- 长时任务执行，不是单轮问答
- 接 email / calendar / payments / health services
- 上 Meta AI 眼镜、有电视广告投放

**⚠️ 但它不是"社交身份"产品**，是**个人事务管家**。而且有两个硬问题：

1. 🔴 **没有公开开发者 API**（未查到；消费级产品，主要走 App）
2. 🔴 **隐私争议很大**：TIME 2026-10-06 调查报道 —— Muse 会 map 用户及其联系人（**包括不用 Muse 的人**），跨系统共享匿名化信息

**结论：Muse 不适合作为工作流的 LLM 调用层，也不适合作为身份层。** 它是 Meta 抢消费入口的产品。

---

## 三、Grok Bot（xAI，2026-08-11）—— 这个值得认真看

### 它到底是什么
🟢 官方文档（docs.x.ai/grok-bot/overview）：
> "Each Bot works on a **persistent cloud computer with a browser, filesystem, and terminal**, so tasks finish in your real tools"

🟢 X 官方账号原文：
> "Bots are AI teammates that do real work for you. **They sign in to your tools, use them just like you do**, and come back with finished work"

**它是"AI 用浏览器像人一样登录操作"，不是"AI 调 API"。**

### X 集成（这是 Daryl 关心的点）
🟢 x.ai/news/grok-bot-and-x（2026-08-29）：
> "Connect your X account in Grok Bot and we'll create a developer account for you if you don't have one. **Paid Grok Bot users get free X API credits**"
> "ask a Bot to search posts, read your timeline, check mentions"

### 🔴 但有个致命限制（决定它能不能进你的工作流）
多源一致（getaiperks 2026-09-16 / continuumcode 2026-09-08）：
> "Grok Bot... **has no public API** and no free tier. It is available only through SuperGrok and Cursor subscription plans."
> "**You cannot do it programmatically today.** Inside Grok Bot, the mechanism is routines: demonstrate a multi-step path once and the Bot saves it and re-runs it on a schedule or on demand."

**→ Grok Bot 无法被你的工作流以代码方式调用。** 它只能：
- 你手动跟它说话
- 或录一个 routine 让它定时跑

**这个是硬阻断。** 它是个给人用的产品，不是给程序调的组件。

### 顺带澄清：Grok Build ≠ Grok Bot
🟢 `docs.x.ai/build/overview`：
> "Grok Build is SpaceXSI's powerful, extensible coding agent. Install the CLI... run interactive or **headless** sessions, and connect via **ACP**"

**要编程调用，用 Grok Build（有 CLI + ACP）或直接用 xAI API，不是 Grok Bot。**

### 定价线索
🟡 2026-10-12 起有 X Subscription 打包：Grok + Grok Bot + Cursor + X Premium 一个订阅。

---

## 四、OpenClaw 这边到底能不能"按需调用不同 LLM"——实测结论：**已经原生支持，不用买任何东西**

### 🟢 实测证据

**1. 每个 Agent 可独立配模型**
```
~/.openclaw/openclaw.json → agents.list[]
  - main     | deepseek/deepseek-v4-flash
  - xiaofeng | deepseek/deepseek-v4-flash
  - balance  | deepseek/deepseek-v4-flash
  - self     | deepseek/deepseek-v4-flash
```

**2. 子任务可单独指定模型**（官方文档 `docs/tools/subagents.md`）
> "native sub-agents inherit the caller unless you set `agents.defaults.subagents.model` (or per-agent `agents.list[].subagents.model`)... **An explicit `sessions_spawn.model` still wins.**"

**3. 单次 spawn 可临时指定任意模型**
> "`--model` and `--thinking` override defaults for that specific run."
> 第 206 行："Override the sub-agent model. Invalid values are skipped..."

### 能力现状表

| 需求 | OpenClaw 现状 |
|---|---|
| 不同 Agent 用不同模型 | ✅ 已支持（per-agent `model`） |
| 同一 Agent 内按子任务换模型 | ✅ 已支持（`sessions_spawn.model`） |
| 一次运行临时换模型 | ✅ 已支持 |
| 多 provider 并存（DeepSeek / OpenRouter / Google / Anthropic…） | ✅ `models.providers` |
| **可视化拖拽编排** | ❌ 没有（要自己写代码/cron） |
| **工作流存成可复用文件、可版本管理** | ⚠️ 有（cron job + skill），但不是图形化 |
| **浏览器持久身份（自动登录第三方平台）** | ❌ **没有——这是真正的缺口** |

**关键结论：你想要的"按需调用不同 LLM"，OpenClaw 现在已经能做到，零成本。**
真正缺的只有一条：**浏览器持久身份**。

---

## 五、架构判断：外壳该不该自建

### 把问题正确拆开，是三层不是一层

```
┌─────────────────────────────────────┐
│  Layer 3  编排层（谁先谁后、条件分支）  │
│           → OpenClaw cron + subagents │
│           → 缺图形界面，但功能齐       │
├─────────────────────────────────────┤
│  Layer 2  模型层（这一步用哪个 LLM）    │
│           → ✅ 已支持，per-agent/spawn │
│           → 零成本，不用外购            │
├─────────────────────────────────────┤
│  Layer 1  身份层（用谁的身份行动）      │
│           → ❌ 真缺口                  │
│           → 且与 LLM 完全无关          │
└─────────────────────────────────────┘
```

**Daryl 想要的营销工作流，卡的是 Layer 1，不是 Layer 2。**

### Layer 1 的三条实现路径（各有代价）

| 路径 | 怎么做 | 优点 | 缺点 | 能编程调用 |
|---|---|---|---|---|
| **A. 官方 API** | X API / LinkedIn API / Meta Graph API + 自己的 token | 稳定、合规、可自动 | 贵（X API 分档收费）、部分平台不对个人开放、功能受限 | ✅ |
| **B. 浏览器自动化** | Playwright/CDP 维持登录态，像人一样操作 | 任何平台都能干、不依赖 API | **封号风险高**、要维护登录态、不稳定 | ✅ |
| **C. 用现成 agent（Grok Bot）** | 让 Grok Bot 帮你登录操作 | 别人搞定反封和登录 | **无 API，无法被工作流调用**、要买订阅、数据过第三方 | ❌ |

**核心矛盾：C 最省事，但最不可集成。A 最可集成，但最贵最受限。B 最灵活，但风险最高。**

### Muse 该不该考虑
**不该。** 理由：无公开 API（工作流无法调用）+ 隐私争议（TIME 报道它会 profile 联系人）+ 它是消费级入口产品，不是开发者组件。

### Lancer 的参考价值
它本身不是外壳，但它证明了一件事：**垂直场景的自动化 agent 有人愿意付钱**（$12/meeting vs $98/meeting 的对比是他们卖点）。
**这个商业逻辑可以借鉴，但产品本身不能拿来当基础设施。**

---

## 六、给你的建议（分三步，不要一次做完）

### 第一步：立刻能做的（0 成本，不用买任何东西）
**验证 OpenClaw 的模型路由能力是否够你用。**
我可以现在就能给你搭一个 demo：同一个营销任务，分别用 DeepSeek / Grok（走 xAI API）/ Gemini 各跑一遍，对比产出。**这能直接回答"不同 LLM 侧重不同"对你实际有没有影响。**
在没跑这个对比之前，讨论买什么工具都是空谈。

### 第二步：先解决身份层，但要选对路径
营销工作流的身份需求，先明确**具体是哪个平台、要做什么动作**：
- 只是**读**（看趋势、看竞品、抓内容）→ 走 API 或抓取，不需要"身份"
- 要**发**（发帖、回复、私信）→ 必须有身份，且要考虑封号成本
- 要**维护人设长期互动**→ 需要持久会话，这条路最重

**不同答案对应完全不同的方案。这个必须先定。**

### 第三步：外壳要不要自建
**我的判断：不要为了"可视化"去自建外壳。**
理由：
- 可视化编排的价值是**让人能改流程**。如果你改流程靠跟我说，那可视化没意义
- 真正的复用价值在**工作流文件**，这个 cron + skill 已经能做
- 自建外壳的成本高、维护重，且解决不了 Layer 1

**但如果你的场景是"要卖给别人用"，那外壳就是产品本体，逻辑完全不同。**
这一点要你定：**是自用工具，还是要做成产品？**

---

## 七、待 Daryl 确认的三件事

1. **"Lancer AI" 是不是记错名字了？** 我查到两个 Lancer 都不是工作流外壳。你要找的是不是 Langflow / n8n / Dify 这类？
2. **营销工作流的"身份"具体要做什么？** 平台是哪个、要读还是要发、要不要长期人设？
3. **这外壳是自用还是产品？** 决定该不该投入做可视化界面。

---

## 八、信源

- 🟢 https://lancer.app/ （Upwork AI Agent 官网）
- 🟢 https://www.lancer.work/ （另一个同名产品）
- 🟢 https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/ （Meta Muse 官方）
- 🟡 https://time.com/article/2026/10/06/meta-muse-ai-agent-privacy/ （TIME 隐私调查）
- 🟢 https://docs.x.ai/grok-bot/overview （Grok Bot 官方文档）
- 🟢 https://x.ai/news/grok-bot-and-x （Grok Bot × X 集成官方公告）
- 🟢 https://docs.x.ai/build/overview （Grok Build，有 CLI/headless/ACP）
- 🟡 https://www.getaiperks.com/en/ai/grok-bot-api （Grok Bot 无公开 API）
- 🟡 https://continuumcode.ai/guides/grok-bot-vs-grok-build/ （"cannot do it programmatically today"）
- 🟢 `~/.openclaw/openclaw.json` + `docs/tools/subagents.md` （OpenClaw 模型路由能力，本机实测）
