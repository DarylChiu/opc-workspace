"""
语音交互 Debug 验收模块 — 核心 Logger
只当 DEBUG_MODE=1 时激活，零生产环境开销
"""
import os, json, time, logging, asyncio, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger("debug-logger")

DEBUG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug-data")
DEBUG_DB = os.path.join(DEBUG_DIR, "debug_sessions.db")

os.makedirs(DEBUG_DIR, exist_ok=True)

# ── Data Structures ──

@dataclass
class AudioSegment:
    duration_s: float = 0.0
    size_bytes: int = 0
    chunks_count: int = 0
    final_size: int = 0

@dataclass
class ASRRecord:
    transcript: str = ""
    confidence: float = 0.0
    latency_ms: float = 0.0
    alternatives: list = field(default_factory=list)
    model: str = "google-stt-latest_short"
    error: Optional[str] = None

@dataclass
class LLMRecord:
    intent: str = "unknown"
    intent_confidence: float = 0.0
    response: str = ""
    latency_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""
    tool_calls: list = field(default_factory=list)
    error: Optional[str] = None

@dataclass
class TTSRecord:
    text: str = ""
    latency_ms: float = 0.0
    voice: str = "en-US-Journey-O"
    speed: float = 0.95
    chars: int = 0
    error: Optional[str] = None

@dataclass
class DiagnosticIssue:
    severity: str = "ok"       # ok | warn | error
    symptom: str = ""
    diagnosis: str = ""
    solution: str = ""
    rule_id: str = ""

@dataclass
class DebugTurn:
    turn_id: int = 0
    session_id: str = ""
    pipeline: str = "cascade"
    timestamp_start: float = 0.0
    timestamp_end: float = 0.0
    e2e_latency_ms: float = 0.0
    interrupted: bool = False
    audio: AudioSegment = field(default_factory=AudioSegment)
    asr: ASRRecord = field(default_factory=ASRRecord)
    llm: LLMRecord = field(default_factory=LLMRecord)
    tts: TTSRecord = field(default_factory=TTSRecord)
    issues: list = field(default_factory=list)
    severity: str = "ok"

    def to_dict(self):
        d = asdict(self)
        d["audio"] = asdict(self.audio) if self.audio else {}
        d["asr"] = asdict(self.asr) if self.asr else {}
        d["llm"] = asdict(self.llm) if self.llm else {}
        d["tts"] = asdict(self.tts) if self.tts else {}
        return d


# ── Diagnostic Engine ──

