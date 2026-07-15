#!/usr/bin/env python3
"""
SAGE Checker — Self(恨点小己) L3自进化基建 M1
在交付前审查产出的三个维度: 来源可追溯 / 结构化 / 逻辑严谨
用法:
  python3 checker.py --file draft.md [--task "原始任务描述"]
  echo "草稿内容" | python3 checker.py [--task "..."]
退出码: 0=PASS 1=FAIL 2=错误
每次审查追加日志到 memory/evolution/checker-log.jsonl
依赖: 仅python3标准库 + 环境变量 DEEPSEEK_API_KEY
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
WORKSPACE = os.path.expanduser("~/.openclaw/workspace-self")
LOG_DIR = os.path.join(WORKSPACE, "memory", "evolution")
LOG_FILE = os.path.join(LOG_DIR, "checker-log.jsonl")
VN_TZ = timezone(timedelta(hours=7))

CHECKER_SYSTEM_PROMPT = """你是SAGE框架中的Checker角色，负责在知识管理Agent「Self」交付产出前做强制审查。
你的审查极其严格，专治她的两个已知短板：推理严谨性不足、结构化不足。

对稿件按三个维度打分（0-10）：

1. traceability 来源可追溯
   - 每个事实性结论是否标注来源（文档名/URL/数据来源+时间）？
   - 无法溯源的内容是否明确标注「推测」「待验证」「无来源」？
   - 引用是否可定位（能找到原文，而非泛泛"据研究"）？

2. structure 结构化
   - 是否有清晰层次：结论 → 证据 → 来源 → 置信度？
   - 范围是否明确界定（时间范围/领域/对象）？
   - 是否区分了事实、推断、个人意见三类内容？

3. rigor 逻辑严谨
   - 是否存在跳跃推理（结论跳过必要中间步骤）？
   - 因果论断是否有依据（相关≠因果）？
   - 数字是否可复算、口径是否一致？
   - 是否过度概括（以个案推全体）？

判定规则：三项全部 >= 7 且无致命问题(critical) → PASS，否则 FAIL。

严格输出JSON（不要markdown代码块、不要多余文字）：
{"verdict":"PASS或FAIL","scores":{"traceability":N,"structure":N,"rigor":N},"issues":[{"dim":"维度名","critical":true或false,"quote":"稿件原文片段(截断到50字)","problem":"具体问题","fix":"具体改法"}],"summary":"一句话总结"}

issues按严重程度排序，最多列5条。稿件很好时issues可为空数组。"""


def call_deepseek(task: str, draft: str, timeout: int = 90) -> dict:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY 未设置")
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": CHECKER_SYSTEM_PROMPT},
            {"role": "user", "content": f"【原始任务】{task or '(未提供)'}\n\n【待审查稿件】\n{draft}"},
        ],
        "temperature": 0.1,
        "max_tokens": 1500,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    last_err = None
    for attempt in range(2):  # 1次重试
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"].strip()
            # 容错: 模型可能包了 ```json ... ```
            m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            if m:
                content = m.group(1).strip()
            return json.loads(content)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as e:
            last_err = e
            if attempt == 0:
                time.sleep(3)
    raise RuntimeError(f"Checker调用失败(已重试): {last_err}")


def log_result(task: str, draft_len: int, result: dict):
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = {
        "ts": datetime.now(VN_TZ).isoformat(timespec="seconds"),
        "task": (task or "")[:120],
        "draft_chars": draft_len,
        "verdict": result.get("verdict"),
        "scores": result.get("scores"),
        "issue_count": len(result.get("issues", [])),
        "summary": result.get("summary", ""),
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description="SAGE Checker for Self")
    ap.add_argument("--file", help="草稿文件路径(不传则读stdin)")
    ap.add_argument("--task", default="", help="原始任务描述")
    ap.add_argument("--quiet", action="store_true", help="只输出verdict")
    args = ap.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            draft = f.read()
    else:
        draft = sys.stdin.read()
    draft = draft.strip()
    if not draft:
        print("错误: 草稿为空", file=sys.stderr)
        sys.exit(2)

    try:
        result = call_deepseek(args.task, draft)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(2)

    log_result(args.task, len(draft), result)

    if args.quiet:
        print(result.get("verdict", "?"))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    sys.exit(0 if result.get("verdict") == "PASS" else 1)


if __name__ == "__main__":
    main()
