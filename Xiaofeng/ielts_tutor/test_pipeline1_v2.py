#!/usr/bin/env python3
"""IELTS v0.9.1 Pipeline 1 — 5 mode stress test (streaming TTS edition)"""
import asyncio, aiohttp, json, time, subprocess, os, base64

SERVER = "http://localhost:8767"
MODES = ["ielts_part1", "ielts_part2", "ielts_part3", "business_pitch", "free_talk"]
ROUNDS, WARMUP = 5, 1

RESPONSES = {
    "ielts_part1": [
        "My name is Daryl. I'm from China but I live in Vietnam. I work in textiles.",
        "I enjoy reading and hiking on weekends. I also like trying new restaurants.",
        "I studied international business. My favorite subject was cross-cultural communication.",
        "I live in Ho Chi Minh City. It's busy but convenient for work.",
        "I wake up at seven and start work at eight thirty. I commute by motorbike.",
        "Yes I love traveling. I've been to Thailand and Singapore.",
    ],
    "ielts_part2": [
        "The book was Atomic Habits by James Clear. It's about small changes leading to big results.",
        "I finished it last month reading twenty pages nightly. My friend recommended it.",
        "The main idea is tiny daily improvements. One percent better each day compounds.",
        "It changed my work approach. I focus on small routines instead of huge goals.",
        "I recommend it to anyone wanting to improve. It's practical and easy.",
    ],
    "ielts_part3": [
        "People definitely read less now. Social media consumes our free time.",
        "Reading develops critical thinking. Regular readers communicate more clearly.",
        "Schools need thirty minutes of silent reading daily. It helps a lot.",
        "Digital platforms make books accessible. Audiobooks are growing popular.",
        "In my country people read business books. Fiction is less popular now.",
    ],
    "business_pitch": [
        "Our company Future Textile makes sustainable fabrics. Revenue grew forty percent.",
        "We serve international fashion brands. Twelve clients across Europe and America.",
        "Our waterless dyeing technology reduces water use by ninety percent.",
        "The sustainable textile market reaches two hundred billion by twenty thirty.",
        "We seek five million series A to scale production and enter Europe.",
    ],
    "free_talk": [
        "I visited Tokyo and Kyoto recently. The food was incredible.",
        "I'm into photography. I bought a camera last year for street photography.",
        "Work life balance matters. I don't check emails after eight PM.",
        "I'm thinking about learning Spanish. It would be useful for travel.",
        "My favorite cuisine is Japanese. I cook pasta at home.",
    ],
}

def gen_audio(text, path):
    aiff = path + ".aiff"
    r = subprocess.run(["say", "-o", aiff, text], capture_output=True, timeout=15)
    if r.returncode or not os.path.exists(aiff) or os.path.getsize(aiff) < 100:
        return b""
    subprocess.run(["ffmpeg", "-y", "-i", aiff, "-f", "s16le", "-acodec", "pcm_s16le",
                    "-ar", "16000", "-ac", "1", path], capture_output=True, timeout=10)
    try: os.unlink(aiff)
    except: pass
    return open(path, "rb").read() if os.path.exists(path) else b""

