#!/usr/bin/env python3
"""
IELTS 陪练助手 - 统一服务 v3.0
合并 STT + TTS + DeepSeek 评估引擎 + 对话模式
Bryson / 吹点小风 | 2026-06-07
"""

import os, json, base64, logging, time, ssl, traceback
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import requests

ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("ielts_unified")

# ── API Keys ──────────────────────────────────────────────
with open(os.path.expanduser("~/.openclaw/auth/google/ielts_tts_2026.key")) as f:
    GOOGLE_API_KEY = f.read().strip()
# STT uses a different key with Speech-to-Text API enabled
GOOGLE_STT_KEY = "AIzaSyDUwxtaIAuXXTKwuyabGzBYFYC3-eaIw0A"
with open(os.path.expanduser("~/.openclaw/auth/agents/xiaofeng/deepseek_bryson.json")) as f:
    DEEPSEEK_KEY = json.load(f)["key"]

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
GOOGLE_STT_URL = f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_STT_KEY}"
GOOGLE_TTS_URL = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_API_KEY}"

# ── Conversation State ────────────────────────────────────
from dataclasses import dataclass, field

@dataclass
class ConversationState:
    mode: str = "part1"          # part1 | part2
    stage: str = "idle"          # idle | asking | waiting | evaluating | done
    current_question: int = 0
    questions: list = field(default_factory=list)
    history: list = field(default_factory=list)
    last_transcript: str = ""
    last_evaluation: dict = field(default_factory=dict)

PART1_QUESTIONS = [
    "Let's start with something simple. Tell me about your hometown. Where are you from and what do you like about it?",
    "What do you do? Are you a student or do you work?",
    "Why are you learning English? What motivates you?",
    "What do you enjoy doing in your free time?",
    "Do you like traveling? Tell me about a place you've visited recently.",
]

PART2_TOPICS = [
    {"topic": "Describe a memorable trip you've taken.",
     "prompt": "You should say: where you went, who you went with, what you did there, and explain why it was memorable."},
    {"topic": "Describe a person who has influenced your career.",
     "prompt": "You should say: who this person is, how you know them, what they did, and explain how they influenced you."},
    {"topic": "Describe a business idea you find interesting.",
     "prompt": "You should say: what the idea is, how you came up with it, why you think it could succeed, and explain what challenges it might face."},
]

conversations = {}

# ── FastAPI App ───────────────────────────────────────────
app = FastAPI(title="IELTS Practice Assistant", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── STT: Speech to Text ───────────────────────────────────
@app.post("/api/stt")
async def speech_to_text(request: Request):
    try:
        data = await request.json()
        audio_data = data.get("audio", {})
        if isinstance(audio_data, str):
            audio_b64 = audio_data
        else:
            audio_b64 = audio_data.get("content", "")
        if not audio_b64:
            return JSONResponse({"error": "no audio"}, 400)
        logger.info(f"STT: {len(audio_b64)} chars")

        # Proven encoding fallback chain (matches stt_final_demo.py)
        # WebM Opus is what the browser records; try with+without enhanced model
        configs = [
            {"encoding": "WEBM_OPUS", "sampleRateHertz": 48000, "languageCode": "en-US", "model": "default", "useEnhanced": True, "enableAutomaticPunctuation": True},
            {"encoding": "WEBM_OPUS", "sampleRateHertz": 48000, "languageCode": "en-US", "model": "default", "useEnhanced": False, "enableAutomaticPunctuation": True},
        ]
        best_transcript, best_confidence = "", 0
        import time as _time
        chain_start = _time.time()
        for cfg in configs:
            elapsed = _time.time() - chain_start
            if elapsed > 50:
                logger.warning(f"STT chain timeout after {elapsed:.0f}s — stopping config loop")
                break
            remain = max(8, 55 - elapsed)
            try:
                r = requests.post(GOOGLE_STT_URL, json={"config": cfg, "audio": {"content": audio_b64}}, timeout=remain)
                result = r.json()
                if "error" in result: continue
                if "results" in result and result["results"]:
                    alt = result["results"][0]["alternatives"][0]
                    t = alt.get("transcript", "").strip()
                    c = alt.get("confidence", 0)
                    if t and c > best_confidence:
                        best_transcript, best_confidence = t, c
                        logger.info(f"STT [{cfg['encoding']} enhanced={cfg.get('useEnhanced','?')}]: '{t[:60]}' ({c*100:.0f}%)")
            except Exception as e:
                logger.warning(f"STT config {cfg['encoding']} failed: {type(e).__name__}")
        if best_transcript:
            return JSONResponse({"transcript": best_transcript, "confidence": round(best_confidence*100,1)})
        return JSONResponse({"transcript": "(no speech detected)", "confidence": 0})
    except Exception as e:
        logger.error(f"STT error: {e}\n{traceback.format_exc()}")
        return JSONResponse({"error": str(e)}, 500)

# ── TTS: Text to Speech (Daryl voice params) ──────────────
@app.post("/api/tts")
async def text_to_speech(request: Request):
    try:
        data = await request.json()
        text = data.get("text", "")
        if not text:
            return JSONResponse({"error": "no text"}, 400)

        tts_req = {
            "input": {"text": text},
            "voice": {"languageCode": "en-US", "name": "en-US-Journey-O",
                      "ssmlGender": "MALE"},
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 0.85,
                "pitch": 0,
                "volumeGainDb": 1.0
            }
        }
        resp = requests.post(GOOGLE_TTS_URL, json=tts_req, timeout=15)
        result = resp.json()
        return JSONResponse({"audio": result.get("audioContent", "")})
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return JSONResponse({"error": str(e)}, 500)

