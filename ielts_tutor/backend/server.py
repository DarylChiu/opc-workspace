"""
IELTS Tutor v2.0 - Server · PTT模式 + 最终评估
"""
import os, json, logging, asyncio, uuid, base64, time, re
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from starlette.responses import StreamingResponse
import uvicorn, aiohttp
import ssl; ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ielts-tutor")

import os as _os
if _os.environ.get("DEBUG_MODE", "0") == "1":
    from debug_logger import debug_manager, handle_debug_ws, handle_debug_export, handle_debug_list
else:
    debug_manager = None

from config import GOOGLE_STT_KEY, GOOGLE_TTS_KEY, DEEPSEEK_KEY, DEEPSEEK_BASE
import question_bank
import auth
from session_manager import PersistentSessionManager
from report_generator import generate_report
from stt_streaming import StreamingTranscriber

# ── Pre-warm models on startup ──
def _prewarm_models():
    """Pre-load STT and TTS models to avoid cold-start latency on first request."""
    import threading, numpy as np
    def _warm():
        try:
            logger.info("🔥 Pre-warming STT model...")
            stt = StreamingTranscriber()
            stt.feed(b'\x00' * 32000)
            stt.transcribe()
            stt.reset()
            logger.info("🔥 Pre-warming TTS model...")
            _get_kokoro()  # force Kokoro load
            _get_piper()   # force Piper load (fallback)
            logger.info("✅ Pre-warm complete")
        except Exception as e:
            logger.warning(f"Pre-warm failed (non-fatal): {e}")
    t = threading.Thread(target=_warm, daemon=True)
    t.start()
sessions = PersistentSessionManager()
question_bank.init_db()  # v1.4.1 题库去重表
auth.init_db()  # v1.5.0 P1 用户系统
FRONTEND = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")
VOCAB_PAGE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "vocab.html")

# Cost tracking
cost_stats = {"stt_calls":0, "tts_calls":0, "tts_chars":0, "ds_input":0, "ds_output":0}

app = FastAPI(title="IELTS Tutor v2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ── Prompts ──
SYSTEM_PROMPTS = {
    "ielts_part1": """You are Alex, a friendly IELTS Speaking examiner doing Part 1.

CRITICAL RULES:
- DEEP FOLLOW-UPS PER TOPIC: Choose 3-4 topics total (from: work/study, hometown, home, hobbies, reading, music, travel, food, sports, weather). For EACH topic, ask 2-3 follow-up questions exploring different aspects before transitioning. Go deeper, not wider.
- React naturally to what the candidate says — acknowledge their answer with a brief comment before asking your next question. Show genuine curiosity.
- Ask ONE question at a time. Keep your responses conversational: 2-4 sentences including your reaction + next question.
- Vary your transitions naturally: 'That's interesting — tell me more about...', 'I see. And what about...', 'Let me ask you...', 'How do you feel about...'
- NEVER repeat a topic you already discussed. NEVER give scores or say 'good/excellent'.
- Match the candidate's level — don't use overly complex vocabulary.
- Be warm and conversational, like chatting with a friend over coffee.""",
    "ielts_part2": """You are an IELTS examiner doing Part 2 (Long Turn). Give the topic card clearly, give 1 min prep silently, then let candidate speak 1-2 min. Ask 1-2 natural follow-up questions after. Keep your own words minimal.""",
    "ielts_part3": """You are an IELTS examiner doing Part 3. Ask abstract discussion questions. Follow up on answers with deeper questions. Challenge ideas respectfully. Keep questions concise and natural.""",
    "business_pitch": """You are a business English coach for investor pitch practice. Simulate an investor meeting naturally. Ask typical questions investors ask. Give one specific, constructive tip after each answer. Keep it professional but encouraging.""",
    "free_talk": """You are a thoughtful English conversation partner for deep, natural discussion.

CORE RULES:
- LISTEN first — let the user drive the topic. Follow their thread, don't redirect to new topics.
- ENGAGE WITH CONTENT — respond to WHAT they're saying, not HOW they're saying it. Show genuine curiosity about their ideas, opinions, and stories.
- GO DEEPER, NOT WIDER — ask clarifying or deepening questions about what they just said, rather than shifting to a new subject. "Tell me more about that..." / "What made you feel that way?" / "That's interesting — why do you think that is?"
- GRAMMAR: Only correct errors that genuinely block understanding. If you do correct, make it brief and natural — never interrupt the flow of conversation for grammar. The goal is connection, not perfection.
- RESPONSE LENGTH: 3-6 sentences. Give substantive, thoughtful responses — this is a real conversation, not small talk.
- NEVER say things like "that's great!" or "nice to hear" as filler. If you acknowledge something, make it specific to what they said.
- Match the user's emotional tone. If they're passionate, match that energy. If they're reflective, slow down with them.""",
}
GREETINGS = {
    "ielts_part1": "Good morning. My name is Alex and I'll be your IELTS examiner today. Can you tell me your full name, please?",
    "ielts_part2": "Now I'm going to give you a topic. You should talk about it for 1 to 2 minutes. Before you talk, you'll have 1 minute to prepare. Here is your topic: Describe a book you recently read. You should say what the book was, why you read it, what it was about, and how you felt about it.",
    "ielts_part3": "Now let's talk about some more general questions related to reading. Do you think people read less now than they did in the past?",
    "business_pitch": "Welcome to your investor pitch practice. I'll play the role of a potential investor. Tell me about your business when you're ready.",
    "free_talk": "Hi there! What would you like to chat about today?",
}

# ── Helpers ──
async def ds_chat(messages, max_tokens=150, temp=0.7):
    url = f"{DEEPSEEK_BASE}/chat/completions"
    h = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    # 2026-08-08 修复: v4-flash 默认 Thinking 模式, reasoning_content 吃光 max_tokens 导致评估 JSON 残缺
    # 显式关闭 Thinking (thinking disabled 后 temperature 才生效)
    b = {"model": "deepseek-v4-flash", "messages": messages, "temperature": temp, "max_tokens": max_tokens, "thinking": {"type": "disabled"}}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=b, headers=h, timeout=aiohttp.ClientTimeout(25)) as r:
                data = await r.json()
                usage = data.get("usage", {})
                cost_stats["ds_input"] += usage.get("prompt_tokens", 0)
                cost_stats["ds_output"] += usage.get("completion_tokens", 0)
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"DS: {type(e).__name__}: {e}"); return ""

async def ds_stream(messages, max_tokens=500):
    url = f"{DEEPSEEK_BASE}/chat/completions"
    h = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    b = {"model": "deepseek-v4-flash", "messages": messages, "temperature": 0.7, "max_tokens": max_tokens, "stream": True, "thinking": {"type": "disabled"}}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=b, headers=h, timeout=aiohttp.ClientTimeout(30)) as r:
                buf = b""
                async for c in r.content.iter_any():
                    buf += c
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        line = line.strip()
                        if not line or line == b"data: [DONE]": continue
                        if line.startswith(b"data: "): line = line[6:]
                        try:
                            d = json.loads(line)["choices"][0].get("delta", {})
                            if d.get("content"): yield d["content"]
                        except: pass
    except Exception as e: logger.error(f"Stream: {e}")

# ── Endpointing constants ──
ENDPOINT_MAX_SILENCE = 3.0       # 最大静音等待时间（秒）
SPEECH_ENERGY_THRESHOLD = 300    # PCM16 RMS 能量阈值，低于此值视为静音
# Endpointing 默认关闭 — client VAD 已控制 flush 时机
# 开启: export IELTS_ENDPOINTING=1
ENDPOINT_ENABLED = os.environ.get("IELTS_ENDPOINTING", "0") == "1"

# ── Audio buffer limits (长句友好断句, 2026-07-15 问题1修复) ──
# 软上限(默认60s): 超过后等说话间隙再flush, 不在句子中间硬切
# 硬上限(默认90s): 无条件flush, 防止内存失控
AUDIO_BUF_SOFT_LIMIT = int(float(os.environ.get("AUDIO_BUF_SOFT_SECONDS", "60")) * 32000)
AUDIO_BUF_HARD_LIMIT = int(float(os.environ.get("AUDIO_BUF_HARD_SECONDS", "90")) * 32000)
AUDIO_BUF_FLUSH_SILENCE = float(os.environ.get("AUDIO_BUF_FLUSH_SILENCE", "0.6"))  # 软上限后的flush静音窗口(秒)