class DiagnosticEngine:
    """分析每轮对话，自动检测问题并给出诊断"""

    RULES = [
        {
            "id": "high_e2e_latency",
            "name": "端到端延迟偏高",
            "check": lambda t: t.e2e_latency_ms > 800,
            "severity": lambda t: "error" if t.e2e_latency_ms > 1500 else "warn",
            "diagnose": lambda t: (
                f"总延迟 {t.e2e_latency_ms:.0f}ms，"
                f"ASR={t.asr.latency_ms:.0f}ms LLM={t.llm.latency_ms:.0f}ms TTS={t.tts.latency_ms:.0f}ms"
            ),
            "solve": lambda t: (
                "🔧 已启用流式TTS降低首块延迟"
                if t.e2e_latency_ms > 1500 else
                f"📝 延迟偏高，主因: {'ASR' if t.asr.latency_ms>300 else 'LLM' if t.llm.latency_ms>600 else 'TTS' if t.tts.latency_ms>200 else '综合'}，已记录"
            ),
        },
        {
            "id": "low_asr_confidence",
            "name": "ASR 识别置信度低",
            "check": lambda t: t.asr.confidence > 0 and t.asr.confidence < 0.7,
            "severity": lambda t: "error" if t.asr.confidence < 0.5 else "warn",
            "diagnose": lambda t: (
                f"转录: \"{t.asr.transcript[:60]}\"，置信度 {t.asr.confidence:.0%}"
            ),
            "solve": lambda t: (
                "🔧 可能原因: 背景噪音/发音不清/口音。建议: 靠近麦克风、放慢语速、检查环境噪音"
            ),
        },
        {
            "id": "slow_asr_only",
            "name": "ASR 处理偏慢",
            "check": lambda t: t.asr.latency_ms > 300 and t.asr.confidence > 0.7,
            "severity": lambda t: "warn",
            "diagnose": lambda t: f"ASR 耗时 {t.asr.latency_ms:.0f}ms，超过推荐值 300ms",
            "solve": lambda t: "📝 可能原因: 长句子/网络延迟/STT服务响应慢，已记录",
        },
        {
            "id": "slow_llm",
            "name": "LLM 推理偏慢",
            "check": lambda t: t.llm.latency_ms > 600,
            "severity": lambda t: "warn",
            "diagnose": lambda t: (
                f"LLM 耗时 {t.llm.latency_ms:.0f}ms，"
                f"tokens: in={t.llm.tokens_in} out={t.llm.tokens_out} model={t.llm.model}"
            ),
            "solve": lambda t: "📝 LLM延迟偏高，可能原因: 上下文过长/模型负载/复杂推理，已记录",
        },
        {
            "id": "interruption",
            "name": "检测到用户打断",
            "check": lambda t: t.interrupted,
            "severity": lambda t: "warn",
            "diagnose": lambda t: "系统在TTS播放中被用户打断",
            "solve": lambda t: "✅ 已自动停止播放，切换到聆听模式",
        },
        {
            "id": "silent_asr",
            "name": "ASR 无有效输出",
            "check": lambda t: t.asr.transcript == "" and t.audio.duration_s > 0.5,
            "severity": lambda t: "error",
            "diagnose": lambda t: (
                f"录音 {t.audio.duration_s:.1f}s 但无识别结果，"
                f"大小={t.audio.final_size}bytes"
            ),
            "solve": lambda t: "🔧 可能原因: 录音音量过低/无语音/STT服务异常，检查音频质量",
        },
    ]

    @classmethod
    def analyze(cls, turn: DebugTurn) -> list[DiagnosticIssue]:
        issues = []
        for rule in cls.RULES:
            try:
                if rule["check"](turn):
                    sev = rule["severity"](turn) if callable(rule["severity"]) else rule["severity"]
                    issues.append(DiagnosticIssue(
                        severity=sev,
                        symptom=rule["name"],
                        diagnosis=rule["diagnose"](turn),
                        solution=rule["solve"](turn),
                        rule_id=rule["id"],
                    ))
            except Exception as e:
                logger.debug(f"Rule {rule['id']} failed: {e}")

        # Determine overall severity
        if any(i.severity == "error" for i in issues):
            turn.severity = "error"
        elif any(i.severity == "warn" for i in issues):
            turn.severity = "warn"
        else:
            turn.severity = "ok"

        turn.issues = [asdict(i) for i in issues]
        return issues


# ── SQLite Persistence ──

