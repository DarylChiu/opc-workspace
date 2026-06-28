#!/usr/bin/env python3
"""GPT-4o: 帧序列 + 对白逐场景分析"""
import os, sys, json, base64, time, glob, subprocess, urllib.request

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
VIDEO = os.path.join(os.path.dirname(__file__), "videos", "7650848441777540392.mp4")
FRAMES_DIR = "/tmp/pangdahui_frames"

# --- 1. Transcribe ---
print("🎙️ Transcribing...")
audio = "/tmp/pangdahui_audio.wav"
subprocess.run(["ffmpeg","-y","-i",VIDEO,"-vn","-acodec","pcm_s16le","-ar","16000","-ac","1",audio],
               capture_output=True, timeout=15)
subprocess.run(["whisper",audio,"--model","tiny","--language","zh","--output_format","txt","--output_dir","/tmp"],
               capture_output=True, timeout=60)
transcript = open("/tmp/pangdahui_audio.txt").read().strip()
print(f"   {transcript[:150]}...")

# --- 2. Select frames ---
frames = sorted(glob.glob(os.path.join(FRAMES_DIR, "frame_*.jpg")))
selected = frames[::2]  # ~23 frames, every 2s
print(f"📸 {len(selected)} frames")

# --- 3. Build content ---
user_text = (
    "请分析以下视频的完整脚本故事。视频对白如下：\n\n"
    + transcript + "\n\n"
    "请结合画面和对白，逐场景详细分析。\n"
    "特别注意：观察人物外貌在视频前后是否有变化，如果有，是哪个行为导致的。"
)

content = [{"type": "text", "text": user_text}]
for f in selected:
    with open(f, "rb") as img:
        b64 = base64.b64encode(img.read()).decode()
    content.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}
    })

# --- 4. Call API ---
payload = {
    "model": "openai/gpt-4o",
    "messages": [
        {"role": "system", "content": "你是一个专业的短视频脚本分析师。逐场景分析，注意面部变化和因果关系。"},
        {"role": "user", "content": content}
    ],
    "max_tokens": 6000, "temperature": 0.3
}

print(f"\n🚀 GPT-4o ({len(selected)} frames)...")
start = time.time()

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json",
             "HTTP-Referer": "https://xiaofeng.local", "X-Title": "gpt4o-video"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        r = json.loads(resp.read().decode())
        elapsed = time.time() - start
        u = r.get("usage", {})
        print(f"✅ {elapsed:.1f}s | prompt: {u.get('prompt_tokens')} | completion: {u.get('completion_tokens')}")

        text = r["choices"][0]["message"]["content"]
        out = os.path.join(os.path.dirname(__file__), "reports", "7650848441777540392_gpt4o_story.md")
        with open(out, "w") as f:
            f.write(f"# GPT-4o 帧序列分析\n\n- {len(selected)} frames\n- {elapsed:.1f}s\n- {u}\n\n---\n\n{text}")
        print(f"📄 {out}")
        print(f"\n{'='*60}\n{text[:1500]}\n... ({len(text)} chars)")

except urllib.error.HTTPError as e:
    print(f"❌ HTTP {e.code}: {e.read().decode()[:500]}")
except Exception as e:
    print(f"❌ {e}")
