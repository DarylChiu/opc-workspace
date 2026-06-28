"""
视频分析交互Workflow V3 — Gemini 原生视频一站式分析
架构: yt-dlp下载 → Gemini视频(转写+视觉) → DeepSeek文本分析
"""
import os, sys, json, urllib.request, urllib.parse, threading, uuid
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import time, base64, subprocess, shutil, tempfile

WORKSPACE = Path(__file__).parent
sys.path.insert(0, str(WORKSPACE))
from prompts import PROMPTS, format_transcript, GEMINI_VIDEO_ANALYSIS_V3
from analysis_log import log_run, annotate_run, stats_summary, query_runs
from report_exporter import generate_report, save_report, get_version

# 仅转写的轻量 prompt
GEMINI_TRANSCRIBE_ONLY = """请完整转写这段视频的全部对白和旁白。

要求：
1. 结合画面和音频，逐句转写，按时间顺序排列
2. 每行格式：MM:SS 说话者：对白内容
3. 听不清的标注 [听不清]
4. 直接输出转写文本，不要添加任何解释、markdown 格式或 JSON

示例：
00:00 男声：大家好欢迎来到我的频道
00:05 女声：今天我们来聊聊一个重要的话题
00:12 [听不清]
00:15 男声：没错就是这样"""

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE = "https://api.deepseek.com/v1/chat/completions"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_MODEL = "google/gemini-2.5-flash"


# ═══ DeepSeek API ═══
def call_deepseek(prompt: str, system: str = "你是专业的视频分析助手。严格按JSON格式输出，不要其他内容。", max_tokens: int = 3072) -> tuple:
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    payload = json.dumps({"model": "deepseek-chat",
        "messages": [{"role":"system","content":system},{"role":"user","content":prompt}],
        "temperature":0.3,"max_tokens":max_tokens}).encode()
    req = urllib.request.Request(DEEPSEEK_BASE, data=payload,
        headers={"Authorization":f"Bearer {DEEPSEEK_API_KEY}","Content-Type":"application/json"})
    resp = urllib.request.urlopen(req, timeout=120)
    data = json.loads(resp.read())
    content = data["choices"][0]["message"]["content"].strip()
    if content.startswith("```"): content = content.split("\n",1)[1]
    if content.endswith("```"): content = content[:-3]
    return content, data.get("usage",{})


def image_to_base64(path: str) -> str:
    with open(path,"rb") as f:
        return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"


