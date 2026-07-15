#!/usr/bin/env python3
"""5-round stress test for streaming STT + cascade pipeline"""
import asyncio, json, base64, time, os
import aiohttp
import websockets
import subprocess

SERVER_HTTP = "http://localhost:8767"
SERVER_WS = "ws://localhost:8767"
TEST_MP3 = os.path.expanduser("~/.openclaw/xiaofeng_workspace/test_audio/ielts_benchmark/advanced/sample_044.mp3")

def mp3_to_pcm16(mp3_path, target_sr=16000):
    result = subprocess.run(
        ['ffmpeg', '-y', '-i', mp3_path, '-f', 's16le', '-ar', str(target_sr),
         '-ac', '1', '-'],
        capture_output=True, timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()}")
    return result.stdout

async def stress_test():
    print("=" * 60)
    print("IELTS Tutor v0.9.1 — 5-Round Stress Test")
    print(f"Server: {SERVER_WS}, Audio: {TEST_MP3}")
    print("=" * 60)

    pcm = mp3_to_pcm16(TEST_MP3)
    chunk_size = 4096
    chunks = [pcm[i:i+chunk_size] for i in range(0, len(pcm), chunk_size)]
    audio_duration = len(pcm) / 32000
    print(f"Audio: {len(pcm)} bytes ({audio_duration:.1f}s), {len(chunks)} chunks")

    metrics = []

    for round_num in range(1, 6):
        print(f"\n{'─' * 40}")
        print(f"Round {round_num}/5")

        # Create session via REST API
        async with aiohttp.ClientSession() as http:
            async with http.post(f"{SERVER_HTTP}/api/session/start",
                                json={"mode": "ielts_part1", "pipeline": "cascade"}) as resp:
                data = await resp.json()
                sid = data.get("session_id", f"stress-{round_num}")
        print(f"  Session: {sid}")

        async with websockets.connect(f"{SERVER_WS}/ws/chat/{sid}") as ws:
            # Absorb greeting
            partial_count = 0
            partial_first = None
            t_start = time.time()
            greeting_done = False
            while not greeting_done:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if msg.get('type') == 'status' and msg.get('state') == 'done':
                    greeting_done = True
                elif msg.get('type') == 'response_text':
                    print(f"  Greeting: {msg.get('text','')[:60]}...")

            # Send audio chunks
            t_audio_start = time.time()
            for chunk in chunks:
                await ws.send(json.dumps({
                    "type": "audio",
                    "data": base64.b64encode(chunk).decode()
                }))
                await asyncio.sleep(0.015)  # ~15ms intervals simulates real-time

            # Send flush
            t_flush = time.time()
            await ws.send(json.dumps({"type": "flush"}))
            print(f"  Audio sent in {t_flush - t_audio_start:.1f}s, waiting for response...")

            # Wait for processing
            stt_ms = None
            ttfa_ms = None
            total_ms = None
            text = ""

            try:
                while True:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=45))
                    mtype = msg.get('type', '')
                    now = time.time()

                    if mtype == 'partial_transcript':
                        if partial_first is None:
                            partial_first = now - t_flush
                        partial_count += 1

                    elif mtype == 'final_transcript':
                        stt_ms = (now - t_flush) * 1000
                        text = msg.get('text', '')

                    elif mtype == 'response_text':
                        text = msg.get('text', '')

                    elif mtype == 'audio':
                        if ttfa_ms is None:
                            ttfa_ms = (now - t_flush) * 1000

                    elif mtype == 'status' and msg.get('state') == 'done':
                        total_ms = (now - t_flush) * 1000
                        break

            except asyncio.TimeoutError:
                print("  ⚠️ Timeout")

            m = {
                'round': round_num,
                'stt_ms': stt_ms,
                'ttfa_ms': ttfa_ms,
                'total_ms': total_ms,
                'partials': partial_count,
                'partial_first_ms': (partial_first * 1000) if partial_first else None,
                'text': text[:60],
            }
            metrics.append(m)

            print(f"  📊 STT={m['stt_ms']:.0f}ms" if m['stt_ms'] else "  📊 STT=N/A", end="")
            print(f" TTFA={m['ttfa_ms']:.0f}ms" if m['ttfa_ms'] else " TTFA=N/A", end="")
            print(f" Total={m['total_ms']:.0f}ms" if m['total_ms'] else " Total=N/A", end="")
            print(f" Partial={m['partials']}x" if m['partials'] else "")
            if text:
                print(f"  Text: {text}")

            await asyncio.sleep(0.3)

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 5-ROUND STRESS TEST RESULTS")
    print(f"{'=' * 60}")

    valid = [m for m in metrics if m['stt_ms'] and m['ttfa_ms']]
    if valid:
        stt_vals = [m['stt_ms'] for m in valid]
        ttfa_vals = [m['ttfa_ms'] for m in valid]
        total_vals = [m['total_ms'] for m in valid]
        partial_vals = [m['partials'] for m in metrics]

        print(f"STT latency:        {sum(stt_vals)/len(stt_vals):.0f}ms avg ({min(stt_vals):.0f}-{max(stt_vals):.0f}ms)")
        print(f"TTFA (first audio): {sum(ttfa_vals)/len(ttfa_vals):.0f}ms avg")
        print(f"Total cycle:        {sum(total_vals)/len(total_vals):.0f}ms avg")
        print(f"Partial transcripts: {sum(partial_vals)/len(partial_vals):.1f}/round avg")
        print(f"Rounds completed:   {len(valid)}/5")

        stt_avg = sum(stt_vals)/len(stt_vals)
        ttfa_avg = sum(ttfa_vals)/len(ttfa_vals)

        print()
        if stt_avg < 1500:
            print(f"✅ STT {stt_avg:.0f}ms < 1.5s — PASS")
        elif stt_avg < 2000:
            print(f"⚠️  STT {stt_avg:.0f}ms — MARGINAL")
        else:
            print(f"❌ STT {stt_avg:.0f}ms > 1.5s — FAIL")

        if ttfa_avg < 3000:
            print(f"✅ TTFA {ttfa_avg:.0f}ms < 3s — PASS")
        elif ttfa_avg < 5000:
            print(f"⚠️  TTFA {ttfa_avg:.0f}ms — MARGINAL")
        else:
            print(f"❌ TTFA {ttfa_avg:.0f}ms > 5s — FAIL")
    else:
        print("❌ No valid rounds!")

if __name__ == "__main__":
    asyncio.run(stress_test())
