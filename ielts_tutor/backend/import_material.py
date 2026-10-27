"""
C1 素材导入 · 双路径自动分流 (2026-10-07)

- 路径A（有字幕）: YouTube 用 yt-dlp 拉英文字幕 / B站用官方 API 字幕 → 秒级
- 路径B（无字幕, vlog 主力）: 下载音频 → faster-whisper 转写（带时间戳分句）
- 分句三规则: 句末标点 / 与下句间隔≥0.8s / ≥18词合并
- 转写后过滤: 口头禅碎句 (uh/you know/like...)
- 中文: B站有中文字幕直接匹配 / 否则 DeepSeek 批量逐句翻译

本模块所有函数为同步阻塞（下载/转写耗时），由 server.py 通过 asyncio.to_thread
在后台线程调用，避免阻塞事件循环。
"""
import os
import re
import json
import subprocess
import tempfile
import logging
from pathlib import Path
from datetime import datetime

import requests

logger = logging.getLogger("import-material")

from config import DEEPSEEK_KEY, DEEPSEEK_BASE
import session_manager as sm


def _get_sm():
    """惰性获取 session manager 实例（materials 操作为纯 DB，多实例无妨）。"""
    if not hasattr(_get_sm, "inst"):
        _get_sm.inst = sm.PersistentSessionManager()
    return _get_sm.inst

# ── 路径与工具 ──
MATERIALS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "materials")
YTDLP = "/opt/homebrew/bin/yt-dlp"  # 系统 yt-dlp（与 video_analyzer_app 一致）
FFMPEG = "/opt/homebrew/bin/ffmpeg"
YOUGET = "/opt/homebrew/bin/you-get"

# 转写模型（离线求准；默认 small.en 已缓存可秒加载，可切 medium.en/large-v3 求更高准确率）
TRANSCRIBE_MODEL = os.environ.get("IELTS_MATERIAL_MODEL", "small.en")
TRANSCRIBE_BEAM = int(os.environ.get("IELTS_MATERIAL_BEAM", "5"))

_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"),
    "Referer": "https://www.bilibili.com/",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 口头禅/无意义碎句（转写后过滤）
_FILLERS = {"uh", "um", "hmm", "mm", "you know", "like", "okay", "ok", "yeah",
            "right", "well", "so", "and", "but", "oh", "ah", "yes", "no", "hey"}


# ══════════════════════════════════════════════════════════════
# 平台判定
# ══════════════════════════════════════════════════════════════
def is_youtube(url: str) -> bool:
    return any(k in url for k in ("youtube.com", "youtu.be"))


def is_bilibili(url: str) -> bool:
    return any(k in url for k in ("bilibili.com", "b23.tv")) or re.search(r"\bBV[A-Za-z0-9]+\b", url) is not None


def is_douyin(url: str) -> bool:
    return any(k in url for k in ("douyin.com", "iesdouyin.com"))


# ══════════════════════════════════════════════════════════════
# 后台任务入口
# ══════════════════════════════════════════════════════════════
def process_material(material_id: int, url: str) -> None:
    """后台任务：判定平台 → 双路径分流 → 入库 → 更新状态。同步阻塞，须在线程中调用。"""
    try:
        if is_youtube(url):
            result = _process_youtube(url)
        elif is_bilibili(url):
            result = _process_bilibili(url)
        elif is_douyin(url):
            result = _process_douyin(url)
        else:
            raise ValueError(f"不支持的链接: {url}")
        sm_inst = _get_sm()
        sm_inst.complete_material(material_id, result["title"], result["segments"], result.get("audio_path"))
        logger.info(f"material {material_id}: OK ({len(result['segments'])} 句)")
    except Exception as e:
        logger.error(f"material {material_id}: FAILED — {type(e).__name__}: {e}")
        _get_sm().fail_material(material_id, str(e))


# ══════════════════════════════════════════════════════════════
# YouTube
# ══════════════════════════════════════════════════════════════
def _ytdlp_title(url: str) -> str:
    """单独取视频标题（skip_download）。"""
    try:
        proc = subprocess.run([YTDLP, "--print", "%(title)s", "--skip-download",
                               "--no-warnings", url], capture_output=True, text=True, timeout=60)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip().splitlines()[0].strip()
    except Exception:
        pass
    return "YouTube Lesson"


