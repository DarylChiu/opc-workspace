"""
IELTS Tutor v2.0 - Server 路由层
WebSocket 音频通道 + 双管线路由
"""
import os
import json
import logging
import asyncio
import uuid
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

# SSL hack for local dev
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
# HTTP endpoints
# ---------------------------------------------------------------------------
@app.get("/")
async def serve_frontend():
    html = open(FRONTEND_PATH).read()
    return HTMLResponse(html)

@app.get("/api/health")
async def health():
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")) as f:
        version = f.read().strip()
    return {"status": "ok", "version": version, "sessions": len(sessions)}

@app.post("/api/session/start")
async def start_session(req: Request):
    body = await req.json()
    mode = body.get("mode", "ielts_part1")
    pipeline = body.get("pipeline", "cascade")  # cascade | qwen-omni
    sid = str(uuid.uuid4())[:8]
    sessions.create(sid, mode=mode, pipeline=pipeline)
    logger.info(f"Session {sid} started | mode={mode} | pipeline={pipeline}")
    return {"session_id": sid, "pipeline": pipeline, "mode": mode}

@app.get("/api/session/{sid}")
async def get_session(sid: str):
    s = sessions.get(sid)
    if not s:
        return JSONResponse({"error": "not found"}, 404)
    return {
        "session_id": sid,
        "mode": s["mode"],
        "pipeline": s["pipeline"],
        "status": s["status"],
        "transcript_count": len(s.get("transcripts", [])),
        "created": s["created"].isoformat()
    }

# ---------------------------------------------------------------------------
# WebSocket - 管线1 链式流式
# ---------------------------------------------------------------------------
@app.websocket("/ws/chat/{sid}")
async def ws_chat(ws: WebSocket, sid: str):
    await ws.accept()
    session = sessions.get(sid)
    if not session:
        await ws.send_json({"type": "error", "msg": "session not found"})
        await ws.close()
        return

    pipeline = session.get("pipeline", "cascade")
    mode = session.get("mode", "ielts_part1")

    if pipeline == "qwen-omni":
        await ws.send_json({"type": "error", "msg": "pipeline 2 not yet available"})
        await ws.close()
        return

    # Init pipeline 1 components
    stt = GoogleSTTStreamer(api_key=GOOGLE_STT_KEY)
    engine = ConversationEngine(api_key=DEEPSEEK_KEY, base_url=DEEPSEEK_BASE, mode=mode)
    tts = GoogleTTSStreamer(api_key=GOOGLE_TTS_KEY)
    session["status"] = "active"

    logger.info(f"Pipeline 1 active for {sid} | mode={mode}")

    try:
        while True:
            msg = await ws.receive_json()
            msg_type = msg.get("type")

            if msg_type == "audio":
                # Client sent audio chunk (base64 PCM)
                audio_b64 = msg.get("data", "")
                if not audio_b64:
                    continue

                import base64
                audio_bytes = base64.b64decode(audio_b64)

                # Feed to STT streamer → get partial text
                partial = stt.feed(audio_bytes)

                if partial:
                    await ws.send_json({"type": "partial_transcript", "text": partial})

                # Check if utterance ended (STT detected silence/endpoint)
                if stt.is_utterance_complete():
                    full_text = stt.flush()
                    if full_text and len(full_text.strip()) > 2:
                        await ws.send_json({"type": "final_transcript", "text": full_text})
                        session.setdefault("transcripts", []).append({
                            "speaker": "user", "text": full_text, "time": datetime.now().isoformat()
                        })

                        # Generate response via DeepSeek
                        await ws.send_json({"type": "status", "state": "thinking"})
                        full_response = ""

                        async for token in engine.generate(full_text):
                            full_response += token

                        if full_response:
                            await ws.send_json({"type": "response_text", "text": full_response})
                            session["transcripts"].append({
                                "speaker": "tutor", "text": full_response, "time": datetime.now().isoformat()
                            })

                            # TTS
                            await ws.send_json({"type": "status", "state": "speaking"})
                            async for audio_chunk in tts.synthesize(full_response):
                                await ws.send_json({"type": "audio", "data": audio_chunk})

                        await ws.send_json({"type": "status", "state": "listening"})

            elif msg_type == "mode":
                new_mode = msg.get("mode")
                if new_mode:
                    session["mode"] = new_mode
                    engine.set_mode(new_mode)
                    await ws.send_json({"type": "status", "state": "mode_changed", "mode": new_mode})

            elif msg_type == "stop":
                await ws.send_json({"type": "status", "state": "stopped"})
                break

    except WebSocketDisconnect:
        logger.info(f"Session {sid} disconnected")
    except Exception as e:
        logger.exception(f"Session {sid} error")
        try:
            await ws.send_json({"type": "error", "msg": str(e)})
        except:
            pass
    finally:
        session["status"] = "ended"
        stt.close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8766))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
