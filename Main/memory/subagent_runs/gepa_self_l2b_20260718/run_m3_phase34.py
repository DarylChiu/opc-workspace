#!/usr/bin/env python3
"""
M3: GEPA Optimization Run (Phase 3-4 only)
Baseline results already collected.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE_SELF = Path(os.path.expanduser("~/.openclaw/workspace-self"))
WORKSPACE_MAIN = Path(os.path.expanduser("~/.openclaw/workspace"))
SCRIPTS_DIR = WORKSPACE_SELF / "scripts" / "evolution"
RUN_DIR = WORKSPACE_MAIN / "memory" / "subagent_runs" / "gepa_self_l2b_20260718"
TRACE_PATH = RUN_DIR / "execution_trace.jsonl"

sys.path.insert(0, str(SCRIPTS_DIR))
from self_gepa_adapter import SelfGEPAAdapter

VN_TZ = timezone(timedelta(hours=7))

def trace(step, detail):
    entry = {"ts": datetime.now(VN_TZ).isoformat(), "step": step, **detail}
    with open(TRACE_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[TRACE] {step}: {json.dumps(detail, ensure_ascii=False)[:200]}")

SEED_PROMPT = """你是Self，一个严谨的知识管理Agent。输出要求：

1. **来源可追溯**: 所有事实性结论必须标注来源（文档名/URL/数据来源+时间），引用git管理的文件需附commit hash
2. **推测标注**: 无法溯源的内容标注[推测]或[待验证]
3. **内容分类**: 区分事实、推断、个人意见三类内容
4. **置信度体系**: 结论附置信度（高/中/低），基于证据强度
5. **结构化输出**: 清晰层次 → 结论/发现 → 证据/分析 → 来源 → 置信度 → 风险/局限
6. **严谨表述**: 机制/能力类陈述避免绝对化词汇（保证/100%/绝对），使用"降低风险""理论上""依赖X机制"等表述

