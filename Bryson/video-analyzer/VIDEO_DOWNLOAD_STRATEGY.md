# 视频下载策略 · 视频分析交互Workflow

> 最后更新: 2026-06-24 11:30

## 决策树

```
输入 URL
  │
  ├─ 包含 b23.tv？
  │   └─ YES → 前端 resolveB23Url() 解析短链
  │           ├─ 成功 → 拿到完整 bilibili.com URL → 走 Bilibili 下载
  │           └─ 失败 → 直接传给后端尝试（you-get 可能直接处理）
  │
  ├─ 平台判定
  │   ├─ douyin.com / iesdouyin.com / v.douyin
  │   │   └─ Phase 1: Playwright + douyin_downloader.py（3次重试）
  │   │       Phase 2: yt-dlp 兜底
  │   │
  │   ├─ bilibili.com / b23.tv
  │   │   └─ Phase 1: you-get（3次重试，480p → 360p 降级）
  │   │       Phase 2: yt-dlp 兜底
  │   │
  │   └─ 其他（YouTube / 小红书 / 通用）
  │       └─ Phase 1: yt-dlp（单次，max 500MB）
  │
  └─ 下载后验证
      ├─ ffprobe 检查 codec_type=video
      │   └─ 无视频流 → 删除文件 → 下一 Phase
      └─ 保存到 videos/{url_hash}.mp4（持久化）
```

## 关键设计决策

### 1. B站：you-get 替代 yt-dlp

**根因**：yt-dlp 对 Bilibili 的 extractor 在 Python 3.14 下有 cookie 兼容 bug，且 B站 API 可能拦截境外 IP（HTTP 412）。

**方案**：`you-get` 可直接从境外下载 B站视频（无需 cookie，向下兼容 480p/360p）。

**备选**：如果 480p 质量不够（分析够用），后续可加 `--cookies` 参数支持高品质。

### 2. b23.tv 短链：前端浏览器解析

**根因**：b23.tv 是 Bilibili 短链服务，用 JS 客户端跳转。后端（境外 IP）调用其 API 返回 `{"code":-404}`——IP 级 geo-blocking。

**方案**：`index.html` 的 `resolveB23Url()` 函数在用户浏览器中运行（国内 IP），通过 fetch 调用 B站分享 API 获取完整 BV 号。

**流程**：
```
fetch('https://api.bilibili.com/x/share/channel/get?share_channel=COPY&share_id=XXXXX')
  → 浏览器国内IP → API返回 {bvid: "BVxxxxxx"} 
  → 拼接完整URL → 'https://www.bilibili.com/video/BVxxxxxx'
  → 发给后端 you-get 下载
```

### 3. 海外 IP 封锁的通用处理模式

| 现象 | 检测方式 | 解决方案 |
|------|----------|----------|
| API 返回 -404/-400（B站） | 前端 fetch B站API → 浏览器IP可用 | 前端解析 + 后端 you-get |
| HTTP 412（B站 yt-dlp） | yt-dlp stderr 含 "412" | 切换 you-get |
| 音频-only 文件（抖音） | ffprobe 检查无 video 流 | 删除 → 重试/换 downloader |
| 同名文件不覆盖 | URL hash 唯一文件名 | 始终覆盖保存 |

## 涉及文件

| 文件 | 负责 |
|------|------|
| `server.py:process_video_url()` | 后端下载调度（you-get / Playwright / yt-dlp） |
| `index.html:resolveB23Url()` | 前端 b23.tv 短链解析 |
| `index.html:analyzeFromUrl()` | 入口函数，短链解析后提交 |
| `douyin_downloader.py` | 抖音专用 Playwright 下载器 |

## 已知限制与修复记录

| 日期 | 问题 | 根因 | 修复 |
|------|------|------|------|
| 6/24 | b23.tv 短链无法解析 | yt-dlp 不识别 b23.tv 格式 | you-get 下载 + 前端 resolveB23Url 解析 |
| 6/24 | 脚本解析只到 02:59 | ffmpeg `-t 180` 硬编码截断大视频 | L1-L3 分级策略：按视频时长智能选择压缩/截断参数 |

## Gemini 视频输入分级策略 (L1-L3)

> 核心原则：每一级的参数选择必须考虑下游 Gemini 的输入承受力

| 级别 | 条件 | 处理 | 下游影响 |
|------|------|------|----------|
| **L1** | ≤15MB且≤3分钟 | 原始 base64 直发 | 质量最高、转写最全 |
| **L2** | 3-10分钟 | 480p CRF28，不截断 | 若压后≤25MB→完整视频 / >25MB→30帧关键帧 |
| **L3** | >10分钟 | 360p CRF32 + 10分钟截断 + 30帧 | 牺牲分辨率换时长覆盖，帧数翻倍 |

**设计依据：** L2 覆盖大多数短视频，480p 对画面分析足够；L3 确保不超 Gemini 限制

## 后续扩展

如遇到新的非大陆视频平台（小红书、快手等）：
1. 先测试 yt-dlp 是否支持该平台的 extractor
2. 若失败，检查是否为 geo-blocking → 使用对应平台专用下载工具
3. 短链问题 → 前端解析（浏览器IP），与 b23.tv 模式一致