# ═══════════════════════════════════════════
# V3 核心: Gemini 原生视频一站式分析
# ═══════════════════════════════════════════
def gemini_video_analyze(video_path: str, max_retries: int = 2, transcribe_only: bool = False) -> dict:
    """发送视频到 Gemini
    transcribe_only=True: 仅转写（快速，用于 process_video_url 兜底）
    transcribe_only=False: 完整分析（转写+场景+故事+视觉，用于 run_pipeline）
    """
    if not OPENROUTER_API_KEY:
        print("[GEMINI-V3] OPENROUTER_API_KEY not set"); return {}
    
    td = tempfile.mkdtemp(prefix="gv3_")
    try:
        # Step 1: 选择 prompt 和 token 限制
        if transcribe_only:
            prompt_text = GEMINI_TRANSCRIBE_ONLY
            token_limit = 4096
            # 转写模型列表：Gemini 优先，GPT-4o 兜底
            models_to_try = [GEMINI_MODEL, "openai/gpt-4o"]
            print(f"[GEMINI-V3] 模式: 仅转写")
        else:
            prompt_text = GEMINI_VIDEO_ANALYSIS_V3
            token_limit = 16384
            models_to_try = [GEMINI_MODEL]
        
        # Step 2: 准备视频
        # 当前阶段目标：保证脚本/叙事结构完整正确
        # 策略：只做必要压缩（降分辨率+码率），不截断时长
        original_mb = os.path.getsize(video_path) / (1024*1024)
        send_path = video_path
        
        if original_mb <= 15:
            # 小视频：直接发送
            print(f"[GEMINI-V3] 小视频({original_mb:.0f}MB) → 完整发送")
            with open(send_path, "rb") as f:
                video_b64 = base64.b64encode(f.read()).decode()
            content = [
                {"type": "text", "text": prompt_text},
                {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{video_b64}"}}
            ]
        else:
            # 大视频：压缩但不截断——叙事结构需要完整时长
            print(f"[GEMINI-V3] 大视频({original_mb:.0f}MB) → 压缩(不截断)")
            compressed = os.path.join(td, "compressed.mp4")
            r = subprocess.run(["ffmpeg","-y","-i",video_path,
                "-vf","scale=480:-2","-c:v","libx264","-crf","28",
                "-preset","medium",
                "-c:a","aac","-b:a","64k","-ac","1",
                "-movflags","+faststart",
                compressed], capture_output=True, text=True, timeout=180)
            if os.path.exists(compressed) and os.path.getsize(compressed) > 1024:
                send_path = compressed
                print(f"[GEMINI-V3] 压缩: {original_mb:.0f}MB → {os.path.getsize(compressed)/1024/1024:.1f}MB")
            
            if os.path.getsize(send_path)/(1024*1024) > 50:
                # 压缩后还是太大 → 关键帧模式（会牺牲镜头/BGM分析质量）
                print(f"[GEMINI-V3] 超限({os.path.getsize(send_path)/1024/1024:.0f}MB) → 关键帧(⚠️镜头分析降级)")
                probe = json.loads(subprocess.run(
                    ["ffprobe","-v","quiet","-print_format","json","-show_format",send_path],
                    capture_output=True, text=True, timeout=10).stdout)
                dur = float(probe.get("format",{}).get("duration", 60))
                num_frames = min(30, max(10, int(dur / 5)))
                step = dur / num_frames
                content = [{"type": "text", "text": prompt_text}]
                for i in range(num_frames):
                    t = min(i * step + step/2, dur - 0.5)
                    fpath = os.path.join(td, f"frame_{i:03d}.jpg")
                    subprocess.run(["ffmpeg","-y","-ss",str(t),"-i",send_path,
                        "-vframes","1","-q:v","2","-vf","scale=720:-2",fpath],
                        capture_output=True, text=True, timeout=10)
                    if os.path.exists(fpath) and os.path.getsize(fpath) > 1024:
                        content.append({"type": "image_url", "image_url": {
                            "url": image_to_base64(fpath), "detail": "high"
                        }})
                print(f"[GEMINI-V3] 提取 {len(content)-1} 帧")
            else:
                with open(send_path, "rb") as f:
                    video_b64 = base64.b64encode(f.read()).decode()
                content = [
                    {"type": "text", "text": prompt_text},
                    {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{video_b64}"}}
                ]
        
        # Step 3: 发送请求 (带重试 + 模型切换)
        for model_idx, model_name in enumerate(models_to_try):
            if model_idx > 0:
                print(f"[GEMINI-V3] 切换模型: {model_name}")
                time.sleep(3)
            for retry in range(max_retries + 1):
                try:
                    if retry > 0:
                        wait = 3 * retry
                        print(f"[GEMINI-V3] 重试 {retry}/{max_retries} (等待{wait}s)...")
                        time.sleep(wait)
                    
                    print(f"[GEMINI-V3] 发送请求 ({model_name})...")
                    t0 = time.time()
                    payload = json.dumps({
                        "model": model_name,
                        "messages": [{"role": "user", "content": content}],
                        "temperature": 0.3,
                        "max_tokens": token_limit
                    }).encode()
                    req = urllib.request.Request(OPENROUTER_BASE, data=payload,
                        headers={"Authorization":f"Bearer {OPENROUTER_API_KEY}",
                                 "Content-Type":"application/json",
                                 "HTTP-Referer":"http://localhost:8777",
                                 "X-Title":"Video Analyzer V3"})
                    resp = urllib.request.urlopen(req, timeout=300)
                    data = json.loads(resp.read())
                    elapsed = time.time() - t0
                    usage = data.get("usage", {})
                    
                    if "choices" not in data or not data["choices"]:
                        err_msg = data.get("error", {}).get("message", str(data)[:300])
                        print(f"[GEMINI-V3] ⚠️  响应异常 ({model_name}): {err_msg}")
                        if retry < max_retries: continue
                        break  # try next model
                    
                    raw = data["choices"][0]["message"]["content"].strip()
                    if raw.startswith("```"): raw = raw.split("\n",1)[1]
                    if raw.endswith("```"): raw = raw[:-3]
                    
                    if transcribe_only:
                        # 纯文本模式：解析转写文本
                        transcript = parse_transcript_text(raw)
                        result = {"transcript": transcript, "_token_usage": usage, "_elapsed": elapsed}
                        print(f"[GEMINI-V3] ✅ {elapsed:.1f}s | {len(transcript)}条对白 | {usage.get('total_tokens','?')}t")
                    else:
                        # JSON 模式：完整分析
                        result = json.loads(raw)
                        result["_token_usage"] = usage
                        result["_elapsed"] = elapsed
                        t_count = len(result.get("transcript", []))
                        s_count = len(result.get("scenes", []))
                        print(f"[GEMINI-V3] ✅ {elapsed:.1f}s | {t_count}条对白 {s_count}个场景 | {usage.get('total_tokens','?')}t")
                    
                    return result
                    
                except urllib.error.HTTPError as e:
                    err = e.read().decode()[:500]
                    print(f"[GEMINI-V3] ⚠️  HTTP {e.code} ({model_name}): {err[:200]}")
                    if retry < max_retries: continue
                except json.JSONDecodeError as e:
                    print(f"[GEMINI-V3] ⚠️  JSON错误 ({model_name}): {e}")
                    if retry < max_retries: continue
                except Exception as e:
                    if retry < max_retries:
                        print(f"[GEMINI-V3] ⚠️  网络错误 ({model_name}): {e}")
                        continue
                    break  # try next model
        
        return {}
        
    finally:
        try: shutil.rmtree(td)
        except: pass


# ═══ 视频下载与处理 ═══
def process_video_url(url: str) -> tuple:
    """下载视频 + 提取字幕 + Gemini 转写兜底
    Returns (transcript_list, video_serving_url, video_local_path)
    """
    import hashlib
    od = Path(tempfile.mkdtemp(prefix="video_"))
    t, vu, vl = [], "", ""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    is_douyin = 'douyin.com' in url or 'iesdouyin.com' in url or 'v.douyin' in url
    is_bilibili = 'bilibili.com' in url or 'b23.tv' in url
    
    try:
        print(f"[VIDEO] {url}")
        
        # 两阶段下载: Playwright(Douyin) / you-get(Bilibili) → yt-dlp 兜底
        for phase in range(2):
            if phase > 0:
                is_douyin = False  # Phase 2: yt-dlp
                is_bilibili = False  # Phase 2: yt-dlp
                print(f"[VIDEO] Phase {phase}: 回退 yt-dlp")
            
            if is_douyin:
                print("[VIDEO] Douyin → Playwright 直链下载")
                douyin_dl = WORKSPACE / "douyin_downloader.py"
                if douyin_dl.exists():
                    temp_out = str(od / "video.mp4")
                    for retry in range(3):
                        if retry > 0: print(f"[VIDEO] Playwright 重试 {retry}/2..."); time.sleep(5)
                        r = subprocess.run([sys.executable, str(douyin_dl), url, temp_out],
                            capture_output=True, text=True, timeout=120, cwd=str(WORKSPACE))
                        if os.path.exists(temp_out) and os.path.getsize(temp_out) > 1024:
                            print(f"[VIDEO] Playwright: {os.path.getsize(temp_out)/1024/1024:.1f}MB")
                            break
                        print(f"[VIDEO] Playwright 尝试 {retry+1}: {(r.stderr or r.stdout or '')[:100]}")
                    else:
                        continue  # 3次失败 → 下一 phase
                else:
                    print("[VIDEO] douyin_downloader.py 缺失")
                    continue
            elif is_bilibili:
                print("[VIDEO] Bilibili → you-get 下载")
                # you-get 默认格式自动处理音频，无需手动合并
                r = subprocess.run(["you-get","-o",od,"-O","bili_video",url],
                    capture_output=True, text=True, timeout=120, cwd=str(od))
                # you-get 输出 bili_video.mp4 或 bili_video.flv
                for ext in ['.mp4', '.flv', '']:
                    cand = Path(str(od / "bili_video") + ext)
                    if cand.exists() and cand.stat().st_size > 1024:
                        print(f"[VIDEO] you-get: {cand.stat().st_size/1024/1024:.1f}MB ({cand.name})")
                        break
                else:
                    cand = None
                if not cand:
                    print("[VIDEO] you-get 未找到输出文件")
            else:
                r = subprocess.run(["yt-dlp","-o",str(od/"%(id)s.%(ext)s"),
                    "--no-playlist","--max-filesize","500M",
                    "-f","bestvideo+bestaudio/best",url],
                    capture_output=True, text=True, timeout=60)
            
            # 找下载文件
            vfs = [f for f in od.glob("*.*") if f.suffix.lower() in ('.mp4','.webm','.mkv','.mov')]
            if not vfs:
                if phase == 0: continue  # 尝试下一 phase
                print(f"[VIDEO] 所有下载方式均失败")
                return [], "", ""
            
            vf = vfs[0]
            print(f"[VIDEO] {vf.name} ({os.path.getsize(vf)/1024/1024:.1f}MB)")
            
            # 验证是否有视频流
            vcheck = subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
                "-show_entries","stream=codec_type","-of","csv=p=0", str(vf)],
                capture_output=True, text=True, timeout=10)
            if vcheck.stdout.strip() != "video":
                print(f"[VIDEO] ⚠️ 无视频流，尝试下一方式")
                os.remove(vf)
                continue  # 下一 phase
            
            # 验证音频流
            achek = subprocess.run(["ffprobe","-v","error","-select_streams","a:0",
                "-show_entries","stream=codec_type","-of","csv=p=0", str(vf)],
                capture_output=True, text=True, timeout=10)
            has_audio = (achek.stdout.strip() == "audio")
            if not has_audio:
                print(f"[VIDEO] ⚠️ 无音频流！尝试下一下载方式...")
                if phase == 0:
                    os.remove(vf)
                    continue  # 下一 phase
                else:
                    print(f"[VIDEO] 最终阶段仍无音频，视频将静音播放")
            
            # 保存到持久目录
            vd = WORKSPACE / "videos"; vd.mkdir(exist_ok=True)
            pp = vd / f"{url_hash}.mp4"
            shutil.copy2(vf, pp)
            vu = f"/video/{url_hash}.mp4"
            vl = str(pp)
            break  # 成功，跳出 phase 循环
        
        if not vl:
            return [], "", ""
        
        # vf 现在指向有效视频文件的临时路径
        
        # 尝试内嵌字幕
        probe = subprocess.run(["ffprobe","-v","quiet","-print_format","json",
            "-show_streams",str(vf)], capture_output=True, text=True, timeout=10)
        has_sub = False
        try:
            has_sub = any(s.get("codec_type")=="subtitle"
                         for s in json.loads(probe.stdout).get("streams",[]))
        except: pass
        
        if has_sub:
            subprocess.run(["ffmpeg","-i",str(vf),"-map","0:s:0","-f","webvtt",
                str(od/"sub.vtt")], capture_output=True, text=True, timeout=30)
            sf = od / "sub.vtt"
            if sf.exists(): t = parse_vtt(sf.read_text())
        
        # 尝试外部字幕
        if not t:
            subprocess.run(["yt-dlp","--skip-download","--write-subs","--write-auto-subs",
                "--sub-lang","zh-Hans,zh,en","--sub-format","vtt",
                "-o",str(od/"%(id)s"),url],
                capture_output=True, text=True, timeout=30)
            for sf in list(od.glob("*.vtt")) + list(od.glob("*.srt")):
                t = parse_vtt(sf.read_text())
                break
        
        # Gemini 原生视频转写兜底
        if not t and vl and os.path.exists(vl):
            print("[VIDEO] Gemini 原生视频转写...")
            try:
                r = gemini_video_analyze(vl, transcribe_only=True)
                if r and r.get("transcript"):
                    t = r["transcript"]
                    print(f"[VIDEO] Gemini 转写: {len(t)} 条")
            except Exception as e:
                print(f"[VIDEO] Gemini 转写失败: {e}")
        
        if not t:
            print("[VIDEO] 无可用字幕")
            return [], vu, vl
        
    except subprocess.TimeoutExpired:
        print("[VIDEO] 超时")
    except Exception as e:
        print(f"[VIDEO] 异常: {e}")
    finally:
        try: shutil.rmtree(od)
        except: pass
    return t, vu, vl


