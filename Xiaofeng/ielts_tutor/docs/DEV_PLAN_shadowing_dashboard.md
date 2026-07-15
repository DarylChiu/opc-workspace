# 雅思陪练助手 v0.9.1 → v1.0 开发方案：跟读模块 + 训练数据库

> 制定人: Bryson | 日期: 2026-07-14 | 状态: 待 Daryl 通过
> 前置条件: 管线1 M2 P0 延时优化收尾（降至 3000ms 级）+ 今晚最终验收通过

---

## 0. 核心决策回顾

- **管线2（Qwen Omni）**: 🔴 冻结。它是管线1 的技术替代品，不产生新用户价值。存档"重启触发条件"（见附录A）。
- **方向**: 从"单次模考机"→"练习周期学习闭环"。
- **闭环**: 练习 → 评估 → 找弱点(To Improve) → 跟读巩固 → 再练习。

---

## 1. 现状盘点（已有地基，避免重复造轮子）

| 已有能力 | 位置 | 复用方式 |
|---------|------|---------|
| sessions/transcripts/evaluations/errors 四表 | `session_manager.py` | 直接扩展 |
| `get_weakness_profile()` 跨会话薄弱点统计 | `session_manager.py` | 数据库页数据源 |
| `get_history()` 历史+分数 join | `session_manager.py` | 趋势曲线数据源 |
| `save_evaluation()` 自动拆解 improvements→errors 表 | `session_manager.py` | 跟读队列数据源 |
| 本地 TTS (Kokoro/Piper) | `server.py tts_speak()` | 生成范音 |
| 本地 STT (faster-whisper) | `stt_streaming.py` | 跟读复述识别 |
| HTML 评估报告 | `report_generator.py` | 数据库页样式参考 |

**关键发现**: 数据库骨架已存在，本方案 60% 是"聚合视图 + 前端页面"，40% 是"跟读闭环新逻辑"。

---

## 2. 功能拆解（3 个模块）

### 模块 A：训练数据库页（Dashboard）
**目标**: 把散落的单次会话聚合成"练习周期"视图。

功能点:
1. **分数趋势曲线**: overall/fluency/vocabulary/grammar/pronunciation 随时间的折线图
2. **练习日历热力图**: 每日练习次数（GitHub 贡献图样式），驱动打卡习惯
3. **To Improve 累积清单**: 跨会话聚合的错误/待改进项，按频次排序，标记"待巩固/已巩固"
4. **周期统计卡**: 本周练习次数、累计时长、平均分变化、最高分
5. **会话历史列表**: 点击可查看单次报告（复用现有 report）

数据源: 主要复用 `get_history()` + `get_weakness_profile()`，新增聚合查询。

### 模块 B：跟读模块（Shadowing）— 核心新增
**目标**: 把 To Improve 内容用跟读法再巩固一遍。

单条跟读循环:
```
从数据库取一条 To Improve（正确版句子/表达）
  → TTS 播放范音（Kokoro，慢速 0.85x 可选）
  → 用户点击"跟读"→ 录音
  → STT 识别用户复述
  → 发音/相似度打分（见 §3 打分方案）
  → 反馈: ✅ 通过 / 🔁 再试一次
  → 通过后标记"已巩固"，回写数据库
```

每日复习流程:
- 完成单次口语训练 → 自动跳转数据库页 → "今日跟读复习"入口
- 取今日新增 + 历史未巩固的 To Improve，组成复习队列（建议每次 5-8 条，避免疲劳）
- 支持"间隔重复"（SRS）: 已巩固项隔 N 天再复现一次（P1，非首版必须）

### 模块 C：流程串联
- 口语训练结束 → 评估完成 → 前端自动跳转 `/dashboard`
- Dashboard 顶部醒目卡片: "今日有 6 条待巩固，开始跟读 →"

---

## 3. 发音打分方案（跟读模块的技术核心）

这是本项目最需要新建的能力（当前评估是 DeepSeek 纯文本判断，无真发音打分）。三档方案：

| 档位 | 方法 | 精度 | 成本 | 建议 |
|------|------|------|------|------|
| **L1 文本相似度** | STT 转文字 → 与目标句做词级对齐 (Levenshtein/WER) | 低（只判"读对词没"） | 免费，已有STT | ✅ **首版落地** |
| **L2 音素级对齐** | forced alignment (如 wav2vec2/MFA) → 音素准确率 | 中高 | 需装模型，本地可跑 | P1 增强 |
| **L3 商用API** | Azure Pronunciation Assessment | 高（音素+韵律+流利度） | 付费 | 仅当 demo 需要 |

**首版决策**: L1 起步（复述内容正确 + WER 阈值），配合"跟读次数"作为巩固信号。发音精度打分作为 P1 增强，避免首版被卡在音素对齐工程上（重蹈管线2覆辙）。