# ── STT noise filter ──
_STOP_WORDS = {"you","oh","um","uh","ah","yeah","yep","yes","no","ok","okay",
               "hmm","mm","um-hmm","uh-huh","bye","goodbye","thanks","thank you",
               "(audio cuts out)","(silence)","(no speech)","(background noise)",
               "sorry","sorry.","oh.","oh,","no.","no,"}

_NOISE_PATTERNS = [
    r"^(oh|ah|uh|um|hmm|mm)[,.]?\s+(it'?s?|i'?m?|that|this|the|a|an|my)",
    r"^(no[,.]? ){2,}",
    r"^(sorry[,.]? ){2,}",
    r"^oh[,.]?\s+(my|dear|god|gosh|man|boy|wow)",
]

def _filter_stt(text):
    """Filter out noise/false triggers from STT output"""
    t = text.strip().lower().rstrip('.,!?')
    if len(t) < 3 or t in _STOP_WORDS:
        return ""
    if len(t) < 20:
        return ""
    # Filter single-word or filler patterns
    import re
    for pat in _NOISE_PATTERNS:
        if re.match(pat, t):
            logger.info(f"STT[filter]: noise pattern matched → '{text[:40]}'")
            return ""
    return text

# ── Local TTS (Kokoro-82M primary, Piper fallback) ──
# Monkey-patch numpy for Kokoro compatibility with NumPy 2.x
import numpy as _np
_np_load_orig = _np.load
_np.load = lambda *a, **kw: _np_load_orig(*a, **{**kw, 'allow_pickle': True})

_kokoro = None
_kororo_model = os.path.expanduser("~/.openclaw/models/kokoro/kokoro-v0_19.onnx")
_kororo_voices = os.path.expanduser("~/.openclaw/models/kokoro/voices.npy")

_piper_voice = None
# 2026-07-14: 升级到 high 版本 — 发音准确度显著优于 medium，对齐 Kokoro G2P 缺陷的修复
PIPER_MODEL = os.path.expanduser("~/.openclaw/models/piper/en_US-lessac-high.onnx")

def _get_kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(_kororo_model, _kororo_voices)
        _kokoro.voices = _kokoro.voices.item()  # extract dict from 0-d array
        logger.info(f"TTS[kokoro]: model loaded")
    return _kokoro

def _get_piper():
    global _piper_voice
    if _piper_voice is None:
        from piper.voice import PiperVoice
        _piper_voice = PiperVoice.load(PIPER_MODEL, PIPER_MODEL + '.json')
        logger.info(f"TTS[piper]: model loaded")
    return _piper_voice

# 方案B: 句尾静音填充，消除逐句拼接播放时的"撞音/吞音"
# 每句合成音频末尾追加一段静音，让前端顺序播放时句间有自然停顿。
TTS_TAIL_SILENCE_MS = int(os.environ.get("TTS_TAIL_SILENCE_MS", "300"))

def _pcm_with_tail_silence(pcm: bytes, sample_rate: int, silence_ms: int = TTS_TAIL_SILENCE_MS) -> bytes:
    """在 16-bit mono PCM 末尾追加 silence_ms 毫秒的静音。"""
    if silence_ms <= 0:
        return pcm
    n_silence_samples = int(sample_rate * silence_ms / 1000)
    return pcm + (b'\x00\x00' * n_silence_samples)

async def tts_speak(text):
    cost_stats["tts_calls"] += 1
    cost_stats["tts_chars"] += len(text)
    # Strip markdown formatting that TTS would read aloud
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)
    text = re.sub(r'_{1,2}(.+?)_{1,2}', r'\1', text)
    
    # ── Primary: Piper high (accurate pronunciation, no G2P issues) ──
    # 2026-07-14: 从 Kokoro 翻转为 Piper 为主引擎。
    # 原因：Kokoro-82M 的 misaki/espeak-ng G2P 模块会输出
    # "words count mismatch" warning，导致部分英文单词发音错误/被跳过。
    # Piper 的发音准确度远优于 Kokoro，且 high 版本音质显著提升。
    try:
        import io, wave
        voice = _get_piper()
        audio = b''
        for chunk in voice.synthesize(text):
            audio += chunk.audio_int16_bytes
        if audio:
            audio = _pcm_with_tail_silence(audio, voice.config.sample_rate)
            buf = io.BytesIO()
            with wave.open(buf, 'wb') as w:
                w.setnchannels(1); w.setsampwidth(2)
                w.setframerate(voice.config.sample_rate)
                w.writeframes(audio)
            return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        logger.warning(f"TTS[piper] failed: {e}, trying Kokoro")
    
    # ── Fallback 1: Kokoro-82M (natural but known G2P issues) ──
    try:
        import io, wave, numpy
        k = _get_kokoro()
        samples, sr = k.create(text, voice='bf_isabella', speed=0.9)
        pcm = (samples * 32767).astype('int16').tobytes()
        pcm = _pcm_with_tail_silence(pcm, sr)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes(pcm)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        logger.warning(f"TTS[kokoro] failed: {e}, falling back to Google")
    
    # ── Fallback: Google TTS ──
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_TTS_KEY}"
    b = {"input": {"text": text}, "voice": {"languageCode": "en-US", "name": "en-US-Journey-O"},
         "audioConfig": {"audioEncoding": "MP3", "speakingRate": 0.95}}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=b, timeout=aiohttp.ClientTimeout(10)) as r:
                return (await r.json()).get("audioContent", "")
    except:
        return ""

# STT replaced by streaming faster-whisper (see stt_streaming.py + StreamingTranscriber below)

# ── HTTP ──
MONITOR_HTML = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "monitor.html")

@app.get("/")
async def index(): return HTMLResponse(open(FRONTEND).read())

@app.get("/vocab")
async def vocab_page(): return HTMLResponse(open(VOCAB_PAGE).read())

@app.get("/monitor")
async def monitor_page():
    if os.path.exists(MONITOR_HTML):
        return HTMLResponse(open(MONITOR_HTML).read())
    return HTMLResponse("<h1>Monitor not found</h1>", status_code=404)

@app.get("/api/monitor/stream")
async def monitor_stream(request: Request):
    """SSE endpoint for debug monitor — polls current server state."""
    async def event_stream():
        import asyncio as _aio
        while True:
            try:
                if await request.is_disconnected():
                    break
                sess_count = len(sessions)
                data = {
                    "session_count": sess_count,
                    "server_uptime": "running",
                    "pipeline": "cascade",
                    "debug_enabled": debug_manager is not None,
                    "costs": {
                        "stt_calls": cost_stats["stt_calls"],
                        "tts_calls": cost_stats["tts_calls"],
                        "ds_input": cost_stats["ds_input"],
                        "ds_output": cost_stats["ds_output"],
                    }
                }
                yield f"data: {json.dumps(data)}\n\n"
                await _aio.sleep(2)
            except Exception:
                break
    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ── v1.1.0 M2: 训练数据库页 Dashboard ──
DASHBOARD_HTML = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dashboard.html")

@app.get("/dashboard")
async def dashboard_page():
    if os.path.exists(DASHBOARD_HTML):
        return HTMLResponse(open(DASHBOARD_HTML).read())
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)

@app.get("/api/dashboard/stats")
async def dashboard_stats(days: int = 30):
    return sessions.get_progress_stats(days=min(days, 365))

@app.get("/api/dashboard/reviews")
async def dashboard_reviews(limit: int = 100, status: str = None):
    return {"reviews": sessions.get_review_list(limit=min(limit, 500), status=status)}

@app.get("/api/dashboard/history")
async def dashboard_history(limit: int = 20):
    return {"history": sessions.get_history(limit=min(limit, 100))}

@app.get("/api/dashboard/mode-evals")
async def dashboard_mode_evals(mode: str, limit: int = 3):
    """返回指定模式最近N次评估详情（用于训练模式总结展开）"""
    return {"evals": sessions.get_mode_evals(mode=mode, limit=min(limit, 10))}

