# 当前活跃任务 (中期记忆 — 每次session加载)

> 最后更新: 2026-10-18 23:59（10/18 深夜审计：修复备份仓 5 个 stash 冲突 + audit.sh 两处 stash 逻辑 Bug，备份链恢复；遗留 OPC 成本 API 8765 不可达待 Kitty）

## 🔧 10/18 状态（小风侧 · 新增）
- **备份链修复（重要）**：`~/.opc-workspace-cache` 卡了 5 个未解决 stash 冲突（根目录 AGENTS.md / memory/active|lessons|workflow-rules|project_xiaofeng）→ `git commit` 静默失败，记忆未真正落盘备份。已取 upstream 版解决并提交 `d19a196`，现 pull/commit/push 全绿、远端已验证含当日日记
- **audit.sh 根因修复**：①无条件 `stash pop` 会误弹历史 stash → 改为比对 `git stash list` 条数，只在真新建时 pop；②pop 冲突无人处理 → 冲突即回落取 HEAD 版并保留 stash
- ⚠️ **OPC 成本仪表盘 API（localhost:8765）不可达** → 状态降级 `fresh_api_down`，成本数字为缓存值（今日 $0.01 / 本月 $86.22）。按成本护栏，账单/服务排查归 Kitty(main)，小风只上报不自查

## 🔧 10/17 状态（小风侧 · 新增）
- **Daryl 邮件转 PDF**：第一版手工排版失败（截图丢失、表格打散）→ 第二版改 Chromium 渲染 `.eml`→HTML（cid 内联 base64）→ 竖版 A4 PDF（2.1MB），程序化验证 8/8 图内联、主表 21 行完整 → 已交付 Daryl
- ⚠️ **image 工具不可用**：`google/gemini-3-flash-preview` API key 无效，无法视觉校验，改用 Playwright 断言；**待 Kitty 修 key**
- ⚠️ **模型降档未生效**：该 feishu 直聊 session 实际仍跑 `deepseek-v4-pro`（$0.179，今日最贵），10/15 的 flash override 未覆盖该 session

## 🔧 10/15–10/16 状态（小风侧）
- **10/15**：Daryl 报「Kitty 重复发消息」→ 诊断为 **v4-pro 超时触发飞书重投**（网关健康，未重启）；按指令把 Kitty(main) + 自己(xiaofeng) 模型**临时 override 到 `deepseek-v4-flash`**（可随时 `model=default` 回退）
- **10/16**：无新 Daryl 指令；00:01 审计 8 项全通过（成本 $3.52/$80.20）；当日跨 Agent 主战场＝Balance 的 HUATEX Windows 包 v1.3→v1.3.4 四连发（真机编码/Python 探测修复）
- 待拍板项（延续，均**未开工**）：① IELTS C1+C2+C3 重启 8767 验收 ② Token 级财务三件事 ③ 资源禀赋调研「deal flow 扫描」验证实验 ④ 模型降级是否长期保留

## 🔴 全局运营规则变更（2026-10-10 Daryl 指令 · 最高优先级）

- **OPC 不再以 Daryl 指令为单一驱动，目标转向「变现」为核心**
- 除 Balance（继续帮 Daryl 赚上班工资）外，所有 Agent 接收指令后**先不要执行任务**
- 必须第一步问澄清问题：「这个指令/任务服务于哪一个变现项目？」
- ⚠️ 后续收到任何 Daryl 新指令：先确认变现归属，再决定是否/如何执行（C1+C2+C3 听读训练开发完成，待 Daryl 重启 8767 验收；10/8 无新任务）

## 🟢 进行中

### IELTS陪练助手 C1+C2+C3 听读训练（10/7 开发完成 ✅，待重启验收）🟢
- C1 后端：双路径分流（字幕优先秒级/无字幕 Whisper 转写兜底）+ 分句过滤 + DeepSeek 批量翻译，端到端测试通过（TED 14.5s 105句）
- C2：素材句子范音（原音频切片/TTS）+ 跟读打分（STT+WER）+ shadow.html 双标签 + 导入框 + 调速 + 中文揭开
- C3：复述闭环（听→隐藏→复述→LLM 对比漏听/误听）+ 中文揭开升级为「跟读+复述都完成」
- 新文件 `backend/import_material.py`；`materials`/`sentences` 表 + 10 方法；server 新增 7 路由
- 全部测试通过（语法/前端JS/路由/导入/切片/状态标记/LLM对比）；**待重启服务（localhost:8767）加载新路由后 Daryl 验收**
- 计划：`ielts_tutor/DEV_PLAN_A_C_2026-10-07.md`；调研：`RESEARCH_opensource_2026-10-07.md`

