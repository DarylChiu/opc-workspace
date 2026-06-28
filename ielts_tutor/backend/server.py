"""
IELTS Tutor v2.0 - Server · 连续对话 + 实时评分
"""
import os, json, logging, asyncio, uuid, base64, time
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import aiohttp

from config import GOOGLE_STT_KEY, GOOGLE_TTS_KEY, DEEPSEEK_KEY, DEEPSEEK_BASE
from session_manager import SessionManager
from stt_streaming import GoogleSTTStreamer

import ssl; ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ielts-tutor")

FRONTEND = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")
app = FastAPI(title="IELTS Tutor v2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
sessions = SessionManager()

SILENCE_TIMEOUT = 1.0
MIN_AUDIO = 3200

# ── DeepSeek helpers ──
async def ds_chat(api_key, base_url, messages, max_tokens=200, temperature=0.7):
    """Non-streaming DeepSeek call, returns full response text"""
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"model": "deepseek-chat", "messages": messages, "temperature": temperature,
            "max_tokens": max_tokens}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=body, headers=headers,
                              timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"DeepSeek error: {e}")
        return ""

async def ds_stream(api_key, base_url, messages, max_tokens=300):
    """Streaming DeepSeek call, yields tokens"""
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"model": "deepseek-chat", "messages": messages, "temperature": 0.7,
            "max_tokens": max_tokens, "stream": True}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=body, headers=headers,
                              timeout=aiohttp.ClientTimeout(total=30)) as resp:
                buf = b""
                async for chunk in resp.content.iter_any():
                    buf += chunk
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        line = line.strip()
                        if not line or line == b"data: [DONE]": continue
                        if line.startswith(b"data: "): line = line[6:]
                        try:
                            delta = json.loads(line)["choices"][0].get("delta", {})
                            if delta.get("content"): yield delta["content"]
                        except: pass
    except Exception as e:
        logger.error(f"Stream error: {e}")

# ── TTS ──
async def tts_speak(api_key, text, language="en-US"):
    """Synthesize text to base64 MP3"""
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
    body = {"input": {"text": text}, "voice": {"languageCode": language, "name": "en-US-Journey-O"},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": 0.95}}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=body, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                return data.get("audioContent", "")
    except: return ""

# ── STT ──
async def stt_transcribe(api_key, audio_bytes):
    """Send audio to Google STT, return text"""
    body = {"config": {"encoding": "LINEAR16", "sampleRateHertz": 16000, "languageCode": "en-US",
                       "enableAutomaticPunctuation": True, "model": "latest_short"},
            "audio": {"content": base64.b64encode(audio_bytes).decode()}}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}",
                              json=body, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                r = await resp.json()
                return r["results"][0]["alternatives"][0]["transcript"]
    except: return ""

# ── Prompts ──
SYSTEM_PROMPTS = {
    "ielts_part1": """You are an IELTS Speaking examiner doing Part 1 interview.
Rules: Ask ONE question at a time about familiar topics. Keep responses short (2-4 sentences). Acknowledge briefly then ask next question. Vary topics naturally. NEVER give scores. Be warm but professional. Speak at B2-C1 level.""",
    "ielts_part2": """You are an IELTS Speaking examiner doing Part 2 (Long Turn). Give topic card, 1 min prep, candidate speaks 1-2 min. Ask 1-2 follow-up questions after. Keep your own words minimal. NEVER interrupt or score.""",
    "ielts_part3": """You are an IELTS Speaking examiner doing Part 3 (Discussion). Ask abstract questions. Follow up on answers. Challenge ideas respectfully. Ask about opinions, comparisons, predictions. NEVER give scores.""",
    "business_pitch": """You are a business English coach for investor pitch practice. Simulate investor meeting. Ask typical investor questions. Give brief, constructive feedback after each response.""",
    "free_talk": """You are a friendly English conversation partner. Chat naturally. Keep responses 3-5 sentences. Gently correct major grammar mistakes. Be encouraging. Ask follow-up questions.""",
}

GREETINGS = {
    "ielts_part1": "Good morning. My name is Alex and I'll be your IELTS examiner today. Can you tell me your full name, please?",
    "ielts_part2": "Now I'm going to give you a topic. You should talk about it for 1 to 2 minutes. Before you talk, you'll have 1 minute to prepare. Here is your topic: Describe a book you recently read. You should say what the book was, why you read it, what it was about, and how you felt about it.",
    "ielts_part3": "Now let's talk about some more general questions related to reading. Do you think people read less now than they did in the past?",
    "business_pitch": "Welcome to your investor pitch practice. I'll play the role of a potential investor. Tell me about your business when you're ready.",
    "free_talk": "Hi there! What would you like to chat about today?",
}

# ── HTTP ──
@app.get("/")
async def index(): return HTMLResponse(open(FRONTEND).read())

@app.get("/api/health")
async def health():
    ver = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")).read().strip()
    return {"status": "ok", "version": ver}

