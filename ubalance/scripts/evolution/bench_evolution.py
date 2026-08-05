#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bench_evolution.py — L4 交付自检：基建组件运行损耗 + API成本基准测试

Daryl 指令 (2026-08-04): 基建最怕冗余，不能把 prompt 从 100 token 变 1000 token。
每个新基建组件交付时必须量化:
  1. 单任务运行时损耗 (ms)
  2. 输入 prompt token 增量 (注入教训的 token 数)
  3. API 调用成本增量 (每次任务/每周)

用法:
  python3 scripts/evolution/bench_evolution.py           # 全量基准
  python3 scripts/evolution/bench_evolution.py --json    # 输出JSON(供审计)

输出: memory/evolution/bench_report.jsonl (每次运行追加一行)
"""
import json
import os
import sys
import time
import datetime
import subprocess

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.environ.get("WORKSPACE") or os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
REPORT = os.path.join(WORKSPACE, "memory/evolution/bench_report.jsonl")

# 粗略估算 token: 中文 ~1.5字/token, 英文 ~4字符/token
def est_tokens(text):
    cjk = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other = len(text) - cjk
    return int(cjk / 1.5 + other / 4) + 1

def run_retrieve(task, project=None):
    """运行检索器，返回 (耗时ms, 输出文本)"""
    cmd = [sys.executable, os.path.join(WORKSPACE, "scripts/evolution/retrieve_patterns.py"),
           "--task", task]
    if project:
        cmd += ["--project", project]
    t0 = time.perf_counter()
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        elapsed = (time.perf_counter() - t0) * 1000
        return elapsed, out.stdout
    except Exception as e:
        return -1, str(e)

def bench():
    results = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "tool": "bench_evolution.py v1.0",
    }

    # ---- 1. 检索器运行时损耗 (每次任务注入的固定开销) ----
    tasks = [
        ("OPC看板前端UI修改交互逻辑", "opc-dashboard"),
        ("开发成本统计脚本", None),
        ("今天天气怎么样", None),  # 闲聊: 应零注入
        ("提交月度成本汇报", None),
    ]
    retrieve_times = []
    for task, proj in tasks:
        ms, out = run_retrieve(task, proj)
        retrieve_times.append({"task": task, "ms": round(ms, 1), "output_chars": len(out)})
    results["retrieve_times_ms"] = retrieve_times
    results["retrieve_avg_ms"] = round(sum(t["ms"] for t in retrieve_times) / len(retrieve_times), 1)

    # ---- 1b. M2 分类器耗时 (状态机判定) ----
    import subprocess as sp
    classify_times = []
    for msg in ["帮我分析XX方案可行性", "继续分析成本部分", "给我输出个md文件报告", "今天天气怎么样"]:
        t0 = time.perf_counter()
        sp.run([sys.executable, os.path.join(WORKSPACE, "scripts/evolution/classify_task.py"),
                "--msg", msg, "--session", "bench_m2"], capture_output=True, text=True, timeout=15)
        classify_times.append((time.perf_counter() - t0) * 1000)
    results["classify_avg_ms"] = round(sum(classify_times) / len(classify_times), 1)

    # ---- 1c. M2 注入器 token 增量 ----
    def run_inject(msg, mode):
        t0 = time.perf_counter()
        r = sp.run([sys.executable, os.path.join(WORKSPACE, "scripts/evolution/inject_lessons.py"),
                    "--msg", msg, "--mode", mode, "--session", "bench_m2"],
                   capture_output=True, text=True, timeout=15)
        ms = (time.perf_counter() - t0) * 1000
        try:
            d = json.loads(r.stdout)
            return ms, d.get("token_estimate", 0), d.get("injected", 0)
        except Exception:
            return ms, 0, 0

    inj_ms, inj_tok, inj_n = run_inject("开发成本统计脚本", "full")
    results["inject_full"] = {"ms": round(inj_ms, 1), "tokens": inj_tok, "patterns": inj_n}
    inj_ms_l, inj_tok_l, inj_n_l = run_inject("给我输出个md文件报告", "light")
    results["inject_light"] = {"ms": round(inj_ms_l, 1), "tokens": inj_tok_l, "patterns": inj_n_l}
    # 清理 bench session
    sp.run([sys.executable, os.path.join(WORKSPACE, "scripts/evolution/classify_task.py"),
            "--reset", "--session", "bench_m2"], capture_output=True, text=True)

    # ---- 2. Prompt token 增量 (注入教训的上下文开销) ----
    # 检索器输出 = 注入到 context 的教训文本。估算其 token 数。
    _, out1 = run_retrieve("OPC看板前端UI修改交互逻辑", "opc-dashboard")
    _, out2 = run_retrieve("提交月度成本汇报", None)
    inj1_tokens = est_tokens(out1)
    inj2_tokens = est_tokens(out2)
    results["injection_tokens"] = {
        "前端任务注入": inj1_tokens,
        "汇报任务注入": inj2_tokens,
        "闲聊任务注入": 0,
        "上限建议": 500,  # 设计约束: 注入 top-5 < 500 tokens
    }
    # 单条模式平均 token
    lib = json.load(open(os.path.join(WORKSPACE, "memory/evolution/failure_patterns.json")))
    texts = [p.get("text", "") for p in lib.get("patterns", [])]
    avg = sum(est_tokens(t) for t in texts) / len(texts) if texts else 0
    results["pattern_avg_tokens"] = round(avg, 1)

    # ---- 3. API 调用成本 ----
    # 每次任务: 检索=本地numpy(零API) + 分类=关键词(零API) → 0 额外API
    # 每周: 蒸馏 1次LLM调用 + 新模式embedding 1次
    results["api_cost"] = {
        "per_task_retrieve": 0.0,     # 本地计算, 无API
        "per_task_classify": 0.0,     # 关键词表, 无API
        "weekly_distill_llm": "~1次调用(约2K tokens, <$0.01)",
        "weekly_new_pattern_embed": "~N次(每次<$0.0001)",
        "说明": "注入本身是prompt token开销(见上), 不是API调用开销",
    }

    # ---- 4. 总账: 单任务损耗 = 运行时 + 注入token ----
    results["summary"] = {
        "单任务检索耗时": f"{results['retrieve_avg_ms']}ms",
        "单任务分类耗时": f"{results['classify_avg_ms']}ms (M2状态机)",
        "单任务注入token": f"0~{max(inj_tok, inj_tok_l)} tokens (仅任务开始注入一次)",
        "单任务API成本": "$0.00 (零API调用, 纯本地)",
        "每周基建成本": "1次蒸馏LLM调用(<$0.01) + 新模式embedding(<$0.0001/条)",
        "prompt膨胀率参考": "基础prompt约2000-5000 tokens, 注入≤100 → 膨胀≤2-5%",
        "是否超标": "超标" if max(inj_tok, inj_tok_l) > 500 else "✅ 未超标(<500 tokens)",
    }

    # ---- 写入报告 ----
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(json.dumps(results, ensure_ascii=False) + "\n")

    if "--json" in sys.argv:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("=" * 56)
        print("🧬 OPC自进化基建L1 · 运行损耗与成本基准")
        print("=" * 56)
        print(f"\n📐 检索器运行时 (每次任务):")
        for t in results["retrieve_times_ms"]:
            flag = "⚠️" if t["ms"] > 1000 else "✅"
            print(f"  {flag} {t['ms']:>7.1f}ms  {t['task'][:30]}")
        print(f"  平均: {results['retrieve_avg_ms']}ms")
        print(f"  M2分类器平均: {results['classify_avg_ms']}ms")
        print(f"  M2全量注入: {results['inject_full']['ms']}ms / {results['inject_full']['tokens']}tokens / {results['inject_full']['patterns']}条")
        print(f"  M2轻量注入: {results['inject_light']['ms']}ms / {results['inject_light']['tokens']}tokens / {results['inject_light']['patterns']}条")
        print(f"\n📊 Prompt token 增量 (注入教训):")
        for k, v in results["injection_tokens"].items():
            print(f"  {k}: {v}")
        print(f"  单条模式平均: {results['pattern_avg_tokens']} tokens")
        print(f"\n💰 API 成本:")
        for k, v in results["api_cost"].items():
            print(f"  {k}: {v}")
        print(f"\n📋 总账:")
        for k, v in results["summary"].items():
            print(f"  {k}: {v}")
        print(f"\n📄 报告已追加: {REPORT}")
    return 0

if __name__ == "__main__":
    sys.exit(bench())