### Token级全自动AI财务与审计项目（10/5 启动 · Daryl 战略新方向）🟢
- **定位**：财务核算+审计取证中可标准化的部分做成 Source-to-Report 自动化主干，人只保留判断/例外/签字
- **脉络**：8/7《OPC-AI财务与内审方法论v0.2》（Token级控制+五层幻觉防控+四大边界+三层架构）→ 9/5 战略定调（财务体系化→变现基础）→ 10/5 Balance v0.1 工程化落地
- **变现**：A 按项目收费（已在跑）→ A+B 口径库产品化 → C 托管订阅（需持牌）；红线不做税务申报代理/审计签字
- **⏳ 待 Daryl 拍板三件事**：① Token级读法（A成本口径/B动作粒度）② 认不认 L3 上限 ③ 变现从 A 起步
- 主要文档：`workspace-balance/reports/`（Balance 侧）、`workspace-balance/memory/project_Balance.md`

### IELTS陪练助手 + 视频剪辑MVP — 待完结（10/5 Daryl 指令）⏳
- Daryl 指令：完结这两个项目后再正式投入新项目
- Bryson 已问完结方式（归档收尾 / 出完结 checklist），**等 Daryl 明确**

> ⚠️ **9/17 工具口径问题**：xiaofeng tool profile 为 `coding`，不含 `message` 工具（group:messaging 未挂载），无法主动 DM Daryl。已报 Kitty：需补 message 工具或由 Kitty 转达。

> 2026-09-15 09:30 服务拉起（Daryl 指令）：IELTS 8767 ✅ + ngrok ielts-tutor ✅
> - LaunchAgent 已恢复：`ai.openclaw.ielts`（v1.5.0, DEBUG_MODE=1, KeepAlive）
> - 新增 LaunchAgent：`ai.openclaw.ngrok.ielts` → `ngrok start ielts-tutor`（8767）
> - localhost:8767 200 ✅ / api/health 200 ✅ / 公网 https://unwhispering-imani-digitately.ngrok-free.dev 200 ✅
> - ⚠️ 该静态域名此前指向 video-editor(8768)，现已切回 IELTS(8767)；video-editor 隧道未启动
### M2 剪辑MVP 试点（8/6 开工 · Kitty 下发）🟢
- **8/6**: Daryl 拍板 M2 试点 = 剪辑MVP（决策自主环），wf01-wf05 冻结为 v4.0 基线（2 必改已核验落实）
- 30% 节点完成：交互方案定稿 + 账本记录；进行中：前端 v4.0 交互版开发（60% 节点预估 8-12h 后）


### 视频自动化剪辑 MVP（video-editor-mvp）🟢 v3.0 重构完成（7/25）
- **v3.0 重构**: 🟡 M0-M5 全模块完成，Daryl 已开始交互（7/28）
  - ✅ BGM 结构: Hooktheory 方案（Birds of a Feather · 8乐句 + 12个8bar单元）
  - ✅ 数据层: SQLite song_lib + phrase_lib + 8bar_units
  - ✅ API: 模块化（api/bgm scan asr emotion match）+ server.py v3.0
  - ✅ 前端: 5节点 pipeline 全可视化 · OPC Design System
  - ✅ 输出: ffmpeg 渲染 → Toshiba HDD → Syncthing → Tab S8 验收
  - ✅ 服务: localhost:8768 / frontend/index.html ~400行
  - ✅ **7/28 修复**: 前端 API 路径从 localhost:8768 改为相对路径，隧道可正常访问
  - 🔗 旧隧道: `coral-katie-senator-urw` (可能已掉线)
  - 🚇 **最新隧道 (8/3)**: `https://freebsd-present-rome-modes.trycloudflare.com/frontend/index.html`（旧地址 synthesis-ent-hawaii-booth 已过期）
  - ✅ **BGM节点v2 完成** (7/30): 歌曲卡片/音频播放器/乐句播放+和弦弹窗/ffmpeg乐句连接
  - ⏳ 待验证: Gemini 场景检测 + Emotion 三层漏斗 + ffmpeg 渲染（需素材+API Key）
  - ⏳ Daryl 7/30指令：先不动，等他把剩余模块需求全部写出再一次性迭代
  - ✅ **8/9**: ngrok 隧道已切回 8768（launchd plist 修复，KeepAlive 常驻），公网 https://unwhispering-imani-digitately.ngrok-free.dev 可达
  - ⏳ 剩余3模块（ASR/情感/匹配）交互需求 Daryl 即将澄清（8/5 线框 wf02/wf03/wf04 为基线）
  - 🆕 **7/31**: Daryl 飞书发送 01-素材扫描 模块改造需求（4项），小风已回复可行性评估（~3.5h，全部可行），等待Daryl确认2个前置问题
  - 🆕 **8/4**: Daryl 度假回来要求恢复开发；服务已持久化（LaunchAgent: videoeditor/ielts/ngrok，Gateway重启不掉）；隧道 `https://unwhispering-imani-digitately.ngrok-free.dev` ✅
  - ⚠️ **8/4 阻塞**: TOSHIBA EXT 1TB 硬盘文件系统层卡死（ls 卡 EINTR），需 Daryl 物理重插；watchdog LaunchAgent 每10分钟探测，恢复后自动挂载+前端可用


