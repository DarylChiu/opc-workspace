"""
视频分析交互Workflow 服务端（纯 stdlib，无外部依赖）
- 静态文件服务
- /api/analyze → DeepSeek V4 Pro 文本分析
- 融合 MVP 深度分析架构：脚本解析 + 镜头语言&声音
"""
import os, sys, json, urllib.request, urllib.parse
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import time

WORKSPACE = Path(__file__).parent
sys.path.insert(0, str(WORKSPACE))
from prompts import PROMPTS, format_transcript

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE = "https://api.deepseek.com/v1/chat/completions"


def call_deepseek(prompt: str, system: str = "你是专业的视频分析助手。严格按JSON格式输出，不要其他内容。", max_tokens: int = 3072) -> tuple:
    """调用 DeepSeek V4 Pro，返回 (content, usage_dict)"""
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens
    }).encode()
    
    req = urllib.request.Request(
        DEEPSEEK_BASE,
        data=payload,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
    )
    
    resp = urllib.request.urlopen(req, timeout=120)
    data = json.loads(resp.read())
    content = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    
    # 清理 markdown 包裹
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
    return content, usage


def process_video_url(url: str) -> tuple:
    """下载视频并提取转写文本，返回 (transcript, video_serving_url)"""
    import subprocess, tempfile, shutil
    
    output_dir = Path(tempfile.mkdtemp(prefix="video_analyze_"))
    transcript = []
    video_serving_url = ""
    
    try:
        # Step 1: 下载视频
        print(f"[VIDEO] 下载中: {url}")
        result = subprocess.run(
            ["yt-dlp", "-o", str(output_dir / "%(id)s.%(ext)s"),
             "--no-playlist", "--max-filesize", "500M", url],
            capture_output=True, text=True, timeout=30
        )
        
        video_files = list(output_dir.glob("*.*"))
        if not video_files:
            print(f"[VIDEO] 下载失败: {result.stderr[:200]}")
            return [], ""
        
        video_file = video_files[0]
        print(f"[VIDEO] 下载完成: {video_file.name}")
        
        # 保存视频到持久目录供前端播放
        videos_dir = WORKSPACE / "videos"
        videos_dir.mkdir(exist_ok=True)
        persisted_path = videos_dir / video_file.name
        if not persisted_path.exists():
            shutil.copy2(video_file, persisted_path)
        video_serving_url = f"/video/{video_file.name}"
        
        # Step 2: 尝试提取内嵌字幕
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", 
             "-show_streams", str(video_file)],
            capture_output=True, text=True, timeout=30
        )
        
        has_subtitle = False
        if result.stdout:
            try:
                info = json.loads(result.stdout)
                for stream in info.get("streams", []):
                    if stream.get("codec_type") == "subtitle":
                        has_subtitle = True
                        break
            except: pass
        
        if has_subtitle:
            # 提取字幕
            print("[VIDEO] 提取内嵌字幕...")
            result = subprocess.run(
                ["ffmpeg", "-i", str(video_file), "-map", "0:s:0",
                 "-f", "webvtt", str(output_dir / "sub.vtt")],
                capture_output=True, text=True, timeout=30
            )
            sub_file = output_dir / "sub.vtt"
            if sub_file.exists():
                transcript = parse_vtt(sub_file.read_text())
        
        # Step 3: 尝试下载外部字幕
        if not transcript:
            print("[VIDEO] 尝试下载外部字幕...")
            result = subprocess.run(
                ["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs",
                 "--sub-lang", "zh-Hans,zh,en", "--sub-format", "vtt",
                 "-o", str(output_dir / "%(id)s"), url],
                capture_output=True, text=True, timeout=30
            )
            sub_files = list(output_dir.glob("*.vtt")) + list(output_dir.glob("*.srt"))
            for sf in sub_files[:1]:
                transcript = parse_vtt(sf.read_text())
                break
        
        # Step 4: Whisper STT 兜底
        if not transcript and video_file:
            print("[VIDEO] 无字幕，使用 Whisper 转写...")
            try:
                result = subprocess.run(
                    ["whisper", str(video_file), "--model", "tiny", 
                     "--language", "zh", "--output_format", "all",
                     "--output_dir", str(output_dir)],
                    capture_output=True, text=True, timeout=300
                )
                # Whisper 输出 VTT 格式
                vtt_files = list(output_dir.glob("*.vtt"))
                for vf in vtt_files[:1]:
                    transcript = parse_vtt(vf.read_text())
                    print(f"[VIDEO] Whisper 完成: {len(transcript)} 条")
                    break
            except subprocess.TimeoutExpired:
                print("[VIDEO] Whisper 超时")
            except Exception as e:
                print(f"[VIDEO] Whisper 失败: {e}")
        
        # Step 5: 如果都没有，返回提示
        if not transcript:
            print("[VIDEO] 无可用字幕，请手动提供转写文本")
        
    except subprocess.TimeoutExpired:
        print("[VIDEO] 处理超时")
    except Exception as e:
        print(f"[VIDEO] 处理异常: {e}")
    finally:
        # 清理临时目录（视频已复制到 videos/）
        try:
            shutil.rmtree(output_dir)
        except: pass
    
    return transcript, video_serving_url


