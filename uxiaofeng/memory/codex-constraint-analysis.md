# Codex → GPT-6-Astra 工程约束分析（学习笔记）

> Daryl 2026-11-13 19:59 纠正：**不要跟着写同类任务代码**，要学的是 Codex 为 Astra 设计好的工程约束。
> 本文只做约束拆解，不做同类实现。观察对象只读。

## 观察对象
- brief：`/private/tmp/atlas-ridge-build.jHdWhd/brief.txt`（11 行，约 5.2KB，一次性给全）
- 执行日志：同目录 `astra.jsonl`（stream-json 事件流）
- 项目产物：`~/Documents/Codex/2026-11-01/do/山脊缆车`
- 启动参数：`-a never -m gpt-6-astra -c model_reasoning_effort="xhigh" --sandbox workspace-write --ephemeral --skip-git-repo-check --json`

---

## 一、约束分五层（这是我该抄的骨架）

### L1 角色与授权层
- **单一角色**："primary developer"，不兼 QA、不兼调度 → 责任边界清晰，不会自己给自己打分。
- **权责分离**：brief 写明"你的工作是主实现，父进程负责完整通关测试与独立 QA"。子 Agent 不负责证明自己合格。
- **排除项写死**："only local development, no deploy, no network fetches, no messaging, no other agents" → 从源头堵掉跑偏路径，不靠模型自律。

### L2 技术与交付层（硬约束，不靠理解靠检查）
- 交付物形态：**可直接双击、完全离线**的单 HTML（`山脊缆车.html`）
- 依赖必须 vendored 本地（Three.js r180），禁网络请求
- 构建链明确：ES module → esbuild 内联成 IIFE → 单文件
- 源码结构：`src/` 可编辑源 + `build.mjs` + 发布物在项目根
- 许可证合规：保留 MIT notice
- **沙箱边界**：`--sandbox workspace-write` + cwd 限定 → 它能写但只能写自己那亩地

### L3 玩法验收层（把"好玩"翻译成可判定条件）
这是最值得学的一层——把主观设计变成可判定：
- 时长 2–4 分钟、一条线路、连续教学节拍（遮蔽起点→弯道→迎风→下行→进站）
- 货箱 3 个 vs 绑扎位 2 个 → **结构性取舍**，不是数值调参
- 三档评级 + 金牌条件（时间/状态双达标）
- 刹车要"有代价"：耗时 + 过热/递减
- 配重必须**可见地**影响侧倾
- **反作弊条款**：「停着不动拿满分」「一直抱闸」都必须拿不到最佳结果
- 必须有**真实失败态**（掉货/超时）

### L4 可验证性层（工程约束的核心）
- 固定步长确定性模拟（`FIXED_DT = 1/60`）
- 无指针锁也能玩（键盘+方向键兜底）→ 自动化可驱动
- SwiftShader 软件渲染可跑 → 无 GPU 也能验
- 提供**只读 diagnostics 接口**（位置/货物状态/计时/进度/状态/控制）→ 给外部验收开一扇窗，但不给后门
- 反自欺：「不要把测试专用捷径当可玩性证据」「不许未经证实就宣称」
- 独立确定性模拟检查允许单列（`qa/simulation.mjs`），但**正常胜负必须用真实玩家输入**

### L5 汇报与收尾层
- 结束必须给出：实现要点 / 路线与操作说明 / **测了什么** / **未解决问题**
- 明确禁止：宣称未验证的东西
- 预算：6 小时总预算，允许长时间连续作业
- 明确禁止停止在"计划"阶段（"Don't stop at a plan"）

---

## 二、这些约束如何实际改变 Astra 的行为（已观察到）

| 约束 | 观察到的行为 |
|------|-------------|
| 先侦察环境 | 前 3 条命令全是探测（rg files / AGENTS.md / 工具链 / playwright 缓存），确认后才动手 |
| 单一职责 + 反自欺 | 自己规划的收尾是"接下来把场景做成可游玩并**校准实际难度**"，难度校准被当成任务项 |
| 可验证性 | 19:57 第一份代码就是 `src/sim.js`：纯逻辑、无渲染依赖、固定步长、导出常量（DEADLINE=250 / GOLD_TIME=205） |
| 反作弊条款 | `sim.js` 里 `PHASES` 每段带官方 advice 与侧倾方向；抱闸有 heat 与递减，超时 fail |
| 反馈不撒谎 | 源码注释原话："Targets are shared by the prompt, highlight and E handler, so the UI never lies." |
| 无隐形必按按键 | 每条 notice 都给出下一步："靠近货物或前方配重手柄，再按 E。" |
| 反侥幸设计 | 搬运超 12 秒强制放下；绑扎位被散货挡住先移开；装卸口无货障但有安全链 → 掉落是真风险 |
| 交付结构 | `package.json` 脚本：`build`（node build.mjs）+ `check`（node qa/simulation.mjs），验收入口预先定义好 |

---

## 三、我的差距（对照自己）