@app.post("/api/session/start")
async def start(req: Request):
    body = await req.json()
    sid = str(uuid.uuid4())[:8]
    sessions.create(sid, mode=body.get("mode", "ielts_part1"))
    return {"session_id": sid, "mode": body.get("mode", "ielts_part1")}

# ── WebSocket ──
@app.websocket("/ws/chat/{sid}")
async def ws_chat(ws: WebSocket, sid: str):
    await ws.accept()
    session = sessions.get(sid)
    if not session:
        await ws.send_json({"type":"error","msg":"session not found"}); await ws.close(); return

    mode = session.get("mode", "ielts_part1")
    stt_buf = b""
    history = [{"role": "system", "content": SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["free_talk"])}]
    last_audio = time.time()
    muted = False  # mute during AI speaking to avoid echo

    async def send_text(text, is_user=False):
        nonlocal last_audio
        if is_user:
            await ws.send_json({"type": "final_transcript", "text": text})
        else:
            await ws.send_json({"type": "response_text", "text": text})
            history.append({"role": "assistant", "content": text})

    async def send_tts(text):
        """Split into sentences and stream audio chunks"""
        import re
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        for sent in sentences:
            audio = await tts_speak(GOOGLE_TTS_KEY, sent)
            if audio: await ws.send_json({"type": "audio", "data": audio})

    async def process_utterance():
        nonlocal stt_buf, last_audio, muted
        if len(stt_buf) < MIN_AUDIO: return
        audio = stt_buf; stt_buf = b""

        text = await stt_transcribe(GOOGLE_STT_KEY, audio)
        if not text or len(text.strip()) < 2: return

        logger.info(f"STT: {text[:80]}")
        await send_text(text, is_user=True)
        history.append({"role": "user", "content": text})

        # Keep history manageable
        if len(history) > 21:
            history[:] = [history[0]] + history[-20:]

        # Generate response
        await ws.send_json({"type": "status", "state": "thinking"})
        full = ""
        async for token in ds_stream(DEEPSEEK_KEY, DEEPSEEK_BASE, history):
            full += token

        if full:
            t0 = time.time()
            await send_text(full)
            await ws.send_json({"type": "status", "state": "speaking"})
            muted = True
            await send_tts(full)
            muted = False
            await ws.send_json({"type": "status", "state": "listening"})
            logger.info(f"  Response: {time.time()-t0:.1f}s → {full[:60]}...")

    async def silence_watcher():
        nonlocal last_audio, muted
        while True:
            await asyncio.sleep(0.25)
            if muted: continue
            if time.time() - last_audio > SILENCE_TIMEOUT and len(stt_buf) > MIN_AUDIO:
                await process_utterance()
                last_audio = time.time()

    bg = asyncio.create_task(silence_watcher())

    # Greeting
    greet = GREETINGS.get(mode, GREETINGS["ielts_part1"])
    await send_text(greet)
    await ws.send_json({"type": "status", "state": "speaking"})
    muted = True
    await send_tts(greet)
    muted = False
    await ws.send_json({"type": "status", "state": "listening"})
    last_audio = time.time()

    try:
        while True:
            msg = await ws.receive_json()
            t = msg.get("type")

            if t == "audio":
                if muted: continue
                stt_buf += base64.b64decode(msg.get("data", ""))
                last_audio = time.time()

            elif t == "evaluate":
                # Quick score for last user utterance
                if len(history) < 3: continue
                last_user = next((m["content"] for m in reversed(history) if m["role"]=="user"), "")
                if not last_user: continue

                score_prompt = [
                    {"role":"system","content":"""You are an IELTS speaking evaluator. Score the user's last response on 4 dimensions (0-9 scale). Return ONLY valid JSON:
{"fluency":X.X, "vocabulary":X.X, "grammar":X.X, "pronunciation":X.X, "note":"one brief improvement tip in Chinese"}"""},
                    {"role":"user","content": f"Score this speaking response:\n\"{last_user}\""}
                ]
                result = await ds_chat(DEEPSEEK_KEY, DEEPSEEK_BASE, score_prompt, max_tokens=150, temperature=0.3)
                try:
                    scores = json.loads(result)
                    await ws.send_json({"type":"score","scores":scores,"note":scores.get("note","")})
                except:
                    logger.debug(f"Score parse failed: {result[:80]}")

            elif t == "mode":
                m = msg.get("mode")
                if m and m in SYSTEM_PROMPTS:
                    history = [{"role":"system","content":SYSTEM_PROMPTS[m]}]
                    session["mode"] = m

            elif t == "stop":
                await ws.send_json({"type":"status","state":"stopped"})
                break

    except WebSocketDisconnect:
        logger.info(f"Session {sid} ended")
    except Exception as e:
        logger.exception(f"Session {sid}")
        try: await ws.send_json({"type":"error","msg":str(e)})
        except: pass
    finally:
        bg.cancel(); session["status"]="ended"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8767)), log_level="info")
