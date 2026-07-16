"""v1.1.0 M1 数据层单元测试 — review_items / shadow_attempts / 6方法"""
import os, sys, tempfile, json

os.environ.setdefault("TESTING", "1")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import session_manager as sm

# 隔离测试库
_tmp = tempfile.mkdtemp()
sm.DB_PATH = os.path.join(_tmp, "test.db")

PASS, FAIL = 0, 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else: FAIL += 1; print(f"  ❌ {name}")

print("── parse_improvement ──")
p = sm.parse_improvement("You said ~~I like play video~~ → **I like playing video games** — missing gerund and plural form.")
check("提取 target_text", p and p["target_text"] == "I like playing video games")
check("category=grammar", p and p["category"] == "grammar")
p2 = sm.parse_improvement("You said ~~Why why?~~ → **Why?** — repetition.")
check("单词目标句拒收(无跟读价值)", p2 is None)
p3 = sm.parse_improvement("完全不符合格式的文本")
check("无格式文本拒收", p3 is None)
p4 = sm.parse_improvement("You said ~~receive an evil~~ → **defeat the enemy** — better word choice for games.")
check("word choice→vocab", p4 and p4["category"] == "vocab")

print("── manager + 灌队列 ──")
mgr = sm.PersistentSessionManager()
mgr.create("s1", mode="ielts_part1")
scores = {
    "overall": 5.5, "fluency": 5.0, "vocabulary": 5.5, "grammar": 5.0, "pronunciation": 6.0,
    "summary": "test",
    "improvements": [
        "You said ~~I like play video~~ → **I like playing video games** — missing gerund and plural form.",
        "You said ~~receive an evil~~ → **defeat the enemy** — better word choice.",
        "You said ~~Why why?~~ → **Why?** — too short.",  # 应被拒收
        "You said ~~I like play video 2~~ → **I like playing video games** — duplicate target.",  # 应去重
    ],
    "highlights": [],
}
mgr.save_evaluation("s1", scores)
queue = mgr.get_review_queue(limit=10)
check("灌入2条(拒收1+去重1)", len(queue) == 2)
check("目标句正确", any(q["target_text"] == "I like playing video games" for q in queue))
check("状态pending", all(q["status"] == "pending" for q in queue))

print("── 跟读记录 + 巩固 ──")
item = queue[0]
mgr.record_shadow_attempt(item["id"], "i like playing video game", 0.85, wer=0.15, audio_ms=2400)
mgr.record_shadow_attempt(item["id"], "i like playing video games", 1.0, wer=0.0, audio_ms=2200)
row = [r for r in mgr.get_review_list() if r["id"] == item["id"]][0]
check("review_count=2", row["review_count"] == 2)
check("best_score=1.0", row["best_score"] == 1.0)
check("last_reviewed_at 已写", bool(row["last_reviewed_at"]))
mgr.mark_consolidated(item["id"])
row = [r for r in mgr.get_review_list() if r["id"] == item["id"]][0]
check("巩固状态回写", row["status"] == "consolidated")
check("队列排除已巩固", all(q["id"] != item["id"] for q in mgr.get_review_queue()))

print("── 周期统计 ──")
stats = mgr.get_progress_stats(days=30)
check("trend 含今日评估", len(stats["trend"]) == 1 and stats["trend"][0]["overall"] == 5.5)
check("calendar 含今日1次", len(stats["calendar"]) == 1 and stats["calendar"][0]["count"] == 1)
check("week 统计", stats["week"].get("sessions_7d") == 1)
check("review 统计 total=2/pending=1/consolidated=1",
      stats["review"]["total"] == 2 and stats["review"]["pending"] == 1 and stats["review"]["consolidated"] == 1)
check("added_today=2", stats["review"]["added_today"] == 2)

print("── 幂等: 重复评估不重复灌 ──")
mgr.save_evaluation("s1", scores)
check("再评估队列不膨胀", stats["review"]["total"] == 2 and len(mgr.get_review_list()) == 2)

print(f"\n{'✅ 全部通过' if FAIL == 0 else '❌ 有失败'}: {PASS} pass / {FAIL} fail")
sys.exit(1 if FAIL else 0)
