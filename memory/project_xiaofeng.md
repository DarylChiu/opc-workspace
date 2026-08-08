# Project Dashboard — xiaofeng（吹点小风）

> 最后编译: 2026-08-08 19:02 +07:00
> 负责人: Bryson | Agent ID: xiaofeng
> 下轮更新: 2026-08-09 07:00

---

## 🟢 进行中项目

---

### 视频自动化剪辑 MVP（video-editor-mvp）★ACTIVE

| 字段 | 值 |
|------|-----|
| 项目ID | video-editor-mvp |
| 状态 | 🟢 active · v4.0 交互版开发中（8/6 M2 决策自主环试点开工，wf01-wf05 冻结为 v4.0 基线）；8/4 服务 LaunchAgent 持久化+隧道恢复 unwhispering-imani-digitately.ngrok-free.dev；8/5 修复 3 个 BUG（launchd PATH/前端 hardcode）+ 自诊断 + 线框先行包 + 机制分层落定；8/6 工作区指针事故闭环（跨工作区同步完成，唯一有效工作区 xiaofeng_workspace）；8/7 OPC 看板 v1.6 同步（项目区保留 ★ACTIVE）+ M2 进度核验 60% |
| 优先级 | P0 |
| 当前阶段 | v4.0 交互版开发（M2 试点 · 前端开发 60% 节点进行中，预估 8-12h 完成） |
| 阶段进度 | 核心链路 100%（7/25 ✅）；wf01-wf05 已冻结为 v4.0 基线（8/6）；前端 v4.0 交互版 60% 节点（8/7 核验，8/6-8/8 无新增开发投入，进度持平） |
| 总进度 | 92% |
| 启动日期 | 2026-07-19 |
| 预计交付 | 2026-08（视Daryl需求节奏） |
| 上周进展 | 8/4 服务持久化（LaunchAgent: videoeditor/ielts/ngrok，Gateway 重启不掉）+ 隧道恢复 unwhispering-imani-digitately ✅；TOSHIBA 硬盘卡死→Daryl 18:10 重插，watchdog 误报 BUG 修复（launchd PATH 缺 timeout，70+ 次误报）；8/5 修复 3 BUG（素材时长 0 / ASR 仅前 3 个 / 看护误报，根因=launchd 极简 PATH + 前端 hardcode）→ 素材扫描解阻（21 组素材可用）；产出自诊断 SELF_DIAGNOSIS_20260805 + 线框先行包 wf01-wf05（含素材可读化/重命名需求）；Daryl 纠正归因→「用户思维」机制沉淀；三个颠覆性方案→Kitty 评估→机制分层落定；8/5 Loop Engineering 移交 Kitty（更名「决策自主环」，M2 试点=剪辑MVP）；8/6 M2 试点开工：wf01-wf05 冻结 v4.0 基线，前端 v4.0 交互版开发中（60% 节点，预估 8-12h）；8/7 OPC 看板 v1.6 初始化（项目清理：洗稿/Loop/视频分析移入归档，剪辑MVP 保留 ★ACTIVE）+ M2 进度核验 60% |
| 本周计划 | 完成前端 v4.0 交互版（8/7-8/8 无新增投入，仍待推进）；ASR/情感/匹配模块按线框先行流程推进；隧道 maintenance 按需刷新（ngrok 8/7 已切给 IELTS 8767，视频编辑器公网暂不可达，本地 8768 不受影响） |
| 阻塞项 | ① ~~TOSHIBA 硬盘卡死~~ ✅ 已恢复（8/5 修复看护+时长 BUG，21 组素材可扫） ② ~~素材扫描 2 前置问题~~ ✅ Daryl 已确认（8/5 核实，wf01 带默认方案冻结） ③ DJI Mic 3 音频同步仅框架+模拟（待设备联调） ④ BGM 替换等待 Daryl 提供《I NEED YOU》文件 |

#### 里程碑

