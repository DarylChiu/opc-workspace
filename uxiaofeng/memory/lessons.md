# 经验教训精华

### 2026-06-25 合规自动化盲区：讨论/辩论/指令类交互被忽略
- **问题**: post-op.sh 关键词只匹配「完成/交付/修复」类，Daryl 的指令下达、架构讨论、方案辩论全被归为「查询类」跳过
- **发现者**: Self 先诊断，Daryl 要求全员检查 → 确认我也有同样问题
- **修复**: (1) 扩展触发词（决策/方案/架构/讨论/辩论/指令/规划/设计/重构/调整/优化/升级）(2) Cron 骨架检测：日记 <15行 + 仅 Cron 事件 → 强制告警 (3) 阈值从 3 行提到 15 行
- **教训**: 自动化合规是兜底，不能替代主动判断。每个 Agent 都需要在相同基础上独立维护自己的合规脚本，不能假设别人的修复会自动同步到自己

## 🔴 2026-06-29 踩坑集
### WebSocket 竞态条件：不要盲等固定时间
- **问题**: endSession 发 evaluate_final 后盲等 5s 关 WebSocket，DeepSeek 评估超时则分数丢失
- **修复**: 改为事件驱动 — 等 score 消息到达再 cleanup，15s 安全兜底
- **教训**: 异步流程不能用固定 timeout，必须用事件回调/标志位控制生命周期

### VAD flush 堆积 — 生产者-消费者不匹配
- **问题**: VAD HANGOVER=5(1.3s断句) 产生大量 flush，process_utterance 慢(3-8s DeepSeek) → WebSocket 消息队列阻塞
- **修复**: `processing_utt` 并发保护 — 正在处理时跳过新 flush，音频累积等下一轮
- **教训**: 流式处理必须处理生产速度 > 消费速度的场景

### Agent 间通信路径验证
- **问题**: Kitty inbox 端口(8766 vs 8765)、workspace 目录名(xiaofeng vs Bryson)全搞错，产物推送2次都失败
- **教训**: 跨 Agent 通信前先确认端点/端口/目录名，不要假设

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

## 2026-07-24 · 项目版本管理混乱导致数字资产丢失
- **教训**: 同一项目存在多个副本（ielts_tutor/ vs Xiaofeng/ielts_tutor/）极易混淆
- **教训**: git rebase 前必须确保所有改动已 commit，否则工作目录修改全部丢失
- **教训**: 项目必须有唯一权威版本标记（PROJECT_MANIFEST.md），注明活跃目录、活跃DB、废弃副本
- **教训**: 废弃副本必须标记 DEPRECATED.md，防止误用
- **教训**: Daryl 的 7/21 重设计工作在 Xiaofeng/ 子目录里，rebse 后 rush 恢复主目录时遗漏了子目录里的文件