def parse_transcript_text(raw_text: str) -> list:
    """解析 Gemini 返回的纯文本转写为 transcript 格式"""
    import re
    items = []
    # 匹配 MM:SS speaker：text 或 MM:SS text
    pattern = r'^(\d{1,2}:\d{2})\s*(?:(.{1,6})：)?\s*(.+?)$'
    for line in raw_text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('```'):
            continue
        m = re.match(pattern, line)
        if m:
            ts = m.group(1)
            speaker = (m.group(2) or '').strip()
            text = m.group(3).strip()
            parts = ts.split(':')
            if len(parts) == 2:
                ts_fmt = f"{int(parts[0]):02d}:{int(parts[1]):02d}"
            else:
                ts_fmt = ts
            items.append({"ts": ts_fmt, "tag": "", "text": text, "speaker": speaker})
    if not items:
        for line in raw_text.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                items.append({"ts": "00:00", "tag": "", "text": line})
    seen = {}
    return [seen.setdefault(i["ts"], i) for i in items if i["ts"] not in seen]


def parse_vtt(text: str) -> list:
    """解析 WebVTT/SRT 为 transcript 格式"""
    import re
    items = []
    text = re.sub(r'^\ufeff','',text)
    text = re.sub(r'^WEBVTT.*\n','',text)
    ts_pat = r'(\d{2}:\d{2}(?::\d{2})?[.,]\d{3})'
    pat = ts_pat + r'\s*-->\s*' + ts_pat + r'\s*\n(.*?)(?=\n\n|\n\d+\n|\Z)'
    for st, et, ct in re.findall(pat, text, re.DOTALL):
        parts = st.split(':')
        ts_s = int(parts[0])*3600+int(parts[1])*60+int(float(parts[-1].replace(',','.'))) if len(parts)==3 else int(parts[0])*60+int(float(parts[1].replace(',','.')))
        ts = f"{int(ts_s//60):02d}:{int(ts_s%60):02d}"
        clean = re.sub(r'<[^>]+>','',ct).strip().replace('\n',' ')
        if clean: items.append({"ts":ts,"tag":"","text":clean})
    seen = {}
    return [seen.setdefault(i["ts"],i) for i in items if i["ts"] not in seen]


