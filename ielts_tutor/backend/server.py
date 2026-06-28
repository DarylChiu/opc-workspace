"""
IELTS Tutor v2.0 - Server · PTT模式 + 最终评估
"""
import os, json, logging, asyncio, uuid, base64, time, re
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn, aiohttp
import ssl; ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ielts-tutor")

from config import GOOGLE_STT_KEY, GOOGLE_TTS_KEY, DEEPSEEK_KEY, DEEPSEEK_BASE
from session_manager import SessionManager
sessions = SessionManager()
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
- Ask ONE question at a time about familiar topics (work, home, hobbies, daily life, travel, food, etc.)
- Vary your responses naturally — don't use the same phrases every time. Mix it up.
- Keep responses SHORT: 1-3 sentences max, then ask your next question.
- React naturally to what the candidate says before moving on. Show you're listening.
- Occasionally use different transitions: 'Interesting...', 'I see...', 'Let's talk about...', 'How about...', 'Moving on...'
- NEVER give scores, NEVER say 'good' or 'excellent' repeatedly
- Match the candidate's level — don't use overly complex vocabulary
- Be warm and conversational, like chatting with a friend""",
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
async def ds_chat(messages, max_tokens=200, temp=0.7):
    url = f"{DEEPSEEK_BASE}/chat/completions"
    h = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    b = {"model": "deepseek-chat", "messages": messages, "temperature": temp, "max_tokens": max_tokens}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=b, headers=h, timeout=aiohttp.ClientTimeout(15)) as r:
                data = await r.json()
                usage = data.get("usage", {})
                cost_stats["ds_input"] += usage.get("prompt_tokens", 0)
                cost_stats["ds_output"] += usage.get("completion_tokens", 0)
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"DS: {e}"); return ""

async def ds_stream(messages, max_tokens=300):
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

async def tts_speak(text):
    cost_stats["tts_calls"] += 1
    cost_stats["tts_chars"] += len(text)
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_TTS_KEY}"
    b = {"input": {"text": text}, "voice": {"languageCode": "en-US", "name": "en-US-Journey-O"},
         "audioConfig": {"audioEncoding": "MP3", "speakingRate": 0.95}}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=b, timeout=aiohttp.ClientTimeout(10)) as r:
                return (await r.json()).get("audioContent", "")
    except: return ""

async def stt_transcribe(audio_bytes):
    cost_stats["stt_calls"] += 1
    body = {"config": {"encoding": "LINEAR16", "sampleRateHertz": 16000, "languageCode": "en-US",
                       "enableAutomaticPunctuation": True, "model": "latest_short"},
            "audio": {"content": base64.b64encode(audio_bytes).decode()}}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_STT_KEY}",
                              json=body, timeout=aiohttp.ClientTimeout(10)) as r:
                return (await r.json())["results"][0]["alternatives"][0]["transcript"]
    except: return ""

# ── HTTP ──
@app.get("/")
async def index(): return HTMLResponse(open(FRONTEND).read())

@app.get("/api/health")
async def health():
    ver = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")).read().strip()
    return {"status": "ok", "version": ver, "costs": cost_stats}

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
        await ws.send_json({"type": "error", "msg": "session not found"}); await ws.close(); return

    mode = session.get("mode", "ielts_part1")
    audio_buf = b""
    history = [{"role": "system", "content": SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["free_talk"])}]
    user_texts = []

    async def send_tts(text):
        for sent in re.split(r'(?<=[.!?])\s+', text):
            s = sent.strip()
            if not s: continue
            a = await tts_speak(s)
            if a: await ws.send_json({"type": "audio", "data": a})

    async def process_utterance():
        nonlocal audio_buf
        if len(audio_buf) < 3200: return
        data = audio_buf; audio_buf = b""
        text = await stt_transcribe(data)
        if not text or len(text.strip()) < 2: return
        logger.info(f"STT: {text[:80]}")
        user_texts.append(text)
        await ws.send_json({"type": "final_transcript", "text": text})
        history.append({"role": "user", "content": text})
        cost_stats["ds_input"] += sum(len(m.get("content","")) for m in history) // 3
        if len(history) > 21: history[:] = [history[0]] + history[-20:]

        await ws.send_json({"type": "status", "state": "thinking"})
        full = ""
        async for t in ds_stream(history): full += t
        if not full: await ws.send_json({"type": "status", "state": "done"}); return

        await ws.send_json({"type": "response_text", "text": full})
        cost_stats["ds_output"] += len(full) // 3
        history.append({"role": "assistant", "content": full})
        await ws.send_json({"type": "status", "state": "speaking"})
        await send_tts(full)
        await ws.send_json({"type": "status", "state": "done"})

    # Greeting
    greet = GREETINGS.get(mode, GREETINGS["ielts_part1"])
    await ws.send_json({"type": "response_text", "text": greet})
    await ws.send_json({"type": "status", "state": "speaking"})
    await send_tts(greet)
    await ws.send_json({"type": "status", "state": "done"})

    try:
        while True:
            msg = await ws.receive_json()
            t = msg.get("type")

            if t == "audio":
                audio_buf += base64.b64decode(msg.get("data", ""))

            elif t == "flush":
                await process_utterance()

            elif t == "evaluate_final":
                if not user_texts: continue
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
                                  max_tokens=400, temp=0.3)
                try:
                    sc = json.loads(r)
                    await ws.send_json({"type": "score", "scores": sc})
                    logger.info(f"Final: overall={sc.get('overall')}")
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
        session["status"] = "ended"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8767)), log_level="info")
