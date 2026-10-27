# IELTS Tutor — 项目清单

> ⚠️ 最后更新: 2026-08-15 (v1.5.0) | 此文件是唯一权威版本标记
> 格式: 永远从这里找最新版，不要凭记忆

## 🏠 唯一工作目录

```
ielts_tutor/
├── backend/
│   ├── server.py          ← 主服务器 (8767端口, /dashboard /shadow /monitor; v1.4.0 Free Talk 持久记忆: 256K窗口+压缩摘要)
│   ├── session_manager.py ← 数据层 (sessions/transcripts/evaluations/errors/review_items/shadow_attempts/ft_memory)
│   ├── stt_streaming.py   ← faster-whisper 本地STT
│   ├── tts_streaming.py   ← Kokoro+Piper 本地TTS
│   ├── config.py
│   ├── conversation_engine.py
│   ├── debug_logger.py
│   ├── pipeline_qwen_omni.py
│   └── report_generator.py
├── frontend/
│   ├── index.html         ← 口语训练主页
│   ├── dashboard.html     ← 训练数据库 (7/21重新设计版, 413行)
│   ├── shadow.html        ← 跟读巩固 (7/21版, 345行)
│   ├── monitor.html       ← 调试事件流面板
│   └── vocab.html         ← Vocabulary复习
├── data/
│   └── ielts_tutor.db     ← **活跃数据库** (92 sessions, 32 review_items, 13 shadow_attempts)
├── debug-data/
│   └── debug_sessions.db  ← 调试会话日志
├── reports/               ← HTML评估报告
├── references/            ← 参考模板
└── VERSION                ← 版号文件
```

## 🗄️ 数据库说明

| 文件 | 大小 | 内容 | 来源 |
|------|------|------|------|
| `data/ielts_tutor.db` | — | 100+ sessions, ft_main(持久free talk), ft_memory(压缩摘要) | 从 Xiaofeng/ 副本恢复 (7/22) + v1.4.0 扩展 |

## 👤 v1.5.0 用户系统 P1 (2026-08-15)

- `backend/auth.py`: users + auth_tokens 表 / PBKDF2-HMAC-SHA256 (200k 迭代) / token 30 天可吊销 / 登录限流 20次/10分、注册 5次/时
- API: /api/auth/register|login|logout|me (Bearer token)
- 页面: `frontend/login.html` + `/login` 路由 (主题与主站一致)
- **AUTH_REQUIRED=0 默认 guest** — 现有路由零影响；P2 数据隔离完成后置 1
- commit: d4ca27d

## ✨ v1.4.1 题库改造 A+B (2026-08-15)

**A 结构化种子库**: `data/question_bank.json` — Part1 30话题×5问 / Part2 60张cue card(6主题×10, 每张4要点+跟进) / Part3 30主题×5问；120 唯一题
**B 变体层**: 12 张槽位卡随机填充 → ~100 组合
**引擎**: `backend/question_bank.py` — 全局去重 (question_progress 表, user_id 预留) + 全部练完自动轮换 + 题库异常兜底硬编码
**注入**: server.py 抽题存 session, system prompt 加种子, Part2 问候语=抽到的题卡 (不再固定 book 卡), Part3 问候语=主题首问
commit: 7cb6231

## ✨ v1.4.0 Free Talk 持久记忆 (2026-08-15)

**方案**: 单条持久会话 `ft_main` + 256K 上下文窗口 + 超限压缩摘要（双层记忆）
- 原文全量留 SQLite (transcripts 表, 真相源)，压缩摘要只影响喂给模型的视图 (ft_memory 表)
- 256K 硬上限 / 230K 触发压缩软阈值；窗口裁剪保守估 token (字符数)，只早压不超限
- 压缩幂等: 按 compacted_seq 推进；摘要合并式更新 (旧摘要+新对话→新摘要)
- 多用户预留: `ft_{user_id}` + ft_memory.user_id 列
- 旧 9 个 free_talk 会话已迁移合并进 ft_main

## 📋 历史事故记录

### 2026-07-21~22 git rebase 事故
- **丢失**: dashboard.html, shadow.html, server.py (dashboard API), session_manager.py (review方法), ielts_tutor.db (完整数据)
- **恢复来源**: `Xiaofeng/ielts_tutor/` 子目录副本（7/22 保存）
- **恢复内容**: 前端2文件 + 后端2文件 + 数据库
- **教训**: rebase 前必须确保所有改动已 commit；子目录的独立副本救了命

## 🔄 版本回滚机制

### 原则: 归档而非删除
- **永远不要 `rm` 旧版本** — 你不知道哪天哪个功能要回退
- 旧版本移到 `_archive/YYYY-MM-DD_HHMM_原因/` 目录
- 每次清理前运行: `bash scripts/archive-before-cleanup.sh "清理描述"`
- Git 作为主版本控制: 每次清理前 commit

### 回滚方法
```bash
# 方法1: 从归档目录恢复
ls _archive/                          # 查看所有快照
cp -r _archive/2026-07-24_1200_xxx/* .  # 恢复到指定快照

# 方法2: 从 git 恢复单个文件
git log --oneline -- frontend/dashboard.html   # 查看历史
git checkout <commit-hash> -- frontend/dashboard.html  # 恢复
```

### 当前归档
| 快照 | 时间 | 原因 |
|------|------|------|
| — | — | 暂无（已删除的副本在 git stash 中） |

## 🚫 已废弃/混淆源（参考用，勿运行）

| 路径 | 说明 |
|------|------|
| `Xiaofeng/ielts_tutor/` | **7/21完整副本，仅作回退参考** |
| `.opc-workspace-cache/Xiaofeng/ielts_tutor/` | 7/19 旧版快照，**已过期** |
| `opc-workspace/xiaofeng/ielts_tutor_v2/` | v2 早期原型，**已废弃** |
| `.opc-workspace-cache/ielts_tutor/` | 更早期的快照，**已过期** |

## 🔧 常用命令

```bash
# 启动
cd ielts_tutor && source venv/bin/activate && python backend/server.py

# 停止
kill $(cat .pid)

# 查看日志
tail -f server.log

# 数据库查询
sqlite3 data/ielts_tutor.db "SELECT count(*) FROM sessions;"

# 隧道
cloudflared tunnel --url http://localhost:8767
```
