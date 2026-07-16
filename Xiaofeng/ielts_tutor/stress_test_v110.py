"""v1.1.0 四模块压力测试 — 每模块5轮
M1 数据层并发写 | M2 Dashboard API | M3 跟读TTS/STT | M4 页面串联
测试数据带 stress- 前缀, 结束后全部清理
"""
import asyncio, aiohttp, base64, json, os, sqlite3, statistics, subprocess, sys, tempfile, time, uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

BASE = "http://localhost:8767"
DB = os.path.join(os.path.dirname(__file__), "data", "ielts_tutor.db")
ROUNDS = 5
REPORT = {"started": datetime.now().isoformat(), "modules": {}}

def pctl(lat, p):
    if not lat: return 0
    s = sorted(lat); i = min(len(s)-1, int(len(s)*p/100))
    return round(s[i]*1000)

# ══ M1 数据层: 每轮20并发线程 全链路写 ══
def m1_worker(i):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
    import session_manager as sm
    mgr = sm.PersistentSessionManager()
    sid = f"stress-{uuid.uuid4().hex[:8]}"
    t0 = time.time()
    mgr.create(sid, mode="ielts_part1")
    mgr.add_transcript(sid, "user", f"stress test utterance {i}")
    mgr.save_evaluation(sid, {
        "overall": 6.0, "fluency": 6.0, "vocabulary": 5.5, "grammar": 6.0, "pronunciation": 6.5,
        "summary": "stress", "improvements": [
            f"You said ~~stress wrong {i}~~ → **stress corrected sentence number {i}** — test."],
        "highlights": []})
    mgr.get_review_queue(limit=8)
    mgr.get_progress_stats(days=7)
    mgr.end_session(sid)
    return time.time() - t0

def run_m1():
    rounds = []
    for r in range(ROUNDS):
        lat, errs = [], 0
        with ThreadPoolExecutor(max_workers=20) as ex:
            futs = [ex.submit(m1_worker, r*20+i) for i in range(20)]
            for f in futs:
                try: lat.append(f.result())
                except Exception as e:
                    errs += 1
                    if errs == 1: print(f"  M1 err: {e}", flush=True)
        rounds.append({"round": r+1, "ops": 20, "errors": errs,
                       "p50_ms": pctl(lat, 50), "p95_ms": pctl(lat, 95)})
        print(f"  M1 R{r+1}: 20并发全链路写 errors={errs} p50={rounds[-1]['p50_ms']}ms p95={rounds[-1]['p95_ms']}ms", flush=True)
    # 完整性校验
    conn = sqlite3.connect(DB)
    n_sess = conn.execute("SELECT COUNT(*) FROM sessions WHERE id LIKE 'stress-%'").fetchone()[0]
    n_eval = conn.execute("SELECT COUNT(*) FROM evaluations WHERE session_id LIKE 'stress-%'").fetchone()[0]
    n_item = conn.execute("SELECT COUNT(*) FROM review_items WHERE source_session_id LIKE 'stress-%'").fetchone()[0]
    integ = conn.execute("PRAGMA integrity_check").fetchone()[0]
    conn.close()
    expected = ROUNDS * 20
    ok = n_sess == expected and n_eval == expected and n_item == expected and integ == "ok"
    print(f"  M1 完整性: sessions={n_sess}/{expected} evals={n_eval} items={n_item} integrity={integ} → {'✅' if ok else '❌'}", flush=True)
    REPORT["modules"]["M1_数据层"] = {"rounds": rounds, "integrity": {"sessions": n_sess, "evals": n_eval, "items": n_item, "expected": expected, "sqlite": integ, "ok": ok}}

# ══ M2 Dashboard API: 每轮50并发×3端点 ══
async def m2_round(sess, rnd):
    urls = ["/api/dashboard/stats?days=30", "/api/dashboard/reviews?limit=100", "/api/dashboard/history?limit=20"]
    lat, errs = [], 0
    async def hit(u):
        nonlocal errs
        t0 = time.time()
        try:
            async with sess.get(BASE+u) as r:
                await r.read()
                if r.status != 200: errs += 1
                else: lat.append(time.time()-t0)
        except Exception: errs += 1
    await asyncio.gather(*[hit(urls[i % 3]) for i in range(50)])
    return {"round": rnd, "reqs": 50, "errors": errs, "p50_ms": pctl(lat,50), "p95_ms": pctl(lat,95)}

# ══ M4 页面串联: 每轮30并发×3页面 ══
async def m4_round(sess, rnd):
    lat, errs = [], 0
    pages = ["/", "/dashboard", "/shadow"]
    async def hit(u):
        nonlocal errs
        t0 = time.time()
        try:
            async with sess.get(BASE+u) as r:
                body = await r.text()
                if r.status != 200 or "<title>" not in body: errs += 1
                else: lat.append(time.time()-t0)
        except Exception: errs += 1
    await asyncio.gather(*[hit(pages[i % 3]) for i in range(30)])
    return {"round": rnd, "reqs": 30, "errors": errs, "p50_ms": pctl(lat,50), "p95_ms": pctl(lat,95)}

# ══ M3 跟读: 每轮 tts×2并发 + attempt×3并发(真实音频) ══
def make_test_audio(item_id):
    import urllib.request
    req = urllib.request.Request(f"{BASE}/api/review/{item_id}/tts", method="POST")
    wav_b64 = json.loads(urllib.request.urlopen(req, timeout=120).read())["audio"]
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(base64.b64decode(wav_b64)); wav = f.name
    raw = subprocess.run(["ffmpeg","-y","-i",wav,"-f","s16le","-acodec","pcm_s16le","-ar","16000","-ac","1","-"],
                         capture_output=True).stdout
    os.unlink(wav)
    return base64.b64encode(raw).decode()

