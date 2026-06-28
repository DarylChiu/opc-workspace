# 视频分析交互Workflow · 第一阶段归档报告

> **归档日期**: 2026-06-28  
> **版号**: v1.1.2  
> **分支**: main → GitHub: `git@github.com:DarylChiu/opc-workspace.git`  
> **目录**: `video_analyzer_app/`

---

## 1. Workflow 工作流

```
用户粘贴URL → 前端解析短链 → POST /api/transcribe → 后台线程启动
                                                    │
  ┌─────────────────────────────────────────────────┘
  ▼
Step 1 · 下载视频 (process_video_url)
  ├─ 抖音: v.douyin.com → iesdouyin.com/share/video/{id}/
  │         → urllib抓页面 → 正则提取video_id → curl下载playwm流
  │         (Playwright 降级为 fallback)
  ├─ B站: you-get 默认格式下载（含音频自动合成）
  └─ 通用: yt-dlp bestvideo+bestaudio/best 兜底
  └─ 验证: ffprobe 检查视频流 + 音频流（无音频→跳过重新下载）
                                                    │
  ▼
Step 2 · 字幕/转写
  ├─ 优先: 内嵌字幕/VTT 解析
  ├─ 兜底: Gemini 原生视频转写 (transcribe_only)
  └─ 输出: [{ts, speaker, text}, ...]
                                                    │
  ▼
Step 3 · Gemini 视频分析 (gemini_video_analyze)
  ├─ ≤15MB: 完整视频发送
  ├─ ≤50MB: ffmpeg 压缩(不截断)后发送
  └─ >50MB: 关键帧模式(⚠️镜头分析降级)
  └─ 输出: {transcript, scenes, story, visuals, ...}
                                                    │
  ▼
Step 4 · DeepSeek 文本分析 (run_pipeline)
  ├─ 内容总览 (genre, synopsis, narrative_core)
  ├─ 脚本解析 (四幕结构, 张力评分, 情绪曲线)
  ├─ 镜头&声音 (镜头类型, 光线色彩, 声音设计)
  └─ 复刻模板 (Hook技巧, 话题切入, 爆款因素)
                                                    │
  ▼
Step 5 · 商业数据抓取 (fetch_commerce_data)
  ├─ B站: api.bilibili.com/x/web-interface/view (前端直连优先)
  ├─ 抖音: iesdouyin.com 页面正则提取 digg/comment/share/collect
  └─ YouTube: oembed + 页面正则提取
                                                    │
  ▼
前端渲染: 视频播放器 + 对白时间轴(滚动联动) + 5个分析Tab + 商业数据卡片
```

---

## 2. 后端架构

### server.py (976行)
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/health` | GET | 健康检查+版本 |
| `/api/transcribe` | POST | 提交分析任务 |
| `/api/task` | POST | 轮询任务进度 |
| `/api/analyze` | POST | 手动触发分析 |
| `/api/commerce` | POST | 商业数据抓取 |
| `/api/annotate` | POST | 标注修正 |
| `/api/stats` | GET | 运行统计 |
| `/api/runs` | GET | 历史运行列表 |
| `/api/export-html` | POST | 导出HTML报告 |
| `/video/{hash}.mp4` | GET | 视频文件服务 |

**关键函数**:
- `process_video_url(url)` → (transcript, video_url, local_path)
- `gemini_video_analyze(path)` → 视频理解结果
- `run_pipeline(transcript, gemini_output)` → 结构化分析
- `fetch_commerce_data(url)` → 商业数据
- `_run_transcribe(task_id, url)` → 后台线程主流程(带进度上报)

### prompts.py (283行)
- `GEMINI_VIDEO_ANALYSIS_V3` — Gemini 视频全量分析 prompt
- `GEMINI_TRANSCRIBE_ONLY` — Gemini 纯转写 prompt
- `PROMPTS` — DeepSeek 各维度分析 prompt 字典 (overview/script/cinematography/template)
- `format_transcript()` — 对白格式化工具

### 辅助模块
| 文件 | 功能 |
|------|------|
| `douyin_downloader.py` | 抖音V4轻量下载器 (urllib+curl, Playwright fallback) |
| `douyin_cookie_fetcher.py` | 抖音Cookie获取 |
| `analysis_log.py` | 运行日志记录/统计 |
| `report_exporter.py` | HTML/Markdown报告导出 |
| `VIDEO_DOWNLOAD_STRATEGY.md` | 下载策略文档 |
| `DESIGN_REFERENCE.md` | 设计参考 |

---

## 3. 前端 & 本地/公网访问

### 前端
- **文件**: `index.html` (1583行, 单文件SPA)
- **本地地址**: `http://localhost:8777` (固定)
- **启动命令**: `cd video_analyzer_app && python3 server.py`

