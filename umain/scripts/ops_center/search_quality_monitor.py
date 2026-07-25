#!/usr/bin/env python3
"""
search_quality_monitor.py — 用预设query测试SearXNG搜索质量。
纯确定性解析，不使用LLM/API。
"""

import json
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

SEARXNG_URL = "http://localhost:8888/search"

TEST_QUERIES = [
    ("常规-技术", "Python asyncio gather vs wait difference"),
    ("冷门-法规", "越南 Circular 200 固定资产折旧"),
    ("时效-越南", "2026年7月 越南 个人所得税"),
    ("常规-技术", "Cloudflare Workers Durable Objects SQLite"),
    ("精确-学术", "site:arxiv.org multi-agent orchestration"),
]

TIMEOUT_SEC = 10


def check_query(category: str, query: str) -> tuple[bool, str]:
    """Test a single query against SearXNG. Returns (passed, reason)."""
    params = urlencode({"q": query, "format": "json"})
    url = f"{SEARXNG_URL}?{params}"

    try:
        req = Request(url)
        req.add_header("User-Agent", "opc-search-monitor/1.0")
        start = time.time()
        with urlopen(req, timeout=TIMEOUT_SEC) as resp:
            elapsed = time.time() - start
            body = resp.read()
            data = json.loads(body)

        results = data.get("results", [])
        if not isinstance(results, list):
            return False, "unexpected response format"

        if len(results) < 3:
            return False, f"only {len(results)} results"

        # Basic relevance: check that titles exist and aren't empty
        valid_titles = 0
        for r in results:
            title = r.get("title", "").strip()
            if title and len(title) > 3:
                valid_titles += 1

        if valid_titles < 2:
            return False, f"only {valid_titles} valid titles in {len(results)} results"

        return True, f"{len(results)} results, {elapsed:.1f}s"

    except HTTPError as e:
        return False, f"HTTP {e.code}"
    except URLError as e:
        return False, f"connection error: {e.reason}"
    except json.JSONDecodeError:
        return False, "invalid JSON response"
    except Exception as e:
        return False, f"error: {e}"


def main():
    passed = 0
    failed_queries = []

    for category, query in TEST_QUERIES:
        ok, reason = check_query(category, query)
        if ok:
            passed += 1
        else:
            failed_queries.append(f'"{query[:30]}..." ({category}): {reason}')

    total = len(TEST_QUERIES)
    fail_count = total - passed

    if fail_count == 0:
        print(f"🔍 搜索质量: ✅ {passed}/{total} 正常")
    elif fail_count <= 2:
        print(f"🔍 搜索质量: ⚠️ {passed}/{total} — 以下查询异常:")
        for fq in failed_queries:
            print(f"  - {fq}")
    else:
        print(f"🔍 搜索质量: 🔴 {passed}/{total} 严重异常")
        for fq in failed_queries:
            print(f"  - {fq}")


if __name__ == "__main__":
    main()
