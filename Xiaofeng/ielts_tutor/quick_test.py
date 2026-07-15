#!/usr/bin/env python3
"""Quick 5-round stress test with short audio"""
import asyncio, json, base64, time
import aiohttp, websockets

SERVER_HTTP = 'http://localhost:8767'
SERVER_WS = 'ws://localhost:8767'

async def main():
    with open('/tmp/test_3s.pcm', 'rb') as f:
        pcm = f.read()
    
    chunks = [pcm[i:i+4096] for i in range(0, len(pcm), 4096)]
    print(f'Test: {len(pcm)} bytes ({len(pcm)/32000:.1f}s), {len(chunks)} chunks')
    
    stt_times = []
    ttfa_times = []
    partial_counts = []
    
    for r in range(1, 6):
        async with aiohttp.ClientSession() as http:
            async with http.post(f'{SERVER_HTTP}/api/session/start',
                                json={'mode':'ielts_part1','pipeline':'cascade'}) as resp:
                data = await resp.json()
                sid = data['session_id']
        
        async with websockets.connect(f'{SERVER_WS}/ws/chat/{sid}') as ws:
            # Absorb greeting
            while True:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if msg.get('type') == 'status' and msg.get('state') == 'done':
                    break
            
            partials = 0
            # Send audio
            for c in chunks:
                await ws.send(json.dumps({'type':'audio','data':base64.b64encode(c).decode()}))
                await asyncio.sleep(0.01)
                # Quick check for partials
                try:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.01))
                    if msg.get('type') == 'partial_transcript':
                        partials += 1
                except:
                    pass
            
            t_flush = time.time()
            await ws.send(json.dumps({'type':'flush'}))
            
            stt_time = None
            ttfa_time = None
            text = ''
            
            while True:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
                now = time.time()
                if msg.get('type') == 'final_transcript':
                    stt_time = (now - t_flush) * 1000
                    text = msg.get('text', '')
                elif msg.get('type') == 'audio' and ttfa_time is None:
                    ttfa_time = (now - t_flush) * 1000
                elif msg.get('type') == 'status' and msg.get('state') == 'done':
                    break
            
            stt_times.append(stt_time)
            ttfa_times.append(ttfa_time)
            partial_counts.append(partials)
            print(f'Round {r}: STT={stt_time:.0f}ms TTFA={ttfa_time:.0f}ms partials={partials}x text={text[:50]}')
        
        await asyncio.sleep(0.3)
    
    print(f'\n{"="*40}')
    print(f'RESULTS (3s audio, 5 rounds)')
    print(f'STT  avg: {sum(stt_times)/len(stt_times):.0f}ms ({min(stt_times):.0f}-{max(stt_times):.0f})')
    print(f'TTFA avg: {sum(ttfa_times)/len(ttfa_times):.0f}ms ({min(ttfa_times):.0f}-{max(ttfa_times):.0f})')
    print(f'Partials: {sum(partial_counts)/len(partial_counts):.1f}/round avg')
    
    stt_avg = sum(stt_times)/len(stt_times)
    if stt_avg < 1500:
        print(f'✅ STT STREAMING PASS ({stt_avg:.0f}ms < 1.5s)')
    else:
        print(f'⚠️  STT above target ({stt_avg:.0f}ms)')

asyncio.run(main())