# ── Evaluation Engine (DeepSeek V4 Pro) ───────────────────
EVALUATION_PROMPT = """You are an IELTS speaking examiner. Evaluate the candidate's response.

Candidate's answer: "{transcript}"
Question/Topic: "{question}"
IELTS Part: {mode}

Provide feedback in this JSON format:
{{
    "fluency": {{"score": 6.0, "comment": "..."}},
    "vocabulary": {{"score": 6.0, "comment": "..."}},
    "grammar": {{"score": 6.0, "comment": "..."}},
    "overall": 6.0,
    "highlights": "...",
    "improvements": "..."
}}

Rules:
- Score each dimension 0-9 (0.5 increments)
- Fluency: coherence, hesitation, speed
- Vocabulary: range, precision, collocations
- Grammar: accuracy, complexity, variety
- highlights: 1-2 things they did well (max 50 words)
- improvements: 1-2 specific suggestions (max 50 words)
- Be constructive and encouraging
- Return ONLY valid JSON, no markdown"""

@app.post("/api/evaluate")
async def evaluate_response(request: Request):
    try:
        data = await request.json()
        transcript = data.get("transcript", "")
        question = data.get("question", "")
        mode = data.get("mode", "part1")

        if not transcript.strip():
            return JSONResponse({"error": "empty transcript"}, 400)

        prompt = EVALUATION_PROMPT.format(transcript=transcript, question=question, mode=mode)

        resp = requests.post(DEEPSEEK_URL, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 500
        }, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=30)

        content = resp.json()["choices"][0]["message"]["content"].strip()
        content = content.replace("```json", "").replace("```", "").strip()
        evaluation = json.loads(content)
        return JSONResponse(evaluation)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}, content: {content if 'content' in dir() else 'N/A'}")
        return JSONResponse({"error": "Evaluation parse failed, please retry", "raw": content if 'content' in dir() else ""}, 500)
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        return JSONResponse({"error": str(e)}, 500)

