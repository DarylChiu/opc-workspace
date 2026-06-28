"""
IELTS Tutor v2.0 - Server 路由层
WebSocket 音频通道 + 双管线路由 + 自动断句 + 开场问候
"""
import os, json, logging, asyncio, uuid, base64, time
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from config import GOOGLE_STT_KEY, GOOGLE_TTS_KEY, DEEPSEEK_KEY, DEEPSEEK_BASE
from session_manager import SessionManager
from stt_streaming import GoogleSTTStreamer
from conversation_engine import ConversationEngine
from tts_streaming import GoogleTTSStreamer

import ssl; ssl._create_default_https_context = ssl._create_unverified_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ielts-tutor")

FRONTEND = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")
app = FastAPI(title="IELTS Tutor v2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
sessions = SessionManager()

SILENCE_TIMEOUT = 1.0
MIN_AUDIO_BYTES = 3200

# ── HTTP ──
@app.get("/")
async def index(): return HTMLResponse(open(FRONTEND).read())

@app.get("/api/health")
async def health():
    ver = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")).read().strip()
    return {"status": "ok", "version": ver, "sessions": len(sessions)}

@app.post("/api/session/start")
async def start(req: Request):
    body = await req.json()
    sid = str(uuid.uuid4())[:8]
    sessions.create(sid, mode=body.get("mode", "ielts_part1"),
                    pipeline=body.get("pipeline", "cascade"))
    logger.info(f"Session {sid} | {body.get('mode')}")
    return {"session_id": sid, "pipeline": body.get("pipeline", "cascade"),
            "mode": body.get("mode", "ielts_part1")}

# ── WebSocket ──
@app.websocket("/ws/chat/{sid}")
async def ws_chat(ws: WebSocket, sid: str):
    await ws.accept()
    session = sessions.get(sid)
    if not session or session.get("pipeline") == "qwen-omni":
        await ws.send_json({"type": "error", "msg": "unavailable"}); await ws.close(); return

    mode = session.get("mode", "ielts_part1")
    stt = GoogleSTTStreamer(api_key=GOOGLE_STT_KEY)
    engine = ConversationEngine(api_key=DEEPSEEK_KEY, base_url=DEEPSEEK_BASE, mode=mode)
    tts = GoogleTTSStreamer(api_key=GOOGLE_TTS_KEY)
    session["status"] = "active"
    last_audio = time.time()
    t_start = time.time()

    async def respond(text: str):
        """One full turn: STT text → DeepSeek → TTS → client"""
        nonlocal last_audio
        await ws.send_json({"type": "final_transcript", "text": text})
        session.setdefault("transcripts", []).append(
            {"speaker": "user", "text": text, "time": datetime.now().isoformat()})
        await ws.send_json({"type": "status", "state": "thinking"})

        t0 = time.time()
        full = ""
        async for token in engine.generate(text): full += token
        dt_turn = time.time() - t0
        logger.info(f"  Turn: {dt_turn:.1f}s → {full[:60]}...")

        if not full:
            await ws.send_json({"type": "status", "state": "listening"}); return

        await ws.send_json({"type": "response_text", "text": full})
        session["transcripts"].append(
            {"speaker": "tutor", "text": full, "time": datetime.now().isoformat()})

        await ws.send_json({"type": "status", "state": "speaking"})
        async for audio_chunk in tts.synthesize(full):
            await ws.send_json({"type": "audio", "data": audio_chunk})
        await ws.send_json({"type": "status", "state": "listening"})
        last_audio = time.time()

    async def silence_watcher():
        nonlocal last_audio
        while True:
            await asyncio.sleep(0.25)
            if time.time() - last_audio > SILENCE_TIMEOUT and len(stt.buffer) > MIN_AUDIO_BYTES:
                text = await stt.flush()
                if text and len(text.strip()) > 2:
                    await respond(text)
                last_audio = time.time()

    bg = asyncio.create_task(silence_watcher())

    # Greeting
    greet = engine.get_greeting()
    if greet:
        await ws.send_json({"type": "response_text", "text": greet})
        session.setdefault("transcripts", []).append(
            {"speaker": "tutor", "text": greet, "time": datetime.now().isoformat()})
        await ws.send_json({"type": "status", "state": "speaking"})
        async for c in tts.synthesize(greet): await ws.send_json({"type": "audio", "data": c})
        await ws.send_json({"type": "status", "state": "listening"})

    last_audio = time.time()

    try:
        while True:
            msg = await ws.receive_json()
            t = msg.get("type")

            if t == "audio":
                stt.feed(base64.b64decode(msg.get("data", "")))
                last_audio = time.time()

            elif t == "flush":
                text = await stt.flush()
                if text and len(text.strip()) > 2:
                    await respond(text)
                last_audio = time.time()

            elif t == "mode":
                m = msg.get("mode")
                if m:
                    session["mode"] = m; engine.set_mode(m)
                    await ws.send_json({"type": "status", "state": "mode_changed", "mode": m})

            elif t == "stop":
                text = await stt.flush()
                if text and len(text.strip()) > 2:
                    await respond(text)
                await ws.send_json({"type": "status", "state": "listening"})

    except WebSocketDisconnect:
        dt = time.time() - t_start
        logger.info(f"Session {sid} ended ({dt:.0f}s)")
    except Exception as e:
        logger.exception(f"Session {sid}")
        try: await ws.send_json({"type": "error", "msg": str(e)})
        except: pass
    finally:
        bg.cancel(); session["status"] = "ended"; stt.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8767)), log_level="info")
