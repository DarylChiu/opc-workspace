# lessons.md — 经验教训精华

## 2026-06-15 · 数字资产丢失
- **教训**: M1代码无git管理→覆盖丢失；6/12日记缺失→Workflow需求蒸发
- **整改**: git强制管理(T0)、日记每日必写、合规系统强制执行

## 2026-06-14 · 基建合规审计
- **教训**: 「建了就放」是最大问题，强制执行机制缺位
- **整改**: 从Agent自觉→系统强制，23:59 Cron兜底

## 2026-06-11 · 思考不全面
- **教训**: 快速作答导致遗漏关键信息
- **整改**: Thinking Completeness Protocol，复杂问题深度分析

## 2026-06-11 · 模型成本
- **教训**: 非必要时用高价模型
- **整改**: 统一DeepSeek V4 Pro，T1-T4不区分

## 2026-06-08 · 双Agent代码冲突
- **教训**: 两人同时修改index.html→协调混乱
- **整改**: 明确分工(Kitty前端/Bryson后端)，互不越界

<<<<<<< HEAD
### API Key 复制粘贴陷阱
- **问题**: Chat 消息手打错字母 P→Q，白白 debug 半小时
- **教训**: API Key 永远从凭证文件/CSV 复制，绝不要手打

### 🔴 脚本分散维护问题（2026-06-25 发现）
- post-op.sh 是每个 Agent 独立维护的，Self 的修复不会自动同步到 xiaofeng
- 后续考虑：提取公共合规逻辑到共享脚本，Agent 只维护自己的特殊规则

## 技术开发
1. **单一入口点原则** — MVP阶段不要搞前后端分离，HTML内嵌到后端最简单可靠
2. **进程残留是隐形杀手** — 部署前必须彻底清理旧进程，不能只看端口是否有响应
3. **用户截图比日志有用** — 版本冲突问题是通过用户截图（繁体vs简体）发现的
4. **SSL证书链** — macOS Python需要手动安装证书，开发环境可临时禁用验证
5. **语音应用必须双向设计** — 只有TTS输出没有用户输入处理是核心缺陷
6. **预留接口** — STT接口预留让后续集成不需要重构架构

## 开发哲学
1. **先验证上限，再降本** — 2026-06-19 Daryl指令：先不计成本开发出能达到需求的产品MVP，然后再降低单位产出成本。不要用低成本方案+打补丁的方式碰运气，换了个测试样本补丁就不适用
2. **高密度数据可能消除补丁需求** — 如10fps Vision分析的帧密度足够高时，因果推理和叙事结构理解可能不需要额外Pass来修补

## 项目管理
1. **成本核算用API实际调用费** — 不要用人工工时估算
2. **里程碑进度汇报** — Daryl要求定期汇报，不能闷头干
3. **方案对比决策** — 给出A/B方案让用户选择，不要自己拍板

## 协作经验
1. **不要过度设计** — Kitty之前的通信系统（Python daemon、安全令牌）严重超出需求
2. **用原生工具** — OpenClaw自带sessions_send/sessions_list就够了，不需要自建
3. **指令遗漏是重大事故** — 2026-03-30 遗漏用户3条指令，导致上下文断裂
4. **🔴 双轨通信** — Agent间通信用sessions_send高效传递，但必须同时在群聊发简短摘要+「（已通过sessions_send通信，对方已收到）」，不@对方以免重复消耗token。Daryl需要看到执行脉络

## 故障诊断（2026-06-07）
1. **先看日志再动手** — 改了4次代码才看日志，3次同一条错误 `ClientDisconnect`，早看日志5分钟解决
2. **本地验证隔离问题** — 绕过tunnel直连localhost测试，2.6秒返回证明后端+API正常，瞬间锁定根因
3. **免费Tunnel不可靠** — Cloudflare trycloudflare.com 会掐断大POST请求，生产环境必须用 ngrok 或正规 Tunnel
4. **治本不治标** — 压缩音频、延长超时都是打补丁，换传输通道才是根本

## 合规系统部署
### 2026-06-26: 升级≠搬迁——不要给已有 Agent 建新 workspace
- 给已有 Agent 部署新系统时，应**升级现有 workspace 的工具**（切 symlink），而非新建 workspace 再试图迁移
- 根因：把「部署新合规系统」等同于「给新 Agent 建 workspace」的思维惯性
- 实际：main 是系统中最老的 Agent，workspace 已运行数月
- 正确做法：旧脚本备份→切 symlink→验证

## 记忆系统（上次重构总结）
1. **MEMORY.md不能当垃圾桶** — 只放高频核心索引，<30行
2. **分层是关键** — 身份/活跃任务/项目归档/经验教训 各司其职
3. **定期归档清理** — 日记>60天的要压缩归档，避免搜索噪音
4. **身份信息强制加载** — 不依赖memory_search，直接写入identity.md每次读取

## 2026-06-28 · CSS 滚动链修复
- **问题**: 对白列表 `.transcript-list` 有 `flex:1; overflow-y:auto` 但无法滚动
- **根因**: 父容器 `.transcript-col` 不是 flex 容器且无高度约束，子元素的 `flex:1` 无参考高度
- **修复**: 父容器加 `display:flex; flex-direction:column; flex:1; min-height:0` — 四个属性缺一不可
- **教训**: flex 子元素要 overflow 生效，整条祖先链都必须有 `min-height:0`