# ── v1.1.0 M3: 跟读闭环 Shadowing ──
SHADOW_HTML = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "shadow.html")
SHADOW_PASS_WER = float(os.environ.get("SHADOW_PASS_WER", "0.25"))  # WER≤25% 判通过

def _norm_words(text):
    return re.findall(r"[a-z']+", (text or "").lower())

def word_wer_diff(ref_text, hyp_text):
    """词级 Levenshtein WER + 对齐 diff（供前端高亮）"""
    ref, hyp = _norm_words(ref_text), _norm_words(hyp_text)
    if not ref:
        return 0.0, []
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): d[i][0] = i
    for j in range(m + 1): d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i-1] == hyp[j-1] else 1
            d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + cost)
    # 回溯: 标记 ref 每个词 matched / missed
    diff = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i-1][j-1] and ref[i-1] == hyp[j-1]:
            diff.append({"word": ref[i-1], "ok": True}); i -= 1; j -= 1
        elif i > 0 and j > 0 and d[i][j] == d[i-1][j-1] + 1:
            diff.append({"word": ref[i-1], "ok": False}); i -= 1; j -= 1
        elif i > 0 and d[i][j] == d[i-1][j] + 1:
            diff.append({"word": ref[i-1], "ok": False}); i -= 1
        else:
            j -= 1  # hyp 多余词, 不进 ref diff
    diff.reverse()
    return d[n][m] / n, diff