# ── Conversation API ──────────────────────────────────────
@app.post("/api/conversation/start")
async def start_conversation(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    mode = data.get("mode", "part1")

    conv = ConversationState(mode=mode)
    conv.questions = PART1_QUESTIONS.copy() if mode == "part1" else PART2_TOPICS.copy()
    conv.current_question = 0
    conv.stage = "asking"
    conversations[session_id] = conv

    first = conv.questions[0]
    if mode == "part2":
        first = f"{first['topic']}\n\n{first['prompt']}"

    return JSONResponse({"mode": mode, "stage": "asking", "question": first,
                         "question_number": 0, "total_questions": len(conv.questions)})

@app.post("/api/conversation/next")
async def next_question(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")

    conv = conversations.get(session_id)
    if not conv:
        return JSONResponse({"error": "no active session"}, 400)

    conv.current_question += 1
    if conv.current_question >= len(conv.questions):
        conv.stage = "done"
        return JSONResponse({"stage": "done", "message": "🎉 Practice session complete! Great work!",
                             "history": conv.history})

    next_q = conv.questions[conv.current_question]
    if conv.mode == "part2":
        next_q = f"{next_q['topic']}\n\n{next_q['prompt']}"

    conv.stage = "asking"
    conv.last_transcript = ""
    conv.last_evaluation = {}

    return JSONResponse({"stage": "asking", "question": next_q,
                         "question_number": conv.current_question,
                         "total_questions": len(conv.questions)})

@app.post("/api/conversation/respond")
async def record_response(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    transcript = data.get("transcript", "")
    evaluation = data.get("evaluation", {})

    conv = conversations.get(session_id)
    if conv:
        conv.last_transcript = transcript
        conv.last_evaluation = evaluation
        conv.history.append({"question": conv.questions[conv.current_question],
                             "answer": transcript, "evaluation": evaluation})
    return JSONResponse({"recorded": True})

# ── Health ────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return JSONResponse({"status": "ok", "version": "3.0.0", "timestamp": datetime.now().isoformat(),
                          "tts_ready": bool(GOOGLE_API_KEY), "stt_ready": bool(GOOGLE_API_KEY),
                          "llm_ready": bool(DEEPSEEK_KEY)})

# ── Static Files ──────────────────────────────────────────
from fastapi.staticfiles import StaticFiles
import tempfile
tmpdir = tempfile.mkdtemp()
app.mount("/static", StaticFiles(directory=tmpdir), name="static")

# ── HTML Frontend ─────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<title>🎤 Bryson IELTS 陪练助手</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--accent:#38bdf8;--green:#4ade80;--red:#f87171;--text:#e2e8f0;--muted:#94a3b8}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;max-width:600px;margin:0 auto;padding:16px}
h1{font-size:1.5rem;text-align:center;margin:12px 0;background:linear-gradient(135deg,var(--accent),#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.card{background:var(--card);border-radius:16px;padding:16px;margin:12px 0}
.mode-select{display:flex;gap:8px;margin:12px 0}
.mode-btn{flex:1;padding:12px;border-radius:12px;border:2px solid var(--card);background:var(--card);color:var(--text);font-size:1rem;cursor:pointer;transition:.2s}
.mode-btn.active{border-color:var(--accent);background:rgba(56,189,248,.1)}
.question-box{background:var(--card);border-left:3px solid var(--accent);padding:14px;border-radius:0 12px 12px 0;margin:16px 0;font-size:1.05rem;line-height:1.6}
.record-controls{display:flex;flex-direction:column;align-items:center;gap:12px;margin:16px 0}
.record-btn{width:80px;height:80px;border-radius:50%;border:none;background:var(--red);cursor:pointer;transition:.2s;color:white;font-size:14px;font-weight:600}
.record-btn.recording{animation:pulse 1.5s infinite;box-shadow:0 0 0 8px rgba(248,113,113,.3)}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(248,113,113,.5)}70%{box-shadow:0 0 0 16px rgba(248,113,113,0)}100%{box-shadow:0 0 0 0 rgba(248,113,113,0)}}
.status{color:var(--muted);font-size:.85rem}
.transcript-box{background:var(--bg);border-radius:12px;padding:12px;margin:8px 0;min-height:40px;color:var(--accent);font-size:.95rem}
.eval-card{background:var(--card);border-radius:12px;padding:14px;margin:8px 0}
.eval-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05)}
.eval-row:last-child{border:none}
.score{font-weight:700;font-size:1.1rem}
.score-high{color:var(--green)}.score-mid{color:#fbbf24}.score-low{color:var(--red)}
.bar{height:6px;border-radius:3px;margin:4px 0;background:rgba(255,255,255,.1);overflow:hidden}.bar-fill{height:100%;border-radius:3px;transition:width .5s}
.highlights{color:var(--green);font-size:.9rem;margin:4px 0}.improvements{color:#fbbf24;font-size:.9rem;margin:4px 0}
.next-btn,.tts-btn{width:100%;padding:14px;border-radius:12px;border:none;background:var(--accent);color:#000;font-size:1rem;font-weight:600;cursor:pointer;margin:8px 0;display:none}
.tts-btn{background:rgba(129,140,248,.2);color:var(--accent);border:1px solid var(--accent)}
.controls-row{display:flex;gap:8px}.controls-row>*{flex:1}
.hidden{display:none!important}
.progress{text-align:center;color:var(--muted);font-size:.8rem;margin:8px 0}
@media(max-width:400px){body{padding:10px}h1{font-size:1.2rem}}
</style>
</head>
<body>
<h1>🎤 Bryson IELTS 陪练助手</h1>

<div class="mode-select">
  <button class="mode-btn active" onclick="setMode('part1')">Part 1 · 问答</button>
  <button class="mode-btn" onclick="setMode('part2')">Part 2 · 独白</button>
</div>

<div class="progress" id="progress"></div>

<div class="card question-box" id="questionBox">
  <div id="questionText">Press <b>Start</b> to begin your practice session</div>
</div>

<div class="record-controls">
  <button class="record-btn" id="recordBtn" onclick="toggleRecording()">START</button>
  <div class="status" id="status">Ready</div>
</div>

<div class="card">
  <div id="transcriptDisplay" class="transcript-box">Your response will appear here...</div>
</div>

<div class="card hidden" id="evalCard">
  <div id="evalContent"></div>
  <div class="controls-row">
    <button class="tts-btn" onclick="playFeedbackAudio()" id="ttsBtn">🔊 Play Feedback</button>
  </div>
  <button class="next-btn" onclick="nextQuestion()" id="nextBtn">Next Question →</button>
</div>

<script>
// ── State ──
let state = {mode:'part1',session:null,recording:false,mediaRecorder:null,audioChunks:[],currentTranscript:'',currentEval:null};
const API = '';

// ── Mode ──
async function setMode(m){state.mode=m;document.querySelectorAll('.mode-btn').forEach(b=>b.classList.toggle('active',b.textContent.includes(m=='part1'?'Part 1':'Part 2')));await startSession()}
async function startSession(){
  document.getElementById('evalCard').classList.add('hidden');
  document.getElementById('nextBtn').style.display='none';
  document.getElementById('ttsBtn').style.display='none';
  document.getElementById('transcriptDisplay').textContent='Your response will appear here...';
  document.getElementById('recordBtn').textContent='⏺ REC';
  document.getElementById('status').textContent='Starting session...';
  let r=await fetch(API+'/api/conversation/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:'default',mode:state.mode})});
  let d=await r.json();
  document.getElementById('questionText').textContent=d.question;
  document.getElementById('progress').textContent=`Question ${d.question_number+1}/${d.total_questions}`;
  document.getElementById('status').textContent='Ready - Press REC to answer';
}

// ── Recording (iOS Safari compatible) ──
let recordingTimer=null;
async function toggleRecording(){
  if(state.recording){await stopRecording();return}
  try{
    let stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true}});
    state.recording=true;state.audioChunks=[];
    document.getElementById('recordBtn').textContent='⏹ STOP';
    document.getElementById('recordBtn').classList.add('recording');
    document.getElementById('status').textContent='🎙 Recording...';

    // Try multiple MIME types for cross-browser compatibility
    let mimeType='audio/webm';
    let types=['audio/webm;codecs=opus','audio/webm','audio/mp4','audio/ogg;codecs=opus','audio/wav'];
    for(let t of types){if(MediaRecorder.isTypeSupported(t)){mimeType=t;break}}
    console.log('MediaRecorder using:',mimeType);

    let opts={mimeType:mimeType,audioBitsPerSecond:64000};
    state.mimeType=mimeType;
    state.mediaRecorder=new MediaRecorder(stream,opts);
    state.mediaRecorder.ondataavailable=e=>{if(e.data.size>0)state.audioChunks.push(e.data)};
    state.mediaRecorder.onstop=processRecording;
    state.mediaRecorder.onerror=e=>{document.getElementById('status').textContent='Recording error: '+(e.error?.message||'unknown');state.recording=false};
    state.mediaRecorder.start();
    // 30s auto-stop
    recordingTimer=setTimeout(()=>{if(state.recording)stopRecording()},30000);
  }catch(e){
    document.getElementById('status').textContent='Mic access denied: '+e.message;
  }
}

async function stopRecording(){
  if(recordingTimer)clearTimeout(recordingTimer);
  state.recording=false;
  if(state.mediaRecorder&&state.mediaRecorder.state!=='inactive')state.mediaRecorder.stop();
  if(state.mediaRecorder&&state.mediaRecorder.stream)state.mediaRecorder.stream.getTracks().forEach(t=>t.stop());
  document.getElementById('recordBtn').textContent='⏺ REC';
  document.getElementById('recordBtn').classList.remove('recording');
  document.getElementById('status').textContent='Processing...';
}

async function processRecording(){
  let mime=state.mimeType||'audio/webm';
  let blob=new Blob(state.audioChunks,{type:mime});
  let reader=new FileReader();
  reader.onload=async()=>{
    let b64=reader.result.split(',')[1];
    document.getElementById('status').textContent='Transcribing...';
    console.log('Sending audio:',mime,'size:',b64.length);
    let ctrl=new AbortController();
    let to=setTimeout(()=>ctrl.abort(),75000);
    let sttR;
    try {
      sttR=await fetch(API+'/api/stt',{method:'POST',signal:ctrl.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({audio:{content:b64,filename:'recording.webm',type:mime}})});
    } catch(e) {
      clearTimeout(to);
      document.getElementById('status').textContent='STT timeout - please try again';
      return;
    }
    clearTimeout(to);
    let sttD=await sttR.json();
    state.currentTranscript=sttD.transcript||'(no speech detected)';
    let conf=sttD.confidence||0;
    document.getElementById('transcriptDisplay').innerHTML=`<b>You said:</b> "${state.currentTranscript}"<br><small style="color:var(--muted)">Confidence: ${conf}%</small>`;
    document.getElementById('status').textContent='Evaluating...';
    let question=document.getElementById('questionText').textContent;
    let evalR=await fetch(API+'/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({transcript:state.currentTranscript,question:question,mode:state.mode})});
    let evalD=await evalR.json();
    if(evalD.error){document.getElementById('status').textContent='Eval error: '+evalD.error;return}
    state.currentEval=evalD;
    await fetch(API+'/api/conversation/respond',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:'default',transcript:state.currentTranscript,evaluation:evalD})});
    showEvaluation(evalD);
    document.getElementById('status').textContent='✅ Evaluation complete';
  };
  reader.readAsDataURL(blob);
}