## 2026-07-23 · 提测前必须自检（血的教训）
- **教训**: 开发完成后跳过端到端自检直接给 Daryl 验收，结果 [object Promise] 这种低级 Bug 浪费他 1-2 小时
- **根因**: 急于交付、功能贪多(32h 硬塞半天)、流程缺 checklist
- **修复**: 建立 L5 交付前质量自检（5 项强制检查），嵌入 AGENTS.md + TOOLS.md
- **铁规**: 任一项不通过，先修再提测，不要把 Daryl 当 Debugger

## 2026-07-23 · async/await 陷阱
- `async function` 返回 Promise，不能用同步方式赋给 innerHTML
- `render()` async 后，`navigateTo()` 也要 async
- 测试方法: 打开页面检查是否显示 `[object Promise]`

## 2026-07-23 · Cloudflare Tunnel 不稳定
- 免费 tunnel ERR 1033 频繁出现，TLS 握手完成但无法连接 origin
- 替代方案: localtunnel (`lt --port`) 或直接 localhost（同机器）

## 2026-07-25 · DeepSeek API 模型名废弃导致 LLM 乱码
- **问题**: 旧模型名 `deepseek-chat` 已被废弃，API 可能返回乱码/无效响应
- **影响**: IELTS 陪练助手的 LLM 对话、评估功能全部异常
- **修复**: 全局替换为 `deepseek-v4-pro`
- **教训**: API 模型名不是永久的；服务商可能直接废弃旧名称而非优雅降级；应定期检查 API 文档确认模型名有效性

## 2026-07-22 · OPC 多 Agent 共享仓库 git rebase 极高风险
- **问题**: git pull --rebase 触发 59 个 commit 跨多 Agent 目录的大规模冲突，rebase 卡死后 abort 被 SIGKILL
- **根因**: 多 Agent 各自维护 memory/ + scripts/ 等共享文件，频繁交叉提交导致 rebase 冲突不可避免
- **修复**: `git checkout -f main && git reset --hard origin/main` 强制恢复，已修改但未 push 的日记文件从心跳内容重建
- **教训**: **共享仓库优先用 merge 策略**，`git pull --rebase` 在多人/多 Agent 环境下是定时炸弹；push 前必须 commit 所有修改

## 2026-07-24 · 项目版本管理混乱导致数字资产丢失
- **教训**: 同一项目存在多个副本（ielts_tutor/ vs Xiaofeng/ielts_tutor/）极易混淆
- **教训**: git rebase 前必须确保所有改动已 commit，否则工作目录修改全部丢失
- **教训**: 项目必须有唯一权威版本标记（PROJECT_MANIFEST.md），注明活跃目录、活跃DB、废弃副本
- **教训**: 废弃副本必须标记 DEPRECATED.md，防止误用
- **教训**: Daryl 的 7/21 重设计工作在 Xiaofeng/ 子目录里，rebse 后 rush 恢复主目录时遗漏了子目录里的文件

## 2026-08-06 · workspace 指针丢失导致失忆（重大）
- **问题**: 8/4 openclaw.json 重写时 agents.list 的 workspace 字段被删 → 新会话回退默认 `workspace-xiaofeng` 空壳（IDENTITY.md 空模板）→ 我 11:03 误诊「身份没落盘」
- **真相**: 真工作区 `xiaofeng_workspace` 6/28 就写好了 Bryson/吹点小风；根因是指针丢失，不是身份没记录
- **失职点**: session 启动时没核对记忆完整性（identity.md/active.md/日记数量），读到的记忆异常单薄时没有警觉
- **修复**: Kitty 11:11 恢复 4 agent workspace 指针并重启 gateway；我 11:57 补跨工作区同步（shell 归档+orphan 标记）
- **教训**: ①启动必核对记忆文件完整性，发现异常立即上报而非自我解释 ②一个 Agent 只能有一个工作区，出现双工作区=配置事故 ③核心配置变更（openclaw.json）后必须验证 workspace 指针

## 2026-10-27 · audit.sh 交叉验证假阴性：不能只信脚本的「无活动」结论
- **问题**: 23:59 审计第 6 项「Session-Diary 交叉验证」判定「今天无实质 session 活动（仅 cron/审计）」，但实际当日有大量实质工作（本 Agent 交接清单 + 7 份 SOP 归档；Balance 华特 5 版迭代）
- **根因**: 该检查覆盖范围与时区/判据过窄，只扫部分 session 或按当日已写日记反推，形成假阴性；Cron 骨架日记因此被「认证」为无需补记
- **修复**: 手工 `sessions_list` 交叉核对近 24h 全 Agent session，据实补写 `memory/2026-10-27.md`，并在 active.md 记录待修
- **教训**: ①**审计脚本的"PASS"不等于事实正确**——凡涉及「今天有没有做事」的判断，必须自己拉 session 列表复核 ②Cron 骨架日记不能因为脚本说"无需补记"就放过，骨架=证据缺失，默认应补 ③脚本判据有盲区时要记入待修清单，别让同一个假阴性连犯多日
=======
---
*更多详情见 memory/learning_*.md*
>>>>>>> f84ca06f29566ba0eac5d0b2a33984ab963d31d6