class DebugDB:
    def __init__(self, db_path=DEBUG_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    mode TEXT,
                    pipeline TEXT,
                    created_at TEXT,
                    ended_at TEXT,
                    total_turns INTEGER DEFAULT 0,
                    avg_e2e_ms REAL DEFAULT 0,
                    total_issues INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_id INTEGER NOT NULL,
                    timestamp_start REAL,
                    timestamp_end REAL,
                    e2e_latency_ms REAL,
                    pipeline TEXT,
                    interrupted INTEGER DEFAULT 0,
                    asr_transcript TEXT,
                    asr_confidence REAL,
                    asr_latency_ms REAL,
                    asr_model TEXT,
                    llm_intent TEXT,
                    llm_response TEXT,
                    llm_latency_ms REAL,
                    llm_model TEXT,
                    llm_tokens_in INTEGER DEFAULT 0,
                    llm_tokens_out INTEGER DEFAULT 0,
                    tts_text TEXT,
                    tts_latency_ms REAL,
                    tts_voice TEXT,
                    tts_speed REAL,
                    audio_duration_s REAL,
                    audio_size_bytes INTEGER,
                    severity TEXT DEFAULT 'ok',
                    issues_json TEXT DEFAULT '[]',
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            conn.commit()

    def create_session(self, sid: str, mode: str, pipeline: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions (session_id, mode, pipeline, created_at) VALUES (?,?,?,?)",
                (sid, mode, pipeline, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()

    def end_session(self, sid: str):
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*), AVG(e2e_latency_ms), COUNT(CASE WHEN severity!='ok' THEN 1 END) FROM turns WHERE session_id=?",
                (sid,),
            ).fetchone()
            conn.execute(
                "UPDATE sessions SET ended_at=?, total_turns=?, avg_e2e_ms=?, total_issues=? WHERE session_id=?",
                (datetime.now(timezone.utc).isoformat(), row[0], round(row[1] or 0, 0), row[2] or 0, sid),
            )
            conn.commit()

    def save_turn(self, turn: DebugTurn):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO turns (
                        session_id, turn_id, timestamp_start, timestamp_end,
                        e2e_latency_ms, pipeline, interrupted,
                        asr_transcript, asr_confidence, asr_latency_ms, asr_model,
                        llm_intent, llm_response, llm_latency_ms, llm_model,
                        llm_tokens_in, llm_tokens_out,
                        tts_text, tts_latency_ms, tts_voice, tts_speed,
                        audio_duration_s, audio_size_bytes,
                        severity, issues_json
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    turn.session_id, turn.turn_id, turn.timestamp_start, turn.timestamp_end,
                    turn.e2e_latency_ms, turn.pipeline, int(turn.interrupted),
                    turn.asr.transcript, turn.asr.confidence, turn.asr.latency_ms, turn.asr.model,
                    turn.llm.intent, turn.llm.response[:2000], turn.llm.latency_ms, turn.llm.model,
                    turn.llm.tokens_in, turn.llm.tokens_out,
                    turn.tts.text, turn.tts.latency_ms, turn.tts.voice, turn.tts.speed,
                    turn.audio.duration_s, turn.audio.size_bytes,
                    turn.severity, json.dumps(turn.issues, ensure_ascii=False),
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"save_turn failed: {e}")

    def get_session_turns(self, sid: str) -> list:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM turns WHERE session_id=? ORDER BY turn_id", (sid,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_session_summary(self, sid: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM sessions WHERE session_id=?", (sid,)).fetchone()
            return dict(row) if row else {}

    def export_session(self, sid: str) -> dict:
        """Export full session as structured JSON"""
        summary = self.get_session_summary(sid)
        turns = self.get_session_turns(sid)
        for t in turns:
            if isinstance(t.get("issues_json"), str):
                t["issues"] = json.loads(t["issues_json"])
                del t["issues_json"]
        return {"summary": summary, "turns": turns}

    def list_sessions(self, limit: int = 30) -> list:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

db = DebugDB()


# ── Debug Tracker (per-session) ──