// ── Display ──
function sc(c){return c>=7?'score-high':c>=5?'score-mid':'score-low'}
function showEvaluation(e){
  let h='';
  for(let k of['fluency','vocabulary','grammar']){
    let v=e[k]||{};
    h+=`<div class="eval-row"><span>${k==='fluency'?'🗣 Fluency':k==='vocabulary'?'📚 Vocabulary':'✏️ Grammar'}</span><span class="score ${sc(v.score)}">${v.score||'?'}/9</span></div>`;
    h+=`<div class="bar"><div class="bar-fill" style="width:${(v.score||0)*11}%;background:${v.score>=7?'var(--green)':v.score>=5?'#fbbf24':'var(--red)'}"></div></div>`;
    h+=`<div style="font-size:.85rem;color:var(--muted);margin:2px 0 6px">${v.comment||''}</div>`;
  }
  h+=`<div class="eval-row"><span><b>📊 Overall</b></span><span class="score ${sc(e.overall||0)}" style="font-size:1.3rem">${e.overall||'?'}/9</span></div>`;
  if(e.highlights)h+=`<div class="highlights">✅ ${e.highlights}</div>`;
  if(e.improvements)h+=`<div class="improvements">💡 ${e.improvements}</div>`;
  document.getElementById('evalContent').innerHTML=h;
  document.getElementById('evalCard').classList.remove('hidden');
  document.getElementById('nextBtn').style.display='block';
  document.getElementById('ttsBtn').style.display='block';
  window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'});
}