| 里程碑 | 状态 | 完成 | 预计完成 |
|--------|------|------|----------|
| Phase 0 · MVP 核心剪辑引擎 | 🟢 done | 100% | 7/21 ✅ |
| Phase 1 · 极简可视化前端 | 🟢 done | 100% | 7/23 ✅ |
| v3.0 · Hooktheory BGM + SQLite + ffmpeg 渲染 | 🟢 done | 100% | 8/6 冻结为 v4.0 基线 ✅ |
| v4.0 · M2 决策自主环试点（wf01-wf05 交互版） | 🟡 in-progress | 60% | 8/6 开工，8/7 核验 60%；8/7-8/8 无新增投入 |
| Phase 1(旧) · 高级编排+模板 | ⚪ pending | 0% | 顺延 TBD |
| Phase 2(旧) · 变现交付 | ⚪ pending | 0% | 顺延 TBD |

#### 成本归集

| 月份 | 预算 | 实际 | 差额 |
|------|------|------|------|
| 2026-07 | $20 | ~$6 | +$14 |
| 2026-08 | $20 | ~$2.15* | +$17.85 |

> *2026-08 实际为 xiaofeng 全项目合计 $2.15（balance ledger 权威源，8/7 看板核对；预算 $15 口径，14%），项目内拆分估算待细化。

#### 本周更新（8/7-8/8）

- 8/7：OPC 看板 v1.6 初始化（Daryl 指令）——项目区清理为仅剩 剪辑MVP★ACTIVE + IELTS；任务清理 12 条；成本核对以 balance ledger 为准（8月 $2.15 / 累计 $91.52 / 742M tokens / 9564 calls）
- 8/7：ngrok 隧道由 8768 切换至 IELTS 8767（Daryl 练口语），视频编辑器公网入口暂让位；本地 8768 + LaunchAgent 托管不受影响
- 8/7：M2 前端 v4.0 交互版 60% 节点核验（无新增进度，等待继续开发）
- 8/8：无实质开发投入（仅心跳/审计，8/8 日记待补）

#### 关键决策

| 日期 | 决策 | 级别 | 状态 |
|------|------|------|------|
| 7/25 | v3.0 Grill压力测试通过+3Bug修复，核心链路走通；Justin Bieber That Should Be Me BGM结构导入 | P1 | 🟡 待验收 |
| 7/24 | Daryl 要求找《I NEED YOU》做 BGM，仅 QQ 音乐有源，等 Daryl 提供文件后跑 msaf 分析 | P2 | 🟡 等待 |
| 7/23 | Phase1 极简可视化前端当天交付 5 节点全可视化+API 对接；原 Phase1&2 顺延 | P1 | ✅ 通过（7/25 Grill确认） |
| 7/23 | L5 交付前质量自检基建落地：提测前必须完整 e2e 自检，不能把 Daryl 当 Debugger | P1 | ✅ 已落地 |
| 7/26 | Daryl Grill-me Q1 BGM歌库节点交互：确认只显示歌名（极简卡片方案） | P2 | ✅ 通过 |
| 7/22 | V3.4 按15:00会话严格修正：BGM Bridge→Intro、恢复海面、白建筑+鸟 | P1 | ⏳ 等待 Daryl 澄清 |
| 7/21 | Phase 0 完结，进入实战迭代验收阶段 | P1 | ✅ Daryl 确认 |
| 7/19 | 变现加速器定位：16:9+9:16双格式，BGM驱动编排+三层情感漏斗 | P1 | ✅ Daryl 确认 |
| 8/3 | 隧道三次刷新：synthesis-ent-hawaii-booth → freebsd-present-rome-modes（前隧道已过期），飞书直聊重建 ✅ | P2 | ✅ 完成 |
| 8/1 | 隧道二次刷新：degree-human-intro-airports → synthesis-ent-hawaii-booth，Daryl 确认可用 | P2 | ✅ 完成 |
| 8/6 | M2 试点开工：wf01-wf05 冻结为 v4.0 基线；前端 v4.0 交互版开发中（60% 节点，预估 8-12h） | P0 | 🟡 进行中 |
| 8/5 | Loop Engineering 移交 Kitty（更名「决策自主环」），M2 试点=剪辑MVP；Bryson 只保留剪辑MVP 开发 | P0 | ✅ 移交完成 |
| 8/5 | 机制分层落定：方向级→Daryl 确认；细节级→用户替身+决策账本自主（三方案经 Kitty 评估后取舍） | P1 | ✅ 已落定 |
| 8/5 | Daryl 纠正自诊断归因：真根因=Grill-me 交互逻辑问太少+实现自我简化+把产品逻辑问题当格式偏好问 → 「用户思维」三层检查清单入 workflow-rules | P1 | ✅ 已固化 |
| 8/5 | 素材扫描解阻：watchdog 误报/时长0/ASR前3 三 BUG 修复（launchd PATH + 前端 hardcode 根因），21 组素材可用 | P1 | ✅ 已修复 |
| 7/31 | Daryl 开始逐模块发送交互需求（01-素材扫描 4项）；小风回复可行性评估 ~3.5h 全部可行；隧道刷新为 degree-human-intro-airports.trycloudflare.com | P1 | ✅ Daryl 已确认（8/5 核实） |
| 7/30 | BGM节点v2 完成：歌曲卡片/音频播放器/乐句播放+和弦弹窗/ffmpeg乐句连接；隧道 scanner-valves-domain-traveling.trycloudflare.com；Daryl 指令暂不动，等全部需求一次性迭代 | P1 | ✅ 完成 |
| 7/28 | 飞书隧道修复：前端 API 路径 localhost→相对路径，隧道确认可用，Daryl 开始提交交互需求 | P1 | ✅ 已修复 |

