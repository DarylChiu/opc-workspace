"""
用户系统 v1.5.0 P1 — users + auth_tokens + PBKDF2 + token 鉴权 + 基础限流
- 增量式: 只加不改现有功能; AUTH_REQUIRED=0 时所有现有路由照旧 (guest 模式)
- 多用户数据隔离在 P2 接入 (sessions/transcripts/ft_memory/question_progress 挂 user_id)
"""
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ielts_tutor.db")

# 强制登录开关: P1 默认关 (0), P2 数据隔离完成后置 1
AUTH_REQUIRED = os.environ.get("AUTH_REQUIRED", "0") == "1"

TOKEN_TTL_DAYS = 30
PBKDF2_ITERATIONS = 200_000

# 基础限流 (进程内): ip -> [timestamps]
_login_attempts = {}
_register_attempts = {}
MAX_LOGIN_PER_10MIN = 20
MAX_REGISTER_PER_HOUR = 5


def _get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT DEFAULT '',
            plan TEXT DEFAULT 'free',
            monthly_quota_tokens INTEGER DEFAULT 200000,
            created_at TEXT NOT NULL,
            last_active TEXT
        );
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_tokens_user ON auth_tokens(user_id);
    """)
    conn.commit()
    conn.close()


# ── 密码哈希 (PBKDF2-HMAC-SHA256, 标准库零依赖) ──

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


# ── 限流 ──

def _rate_check(bucket, limit, window_secs, key):
    now = time.time()
    bucket[key] = [t for t in bucket.get(key, []) if now - t < window_secs]
    if len(bucket[key]) >= limit:
        return False
    bucket[key].append(now)
    return True


# ── 核心操作 ──

def register(email: str, password: str, display_name: str = "", ip: str = "local"):
    """注册; 返回 (ok, payload|error_msg)"""
    email = (email or "").strip().lower()
    if not email or "@" not in email or len(email) > 200:
        return False, "邮箱格式不正确"
    if not password or len(password) < 6:
        return False, "密码至少 6 位"
    if not _rate_check(_register_attempts, MAX_REGISTER_PER_HOUR, 3600, ip):
        return False, "注册太频繁，请 1 小时后再试"
    conn = _get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users(email, password_hash, display_name, created_at) VALUES(?,?,?,?)",
            (email, hash_password(password), (display_name or "").strip()[:60],
             datetime.now().isoformat()))
        uid = cur.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False, "该邮箱已注册"
    token = _issue_token(conn, uid)
    conn.close()
    return True, {"user": _user_dict(uid), "token": token}


def login(email: str, password: str, ip: str = "local"):
    email = (email or "").strip().lower()
    if not _rate_check(_login_attempts, MAX_LOGIN_PER_10MIN, 600, ip):
        return False, "登录尝试过多，请 10 分钟后再试"
    conn = _get_db()
    row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        conn.close()
        return False, "邮箱或密码错误"
    conn.execute("UPDATE users SET last_active=? WHERE id=?", (datetime.now().isoformat(), row["id"]))
    conn.commit()
    token = _issue_token(conn, row["id"])
    conn.close()
    return True, {"user": _user_dict(row["id"]), "token": token}


def _issue_token(conn, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now()
    conn.execute(
        "INSERT INTO auth_tokens(token, user_id, created_at, expires_at) VALUES(?,?,?,?)",
        (token, user_id, now.isoformat(), (now + timedelta(days=TOKEN_TTL_DAYS)).isoformat()))
    conn.commit()
    return token


def logout(token: str):
    conn = _get_db()
    conn.execute("DELETE FROM auth_tokens WHERE token=?", (token,))
    conn.commit()
    conn.close()


def get_user_by_token(token: str):
    """token → user dict 或 None (过期/不存在返回 None)"""
    if not token:
        return None
    conn = _get_db()
    row = conn.execute(
        "SELECT u.* FROM auth_tokens t JOIN users u ON u.id=t.user_id "
        "WHERE t.token=? AND t.expires_at>?", (token, datetime.now().isoformat())).fetchone()
    conn.close()
    return dict(row) if row else None


def _user_dict(uid: int):
    conn = _get_db()
    row = conn.execute("SELECT id, email, display_name, plan, monthly_quota_tokens, created_at, last_active "
                       "FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return dict(row) if row else None