def _ytdlp_subtitles(url: str, outdir: Path) -> Path:
    """路径A: 只拉英文字幕（skip_download），返回 vtt 路径。"""
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [YTDLP, "--skip-download", "--write-subs", "--write-auto-subs",
           "--sub-langs", "en", "--sub-format", "vtt", "--no-warnings",
           "-o", str(outdir / "%(id)s.%(ext)s"), url]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp 字幕失败: {proc.stderr.strip()[-300:]}")
    vtt = next((p for p in outdir.iterdir() if p.suffix == ".vtt"), None)
    if not vtt:
        raise RuntimeError("未找到英文字幕")
    return vtt


def _ytdlp_audio(url: str, outdir: Path) -> Path:
    """路径B: 下载最佳音频流。"""
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [YTDLP, "-f", "bestaudio[ext=m4a]/bestaudio/best", "--no-playlist",
           "--no-warnings", "-o", str(outdir / "%(id)s.%(ext)s"), url]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp 音频失败: {proc.stderr.strip()[-300:]}")
    for ext in ("m4a", "webm", "mp4", "opus", "m4b"):
        matches = list(outdir.glob(f"*.{ext}"))
        if matches:
            return matches[0]
    raise RuntimeError("音频下载失败：未找到输出文件")


def _process_youtube(url: str) -> dict:
    title = _ytdlp_title(url)
    with tempfile.TemporaryDirectory(prefix="yt-lesson-") as tmp:
        tmpdir = Path(tmp)
        # 路径A：字幕优先
        try:
            vtt = _ytdlp_subtitles(url, tmpdir)
            segments = _parse_vtt(vtt)
            if segments:
                segments = _add_translations(_merge_and_filter(segments))
                return {"title": title, "segments": segments, "audio_path": None}
        except Exception as e:
            logger.info(f"YouTube 字幕路径失败（转走转写）: {e}")
        # 路径B：下载音频 + 转写
        audio = _ytdlp_audio(url, tmpdir)
        audio_dst = _save_audio(audio)
        segments = _transcribe(audio)
        segments = _add_translations(_merge_and_filter(segments))
        return {"title": title, "segments": segments, "audio_path": audio_dst}


# ══════════════════════════════════════════════════════════════
# B站
# ══════════════════════════════════════════════════════════════
def _extract_bvid(url: str) -> str:
    if "b23.tv" in url:
        try:
            r = requests.get(url, headers=_HEADERS, timeout=15, allow_redirects=False)
            if r.is_redirect and r.headers.get("Location"):
                url = r.headers["Location"]
            else:
                url = requests.get(url, headers=_HEADERS, timeout=15, allow_redirects=True).url
        except Exception:
            pass
    m = re.search(r"/video/(BV[A-Za-z0-9]+)", url)
    if m:
        return m.group(1)
    m = re.search(r"\b(BV[A-Za-z0-9]{10})\b", url)
    if m:
        return m.group(1)
    raise ValueError(f"无法从链接提取 Bilibili BV 号: {url}")


def _bilibili_title(url: str) -> str:
    """用 you-get -i 拿 B站标题（绕过 412 风控）。"""
    cmd = [YOUGET, "-i", url]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
    if proc.returncode != 0:
        raise RuntimeError(f"you-get 失败: {proc.stderr.strip()[-300:]}")
    m = re.search(r"title:\s+(.+)", proc.stdout)
    return m.group(1).strip() if m else "Bilibili Lesson"


def _bilibili_video_youget(url: str, outdir: Path) -> Path:
    """you-get 下载 B站视频（绕过 412 风控），返回视频文件路径。"""
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [YOUGET, "-o", str(outdir), "-O", "bili_video", url]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(f"you-get 下载失败: {proc.stderr.strip()[-300:]}")
    video = next((p for p in outdir.iterdir() if p.name.startswith("bili_video") and p.is_file()), None)
    if not video:
        video = next((p for p in outdir.iterdir() if p.suffix.lower() in (".mp4", ".flv", ".mkv", ".mp3")), None)
    if not video:
        raise RuntimeError("you-get 下载后未找到视频文件")
    return video


