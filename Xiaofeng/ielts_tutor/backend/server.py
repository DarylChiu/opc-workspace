"""
IELTS Tutor v2.0 - Server · PTT模式 + 最终评估
"""
import os, json, logging, asyncio, uuid, base64, time, re
from datetime import datetime
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
FRONTEND = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")

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
    "free_talk": """You are a friendly English conversation partner. Chat naturally about any topic. Respond with 2-4 sentences. When you notice a grammar error, gently correct it once: 'By the way, we usually say...' Be warm and curious. Ask follow-up questions.""",
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
    b = {"model": "deepseek-chat", "messages": messages, "temperature": temp, "max_tokens": max_tokens}
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
    b = {"model": "deepseek-chat", "messages": messages, "temperature": 0.7, "max_tokens": max_tokens, "stream": True}
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

@app.get("/api/health")
async def health():
    ver = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")).read().strip()
    return {"status": "ok", "version": ver, "costs": cost_stats}

@app.post("/api/session/start")
async def start(req: Request):
    body = await req.json()
    sid = str(uuid.uuid4())[:8]
    sessions.create(sid, mode=body.get("mode", "ielts_part1"),
                pipeline=body.get("pipeline", "cascade"))
    return {"session_id": sid, "mode": body.get("mode", "ielts_part1")}

@app.get("/api/session/{sid}/score")
async def get_session_score(sid: str):
    """HTTP fallback: WS断开时前端轮询取评估结果 (2026-07-15 问题3修复)"""
    session = sessions.get(sid)
    if not session:
        return {"status": "not_found"}
    sc = session.get("last_score")
    if sc:
        return {"status": "ready", "scores": sc}
    return {"status": "pending"}

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
@app.websocket("/ws/chat/{sid}")
async def ws_chat(ws: WebSocket, sid: str):
    await ws.accept()
    session = sessions.get(sid)
    if not session:
        await ws.send_json({"type": "error", "msg": "session not found"}); await ws.close(); return

    mode = session.get("mode", "ielts_part1")
    pipeline = session.get("pipeline", "cascade")

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
    user_texts = []

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
        logger.info(f"STT: {text[:80]} (conf={conf:.2f})")
        
        user_texts.append(text)
        await ws.send_json({"type": "final_transcript", "text": text})
        # 保留完整原文 — 雅思评估需要语言细节，不摘要
        history.append({"role": "user", "content": text})
        cost_stats["ds_input"] += sum(len(m.get("content","")) for m in history) // 3
        if len(history) > 18: history[:] = [history[0]] + history[-14:]

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

    # Greeting
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
        # Auto-evaluate on disconnect if user spoke
        if user_texts:
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
                try: await ws.send_json({"type": "score", "scores": sc})
                except: logger.warning(f"AUTO-EVAL: client disconnected, score cached for /api/session/{sid}/score")
                logger.info(f"AUTO-EVAL: score={sc.get('overall')}")
            except Exception as e:
                logger.error(f"AUTO-EVAL failed: {e}")
        session["status"] = "ended"
        if tracker: tracker.end_session()

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

# ── Cost Endpoint ──
@app.get("/api/costs")
async def api_costs():
    """成本核算
    TTS: 本地 Kokoro-82M — 免费
    STT: 本地 whisper.cpp — 免费  
    LLM: deepseek-chat — ~$0.27/1M input, ~$1.10/1M output (旧价格)"""
    total = (
        cost_stats["ds_input"] * 0.27 / 1_000_000
        + cost_stats["ds_output"] * 1.10 / 1_000_000
    )
    return {
        "total": round(total, 6),
        "session_count": len(sessions),
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
