#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
retrieve_patterns.py — M1/M2 三层检索器

三层:
  ① 结构化过滤(确定性): project/task_type/status/severity 硬过滤
  ② 规则表(确定性): 命中规则 → 必注入，不走向量
  ③ 语义兜底(向量层): 剩余候选取 embedding 做余弦 top-N → 排序 → top-5

用法:
  python3 retrieve_patterns.py --task "<任务描述>" [--project <项目>] [--topk 5] [--debug]

输出: 注入候选列表 (id, category, text, reason)
"""
import json
import os
import sys
import math
import argparse

WORKSPACE = os.environ.get("WORKSPACE", "/Users/zhaoyuzhao/.openclaw/workspace")
LIBRARY = os.path.join(WORKSPACE, "memory/evolution/failure_patterns.json")
RULES = os.path.join(WORKSPACE, "memory/evolution/rules_table.json")


def load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cosine(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def match_rules(task, project, rules):
    """规则表匹配：命中即必注入"""
    hits = []
    task_l = task.lower()
    for rule in rules.get("rules", []):
        trig = rule.get("trigger", {})
        # 项目匹配
        if trig.get("project") and project:
            if trig["project"] != project:
                continue
        # 任务类型匹配（子串匹配，宽松）
        types = trig.get("task_type", [])
        matched = any(t.lower() in task_l for t in types) if types else True
        if not matched and types:
            # 反向：任务词出现在类型里（如任务='前端'）
            matched = any(task_l in t.lower() for t in types)
        if matched:
            hits.append(rule)
    return hits


def retrieve(task, project=None, topk=5, debug=False):
    lib = load(LIBRARY, {"patterns": []})
    rules = load(RULES, {"rules": []})
    patterns = [p for p in lib.get("patterns", []) if p.get("status") == "active"]
    results = []
    reasons = []

    # ① 结构化过滤
    candidates = patterns
    if project:
        proj_matched = [p for p in candidates if p.get("project") == project]
        if proj_matched:
            candidates = proj_matched
            reasons.append(f"项目过滤: {project} ({len(candidates)}条)")
        else:
            reasons.append(f"项目过滤: 无{project}专属模式，放宽到全部")

    # ② 规则表命中（必注入）
    rule_hits = match_rules(task, project, rules)
    for rule in rule_hits:
        inject_by = rule.get("inject_by", {})
        cat = inject_by.get("category")
        pid = inject_by.get("id")
        for p in patterns:
            matched = False
            if cat and p.get("category") == cat:
                matched = True
            elif pid and (p.get("id") == pid or pid in p.get("text", "")):
                matched = True
            if matched and p not in results:
                p["_rule_hit"] = True
                results.append(p)
                reasons.append(f"规则命中: {rule.get('name')}")

    # ③ 语义兜底
    semantic_pool = [p for p in candidates if p not in results]
    if semantic_pool:
        # 简单文本特征提取（无embedding时降级为关键词重叠）
        def text_vec(t):
            # 用token出现位置哈希成简易向量（降级方案）
            import hashlib
            vec = {}
            for tok in t.lower().split():
                h = int(hashlib.md5(tok.encode()).hexdigest()[:4], 16)
                vec[h] = vec.get(h, 0) + 1
            return vec

        task_emb = None
        # 尝试从任务文本计算语义（复用API会花钱，此处用本地降级：关键词重叠）
        scored = []
        for p in semantic_pool:
            p_text = p.get("text", "")
            p_emb = p.get("embedding")
            if p_emb:
                # 需要任务embedding——为省API成本，这里用关键词重叠近似
                score = overlap_score(task, p_text)
            else:
                score = overlap_score(task, p_text)
            scored.append((score, p))
        scored.sort(key=lambda x: -x[0])
        for score, p in scored[:topk]:
            if score > 0 and p not in results:
                results.append(p)
                reasons.append(f"语义匹配(重叠度{score:.2f})")

    # 排序：规则命中优先 → severity → 出现次数
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    rule_ids = {r.get("id") for r in results if r.get("_rule_hit")}

    def rank(p):
        is_rule = p.get("id") in rule_ids
        return (0 if is_rule else 1,
                sev_order.get(p.get("severity", "medium"), 2),
                -(p.get("occurrences", 1)))

    results.sort(key=rank)

    if debug:
        print(f"📋 任务: {task} | 项目: {project or '无'}")
        print(f"   过滤: {'; '.join(reasons)}")
        print(f"   候选: {len(candidates)}条 | 注入: {len(results[:topk])}条")
        print()

    out = results[:topk]
    for i, p in enumerate(out, 1):
        reason = reasons[results.index(p)] if p in results else ""
        print(f"[{i}] {p.get('id')} [{p.get('category')}] sev={p.get('severity')} occ={p.get('occurrences')}")
        print(f"    {p.get('text', '')[:100]}")
        print(f"    ↳ {reason}")

    # 清理临时标记
    for p in results:
        p.pop("_rule_hit", None)
    return out


def overlap_score(task, text):
    """关键词重叠分数（本地降级，无API成本）— 中文按字符n-gram + 英文按词"""
    def toks(s):
        # 英文按词，中文按 2-gram（无分词依赖）
        words = [w for w in s.lower().split() if len(w) > 1]
        cjk = ''.join(words)
        cjk_chars = [c for c in cjk if '\u4e00' <= c <= '\u9fff']
        grams = set()
        if len(cjk_chars) >= 2:
            grams.update(''.join(cjk_chars[i:i+2]) for i in range(len(cjk_chars)-1))
        grams.update(words)
        return grams

    task_toks = toks(task)
    text_toks = toks(text)
    if not task_toks:
        return 0.0
    return len(task_toks & text_toks) / len(task_toks)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--project", default=None)
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    retrieve(args.task, args.project, args.topk, args.debug)