def _process_bilibili(url: str) -> dict:
    """B站：view/playurl API 被境外 IP 412 风控，统一走 you-get 下载视频 + Whisper 转写。"""
    title = _bilibili_title(url)
    with tempfile.TemporaryDirectory(prefix="bili-lesson-") as tmp:
        tmpdir = Path(tmp)
        video = _bilibili_video_youget(url, tmpdir)
        audio_dst = _save_audio(video)
        segs = _transcribe(video)
        segs = _add_translations(_merge_and_filter(segs))
        return {"title": title, "segments": segs, "audio_path": audio_dst}


# ══════════════════════════════════════════════════════════════
# 抖音
# ══════════════════════════════════════════════════════════════
_DOUYIN_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def _douyin_audio(url: str, outdir: Path):
    """Playwright 打开抖音视频页，拦截独立音频流（media-audio）并下载，返回 (audio_path, title)。"""
    from playwright.sync_api import sync_playwright
    audio_urls = []
    title = "抖音视频"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled', '--no-sandbox', '--mute-audio'])
        context = browser.new_context(user_agent=_DOUYIN_UA, viewport={"width": 1440, "height": 900},
                                      locale="zh-CN", timezone_id="Asia/Shanghai")
        context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = context.new_page()

        def on_response(resp):
            u = resp.url
            if "media-audio" in u:
                audio_urls.append(u)
        page.on("response", on_response)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(6000)
            t = (page.title() or "").strip()
            if t:
                title = re.sub(r"\s*[-_|]\s*(抖音|douyin)\s*$", "", t, flags=re.I).strip() or t
        except Exception:
            pass
        browser.close()
    if not audio_urls:
        raise RuntimeError("未拦截到抖音音频流（可能被风控）")
    audio_url = audio_urls[0]
    out = outdir / "douyin_audio.m4a"
    r = requests.get(audio_url, headers={"User-Agent": _DOUYIN_UA, "Referer": "https://www.douyin.com/"},
                     stream=True, timeout=120)
    r.raise_for_status()
    with open(out, "wb") as f:
        for chunk in r.iter_content(1024 * 256):
            if chunk:
                f.write(chunk)
    return out, title


def _process_douyin(url: str) -> dict:
    """抖音：Playwright 拦截音频流 → 下载 → Whisper 转写。"""
    with tempfile.TemporaryDirectory(prefix="dy-lesson-") as tmp:
        tmpdir = Path(tmp)
        audio, title = _douyin_audio(url, tmpdir)
        audio_dst = _save_audio(audio)
        segs = _transcribe(audio)
        segs = _add_translations(_merge_and_filter(segs))
        return {"title": title, "segments": segs, "audio_path": audio_dst}


# ══════════════════════════════════════════════════════════════
# 转写（路径B）
# ══════════════════════════════════════════════════════════════
_transcriber = None

def _get_transcriber():
    global _transcriber
    if _transcriber is None:
        from faster_whisper import WhisperModel
        logger.info(f"转写模型加载中: {TRANSCRIBE_MODEL} ...")
        _transcriber = WhisperModel(TRANSCRIBE_MODEL, device="auto", compute_type="auto")
        logger.info(f"转写模型就绪: {TRANSCRIBE_MODEL}")
    return _transcriber


