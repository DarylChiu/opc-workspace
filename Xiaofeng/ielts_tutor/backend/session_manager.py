"""
会话 & 历史数据持久化 · SQLite
"""
import os
import json
import re
import sqlite3
from datetime import datetime
from threading import Lock


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ielts_tutor.db")

# v1.1.0 M1: improvements 文本解析（"You said ~~wrong~~ → **corrected** — explanation"）
_RE_CORRECTED = re.compile(r"\u2192\s*\*\*(.+?)\*\*")
_RE_WRONG = re.compile(r"~~(.+?)~~")
_CATEGORY_HINTS = [
    ("pronunciation", ("pronounce", "pronunciation", "sound", "stress")),
    ("vocab", ("vocabulary", "word choice", "phrase", "expression", "informal", "natural")),
    ("grammar", ("tense", "plural", "gerund", "article", "grammar", "structure", "sentence")),
]


def parse_improvement(imp: str):
    """从一条 improvement 文本提取 (target_text, context, category)；无法提取返回 None"""
    m = _RE_CORRECTED.search(imp)
    if not m:
        return None
    target = m.group(1).strip().rstrip(".。")
    if len(target.split()) < 2:  # 单词级目标句无跟读价值
        return None
    explanation = imp.split("—", 1)[1].strip() if "—" in imp else ""
    low = (imp + " " + explanation).lower()
    category = "grammar"
    for cat, kws in _CATEGORY_HINTS:
        if any(k in low for k in kws):
            category = cat
            break
    return {"target_text": target, "context": imp.strip(), "category": category}


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
        -- v1.1.0 M1: 跟读复习项（从 improvements 派生，带巩固状态）
        CREATE TABLE IF NOT EXISTS review_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_session_id TEXT,
            target_text TEXT NOT NULL,
            context TEXT,
            category TEXT DEFAULT 'grammar',
            status TEXT DEFAULT 'pending',
            review_count INTEGER DEFAULT 0,
            best_score REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            last_reviewed_at TEXT,
            next_due_at TEXT
        );
        -- v1.1.0 M1: 跟读尝试明细
        CREATE TABLE IF NOT EXISTS shadow_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_item_id INTEGER NOT NULL,
            user_transcript TEXT,
            score REAL,
            wer REAL,
            audio_ms INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (review_item_id) REFERENCES review_items(id)
        );
        CREATE INDEX IF NOT EXISTS idx_review_status ON review_items(status, created_at);
        CREATE INDEX IF NOT EXISTS idx_attempts_item ON shadow_attempts(review_item_id);
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
        # v1.1.0 M1: 评估后自动把 To Improve 灌入跟读队列
        try:
            self.enqueue_review_items(sid, scores.get("improvements") or [])
        except Exception:
            pass  # 队列灌库失败不影响评估主流程

    # ── v1.1.0 M1: 跟读复习数据层 ──

    def enqueue_review_items(self, sid, improvements):
        """把评估 improvements 解析为可跟读的目标句入库（同 target_text 全局去重）；返回新入库条数"""
        if not improvements:
            return 0
        now = datetime.now().isoformat()
        conn = _get_db()
        added = 0
        for imp in improvements:
            parsed = parse_improvement(imp) if isinstance(imp, str) else None
            if not parsed:
                continue
            dup = conn.execute(
                "SELECT id FROM review_items WHERE lower(target_text)=lower(?) LIMIT 1",
                (parsed["target_text"],)).fetchone()
            if dup:
                continue
            conn.execute(
                "INSERT INTO review_items(source_session_id,target_text,context,category,created_at) VALUES(?,?,?,?,?)",
                (sid, parsed["target_text"], parsed["context"], parsed["category"], now))
            added += 1
        conn.commit(); conn.close()
        return added

    def get_review_queue(self, limit=8):
        """今日跟读队列：未巩固项，新错优先"""
        conn = _get_db()
        rows = conn.execute(
            "SELECT * FROM review_items WHERE status='pending' ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def record_shadow_attempt(self, item_id, transcript, score, wer, audio_ms=0):
        """记录一次跟读；回写 review_count/best_score/last_reviewed_at"""
        now = datetime.now().isoformat()
        conn = _get_db()
        conn.execute(
            "INSERT INTO shadow_attempts(review_item_id,user_transcript,score,wer,audio_ms,created_at) VALUES(?,?,?,?,?,?)",
            (item_id, transcript, score, wer, audio_ms, now))
        conn.execute(
            "UPDATE review_items SET review_count=review_count+1, best_score=MAX(best_score,?), last_reviewed_at=? WHERE id=?",
            (score, now, item_id))
        conn.commit(); conn.close()

    def mark_consolidated(self, item_id):
        conn = _get_db()
        conn.execute("UPDATE review_items SET status='consolidated' WHERE id=?", (item_id,))
        conn.commit(); conn.close()

    def get_review_list(self, limit=100, status=None):
        """To Improve 累积清单（Dashboard 用），含跟读次数/最佳分"""
        conn = _get_db()
        q = "SELECT * FROM review_items"
        params = []
        if status:
            q += " WHERE status=?"
            params.append(status)
        q += " ORDER BY status='pending' DESC, created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_progress_stats(self, days=30):
        """Dashboard 周期统计：分数趋势 + 练习日历 + 汇总卡"""
        conn = _get_db()
        cutoff = f"-{int(days)} days"
        trend = [dict(r) for r in conn.execute("""
            SELECT substr(e.created_at,1,10) AS day, s.mode,
                   e.overall, e.fluency, e.vocabulary, e.grammar, e.pronunciation,
                   e.session_id, e.report_path
            FROM evaluations e JOIN sessions s ON s.id=e.session_id
            WHERE e.overall IS NOT NULL AND e.overall > 0
              AND e.created_at >= datetime('now', 'localtime', ?)
            ORDER BY e.created_at""", (cutoff,)).fetchall()]
        calendar = [dict(r) for r in conn.execute("""
            SELECT substr(created_at,1,10) AS day, COUNT(*) AS count
            FROM sessions
            WHERE created_at >= datetime('now', 'localtime', ?)
            GROUP BY day ORDER BY day""", (cutoff,)).fetchall()]
        week = conn.execute("""
            SELECT COUNT(*) AS sessions_7d,
                   (SELECT COUNT(*) FROM evaluations WHERE overall>0 AND created_at >= datetime('now','localtime','-7 days')) AS evals_7d,
                   (SELECT MAX(overall) FROM evaluations WHERE created_at >= datetime('now','localtime','-7 days')) AS best_7d
            FROM sessions WHERE created_at >= datetime('now','localtime','-7 days')""").fetchone()
        review = conn.execute("""
            SELECT COUNT(*) AS total,
                   SUM(status='pending') AS pending,
                   SUM(status='consolidated') AS consolidated,
                   SUM(CASE WHEN substr(created_at,1,10)=date('now','localtime') THEN 1 ELSE 0 END) AS added_today
            FROM review_items""").fetchone()
        conn.close()
        return {
            "trend": trend,
            "calendar": calendar,
            "week": dict(week) if week else {},
            "review": dict(review) if review else {},
        }

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