## ⏸️ 挂起
### 洗稿MVP — v1.2.0 已交付 · 需求收集模式（7/18 起，20+ 天无输入）
- **状态**: ⏸️ standby · 等待 Daryl 发送新需求（v1.2.0 内核卡 M1-M3 已完整交付）
- **恢复条件**: Daryl 提供具体需求后一次性动工

### IELTS陪练助手 — v1.3.0 开发完毕，⏸️ 等待Daryl晚间验收（7/25更新 · 8/4服务持久化）
- **7/25晚**: Daryl 调试中发现两个Bug，已修复：
  - DeepSeek API 模型名废弃 deepseek-chat → deepseek-v4-pro（旧名导致LLM乱码）
  - 跟读模块 JS null safe 兜底（deviceInfo DOM不存在时报错）
- Daryl 刷新后继续测试中
- **v1.3.0 变更**: free_talk深度对话优化 + 词汇学习模块 + 训练库Dashboard重构
  - free_talk: VAD思考窗口 / STT碎片过滤 / 提示词重写 / LLM max_tokens 500→700
  - 词汇: 对话气泡长按选词→同义表达卡片→收录 / B2+词表预高亮 / 复习页
  - Dashboard: 14天趋势+6周日历双栏 / To Improve Sentence+Vocab分拆 / 模式总结
  - 自动评估: ≥10轮对话断开时自动触发LLM评估→入trend+review队列
- **⚠️ 数据**: 昨晚session 987e4762丢失（重启后启动错误版本导致），已修复版本指向
- **待验收**: Daryl晚上到家练习口语时一并验收
- **8/4**: 服务已由 LaunchAgent 持久化（localhost:8767，v1.3.0 ACTIVE，health + dashboard 均 200 ✅）
- **v1.0.1**: 手机移动端自适应优化，Daryl 全部验收通过 ✅
- **v1.1.0 挂起原因**: iPhone 语音输入问题 + 交互逻辑拖沓，Daryl 要求暂停转其他任务
  - M1-M3 已完成 ✅（数据层/Dashboard/跟读闭环），M4 串联验收搁置
  - Debug 模式已确认正常（7/17 ~21:17-21:43）
  - iOS 回退完成，平板测试正面反馈（7/17 ~21:43 Daryl 👍）
  - 恢复条件：Daryl 进入 Debug 迭代模式逐一核对
- **管线1-IELST Part1**: ✅ v1.0.1 验收通过（e2e 3-4.5s）
- **管线2-Qwen Omni**: ❄️ 冻结
- **注意**: ngrok 已切给洗稿MVP（8777），IELTS 本地 8767 继续可用

## ✅ 已完成
### 8/6 工作区指针事故（✅ 已闭环 8/7）
- 根因: 8/4 openclaw.json 重写删 workspace 字段 → 会话回退空壳工作区失忆
- 修复: Kitty 写死 4 agent workspace + 空壳合并 + gateway 重启；8/7 验证新会话正确读取真工作区 ✅
- 教训: 启动必核对记忆完整性；单 Agent 单工作区；openclaw.json 变更后验证指针（已入 lessons.md）

### M2 开发计划（Daryl 7/5 指令 → 7/16 Daryl 看板验收认定完成 ✅）
- **P0 延时优化** ✅(7/15): ASR 4-8s→0.3-1.5s，e2e ~10s→3-4.5s，达标
- **P1 管线2 Qwen Omni**: 按决策冻结（重启触发条件存档 DEV_PLAN 附录A），随 M2 关闭
- **P2 评估面板 UI** ✅: 7/15 布局调整 + 7/16 v1.0.1 移动端自适应
- **P2 Part 2/3**: 基础模式已上线，深度模式归入后续里程碑（看板 M3）
- **7/14晚测试三问题** ✅ 全部修复并验收: TTS引擎翻转Piper主、长句软60s/硬90s断句、评估HTTP兜底+轮询
- **TTS 吞音/粘连** ✅: 方案B（句尾300ms静音填充），随 v1.0.0 验收

