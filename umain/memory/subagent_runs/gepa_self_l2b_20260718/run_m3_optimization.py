#!/usr/bin/env python3
"""
M3: GEPA First Optimization Run — 研究报告类别
===============================================
Phase 1: 准备
Phase 2: 基线测试 (优化前)
Phase 3: GEPA 优化运行
Phase 4: A/B 对比
Phase 5: 生成报告

Trace: execution_trace.jsonl
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

# ─── Paths ───
WORKSPACE_SELF = Path(os.path.expanduser("~/.openclaw/workspace-self"))
WORKSPACE_MAIN = Path(os.path.expanduser("~/.openclaw/workspace"))
SCRIPTS_DIR = WORKSPACE_SELF / "scripts" / "evolution"
RUN_DIR = WORKSPACE_MAIN / "memory" / "subagent_runs" / "gepa_self_l2b_20260718"
TRACE_PATH = RUN_DIR / "execution_trace.jsonl"

sys.path.insert(0, str(SCRIPTS_DIR))
from self_gepa_adapter import SelfGEPAAdapter

VN_TZ = timezone(timedelta(hours=7))

# ─── Trace ───
def trace(step: str, detail: dict):
    entry = {"ts": datetime.now(VN_TZ).isoformat(), "step": step, **detail}
    with open(TRACE_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[TRACE] {step}: {json.dumps(detail, ensure_ascii=False)[:200]}")

# ─── Seed Prompt ───
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


# ═══════════════════════════════════════════════════════════════
# Phase 1: Prepare
# ═══════════════════════════════════════════════════════════════

def phase1_prepare():
    """Load data and prepare for optimization."""
    trace("phase1_start", {"message": "Loading adapter and preparing data"})

    adapter = SelfGEPAAdapter(verbose=True)

    # Filter for 研究报告 benchmark entries
    research_tasks = [
        d for d in adapter._training_data
        if d.get("category") == "研究报告" and d["source"] == "benchmark"
    ]
    trace("phase1_data", {
        "total_training": len(adapter._training_data),
        "research_report_tasks": len(research_tasks),
        "research_ids": [d["id"] for d in research_tasks],
        "baseline_score": adapter.baseline_score,
    })

    # Split: 5 research tasks train, others val
    other_tasks = [d for d in adapter._training_data if d not in research_tasks]

    # Use all 5 for training (small dataset)
    train_items = [{"task": d["task"]} for d in research_tasks]
    val_items = [{"task": d["task"]} for d in other_tasks[:5]]  # 5 val items

    print(f"\n[Phase 1] Prepared:")
    print(f"  Train: {len(train_items)} research report tasks")
    print(f"  Val: {len(val_items)} mixed tasks")
    print(f"  Seed prompt length: {len(SEED_PROMPT)} chars")

    return adapter, train_items, val_items, research_tasks, other_tasks


# ═══════════════════════════════════════════════════════════════
# Phase 2: Baseline
# ═══════════════════════════════════════════════════════════════

def phase2_baseline(adapter: SelfGEPAAdapter, test_items: list, label: str = "baseline"):
    """Run baseline evaluation on the test set."""
    trace(f"phase2_{label}_start", {"n_items": len(test_items)})

    candidate = SEED_CANDIDATE

    results = []
    total_score = 0.0
    dimension_scores = {"traceability": [], "structure": [], "rigor": []}
    issues_list = []

    for i, item in enumerate(test_items):
        task = item["task"]
        print(f"\n  [{label}] Task {i+1}/{len(test_items)}: {task[:60]}...")

        try:
            eval_batch = adapter.evaluate(
                [item], candidate, capture_traces=True
            )
            score = eval_batch.scores[0] if eval_batch.scores else 0.0
            total_score += score

            traj = eval_batch.trajectories[0] if eval_batch.trajectories else {}
            sage = traj.get("sage_result", {})
            scores = sage.get("scores", {})
            for dim in ["traceability", "structure", "rigor"]:
                dimension_scores[dim].append(scores.get(dim, 0))
            issues = sage.get("issues", [])
            issues_list.append({"task": task[:80], "verdict": sage.get("verdict"), "issues": issues})

            results.append({
                "task": task[:80],
                "score": round(score, 3),
                "scores": {k: scores.get(k, 0) for k in ["traceability", "structure", "rigor"]},
                "verdict": sage.get("verdict"),
            })

            print(f"    Score: {score:.3f} | T={scores.get('traceability',0)} S={scores.get('structure',0)} R={scores.get('rigor',0)} | {sage.get('verdict','?')}")

        except Exception as e:
            print(f"    ⚠️ Error: {e}")
            results.append({"task": task[:80], "score": 0.0, "error": str(e)})
            for dim in ["traceability", "structure", "rigor"]:
                dimension_scores[dim].append(0)

    n = len(test_items)
    avg_score = total_score / n if n > 0 else 0.0
    dim_avgs = {dim: sum(vals)/len(vals) if vals else 0.0 for dim, vals in dimension_scores.items()}
    pass_count = sum(1 for r in results if r.get("verdict") == "PASS")

    summary = {
        "label": label,
        "n_items": n,
        "avg_score": round(avg_score, 3),
        "dimension_averages": {k: round(v, 1) for k, v in dim_avgs.items()},
        "pass_rate": f"{pass_count}/{n}",
        "per_task": results,
    }

    trace(f"phase2_{label}_done", summary)
    return summary, results


# ═══════════════════════════════════════════════════════════════
# Phase 3: GEPA Optimization
# ═══════════════════════════════════════════════════════════════

def create_batch_evaluator(adapter: SelfGEPAAdapter):
    """Create a batch_evaluator compatible with GEPA's optimize_anything."""

    def batch_evaluator(pairs, **kwargs):
        """
        pairs: list of (candidate_dict, example_dict)
        Returns: list of (score, output, side_info) or (score, side_info)
        """
        # Group by candidate (usually all same in one iteration)
        results_by_index = [None] * len(pairs)

        # Group pairs by candidate
        candidate_groups = {}  # candidate_key -> list of (index, example)
        for idx, (candidate, example) in enumerate(pairs):
            # Use a hashable key
            cand_key = json.dumps(candidate, sort_keys=True, ensure_ascii=False)
            if cand_key not in candidate_groups:
                candidate_groups[cand_key] = {"candidate": candidate, "indices": [], "examples": []}
            candidate_groups[cand_key]["indices"].append(idx)
            candidate_groups[cand_key]["examples"].append(example)

        # Evaluate each candidate group
        for cand_key, group in candidate_groups.items():
            candidate = group["candidate"]
            examples = group["examples"]
            indices = group["indices"]

            try:
                eval_batch = adapter.evaluate(
                    examples, candidate, capture_traces=True
                )
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