---

## 4. 数据库 Schema 变更

新增 2 张表（现有 4 表不动）:

```sql
-- 跟读复习项（从 errors/improvements 派生，带巩固状态）
CREATE TABLE review_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_session_id TEXT,           -- 来源会话
    target_text TEXT NOT NULL,        -- 正确版范句（跟读目标）
    context TEXT,                     -- 原错误/解释
    category TEXT,                    -- grammar/vocab/pronunciation
    status TEXT DEFAULT 'pending',    -- pending/consolidated
    review_count INTEGER DEFAULT 0,   -- 已跟读次数
    best_score REAL DEFAULT 0,        -- 最佳跟读得分
    created_at TEXT NOT NULL,
    last_reviewed_at TEXT,
    next_due_at TEXT                  -- SRS 下次到期（P1）
);

-- 跟读记录（每次跟读的明细，供分析）
CREATE TABLE shadow_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_item_id INTEGER NOT NULL,
    user_transcript TEXT,             -- STT 识别的用户复述
    score REAL,                       -- 本次得分
    wer REAL,                         -- 词错误率
    audio_ms INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (review_item_id) REFERENCES review_items(id)
);
```

配套方法（`session_manager.py`）:
- `enqueue_review_items(sid, improvements)` — 评估后把 To Improve 灌入 review_items
- `get_review_queue(limit=8)` — 取待巩固队列
- `record_shadow_attempt(item_id, transcript, score, wer)` — 记录跟读
- `mark_consolidated(item_id)` — 标记已巩固
- `get_progress_stats(days=30)` — 数据库页周期统计

---

## 5. 后端 API 设计

```
GET  /dashboard                        # Dashboard 页面
GET  /api/dashboard/stats?days=30      # 趋势/日历/周期统计
GET  /api/dashboard/reviews            # To Improve 累积清单
GET  /api/review/queue?limit=8         # 今日跟读队列
POST /api/review/{item_id}/tts         # 生成范音（复用 tts_speak）
WS   /ws/shadow/{item_id}              # 跟读会话: 收音频→STT→打分→反馈
POST /api/review/{item_id}/consolidate # 标记已巩固
```

跟读 WS 复用现有 `/ws/chat` 的音频采集 + STT 管线，只替换"对话"为"比对打分"。

---

## 6. 前端页面

- `frontend/dashboard.html` — 数据库页（Chart.js 折线 + 日历热力图 + 清单）
- `frontend/shadow.html` 或集成进 dashboard — 跟读交互（范音播放 + 录音 + 打分反馈）
- 训练页评估完成后 `window.location = '/dashboard'` 自动跳转

---

## 7. 里程碑与工时估算

| 里程碑 | 内容 | 估时 | 依赖 |
|--------|------|------|------|
| **M0 前置** | 管线1 P0 延时收尾 + 今晚验收 | — | Daryl |
| **M1 数据层** | 2 张新表 + 6 个方法 + 评估后自动灌 review_items | 0.5d | M0 |
| **M2 Dashboard** | stats/reviews API + dashboard.html（曲线+日历+清单） | 1d | M1 |
| **M3 跟读闭环** | shadow WS + L1 打分 + 范音 + 巩固回写 + shadow.html | 1.5d | M1 |
| **M4 串联+验收** | 训练→跳转→跟读全流程打通 + 联调 | 0.5d | M2,M3 |
| **P1 增强** | SRS 间隔重复 + L2 音素打分 | 待定 | M4后 |

**首版(M1-M4)预计 3.5 个工作日**，全本地模型，成本仍 ~$0（仅 DeepSeek 评估 token）。

---

## 8. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| L1 文本相似度打分太粗，用户觉得"没在评发音" | 体验落差 | 首版明确标注"内容准确度"，发音打分 P1；或先接 L2 |
| improvements 文本格式不规范，拆解出的 target_text 不干净 | 跟读目标句质量差 | 灌库时用 LLM 规范化成"可跟读的完整句" |
| 跟读疲劳（一次太多条） | 弃用 | 每次限 5-8 条，可"稍后再练" |
| 数据库页空数据（新用户/历史少） | 首屏尴尬 | 空状态引导文案 + 鼓励先做1次训练 |

---

## 附录A：管线2 重启触发条件（冻结存档）

满足**任一**条件才解冻管线2:
1. 管线1 延时经 P0 优化后仍 > 5000ms 且无法进一步压缩
2. 需要"旗舰级实时对话"做投资人 demo
3. 用户明确反馈"对话不够自然/像真人"成为主要痛点

冻结前已知问题: Voice 参数(Cherry不支持)、256KB frame 限制、buffer too small。