def parse_vtt(text: str) -> list:
    """解析 WebVTT/SRT 字幕为统一的 transcript 格式
    支持两种时间戳格式：
    - HH:MM:SS.mmm (标准 WebVTT)
    - MM:SS.mmm (Whisper 输出)
    """
    import re
    items = []
    text = re.sub(r'^\ufeff', '', text)
    text = re.sub(r'^WEBVTT.*\n', '', text)
    
    # 匹配 HH:MM:SS.mmm 或 MM:SS.mmm
    ts_pattern = r'(\d{2}:\d{2}(?::\d{2})?[.,]\d{3})'
    pattern = ts_pattern + r'\s*-->\s*' + ts_pattern + r'\s*\n(.*?)(?=\n\n|\n\d+\n|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for start_ts, end_ts, content in matches:
        # 统一转为总秒数 → MM:SS 格式
        parts = start_ts.split(':')
        if len(parts) == 3:  # HH:MM:SS.mmm
            total_s = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(float(parts[2].replace(',', '.')))
        else:  # MM:SS.mmm (Whisper)
            total_s = int(parts[0]) * 60 + int(float(parts[1].replace(',', '.')))
        
        ts = f"{int(total_s // 60):02d}:{int(total_s % 60):02d}"
        
        clean_text = re.sub(r'<[^>]+>', '', content).strip()
        clean_text = clean_text.replace('\n', ' ')
        
        if clean_text:
            items.append({"ts": ts, "tag": "", "text": clean_text})
    
    # 去重
    seen = {}
    result = []
    for item in items:
        if item["ts"] not in seen:
            seen[item["ts"]] = item
            result.append(item)
    
    return result


def run_pipeline(transcript: list) -> tuple:
    """运行文本分析管道，返回 (results, token_stats)"""
    transcript_text = format_transcript(transcript)
    results = {}
    token_stats = {
        "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
        "cost_usd": 0.0, "per_call": []
    }
    
    tasks = [
        ("overview", PROMPTS["overview"], 2048),
        ("script_analysis", PROMPTS["script_analysis"], 4096),
        ("template", PROMPTS["template"], 3072),
        ("cinematography", PROMPTS["cinematography"], 4096),
        ("scoring", PROMPTS["scoring"], 2048),
    ]
    
    for name, prompt_template, max_tok in tasks:
        try:
            prompt = prompt_template.format(transcript=transcript_text)
            raw, usage = call_deepseek(prompt, max_tokens=max_tok)
            results[name] = json.loads(raw)
            
            pt = usage.get("prompt_tokens", 0)
            ct = usage.get("completion_tokens", 0)
            tt = usage.get("total_tokens", 0)
            # DeepSeek定价: input $0.27/M, output $1.10/M
            cost = (pt * 0.27 + ct * 1.10) / 1_000_000
            
            token_stats["prompt_tokens"] += pt
            token_stats["completion_tokens"] += ct
            token_stats["total_tokens"] += tt
            token_stats["cost_usd"] += cost
            token_stats["per_call"].append({
                "name": name, "prompt_tokens": pt, "completion_tokens": ct,
                "total_tokens": tt, "cost_usd": round(cost, 6)
            })
            print(f"  [{name}] {tt}t, \${cost:.5f}")
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            results[name] = None
    
    return results, token_stats