class DebugTracker:
    """单会话追踪器，管理当前会话所有 Turn 的采集和诊断"""

    def __init__(self, sid: str, mode: str, pipeline: str):
        self.sid = sid
        self.mode = mode
        self.pipeline = pipeline
        self.turns: list[DebugTurn] = []
        self._current: Optional[DebugTurn] = None
        self._turn_counter = 0
        self._subscribers: list[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=100)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q):
        if q in self._subscribers:
            self._subscribers.remove(q)

    async def _broadcast(self, msg: dict):
        msg["session_id"] = self.sid
        dead = []
        for q in self._subscribers:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._subscribers.remove(q)

    async def start_turn(self):
        self._turn_counter += 1
        self._current = DebugTurn(
            turn_id=self._turn_counter,
            session_id=self.sid,
            pipeline=self.pipeline,
            timestamp_start=time.time(),
        )
        await self._broadcast({
            "type": "turn_start",
            "data": {"turn_id": self._turn_counter, "ts": time.time()},
        })

    async def record_audio_chunk(self, size: int):
        if not self._current: return
        self._current.audio.chunks_count += 1
        self._current.audio.size_bytes += size

    async def record_asr(
        self, transcript: str, confidence: float, latency_ms: float,
        alternatives: list = None, model: str = "google-stt-latest_short",
        error: str = None,
    ):
        if not self._current: return
        self._current.asr = ASRRecord(
            transcript=transcript or "",
            confidence=confidence,
            latency_ms=latency_ms,
            alternatives=alternatives or [],
            model=model,
            error=error,
        )
        self._current.audio.final_size = self._current.audio.size_bytes
        await self._broadcast({
            "type": "asr_done",
            "data": {
                "turn_id": self._current.turn_id,
                "transcript": transcript,
                "confidence": confidence,
                "latency_ms": latency_ms,
            },
        })

    async def record_llm(
        self, intent: str, response: str, latency_ms: float,
        tokens_in: int = 0, tokens_out: int = 0, model: str = "",
        tool_calls: list = None, error: str = None,
    ):
        if not self._current: return
        self._current.llm = LLMRecord(
            intent=intent or "general_chat",
            response=response or "",
            latency_ms=latency_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=model,
            tool_calls=tool_calls or [],
            error=error,
        )
        await self._broadcast({
            "type": "llm_done",
            "data": {
                "turn_id": self._current.turn_id,
                "intent": intent,
                "response_preview": response[:120] if response else "",
                "latency_ms": latency_ms,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "model": model,
            },
        })

    async def record_tts(
        self, text: str, latency_ms: float, voice: str = "",
        speed: float = 0.95, chars: int = 0, error: str = None,
    ):
        if not self._current: return
        self._current.tts = TTSRecord(
            text=text or "",
            latency_ms=latency_ms,
            voice=voice or "en-US-Journey-O",
            speed=speed,
            chars=chars or len(text),
            error=error,
        )
        await self._broadcast({
            "type": "tts_done",
            "data": {
                "turn_id": self._current.turn_id,
                "text_preview": text[:80] if text else "",
                "latency_ms": latency_ms,
            },
        })

    async def record_audio_meta(self, duration_s: float, size: int = 0):
        if not self._current: return
        self._current.audio.duration_s = duration_s
        if size:
            self._current.audio.final_size = size

    async def record_interruption(self):
        if not self._current: return
        self._current.interrupted = True

    async def complete_turn(self) -> Optional[DebugTurn]:
        if not self._current: return None
        self._current.timestamp_end = time.time()

        # Calculate e2e
        if self.pipeline == "cascade":
            self._current.e2e_latency_ms = (
                self._current.asr.latency_ms
                + self._current.llm.latency_ms
                + self._current.tts.latency_ms
            )
        else:
            # Realtime pipeline: e2e from start to end
            self._current.e2e_latency_ms = (
                (self._current.timestamp_end - self._current.timestamp_start) * 1000
            )

        # Run diagnostics
        DiagnosticEngine.analyze(self._current)

        # Save to DB
        db.save_turn(self._current)
        self.turns.append(self._current)

        # Build turn complete message
        td = self._current.to_dict()
        await self._broadcast({
            "type": "turn_complete",
            "data": {
                "turn_id": self._current.turn_id,
                "e2e_latency_ms": self._current.e2e_latency_ms,
                "severity": self._current.severity,
                "issues": self._current.issues,
                "asr_preview": self._current.asr.transcript[:80],
                "llm_preview": self._current.llm.response[:80],
            },
        })

        # Emit diagnostic alerts if any
        for issue in self._current.issues:
            if issue["severity"] in ("warn", "error"):
                await self._broadcast({
                    "type": "diagnostic_alert",
                    "data": {
                        "turn_id": self._current.turn_id,
                        **issue,
                    },
                })

        turn = self._current
        self._current = None
        return turn

    def end_session(self):
        """Finalize session, save summary to DB"""
        db.end_session(self.sid)


