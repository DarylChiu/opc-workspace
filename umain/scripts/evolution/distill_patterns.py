#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
distill_patterns.py — M0 周度蒸馏：corrections_inbox.jsonl → failure_patterns.json

原理: 原始信号(inbox) → LLM一次过批量提炼 → 满足三条件才成模式:
  ① 重复≥2次 或 severity=critical(Daryl明说规矩/丢数据/误期)
  ② 可行动 (有具体预防动作)
  ③ 具体   (能写进 trigger)

输出: memory/evolution/failure_patterns.json (模式库, M1真相源)
      inbox 中已处理的条目标记 status=distilled / dropped

用法:
  python3 distill_patterns.py            # 蒸馏 inbox 中所有 pending 条目
  python3 distill_patterns.py --dry-run  # 只预览不写入
"""
import json
import os
import sys
import urllib.request
import datetime

WORKSPACE = os.environ.get("WORKSPACE", "/Users/zhaoyuzhao/.openclaw/workspace")
INBOX = os.path.join(WORKSPACE, "memory/evolution/corrections_inbox.jsonl")
LIBRARY = os.path.join(WORKSPACE, "memory/evolution/failure_patterns.json")

MODEL = os.environ.get("DISTILL_MODEL", "deepseek-v4-pro")
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

def load_inbox():
    if not os.path.exists(INBOX):
        return []
    items = []
    with open(INBOX, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return items

def load_library():
    if not os.path.exists(LIBRARY):
        return {"version": "1.0", "patterns": [], "stats": {}}
    with open(LIBRARY, "r", encoding="utf-8") as f:
        return json.load(f)

def call_llm(system, user):
    """调用 DeepSeek API 做蒸馏。失败时降级为本地启发式。"""
    if not API_KEY:
        return None
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
        "max_tokens": 4000,
    }
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"⚠️ LLM调用失败: {e}", file=sys.stderr)
        return None

def heuristic_distill(pending):
    """无API时的本地降级：按类型聚合，简单去重，生成基础模式。"""
    patterns = []
    seen = set()
    for item in pending:
        key = item.get("type", "?") + "|" + item.get("text", "")[:40]
        if key in seen:
            continue
        seen.add(key)
        patterns.append({
            "id": f"fp-auto-{item['ts'][:10].replace('-', '')}",
            "category": item.get("type", "unknown"),
            "project": item.get("project"),
            "trigger": {"raw": item.get("text", "")[:80]},
            "text": item.get("text", ""),
            "source": item.get("source", "auto"),
            "severity": "medium",
            "status": "active",
            "occurrences": 1,
            "last_seen": item.get("ts", "")[:10],
            "resolved": False,
        })
    return patterns

def build_prompt(pending, existing):
    existing_summary = "\n".join(
        f"- {p.get('id')} [{p.get('category')}] {p.get('text', '')[:80]}"
        for p in existing.get("patterns", [])[-20:]
    ) or "(空库)"
    signals = "\n".join(
        f"[{i+1}] ts={s.get('ts')} agent={s.get('agent')} type={s.get('type')} "
        f"source={s.get('source')} project={s.get('project')}\n    text: {s.get('text')}"
        for i, s in enumerate(pending)
    ) or "(无)"
    return f"""你是 OPC 自进化基建的教训蒸馏器。把原始纠错/失败信号提炼为结构化失败模式。

## 入库三条件（全部满足才入库）
① 重复≥2次 或 severity=critical（Daryl明说的规矩/丢数据/误期/安全事故）
② 可行动：有具体预防动作，不是「要更细心」这类空话
③ 具体：能写进 trigger（项目/类型/触发场景可识别）

不满足的：标记 dropped，给出原因。

## 已有模式（供去重/合并参考）
{existing_summary}

## 待蒸馏信号
{signals}

