# 搬家后开机检查清单（越南 UTC+7 → 广东江门 UTC+8）

> 创建：2026-10-30 · 执行时机：11/1 抵达后首次开机
> 目标：**开机后能正常继续工作**，定时任务不漂移

## P0 · 必做（不做会静默坏掉）

### 1. 系统时区确认
```bash
date              # 应显示 CST +0800 / Asia/Shanghai
sudo systemsetup -gettimezone
# 若不对：sudo systemsetup -settimezone Asia/Shanghai
```
> macOS 改系统时区后，crontab 与 launchd 的「墙钟时间」自动跟随，无需改数字

### 2. OpenClaw Gateway 时区
- 检查 `~/.openclaw/openclaw.json` 是否有显式 tz 字段（当前无 → 跟随系统）
- 改后必须：`openclaw gateway restart`

### 3. OpenClaw cron job 时区（**必须改**）
当前 `14d6ef92 每日记忆归档`：
- `schedule.expr = "59 23 * * *"` · `schedule.tz = "Asia/Saigon"`
- 搬家后若不改 → 会在广东时间 **00:59** 跑（偏移 1 小时，跨日导致日记日期错位）
- 改为 `"tz": "Asia/Shanghai"`：
```bash
# 通过 cron 工具 update（不要手改 sqlite）
cron update jobId=14d6ef92-a3af-4b6f-bb78-6b3cb2d33437 patch.schedule.tz=Asia/Shanghai
```
- 验证：`cron list` → nextRunAtMs 应为当地 23:59

### 4. ~~修 deepseek auth~~ ✅ 已于 10/30 09:4x 验证正常
- 10/30 00:08 cron 曾报 `No API key found for provider "deepseek"`
- 核查 auth store（`auth_profile_store` 表）：`deepseek:default` api_key 存在（len 35），google 也在
- 本 session 正常跑在 deepseek-v4-flash 上 → **auth 链已恢复正常**，无需修
- 若 11/1 后 cron 再报同样错，才需 `openclaw agents add main` 重配
- 验证方式：`cron run jobId=14d6ef92-... runMode=force`

## P1 · 应做（体验退化）

### 5. crontab 生活提醒语义确认
当前（数字不变即墙钟不变，**多数无需改**）：
| 时间 | 内容 | 搬家后是否需要改 |
|---|---|---|
| 07:20 | 早上涂软膏 | ❌ 保持墙钟 07:20 |
| 20:00 | 花青素 | ❌ 保持 |
| 23:00 | 睡前准备 | ❌ 保持 |
| 23:30 | 确认就寝 | ❌ 保持 |
| 23:59 | xiaofeng 审计 cron | ❌ 保持 |
| 07/13/19:00 | 项目进度通知 | ❌ 保持 |
| 08:00 周一 | searxng 周检 | ❌ 保持 |
| 08:00 | ops center | ❌ 保持 |
| */5 | dashboard watchdog | ❌ 与 TZ 无关 |

> ⚠️ 唯一需注意：如果有「必须对应越南时间某绝对时刻」的任务才需 +/-1h。当前清单里没有。
> `crontab -l` 备份：`crontab -l > ~/Desktop/crontab-backup-20261030.txt`

### 6. launchd 验证
```bash
launchctl list | grep -E 'openclaw|opc'
# 两个关键：ai.openclaw.gateway（常驻）/ ai.openclaw.daily-memory-check（23:59）
# ai.openclaw.daily-memory-check 与 com.opc.autobackup 均为 23:59 墙钟 → 自动跟随系统 TZ
```
- 若 gateway 未自启：`launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway`

### 7. 外网连通性（搬家换网络）
```bash
curl -s -m 10 https://api.deepseek.com >/dev/null && echo "deepseek OK"
curl -s -m 10 https://api.moonshot.ai >/dev/null && echo "moonshot OK"
curl -s -m 10 https://open.feishu.cn >/dev/null && echo "feishu OK"
```
- 若飞书长连接断：`openclaw gateway restart`
- ngrok / serveo / cloudflared 隧道 IP 会变，需重启 autossh：
```bash
@reboot 已配置，重启即可；手动：AUTOSSH_PIDFILE=/tmp/autossh_serveo.pid autossh -M 0 -f -i ~/.ssh/id_ed25519_serveo -R opc-darylchiu:80:localhost:8765 serveo.net
```

## P2 · 可选（技术债）

### 8. 仓库瘦身（.git 已 783M，bundle 717M）
- 50817 个 tracked venv 文件（keyframe_venv 的 torch/paddle/cv2）
- 建议搬家后：`.gitignore` 加 `*_venv/`，用 `git filter-repo` 清历史，或新建干净仓
- 风险：不可逆操作，需 Daryl 批准

### 9. workspace 补 remote（可选）
当前无 remote → 本地 commit 推不出去，靠 `~/.opc-workspace-cache` 独立仓做备份
- 若要补：`git remote add origin git@github.com:DarylChiu/opc-workspace.git`（注意分支冲突风险）

## 备份文件位置（桌面，11/1 开机前若换机器可用）
- `~/Desktop/openclaw-backup-main-20261030.tar.gz`（669K · 记忆+脚本+交付物）
- `~/Desktop/openclaw-workspace-main-20261030.bundle`（717M · 全量 git）
- `~/Desktop/openclaw-config-backup-20261030.tar.gz`（22M · 配置+auth）

## 恢复方式（如需换机）
```bash
mkdir -p ~/.openclaw/workspace && cd ~/.openclaw/workspace
git clone ~/Desktop/openclaw-workspace-main-20261030.bundle .
cd ~/.openclaw && tar -xzf ~/Desktop/openclaw-config-backup-20261030.tar.gz
```