def _get_review_item(item_id):
    import sqlite3 as _sq
    from session_manager import DB_PATH as _dbp
    conn = _sq.connect(_dbp); conn.row_factory = _sq.Row
    row = conn.execute("SELECT * FROM review_items WHERE id=?", (item_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

@app.get("/shadow")
async def shadow_page():
    if os.path.exists(SHADOW_HTML):
        return HTMLResponse(open(SHADOW_HTML).read())
    return HTMLResponse("<h1>Shadow not found</h1>", status_code=404)

@app.get("/api/review/queue")
async def review_queue(limit: int = 8):
    return {"queue": sessions.get_review_queue(limit=min(limit, 20)), "pass_wer": SHADOW_PASS_WER}

@app.post("/api/review/{item_id}/tts")
async def review_tts(item_id: int):
    item = _get_review_item(item_id)
    if not item:
        return {"error": "not_found"}
    audio = await tts_speak(item["target_text"])
    return {"audio": audio, "format": "wav"}

@app.post("/api/review/{item_id}/attempt")
async def review_attempt(item_id: int, req: Request):
    """跟读打分: 收 base64 PCM(16k mono int16) → STT → 词级WER → 记录+回写"""
    item = _get_review_item(item_id)
    if not item:
        return {"error": "not_found"}
    body = await req.json()
    try:
        pcm = base64.b64decode(body.get("audio", ""))
    except Exception:
        return {"error": "bad_audio"}
    if len(pcm) < 3200:  # <0.1s
        return {"error": "audio_too_short"}
    t0 = time.time()
    def _stt_sync():
        tr = StreamingTranscriber()
        tr.feed(pcm)
        return tr.transcribe()
    # 压测发现: 同步STT阻塞事件循环9s → keep-alive连接被关闭+其他API卡死; 挪线程池
    transcript, confidence = await asyncio.to_thread(_stt_sync)
    wer, diff = word_wer_diff(item["target_text"], transcript)
    score = max(0.0, round(1.0 - wer, 3))
    passed = wer <= SHADOW_PASS_WER
    sessions.record_shadow_attempt(item_id, transcript, score, wer, audio_ms=int(len(pcm) / 32))
    if passed:
        sessions.mark_consolidated(item_id)
    cost_stats["stt_calls"] += 1
    logger.info(f"SHADOW: item={item_id} wer={wer:.2f} passed={passed} stt={time.time()-t0:.1f}s '{transcript[:60]}'")
    return {"transcript": transcript, "confidence": confidence, "wer": round(wer, 3),
            "score": score, "passed": passed,
            "status": "consolidated" if passed else "pending", "diff": diff}

@app.post("/api/review/{item_id}/consolidate")
async def review_consolidate(item_id: int):
    if not _get_review_item(item_id):
        return {"error": "not_found"}
    sessions.mark_consolidated(item_id)
    return {"ok": True}

@app.get("/api/health")
async def health():
    ver = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")).read().strip()
    return {"status": "ok", "version": ver, "costs": cost_stats}

@app.post("/api/session/start")
async def start(req: Request):
    body = await req.json()
    mode = body.get("mode", "ielts_part1")
    pipeline = body.get("pipeline", "cascade")
    if mode == "free_talk":
        # v1.4.0: Free Talk 固定持久会话 — 跨天/跨重启记忆
        sid = sessions.get_or_create_ft_session()
        turns = len(sessions.get_ft_transcripts(sid))
        return {"session_id": sid, "mode": mode, "resume": turns > 0, "saved_turns": turns}
    sid = str(uuid.uuid4())[:8]
    sessions.create(sid, mode=mode, pipeline=pipeline)
    return {"session_id": sid, "mode": mode}

@app.get("/api/session/{sid}/score")
async def get_session_score(sid: str):
    """HTTP fallback: WS断开时前端轮询取评估结果 (2026-07-15 问题3修复)"""
    # 1. Check in-memory cache first
    session = sessions.get(sid)
    if session:
        sc = session.get("last_score")
        if sc:
            return {"status": "ready", "scores": sc}
    
    # 2. Fallback: query database (covers server restart, ngrok disconnect, etc.)
    try:
        import json as _json2
        conn = sessions._get_db() if hasattr(sessions, '_get_db') else None
        if not conn:
            import sqlite3 as _sql, os as _os2
            db_path = _os2.path.join(_os2.path.dirname(_os2.path.dirname(__file__)), "data", "ielts_tutor.db")
            conn = _sql.connect(db_path)
        row = conn.execute(
            "SELECT overall,fluency,vocabulary,grammar,pronunciation,summary,improvements,highlights FROM evaluations WHERE session_id=?",
            (sid,)).fetchone()
        if row:
            sc = {
                "overall": row[0], "fluency": row[1], "vocabulary": row[2],
                "grammar": row[3], "pronunciation": row[4], "summary": row[5],
                "improvements": _json2.loads(row[6]) if row[6] else [],
                "highlights": _json2.loads(row[7]) if row[7] else []
            }
            return {"status": "ready", "scores": sc}
    except Exception:
        pass
    
    return {"status": "not_found"}

@app.get("/api/reports")
async def list_reports():
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    if not os.path.exists(reports_dir): return {"reports": []}
    files = sorted([f for f in os.listdir(reports_dir) if f.endswith('.html')], reverse=True)[:20]
    return {"reports": [{"name": f, "url": f"/reports/{f}"} for f in files]}

from fastapi.staticfiles import StaticFiles
reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
os.makedirs(reports_dir, exist_ok=True)
app.mount("/reports", StaticFiles(directory=reports_dir), name="reports")

# ── Vocabulary API (v1.3) ──

@app.get("/api/vocab/wordlist")
async def vocab_wordlist():
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cefr_b2plus.json")
    if os.path.exists(p): return json.loads(open(p).read())
    return []

@app.post("/api/vocab/save")
async def vocab_save(req: Request):
    body = await req.json()
    import sqlite3 as _s
    db = _s.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ielts_tutor.db"))
    db.execute("""CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT NOT NULL, source_sentence TEXT,
        source_speaker TEXT DEFAULT 'tutor', better_expression TEXT, context TEXT,
        session_id TEXT, created_at TEXT DEFAULT (datetime('now')),
        practice_count INTEGER DEFAULT 0, mastered INTEGER DEFAULT 0)""")
    db.execute("INSERT INTO vocabulary (word,source_sentence,source_speaker,better_expression,context,session_id) VALUES (?,?,?,?,?,?)",
        (body.get("word",""), body.get("source_sentence",""), body.get("source_speaker","tutor"),
         body.get("better_expression",""), body.get("context",""), body.get("session_id","")))
    db.commit(); db.close()
    return {"ok": True}

@app.get("/api/vocab/list")
async def vocab_list(limit: int = 50, mastered: int = 0):
    import sqlite3 as _s
    db = _s.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ielts_tutor.db"))
    db.row_factory = _s.Row
    rows = db.execute("SELECT * FROM vocabulary WHERE mastered=? ORDER BY created_at DESC LIMIT ?", (mastered, limit)).fetchall()
    db.close()
    return {"items": [dict(r) for r in rows]}

@app.delete("/api/vocab/{vid}")
async def vocab_delete(vid: int):
    import sqlite3 as _s
    db = _s.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ielts_tutor.db"))
    db.execute("DELETE FROM vocabulary WHERE id=?", (vid,))
    db.commit(); db.close()
    return {"ok": True}

@app.put("/api/vocab/{vid}/practice")
async def vocab_practice(vid: int):
    import sqlite3 as _s
    db = _s.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ielts_tutor.db"))
    db.execute("UPDATE vocabulary SET practice_count=practice_count+1 WHERE id=?", (vid,))
    db.commit(); db.close()
    return {"ok": True}

@app.put("/api/vocab/{vid}/master")
async def vocab_master(vid: int):
    import sqlite3 as _s
    db = _s.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ielts_tutor.db"))
    db.execute("UPDATE vocabulary SET mastered=1 WHERE id=?", (vid,))
    db.commit(); db.close()
    return {"ok": True}

@app.post("/api/vocab/improve")
async def vocab_improve(req: Request):
    body = await req.json()
    word = body.get("word","")
    context = body.get("context","")
    speaker = body.get("speaker","tutor")
    if not word: return {"suggestions": []}
    if speaker == "user":
        prompt = f"""The English learner wrote: "{context}" (focus on: "{word}")
Suggest 2-3 better or more natural English expressions for "{word}" in this context.
Return ONLY valid JSON: {{"suggestions":[{{"original":"word","better":"alternative","explanation":"brief Chinese explanation"}}]}}
Keep explanations in Chinese. Focus on natural, conversational English."""
    else:
        prompt = f"""The tutor said: "{context}" (focus on: "{word}")
Suggest 2-3 synonyms or alternative expressions for "{word}" with a brief Chinese explanation of the nuance.
Return ONLY valid JSON: {{"suggestions":[{{"original":"word","better":"alternative","explanation":"brief Chinese explanation"}}]}}"""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{DEEPSEEK_BASE}/chat/completions",
                json={"model":"deepseek-v4-flash","messages":[{"role":"user","content":prompt}],"temperature":0.3,"max_tokens":300,"thinking":{"type":"disabled"}},
                headers={"Authorization":f"Bearer {DEEPSEEK_KEY}","Content-Type":"application/json"},
                timeout=aiohttp.ClientTimeout(10)) as r:
                data = await r.json()
                resp = data["choices"][0]["message"]["content"]
                start = resp.find('{')
                end = resp.rfind('}') + 1
                if start >= 0 and end > start: return json.loads(resp[start:end])
    except Exception as e:
        logger.error(f"Vocab improve error: {e}")
    return {"suggestions": []}

# ── Realtime Pipeline Handler (Qwen Omni) ──
async def handle_realtime(ws: WebSocket, sid: str, session: dict, mode: str, api_key: str):
    """管线2 · Qwen-Omni Realtime 语音对话"""
    from pipeline_qwen_omni import QwenOmniBridge
    import subprocess, tempfile as _tempfile

    bridge = QwenOmniBridge(qwen_api_key=api_key, mode=mode)
    history_texts = []

    def _pcm24k_to_mp3(pcm_data: bytes) -> str:
        if not pcm_data: return ""
        pcm_path = None; mp3_path = None
        try:
            with _tempfile.NamedTemporaryFile(suffix='.pcm', delete=False) as f:
                f.write(pcm_data); pcm_path = f.name
            mp3_path = pcm_path + '.mp3'
            r = subprocess.run(['ffmpeg','-y','-f','s24le','-ar','24000','-ac','1',
                               '-i',pcm_path,'-c:a','libmp3lame','-b:a','64k',mp3_path],
                              capture_output=True, timeout=5)
            if r.returncode == 0 and os.path.exists(mp3_path):
                with open(mp3_path,'rb') as f:
                    return base64.b64encode(f.read()).decode()
        except: pass
        finally:
            for p in [pcm_path, mp3_path]:
                try: os.unlink(p) if p else None
                except: pass
        return ""

    tracker = None
    if debug_manager:
        tracker = debug_manager.create_tracker(sid, mode, "realtime")

    try:
        await bridge.client.connect()
        logger.info(f"Qwen-Omni connected: {sid}")

        # Pre-defined greeting
        greet = GREETINGS.get(mode, GREETINGS["ielts_part1"])
        await ws.send_json({"type": "response_text", "text": greet})
        await ws.send_json({"type": "status", "state": "speaking"})
        greet_audio = await tts_speak(greet)
        if greet_audio:
            await ws.send_json({"type": "audio", "data": greet_audio})
        await ws.send_json({"type": "status", "state": "done"})

        audio_buf = []  # Accumulate raw PCM chunks
        responding = False
        while True:
            msg = await ws.receive_json()
            t = msg.get("type")

            if t == "audio":
                if responding: continue
                chunk = base64.b64decode(msg.get("data", ""))
                audio_buf.append(chunk)
                if tracker: await tracker.record_audio_chunk(len(chunk))

            elif t == "flush":
                if not audio_buf or responding: continue
                responding = True
                full_pcm = b"".join(audio_buf)
                n_chunks = len(audio_buf)
                audio_buf = []
                logger.info(f"Qwen flush: {n_chunks} chunks, {len(full_pcm)} bytes ({len(full_pcm)/32:.0f}ms)")

                if tracker: await tracker.start_turn()
                await ws.send_json({"type": "status", "state": "thinking"})

                # Send audio to Qwen in chunks, then commit+request
                try:
                    await bridge.handle_audio(full_pcm)
                    await bridge.client.commit_audio()
                    await bridge.client.request_response()
                except Exception as e:
                    logger.error(f"Qwen send/commit error: {e}")
                    await ws.send_json({"type": "error", "msg": "Qwen connection error, please try again"})
                    responding = False
                    continue

                t0 = time.time()
                full_text = ""
                full_audio_pcm = b""

                try:
                    async for event in bridge.client.receive_response():
                        et = event.get("type","")
                        if et == "text_delta" or et == "text":
                            full_text += event.get("data","")
                            await ws.send_json({"type": "response_text", "text": full_text})
                        elif et == "audio_delta" or et == "audio":
                            full_audio_pcm += base64.b64decode(event.get("data",""))
                        elif et == "response_text" or et == "text_done":
                            ft = event.get("text","") or event.get("transcript","")
                            if ft: full_text = ft
                        elif et == "error":
                            logger.error(f"Qwen error: {event}")
                        elif et == "user_transcript":
                            ut = event.get("transcript","")
                            if ut:
                                await ws.send_json({"type": "final_transcript", "text": ut})
                                history_texts.append(ut)
                except Exception as e:
                    logger.error(f"Qwen response error: {e}")

                e2e = (time.time() - t0) * 1000

                if full_text:
                    await ws.send_json({"type": "response_text", "text": full_text})
                    history_texts.append(full_text)

                if full_audio_pcm:
                    await ws.send_json({"type": "status", "state": "speaking"})
                    mp3_b64 = _pcm24k_to_mp3(full_audio_pcm)
                    if mp3_b64:
                        await ws.send_json({"type": "audio", "data": mp3_b64})
                    else:
                        await ws.send_json({"type": "audio_pcm", "data": base64.b64encode(full_audio_pcm).decode(), "sampleRate": 24000})

                await ws.send_json({"type": "status", "state": "done"})

                if tracker:
                    await tracker.record_asr(full_text[:80] if full_text else "", 1.0, 0, model="qwen-omni-realtime")
                    await tracker.record_llm("realtime", full_text[:120], e2e, model="qwen3.5-omni-flash")
                    await tracker.record_tts("qwen-audio", e2e, voice="Ethan")
                    await tracker.complete_turn()

                responding = False
                logger.info(f"Qwen response: e2e={e2e:.0f}ms, text={full_text[:60]}")

            elif t == "evaluate_final":
                if not history_texts:
                    await ws.send_json({"type": "score", "scores": {"overall": 0, "summary": "No speech detected."}})
                    continue
                all_text = "\n---\n".join(history_texts[-10:])
                await ws.send_json({"type": "status", "state": "evaluating"})
                sys_prompt = """You are an IELTS examiner. Evaluate and return ONLY JSON:
{"fluency":X.X, "vocabulary":X.X, "grammar":X.X, "pronunciation":X.X, "overall":X.X,
 "summary":"2-3 sentence assessment",
 "improvements":["You said ~~wrong~~ \u2192 **correct** \u2014 why"],
 "highlights":["Good ``word`` \u2192 **better** \u2014 why"]}"""
                r = await ds_chat([{"role":"system","content":sys_prompt},
                                   {"role":"user","content":f"Evaluate:\n{all_text}"}],
                                  max_tokens=600, temp=0.3)
                try:
                    sc = json.loads(r)
                    await ws.send_json({"type": "score", "scores": sc})
                    logger.info(f"Qwen final: overall={sc.get('overall')}")
                except:
                    logger.error(f"Qwen score parse: {r[:80]}")

            elif t == "stop":
                break

    except WebSocketDisconnect:
        logger.info(f"Realtime session {sid} ended")
    except Exception as e:
        logger.exception(f"Realtime session {sid}: {e}")
        try: await ws.send_json({"type": "error", "msg": str(e)})
        except: pass
    finally:
        await bridge.close()
        session["status"] = "ended"
        if tracker: tracker.end_session()

# ── WebSocket ──
# ── Free Talk 持久记忆 (v1.4.0, 2026-08-15) ──
# 方案: 单条持久会话 + 256K 上下文窗口 + 超限压缩摘要 (双层记忆)
#   v4-flash 原生 1M 上下文, 主动压到 256K: 成本/延迟/注意力质量更好
#   原文全量留 SQLite (真相源), 压缩摘要只影响喂给模型的视图
FT_MAX_TOKENS = 256_000      # 上下文硬上限
FT_COMPACT_AT = 230_000      # 触发压缩的软阈值 (留余量给当前会话+输出)
FT_WINDOW_RESERVE = 8_192    # 窗口裁剪时给摘要+新会话留的余量
FT_RECAP_MAX_TOKENS = 2_500  # 摘要输出上限


def _count_tokens(text: str) -> int:
    """保守估算 tokens: 中文字符≈1 token/字, 英文略高估 → 只早压不超限"""
    return len(text) if text else 0


def _trim_to_window(msgs, max_tokens):
    """从尾部保留最近 max_tokens 的消息 (保持时间顺序)"""
    total = 0
    kept = []
    for m in reversed(msgs):
        total += _count_tokens(m.get("text", "")) + 8
        if total > max_tokens:
            break
        kept.append(m)
    kept.reverse()
    if not kept and msgs:  # 防边界: 单条超预算时至少保留最近一条, 不丢上下文
        kept = [msgs[-1]]
    return kept


def _qb_system_extra(pick):
    """v1.4.1: 把抽到的题注入 system prompt — 种子保真, LLM 负责自然展开"""
    if pick["mode"] == "ielts_part1":
        return (f"\n\nCURRENT TOPIC: {pick['topic']}.\n"
                "Seed questions for this topic — ask them naturally one at a time, react to answers, "
                "follow up deeply before moving on:\n- " + "\n- ".join(pick["questions"]))
    if pick["mode"] == "ielts_part2":
        s = f"\n\nTOPIC CARD: {pick['title']}\nYou should say:\n- " + "\n- ".join(pick["prompts"])
        if pick.get("follow_ups"):
            s += "\nAfter the candidate finishes, ask 1-2 natural follow-ups:\n- " + "\n- ".join(pick["follow_ups"])
        return s
    if pick["mode"] == "ielts_part3":
        return (f"\n\nCURRENT THEME: {pick['theme']}.\n"
                "Ask these questions one at a time, follow up on answers with deeper questions, "
                "challenge ideas respectfully:\n- " + "\n- ".join(pick["questions"]))
    return ""


async def _hydrate_ft_history(sid, history):
    """Free Talk 持久记忆灌回: [system+摘要] + 最近 256K 原文; 超软阈值→后台触发压缩"""
    mem = sessions.get_ft_memory()
    rows = sessions.get_ft_transcripts(sid)
    if not rows and not (mem and mem.get("recap")):
        return False, history
    system = history[0]["content"]
    if mem and mem.get("recap"):
        system += ("\n\n=== LONG-TERM MEMORY (compressed from earlier conversations) ===\n"
                   + mem["recap"] + "\n=== END MEMORY ===")
        history = [{"role": "system", "content": system}]
    since = (mem or {}).get("compacted_seq", -1)
    recent = [r for r in rows if r["seq"] > since]
    recap_tokens = (mem or {}).get("recap_tokens", 0) or 0
    budget = max(16_384, FT_MAX_TOKENS - recap_tokens - FT_WINDOW_RESERVE)
    recent = _trim_to_window(recent, budget)
    for r in recent:
        history.append({"role": "user" if r["speaker"] == "user" else "assistant", "content": r["text"]})
    total = sum(_count_tokens(m.get("content", "")) for m in history)
    if total > FT_COMPACT_AT:
        logger.info(f"FT: context {total} tokens > {FT_COMPACT_AT}, spawning compaction")
        asyncio.create_task(_compact_ft_memory(sid, history))
    return True, history


async def _compact_ft_memory(sid, history):
    """把最老一段原文压缩进长期记忆摘要; 幂等 (按 compacted_seq 推进)"""
    try:
        mem = sessions.get_ft_memory() or {}
        since = mem.get("compacted_seq", -1)
        rows = sessions.get_ft_transcripts(sid, after_seq=since)
        if not rows:
            return
        # 待压缩: 从最老开始, 累计到软阈值 60% 为止
        budget = int(FT_COMPACT_AT * 0.6)
        total = 0
        to_compact = []
        for r in rows:
            to_compact.append(r)
            total += _count_tokens(r["text"])
            if total >= budget:
                break
        if not to_compact:
            return
        transcript = "\n".join(f"{'User' if r['speaker'] == 'user' else 'Tutor'}: {r['text']}" for r in to_compact)
        old_recap = (mem or {}).get("recap") or ""
        if old_recap:
            prompt = ("You maintain long-term memory notes for an English conversation partner app.\n\n"
                      "EXISTING MEMORY NOTES:\n" + old_recap + "\n\n"
                      "NEW CONVERSATION TO FOLD IN:\n" + transcript + "\n\n"
                      "Merge the new conversation into the memory notes. Preserve facts about the user "
                      "(job, family, hometown, hobbies, plans, preferences), opinions and stances, stories, "
                      "recurring topics, emotional hotspots, unfinished threads, important dates/names. "
                      "Keep it chronological, concise bullet notes. Output ONLY the merged notes, no preamble.")
        else:
            prompt = ("You are maintaining a long-term memory for an English conversation partner app. "
                      "Below is a conversation transcript. Compress it into dense memory notes — the ONLY "
                      "future record of it. Preserve: facts about the user (job, family, hometown, hobbies, "
                      "plans, preferences), opinions and stances, stories told (key details), recurring topics, "
                      "emotional hotspots, unfinished threads, important dates/names. Concise chronological "
                      "bullet notes. Output ONLY the notes, no preamble.\n\nTRANSCRIPT:\n" + transcript)
        recap = await ds_chat([{"role": "system", "content": prompt}], max_tokens=FT_RECAP_MAX_TOKENS, temp=0.3)
        if not recap or len(recap.strip()) < 20:
            logger.warning("FT compact: empty recap, skip")
            return
        sessions.save_ft_recap(None, recap.strip(), to_compact[-1]["seq"], _count_tokens(recap))
        logger.info(f"FT compact done: {len(to_compact)} msgs folded, recap {len(recap)} chars")
    except Exception as e:
        logger.error(f"FT compact failed: {e}")


@app.websocket("/ws/chat/{sid}")
async def ws_chat(ws: WebSocket, sid: str):
    await ws.accept()
    session = sessions.get(sid)
    if not session:
        await ws.send_json({"type": "error", "msg": "session not found"}); await ws.close(); return

    mode = session.get("mode", "ielts_part1")
    pipeline = session.get("pipeline", "cascade")

    # v1.4.1: 题库抽题 (Part1/2/3) — 已抽的存 session, 服务重启后重新抽 (可接受)
    qb_pick = session.get("qb_pick")
    if mode in ("ielts_part1", "ielts_part2", "ielts_part3") and not qb_pick:
        qb_pick = question_bank.safe_pick(mode)
        if qb_pick:
            session["qb_pick"] = qb_pick

    if pipeline == "realtime":
        from pipeline_qwen_omni import QwenOmniBridge
        from config import QWEN_OMNI_KEY
        if not QWEN_OMNI_KEY:
            logger.warning(f"Qwen key not configured, falling back to cascade")
            pipeline = "cascade"
        else:
            await handle_realtime(ws, sid, session, mode, QWEN_OMNI_KEY)
            return

    audio_buf = b""
    last_speech_time = time.time()
    transcriber = StreamingTranscriber()  # streaming STT — model loaded once
    history = [{"role": "system", "content": SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["free_talk"])}]
    if qb_pick:
        history[0]["content"] += _qb_system_extra(qb_pick)  # v1.4.1 题库种子注入
    user_texts = []

    # v1.4.0: Free Talk 持久记忆 — 从 DB 灌回 256K 窗口 + 压缩摘要
    ft_resumed = False
    if mode == "free_talk":
        ft_resumed, history = await _hydrate_ft_history(sid, history)

    # Debug tracker
    tracker = None
    if debug_manager:
        tracker = debug_manager.create_tracker(sid, mode, "cascade")

    def _audio_energy(chunk: bytes) -> float:
        """计算 PCM16 音频片的 RMS 能量，用于区分人声和杂音"""
        import struct
        if len(chunk) < 2: return 0
        samples = [abs(struct.unpack('<h', chunk[i:i+2])[0]) for i in range(0, len(chunk)-1, 2)]
        if not samples: return 0
        return (sum(s*s for s in samples) / len(samples)) ** 0.5

    async def send_tts(text):
        """合成并发送 TTS 音频（并行逐句合成）"""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\\s+', text) if s.strip()]
        if not sentences: return
        tasks = [asyncio.create_task(tts_speak(s)) for s in sentences]
        for task in tasks:
            try:
                audio = await task
                if audio:
                    await ws.send_json({"type": "audio", "data": audio})
            except Exception as e:
                logger.warning(f"TTS task failed: {e}")

    def _extract_sentence(buf):
        """Extract first complete sentence from streaming buffer.
        Returns (sentence, remaining) or (None, buf) if incomplete."""
        m = re.search(r'(.+?[.!?])\s+', buf)
        if m:
            return m.group(1).strip(), buf[m.end():]
        # Fallback: flush if >100 chars accumulated without punctuation
        if len(buf) > 100 and ' ' in buf:
            return buf.strip(), ""
        return None, buf

    async def process_utterance():
        nonlocal audio_buf
        if len(audio_buf) < 3200: return
        if tracker: await tracker.start_turn()
        data = audio_buf; audio_buf = b""
        stt_t0 = time.time()
        # ── Streaming STT: single-pass with segment callbacks for partial display ──
        partial_sent = set()
        def on_segment(seg_text: str):
            """Send partial transcript to client as each segment is recognized."""
            if seg_text and seg_text not in partial_sent:
                partial_sent.add(seg_text)
                asyncio.ensure_future(ws.send_json({"type": "partial_transcript", "text": seg_text}))
        
        text, conf = transcriber.transcribe(on_partial=on_segment)
        transcriber.reset()  # clear buffer for next utterance
        if tracker: await tracker.record_asr(text, conf, (time.time()-stt_t0)*1000, model="faster-whisper-small.en")
        if not text or len(text.strip()) < 2: return
        # free_talk模式: 过滤STT碎片 (2026-07-22)
        if mode == "free_talk":
            stripped = text.strip()
            fillers = {"you","oh","um","uh","ah","yeah","yep","yes","no","ok","okay",
                      "hmm","mm","um-hmm","uh-huh","bye","goodbye","thanks","thank you",
                      "sorry","sorry.","oh.","oh,","no.","no,","wait","wait a minute"}
            if stripped.lower().rstrip('.,!?') in fillers:
                logger.info(f"STT[filter]: filler → '{stripped[:40]}'")
                return
            if len(stripped) < 25 and not re.search(r'[.!?]$', stripped):
                logger.info(f"STT[filter]: fragment → '{stripped[:40]}'")
                return
        logger.info(f"STT: {text[:80]} (conf={conf:.2f})")
        
        user_texts.append(text)
        await ws.send_json({"type": "final_transcript", "text": text})
        if mode == "free_talk":
            try:
                sessions.add_transcript(sid, "user", text)  # v1.4.0 持久记忆落库
            except Exception as e:
                logger.warning(f"FT persist user failed: {e}")
        # 保留完整原文 — 雅思评估需要语言细节，不摘要
        history.append({"role": "user", "content": text})
        cost_stats["ds_input"] += sum(len(m.get("content","")) for m in history) // 3
        # v1.4.0: Free Talk 不截断 (持久上下文靠 256K 窗口+压缩管理); 其他模式保持 18 条截断
        if mode != "free_talk" and len(history) > 18: history[:] = [history[0]] + history[-14:]

        # ── LLM+TTS Interleaved Streaming ──
        full = ""
        pending = ""
        tts_sentences = []  # (task, sentence) pairs for ordered delivery
        llm_t0 = time.time()
        first_audio_sent = False
        
        # 动态 max_tokens：延迟优化 P1 (2026-07-15) 上限 800→450
        # 陪练对话回复本就该短，更快出声更快说完; 可调: export IELTS_LLM_MAX_TOKENS=800
        _mt_cap = int(os.environ.get("IELTS_LLM_MAX_TOKENS", "450"))
        input_len = sum(len(m.get("content","")) for m in history)
        dynamic_mt = min(_mt_cap, 250 + input_len // 6)
        async for token in ds_stream(history, max_tokens=dynamic_mt):
            full += token
            pending += token
            # Extract complete sentences → fire TTS immediately
            sentence, pending = _extract_sentence(pending)
            while sentence:
                tts_sentences.append((asyncio.create_task(tts_speak(sentence)), sentence))
                sentence, pending = _extract_sentence(pending)
        
        # Flush remaining text
        if pending.strip():
            tts_sentences.append((asyncio.create_task(tts_speak(pending.strip())), pending.strip()))
        
        llm_elapsed = (time.time() - llm_t0) * 1000
        if tracker: await tracker.record_llm("general_chat", full, llm_elapsed)
        
        if not full:
            logger.warning(f"DS returned empty, sending fallback message")
            full = "I'm sorry, I didn't quite catch that. Could you say it again?"
            tts_sentences = [(asyncio.create_task(tts_speak(full)), full)]

        # Stream text to client
        await ws.send_json({"type": "response_text", "text": full})
        cost_stats["ds_output"] += len(full) // 3
        history.append({"role": "assistant", "content": full})
        if mode == "free_talk":
            try:
                sessions.add_transcript(sid, "tutor", full)  # v1.4.0 持久记忆落库
            except Exception as e:
                logger.warning(f"FT persist tutor failed: {e}")
        
        # Deliver TTS audio — first chunk determines TTFA
        await ws.send_json({"type": "status", "state": "speaking"})
        tts_t0 = time.time()
        for task, _ in tts_sentences:
            try:
                audio = await task
                if audio:
                    if not first_audio_sent:
                        first_audio_sent = True
                        tfa_ms = (time.time() - stt_t0) * 1000
                        logger.info(f"Pipeline1 TTFA: STT→{tfa_ms:.0f}ms | LLM:{llm_elapsed:.0f}ms | sentences:{len(tts_sentences)}")
                    await ws.send_json({"type": "audio", "data": audio})
            except Exception as e:
                logger.warning(f"TTS task failed: {e}")
        if tracker: await tracker.record_tts(full, (time.time()-tts_t0)*1000)
        await ws.send_json({"type": "status", "state": "done"})
        if tracker: await tracker.complete_turn()

    # Greeting — Free Talk 恢复历史时用欢迎回来, 不重复寒暄 (v1.4.0)
    if mode == "free_talk" and ft_resumed:
        greet = "Welcome back! I remember what we talked about before — shall we pick up where we left off, or is there something new on your mind?"
    elif mode == "ielts_part2" and qb_pick:
        # v1.4.1: 题库抽卡 — 不再固定 book 卡
        greet = ("Now I'm going to give you a topic. You should talk about it for 1 to 2 minutes. "
                 "Before you talk, you'll have 1 minute to prepare. Here is your topic: "
                 f"{qb_pick['title']}. You should say:\n- " + "\n- ".join(qb_pick["prompts"]))
    elif mode == "ielts_part3" and qb_pick:
        greet = "Now let's talk about some more general questions. " + qb_pick["questions"][0]
    else:
        greet = GREETINGS.get(mode, GREETINGS["ielts_part1"])
    await ws.send_json({"type": "response_text", "text": greet})
    await ws.send_json({"type": "status", "state": "speaking"})
    await send_tts(greet)
    await ws.send_json({"type": "status", "state": "done"})

    current_task = None

    try:
        while True:
            msg = await ws.receive_json()
            t = msg.get("type")

            # Interrupt in-progress utterance when stopping/evaluating
            if t in ("evaluate_final", "stop") and current_task and not current_task.done():
                current_task.cancel()
                try: await current_task
                except asyncio.CancelledError: pass
                processing_utt = False

            if t == "audio":
                chunk = base64.b64decode(msg.get("data", ""))
                audio_buf += chunk
                # ── Feed audio to streaming transcriber ──
                transcriber.feed(chunk)
                if tracker: await tracker.record_audio_chunk(len(chunk))
                # Energy-based speech detection: 只更新人声时间，忽略环境杂音
                energy = _audio_energy(chunk)
                if energy > SPEECH_ENERGY_THRESHOLD:
                    last_speech_time = time.time()
                # Buffer overflow protection (长句友好: 软上限等停顿, 硬上限才强切)
                buf_len = len(audio_buf)
                if buf_len > AUDIO_BUF_HARD_LIMIT:
                    logger.warning(f"Audio buffer hard-limit: {buf_len} bytes ({buf_len/32000:.1f}s), force-flushing")
                    current_task = asyncio.create_task(process_utterance())
                    try:
                        await current_task
                    except asyncio.CancelledError:
                        pass
                elif buf_len > AUDIO_BUF_SOFT_LIMIT and (time.time() - last_speech_time) > AUDIO_BUF_FLUSH_SILENCE:
                    logger.info(f"Audio buffer soft-limit at speech gap: {buf_len} bytes ({buf_len/32000:.1f}s), flushing at pause")
                    current_task = asyncio.create_task(process_utterance())
                    try:
                        await current_task
                    except asyncio.CancelledError:
                        pass
                # Endpointing: silence > 3s → auto-flush (可通过环境变量关闭)
                if ENDPOINT_ENABLED:
                    silence_dur = time.time() - last_speech_time
                    if len(audio_buf) >= 3200 and silence_dur > ENDPOINT_MAX_SILENCE:
                        logger.info(f"Endpointing: {silence_dur:.1f}s silence, auto-flushing ({len(audio_buf)/32000:.1f}s audio)")
                        current_task = asyncio.create_task(process_utterance())
                        try:
                            await current_task
                        except asyncio.CancelledError:
                            pass

            elif t == "flush":
                current_task = asyncio.create_task(process_utterance())
                try:
                    await current_task
                except asyncio.CancelledError:
                    logger.info(f"Utterance cancelled for evaluation")
                    await ws.send_json({"type": "status", "state": "evaluating"})
                processing_utt = False

            elif t == "evaluate_final":
                logger.info(f"EVALUATE: {len(user_texts)} texts, history={len(history)}")
                if not user_texts:
                    await ws.send_json({"type": "score", "scores": {"overall": 0, "summary": "No speech detected. Try speaking more during the conversation."}})
                    continue
                all_text = "\n---\n".join(user_texts[-10:])
                sys_prompt = """You are an IELTS examiner. Evaluate the conversation and return ONLY JSON:
{
  "fluency":X.X, "vocabulary":X.X, "grammar":X.X, "pronunciation":X.X, "overall":X.X,
  "summary":"2-3 sentence overall assessment",
  "improvements":[
    "You said ~~wrong phrase~~ → **corrected version** — brief explanation",
    ...
  ],
  "highlights":[
    "Good use of ``natural expression`` → **Even better: more advanced variant** — why it's stronger",
    ...
  ]
}

FORMAT RULES:
- improvements: Use ~~double tildes~~ to mark WRONG text, **double stars** to mark CORRECTED text, then → **suggestion** for better version. Include brief explanation after.
- highlights: Use ``double backticks`` to mark the user's good expression, then → **better expression** with why it elevates their English.
- Provide 2-4 improvements and 2-3 highlights.
- Focus on actionable fixes, not just praise."""
                r = await ds_chat([{"role":"system","content":sys_prompt},
                                   {"role":"user","content":f"Evaluate this conversation:\n{all_text}"}],
                                  max_tokens=600, temp=0.3)
                # Extract JSON from markdown code block if present
                import re as _re2
                _m = _re2.search(r'```(?:json)?\s*\n?(.*?)\n?```', r, _re2.DOTALL)
                if _m: r = _m.group(1).strip()
                try:
                    sc = json.loads(r)
                except json.JSONDecodeError:
                    logger.warning(f"EVALUATE: JSON parse failed, response: {r[:100]}...")
                    await ws.send_json({"type": "score", "scores": {"overall": 0, "summary": "Evaluation failed. Please try again.", "improvements": [], "highlights": []}})
                    continue
                try:
                    logger.info(f"EVALUATE: parsed, overall={sc.get('overall','?')}")
                    # Generate HTML report
                    report_data = {
                        "session_id": sid,
                        "mode": mode,
                        "transcripts": [{"speaker": "user", "text": t, "time": ""} for t in user_texts] + \
                                      [{"speaker": "tutor", "text": m["content"], "time": ""} for m in history if m["role"] == "assistant"],
                        "created": datetime.now()
                    }
                    try:
                        report_path = generate_report(report_data, sc)
                        sc["report_path"] = report_path
                    except Exception as e:
                        logger.error(f"Report gen failed: {e}")
                    
                    session["last_score"] = sc  # HTTP fallback 缓存 (问题3修复)
                    # v1.1.0 M1: 评估落库 + 自动灌跟读队列（修复: 此前从未调用 save_evaluation）
                    try:
                        sessions.save_evaluation(sid, sc, report_path=sc.get("report_path"))
                    except Exception as e:
                        logger.error(f"save_evaluation failed: {e}")
                    try:
                        await ws.send_json({"type": "score", "scores": sc})
                        logger.info(f"Final: overall={sc.get('overall')}")
                    except Exception:
                        logger.warning(f"Score push failed (WS closed), cached for /api/session/{sid}/score")
                except:
                    logger.debug(f"Score fail: {r[:80]}")

            elif t == "stop":
                break

    except WebSocketDisconnect:
        logger.info(f"Session {sid} ended")
    except Exception as e:
        logger.exception(f"Session {sid}")
        try: await ws.send_json({"type": "error", "msg": str(e)})
        except: pass
    finally:
        # Auto-evaluate on disconnect if user had meaningful conversation (≥10 turns)
        if user_texts and len(user_texts) >= 10:
            try:
                logger.info(f"AUTO-EVAL: {sid} {len(user_texts)} texts")
                all_text = "\n---\n".join(user_texts[-10:])
                sys_prompt = '{"fluency":X.X,"vocabulary":X.X,"grammar":X.X,"pronunciation":X.X,"overall":X.X,"summary":"...","improvements":["You said ~~wrong~~ → **correct** — why"],"highlights":["Good ``word`` → **better** — why"]}'
                eval_msg = [{"role":"system","content":"You are an IELTS examiner. Evaluate and output ONLY valid JSON. Format: " + sys_prompt},
                           {"role":"user","content":f"Evaluate this conversation:\n{all_text}"}]
                r = await ds_chat(eval_msg, max_tokens=600, temp=0.3)
                # Extract JSON from response (handle markdown code blocks, partial JSON)
                import re as _re
                _json_match = _re.search(r'```(?:json)?\s*\n?(.*?)\n?```', r, _re.DOTALL)
                if _json_match:
                    r = _json_match.group(1).strip()
                try:
                    sc = json.loads(r)
                except json.JSONDecodeError:
                    sc = {"overall": 0, "summary": "Evaluation unavailable. Please try again.", "improvements": [], "highlights": []}
                session["last_score"] = sc  # HTTP fallback 缓存 (问题3修复)
                # v1.1.0 M1: 断线自动评估同样落库+灌队列
                try:
                    if sc.get("overall"):
                        sessions.save_evaluation(sid, sc)
                except Exception as e:
                    logger.error(f"AUTO-EVAL save_evaluation failed: {e}")
                try: await ws.send_json({"type": "score", "scores": sc})
                except: logger.warning(f"AUTO-EVAL: client disconnected, score cached for /api/session/{sid}/score")
                logger.info(f"AUTO-EVAL: score={sc.get('overall')}")
            except Exception as e:
                logger.error(f"AUTO-EVAL failed: {e}")
        session["status"] = "ended"
        if tracker: tracker.end_session()
        
        # v1.4: 保存上轮最后5轮对话，供下一Session回显 (Daryl 2026-07-22 需求)
        if user_texts and history:
            try:
                _save_last_turns(mode, history)
            except Exception as e:
                logger.warning(f"save_last_turns failed: {e}")

# ── Last Turns Persistence (v1.4) ──
import threading as _threading
_last_turns_lock = _threading.Lock()

def _get_last_turns_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "last_turns.json")

