# MEMORY.md - 长期记忆

> 最近更新：2026-08-06

## 关于本工作区
- 主人：Daryl（Feishu 用户 DarylChiu；群聊「OPC of DarylChiu」为 OPC 群）。
- 我：**Bryson（吹点小风）**，AgentID `xiaofeng`，工作区 `workspace-xiaofeng`，2026-08-04 初始化，2026-08-05 完成 bootstrap。
- 注意：我的名字是 Bryson / 吹点小风（2026-08-06 Daryl 确认），见 IDENTITY.md。
- 渠道：Feishu。时区：Asia/Saigon (GMT+7)。

## 项目
- 暂无实际项目。`memory/project_xiaofeng.md` 为项目看板，bootstrap 后开始归集。

## 基建
- 每日记忆归档 cron 任务已配置（每晚运行 `scripts/compliance/audit.sh --report`，修复问题后向 OPC 群发完成通知）。
- 2026-08-05 自建 `scripts/compliance/audit.sh`：审计记忆文件健康度（MEMORY.md、每日记录、看板、git 状态）。

## 经验教训
- 定时任务依赖的脚本若缺失，先手动审计兜底，再补齐基建，避免任务空转。
- 文档优于脑记：任何决定/事件写进 `memory/YYYY-MM-DD.md`。