def _transcribe(audio_path: Path) -> list:
    model = _get_transcriber()
    segments, info = model.transcribe(
        str(audio_path), beam_size=TRANSCRIBE_BEAM, vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    out = []
    for seg in segments:
        t = seg.text.strip()
        if t:
            out.append({"text": t, "start": round(seg.start, 2), "end": round(seg.end, 2)})
    return out


# ══════════════════════════════════════════════════════════════
# 字幕解析 + 分句合并 + 过滤
# ══════════════════════════════════════════════════════════════
def _parse_vtt(vtt_path: Path) -> list:
    """解析 webvtt：时间轴 + 文本，去 <c> 等标签，按空行分块。"""
    segs = []
    block = []
    for line in vtt_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            if block:
                _vtt_block(segs, block)
                block = []
            continue
        block.append(line)
    if block:
        _vtt_block(segs, block)
    return segs


def _vtt_block(segs: list, block: list):
    m = re.search(r"(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})", "\n".join(block[:2]))
    if not m:
        return
    start = _ts(m.group(1))
    end = _ts(m.group(2))
    text = " ".join(l for l in block[2:] if not l.startswith(("WEBVTT", "NOTE", "Kind:", "Language:")))
    text = re.sub(r"<[^>]+>", "", text).strip()
    if text:
        segs.append({"text": text, "start": start, "end": end})


def _ts(hms: str) -> float:
    h, m, s = hms.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def _merge_and_filter(segments: list, max_words: int = 18) -> list:
    """过滤口头禅碎句 + 合并短句到完整句（三规则）。"""
    kept = []
    for s in segments:
        t = s["text"].strip()
        words = t.split()
        if not words:
            continue
        low = t.lower().rstrip(".,!?")
        if low in _FILLERS or (len(words) == 1 and len(low) < 5):
            continue
        kept.append(s)
    merged, buf = [], []
    for s in kept:
        buf.append(s)
        text = " ".join(x["text"].strip() for x in buf)
        has_end = bool(re.search(r"[.!?][\"']?$", s["text"].strip()))
        if has_end or len(text.split()) >= max_words:
            merged.append({"text": text, "start": buf[0]["start"], "end": buf[-1]["end"]})
            buf = []
    if buf:
        merged.append({"text": " ".join(x["text"].strip() for x in buf),
                       "start": buf[0]["start"], "end": buf[-1]["end"]})
    return merged


# ══════════════════════════════════════════════════════════════
# 中文翻译（DeepSeek 批量）
# ══════════════════════════════════════════════════════════════
def _deepseek_chat(messages, max_tokens=4000, temp=0.3):
    url = f"{DEEPSEEK_BASE}/chat/completions"
    h = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    b = {"model": "deepseek-v4-flash", "messages": messages, "temperature": temp,
         "max_tokens": max_tokens, "thinking": {"type": "disabled"}}
    r = requests.post(url, json=b, headers=h, timeout=120)
    data = r.json()
    return data["choices"][0]["message"]["content"]


def _translate_batch(texts: list) -> list:
    """DeepSeek 批量逐句翻译，返回与输入等长的 list[str]。失败返回空串。"""
    if not DEEPSEEK_KEY:
        return [""] * len(texts)
    out = [""] * len(texts)
    batch_size = 40
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        numbered = "\n".join(f"{j + 1}. {t}" for j, t in enumerate(batch))
        prompt = ("Translate the following English sentences to Simplified Chinese. "
                  "Return ONLY a JSON array of strings, one translation per sentence, same order, no extra text.\n\n"
                  + numbered)
        try:
            raw = _deepseek_chat([{"role": "user", "content": prompt}])
            raw = re.sub(r"```(json)?", "", raw).strip().strip("`")
            arr = json.loads(raw)
            if isinstance(arr, list):
                for j, v in enumerate(arr[:len(batch)]):
                    out[i + j] = str(v).strip()
        except Exception as e:
            logger.warning(f"翻译失败 batch@{i}: {e}")
    return out


def _add_translations(segments: list) -> list:
    """为无 translation 的句批量补中文。"""
    need = [s for s in segments if not s.get("translation")]
    if need:
        trans = _translate_batch([s["text"] for s in need])
        for s, t in zip(need, trans):
            s["translation"] = t
    for s in segments:
        s.setdefault("translation", "")
    return segments


def _fill_missing_translations(segments: list) -> list:
    return _add_translations(segments)


# ══════════════════════════════════════════════════════════════
# 音频归档
# ══════════════════════════════════════════════════════════════
def _save_audio(src: Path) -> str:
    """把下载的音频复制到 data/materials/ 持久目录，返回绝对路径。"""
    os.makedirs(MATERIALS_DIR, exist_ok=True)
    name = f"{int(datetime.now().timestamp() * 1000)}_{src.name}"
    dst = Path(MATERIALS_DIR) / name
    import shutil
    shutil.copy2(src, dst)
    return str(dst)