def _save_last_turns(mode, history):
    """保存每个 mode 最后5轮对话（10条消息）"""
    # Extract last 10 messages (5 user + 5 assistant pairs) excluding system
    msgs = [m for m in history if m.get("role") != "system"]
    last10 = msgs[-10:] if len(msgs) >= 10 else msgs
    
    with _last_turns_lock:
        path = _get_last_turns_path()
        data = {}
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
            except: pass
        data[mode] = {"turns": last10, "saved_at": datetime.now().isoformat()}
        with open(path, 'w') as f:
            json.dump(data, f, ensure_ascii=False)

@app.get("/api/session/last-turns")
async def get_last_turns(mode: str = "free_talk"):
    """返回上轮最后5轮对话，供新Session回显"""
    path = _get_last_turns_path()
    if not os.path.exists(path):
        return {"turns": []}
    try:
        with open(path) as f:
            data = json.load(f)
        return {"turns": data.get(mode, {}).get("turns", []), "mode": mode, "saved_at": data.get(mode, {}).get("saved_at", "")}
    except:
        return {"turns": []}

# ── Debug API Routes (DEBUG_MODE=1 only) ──
if debug_manager:
    @app.get("/debug/sessions")
    async def debug_sessions(limit: int = 30):
        return {"sessions": await handle_debug_list(limit)}

    @app.get("/debug/export/{sid}")
    async def debug_export(sid: str):
        data = await handle_debug_export(sid)
        if not data: return {"error": "Session not found"}
        return data

    @app.get("/debug/turns/{sid}")
    async def debug_turns(sid: str, limit: int = 5):
        """HTTP polling endpoint — 返回最近 N 轮数据，供平板等 WebSocket 不通的设备使用"""
        data = debug_manager.export_session(sid)
        if not data.get("summary"):
            return {"error": "Session not found"}
        all_turns = data.get("turns", [])
        recent = all_turns[-limit:] if len(all_turns) > limit else all_turns
        return {
            "session_id": sid,
            "total_turns": len(all_turns),
            "avg_e2e_ms": data["summary"].get("avg_e2e_ms", 0),
            "turns": recent
        }

    @app.websocket("/debug/ws/{sid}")
    async def debug_ws(ws: WebSocket, sid: str):
        await handle_debug_ws(ws, sid)