# ═══ 商业数据抓取 ═══
def fetch_commerce_data(url: str) -> dict:
    """从视频 URL 抓取播放/点赞/收藏/转发等商业数据"""
    result = {}
    
    # Bilibili
    if 'bilibili.com' in url or 'b23.tv' in url:
        try:
            import re
            bv_match = re.search(r'BV[a-zA-Z0-9]{10}', url)
            av_match = re.search(r'av(\d+)', url)
            if bv_match:
                vid = bv_match.group(0)
            elif av_match:
                vid = av_match.group(1)
            else:
                try:
                    req = urllib.request.Request(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Referer': 'https://www.bilibili.com/'
                    })
                    html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
                    bv_match = re.search(r'BV[a-zA-Z0-9]{10}', html)
                    av_match = re.search(r'av(\d+)', html)
                    if bv_match: vid = bv_match.group(0)
                    elif av_match: vid = av_match.group(1)
                except: pass
            
            if vid:
                stat_url = (f'https://api.bilibili.com/x/web-interface/view?bvid={vid}'
                    if (isinstance(vid, str) and vid.startswith('BV'))
                    else f'https://api.bilibili.com/x/web-interface/view?aid={vid}')
                req = urllib.request.Request(stat_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Referer': 'https://www.bilibili.com/'
                })
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read())
                if data.get('code') == 0 and data.get('data'):
                    stat = data['data'].get('stat', {})
                    result = {
                        'views': format_count(stat.get('view', 0)),
                        'likes': format_count(stat.get('like', 0)),
                        'saves': format_count(stat.get('favorite', 0)),
                        'shares': format_count(stat.get('share', 0)),
                        'comments': format_count(stat.get('reply', 0)),
                        'source': 'bilibili_api'
                    }
                    print(f'[COMMERCE] B站: {result["views"]}播放 {result["likes"]}赞')
        except Exception as e:
            print(f'[COMMERCE] B站失败: {e}')
    
    # YouTube
    elif 'youtube.com' in url or 'youtu.be' in url:
        try:
            import re
            vid_match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
            if vid_match:
                vid = vid_match.group(1)
                oembed_url = f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json'
                req = urllib.request.Request(oembed_url)
                resp = urllib.request.urlopen(req, timeout=10)
                oembed = json.loads(resp.read())
                result['title'] = oembed.get('title', '')
                result['author'] = oembed.get('author_name', '')
                result['source'] = 'youtube_oembed'
                try:
                    page_url = f'https://www.youtube.com/watch?v={vid}'
                    req = urllib.request.Request(page_url, headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    })
                    html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
                    views_match = re.search(r'"viewCount":\s*"(\d+)"', html)
                    if views_match:
                        result['views'] = format_count(int(views_match.group(1)))
                    likes_match = re.search(r'"likeCount":\s*"(\d+)"', html)
                    if likes_match:
                        result['likes'] = format_count(int(likes_match.group(1)))
                except Exception as e:
                    print(f'[COMMERCE] YT页面: {e}')
        except Exception as e:
            print(f'[COMMERCE] YT失败: {e}')
    
    # 抖音
    elif 'douyin.com' in url or 'iesdouyin.com' in url:
        try:
            import re
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'
            })
            html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
            
            # 匹配多种格式: "digg_count": 551 或 digg_count: 551
            likes = re.search(r'["\']?digg_count["\']?\s*:\s*(\d+)', html)
            comments = re.search(r'["\']?comment_count["\']?\s*:\s*(\d+)', html)
            shares = re.search(r'["\']?share_count["\']?\s*:\s*(\d+)', html)
            saves = re.search(r'["\']?collect_count["\']?\s*:\s*(\d+)', html)
            views = re.search(r'["\']?play_count["\']?\s*:\s*(\d+)', html)
            
            if likes or comments or saves:
                result = {'source': 'douyin_page'}
                if views and int(views.group(1)) > 0:
                    result['views'] = format_count(int(views.group(1)))
                if likes: result['likes'] = format_count(int(likes.group(1)))
                if comments: result['comments'] = format_count(int(comments.group(1)))
                if shares: result['shares'] = format_count(int(shares.group(1)))
                if saves: result['saves'] = format_count(int(saves.group(1)))
                print(f'[COMMERCE] 抖音: 赞{result.get("likes","?")} 评{result.get("comments","?")} 藏{result.get("saves","?")}')
            else:
                result = {'source': 'douyin_limited', 'note': '页面未提取到互动数据'}
        except Exception as e:
            print(f'[COMMERCE] 抖音失败: {e}')
            result = {'source': 'douyin_limited', 'note': f'错误: {str(e)[:50]}'}
    
    # 小红书
    elif 'xiaohongshu.com' in url or 'xhslink.com' in url:
        result = {'source': 'xhs_limited', 'note': '小红书需登录认证'}
    
    return result