### Ngrok 公网隧道
```bash
# 当前隧道
ngrok http 8777 --log=stdout
→ https://unwhispering-imani-digitately.ngrok-free.dev

# 隧道配置 (~/Library/Application Support/ngrok/ngrok.yml)
tunnels:
  bryson-app:        # ← 视频分析Workflow (端口8777)
    proto: http
    addr: 8777
  opc-dashboard:     # ← OPC控制台 (端口8765)
    proto: http
    addr: 8765

# 如 unwhispering 隧道被其他项目占用，重新映射：
# 方法1: ngrok http 8777                        → 自动分配新URL
# 方法2: ngrok http --domain=unwhispering-... 8777 → 使用固定域名(需付费)
# 方法3: ngrok tunnel start bryson-app           → 使用配置文件中的命名隧道
```

---

## 4. 版号演进 & 迭代记录

| 版号 | 日期 | 变更 |
|------|------|------|
| **v1.0.0** | 06-16 | MVP: 视频+对白+5Tab分析+素材库 |
| **v1.1.0** | 06-27 | Sidebar左置/顶栏精简/对白滚动条/进度条/Tab重构/商业数据 |
| **v1.1.1** | 06-28 | 视频无声修复/滚动条深色/进度条%显示/三平台商业数据 |
| **v1.1.2** | 06-28 | 抖音iesdouyin下载/V4下载器/小红书缩进bug/商业数据全面修复/B站下载简化 |

### 开发经验

**版号控制**:
- VERSION 文件 + index.html `APP_VERSION` + `/api/health` 三处同步
- 每次部署前 `python3 -c "import py_compile; py_compile.compile('server.py')"` 语法校验

**迭代沟通**:
- 需求用飞书消息提出，逐条回复修改方案
- 每轮修改后重启服务并验证端点
- 重大变更写入 `memory/YYYY-MM-DD.md` 日记 + `memory/active.md` 任务状态

**网页设计逻辑**:
- CSS flex 嵌套: 祖先链必须都有 `min-height:0` 才能让子元素 overflow 生效
- macOS 滚动条: `-webkit-appearance` 和 `color-scheme: dark` 缺一不可
- 跨域Commerce: 前端 fetch B站API (浏览器IP不限制) + 后端 urllib (越南IP受限时走 iesdouyin.com)

**常犯陷阱**:
- Python 缩进: `elif` 块内不能混入其他条件代码
- you-get B站: 默认格式自动合成音频，手动指定 `--format` 反而出错
- 字节对齐: 正则 `\s*` 比固定空格更可靠

---

## 5. 文件清单

```
video_analyzer_app/
├── index.html              # 前端 SPA (1583行)
├── server.py               # 后端服务 (976行)
├── prompts.py              # AI Prompt 模板 (283行)
├── douyin_downloader.py    # 抖音V4下载器 (175行)
├── douyin_cookie_fetcher.py # Cookie获取
├── analysis_log.py         # 日志系统
├── report_exporter.py      # 报告导出
├── run_10fps.py            # 10fps运行脚本
├── test_gemini_video.py    # Gemini测试
├── test_gpt4o_video.py     # GPT-4o测试
├── VERSION                 # 版号文件
├── VIDEO_DOWNLOAD_STRATEGY.md # 下载策略
├── DESIGN_REFERENCE.md     # 设计参考
├── .gitignore
├── videos/                 # 下载视频缓存
└── logs/                   # 运行日志
```

---

## 6. Git 同步

```bash
cd /Users/zhaoyuzhao/.openclaw/xiaofeng_workspace
git add video_analyzer_app/
git commit -m "v1.1.2: 视频分析交互Workflow第一阶段归档
- 抖音下载: V4轻量下载器(urllib+curl, 5秒完成)
- B站下载: 简化you-get默认格式(自动音频)
- 商业数据: 三平台全覆盖(修复缩进bug)
- 进度条: 百分比显示+客户端估算fallback
- 滚动条: color-scheme dark融入深色背景
- 视频无声: you-get音频流自动合成
- 对白模块: flex布局修复滚动链
- 版号: 1.0.0→1.1.2"
git push origin main
```