def phase3_optimize(adapter: SelfGEPAAdapter, train_items: list, val_items: list):
    """Run GEPA optimization."""
    trace("phase3_start", {
        "n_train": len(train_items),
        "n_val": len(val_items),
        "seed_prompt_len": len(SEED_PROMPT),
    })

    from gepa.optimize_anything import (
        optimize_anything,
        GEPAConfig,
        EngineConfig,
        ReflectionConfig,
        TrackingConfig,
        make_litellm_lm,
    )

    batch_eval_fn = create_batch_evaluator(adapter)

    # Build config
    run_dir = str(RUN_DIR / "gepa_run")
    os.makedirs(run_dir, exist_ok=True)
    engine_cfg = EngineConfig(
        max_metric_calls=60,
        max_candidate_proposals=None,
        parallel=False,  # Sequential to avoid API rate limits
        display_progress_bar=True,
        raise_on_exception=False,  # Don't crash on single eval failures
        acceptance_criterion="improvement_or_equal",  # Be lenient for first run
        cache_evaluation=True,
        cache_evaluation_storage="disk",
        run_dir=run_dir,
        val_evaluation_policy="full_eval",
        seed=42,
    )

    # Create LiteLLM language model for reflection
    reflection_lm = make_litellm_lm(
        "deepseek/deepseek-chat",
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
        temperature=0.7,
    )

    reflection_cfg = ReflectionConfig(
        reflection_lm=reflection_lm,
        reflection_strategy=None,  # Use default reflective mutation
        reflection_minibatch_size=3,
        skip_perfect_score=False,
    )

    tracking_cfg = TrackingConfig(
        use_wandb=False,
        use_mlflow=False,
        key_prefix="gepa_self_m3",
    )

    config = GEPAConfig(
        engine=engine_cfg,
        reflection=reflection_cfg,
        tracking=tracking_cfg,
    )

    print("\n[Phase 3] Starting GEPA optimization...")
    print(f"  Config: max_metric_calls={engine_cfg.max_metric_calls}")
    print(f"  Reflection LM: deepseek/deepseek-chat")
    print(f"  Train size: {len(train_items)}, Val size: {len(val_items)}")

    t0 = time.time()

    try:
        result = optimize_anything(
            seed_candidate=SEED_CANDIDATE,
            batch_evaluator=batch_eval_fn,
            dataset=train_items,
            valset=val_items,
            objective="提高研究报告类输出的SAGE三维评分（traceability/structure/rigor加权分），尤其是来源可追溯性和逻辑严谨性",
            background="Self是一个知识管理Agent，需要输出严谨的研究报告。当前prompt已包含来源标注、推测标注、置信度等要求，但可能在具体执行时不够明确。优化目标：让prompt更具体、更有操作性。",
            config=config,
        )
        elapsed = time.time() - t0

        opt_prompt = None
        if result.best_candidate:
            if isinstance(result.best_candidate, dict):
                opt_prompt = result.best_candidate.get("system_prompt", str(result.best_candidate))
            else:
                opt_prompt = str(result.best_candidate)

        trace("phase3_done", {
            "elapsed_sec": round(elapsed, 1),
            "best_score": getattr(result, 'best_score', None),
            "optimized_prompt_len": len(opt_prompt) if opt_prompt else 0,
            "total_iterations": getattr(result, 'num_iterations', None),
            "total_metric_calls": adapter.num_metric_calls,
        })

        print(f"\n[Phase 3] Optimization complete in {elapsed:.1f}s")
        print(f"  Best score: {getattr(result, 'best_score', 'N/A')}")
        print(f"  Optimized prompt length: {len(opt_prompt) if opt_prompt else 0} chars")
        print(f"  Total metric calls: {adapter.num_metric_calls}")

        return result, opt_prompt

    except Exception as e:
        elapsed = time.time() - t0
        trace("phase3_error", {"error": str(e), "elapsed_sec": round(elapsed, 1)})
        print(f"\n[Phase 3] ⚠️ Optimization failed after {elapsed:.1f}s: {e}")
        import traceback
        traceback.print_exc()
        return None, None


