#!/usr/bin/env python3
"""
search_quality_monitor.py — 用预设query测试搜索质量。
v2.0: 主引擎 Brave API，兜底引擎 SearXNG。
纯确定性解析，不使用LLM/API。
"""

import json
import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

# --- Brave API config ---
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

# --- SearXNG config (fallback) ---
SEARXNG_URL = "http://localhost:8888/search"

TEST_QUERIES = [
    ("常规-技术", "Python asyncio gather vs wait difference"),
    ("冷门-法规", "越南 Circular 200 固定资产折旧"),
    ("时效-越南", "2026年7月 越南 个人所得税"),
    ("常规-技术", "Cloudflare Workers Durable Objects SQLite"),
    ("精确-学术", "arxiv multi-agent orchestration"),
]

TIMEOUT_SEC = 15


def check_brave(category: str, query: str) -> tuple[bool, str]:
    """Test a single query against Brave Search API. Returns (passed, reason)."""
    if not BRAVE_API_KEY:
        return False, "BRAVE_API_KEY not set"

    params = urlencode({"q": query, "count": 5})
    url = f"{BRAVE_SEARCH_URL}?{params}"

    try:
        req = Request(url)
        req.add_header("Accept", "application/json")
        req.add_header("Accept-Encoding", "gzip")
        req.add_header("X-Subscription-Token", BRAVE_API_KEY)
        start = time.time()
        with urlopen(req, timeout=TIMEOUT_SEC) as resp:
            elapsed = time.time() - start
            body = resp.read()
            # Handle gzip
            import gzip
            try:
                body = gzip.decompress(body)
            except (gzip.BadGzipFile, OSError):
                pass
            data = json.loads(body)

        # Brave API response: {"web": {"results": [...]}}
        web = data.get("web", {})
        results = web.get("results", []) if isinstance(web, dict) else []

        if not isinstance(results, list):
            return False, "unexpected response format"

        if len(results) < 2:
            return False, f"only {len(results)} results"

        # Basic relevance check: titles exist and aren't empty
        valid_titles = sum(
            1 for r in results
            if r.get("title", "").strip() and len(r.get("title", "").strip()) > 3
        )

        if valid_titles < 2:
            return False, f"only {valid_titles} valid titles in {len(results)} results"

        return True, f"Brave: {len(results)} results, {elapsed:.1f}s"

    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        return False, f"Brave HTTP {e.code}: {body}"
    except URLError as e:
        return False, f"Brave connection error: {e.reason}"
    except json.JSONDecodeError:
        return False, "Brave invalid JSON response"
    except Exception as e:
        return False, f"Brave error: {e}"


def check_searxng(category: str, query: str) -> tuple[bool, str]:
    """Test a single query against SearXNG. Returns (passed, reason)."""
    params = urlencode({"q": query, "format": "json"})
    url = f"{SEARXNG_URL}?{params}"

    try:
        req = Request(url)
        req.add_header("User-Agent", "opc-search-monitor/2.0")
        start = time.time()
        with urlopen(req, timeout=TIMEOUT_SEC) as resp:
            elapsed = time.time() - start
            body = resp.read()
            data = json.loads(body)

        results = data.get("results", [])
        if not isinstance(results, list):
            return False, "unexpected response format"

        if len(results) < 2:
            return False, f"only {len(results)} results"

        valid_titles = sum(
            1 for r in results
            if r.get("title", "").strip() and len(r.get("title", "").strip()) > 3
        )

        if valid_titles < 2:
            return False, f"only {valid_titles} valid titles in {len(results)} results"

        return True, f"SearXNG: {len(results)} results, {elapsed:.1f}s"

    except HTTPError as e:
        return False, f"SearXNG HTTP {e.code}"
    except URLError as e:
        return False, f"SearXNG connection error: {e.reason}"
    except json.JSONDecodeError:
        return False, "SearXNG invalid JSON response"
    except Exception as e:
        return False, f"SearXNG error: {e}"


def main():
    brave_pass = 0
    searxng_pass = 0
    total = len(TEST_QUERIES)
    lines = []

    for category, query in TEST_QUERIES:
        short = query[:30] + "..." if len(query) > 30 else query

        # Test Brave (primary)
        b_ok, b_reason = check_brave(category, query)
        if b_ok:
            brave_pass += 1

        # Test SearXNG (fallback)
        s_ok, s_reason = check_searxng(category, query)
        if s_ok:
            searxng_pass += 1

        # Summary line per query
        brave_flag = "✅" if b_ok else "🔴"
        sx_flag = "✅" if s_ok else "🔴"
        lines.append(f"  {brave_flag}{sx_flag} \"{short}\" ({category})")

    # Overall status
    if brave_pass == total and searxng_pass == total:
        status = "✅"
        summary = f"Brave {brave_pass}/{total} + SearXNG {searxng_pass}/{total} 全部正常"
    elif brave_pass >= 3:
        status = "⚠️"
        summary = f"Brave {brave_pass}/{total} 正常 | SearXNG {searxng_pass}/{total} (兜底引擎异常)"
    elif brave_pass == 0:
        status = "🔴"
        summary = f"Brave {brave_pass}/{total} 严重异常, SearXNG {searxng_pass}/{total}"
    else:
        status = "⚠️"
        summary = f"Brave {brave_pass}/{total} | SearXNG {searxng_pass}/{total}"

    print(f"🔍 搜索质量: {status} {summary}")
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
