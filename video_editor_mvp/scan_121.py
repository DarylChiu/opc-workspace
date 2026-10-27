#!/usr/bin/env python3
"""Simple video content scanner using Gemini via OpenRouter"""
import os, sys, json, base64, subprocess, tempfile, time

VIDEO = sys.argv[1] if len(sys.argv) > 1 else "/Volumes/TOSHIBA EXT/Video/Raw Materials/Insta 360/VID_20260430_162809_00_121.mp4"

# Get video duration
dur = float(subprocess.check_output(
    ['ffprobe','-v','quiet','-show_entries','format=duration','-of','csv=p=0', VIDEO]).strip())
print(f"Analyzing: {os.path.basename(VIDEO)} ({dur:.0f}s)")

# Sample frames at regular intervals
INTERVAL = 10  # every 10 seconds (fewer frames = cheaper & faster)
frames = []
timestamps = []
for t in range(0, int(dur), INTERVAL):
    tmp = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    tmp.close()
    subprocess.run(['ffmpeg','-y','-ss',str(t),'-i',VIDEO,'-vframes','1','-q:v','3',tmp.name],
                   capture_output=True)
    with open(tmp.name, 'rb') as f:
        frames.append(base64.b64encode(f.read()).decode())
    timestamps.append(t)
    os.unlink(tmp.name)

print(f"Sampled {len(frames)} frames at {INTERVAL}s intervals")

# Build prompt
API_KEY = os.environ.get('OPENROUTER_API_KEY', os.environ.get('GEMINI_API_KEY', ''))
if not API_KEY:
    print("ERROR: No API key found. Set OPENROUTER_API_KEY or GEMINI_API_KEY")
    sys.exit(1)

import urllib.request

parts = []
for i, (ts, b64) in enumerate(zip(timestamps, frames)):
    parts.append({"text": f"Frame at {ts}s:"})
    parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64}})

parts.append({"text": """Analyze each frame and describe what you see. For EACH frame, output:
- Timestamp
- Scene type (e.g., outdoor/indoor, landscape/urban/people)
- Key elements visible (buildings, sea/ocean, birds, people, vegetation, sky, etc.)
- Mood/lighting (bright, sunset, dark, etc.)
Be concise. Format as: "Xs: description"

After describing all frames, ALSO answer:
1. Which time range shows a WHITE BUILDING + SEA + FLYING BIRDS?
2. Which time range has the most visually striking ocean/sea scenery?
3. Which segments would work well as a gentle, scenic video intro?"""})

body = {
    "model": "google/gemini-3.5-flash",
    "messages": [{"role": "user", "content": parts}],
    "max_tokens": 2000
}

print(f"\nSending to Gemini via OpenRouter ({len(frames)} frames)...")
req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
)

t0 = time.time()
resp = urllib.request.urlopen(req, timeout=60)
data = json.loads(resp.read())
elapsed = time.time() - t0
print(f"Response in {elapsed:.1f}s\n")
print("="*60)
print(data['choices'][0]['message']['content'])
print("="*60)

if 'usage' in data:
    u = data['usage']
    print(f"\nTokens: {u.get('prompt_tokens',0)} in / {u.get('completion_tokens',0)} out")
    print(f"Cost: ~${(u.get('prompt_tokens',0)*0.000075 + u.get('completion_tokens',0)*0.00015):.4f}")