## 输出格式（严格JSON，不要其他文字）
{{
  "patterns": [
    {{
      "category": "类别(如 git_compliance/search_quality/frontend_design)",
      "project": "涉及项目或null",
      "task_type": "任务类型",
      "severity": "critical|high|medium|low",
      "text": "教训正文：上下文+错误+正确做法",
      "trigger": {{"项目": "", "类型": "", "涉及": ""}},
      "occurrences": 1
    }}
  ],
  "dropped": [
    {{"text": "被丢弃的信号原文", "reason": "丢弃原因"}}
  ]
}}"""

def main():
    dry = "--dry-run" in sys.argv
    pending = [i for i in load_inbox() if i.get("status") == "pending"]
    if not pending:
        print("✅ inbox 无 pending 信号，无需蒸馏")
        return 0

    lib = load_library()
    print(f"📥 待蒸馏信号: {len(pending)} 条 | 现有模式: {len(lib.get('patterns', []))} 条")

    llm_out = call_llm(
        "你是严格的教训蒸馏器，只输出JSON。",
        build_prompt(pending, lib),
    )

    if llm_out:
        try:
            # 提取 JSON 块（LLM可能包在```json里）
            start = llm_out.find("{")
            end = llm_out.rfind("}") + 1
            result = json.loads(llm_out[start:end])
            patterns = result.get("patterns", [])
            dropped_texts = {d.get("text", "")[:50] for d in result.get("dropped", [])}
            mode = "LLM蒸馏"
        except Exception as e:
            print(f"⚠️ LLM输出解析失败，降级本地启发式: {e}", file=sys.stderr)
            patterns = heuristic_distill(pending)
            dropped_texts = set()
            mode = "本地启发式(降级)"
    else:
        patterns = heuristic_distill(pending)
        dropped_texts = set()
        mode = "本地启发式(降级)"

    # 去重：与已有模式 text 前缀相似则合并计数
    existing_texts = {p.get("text", "")[:50] for p in lib.get("patterns", [])}
    new_count = 0
    seq = len(lib.get("patterns", []))  # 独立自增计数器，避免跳号/重复
    for p in patterns:
        if p.get("text", "")[:50] in existing_texts:
            for ep in lib["patterns"]:
                if ep.get("text", "")[:50] == p.get("text", "")[:50]:
                    ep["occurrences"] = ep.get("occurrences", 1) + 1
                    ep["last_seen"] = datetime.date.today().isoformat()
            continue
        seq += 1
        p["id"] = f"fp-{datetime.date.today().strftime('%Y%m%d')}-{seq:03d}"
        p["status"] = "active"
        p["resolved"] = False
        p["last_seen"] = datetime.date.today().isoformat()
        lib["patterns"].append(p)
        existing_texts.add(p.get("text", "")[:50])
        new_count += 1

    if dry:
        print(f"[dry-run] 将新增 {new_count} 条模式 (mode={mode})")
        for p in patterns[:5]:
            print(f"  + {p.get('category')} | {p.get('text', '')[:60]}")
        return 0

    # 更新 stats
    active = [p for p in lib["patterns"] if p.get("status") == "active"]
    lib["stats"] = {
        "total_patterns": len(lib["patterns"]),
        "active_patterns": len(active),
        "resolved_patterns": len(lib["patterns"]) - len(active),
        "last_distill": datetime.date.today().isoformat(),
    }

    # 更新 inbox 状态（按索引匹配，避免 id() 不可靠）
    with open(INBOX, "r", encoding="utf-8") as f:
        all_items = [json.loads(l) for l in f if l.strip()]

    # 找到 pending 条目在 all_items 中的索引
    pending_keys = {(i.get("ts"), i.get("text", "")[:40]) for i in pending}
    for item in all_items:
        if (item.get("ts"), item.get("text", "")[:40]) in pending_keys:
            if item.get("text", "")[:50] in dropped_texts:
                item["status"] = "dropped"
            else:
                item["status"] = "distilled"

    with open(INBOX, "w", encoding="utf-8") as f:
        for item in all_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(LIBRARY, "w", encoding="utf-8") as f:
        json.dump(lib, f, ensure_ascii=False, indent=2)

    print(f"✅ 蒸馏完成: 新增 {new_count} 条模式 (mode={mode})")
    print(f"   📚 模式库总计: {len(lib['patterns'])} 条")
    return 0

if __name__ == "__main__":
    sys.exit(main())