#### 风险/问题

| 日期 | 风险 | 影响 | 措施 |
|------|------|------|------|
| 8/6 | workspace 指针丢失事故（8/4 openclaw.json 重写删 workspace 字段）→ 会话读错工作区短暂失忆 | 记忆系统可用性 | Kitty 已修复（4 agent 显式写死 workspace）；空壳工作区已隔离归档 workspace-xiaofeng.orphan-20260806；8/7 验证：新会话正确读取真工作区 ✅ 事故闭环 |
| 8/5 | launchd 托管服务默认 PATH 极简（无 /opt/homebrew/bin） | 素材时长/缩略图/ASR 返回空 | 双保险修复：server.py 补 PATH + shutil.which 绝对路径 + plist EnvironmentVariables |
| 7/25 | Toshiba HDD exFAT 卡死（BGM文件写入时） | 输出路径不可用 | 已请求 Daryl 物理重新插拔 → 8/5 恢复 ✅ |
| 7/24 | git rebase 事故：dashboard.html+shadow.html 从 HEAD 丢失 | DB+跟读页不可用，Daryl 发现后紧急恢复 | 已从子目录恢复；PROJECT_MANIFEST.md 标记唯一权威版本 |
| 7/24 | 项目副本混淆（ielts_tutor/ vs Xiaofeng/ielts_tutor/） | 导致恢复时定位混乱 | 清理：Xiaofeng/ 加 DEPRECATED.md、删除旧 DB/server 备份 |
| 7/23 | [object Promise] 阻断 Bug 提测前未发现 | 0.2 扫描页完全不可用，影响验收体验 | 已修复；L5 自检机制已落地 |
| 7/23 | API Server (8768) 进程挂掉 | 服务不可用 | 19:53 心跳修复并重启 |
| 7/22 | Insta360 FreeFrame 竖拍→ffmpeg 不自动旋转 | 竖版输出错误 | 已写入检测脚本修复 |
| 7/19 | DJI Mic 3 音频同步仅框架+模拟 | 多音轨场景不可用 | 等设备到位联调 |

---

### IELTS陪练助手v2.0