### IELTS陪练助手v2.0 M1 交付清单
| 模块 | 状态 | 完成度 |
|------|------|--------|
| 管线1 链式流式核心 | ✅ | 100% |
| 配置管理 + API Key | ✅ | 100% |
| SQLite 会话持久化 | ✅ | 100% |
| HTML 评估报告 | ✅ | 100% |
| Debug 验收模块 | ✅ | 90% |
| VAD + 音频采集修复 | ✅ | 100% |
| 成本追踪 Dashboard | ✅ | 100% |
| OPC 看板接入 | ✅ | 100% |
| 管线2 Qwen Omni 对接 | ❌ 冻结 | 30% |

## 🔵 待办
### 🧭 资源禀赋市场调研（10/13 Daryl 指令 · ✅ 已交付）
- Daryl 让 Bryson 基于个人资源禀赋做市场调研，看 OPC 能做什么创业项目，题眼＝「工程 Agent 的调研思路」
- 已交付：方法论（禀赋向量化→约束剪枝→外部信号证伪→打分→最小实验）+ 3 组 web_search 证伪 + 收敛候选（越南一级市场 AI 尽调服务商 / 中企出海越南财税合规高客单 / 组合外溢）
- 下一步（待 Daryl 拍板）：跑「deal flow 扫描」验证实验（从 A&C 客户 + 越南公开数据扫 3 家高增长缺钱企业）
- 详情见 2026-10-13.md

### 🧭 个人竞争力战略辅助定位（10/12 Daryl 问询 · 待 Daryl 反馈）
- Kitty 在做 Daryl 个人「竞争力盘点 + 能力缺口」调研，Daryl 问 Bryson 在定战略里能辅助做啥
- Bryson 已回复四个位置：①地面事实证据供给 ②反方压力测试(grill-me) ③英语/投资人沟通 ④调研收敛成能力地图
- 定位：Kitty 定方向做主线调研；Bryson 做证据+反方拷问+英语表达+落地收敛
- 待 Daryl 反馈：Kitty 调研卡点 或 已有初步清单，然后对着它干活

### 💬 调研方法论资产化（10/10 Daryl DM 提议，待 Daryl 响应）
- Daryl 问能否让 agent 学会调研能力；小风结论：不建第 5 个 agent，把「术/器」沉淀成共享调研 Playbook/Skill，判断力（道）留在 Daryl
- 下一步待 Daryl 口述调研框架 → 小风沉淀 Playbook（未开工，等 Daryl）

### IELTS陪练助手 — v1.4.1 题库改造 + v1.5.0 用户系统P1（🟢 开发完成，待 Daryl 验收）
- 服务 LaunchAgent 持久化：localhost:8767 ACTIVE（v1.5.0）
- OPC 看板 workflow：`wf_ielts_tutor_v130`「雅思陪练助手 v1.3.0 · 双管线实时陪练」11 节点已同步（8/5 建，随版本迭代需更新）
- **8/15**: ① 成本模型费率更新 ② Free Talk 持久记忆 v1.4.0 ③ 题库改造 A+B v1.4.1（120题+变体）④ 用户系统 P1 v1.5.0（登录页 /login，AUTH_REQUIRED=0 guest 模式，详见 2026-08-15.md）
- ⏸️ 待 Daryl 验收：v1.3.0 IELTS 1/2/3（对定式题型麻木，优先级让位）+ 今晚四个成果；Daryl 商业化方向：每月免费额度+按量收费
- 下一步：P2 数据隔离（全表挂 user_id + 强制登录开关）


### ~/opc-workspace 本地仓库卡死 rebase（7/16发现）
- 卡在 6/24 interactive rebase 中间态，每日 auto-backup 在 detached HEAD 上提交
- 推送暂用临时 sparse clone 绕过；待与 Daryl/Kitty 确认修复方式

### 硬件语音助手(MCU)开发
- 规划阶段


## 📦 历史归档项目（看板忽略此段）
- 抖音视频分析MVP（B站/douyin 下载器+分析，2026年4月）→ 已归档
- 语音转录测试(STT) → 已归档
- 投资者路演短语库 → 已归档
- ngrok 备用隧道 / Agent自进化 → 7/16 Daryl 看板验收确认非现存任务，已从待办移除