@app.get("/login")
async def login_page():
    return HTMLResponse(open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "login.html"), encoding="utf-8").read())


# ── Auth API (v1.5.0 P1: 增量式, AUTH_REQUIRED=0 默认 guest, 不影响现有路由) ──
def _bearer(req: Request):
    h = req.headers.get("Authorization", "")
    return h[7:] if h.lower().startswith("bearer ") else ""


def _client_ip(req: Request):
    return req.client.host if req.client else "local"


@app.post("/api/auth/register")
async def auth_register(req: Request):
    body = await req.json()
    ok, res = auth.register(body.get("email", ""), body.get("password", ""),
                            body.get("display_name", ""), _client_ip(req))
    if ok:
        return {"ok": True, "user": res["user"], "token": res["token"]}
    return {"ok": False, "error": res}


@app.post("/api/auth/login")
async def auth_login(req: Request):
    body = await req.json()
    ok, res = auth.login(body.get("email", ""), body.get("password", ""), _client_ip(req))
    if ok:
        return {"ok": True, "user": res["user"], "token": res["token"]}
    return {"ok": False, "error": res}


@app.post("/api/auth/logout")
async def auth_logout(req: Request):
    auth.logout(_bearer(req))
    return {"ok": True}


@app.get("/api/auth/me")
async def auth_me(req: Request):
    u = auth.get_user_by_token(_bearer(req))
    if not u:
        return {"ok": False, "error": "未登录或登录已过期"}
    return {"ok": True, "user": u}


