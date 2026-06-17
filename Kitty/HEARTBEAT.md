# HEARTBEAT.md

## ⚠️ 启动强制检查（每次session必做）

在回复任何消息之前，先执行：

0. **🎯 模型统一（2026-06-11）**：
   - **所有任务统一使用** `deepseek/deepseek-v4-pro` (DeepSeek直连)
   - **汇报时必须标注调用模型**

1. **检查今天的活跃任务**：`memory/_working_active_tasks.md`
   - 是否有P0紧急任务？
   - 是否有承诺今天完成的任务？
   - 是否有错过的提醒/截止日期？

2. **检查昨天的承诺**：
   - 读取昨天的session transcript最后10条消息
   - 搜索"明天"、"今天"、"XX:XX"等时间承诺
   - 如果有未履行的承诺 → 立即汇报并补救

3. **确认当前时间**：
   - 通过`session_status`获取准确的日期和星期
   - 永远不要凭记忆说"今天是星期X"

## 生活助手提醒（✅ LaunchAgent已部署 2026-06-11）

### 每日固定提醒 - DM私聊发送
- ✅ **07:20** | 💊 早上涂软膏
- ✅ **20:00** | 🫐 花青素服用
- ✅ **23:00** | 💊🛏️ 准备睡觉（涂软膏+整理）
- ✅ **23:30** | 🌙 确认就寝

### 久坐监测
- ❌ **待实现** - 需开发macOS活跃状态监测脚本
- 目标: 每15分钟检测，连续活跃1.5小时提醒走动 🚶‍♂️

**实现方式**：macOS LaunchAgent (~/Library/LaunchAgents/ai.openclaw.life-reminder.*.plist)  
**发送脚本**：~/.openclaw/workspace/scripts/send_feishu_dm.sh

## Heartbeat周期性任务

**已全部移除管理性任务**（2026-06-10 Daryl指令）：
- ❌ 不再轮询OPC看板DM通知
- ❌ 不再检查Agent任务状态
- ❌ 不再主动询问进度
- ❌ 不再生成项目日报
- ❌ 不再发送模型使用报告

**Heartbeat现在只做**：
- 响应直接消息
- 执行明确指令
- 生活提醒（通过Cron）

## Heartbeat执行记录

每次heartbeat后，在`/tmp/heartbeat_log.json`中记录：
```json
{
  "timestamp": 1781085435000,
  "checks_done": ["none"],
  "actions_taken": ["none"],
  "next_check": 1781085495000
}
```