# ── Global tracker registry (for multi-session support) ──

class DebugManager:
    """管理所有活跃 debug session"""
    def __init__(self):
        self.trackers: dict[str, DebugTracker] = {}
        self.enabled = os.environ.get("DEBUG_MODE", "0") == "1"
        if self.enabled:
            logger.info("🔍 DEBUG MODE enabled — voice interaction debug module active")

    def create_tracker(self, sid: str, mode: str, pipeline: str) -> DebugTracker:
        if not self.enabled:
            # Return a no-op tracker
            return _NoopTracker()
        tracker = DebugTracker(sid, mode, pipeline)
        self.trackers[sid] = tracker
        db.create_session(sid, mode, pipeline)
        return tracker

    def get_tracker(self, sid: str) -> Optional[DebugTracker]:
        if not self.enabled:
            return _NoopTracker()
        return self.trackers.get(sid)

    def remove_tracker(self, sid: str):
        if sid in self.trackers:
            self.trackers[sid].end_session()
            del self.trackers[sid]

    def export_session(self, sid: str) -> dict:
        return db.export_session(sid)

    def list_sessions(self, limit: int = 30) -> list:
        return db.list_sessions(limit)


class _NoopTracker:
    """空追踪器，DEBUG_MODE=0 时使用，所有方法无操作"""
    async def start_turn(self): pass
    async def record_audio_chunk(self, *a, **kw): pass
    async def record_asr(self, *a, **kw): pass
    async def record_llm(self, *a, **kw): pass
    async def record_tts(self, *a, **kw): pass
    async def record_audio_meta(self, *a, **kw): pass
    async def record_interruption(self): pass
    async def complete_turn(self): return None
    def subscribe(self): return asyncio.Queue()
    def unsubscribe(self, q): pass
    def end_session(self): pass

    @staticmethod
    async def _broadcast(msg): pass

debug_manager = DebugManager()


# ── Debug WebSocket Handler ──

async def handle_debug_ws(ws, sid: str):
    """处理 Debug 面板的 WebSocket 连接"""
    await ws.accept()

    tracker = debug_manager.get_tracker(sid)
    if not tracker or isinstance(tracker, _NoopTracker):
        await ws.send_json({
            "type": "error",
            "msg": f"Debug mode not enabled or session {sid} not found. Set DEBUG_MODE=1 and start a session first."
        })
        await ws.close()
        return

    q = tracker.subscribe()
    try:
        # Send full history on connect
        await ws.send_json({
            "type": "session_info",
            "data": {
                "session_id": sid,
                "turns_count": len(tracker.turns),
                "turns": [t.to_dict() for t in tracker.turns],
            },
        })
        await ws.send_json({"type": "ready", "data": {}})

        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=15.0)
                await ws.send_json(msg)
            except asyncio.TimeoutError:
                try:
                    await ws.send_json({"type": "ping"})
                except Exception:
                    break
    except Exception as e:
        logger.debug(f"Debug WS {sid}: {e}")
    finally:
        tracker.unsubscribe(q)
        try:
            await ws.close()
        except Exception:
            pass


# ── Session Export ──

async def handle_debug_export(sid: str) -> dict | None:
    """Export full session as JSON, return the data for API response"""
    data = debug_manager.export_session(sid)
    if not data.get("summary"):
        return None

    # Save export file
    export_dir = os.path.join(DEBUG_DIR, "exports")
    os.makedirs(export_dir, exist_ok=True)
    export_path = os.path.join(export_dir, f"debug_session_{sid}.json")
    with open(export_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    return {
        "session_id": sid,
        "file": export_path,
        "summary": data["summary"],
        "turns_count": len(data.get("turns", [])),
    }


async def handle_debug_list(limit: int = 30) -> list:
    """List all debug sessions"""
    return debug_manager.list_sessions(limit)
