"""
题库引擎 v1.4.1 — Part1/Part2/Part3 抽题 + 已练去重 + 槽位变体 (A+B)
- A 结构化真题种子库: data/question_bank.json (Part1 30话题 / Part2 60卡 / Part3 30主题)
- B LLM 变体: 槽位卡随机填充 → 60卡 × 变体 ≈ 100+ 组合
- 去重: question_progress 表, 全部练过自动重置轮换
"""
import json
import os
import random
import sqlite3
from datetime import datetime

BANK_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "question_bank.json")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ielts_tutor.db")

_bank = None


def _load_bank():
    global _bank
    if _bank is None:
        with open(BANK_PATH, encoding="utf-8") as f:
            _bank = json.load(f)
    return _bank


def _get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS question_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'local',
        mode TEXT NOT NULL,
        question_id TEXT NOT NULL,
        picked_at TEXT NOT NULL
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qp ON question_progress(user_id, mode, question_id)")
    conn.commit()
    conn.close()


def _fill_slots(card):
    """槽位随机填充: 'Describe {x} you admire' + slots{x:[...]} → 具体标题"""
    title = card["title"]
    if "slots" not in card:
        return title
    for k, opts in card["slots"].items():
        title = title.replace("{" + k + "}", random.choice(opts))
    return title


def _practiced_ids(mode, user_id="local"):
    conn = _get_db()
    rows = conn.execute(
        "SELECT question_id FROM question_progress WHERE user_id=? AND mode=?",
        (user_id, mode)).fetchall()
    conn.close()
    return {r["question_id"] for r in rows}


def _mark_practiced(mode, qid, user_id="local"):
    conn = _get_db()
    conn.execute(
        "INSERT INTO question_progress(user_id, mode, question_id, picked_at) VALUES(?,?,?,?)",
        (user_id, mode, qid, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def _pick_unseen(candidates, mode, user_id="local"):
    """优先抽未练过的; 全部练过 → 重置轮换 (去重周期 = 题库大小)"""
    done = _practiced_ids(mode, user_id)
    fresh = [c for c in candidates if c["id"] not in done]
    pool = fresh or candidates
    return random.choice(pool)


def pick_part1(user_id="local"):
    bank = _load_bank()
    t = _pick_unseen(bank["part1"]["topics"], "ielts_part1", user_id)
    _mark_practiced("ielts_part1", t["id"], user_id)
    return {"mode": "ielts_part1", "topic": t["topic"], "questions": t["questions"],
            "question_id": t["id"]}


def pick_part2(user_id="local"):
    bank = _load_bank()
    # 跨主题全局去重: 所有卡合并为一个池, 避免单主题耗尽后重复 (v1.4.1 fix)
    all_cards = []
    card_theme = {}
    for theme, cards in bank["part2"]["themes"].items():
        for c in cards:
            all_cards.append(c)
            card_theme[c["id"]] = theme
    c = _pick_unseen(all_cards, "ielts_part2", user_id)
    _mark_practiced("ielts_part2", c["id"], user_id)
    return {"mode": "ielts_part2", "theme": card_theme[c["id"]], "title": _fill_slots(c),
            "prompts": c["prompts"], "follow_ups": c.get("follow_ups", []),
            "question_id": c["id"]}


def pick_part3(user_id="local"):
    bank = _load_bank()
    t = _pick_unseen(bank["part3"]["themes"], "ielts_part3", user_id)
    _mark_practiced("ielts_part3", t["id"], user_id)
    return {"mode": "ielts_part3", "theme": t["theme"], "questions": t["questions"],
            "question_id": t["id"]}


def safe_pick(mode, user_id="local"):
    """带兜底的抽题入口 — 题库异常时返回 None, 调用方回退硬编码"""
    try:
        if mode == "ielts_part1":
            return pick_part1(user_id)
        if mode == "ielts_part2":
            return pick_part2(user_id)
        if mode == "ielts_part3":
            return pick_part3(user_id)
    except Exception:
        return None
    return None


def stats(user_id="local"):
    conn = _get_db()
    rows = conn.execute(
        "SELECT mode, COUNT(DISTINCT question_id) c FROM question_progress "
        "WHERE user_id=? GROUP BY mode", (user_id,)).fetchall()
    conn.close()
    return {r["mode"]: r["c"] for r in rows}


if __name__ == "__main__":
    init_db()
    print("已练过:", stats())
    for m in ("ielts_part1", "ielts_part2", "ielts_part3"):
        p = safe_pick(m)
        print(f"\n[{m}] {p['question_id']} | {p.get('topic') or p.get('theme') or p.get('title')}")
        print("  种子:", (p.get("questions") or [p["title"]])[:1])