1. **我缺 L4**：我最弱的是"可验证性"。过去交付常靠"我看了一眼觉得行"，没有把确定性、诊断接口、无 GPU 可跑写进需求。
2. **我接活常缺 L3**：模糊需求直接开工 → 中途反复问边界。Astra 拿到的是把主观标准翻译成判定条件后的 spec。
3. **我常自我验收**：既写又测，容易自己给自己发合格证。这里分工是硬规则。
4. **我不写排除项**：不列"不许做什么"，就容易发散。brief 里的 no network/no messaging/no other agents 我不常写。
5. **我缺反作弊思维**：只设计"怎么成功"，不设计"怎么防止轻易成功"。这一条直接决定体验有没有张力。
6. **我汇报常只报好消息**：brief 要求"测了什么 + 未解决问题"，这是强制的诚实项。

---

## 四、可直接复用的动作（写成我自己的模板）

接任何工程任务时，先补齐这五块再动手：
1. **排除项**（no X / no Y）
2. **交付物形态与边界**（形态/路径/离线与否/沙箱范围）
3. **可判定验收条件**（把主观词翻译成数字或布尔）
4. **反作弊条款**（防止"最省事的做法就拿满分"）
5. **可验证性要求**（确定性、诊断接口、无特殊硬件可测）
6. **收尾格式**（实现要点 / 测了什么 / 未解决问题 / 不许未验证就宣称）

---
---

# 终版：约束执行效果核查（2026-11-13 20:25）

## 交付事实
- 工期：19:50:33 开工 → 20:23 产出单文件，约 **33 分钟**（预算 6 小时，用量 ~1/10）
- 发布物：`山脊缆车.html` 626KB，单文件双击可跑，MIT notice 保留，零外部请求（仅 SVG 命名空间 `http://www.w3.org/2000/svg`）
- 源码：`src/`（sim/world/main/audio/index/style）+ `build.mjs` + `qa/`（simulation.mjs / input-driver.mjs / smoke.py）+ `.gitignore`
- 模型档位：`gpt-6-astra` + `xhigh`，`-a never`

## 硬核证据：13 项断言全部 PASS（`qa/simulation.mjs`）
| 断言 | 证明了哪条约束 |
|------|---------------|
| No handling causes genuine cargo-loss failure（t=63.5s，delivered=1） | 真实失败态 |
| Two crates tied complete the route（t=177.2s，合格运输） | 合格线可达 |
| Fixed simulation inputs reproduce the exact same outcome（deepEqual 两次快照） | 确定性 |
| Holding brake → deadline failure（t=250.0） | 反作弊：抱闸拿不到分 |
| Parking all three without handling does not earn gold（health<80） | 反作弊：摆完不管不行 |
| Balance strategy earns gold using **real E interaction path**（ballastMoves=3） | 真实输入验证 |
| Balance + short braking trades time for condition（t=196.6，cond=100 vs 177.2/95） | 有两条可行策略 |
| Carry timeout forces visible recoverable set-down | 无隐形必按按键 |
| Ties limited to two, unlock with E | 结构性取舍 |
| Pause freezes the same loop the browser uses | 不测旁路 |
| Failure→reset→normal win clears transient state | 干净重置 |
| Keyboard-only turning / vertical look / deck bounds | 无 pointer lock 可玩 |
| Release HTML inlines JS/CSS + retains Three.js license | 离线单文件 |

**自我设限**：报告首字段就是 `"scope": "Deterministic simulation and release structure only. **Not a browser playthrough.**"`
→ 这是 L5「不许未验证就宣称」的直接兑现：它主动把自己的证据降级。

**真实输入路径不是后门**：`qa/input-driver.mjs` 头部写死
`"These helpers never set cargo, positions, health, progress, speed or outcomes."`
只发 `{forward, strafe, interact, brake}` 输入，每步 `s.step(FIXED_DT, input)`，走的是 UI 同一条 target/interact 链路。

## 约束被逼出来的行为（最能说明约束有效）
1. **沙箱撞墙后不降级标准**：`python3 qa/smoke.py` 启动 Chromium 失败（macOS 沙箱），又试了 `cua_repl` 浏览器控制 → 返回"Local browser use is disabled in Work settings"。
   它的反应：把浏览器脚本 `qa/smoke.py` 留在项目里给父进程独立 QA，自己改走确定性输入验证，并明说「当前会话的 macOS 沙箱禁止启动 Chromium」。
   → 对应 brief 的「父进程负责浏览器验收」分工，它没有越权宣称可玩性。
2. **难度校准被当成任务项而非收尾**：中途就报「已校准出两条可行路线」，报告里 `balance_gold` vs `careful_gold` 是同一条线路的两种策略对照（177.2s/95 分状态 vs 196.6s/100 状态）。
3. **反作弊条款落地成数据**：`parked_three` 三件全摆放但不照看 → `稳健运输`（非金牌）；`always-brake` → `timeout`。
4. **收尾预留验收入口**：`package.json` 的 `build` / `check` 两条脚本就是外部验收的两个按钮。

