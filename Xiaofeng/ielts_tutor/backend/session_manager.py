"""
会话 & 历史数据持久化 · SQLite
"""
import os
import json
import sqlite3
from datetime import datetime
from threading import Lock


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ielts_tutor.db")


def _get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            mode TEXT NOT NULL,
            pipeline TEXT NOT NULL DEFAULT 'cascade',
            status TEXT DEFAULT 'active',
            transcript_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            ended_at TEXT
        );
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            speaker TEXT NOT NULL,
            text TEXT NOT NULL,
            seq INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
        CREATE TABLE IF NOT EXISTS evaluations (
            session_id TEXT PRIMARY KEY,
            overall REAL,
            fluency REAL,
            vocabulary REAL,
            grammar REAL,
            pronunciation REAL,
            summary TEXT,
            improvements TEXT,
            highlights TEXT,
            report_path TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            error_type TEXT,
            wrong TEXT,
            corrected TEXT,
            explanation TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
    """)
    conn.commit()
    conn.close()


class PersistentSessionManager:
    def __init__(self):
        self._sessions = {}  # 内存缓存
        self._lock = Lock()
        init_db()

    def create(self, sid, mode="ielts_part1", pipeline="cascade"):
        now = datetime.now().isoformat()
        with self._lock:
            self._sessions[sid] = {
                "mode": mode, "pipeline": pipeline, "status": "active",
                "transcripts": [], "transcript_count": 0, "created": now,
            }
            conn = _get_db()
            conn.execute(
                "INSERT INTO sessions(id,mode,pipeline,status,created_at) VALUES(?,?,?,?,?)",
                (sid, mode, pipeline, "active", now))
            conn.commit(); conn.close()

    def get(self, sid):
        return self._sessions.get(sid)

    def add_transcript(self, sid, speaker, text, timestamp=None):
        ts = timestamp or datetime.now().isoformat()
        with self._lock:
            if sid in self._sessions:
                s = self._sessions[sid]
                seq = s["transcript_count"]
                s["transcripts"].append({"speaker": speaker, "text": text, "time": ts, "seq": seq})
                s["transcript_count"] += 1
            conn = _get_db()
            conn.execute(
                "INSERT INTO transcripts(session_id,speaker,text,seq,timestamp) VALUES(?,?,?,?,?)",
                (sid, speaker, text, s.get("transcript_count", 0) if sid in self._sessions else 0, ts))
            conn.execute("UPDATE sessions SET transcript_count=transcript_count+1 WHERE id=?", (sid,))
            conn.commit(); conn.close()

    def save_evaluation(self, sid, scores, report_path=None):
        now = datetime.now().isoformat()
        conn = _get_db()
        conn.execute("""
            INSERT OR REPLACE INTO evaluations
            (session_id,overall,fluency,vocabulary,grammar,pronunciation,summary,improvements,highlights,report_path,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (
            sid,
            scores.get("overall"), scores.get("fluency"), scores.get("vocabulary"),
            scores.get("grammar"), scores.get("pronunciation"),
            scores.get("summary", ""),
            json.dumps(scores.get("improvements", [])),
            json.dumps(scores.get("highlights", [])),
            report_path, now))
        if scores.get("improvements"):
            for imp in scores["improvements"]:
                parts = imp.split("→")
                wrong = parts[0].replace("~~", "").strip() if parts else ""
                corrected = parts[1].split("—")[0].replace("**", "").strip() if len(parts) > 1 else ""
                explanation = parts[1].split("—")[1].strip() if len(parts) > 1 and "—" in parts[1] else ""
                conn.execute(
                    "INSERT INTO errors(session_id,error_type,wrong,corrected,explanation,timestamp) VALUES(?,?,?,?,?,?)",
                    (sid, "grammar", wrong, corrected, explanation, now))
        conn.commit(); conn.close()

    def end_session(self, sid):
        now = datetime.now().isoformat()
        with self._lock:
            if sid in self._sessions:
                self._sessions[sid]["status"] = "ended"
        conn = _get_db()
        conn.execute("UPDATE sessions SET status='ended',ended_at=? WHERE id=?", (now, sid))
        conn.commit(); conn.close()

    def get_history(self, limit=20, mode=None):
        conn = _get_db()
        q = "SELECT s.*, e.overall,e.report_path FROM sessions s LEFT JOIN evaluations e ON s.id=e.session_id"
        params = []
        if mode:
            q += " WHERE s.mode=?"
            params.append(mode)
        q += " ORDER BY s.created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_weakness_profile(self, limit=50):
        """跨会话薄弱点统计"""
        conn = _get_db()
        rows = conn.execute(
            "SELECT error_type,wrong,corrected,COUNT(*) as freq FROM errors GROUP BY wrong ORDER BY freq DESC LIMIT ?",
            (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_transcripts(self, sid):
        conn = _get_db()
        rows = conn.execute(
            "SELECT * FROM transcripts WHERE session_id=? ORDER BY seq", (sid,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update(self, sid, **kwargs):
        with self._lock:
            if sid in self._sessions:
                self._sessions[sid].update(kwargs)

    def remove(self, sid):
        with self._lock:
            self._sessions.pop(sid, None)

    def __len__(self):
        return len(self._sessions)
