#!/usr/bin/env python3
"""GEPA minimal example with DeepSeek — M1 compatibility test."""
import os
import json
import sys
import time
import traceback

# Use Python 3.12 for gepa compatibility
PYTHON = "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"

MODELS = {
    "deepseek-chat": "deepseek/deepseek-chat",
    "deepseek-v4": "deepseek/deepseek-v4-pro",
}

def test_model(model_name: str):
    """Run GEPA optimize with a specific model."""
    start = time.time()
    import gepa

    trainset = [
        {"input": "What is 2+2?", "additional_context": {}, "answer": "4"},
        {"input": "What is the capital of France?", "additional_context": {}, "answer": "Paris"},
        {"input": "What color is the sky?", "additional_context": {}, "answer": "blue"},
    ]

    seed_prompt = {
        "system_prompt": "You are a helpful assistant. Answer questions concisely and accurately."
    }

    print(f"\n{'='*60}")
    print(f"Testing model: {model_name}")
    print(f"{'='*60}")

    try:
        result = gepa.optimize(
            seed_candidate=seed_prompt,
            trainset=trainset,
            task_lm=model_name,
            reflection_lm=model_name,
            max_metric_calls=15,
            display_progress_bar=False,
        )
        elapsed = time.time() - start
        print(f"\n✅ SUCCESS ({elapsed:.1f}s)")
        print(f"Best prompt: {result.best_candidate['system_prompt']}")
        print(f"Best score: {result.val_aggregate_scores[result.best_idx]}")
        best_score = result.val_aggregate_scores[result.best_idx]
        return {
            "model": model_name,
            "success": True,
            "elapsed_s": round(elapsed, 1),
            "best_prompt": result.best_candidate['system_prompt'],
            "best_score": best_score,
            "error": None,
        }
    except Exception as e:
        elapsed = time.time() - start
        error_str = f"{type(e).__name__}: {str(e)}"
        trace = traceback.format_exc()
        print(f"\n❌ FAILED ({elapsed:.1f}s)")
        print(f"Error: {error_str}")
        print(f"\nFull traceback:\n{trace}")
        return {
            "model": model_name,
            "success": False,
            "elapsed_s": round(elapsed, 1),
            "best_prompt": None,
            "best_score": None,
            "error": error_str,
            "traceback": trace[-500:],
        }


def main():
    results = {}

    # Test 1: deepseek-chat
    print("=" * 60)
    print("TEST 1: deepseek/deepseek-chat")
    print("=" * 60)
    results["deepseek-chat"] = test_model(MODELS["deepseek-chat"])

    # Test 2: deepseek-v4-pro (if available)
    print("\n" + "=" * 60)
    print("TEST 2: deepseek/deepseek-v4-pro")
    print("=" * 60)
    results["deepseek-v4-pro"] = test_model(MODELS["deepseek-v4"])

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, r in results.items():
        status = "✅ PASS" if r["success"] else "❌ FAIL"
        print(f"  {name}: {status} ({r['elapsed_s']}s)")
        if r["success"]:
            print(f"    Best score: {r['best_score']}")
            print(f"    Best prompt (first 120 chars): {r['best_prompt'][:120]}...")
        else:
            print(f"    Error: {r['error']}")

    # Save results
    outpath = os.path.join(os.path.dirname(__file__) or ".", "M1_results.json")
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {outpath}")

    return results


if __name__ == "__main__":
    main()
