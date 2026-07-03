#!/usr/bin/env python3
"""Qwen-Omni 连通性测试 - 验证 API Key 和 WebSocket 连接"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ielts_tutor", "backend"))

async def test():
    from pipeline_qwen_omni import QWEN_WS_URL, QWEN_MODEL
    from config import QWEN_OMNI_KEY
    
    print(f"Key prefix: {QWEN_OMNI_KEY[:15]}...")
    print(f"Key length: {len(QWEN_OMNI_KEY)}")
    print(f"WS URL: {QWEN_WS_URL}")
    print(f"Model: {QWEN_MODEL}")
    
    try:
        import websockets
    except ImportError:
        print("❌ websockets not installed, installing...")
        os.system(f"{sys.executable} -m pip install websockets -q")
        import websockets
    
    import uuid
    ws_url = f"{QWEN_WS_URL}?model={QWEN_MODEL}"
    headers = {"Authorization": f"Bearer {QWEN_OMNI_KEY}"}
    
    print(f"\n🔗 Connecting to Qwen-Omni...")
    try:
        ws = await websockets.connect(ws_url, additional_headers=headers, ping_interval=30, ping_timeout=10)
        print("✅ WebSocket connected!")
        
        # Send session.update
        session_config = {
            "event_id": f"event_{uuid.uuid4().hex[:21]}",
            "type": "session.update",
            "session": {
                "modalities": ["text"],
                "instructions": "You are a test assistant. Reply with 'Connection successful!'",
                "voice": "Cherry",
                "input_audio_format": "pcm",
                "output_audio_format": "pcm",
            },
        }
        await ws.send(json.dumps(session_config))
        print("📤 Sent session.update")
        
        # Wait for session.created
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        print(f"📥 Received: {msg.get('type')}")
        if msg.get("type") == "session.created":
            print(f"✅ Session created! ID: {msg['session']['id']}")
            print(f"   Model: {msg['session'].get('model', 'N/A')}")
            print(f"   Voice: {msg['session'].get('voice', 'N/A')}")
        elif msg.get("type") == "error":
            print(f"❌ Error: {msg}")
            await ws.close()
            return
        
        await ws.close()
        print("✅ Test PASSED - Qwen-Omni API 连通正常")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

asyncio.run(test())
