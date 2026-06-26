"""
视频分析日志系统 v1
每次管线运行后写入 JSONL，支持后置人工标注和累积查询。
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_FILE = LOG_DIR / "runs.jsonl"
ANNOTATION_FILE = LOG_DIR / "annotations.json"


# ═══ 日志写入 ═══

def log_run(
    video_meta: dict,
    pipeline_results: dict,
    token_stats: dict,
    elapsed_ms: float,
    pass1_enabled: bool = True,
    pass2_enabled: bool = True,
    pass3_enabled: bool = True,
    causal_enabled: bool = True,
):
    """写入一次完整分析运行日志"""
    run_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()

    # ── 提取 Pass 摘要 ──
    passes = {}

    # Pass 1
    p1_story = pipeline_results.get("pass1_story")
    passes["pass1"] = {
        "triggered": pass1_enabled,
        "genre": p1_story.get("genre", []) if p1_story else None,
        "confidence": pipeline_results.get("pass1_confidence"),
        "needs_detail": p1_story.get("needsDetail") if p1_story else None,
        "synopsis_short": (p1_story.get("synopsis", "")[:80]) if p1_story else None,
    }

    # Pass 2
    p2_story = pipeline_results.get("pass2_story")
    passes["pass2"] = {
        "triggered": pass2_enabled and p2_story is not None,
        "genre": p2_story.get("genre", []) if p2_story else None,
        "confidence": pipeline_results.get("pass2_confidence"),
        "synopsis_short": (p2_story.get("synopsis", "")[:80]) if p2_story else None,
    }

    # Causal reasoning
    causal_result = pipeline_results.get("causal_reasoning", {})
    passes["causal"] = {
        "triggered": causal_enabled and bool(causal_result),
        "is_coherent": causal_result.get("isCoherent"),
        "confidence": causal_result.get("confidence"),
        "unexplained_count": len(causal_result.get("unexplained", [])),
        "unexplained_short": causal_result.get("unexplained", [])[:3],
        "needs_dense_scan": causal_result.get("needsDenseScan"),
    }

    # Pass 3
    p3_story = pipeline_results.get("pass3_story")
    passes["pass3"] = {
        "triggered": pass3_enabled and p3_story is not None,
        "genre": p3_story.get("genre", []) if p3_story else None,
        "confidence": pipeline_results.get("pass3_confidence"),
    }

    # 最终输出
    final_story = pipeline_results.get("story", {})
    cv = pipeline_results.get("cross_validation", {})

    entry = {
        "id": run_id,
        "timestamp": now,
        "video": {
            "path": video_meta.get("path", ""),
            "filename": video_meta.get("filename", ""),
            "duration_s": video_meta.get("duration", 0),
            "label": video_meta.get("label", ""),
            "source": video_meta.get("source", "local"),
        },
        "pipeline": passes,
        "pass_level": pipeline_results.get("pass_level", 0),
        "final_output": {
            "genre": final_story.get("genre", []),
            "synopsis_short": final_story.get("synopsis", "")[:120],
            "narrative_core": final_story.get("narrativeCore", ""),
            "cross_validation": {
                "script_genre": cv.get("script_genre", ""),
                "coherence_score": cv.get("coherence_score"),
                "anomalies": cv.get("anomalies", [])[:3],
            },
        },
        "token": {
            "total": token_stats.get("total_tokens", 0),
            "prompt": token_stats.get("prompt_tokens", 0),
            "completion": token_stats.get("completion_tokens", 0),
            "cost_usd": round(token_stats.get("cost_usd", 0), 6),
        },
        "elapsed_ms": round(elapsed_ms),
        "review": {
            "genre_correct": None,
            "issues": [],
            "notes": "",
            "annotated_by": None,
            "annotated_at": None,
        },
    }

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # 同时写入 annotations.json 索引
    _update_annotation_index(run_id, entry)

    print(f"[LOG] 运行 {run_id} 已记录 → {LOG_FILE}")
    return run_id


def _update_annotation_index(run_id: str, entry: dict):
    """维护一个轻量的待标注索引"""
    idx = {}
    if ANNOTATION_FILE.exists():
        try:
            idx = json.loads(ANNOTATION_FILE.read_text())
        except:
            pass

    idx[run_id] = {
        "timestamp": entry["timestamp"],
        "label": entry["video"]["label"],
        "filename": entry["video"]["filename"],
        "pass_level": entry["pass_level"],
        "final_genre": entry["final_output"]["genre"],
        "pass1_genre": (entry["pipeline"].get("pass1") or {}).get("genre"),
        "pass2_genre": (entry["pipeline"].get("pass2") or {}).get("genre"),
        "causal_coherent": (entry["pipeline"].get("causal") or {}).get("is_coherent"),
        "genre_correct": None,
        "issues": [],
        "notes": "",
    }
    ANNOTATION_FILE.write_text(json.dumps(idx, ensure_ascii=False, indent=2))


# ═══ 标注更新 ═══

def annotate_run(run_id: str, genre_correct: bool = None, issues: list = None, notes: str = ""):
    """更新某次运行的标注（类型是否正确、具体问题、备注）"""
    # 更新 JSONL 中的 review 字段（追加一条标注记录）
    updated = False
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text().strip().split("\n")
        new_lines = []
        for line in lines:
            try:
                entry = json.loads(line)
                if entry.get("id") == run_id:
                    entry["review"]["genre_correct"] = genre_correct
                    entry["review"]["issues"] = issues or []
                    entry["review"]["notes"] = notes
                    entry["review"]["annotated_at"] = datetime.now(timezone.utc).isoformat()
                    entry["review"]["annotated_by"] = "daryl"
                    updated = True
                new_lines.append(json.dumps(entry, ensure_ascii=False))
            except:
                new_lines.append(line)
        LOG_FILE.write_text("\n".join(new_lines) + "\n")

    # 更新 annotation index
    if ANNOTATION_FILE.exists():
        try:
            idx = json.loads(ANNOTATION_FILE.read_text())
            if run_id in idx:
                idx[run_id]["genre_correct"] = genre_correct
                idx[run_id]["issues"] = issues or []
                idx[run_id]["notes"] = notes
                idx[run_id]["annotated_at"] = datetime.now(timezone.utc).isoformat()
                ANNOTATION_FILE.write_text(json.dumps(idx, ensure_ascii=False, indent=2))
        except:
            pass

    return updated


# ═══ 查询工具 ═══

def load_all_runs() -> list:
    """加载所有运行记录"""
    if not LOG_FILE.exists():
        return []
    runs = []
    for line in LOG_FILE.read_text().strip().split("\n"):
        if line.strip():
            try:
                runs.append(json.loads(line))
            except:
                pass
    return runs


def query_runs(
    labeled_only: bool = False,
    unannotated_only: bool = False,
    label_filter: str = None,
    genre_mismatch_only: bool = False,
    limit: int = None,
) -> list:
    """查询运行记录
    - labeled_only: 只返回有 label 的
    - unannotated_only: 只返回未标注的
    - label_filter: 按 label 过滤
    - genre_mismatch_only: 只返回类型判断错误的
    - limit: 限制数量
    """
    runs = load_all_runs()
    result = []

    for r in runs:
        if labeled_only and not r["video"].get("label"):
            continue
        if unannotated_only and r["review"].get("genre_correct") is not None:
            continue
        if label_filter and label_filter not in r["video"].get("label", ""):
            continue
        if genre_mismatch_only and r["review"].get("genre_correct") is not False:
            continue
        result.append(r)

    # 按时间倒序
    result.sort(key=lambda x: x["timestamp"], reverse=True)
    if limit:
        result = result[:limit]
    return result


def stats_summary() -> dict:
    """聚合统计摘要"""
    runs = load_all_runs()
    if not runs:
        return {"total_runs": 0}

    annotated = [r for r in runs if r["review"].get("genre_correct") is not None]
    total = len(runs)

    # 按 label 分组
    by_label = {}
    for r in runs:
        label = r["video"].get("label", "unlabeled")
        by_label.setdefault(label, []).append(r)

    # 类型准确率
    correct = sum(1 for r in annotated if r["review"].get("genre_correct") is True)
    wrong = sum(1 for r in annotated if r["review"].get("genre_correct") is False)

    # Pass 分布
    pass_dist = {1: 0, 2: 0, 3: 0}
    for r in runs:
        pl = r.get("pass_level", 0)
        if pl in pass_dist:
            pass_dist[pl] += 1

    # Pass1 → Pass2 类型漂移
    genre_shifts = 0
    for r in runs:
        p1g = set((r["pipeline"].get("pass1") or {}).get("genre") or [])
        p2g = set((r["pipeline"].get("pass2") or {}).get("genre") or [])
        if p1g and p2g and p1g != p2g:
            genre_shifts += 1

    # 常见 issue 模式（从已标注中提取）
    issue_patterns = {}
    for r in annotated:
        for iss in r["review"].get("issues", []):
            issue_patterns[iss] = issue_patterns.get(iss, 0) + 1

    return {
        "total_runs": total,
        "annotated": len(annotated),
        "unannotated": total - len(annotated),
        "genre_accuracy": f"{correct}/{correct + wrong}" if (correct + wrong) > 0 else "N/A",
        "pass_distribution": pass_dist,
        "genre_shifts_p1_to_p2": genre_shifts,
        "by_label": {k: len(v) for k, v in by_label.items()},
        "common_issues": dict(sorted(issue_patterns.items(), key=lambda x: -x[1])[:5]),
        "avg_tokens": round(sum(r["token"]["total"] for r in runs) / total) if total else 0,
        "avg_cost_usd": round(sum(r["token"]["cost_usd"] for r in runs) / total, 6) if total else 0,
    }


# ═══ CLI ═══

if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "stats":
        s = stats_summary()
        print(json.dumps(s, ensure_ascii=False, indent=2))

    elif cmd == "list":
        unannotated = "--unannotated" in sys.argv
        labeled = "--labeled" in sys.argv
        mismatches = "--mismatch" in sys.argv
        limit = None
        for i, a in enumerate(sys.argv):
            if a == "--limit" and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])

        runs = query_runs(
            unannotated_only=unannotated,
            labeled_only=labeled,
            genre_mismatch_only=mismatches,
            limit=limit,
        )
        for r in runs:
            print(
                f"[{r['id']}] {r['video'].get('label', '?')} | "
                f"PL={r['pass_level']} | "
                f"genre={r['final_output']['genre']} | "
                f"review={r['review'].get('genre_correct', '?')} | "
                f"⏱ {r.get('elapsed_ms', 0) // 1000}s"
            )

    elif cmd == "annotate":
        if len(sys.argv) < 3:
            print("Usage: python analysis_log.py annotate <run_id> [correct|wrong] [notes]")
        else:
            run_id = sys.argv[2]
            genre_correct = None
            if len(sys.argv) > 3:
                g = sys.argv[3].lower()
                if g == "correct":
                    genre_correct = True
                elif g == "wrong":
                    genre_correct = False
            notes = sys.argv[4] if len(sys.argv) > 4 else ""
            ok = annotate_run(run_id, genre_correct=genre_correct, notes=notes)
            print(f"Annotated {run_id}: {'OK' if ok else 'not found'}")

    elif cmd == "export":
        runs = load_all_runs()
        output = []
        for r in runs:
            # 精简导出
            output.append(
                {
                    "id": r["id"],
                    "timestamp": r["timestamp"],
                    "label": r["video"]["label"],
                    "duration_s": r["video"]["duration_s"],
                    "pass_level": r["pass_level"],
                    "p1_genre": (r["pipeline"].get("pass1") or {}).get("genre"),
                    "p2_genre": (r["pipeline"].get("pass2") or {}).get("genre"),
                    "final_genre": r["final_output"]["genre"],
                    "causal_coherent": (r["pipeline"].get("causal") or {}).get("is_coherent"),
                    "causal_unexplained": (r["pipeline"].get("causal") or {}).get("unexplained_count"),
                    "review_correct": r["review"].get("genre_correct"),
                    "review_issues": r["review"].get("issues"),
                    "cost_usd": r["token"]["cost_usd"],
                    "elapsed_s": round(r["elapsed_ms"] / 1000, 1),
                }
            )
        print(json.dumps(output, ensure_ascii=False, indent=2))

    else:
        print(f"Unknown command: {cmd}")
        print("Commands: stats, list, annotate, export")
