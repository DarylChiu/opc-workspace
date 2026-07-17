# Sub-Agent Run Traces

Directory for sub-agent execution traces and summaries.

## Structure
```
{subagent_id}_{task_slug}/
  ├── execution_trace.jsonl   # Per-step operation log
  └── summary.md              # Deliverable + execution summary + lessons
```

## Trace Format (JSONL)
```json
{"step":N, "action":"tool_call|web_search|decision|error|complete",
 "tool":"tool_name", "params":{...}, "result_summary":"...",
 "decisions":["why chose this"], "errors":[], "timestamp":"ISO8601"}
```

## Retention
- Active traces: kept in this directory
- Completed traces: git committed, then moved to `archive/`