# ═══════════════════════════════════════════════════════════════
# Phase 4: A/B Comparison
# ═══════════════════════════════════════════════════════════════

def phase4_compare(adapter: SelfGEPAAdapter, test_items: list,
                   baseline_summary: dict, optimized_prompt: str | None):
    """Run A/B comparison: baseline vs optimized prompt."""
    if not optimized_prompt:
        trace("phase4_skip", {"reason": "No optimized prompt available"})
        return None

    trace("phase4_start", {"n_test": len(test_items)})

    opt_candidate = {"system_prompt": optimized_prompt}
    opt_summary, opt_results = phase2_baseline(adapter, test_items, label="optimized")

    # Compute comparison
    delta_score = opt_summary["avg_score"] - baseline_summary["avg_score"]
    dim_deltas = {}
    for dim in ["traceability", "structure", "rigor"]:
        dim_deltas[dim] = round(
            opt_summary["dimension_averages"].get(dim, 0) - baseline_summary["dimension_averages"].get(dim, 0), 1
        )

    comparison = {
        "baseline_avg": baseline_summary["avg_score"],
        "optimized_avg": opt_summary["avg_score"],
        "delta": round(delta_score, 3),
        "delta_pct": round(delta_score / max(baseline_summary["avg_score"], 0.001) * 100, 1),
        "baseline_pass_rate": baseline_summary["pass_rate"],
        "optimized_pass_rate": opt_summary["pass_rate"],
        "dimension_deltas": dim_deltas,
        "baseline_per_task": baseline_summary["per_task"],
        "optimized_per_task": opt_summary["per_task"],
    }

    verdict = "PASS" if delta_score > 0 else "FAIL"

    trace("phase4_done", {
        "delta": comparison["delta"],
        "delta_pct": comparison["delta_pct"],
        "verdict": verdict,
    })

    print(f"\n[Phase 4] A/B Comparison:")
    print(f"  Baseline: {baseline_summary['avg_score']:.3f} → Optimized: {opt_summary['avg_score']:.3f}")
    print(f"  Delta: {comparison['delta']:+.3f} ({comparison['delta_pct']:+.1f}%)")
    print(f"  Dim deltas: {dim_deltas}")
    print(f"  Verdict: {verdict}")

    return comparison, verdict


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("GEPA M3: First Optimization Run — 研究报告")
    print(f"Start: {datetime.now(VN_TZ).isoformat()}")
    print("=" * 70)

    # Phase 1: Prepare
    adapter, train_items, val_items, research_tasks, other_tasks = phase1_prepare()

    # Test items for A/B: 5 research report tasks
    test_items = train_items  # Same 5 tasks

    # Phase 2: Baseline
    print("\n" + "=" * 70)
    print("Phase 2: Baseline Test (优化前)")
    print("=" * 70)
    baseline_summary, _ = phase2_baseline(adapter, test_items, label="baseline")
    print(f"\n Baseline avg: {baseline_summary['avg_score']:.3f}")
    print(f" Dim averages: {baseline_summary['dimension_averages']}")
    print(f" Pass rate: {baseline_summary['pass_rate']}")

    # Phase 3: Optimize
    print("\n" + "=" * 70)
    print("Phase 3: GEPA Optimization")
    print("=" * 70)
    result, optimized_prompt = phase3_optimize(adapter, train_items, val_items)

    # Phase 4: Compare
    comparison = None
    verdict = "SKIP"
    if optimized_prompt:
        print("\n" + "=" * 70)
        print("Phase 4: A/B Comparison")
        print("=" * 70)
        # Reset metric counter for clean comparison
        adapter._num_metric_calls = 0
        comparison, verdict = phase4_compare(
            adapter, test_items, baseline_summary, optimized_prompt
        )
    else:
        print("\n[Phase 4] Skipped — no optimized prompt")

    # Save results
    results = {
        "task": "gepa_self_l2b_20260718_M3",
        "timestamp": datetime.now(VN_TZ).isoformat(),
        "phase1": {
            "n_train": len(train_items),
            "n_val": len(val_items),
            "seed_prompt": SEED_PROMPT,
        },
        "phase2_baseline": baseline_summary,
        "phase3_optimization": {
            "success": optimized_prompt is not None,
            "optimized_prompt": optimized_prompt,
            "prompt_length": len(optimized_prompt) if optimized_prompt else 0,
            "total_metric_calls": adapter.num_metric_calls,
            "prompt_diff": None,  # Will be computed in report
        } if optimized_prompt else {"success": False, "error": "Optimization failed"},
        "phase4_comparison": comparison,
        "verdict": verdict,
    }

    results_path = RUN_DIR / "M3_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Results saved to {results_path}")

    return results, verdict


if __name__ == "__main__":
    results, verdict = main()
    print(f"\n{'='*70}")
    print(f"Final Verdict: {verdict}")
    print(f"{'='*70}")