def format_count(n: int) -> str:
    if n >= 100000000: return f'{n/100000000:.1f}亿'
    if n >= 10000: return f'{n/10000:.1f}万'
    return str(n)


# ═══════════════════════════════════════════
# V3 管线: DeepSeek 文本分析
# 输入: transcript + Gemini 视频分析结果
# ═══════════════════════════════════════════
def run_pipeline(transcript: list, video_path: str = None,
                 video_meta: dict = None, gemini_raw: dict = None) -> tuple:
    """V3 简化管线: Gemini 已负责视频理解，DeepSeek 仅做结构化文本分析"""
    video_meta = video_meta or {}
    ttext = format_transcript(transcript)
    results = {}
    tstats = {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0,
              "cost_usd":0.0,"per_call":[]}
    
    # 费率常量
    DS_PROMPT = 0.14   # Deepseek-chat: $0.14/1M prompt
    DS_COMPLETION = 0.28  # Deepseek-chat: $0.28/1M completion
    GM_PROMPT = 0.30   # Gemini 2.5 Flash via OpenRouter: $0.30/1M prompt
    GM_COMPLETION = 2.50  # Gemini 2.5 Flash via OpenRouter: $2.50/1M completion
    
    def _add(name, pt, ct, tt):
        if name.startswith("gemini"):
            cost = (pt * GM_PROMPT + ct * GM_COMPLETION) / 1_000_000
        else:
            cost = (pt * DS_PROMPT + ct * DS_COMPLETION) / 1_000_000
        for k,v in [("prompt_tokens",pt),("completion_tokens",ct),("total_tokens",tt)]:
            tstats[k] += v
        tstats["cost_usd"] += cost
        tstats["per_call"].append({"name":name,"prompt_tokens":pt,
            "completion_tokens":ct,"total_tokens":tt,"cost_usd":round(cost,6)})
    
    # Step 0: 如果有视频路径但没有 Gemini 分析，先跑 Gemini
    gm = gemini_raw or {}
    has_gemini = bool(gm.get("story") or gm.get("scenes"))
    
    use_gemini = has_gemini or (video_path and os.path.exists(video_path))
    
    if video_path and os.path.exists(video_path) and not has_gemini:
        print("[PIPELINE] 运行 Gemini 视频分析...")
        gm = gemini_video_analyze(video_path)
        if gm and gm.get("_token_usage"):
            pt = gm["_token_usage"].get("prompt_tokens", 0)
            ct = gm["_token_usage"].get("completion_tokens", 0)
            _add("gemini_video", pt, ct, pt+ct)
    
    # 追踪已有 Gemini 分析的 token（来自 _run_transcribe step 2 或 /api/analyze 传入）
    if has_gemini:
        if gm.get("_token_usage"):
            pt = gm["_token_usage"].get("prompt_tokens", 0)
            ct = gm["_token_usage"].get("completion_tokens", 0)
            _add("gemini_video", pt, ct, pt + ct)
        if gm.get("_transcribe_tokens"):
            pt = gm["_transcribe_tokens"].get("prompt_tokens", 0)
            ct = gm["_transcribe_tokens"].get("completion_tokens", 0)
            _add("gemini_transcribe", pt, ct, pt + ct)
    
    if gm:
        results["gemini_analysis"] = {k:v for k,v in gm.items()
                                      if not k.startswith("_")}
        if gm.get("visionStyle"):
            results["vision"] = gm["visualStyle"]
        if gm.get("story"):
            results["story"] = gm["story"]
    
    # 构建 DeepSeek 分析的上下文
    story_json = json.dumps(gm.get("story", {}), ensure_ascii=False)
    scenes_json = json.dumps(gm.get("scenes", []), ensure_ascii=False)[:3000]
    visual_style_json = json.dumps(gm.get("visualStyle", {}), ensure_ascii=False)
    
    # 分析任务列表
    tasks = [
        ("overview", PROMPTS["overview"], 2048, {"story_json": story_json, "transcript": ttext}),
        ("script_analysis", PROMPTS["script_analysis"], 4096,
         {"story_json": story_json, "scenes_json": scenes_json, "transcript": ttext}),
        ("template", PROMPTS["template"], 3072,
         {"story_json": story_json, "scenes_json": scenes_json, "transcript": ttext}),
    ]
    
    if gm.get("visualStyle"):
        tasks.append(("cinematography", PROMPTS["cinematography"], 3072,
            {"story_json": story_json, "visual_style_json": visual_style_json, "transcript": ttext}))
    
    tasks.append(("scoring", PROMPTS["scoring"], 2048,
        {"story_json": story_json, "scenes_json": scenes_json, "transcript": ttext}))
    
    for name, ptpl, mt, kw in tasks:
        try:
            prompt = ptpl.format(**kw)
            raw, usage = call_deepseek(prompt, max_tokens=mt)
            try:
                results[name] = json.loads(raw)
            except json.JSONDecodeError:
                print(f"[WARN] {name} JSON parse failed, raw: {raw[:200]}...")
                results[name] = None
            _add(name, usage.get("prompt_tokens",0),
                 usage.get("completion_tokens",0),
                 usage.get("total_tokens",0))
            print(f"  [{name}] {usage.get('total_tokens',0)}t")
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            results[name] = None
    
    # 如果没有 Gemini visualStyle，添加免责声明
    if not gm.get("visualStyle"):
        results["cinematography"] = results.get("cinematography", {
            "cinematography": {"shotTypes":"","composition":"","cameraMovement":""},
            "lightingColor": {"lightingMood":"","colorPalette":"","visualRhythm":""},
            "soundDesign": {"bgm":"","ambient":"","dialogueStyle":""},
            "directorStyle": {"aesthetic":"","narrativeSignature":"","culturalEncoding":""},
            "disclaimer": "⚠️ 基于对白文本推断，未使用 Gemini 视觉分析。"
        })
    
    return results, tstats