async def test_mode(mode, client, results):
    print(f"\n{'='*50}\n  TEST: {mode}\n{'='*50}")
    async with client.post(f"{SERVER}/api/session/start",
                           json={"mode": mode, "pipeline": "cascade"}) as r:
        sid = (await r.json())["session_id"]
    print(f"  Session: {sid}")

    audios = []
    for i, text in enumerate(RESPONSES[mode]):
        path = f"/tmp/itest_{mode}_{i}.pcm"
        if not os.path.exists(path):
            if not gen_audio(text, path):
                print(f"  FAIL audio gen {i}"); return
        audios.append(path)

    ws = await client.ws_connect(f"ws://localhost:8767/ws/chat/{sid}")
    stats = []

    for rnd in range(ROUNDS + WARMUP):
        with open(audios[min(rnd, len(audios)-1)], "rb") as f:
            raw = f.read()
        t0 = time.time()
        await ws.send_json({"type": "audio", "data": base64.b64encode(raw).decode()})
        await ws.send_json({"type": "flush"})
        stt_t = llm_t = first_audio_t = None
        transcript = ""; chunks = 0

        try:
            while True:
                msg = await asyncio.wait_for(ws.receive(), timeout=60)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    d = json.loads(msg.data); t = d.get("type","")
                    if t == "final_transcript": transcript = d.get("text",""); stt_t = time.time()
                    elif t == "response_text": llm_t = time.time()
                    elif t == "audio":
                        chunks += 1
                        if not first_audio_t:
                            first_audio_t = time.time()
                    elif t == "score": break
                    elif t == "status" and d.get("state") == "done": break
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR): break
        except asyncio.TimeoutError:
            print(f"  R{rnd}: TIMEOUT")

        total = (time.time()-t0)*1000
        stt = (stt_t-t0)*1000 if stt_t else 0
        llm = (llm_t-stt_t)*1000 if llm_t and stt_t else 0
        fa = (first_audio_t-t0)*1000 if first_audio_t else 0
        stat = {"r": rnd, "w": rnd < WARMUP, "stt": round(stt), "llm": round(llm),
                "tot": round(total), "fa": round(fa), "ch": chunks, "txt": transcript[:40]}
        stats.append(stat)
        if not stat["w"]:
            icon = "G" if total<5000 else "Y" if total<8000 else "R"
            print(f"  [{icon}] R{rnd} STT:{stt:.0f} LLM:{llm:.0f} 1stAudio:{fa:.0f} TOT:{total:.0f}ms | {transcript[:35]}")

    await ws.close()
    real = [r for r in stats if not r["w"]]
    if real:
        a = {k: round(sum(r[k] for r in real)/len(real)) for k in ["stt","llm","fa","tot"]}
        print(f"  AVG: STT:{a['stt']} LLM:{a['llm']} 1stAudio:{a['fa']} TOTAL:{a['tot']}ms")
    else:
        a = {"stt":0,"llm":0,"fa":0,"tot":0}
    results.append({"mode": mode, "rounds": stats, "avg": a})

async def main():
    print(f"IELTS v0.9.1 Pipeline 1 Test | {len(MODES)} modes x {ROUNDS} rounds\n")
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(f"{SERVER}/api/health") as r:
                h = await r.json()
            print(f"Server v{h['version']} OK\n")
        except: print("Server DOWN"); return

    results = []
    t0 = time.time()
    async with aiohttp.ClientSession() as s:
        for m in MODES:
            try: await test_mode(m, s, results)
            except Exception as e: print(f"  {m} ERROR: {e}")

    tt = time.time()-t0
    print(f"\n{'='*60}\n📊 FINAL REPORT — IELTS v0.9.1 链式流式 TTS Streaming\n{'='*60}")
    print(f"| {'Mode':<20} | {'Rds':>3} | {'STT':>6} | {'LLM':>6} | {'1st🎵':>7} | {'TOTAL':>7} |")
    print(f"|{'-'*22}|{'-'*5}|{'-'*8}|{'-'*8}|{'-'*9}|{'-'*9}|")
    all_t = []; all_fa = []
    for r in results:
        a = r["avg"]; n = sum(1 for x in r["rounds"] if not x["w"])
        all_t.append(a["tot"]); all_fa.append(a["fa"])
        print(f"| {r['mode']:<20} | {n:3d} | {a['stt']:5d}ms | {a['llm']:5d}ms | {a['fa']:5d}ms | {a['tot']:5d}ms |")

    ga = sum(all_t)/len(all_t); gfa = sum(all_fa)/len(all_fa) if all_fa else 0
    g = "A+" if ga<4000 else "A" if ga<5000 else "B" if ga<7000 else "C"
    print(f"\n🎯 Grand Avg: TOTAL={ga:.0f}ms | FirstAudio={gfa:.0f}ms | Grade: {g} | ⏱️ {tt:.0f}s")

    os.makedirs("test_reports", exist_ok=True)
    with open("test_reports/pipeline1_20260707_v2.json", "w") as f:
        json.dump({"v":"0.9.1","results":results,"grand_avg_ms":round(ga),
                    "first_audio_ms":round(gfa),"time_s":round(tt)}, f, indent=2)

asyncio.run(main())
