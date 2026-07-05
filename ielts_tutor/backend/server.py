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

import os as _os
if _os.environ.get("DEBUG_MODE", "0") == "1":
    from debug_logger import debug_manager, handle_debug_ws, handle_debug_export, handle_debug_list
else:
    debug_manager = None

from config import GOOGLE_STT_KEY, GOOGLE_TTS_KEY, DEEPSEEK_KEY, DEEPSEEK_BASE
from session_manager import PersistentSessionManager
from report_generator import generate_report
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
            async with s.post(url, json=b, headers=h, timeout=aiohttp.ClientTimeout(15)) as r:
                data = await r.json()
                usage = data.get("usage", {})
                cost_stats["ds_input"] += usage.get("prompt_tokens", 0)
                cost_stats["ds_output"] += usage.get("completion_tokens", 0)
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"DS: {e}"); return ""

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
    encoding = "LINEAR16"
    audio_b64 = base64.b64encode(audio_bytes).decode()
    # FLAC compression for 10x faster upload (ffmpeg required)
    try:
        import tempfile, subprocess
        pcm_path = None; flac_path = None
        with tempfile.NamedTemporaryFile(suffix='.pcm', delete=False) as f:
            f.write(audio_bytes); pcm_path = f.name
        flac_path = pcm_path + '.flac'
        r = subprocess.run(['ffmpeg','-y','-f','s16le','-ar','16000','-ac','1',
                           '-i',pcm_path,'-c:a','flac','-compression_level','0',flac_path],
                          capture_output=True, timeout=3)
        if r.returncode == 0 and os.path.exists(flac_path):
            with open(flac_path,'rb') as f: audio_b64 = base64.b64encode(f.read()).decode()
            encoding = "FLAC"
    except: pass
    finally:
        for p in [pcm_path, flac_path]:
            try: os.unlink(p) if p else None
            except: pass
    body = {"config": {"encoding": encoding, "sampleRateHertz": 16000, "languageCode": "en-US",
                       "enableAutomaticPunctuation": True, "model": "latest_short",
                       "useEnhanced": False},
            "audio": {"content": audio_b64}}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_STT_KEY}",
                              json=body, timeout=aiohttp.ClientTimeout(10)) as r:
                data = await r.json()
                alt = data["results"][0]["alternatives"][0]
                return alt["transcript"], alt.get("confidence", 0.0)
    except: return "", 0.0

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
    sessions.create(sid, mode=body.get("mode", "ielts_part1"),
                pipeline=body.get("pipeline", "cascade"))
    return {"session_id": sid, "mode": body.get("mode", "ielts_part1")}

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

                # Send ALL audio at once to Qwen, then commit+request
                try:
                    await bridge.handle_audio(full_pcm)
                    await asyncio.sleep(0.3)  # Let Qwen process
                    await bridge.client.commit_audio()
                    await asyncio.sleep(0.1)
                    await bridge.client.request_response()
                except Exception as e:
                    logger.error(f"Qwen send/commit error: {e}")
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
                                  max_tokens=400, temp=0.3)
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
        await handle_realtime(ws, sid, session, mode, QWEN_OMNI_KEY)
        return

    audio_buf = b""
    history = [{"role": "system", "content": SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["free_talk"])}]
    user_texts = []

    # Debug tracker
    tracker = None
    if debug_manager:
        tracker = debug_manager.create_tracker(sid, mode, "cascade")

    async def send_tts(text, first_chunk_cb=None):
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\\s+', text) if s.strip()]
        if not sentences: return
        first = True
        for s in sentences:
            a = await tts_speak(s)
            if a:
                if first and first_chunk_cb:
                    first_chunk_cb()
                    first = False
                await ws.send_json({"type": "audio", "data": a})

    async def process_utterance():
        nonlocal audio_buf
        if len(audio_buf) < 3200: return
        if tracker: await tracker.start_turn()
        data = audio_buf; audio_buf = b""
        stt_t0 = time.time()
        text, conf = await stt_transcribe(data)
        if tracker: await tracker.record_asr(text, conf, (time.time()-stt_t0)*1000)
        if not text or len(text.strip()) < 2: return
        logger.info(f"STT: {text[:80]} (conf={conf:.2f})")
        user_texts.append(text)
        await ws.send_json({"type": "final_transcript", "text": text})
        history.append({"role": "user", "content": text})
        cost_stats["ds_input"] += sum(len(m.get("content","")) for m in history) // 3
        if len(history) > 25: history[:] = [history[0]] + history[-20:]

        await ws.send_json({"type": "status", "state": "thinking"})
        full = ""
        llm_t0 = time.time()
        async for t in ds_stream(history): full += t
        if tracker: await tracker.record_llm("general_chat", full, (time.time()-llm_t0)*1000)
        if not full: await ws.send_json({"type": "status", "state": "done"}); return

        await ws.send_json({"type": "response_text", "text": full})
        cost_stats["ds_output"] += len(full) // 3
        history.append({"role": "assistant", "content": full})
        await ws.send_json({"type": "status", "state": "speaking"})
        tts_t0 = time.time()
        await send_tts(full)
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
                if tracker: await tracker.record_audio_chunk(len(chunk))

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
                                  max_tokens=400, temp=0.3)
                try:
                    logger.info(f"EVALUATE: parsed, overall={json.loads(r).get('overall','?')}")
                    sc = json.loads(r)
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
        # Auto-evaluate on disconnect if user spoke
        if user_texts and ws.client_state.name != "DISCONNECTED":
            try:
                logger.info(f"AUTO-EVAL: {sid} {len(user_texts)} texts")
                all_text = "\n---\n".join(user_texts[-10:])
                sys_prompt = '{"fluency":X.X,"vocabulary":X.X,"grammar":X.X,"pronunciation":X.X,"overall":X.X,"summary":"...","improvements":["You said ~~wrong~~ → **correct** — why"],"highlights":["Good ``word`` → **better** — why"]}'
                eval_msg = [{"role":"system","content":"You are an IELTS examiner. Evaluate and output ONLY valid JSON. Format: " + sys_prompt},
                           {"role":"user","content":f"Evaluate this conversation:\n{all_text}"}]
                r = await ds_chat(eval_msg, max_tokens=400, temp=0.3)
                sc = json.loads(r)
                await ws.send_json({"type": "score", "scores": sc})
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

    @app.websocket("/debug/ws/{sid}")
    async def debug_ws(ws: WebSocket, sid: str):
        await handle_debug_ws(ws, sid)

# ── Cost Endpoint ──
@app.get("/api/costs")
async def api_costs():
    total = (
        cost_stats["stt_calls"] * 0.006 / 15
        + cost_stats["tts_calls"] * 0.000004 * max(cost_stats["tts_chars"], 1)
        + cost_stats["ds_input"] * 0.00000027
        + cost_stats["ds_output"] * 0.0000011
    )
    return {"total": total, "session_count": len(sessions), "details": cost_stats}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8767)), log_level="info")
