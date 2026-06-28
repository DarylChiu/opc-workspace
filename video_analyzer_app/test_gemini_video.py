#!/usr/bin/env python3
"""
测试 OpenRouter Gemini 3.5 Flash 原生视频理解 — 仅分析脚本故事
庞大辉醉酒视频
"""
import os, sys, json, base64, time

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
VIDEO_PATH = "/tmp/pangdahui_hq.mp4"

if not API_KEY:
    print("❌ OPENROUTER_API_KEY not set")
    sys.exit(1)

# Read and encode video
print(f"📹 Reading video: {VIDEO_PATH}")
file_size = os.path.getsize(VIDEO_PATH)
print(f"   Size: {file_size / 1024 / 1024:.1f} MB")

with open(VIDEO_PATH, "rb") as f:
    video_bytes = f.read()

video_b64 = base64.b64encode(video_bytes).decode("utf-8")
print(f"   Base64: {len(video_b64) / 1024 / 1024:.1f} MB")

# Build request
import urllib.request

SYSTEM_PROMPT = """你是一个专业的短视频脚本分析师。请完整分析这个视频的故事内容。

按以下结构输出：

## 一、逐场景分解
按时间顺序，每个场景标注：
- 时间范围（精确到秒）
- 地点和环境
- 出现的每个人物（描述外貌特征，包括穿着、体型、面部细节）
- 每个人物做了什么动作（手上拿了什么、做了什么）
- 每句对白（逐字记录，标说话者）
- 道具的完整清单和使用方式

## 二、故事内核
- 这个故事在讲什么
- 核心冲突是什么
- 笑点/爆点在哪里

## 三、叙事手法
- 导演用了什么技巧
- 观众的预期如何被引导和打破

注意：分析要基于视频实际内容，注意观察人物外貌在视频前后是否有变化，如果有变化请说明变化发生在什么时间点、由什么行为导致。"""

payload = {
    "model": "openai/gpt-4o",
    "messages": [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请完整分析这个视频的脚本故事，逐场景详细描述。"
                },
                {
                    "type": "video_url",
                    "video_url": {
                        "url": f"data:video/mp4;base64,{video_b64}"
                    }
                }
            ]
        }
    ],
    "max_tokens": 8000,
    "temperature": 0.3
}

print("\n🚀 Sending to OpenRouter (google/gemini-3.5-flash)...")
start = time.time()

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://xiaofeng.local",
        "X-Title": "Video Story Analysis"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        elapsed = time.time() - start
        
        print(f"\n✅ Response received in {elapsed:.1f}s")
        
        # Extract usage
        usage = result.get("usage", {})
        print(f"   Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
        print(f"   Completion tokens: {usage.get('completion_tokens', 'N/A')}")
        print(f"   Cost: ${result.get('usage', {}).get('total_tokens', 0) * 0.0000015 / 1000:.6f} (est)")
        
        # Extract content
        content = result["choices"][0]["message"]["content"]
        
        # Save results
        output_path = os.path.join(os.path.dirname(__file__), "reports", "7650848441777540392_gpt4o_story.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# 庞大辉醉酒视频 · Gemini 3.5 Flash 原生视频故事分析\n\n")
            f.write(f"- 模型: google/gemini-3.5-flash\n")
            f.write(f"- 耗时: {elapsed:.1f}s\n")
            f.write(f"- Tokens: {usage}\n\n")
            f.write("---\n\n")
            f.write(content)
        
        print(f"\n📄 Report saved: {output_path}")
        
        # Print first 500 chars
        print(f"\n{'='*60}")
        print("📝 ANALYSIS PREVIEW (first 800 chars):")
        print(f"{'='*60}")
        print(content[:800])
        if len(content) > 800:
            print(f"\n... ({len(content)} total chars)")

except urllib.error.HTTPError as e:
    elapsed = time.time() - start
    error_body = e.read().decode("utf-8")
    print(f"\n❌ HTTP Error {e.code} after {elapsed:.1f}s")
    print(f"   {error_body[:500]}")

except Exception as e:
    elapsed = time.time() - start
    print(f"\n❌ Error after {elapsed:.1f}s: {e}")
