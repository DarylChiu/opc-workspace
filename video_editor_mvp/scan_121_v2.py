#!/usr/bin/env python3
"""Analyze 121.mp4 with Gemini Flash via OpenRouter"""
import os, json, base64, subprocess, tempfile, time, urllib.request

VIDEO = "/Volumes/TOSHIBA EXT/Video/Raw Materials/Insta 360/VID_20260430_162809_00_121.mp4"
API_KEY = os.environ['OPENROUTER_API_KEY']

dur = float(subprocess.check_output(['ffprobe','-v','quiet','-show_entries','format=duration','-of','csv=p=0', VIDEO]).strip())
print(f"121.mp4: {dur:.0f}s")

def extract_frame(t):
    tmp = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    tmp.close()
    subprocess.run(['ffmpeg','-y','-ss',str(t),'-i',VIDEO,'-vframes','1','-q:v','5',tmp.name],
                   capture_output=True)
    with open(tmp.name, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    os.unlink(tmp.name)
    return b64

def ask_gemini(prompt, frames_b64, timestamps):
    content = []
    for i, (ts, b64) in enumerate(zip(timestamps, frames_b64)):
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}})
    content.append({"type": "text", "text": prompt})
    
    body = {
        "model": "google/gemini-3.5-flash",
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 1500
    }
    
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=60)
    return json.loads(resp.read())

# Batch 1: Frames 0, 10, 20, 30
print("\n--- Batch 1: 0s, 10s, 20s, 30s ---")
t0 = time.time()
ts1 = [0, 10, 20, 30]
frames1 = [extract_frame(t) for t in ts1]
data1 = ask_gemini(f"These are frames from a travel vlog video at {ts1} seconds. For EACH timestamp describe: scene type, key elements (buildings/sea/people/birds/vegetation), lighting. Format: 'Xs: description'", frames1, ts1)
print(f"  ({time.time()-t0:.1f}s)")
print(data1['choices'][0]['message']['content'])

# Batch 2: Frames 40, 50, 60, 70
print("\n--- Batch 2: 40s, 50s, 60s, 70s ---")
t0 = time.time()
ts2 = [40, 50, 60, 70]
frames2 = [extract_frame(t) for t in ts2]
data2 = ask_gemini(f"These are frames from a travel vlog video at {ts2} seconds. For EACH timestamp describe: scene type, key elements, lighting. Format: 'Xs: description'", frames2, ts2)
print(f"  ({time.time()-t0:.1f}s)")
print(data2['choices'][0]['message']['content'])

# Summary question
print("\n--- Key Questions ---")
t0 = time.time()
# Use two representative frames for the summary
key_frames = [extract_frame(50), extract_frame(70)]
data3 = ask_gemini("""
Based on all frames analyzed across this 78-second travel video, answer:
1. At which time range can we see a WHITE BUILDING + SEA + FLYING BIRDS?
2. Which 5-8 second segment has the most beautiful scenic ocean/sea view?
3. Which 5-8 second segment would work best as a gentle video intro (soft, scenic, not too dark)?

Answer concisely with timestamps.
""", key_frames, [50, 70])
print(f"  ({time.time()-t0:.1f}s)")
print(data3['choices'][0]['message']['content'])

u = data1.get('usage', {})
print(f"\nTotal cost est: ~${(u.get('prompt_tokens',0)*3*0.000075 + u.get('completion_tokens',0)*3*0.00015):.4f}")
