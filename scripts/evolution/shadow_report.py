#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shadow_report.py — Phase 0 影子模式评估报告（测试期结束运行）

统计 shadow_log.jsonl:
  - 总记录数 / 判定分布 (new_task/continuation/deliverable_upgrade/chat)
  - 本应注入条数 / 平均token估算（成本红线 ≤500tokens/任务）
  - 命中率(hit) / 噪音率(noise) / 误判率(misjudge) — 基于人工回填的 verdict
  - 误判明细（供 Phase 1 准入决策）

verdict 回填: 每条日志的 "verdict" 字段由评估者(Kitty/Daryl)标注:
  hit      = 本应注入的教训确实相关有用
  noise    = 注入了但不相关（噪音）
  misjudge = 分类决策本身错了（该注入的没注入 / 不该注入的注入了）

用法:
  python3 shadow_report.py                     # 全量统计
  python3 shadow_report.py --verdicts file.jsonl  # 合并人工verdict后出报告
"""
import json
import os
import sys
import datetime
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.environ.get("WORKSPACE") or os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
SHADOW_LOG = os.path.join(WORKSPACE, "memory/evolution/shadow/shadow_log.jsonl")


def load_log():
    if not os.path.exists(SHADOW_LOG):
        return []
    recs = []
    with open(SHADOW_LOG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return recs


def load_verdicts(path):
    verdicts = {}
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    v = json.loads(line)
                    verdicts[v.get("ts")] = v.get("verdict")
                except json.JSONDecodeError:
                    continue
    return verdicts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdicts", default=None, help="人工verdict文件(jsonl)")
    args = ap.parse_args()

    recs = load_log()
    if not recs:
        print("ℹ️ shadow_log 为空 — 测试期内无任务边界触发")
        return 0

    verdicts = load_verdicts(args.verdicts)

    print(f"📊 L1 Phase0 影子模式评估报告")
    print(f"   生成时间: {datetime.datetime.now().isoformat(timespec='seconds')}")
    print(f"   日志范围: {recs[0]['ts']} → {recs[-1]['ts']}")
    print(f"   总记录数: {len(recs)}")
    print()

    # 判定分布
    from collections import Counter
    dec = Counter(r["decision"] for r in recs)
    print("── 判定分布 ──")
    for k in ("new_task", "continuation", "deliverable_upgrade", "chat"):
        print(f"   {k:<20} {dec.get(k, 0)}")
    print()

    # 注入模拟统计
    would_inject = [r for r in recs if r["simulated_injection"]["mode"] != "none"]
    total_patterns = sum(len(r["simulated_injection"]["patterns"]) for r in would_inject)
    tokens = [r["simulated_injection"]["token_estimate"] for r in would_inject]
    avg_tokens = sum(tokens) / len(tokens) if tokens else 0
    max_tokens = max(tokens) if tokens else 0
    print("── 注入模拟（若为线上模式）──")
    print(f"   本应触发注入的任务: {len(would_inject)}/{len(recs)}")
    print(f"   本应注入模式总数: {total_patterns} 条")
    print(f"   token估算: 平均 {avg_tokens:.0f} / 最大 {max_tokens} (红线≤500)")
    print()

    # verdict 统计（若已回填）
    vd = Counter()
    details = []
    for r in recs:
        v = r.get("verdict") or verdicts.get(r["ts"])
        if v:
            vd[v] += 1
            details.append((r["ts"], v, r["decision"], r["msg"][:40], r.get("reason", "")))
    if vd:
        total_v = sum(vd.values())
        print("── 人工评估（verdict）──")
        for k in ("hit", "noise", "misjudge"):
            n = vd.get(k, 0)
            print(f"   {k:<10} {n} ({n/total_v*100:.0f}%)" if n else f"   {k:<10} 0")
        print(f"   已评估: {total_v}/{len(recs)}")
        if vd.get("noise") or vd.get("misjudge"):
            print("\n── 问题明细 ──")
            for ts, v, d, msg, reason in details:
                if v in ("noise", "misjudge"):
                    print(f"   [{v}] {ts} 判定={d} | {msg}")
                    print(f"        ↳ {reason}")
    else:
        print("── 人工评估 ──")
        print("   未回填 verdict（周五由 Kitty/Daryl 标注 hit/noise/misjudge）")

    # 准入建议
    print("\n── Phase 1 准入参考 ──")
    if vd.get("misjudge", 0) > 0:
        print("   ⚠️ 存在误判 → 先修分类器再考虑开放低风险任务")
    elif vd.get("noise", 0) > 0:
        print("   ⚠️ 存在噪音注入 → 收紧检索阈值或调低 topk")
    else:
        print("   ✅ 无明确问题 → 可评估开放低风险任务（Phase 1）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