class APIHandler(SimpleHTTPRequestHandler):
    """处理 API 请求 + 静态文件"""
    
    def do_POST(self):
        if self.path == "/api/analyze":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                
                url = body.get("url", "")
                transcript = body.get("transcript", [])
                
                # 如果提供了 URL，先下载视频并提取转写
                video_url = ""
                if url and not transcript:
                    print(f"[API] 处理视频URL: {url}")
                    transcript, video_url = process_video_url(url)
                    if not transcript:
                        self._json({
                            "error": "视频处理失败：无法下载或提取字幕。请确保链接有效，或直接通过 API 发送 transcript 数据",
                            "transcript": [], "analysis": {}
                        }, 200)
                        return
                    # 注入 video_url 到 body 用于响应
                    body["_video_url"] = video_url
                
                if not transcript:
                    self._json({"error": "缺少 transcript 数据或 URL", "transcript": [], "analysis": {}}, 400)
                    return
                
                print(f"[API] 分析请求：{len(transcript)} 条对白")
                start = time.time()
                analysis, token_stats = run_pipeline(transcript)
                elapsed = time.time() - start
                
                print(f"[API] 分析完成：{elapsed:.1f}s | "
                      f"Tokens: {token_stats['total_tokens']} "
                      f"(in:{token_stats['prompt_tokens']} out:{token_stats['completion_tokens']}) | "
                      f"Cost: \${token_stats['cost_usd']:.5f}")
                
                self._json({
                    "transcript": transcript, 
                    "analysis": analysis, 
                    "video_url": body.get("_video_url", ""),
                    "token_stats": token_stats
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[API ERROR] {e}")
                self._json({"error": str(e), "transcript": [], "analysis": {}}, 500)
        else:
            self._json({"error": "not found"}, 404)
    
    def do_GET(self):
        # 视频文件服务
        if self.path.startswith("/video/"):
            video_name = self.path[7:]
            video_dir = WORKSPACE / "videos"
            video_path = video_dir / video_name
            if video_path.exists() and video_path.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Length", str(video_path.stat().st_size))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(video_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._json({"error": "video not found"}, 404)
            return
        
        # API endpoints
        if self.path == "/api/health":
            self._json({"status": "ok", "model": "deepseek-chat", "has_key": bool(DEEPSEEK_API_KEY)})
            return
        
        # 静态文件
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
        # 减少日志噪音
        if "/api/" in str(args):
            print(f"[HTTP] {args[0]}")


def main():
    port = 8777
    
    if not DEEPSEEK_API_KEY:
        print("⚠️  DEEPSEEK_API_KEY 未设置！分析功能将不可用")
        print("   设置方式: export DEEPSEEK_API_KEY=sk-xxx")
    else:
        print(f"✅ DeepSeek API Key: {DEEPSEEK_API_KEY[:12]}...")
    
    os.chdir(str(WORKSPACE))
    server = HTTPServer(("127.0.0.1", port), APIHandler)
    print(f"🚀 视频分析服务: http://localhost:{port}")
    print(f"   API: POST http://localhost:{port}/api/analyze")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")


if __name__ == "__main__":
    main()