async def m3_round(sess, rnd, item_id, audio_b64):
    lat_tts, lat_att, errs, wrong_score = [], [], 0, 0
    async def tts():
        nonlocal errs
        t0 = time.time()
        try:
            async with sess.post(f"{BASE}/api/review/{item_id}/tts") as r:
                d = await r.json()
                if r.status != 200 or not d.get("audio"): errs += 1
                else: lat_tts.append(time.time()-t0)
        except Exception: errs += 1
    async def attempt():
        nonlocal errs, wrong_score
        t0 = time.time()
        try:
            async with sess.post(f"{BASE}/api/review/{item_id}/attempt",
                                 json={"audio": audio_b64}) as r:
                d = await r.json()
                if r.status != 200 or "wer" not in d: errs += 1
                else:
                    lat_att.append(time.time()-t0)
                    if d["wer"] > 0.3: wrong_score += 1  # 范音回灌应低WER
        except Exception: errs += 1
    await asyncio.gather(tts(), tts(), attempt(), attempt(), attempt())
    return {"round": rnd, "tts_reqs": 2, "attempt_reqs": 3, "errors": errs, "wer_gt30pct": wrong_score,
            "tts_p95_ms": pctl(lat_tts,95), "attempt_p50_ms": pctl(lat_att,50), "attempt_p95_ms": pctl(lat_att,95)}

async def run_async_modules():
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=180)) as sess:
        # M2
        rounds = []
        for r in range(ROUNDS):
            res = await m2_round(sess, r+1)
            rounds.append(res)
            print(f"  M2 R{r+1}: 50并发API errors={res['errors']} p50={res['p50_ms']}ms p95={res['p95_ms']}ms", flush=True)
        REPORT["modules"]["M2_Dashboard_API"] = {"rounds": rounds}
        # M3 准备专用测试项
        conn = sqlite3.connect(DB)
        cur = conn.execute("INSERT INTO review_items(source_session_id,target_text,context,category,created_at) VALUES(?,?,?,?,?)",
            ("stress-m3", "The quick brown fox jumps over the lazy dog", "压测专用", "grammar", datetime.now().isoformat()))
        item_id = cur.lastrowid; conn.commit(); conn.close()
        audio_b64 = await asyncio.get_event_loop().run_in_executor(None, make_test_audio, item_id)
        print(f"  M3 测试音频就绪 ({len(audio_b64)//1024}KB)", flush=True)
        rounds = []
        for r in range(ROUNDS):
            # 每轮重置状态防止 consolidated 影响
            conn = sqlite3.connect(DB); conn.execute("UPDATE review_items SET status='pending' WHERE id=?", (item_id,)); conn.commit(); conn.close()
            res = await m3_round(sess, r+1, item_id, audio_b64)
            rounds.append(res)
            print(f"  M3 R{r+1}: tts×2+attempt×3并发 errors={res['errors']} 异常WER={res['wer_gt30pct']} attempt_p95={res['attempt_p95_ms']}ms", flush=True)
        REPORT["modules"]["M3_跟读闭环"] = {"rounds": rounds, "test_item": item_id}
        # M4
        rounds = []
        for r in range(ROUNDS):
            res = await m4_round(sess, r+1)
            rounds.append(res)
            print(f"  M4 R{r+1}: 30并发页面 errors={res['errors']} p95={res['p95_ms']}ms", flush=True)
        REPORT["modules"]["M4_页面串联"] = {"rounds": rounds}

def cleanup():
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM shadow_attempts WHERE review_item_id IN (SELECT id FROM review_items WHERE source_session_id LIKE 'stress-%')")
    conn.execute("DELETE FROM review_items WHERE source_session_id LIKE 'stress-%'")
    conn.execute("DELETE FROM errors WHERE session_id LIKE 'stress-%'")
    conn.execute("DELETE FROM evaluations WHERE session_id LIKE 'stress-%'")
    conn.execute("DELETE FROM transcripts WHERE session_id LIKE 'stress-%'")
    conn.execute("DELETE FROM sessions WHERE id LIKE 'stress-%'")
    conn.commit()
    left = conn.execute("SELECT (SELECT COUNT(*) FROM sessions WHERE id LIKE 'stress-%') + (SELECT COUNT(*) FROM review_items WHERE source_session_id LIKE 'stress-%')").fetchone()[0]
    conn.close()
    print(f"清理完成, 残留: {left}", flush=True)

if __name__ == "__main__":
    print("═══ M1 数据层 (5轮×20并发全链路写) ═══", flush=True)
    run_m1()
    print("═══ M2/M3/M4 (HTTP) ═══", flush=True)
    asyncio.run(run_async_modules())
    cleanup()
    REPORT["finished"] = datetime.now().isoformat()
    os.makedirs("test_reports", exist_ok=True)
    out = f"test_reports/stress_v110_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    json.dump(REPORT, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"报告: {out}", flush=True)
    # 汇总判定
    fails = []
    for name, m in REPORT["modules"].items():
        errs = sum(r.get("errors", 0) for r in m["rounds"])
        if errs: fails.append(f"{name}: {errs} errors")
        if name == "M1_数据层" and not m["integrity"]["ok"]: fails.append("M1 完整性失败")
    print("❌ " + "; ".join(fails) if fails else "✅ 四模块×5轮 全部通过", flush=True)