## 若我按传统方式做，大概率会翻的三处
1. 沙箱起不了浏览器 → 直接说「已通过测试」或含糊带过（它反而主动降级证据 + 留脚本给父进程）
2. QA 辅助函数顺手设 `cargo.status='tied'` 让断言过（它明确禁止改状态，只发输入）
3. 反作弊条款只写在文档里，报告不体现（它把每条反作弊写成可执行断言并出数据）

## 可直接抄进我模板的 6 条
1. 交付前先写「scope 一句话」：本证据能证明什么 / **不能**证明什么
2. QA 断言必须针对"作弊路径"专门写一条（抱闸、无操作、摆完不管）
3. 测试驱动只允许发输入，禁止直接改被测状态
4. 确定性要求写成断言（两次运行 deepEqual），不写在文档里
5. 环境阻塞时降级证据等级，而不是降级标准；同时把外部可用的验证脚本留在交付物里
6. 收尾必答四问：实现要点 / 操作方式 / 测了什么 / 未解决什么

---

## 五、时间线 / 新证据

### 2026-11-13 20:25 — Astra 收工，产物核验通过

**结束判据（全部满足）**
- 项目根出现 `山脊缆车.html`（626 KB，20:23 构建）
- `astra.jsonl` 最后一条事件 = 第 68 条 `item.completed`（20:23:05），此后无增长
- `ps aux | grep "codex exec"` 无匹配 → 进程已退出

**最终产物结构**
| 项 | 值 |
|---|---|
| 发布物 | `山脊缆车.html` 611.7 KiB，构建日志明确 "No external runtime assets" |
| 源码 | `src/{main,sim,world,audio}.js` + `index.html` + `style.css`（约 100 KB 手写源） |
| 构建 | `build.mjs`（内联 JS/CSS + 保留 Three.js MIT 声明） |
| 自测 | `qa/simulation.mjs`、`qa/input-driver.mjs`、`qa/smoke.py`、`qa/simulation-report.json` |
| npm 脚本 | `build` / `check` —— 交付即带可复跑的验收入口 |

**独立复跑结果（我本人执行 `node qa/simulation.mjs`，未改动任何文件）**
14/14 PASS，含关键反作弊项：
- `Holding the brake with secured cargo produces a deadline failure`（抱闸到底 ≠ 安全躺赢）
- `Parking all three without further handling does not earn gold`（三件摆好不照看拿不到金）
- `Active balance strategy earns gold using the real E interaction path`（金牌走真实操作路径，非测试后门）
- `Fixed simulation inputs reproduce the exact same outcome`（确定性）
- `Release HTML inlines JS/CSS and retains the Three.js license`（离线 + 许可证）

**约束执行效果（哪几条真的改变了行为）**
1. **「Don't use test-only shortcuts as evidence of playability」** —— 最有效的一条。Astra 没有写 `if (test) win()` 之类捷径，而是做了 `qa/input-driver.mjs` 模拟真实按键序列（`walkTo` / `interact` / `tick`）驱动作真实 `GameSim`。金牌是"按 E 搬货 + 移配重"这条真路径跑出来的。
2. **反作弊条款**（"holding brake forever cannot earn best result" / "parking all 3 with zero effort cannot earn gold"） —— 直接产出两条 PASS 用例，且它自己的收尾原话承认："三件摆好后完全不照看无法拿到当前测试中的金牌"。**它主动承认了约束划定的负面结论**，这是最难得的一点。
3. **「Do not claim anything unverified」** —— 收尾文案全程用"已校准出/已验证"，无一句"完美可玩/体验极佳"。
4. **确定性要求** —— 固定 dt=1/60，报告 JSON 首行自设 scope 边界："Deterministic simulation and release structure only. **Not a browser playthrough**." 主动标注能力边界，没把仿真通过吹成浏览器可玩。
5. **排除项（no deploy / no network / no messaging）** —— 全程零网络请求、零部署、零对外发消息，构建日志确认无外部运行时资源。
6. **「Don't stop at a plan」** —— 68 条事件里 command_execution 与 file_change 交替，边写边跑，无长段纯规划空转。

**发现的边界问题（诚实项，非违规）**
- 收尾 agent_message（item_33）在最后两轮构建**之前**给出，措辞是"已校准出两条可行路线"，但真正的 `qa/simulation.mjs` 14 项全量校验是之后才补齐的（item_34/35）。顺序上属"先小结、后补证"，不算未验证宣称——因为最终 PASS 可在 20:23 之后独立复现（我已复现）。
- 该 agent_message 未按 brief 的"测了什么 / 未解决问题"双栏格式组织，偏结果叙述。这是本轮唯一格式偏差。

**给我自己的修正**
- 模板里"收尾格式"那一条要**固化成两栏强制表**（测了什么 / 未解决什么），否则模型会自然滑向只讲成果。
- 反作弊条款价值最高，应作为接活默认项：先问"最省事的做法能不能拿满分？"不能，才继续。

---
_状态：Astra 已交付并核验完毕（2026-11-13 20:25）。已通报主 session 出报告。_