| 字段 | 值 |
|------|-----|
| 项目ID | ielts-tutor-v2 |
| 状态 | 🟡 verifying · v1.3.0 待 Daryl 验收；8/7 Daryl 实际使用练口语（隧道切 8767 + debug 拉起）→ 反馈 STT/ASR 不准 → 当晚修复并实测 100% 词级命中；8/4 服务 LaunchAgent 持久化 localhost:8767 ACTIVE；8/5 OPC看板v1.6 同步 wf_ielts_tutor_v130 工作流 |
| 优先级 | P0 |
| 当前阶段 | v1.3.0 开发完毕 + 8/7 STT/ASR 修复完成（VAD 参数宽容化 + beam 1→3），待 Daryl 实战验收 |
| 阶段进度 | 100%（含 8/7 STT/ASR 修复，stt_streaming.py 有 .bak_20260807 备份，commit 待补） |
| 总进度 | 88% |
| 启动日期 | 2026-06-08 |
| 预计交付 | v1.1.0 挂起中，v1.3.0 待验收 |
| 上周进展 | 7/25 Daryl 飞书调试发现 2 Bug 并修复 ✅：① DeepSeek 废弃 `deepseek-chat` → `deepseek-v4-pro` ② 跟读 JS null safe 兜底；Daryl 指令：自由对话切 `deepseek-v4-flash` + Debug 模式开启 ✅；8/4 服务 LaunchAgent 持久化（ai.openclaw.ielts，localhost:8767，health+dashboard 均 200）；8/5 OPC看板v1.6 同步 wf_ielts_tutor_v130 11 节点工作流（投资人展示准备）；8/7 晚 Daryl 要求练口语：ngrok 隧道 8768→8767 切换 + DEBUG_MODE=1 拉起 debug 模块（/debug/sessions 200）；Daryl 反馈 STT/ASR 识别不准 → 根因定位 VAD 过激（threshold=0.5+min_silence 600ms+pad 400ms 误删 30-43% 语音）+ beam=1 质量最低档 → 修复（VAD 0.35/900ms/700ms + beam 3）→ 实测 5.2s 短句 100% 词级命中 + 15s 长句 49/49 全对 |
| 本周计划 | Daryl 实战验收 v1.3.0 + STT 修复效果（刷新 unwhispering-imani-digitately.ngrok-free.dev 即可）；如有口音个别词不准，评估 small.en→medium.en 或 IELTS_STT_MODEL 覆盖 |
| 阻塞项 | ① iPhone 语音输入问题 → v1.1.0 挂起 ② ~~STT/ASR 识别不准~~ ✅ 8/7 已修复并实测（VAD+beam） ③ 等待 Daryl 实战验收 v1.3.0（8/7 已开始使用） |

#### 里程碑

| 里程碑 | 状态 | 完成 | 预计完成 |
|--------|------|------|----------|
| M1 · 双管线核心+评估+持久化 | 🟢 done | 100% | 7/5 ✅ |
| M2 · 延时优化+管线2修复 | 🟢 done | 100% | 7/15 ✅ |
| v1.0.1 · 移动端自适应 | 🟢 done | 100% | 7/16 ✅ |
| v1.1.0 · iPhone优化+交互重构 | 🔴 suspended | 70% | 挂起 |
| v1.3.0 · 深度对话+词汇+Dashboard | 🟡 verifying | 100% | 7/22（开发完毕）；8/7 STT/ASR 修复后进入实战验证 |
| M3 · Part2/3 深度模式 | ⚪ pending | 0% | TBD |

#### 成本归集

| 月份 | 预算 | 实际 | 差额 |
|------|------|------|------|
| 2026-06 | $20 | ~$18 | +$2 |
| 2026-07 | $15 | ~$6 | +$9 |
| 累计 | — | ~$23 | — |
| 2026-08 | $15 | ~$0* | +$15 |

> *8/7 起 IELTS 恢复使用（隧道切换+STT 修复），相关 token 消耗并入 xiaofeng 8月合计 $2.15（balance ledger 权威源）。

#### 关键决策

| 日期 | 决策 | 级别 | 状态 |
|------|------|------|------|
| 7/25 | Daryl 调试发现 2 Bug → 修复；指令：自由对话切 `deepseek-v4-flash` 降延迟、开 Debug 模式 | P1 | ✅ 已修复 |
| 8/7 | Daryl 要求练口语 → ngrok 隧道切 8767 + DEBUG_MODE=1 拉起 debug；随后反馈 STT/ASR 不准 → 修复 VAD（0.5→0.35 / 600→900ms / 400→700ms）+ beam 1→3，实测 100% 词级命中 | P1 | ✅ 已修复（commit 待补） |
| 7/24 | 数字资产丢失事故：dashboard.html+shadow.html git rebase 后丢失，已从子目录恢复；建立 PROJECT_MANIFEST.md 权威版本标记机制 | P1 | ✅ 已恢复 |
| 7/22 | NHL 验收：跟读作用域/Vocab列过滤/训练总结展开/上轮对话回显修复通过 | P1 | ✅ Daryl 确认 |
| 7/22 | free_talk 深度对话优化（选项A）：VAD窗口+STT碎片+提示词重写 | P1 | ✅ 开发完毕 |
| 7/17 | v1.1.0 因 iPhone 语音输入+交互拖沓暂停，转其他任务 | P1 | ✅ Daryl 确认 |
| 7/16 | M2 验收认定完成（看板验收） | P1 | ✅ Daryl 确认 |
| 7/15 | 交叉开发模式确立：雅思门控期→洗稿午验收 | P1 | ✅ Daryl 确认 |

