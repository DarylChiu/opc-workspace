#!/usr/bin/env python3
"""管线2 Audio Realtime 模拟测试 - WebSocket 端到端验证"""
import asyncio
import json
import sys
import os
import base64
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ielts_tutor", "backend"))

async def test():
    import websockets
    
    print("🧪 管线2 Audio Realtime 模拟测试")
    print("=" * 50)
    
    # Step 1: Create session via REST API
    import aiohttp
    async with aiohttp.ClientSession() as s:
        print("\n1️⃣ 创建 realtime 会话...")
        async with s.post("http://localhost:8777/api/session/start", 
                         json={"mode": "ielts_part1", "pipeline": "realtime"}) as r:
            data = await r.json()
            sid = data["session_id"]
            print(f"   Session: {sid}, pipeline: {data.get('pipeline')}")
    
    # Step 2: Connect WebSocket
    print(f"\n2️⃣ 连接 WebSocket ws://localhost:8777/ws/chat/{sid}...")
    try:
        ws = await websockets.connect(f"ws://localhost:8777/ws/chat/{sid}")
    except Exception as e:
        print(f"   ❌ WebSocket 连接失败: {e}")
        return
    
    # Step 3: Wait for Qwen connection status
    print("\n3️⃣ 等待 Qwen-Omni 连接...")
    connected = False
    try:
        while True:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=20))
            print(f"   📨 {msg.get('type')}: {json.dumps(msg, ensure_ascii=False)[:120]}")
            if msg.get("type") == "status" and msg.get("state") in ("on", "listening"):
                connected = True
                print("   ✅ Qwen-Omni 已连接，等待语音输入")
                break
            elif msg.get("type") == "error":
                print(f"   ❌ 错误: {msg}")
                await ws.close()
                return
    except asyncio.TimeoutError:
        print("   ❌ 超时: Qwen 连接未在 20s 内完成")
        await ws.close()
        return
    
    if not connected:
        print("   ❌ 未能连接 Qwen")
        await ws.close()
        return
    
    # Step 4: Send a test audio chunk (silence/beep - just to test the pipeline)
    print("\n4️⃣ 发送测试音频...")
    # Generate 1 second of 440Hz sine wave (A4 note) at 16kHz mono 16-bit
    sample_rate = 16000
    duration = 1.0
    frequency = 440
    t = [i / sample_rate for i in range(int(sample_rate * duration))]
    samples = [int(16000 * __import__('math').sin(2 * 3.14159 * frequency * s)) for s in t]
    pcm = struct.pack(f'<{len(samples)}h', *samples)
    b64 = base64.b64encode(pcm).decode()
    
    await ws.send(json.dumps({"type": "audio", "data": b64}))
    print(f"   📤 已发送 {len(pcm)} bytes PCM 音频 (440Hz, 1s)")
    
    # Step 5: Flush and wait for response
    print("\n5️⃣ 提交音频，等待 Qwen 回复...")
    await ws.send(json.dumps({"type": "flush"}))
    
    text_received = False
    audio_received = False
    error_received = False
    try:
        while True:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
            mt = msg.get("type", "")
            if mt == "response_text":
                if not text_received:
                    print(f"   📝 Qwen 文本回复: {msg.get('text', '')[:200]}")
                    text_received = True
            elif mt == "audio":
                if not audio_received:
                    audio_size = len(base64.b64decode(msg.get("data", "")))
                    print(f"   🔊 Qwen 音频回复: {audio_size} bytes")
                    audio_received = True
            elif mt == "final_transcript":
                print(f"   🎤 ASR 识别: {msg.get('text', '')[:200]}")
            elif mt == "status":
                print(f"   ℹ️ 状态: {msg.get('state')} — {msg.get('text', '')}")
                if msg.get("state") == "done" or msg.get("state") == "on":
                    break
            elif mt == "error":
                print(f"   ❌ 错误: {msg.get('msg', str(msg))}")
                error_received = True
                break
    except asyncio.TimeoutError:
        print("   ⚠️ 超时等待 Qwen 回复 (>30s)")
    
    # Summary
    print("\n" + "=" * 50)
    if text_received and audio_received:
        print("✅ 管线2 端到端测试通过！收到文本+音频回复")
    elif text_received:
        print("⚠️ 收到文本但未收到音频")
    elif not error_received:
        print("⚠️ Qwen 连接正常但未收到回复（可能是测试音频无语音内容）")
    else:
        print("❌ 测试失败")
    
    await ws.send(json.dumps({"type": "stop"}))
    await ws.close()

asyncio.run(test())
