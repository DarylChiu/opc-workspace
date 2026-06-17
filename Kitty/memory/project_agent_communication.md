# Project: Agent间通信系统

## 历史记录

### 第一次尝试: 共享文件系统 (2026-03)
- 基于shared_memory/目录的JSON文件协作
- 结构：master/ + agents/ + logs/
- 问题：轮询式延迟高、文件锁冲突、长期停滞未更新

### 第二次尝试: 消息总线方案 (2026-05-21)
- 网关部署在Mac mini端口9001
- Redis消息总线端口6379
- 双令牌验证（网关令牌+节点令牌）
- 放弃飞书原生@通信方案
- **状态**: 基础架构搭建完成，未完成Bryson节点注册验证

### 第三次（当前）: OpenClaw原生工具 (2026-06-06)
- Daryl指定使用sessions_send / sessions_list
- 小枫牵头设计，Kitty配合联调
- **通信协议v2**: ~/.openclaw/kitty_collab/agent-comm-protocol-v2.md
- **共享任务板**: ~/.openclaw/kitty_collab/tasks.md
- **Session Keys**:
  - Kitty: `agent:main:feishu:group:oc_7d71d54d87cbd265d9c3811bc59840b2`
  - 小枫: `agent:xiaofeng:feishu:group:oc_7d71d54d87cbd265d9c3811bc59840b2`
- **联调进展**:
  - ✅ 小枫→Kitty: sessions_send 成功
  - ✅ Kitty→小枫: sessions_send 成功
  - ✅ 共享文件空间kitty_collab/ 双向读写OK
  - ✅ 共享任务板双向同步OK
  - ✅ 冲突避免规则（3-5s随机延迟）已加入协议
  - ✅ 离线接管规则（5min超时）已加入协议
  - **状态: 联调完成 ✅**

### 核心问题（已解决）
- ~~飞书群内Agent互相看不到对方消息~~ → sessions_send 双向通信OK
- 群聊@路由: 协议已定义分工规则，实际验证需等下次群聊触发