#### 风险/问题

| 日期 | 风险 | 影响 | 措施 |
|------|------|------|------|
| 7/22 | Ngrok ERR_NGROK_725 带宽超限 | 远程验收不可用 | 切HTTPS局域网自签证书 |
| 8/7 | STT/ASR 识别严重不准（VAD 误删 30-43% 语音 + beam=1 最低质量档，识别出 "in my uh" conf 0.26 残句） | 口语练习体验受损 | 已修复：VAD 宽容化 + beam 3；TTS 实测短/长句均 100% 命中；待 Daryl 真实口音验证 |
| 7/17 | iPhone 语音输入不可靠 | v1.1.0 挂起 | 平板测试正面反馈，iOS 回退 |

---

## 🟡 规划中项目

| 项目名 | 方向 | 优先级 | 预计启动 |
|--------|------|--------|----------|
| 硬件语音助手(MCU) | ESP32等MCU端侧语音交互 | P2 | 待 IELTS v2.0 稳定 |
| ~/opc-workspace rebase 修复 | 本地仓库卡 rebase 中间态，auto-backup 在 detached HEAD | P2 | 待与 Daryl/Kitty 确认 |

---

## 🔵 已完成项目

| 项目名 | 交付日期 | 最终状态 | 归档链接 |
|--------|----------|----------|----------|
| 洗稿MVP v1.2.0 | 2026-07-18 | ✅ 内核卡 M1-M3 完整交付 | `rewrite-mvp/` |
| IELTS陪练助手v2.0 M2 | 2026-07-16 | ✅ 延时优化达标，管线2冻结 | `ielts_tutor/` |
| IELTS陪练助手v2.0 M1 | 2026-07-05 | ✅ 双管线90%交付 | `ielts_tutor/` |
| 视频分析交互Workflow v1.x | 2026-07-04 | ✅ 三代迭代(Gemini V3原生视频) | `video_analyzer_app/` |
| OPC机制基建统一规范 v2.0 | 2026-06-15 | ✅ 已同步4 Agent | `memory/mechanism-infra-spec.md` |
| 成本追踪系统 | 2026-06-06 | ✅ 全Agent部署 | `deepseek_cost_tracker.py` |

---

## ⚪ 归档

| 项目名 | 归档日期 | 最终状态 | 备注 |
|--------|----------|----------|------|
| OPC总控看板 | 2026-06-14 | 已移交 Kitty | M2完成后移交，Kitty全权负责 |
| 视频分析 10fps Vision管线 | 2026-07-04 | 被 Gemini V3 替代 | 首测通过但成本高，V3原生视频更优 |
| Agent自进化 | 2026-07-16 | Daryl 看板验收确认非现存任务 | 已从待办移除 |
| ngrok 备用隧道 | 2026-07-16 | Daryl 看板验收确认非现存任务 | 已从待办移除 |

| 洗稿MVP v1.2.0（rewrite-mvp） | 2026-08-07 | standby · 需求收集模式（20天无输入） | v1.2.0 已交付，待 Daryl 新需求恢复 |
| Loop Engineering → 决策自主环 | 2026-08-05 | 已移交 Kitty | M0机制冻结→M1决策工具→M2剪辑MVP试点→M3推广，开发权归 Kitty |
| 视频分析交互Workflow | 2026-08-07 | maintenance · 不再投入 | v1.x 三代完成，长视频优化取消，维持现有能力 |