async function nextQuestion(){
  document.getElementById('evalCard').classList.add('hidden');
  document.getElementById('nextBtn').style.display='none';
  document.getElementById('ttsBtn').style.display='none';
  document.getElementById('transcriptDisplay').textContent='Your response will appear here...';
  let r=await fetch(API+'/api/conversation/next',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:'default'})});
  let d=await r.json();
  if(d.stage==='done'){document.getElementById('questionText').textContent=d.message;document.getElementById('progress').textContent='✅ Complete';document.getElementById('recordBtn').disabled=true;return}
  document.getElementById('questionText').textContent=d.question;
  document.getElementById('progress').textContent=`Question ${d.question_number+1}/${d.total_questions}`;
  document.getElementById('recordBtn').textContent='⏺ REC';
  document.getElementById('status').textContent='Ready - Press REC to answer';
}

// ── TTS playback ──
async function playFeedbackAudio(){
  let text=`Overall score: ${state.currentEval?.overall||'?'} out of 9. ${state.currentEval?.highlights||''} ${state.currentEval?.improvements||''}`;
  let r=await fetch(API+'/api/tts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:text})});
  let d=await r.json();
  if(d.audio){let a=new Audio('data:audio/mp3;base64,'+d.audio);a.play()}
}
// ── Init ──
startSession();
</script>
</body>
</html>"""

@app.get("/")
async def index():
    return HTMLResponse(HTML)

# ── Launch ────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8090))
    logger.info(f"🚀 IELTS Unified Server starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
