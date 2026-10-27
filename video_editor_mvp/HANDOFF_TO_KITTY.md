# 🔴 视频自动化剪辑MVP Phase1 前端 — Debug Handoff

> 来自: Bryson (xiaofeng)
> 交予: Kitty
> 日期: 2026-07-23 14:30
> 优先级: P0 — Daryl 无法验收

---

## 背景

Daryl 要求今天完成「视频自动化剪辑MVP · Phase1 极简可视化前端」。开发了单文件前端 + Python API Server，但提测后 Bug 太多，Daryl 花了 1-2 小时反馈 Bug 后仍无法验收。

**Daryl 原话:** "根本用不了，算了，你把今天整个项目的内容都发给Kitty让她来做Debuger，太多Bug了"

---

## 项目文件

**根目录:** `/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/video_editor_mvp/`

```
├── frontend/
│   └── index.html          # 单文件应用 (~1400行, vanilla JS, OPC DS v1.0)
├── api_server.py            # Python HTTP Server + REST API (port 8768)
├── FRONTEND_DESIGN.md       # v2.0 设计方案 (5节点详细交互设计)
├── TEST_REPORT.md           # 测试报告 (7个Bug修复记录)
├── PHASE0_WORKFLOW.md       # Phase 0 工作流程图
├── CLIP_RULES.md            # 剪辑核心规则
├── .env                     # API Keys (OPENROUTER_API_KEY)
├── bgm_full.wav             # BGM 测试文件
├── data/                    # 数据库 + 缓存
├── output/                  # 渲染产物
└── server.log / cf.log      # 服务日志
```

---

## 启动方式

```bash
cd /Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/video_editor_mvp
python3 api_server.py --port 8768
# → http://localhost:8768
```

---

## 架构概览

### 前端: 5 步 Pipeline
```
0.2 SCAN → 0.4 BGM → 0.5 ASR → 0.6 Emotion → 0.7 Matcher
```
每步有独立的 render 函数渲染可视化。步骤间通过 STATE 对象共享数据。

### 前端 API 调用流
```
render(step) 
  → showLoading("分析中...") 
  → loadXxx() (如 loadBGM)
    → bgTask(endpoint, body, timeout) 
      → POST /api/xxx 
      → 轮询 GET /api/task/{id} (每1.5s)
  → 更新 STATE 
  → 渲染结果
```

### 后端端点
| 端点 | 方法 | 说明 | 耗时 |
|------|------|------|:---:|
| `/api/health` | GET | 健康检查 | <1ms |
| `/api/scan/groups?date=20260430` | GET | 素材扫描 | <1s |
| `/api/bgm/library` | GET | 歌曲库 | <1ms |
| `/api/bgm/analyze` | POST → poll task | librosa BPM+能量+分段 | 4s |
| `/api/video/asr` | POST → poll task | Whisper 转写+场景检测 | 15-30s |
| `/api/video/emotion` | POST → poll task | Gemini 2.5 Flash L3分析 | 10s/片段 |
| `/api/edit/create` | POST | 匹配编排(即时) | <0.1s |
| `/api/task/{id}` | GET | 轮询 task 结果 | <1ms |

---

## 🔴 已知 Bug 详细清单

### Bug 1 · `[object Promise]` — 阻断级 🔴
**症状:** 打开页面后 0.2 素材扫描区域显示 `[object Promise]`，整个页面不可用
**根因:** `renderScan()` 改为 async 后返回 Promise 对象，但 `render()` 中直接 `main.innerHTML = renderScan()` 没有 await
**修复:** 加了两处：`main.innerHTML = await renderScan()` 和 `async function navigateTo()`
**状态:** 代码已修，但 Daryl 没验证到（因为 Tunnel 也坏了）
**验证:** 打开 localhost:8768，0.2 页正常显示 11 个素材缩略图

### Bug 2 · Cloudflare Tunnel ERR 1033 — 阻断级 🔴
**症状:** Daryl 打不开公网地址，显示 "Error 1033 Cloudflare Tunnel error"
**根因:** cloudflared 免费隧道不稳定，TLS 握手后无法连接 origin
**修复:** 换 localtunnel 或直接用 localhost
```bash
# localtunnel 替代方案:
npm i -g localtunnel
lt --port 8768 --subdomain video-editor-phase1
```

### Bug 3 · Gemini L3 不生效 — 已修 🟡
**根因:** 两个子问题:
  a. 请求格式用了 Gemini 原生 `{"inline_data": {"mime_type": "image/jpeg", "data": b64}}`，OpenRouter 需要 OpenAI 兼容格式 `{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}`
  b. 模型名 `google/gemini-2.0-flash-001` 在 OpenRouter 返回 404，应改为 `google/gemini-2.5-flash`
**状态:** 已修复

### Bug 4 · .env 缺失 — 已修 🟡
**根因:** video_editor_mvp 目录无 .env，Gemini API 调用静默失败，回落为亮度/颜色分析
**状态:** 已创建 .env

### Bug 5 · 素材时长不准 — 已修 🟡
**根因:** 文件大小估算 15MB/s，实际 Insta360 ~0.55MB/s
**修复:** 4月30日文件改用 ffprobe 精确时长
**状态:** 已修复

### Bug 6 · Mock clip 时间越界 — 已修 🟡
**根因:** 121.mp4 实际 78s，但 mock 数据中 clip 引用了 80-122s
**状态:** 已修正为 0-10/10-30/30-50/50-78

### Bug 7 · 无加载进度 — 部分修 🟢
**根因:** bgTask 轮询循环无进度反馈
**状态:** 已添加百分比+耗时显示，但可能还有改进空间

---

## ⚡ 建议修复优先级

1. **先修 #1 `[object Promise]`** → 打开 localhost:8768 确认修好了
2. **修复 #2 Tunnel** → 换 localtunnel 或直接让 Daryl 用 localhost:8768
3. **跑通全流程** → 本地打开页面，0.2→0.4→0.5→0.6→0.7 全部走一遍
4. **Emotion 降级** → Gemini 调用慢(10s/片段)+花钱，验收时可先用 mock 数据确保 UI 流畅
5. **ASR 优化** → 风景视频人声极少，自动检测并跳过，显示「无可识别对白」

---

## Daryl 的期望

1. 打开就能看到东西，不要有任何加载错误
2. 5 个步骤全部走通，数据准确
3. 交互逻辑符合设计文档 FRONTEND_DESIGN.md 的描述
4. 提测前必须先自己跑一遍完整流程
