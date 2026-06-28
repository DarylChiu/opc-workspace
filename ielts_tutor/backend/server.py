"""
IELTS Tutor v2.0 - Server 路由层
WebSocket 音频通道 + 双管线路由 + 自动断句
"""
import os
import json
import logging
import asyncio
import uuid
import base64
import time
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

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ielts-tutor")

FRONTEND_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")
app = FastAPI(title="IELTS Tutor v2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
sessions = SessionManager()

# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
@app.get("/")
async def serve_frontend():
    return HTMLResponse(open(FRONTEND_PATH).read())

@app.get("/api/health")
async def health():
    ver = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")).read().strip()
    return {"status": "ok", "version": ver, "sessions": len(sessions)}

@app.post("/api/session/start")
async def start_session(req: Request):
    body = await req.json()
    sid = str(uuid.uuid4())[:8]
    sessions.create(sid, mode=body.get("mode", "ielts_part1"),
                    pipeline=body.get("pipeline", "cascade"))
    logger.info(f"Session {sid} | {body.get('mode')}")
    return {"session_id": sid, "pipeline": body.get("pipeline", "cascade"),
            "mode": body.get("mode", "ielts_part1")}

# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------
@app.websocket("/ws/chat/{sid}")
async def ws_chat(ws: WebSocket, sid: str):
    await ws.accept()
    session = sessions.get(sid)
    if not session or session.get("pipeline") == "qwen-omni":
        await ws.send_json({"type": "error", "msg": "unavailable"})
        await ws.close(); return

    mode = session.get("mode", "ielts_part1")
    stt = GoogleSTTStreamer(api_key=GOOGLE_STT_KEY)
    engine = ConversationEngine(api_key=DEEPSEEK_KEY, base_url=DEEPSEEK_BASE, mode=mode)
    tts = GoogleTTSStreamer(api_key=GOOGLE_TTS_KEY)
    session["status"] = "active"

    last_audio = time.time()
    SILENCE_TIMEOUT = 1.8  # auto-flush after this many seconds of silence

    async def process_utterance(text: str):
        """Send user text → DeepSeek → TTS → back to client"""
        await ws.send_json({"type": "final_transcript", "text": text})
        session.setdefault("transcripts", []).append(
            {"speaker": "user", "text": text, "time": datetime.now().isoformat()})

        await ws.send_json({"type": "status", "state": "thinking"})
        full_response = ""
        async for token in engine.generate(text):
            full_response += token

        if not full_response:
            await ws.send_json({"type": "status", "state": "listening"})
            return

        await ws.send_json({"type": "response_text", "text": full_response})
        session["transcripts"].append(
            {"speaker": "tutor", "text": full_response, "time": datetime.now().isoformat()})

        await ws.send_json({"type": "status", "state": "speaking"})
        async for audio_chunk in tts.synthesize(full_response):
            await ws.send_json({"type": "audio", "data": audio_chunk})

        await ws.send_json({"type": "status", "state": "listening"})

    async def silence_watcher():
        """Auto-flush STT when user stops speaking"""
        nonlocal last_audio
        while True:
            await asyncio.sleep(0.3)
            elapsed = time.time() - last_audio
            buf_size = len(stt.buffer)
            if elapsed > SILENCE_TIMEOUT and buf_size > 6400:  # >0.2s audio
                text = await stt.flush()
                if text and len(text.strip()) > 2:
                    await process_utterance(text)
                last_audio = time.time()

    bg_task = asyncio.create_task(silence_watcher())

    try:
        while True:
            msg = await ws.receive_json()
            msg_type = msg.get("type")

            if msg_type == "audio":
                audio_bytes = base64.b64decode(msg.get("data", ""))
                stt.feed(audio_bytes)
                last_audio = time.time()

            elif msg_type == "flush":
                text = await stt.flush()
                if text and len(text.strip()) > 2:
                    await process_utterance(text)
                last_audio = time.time()

            elif msg_type == "mode":
                mode = msg.get("mode")
                if mode:
                    session["mode"] = mode
                    engine.set_mode(mode)
                    await ws.send_json({"type": "status", "state": "mode_changed", "mode": mode})

            elif msg_type == "stop":
                # Flush remaining audio
                text = await stt.flush()
                if text and len(text.strip()) > 2:
                    await process_utterance(text)
                await ws.send_json({"type": "status", "state": "stopped"})
                break

    except WebSocketDisconnect:
        logger.info(f"Session {sid} disconnected")
    except Exception as e:
        logger.exception(f"Session {sid}")
        try: await ws.send_json({"type": "error", "msg": str(e)})
        except: pass
    finally:
        bg_task.cancel()
        session["status"] = "ended"
        stt.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8767)), log_level="info")