# ═══ 异步任务系统 ═══
_pending_tasks: dict = {}

def _run_transcribe(task_id: str, url: str):
    """V3 后台线程: 下载 → Gemini 视频分析 → DeepSeek 文本分析 → 全部产出"""
    task_start = time.time()
    def _progress(pct, stage):
        _pending_tasks[task_id] = {"status": "processing", "_start": task_start,
                                   "stage": stage, "progress": pct}
    
    try:
        # Step 1: 下载视频 + 字幕提取
        _progress(5, "📥 下载视频...")
        t, vu, vl = process_video_url(url)
        # V3: 即使没有字幕，只要视频下载成功就用 Gemini 转写
        _transcribe_usage = None
        if not t and vl and os.path.exists(vl):
            print(f"[TASK] 无字幕，尝试 Gemini 转写...")
            _progress(15, "🎙️ Gemini 转写...")
            try:
                gm = gemini_video_analyze(vl, transcribe_only=True)
                if gm and gm.get("_token_usage"):
                    _transcribe_usage = gm["_token_usage"]
                if gm and gm.get("transcript"):
                    t = gm["transcript"]
                    print(f"[TASK] Gemini 转写成功: {len(t)} 条")
                else:
                    # Gemini 也失败了，仍然继续——没有对白但有视觉分析
                    print(f"[TASK] Gemini 转写也失败，使用空对白继续")
                    t = t or []
            except Exception as e:
                print(f"[TASK] Gemini 异常: {e}")
                t = t or []
        
        if not t and not vl:
            _pending_tasks[task_id] = {
                "status": "error",
                "error": "视频下载失败，请检查链接是否有效"
            }
            return
        
        _progress(25, "🔍 Gemini 视频分析...")
        
        # Step 2: Gemini 原生视频一站式分析
        gemini_data = {}
        has_gemini = vl and os.path.exists(vl)
        if has_gemini:
            try:
                gemini_data = gemini_video_analyze(vl)
                _progress(50, "🔍 Gemini 完成")
                # 如果 Gemini 转录质量更好，使用 Gemini 的 transcript
                if gemini_data.get("transcript") and len(gemini_data.get("transcript",[])) >= len(t):
                    t = gemini_data["transcript"]
                    print(f"[TASK] 使用 Gemini 转写: {len(t)} 条")
            except Exception as e:
                print(f"[TASK] Gemini 分析失败: {e}")
        
        _progress(60, "🧠 DeepSeek 文本分析...")
        
        # Step 3: DeepSeek 文本分析
        video_meta = {"path": vl, "filename": vl.split("/")[-1] if vl else "",
                      "source": "url"}
        # 合并转写 token 到 gemini_data，以便 run_pipeline 统一追踪
        if _transcribe_usage:
            gemini_data["_transcribe_tokens"] = _transcribe_usage
        
        t1 = time.time()
        analysis, stats = run_pipeline(t, video_path=vl if vl else None,
                                       video_meta=video_meta, gemini_raw=gemini_data)
        _progress(95, "📊 生成报告...")
        el_ms = (time.time() - t1) * 1000
        # 加上 Gemini 耗时
        t_start = _pending_tasks[task_id].get("_start", t1)
        total_el = round((time.time() - t_start), 1)
        stats["elapsed"] = total_el
        run_id = log_run(video_meta, analysis, stats, el_ms)
        
        _pending_tasks[task_id] = {
            "status": "done",
            "progress": 100,
            "stage": "✅ 完成",
            "result": {
                "transcript": t,
                "video_url": vu,
                "video_path": vl,
                "analysis": analysis,
                "token_stats": stats,
                "run_id": run_id
            }
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        _pending_tasks[task_id] = {"status": "error", "error": str(e)}


# ═══ HTTP Server ═══
class APIHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/transcribe":
            try:
                body = json.loads(self.rfile.read(
                    int(self.headers.get("Content-Length", 0))))
                url = body.get("url", "")
                if not url:
                    self._json({"error": "缺少url"}, 400); return
                print(f"[TRANSCRIBE] 启动: {url}")
                task_id = str(uuid.uuid4())[:8]
                _pending_tasks[task_id] = {"status": "processing", "_start": time.time(),
                    "stage": "⏳ 排队...", "progress": 0}
                threading.Thread(target=_run_transcribe,
                    args=(task_id, url), daemon=True).start()
                self._json({"task_id": task_id, "status": "processing"})
            except Exception as e:
                import traceback; traceback.print_exc()
                self._json({"error": str(e)}, 500)
        
        elif self.path == "/api/task":
            try:
                body = json.loads(self.rfile.read(
                    int(self.headers.get("Content-Length", 0))))
                task_id = body.get("task_id", "")
                task = _pending_tasks.get(task_id)
                if not task:
                    self._json({"status": "not_found",
                               "message": "任务不存在或已过期"})
                else:
                    self._json(task)
            except Exception as e:
                self._json({"error": str(e)}, 500)
        
        elif self.path == "/api/analyze":
            try:
                body = json.loads(self.rfile.read(
                    int(self.headers.get("Content-Length", 0))))
                t = body.get("transcript", [])
                vp = body.get("video_path", "")
                gm = body.get("gemini_analysis", None)
                if not t:
                    self._json({"error": "缺少transcript",
                               "transcript": [], "analysis": {}}, 400)
                    return
                print(f"[ANALYZE] {len(t)}条, video={'yes' if vp else 'no'}, "
                      f"gemini={'yes' if gm else 'no'}")
                t0 = time.time()
                video_meta = {
                    "path": vp or "",
                    "filename": body.get("filename", ""),
                    "duration": body.get("duration", 0),
                    "label": body.get("label", ""),
                    "source": body.get("source", "local"),
                }
                analysis, stats = run_pipeline(
                    t, video_path=vp if vp else None,
                    video_meta=video_meta, gemini_raw=gm)
                el_ms = (time.time()-t0)*1000
                run_id = log_run(video_meta, analysis, stats, el_ms)
                print(f"[ANALYZE] {el_ms/1000:.1f}s | "
                      f"{stats['total_tokens']}t | ${stats['cost_usd']:.5f}")
                self._json({
                    "transcript": t,
                    "analysis": analysis,
                    "video_url": body.get("video_url", ""),
                    "token_stats": stats,
                    "elapsed": round(el_ms/1000, 1),
                    "run_id": run_id
                })
            except Exception as e:
                import traceback; traceback.print_exc()
                print(f"[API ERROR] {e}")
                self._json({"error": str(e),
                           "transcript": [], "analysis": {}}, 500)
        
        elif self.path == "/api/annotate":
            try:
                body = json.loads(self.rfile.read(
                    int(self.headers.get("Content-Length", 0))))
                run_id = body.get("run_id", "")
                notes = body.get("notes", "")
                tags = body.get("tags", [])
                annotate_run(run_id, notes, tags)
                self._json({"status": "ok"})
            except Exception as e:
                self._json({"error": str(e)}, 500)
        
        elif self.path == "/api/stats":
            self._json(stats_summary())
        
        elif self.path == "/api/export-html":
            try:
                body = json.loads(self.rfile.read(
                    int(self.headers.get("Content-Length", 0))))
                video_meta = body.get("video_meta", {})
                transcript = body.get("transcript", [])
                analysis = body.get("analysis", {})
                token_stats = body.get("token_stats", {})
                marks = body.get("marks", [])
                run_id = body.get("run_id", "")
                video_url = body.get("video_url", "")
                
                html = generate_report(video_meta, transcript, analysis,
                                       token_stats, marks, run_id, video_url)
                report_path = save_report(html, video_meta, run_id)
                
                self._json({"status": "ok", "html": html,
                           "saved_to": report_path,
                           "version": get_version()})
            except Exception as e:
                import traceback; traceback.print_exc()
                self._json({"error": str(e)}, 500)
        
        elif self.path == "/api/commerce":
            try:
                body = json.loads(self.rfile.read(
                    int(self.headers.get("Content-Length", 0))))
                url = body.get("url", "")
                commerce = fetch_commerce_data(url)
                self._json({"commerce": commerce})
            except Exception as e:
                self._json({"error": str(e), "commerce": {}}, 200)
        
        elif self.path == "/api/runs":
            try:
                body = json.loads(self.rfile.read(
                    int(self.headers.get("Content-Length", 0))))
                q = body.get("q", "")
                limit = body.get("limit", 20)
                self._json(query_runs(q, limit))
            except:
                self._json(query_runs("", 20))
        else:
            self._json({"error": "not found"}, 404)
    
    def do_GET(self):
        # 视频文件服务
        if self.path.startswith("/video/"):
            vp = WORKSPACE / "videos" / self.path[7:]
            if vp.exists() and vp.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Length", str(vp.stat().st_size))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(vp, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._json({"error": "video not found"}, 404)
            return
        
        # API
        if self.path == "/api/health":
            self._json({
                "status": "ok", "version": get_version(), "app_version": "V3-gemini-native",
                "model": "deepseek-chat",
                "has_deepseek": bool(DEEPSEEK_API_KEY),
                "vision_model": GEMINI_MODEL,
                "has_openrouter": bool(OPENROUTER_API_KEY),
                "log_runs": len(query_runs("", 1))
            })
            return
        if self.path == "/api/stats":
            self._json(stats_summary())
            return
        if self.path == "/api/runs":
            self._json(query_runs("", 20))
            return
        
        return super().do_GET()
    
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def log_message(self, format, *args):
        if "/api/" in str(args):
            print(f"[HTTP] {args[0]}")


def main():
    port = 8777
    if not DEEPSEEK_API_KEY:
        print("⚠️  DEEPSEEK_API_KEY 未设置！分析功能将不可用")
        print("   设置方式: export DEEPSEEK_API_KEY=xxx")
    else:
        print(f"✅ DeepSeek API Key: {DEEPSEEK_API_KEY[:12]}...")
    print(f"✅ OpenRouter: {OPENROUTER_API_KEY[:12]}..." if OPENROUTER_API_KEY
          else "⚠️ OPENROUTER_API_KEY missing")
    
    os.chdir(str(WORKSPACE))
    server = HTTPServer(("127.0.0.1", port), APIHandler)
    print(f"🚀 视频分析服务 V3: http://localhost:{port}")
    print(f"   POST /api/transcribe | /api/task | /api/analyze")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")


if __name__ == "__main__":
    main()