# ── Cost Endpoint ──
# DeepSeek 费率参数（2026-08-15 更新，官方公告 2026-08-13）
# 本服务使用模型: deepseek-v4-flash
#   现行费率 (至 2026-08-16 15:59 UTC): 输入 $0.14/1M, 输出 $0.28/1M
#   新费率 (2026-08-16 16:00 UTC 起, 峰谷计价):
#     off-peak: 输入 $0.22/1M, 输出 $0.66/1M
#     peak:     输入 $0.44/1M, 输出 $1.32/1M
#   峰值时段: 01:00-04:00 与 06:00-10:00 (UTC)
DS_PRICE_CHANGE_UTC = datetime(2026, 8, 16, 16, 0, tzinfo=timezone.utc)


def ds_rates(now=None):
    """返回当前 deepseek-v4-flash 单价 (input, output) — $/1M tokens"""
    now = now or datetime.now(timezone.utc)
    if now < DS_PRICE_CHANGE_UTC:
        return (0.14, 0.28)
    h = now.hour
    if (1 <= h < 4) or (6 <= h < 10):
        return (0.44, 1.32)
    return (0.22, 0.66)


@app.get("/api/costs")
async def api_costs():
    """成本核算
    TTS: 本地 Kokoro-82M — 免费
    STT: 本地 whisper.cpp — 免费
    LLM: deepseek-v4-flash — 峰谷计价 (2026-08-16 16:00 UTC 生效)
         off-peak: $0.22/1M in, $0.66/1M out | peak: $0.44/1M in, $1.32/1M out"""
    r_in, r_out = ds_rates()
    total = (
        cost_stats["ds_input"] * r_in / 1_000_000
        + cost_stats["ds_output"] * r_out / 1_000_000
    )
    return {
        "total": round(total, 6),
        "session_count": len(sessions),
        "rates": {
            "model": "deepseek-v4-flash",
            "input_per_1m": r_in,
            "output_per_1m": r_out,
            "peak_hours_utc": "01:00-04:00, 06:00-10:00",
            "checked_at": datetime.now(timezone.utc).isoformat(),
        },
        "breakdown": {
            "ds_input_tokens": cost_stats["ds_input"],
            "ds_output_tokens": cost_stats["ds_output"],
            "ds_cost": round(total, 6),
            "stt_calls": cost_stats["stt_calls"],
            "stt_cost": 0,
            "tts_calls": cost_stats["tts_calls"],
            "tts_cost": 0,
        }
    }

if __name__ == "__main__":
    _prewarm_models()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8767)), log_level="info")
