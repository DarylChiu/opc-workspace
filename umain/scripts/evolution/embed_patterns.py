#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
embed_patterns.py — M1 向量语义层工具
- 写入时: 为新模式计算 embedding 存入 failure_patterns.json
- 批量回填: --backfill 为历史模式补算 embedding
- 查询时: retrieve 用本地 numpy 余弦（零API调用）

用法:
  python3 embed_patterns.py --backfill          # 为缺失embedding的模式批量补算
  python3 embed_patterns.py --embed "<text>"    # 单条文本算embedding(调试)
"""
import json
import os
import sys
import urllib.request

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.environ.get("WORKSPACE") or os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
LIBRARY = os.path.join(WORKSPACE, "memory/evolution/failure_patterns.json")

# 复用 OpenClaw memorySearch 的 OpenAI-compatible 通道 (openrouter)
EMBED_BASE = os.environ.get("EMBED_BASE", "https://openrouter.ai/api/v1")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
EMBED_KEY = os.environ.get("OPENROUTER_API_KEY", "")


def get_embedding(text):
    if not EMBED_KEY:
        return None
    payload = {
        "model": EMBED_MODEL,
        "input": text[:8000],
    }
    req = urllib.request.Request(
        f"{EMBED_BASE}/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {EMBED_KEY}",
            "HTTP-Referer": "https://openclaw.ai",
            "X-Title": "OpenClaw Memory",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["data"][0]["embedding"]
    except Exception as e:
        print(f"⚠️ embedding调用失败: {e}", file=sys.stderr)
        return None


def load_library():
    if not os.path.exists(LIBRARY):
        return {"version": "1.0", "patterns": [], "stats": {}}
    with open(LIBRARY, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    lib = load_library()
    patterns = lib.get("patterns", [])

    if "--backfill" in sys.argv:
        missing = [p for p in patterns if "embedding" not in p]
        if not missing:
            print("✅ 所有模式已有 embedding")
            return 0
        print(f"📥 待回填 embedding: {len(missing)} 条")
        for p in missing:
            emb = get_embedding(p.get("text", ""))
            if emb:
                p["embedding"] = emb
                print(f"  + {p.get('id')} ✓")
            else:
                print(f"  - {p.get('id')} ✗ (跳过，留空)")
        with open(LIBRARY, "w", encoding="utf-8") as f:
            json.dump(lib, f, ensure_ascii=False, indent=2)
        print("✅ 回填完成")
        return 0

    if "--embed" in sys.argv:
        idx = sys.argv.index("--embed")
        text = sys.argv[idx + 1]
        emb = get_embedding(text)
        if emb:
            print(f"✅ 维度: {len(emb)}")
            print(f"前5维: {emb[:5]}")
        else:
            print("❌ 失败（检查 OPENROUTER_API_KEY）")
        return 0

    print("用法: --backfill 批量回填 | --embed <text> 单条调试")
    return 2


if __name__ == "__main__":
    sys.exit(main())