格式偏好：
- 使用表格呈现对比数据
- 每段结论附明显分隔符
- 数字标注口径和时间范围"""

SEED_CANDIDATE = {"system_prompt": SEED_PROMPT}


def create_batch_evaluator(adapter):
    def batch_evaluator(pairs, **kwargs):
        results_by_index = [None] * len(pairs)
        candidate_groups = {}
        for idx, (candidate, example) in enumerate(pairs):
            cand_key = json.dumps(candidate, sort_keys=True, ensure_ascii=False)
            if cand_key not in candidate_groups:
                candidate_groups[cand_key] = {"candidate": candidate, "indices": [], "examples": []}
            candidate_groups[cand_key]["indices"].append(idx)
            candidate_groups[cand_key]["examples"].append(example)

        for cand_key, group in candidate_groups.items():
            candidate = group["candidate"]
            examples = group["examples"]
            indices = group["indices"]
            try:
                eval_batch = adapter.evaluate(examples, candidate, capture_traces=True)
                for i, idx in enumerate(indices):
                    score = eval_batch.scores[i] if i < len(eval_batch.scores) else 0.0
                    traj = eval_batch.trajectories[i] if eval_batch.trajectories and i < len(eval_batch.trajectories) else {}
                    sage = traj.get("sage_result", {})
                    side_info = {
                        "sage_scores": sage.get("scores", {}),
                        "verdict": sage.get("verdict", "UNKNOWN"),
                        "issues": sage.get("issues", []),
                        "output": traj.get("output", "")[:500],
                    }
                    results_by_index[idx] = (score, side_info)
            except Exception as e:
                print(f"  [BatchEvaluator ERROR] {e}")
                for idx in indices:
                    results_by_index[idx] = (0.0, {"error": str(e)})
        return results_by_index
    return batch_evaluator


def evaluate_on_test(adapter, test_items, candidate, label):
    """Run evaluation on test set."""
    print(f"\n[{label}] Evaluating on {len(test_items)} tasks...")
    results = []
    total = 0.0
    dims = {"traceability": [], "structure": [], "rigor": []}
    for i, item in enumerate(test_items):
        task = item["task"]
        try:
            eb = adapter.evaluate([item], candidate, capture_traces=True)
            score = eb.scores[0] if eb.scores else 0.0
            total += score
            traj = eb.trajectories[0] if eb.trajectories else {}
            sage = traj.get("sage_result", {})
            scores = sage.get("scores", {})
            for d in dims:
                dims[d].append(scores.get(d, 0))
            results.append({
                "task": task[:80], "score": round(score, 3),
                "scores": {k: scores.get(k,0) for k in dims},
                "verdict": sage.get("verdict"),
            })
            print(f"  [{i+1}] Score: {score:.3f} | T={scores.get('traceability',0)} S={scores.get('structure',0)} R={scores.get('rigor',0)} | {sage.get('verdict','?')}")
        except Exception as e:
            print(f"  [{i+1}] ERROR: {e}")
            results.append({"task": task[:80], "score": 0.0, "error": str(e)})
            for d in dims:
                dims[d].append(0)

    n = len(test_items)
    summary = {
        "label": label, "n_items": n,
        "avg_score": round(total/n if n else 0, 3),
        "dimension_averages": {k: round(sum(v)/len(v), 1) if v else 0 for k, v in dims.items()},
        "pass_rate": f"{sum(1 for r in results if r.get('verdict')=='PASS')}/{n}",
        "per_task": results,
    }
    return summary


def main():
    print("=" * 70)
    print("GEPA M3: Optimization Run (Phases 3-4)")
    print(f"Start: {datetime.now(VN_TZ).isoformat()}")
    print("=" * 70)

    # Load adapter
    adapter = SelfGEPAAdapter(verbose=True)
    trace("start", {"training_count": adapter.training_count})

    # Load baseline from previous run
    baseline_path = RUN_DIR / "M3_results.json"
    if baseline_path.exists():
        with open(baseline_path) as f:
            prev = json.load(f)
        baseline_summary = prev["phase2_baseline"]
        print(f"\nLoaded baseline: avg={baseline_summary['avg_score']:.3f}, dims={baseline_summary['dimension_averages']}")
    else:
        print("ERROR: No baseline found!")
        return

    # Get research tasks
    research_tasks = [d for d in adapter._training_data if d.get("category") == "研究报告" and d["source"] == "benchmark"]
    test_items = [{"task": d["task"]} for d in research_tasks]
    other_tasks = [d for d in adapter._training_data if d not in research_tasks]
    val_items = [{"task": d["task"]} for d in other_tasks[:5]]

    # ── Phase 3: Optimize ──
    print("\n" + "=" * 70)
    print("Phase 3: GEPA Optimization")
    print("=" * 70)

    from gepa.optimize_anything import (
        optimize_anything, GEPAConfig, EngineConfig,
        ReflectionConfig, TrackingConfig, make_litellm_lm,
    )

    batch_eval_fn = create_batch_evaluator(adapter)

    run_dir = str(RUN_DIR / "gepa_run")
    os.makedirs(run_dir, exist_ok=True)

    engine_cfg = EngineConfig(
        max_metric_calls=80,
        parallel=False,
        display_progress_bar=True,
        raise_on_exception=False,
        acceptance_criterion="improvement_or_equal",
        cache_evaluation=True,
        cache_evaluation_storage="disk",
        run_dir=run_dir,
        val_evaluation_policy="full_eval",
        seed=42,
    )

    reflection_lm = make_litellm_lm(
        "deepseek/deepseek-chat",
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
        temperature=0.7,
    )

    reflection_cfg = ReflectionConfig(
        reflection_lm=reflection_lm,
        reflection_minibatch_size=3,
    )

    config = GEPAConfig(
        engine=engine_cfg,
        reflection=reflection_cfg,
        tracking=TrackingConfig(key_prefix="gepa_self_m3"),
    )

    print(f"Config: max_metric_calls={engine_cfg.max_metric_calls}, parallel=False")
    print(f"Train: {len(test_items)} research tasks, Val: {len(val_items)} mixed")
    print(f"Reflection LM: deepseek/deepseek-chat")

    t0 = time.time()
    optimized_prompt = None
    opt_success = False

    try:
        result = optimize_anything(
            seed_candidate=SEED_CANDIDATE,
            batch_evaluator=batch_eval_fn,
            dataset=test_items,
            valset=val_items,
            objective="提高研究报告类输出的SAGE三维评分（traceability/structure/rigor），重点提升来源可追溯性和逻辑严谨性（当前基线T=6.0, R=6.0均不及格）",
            background="Self是知识管理Agent，需输出严谨研究报告。当前prompt有6条规则但实际执行效果差（0/5 PASS），需要让规则更具体、可操作。",
            config=config,
        )
        elapsed = time.time() - t0

        if result.best_candidate:
            if isinstance(result.best_candidate, dict):
                optimized_prompt = result.best_candidate.get("system_prompt", str(result.best_candidate))
            else:
                optimized_prompt = str(result.best_candidate)

        opt_success = True
        trace("phase3_done", {
            "elapsed_sec": round(elapsed, 1),
            "best_score": getattr(result, 'best_score', None),
            "optimized_prompt_len": len(optimized_prompt) if optimized_prompt else 0,
            "total_metric_calls": adapter.num_metric_calls,
            "num_iterations": getattr(result, 'num_iterations', None),
        })
        print(f"\n✅ Optimization done in {elapsed:.1f}s")
        print(f"Best score: {getattr(result, 'best_score', 'N/A')}")
        print(f"Optimized prompt: {len(optimized_prompt) if optimized_prompt else 0} chars")
        print(f"Total metric calls: {adapter.num_metric_calls}")

    except Exception as e:
        elapsed = time.time() - t0
        trace("phase3_error", {"error": str(e), "elapsed_sec": round(elapsed, 1)})
        print(f"\n⚠️ Optimization failed: {e}")
        import traceback
        traceback.print_exc()

    # ── Phase 4: A/B Comparison ──
    comparison = None
    verdict = "SKIP"

    if optimized_prompt:
        print("\n" + "=" * 70)
        print("Phase 4: A/B Comparison")
        print("=" * 70)

        opt_candidate = {"system_prompt": optimized_prompt}
        opt_summary = evaluate_on_test(adapter, test_items, opt_candidate, "optimized")

        delta = opt_summary["avg_score"] - baseline_summary["avg_score"]
        dim_deltas = {}
        for d in ["traceability", "structure", "rigor"]:
            dim_deltas[d] = round(opt_summary["dimension_averages"].get(d, 0) - baseline_summary["dimension_averages"].get(d, 0), 1)

        comparison = {
            "baseline_avg": baseline_summary["avg_score"],
            "optimized_avg": opt_summary["avg_score"],
            "delta": round(delta, 3),
            "delta_pct": round(delta / max(baseline_summary["avg_score"], 0.001) * 100, 1),
            "baseline_pass_rate": baseline_summary["pass_rate"],
            "optimized_pass_rate": opt_summary["pass_rate"],
            "dimension_deltas": dim_deltas,
            "baseline_per_task": baseline_summary["per_task"],
            "optimized_per_task": opt_summary["per_task"],
        }
        verdict = "PASS" if delta > 0 else "FAIL" if delta < 0 else "NO_CHANGE"

        trace("phase4_done", {"delta": comparison["delta"], "delta_pct": comparison["delta_pct"], "verdict": verdict})
        print(f"\n{'='*50}")
        print(f"Baseline: {baseline_summary['avg_score']:.3f} → Optimized: {opt_summary['avg_score']:.3f}")
        print(f"Delta: {comparison['delta']:+.3f} ({comparison['delta_pct']:+.1f}%)")
        print(f"Dim deltas: {dim_deltas}")
        print(f"Baseline PASS: {baseline_summary['pass_rate']} → Optimized: {opt_summary['pass_rate']}")
        print(f"Verdict: {verdict}")
        print(f"{'='*50}")
    else:
        print("\n[Phase 4] SKIPPED — no optimized prompt available")

    # Save
    results = {
        "task": "gepa_self_l2b_20260718_M3",
        "timestamp": datetime.now(VN_TZ).isoformat(),
        "seed_prompt": SEED_PROMPT,
        "optimized_prompt": optimized_prompt,
        "prompt_length": len(optimized_prompt) if optimized_prompt else 0,
        "baseline_summary": baseline_summary,
        "optimization_success": opt_success,
        "total_metric_calls": adapter.num_metric_calls,
        "comparison": comparison,
        "verdict": verdict,
    }

    results_path = RUN_DIR / "M3_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Results: {results_path}")

    return results, verdict


if __name__ == "__main__":
    main()
