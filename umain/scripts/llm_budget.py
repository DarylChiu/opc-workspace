#!/usr/bin/env python3
"""
llm_budget.py — 定时 LLM 调用统一护栏（四道闸）

所有 Agent 的定时任务调 LLM 统一走此入口，不靠自觉。四道闸：
  闸1 触发: 由调用方判断（无新料不跑）
  闸2 输入: 硬顶 input-cap 字符数（保守：1 字符≈1 token），倒序截断保留最新
  闸3 输出: max_tokens = output-cap
  闸4 预算: 周预算（默认 $0.5）超了直接拒绝，不调 API

用法:
  python3 scripts/llm_budget.py \
    --system <system_prompt_file或内联字符串> \
    --input  <input_text_file> \
    --output <output_file> \
    [--model deepseek-v4-flash] \
    [--input-cap 80000] [--output-cap 20000] \
    [--budget 0.5]

记账: memory/evolution/llm_budget.jsonl（每行: ts/model/in/out/cost）
"""

import json
import os
import sys
import time
import argparse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.environ.get("WORKSPACE") or os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BUDGET_FILE = os.path.join(WORKSPACE, "memory", "evolution", "llm_budget.jsonl")
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
ENDPOINT = "https://api.deepseek.com/chat/completions"

# 价格（USD / 1M tokens）—— flash 口径，与 MEMORY.md 对齐
PRICE_IN = 0.44
PRICE_OUT = 1.32


def estimate_tokens(text):
    """保守估算：1 字符 ≈ 1 token（CJK 准确，英文高估=安全侧，宁可多截）。"""
    return len(text)


def truncate(text, cap):
    if estimate_tokens(text) <= cap:
        return text, False
    # 倒序截断：保留末尾（最新内容在末尾）
    return text[-cap:], True


def weekly_cost(now=None):
    now = now or time.time()
    if not os.path.exists(BUDGET_FILE):
        return 0.0
    total = 0.0
    with open(BUDGET_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if now - rec.get("ts", 0) < 7 * 86400:
                    total += rec.get("cost", 0.0)
            except json.JSONDecodeError:
                continue
    return total


def log_cost(rec):
    os.makedirs(os.path.dirname(BUDGET_FILE), exist_ok=True)
    with open(BUDGET_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def call_llm(system, user, model, output_cap, timeout=300):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
        "max_tokens": output_cap,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return content, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def main():
    ap = argparse.ArgumentParser(description="定时 LLM 调用统一护栏")
    ap.add_argument("--system", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--model", default=os.environ.get("BUDGET_MODEL", "deepseek-v4-flash"))
    ap.add_argument("--input-cap", type=int, default=80000)
    ap.add_argument("--output-cap", type=int, default=20000)
    ap.add_argument("--budget", type=float, default=0.5)
    args = ap.parse_args()

    # 闸2 输入
    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()
    text, was_truncated = truncate(text, args.input_cap)
    if was_truncated:
        print(f"⚠️ 输入超上限 {args.input_cap}，已倒序截断", file=sys.stderr)

    # 闸4 预算
    spent = weekly_cost()
    if spent >= args.budget:
        print(f"🛑 周预算已超（已用 ${spent:.4f} / 上限 ${args.budget:.2f}），本次拒绝调用", file=sys.stderr)
        sys.exit(2)

    if not API_KEY:
        print("🛑 无 DEEPSEEK_API_KEY，无法调用", file=sys.stderr)
        sys.exit(3)

    # system：文件存在则读文件，否则当内联字符串
    system = args.system
    if os.path.exists(args.system):
        with open(args.system, "r", encoding="utf-8") as f:
            system = f.read()

    try:
        content, in_tokens, out_tokens = call_llm(system, text, args.model, args.output_cap)
    except Exception as e:
        print(f"🛑 LLM 调用失败: {e}", file=sys.stderr)
        sys.exit(1)

    cost = in_tokens / 1_000_000 * PRICE_IN + out_tokens / 1_000_000 * PRICE_OUT

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(content)

    log_cost({"ts": time.time(), "model": args.model,
              "in": in_tokens, "out": out_tokens, "cost": round(cost, 6)})
    print(f"✅ 完成: in={in_tokens} out={out_tokens} cost=${cost:.6f} "
          f"| 周累计 ${spent + cost:.4f}/{args.budget:.2f}")


if __name__ == "__main__":
    main()
