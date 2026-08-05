#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
decide.py — 决策三分类器（确定性关键词表，零 LLM）

决策自主环 M1 · 决策自主层工具之一
规则源: LOOP_ENGINEERING_PLAN.md「三、核心机制设计 1.决策状态机」+「九」决策三分类

分类（对接决策状态机）:
  方向型 → 上报 Daryl（做什么/边界/验收标准）—— 永远上报，不自主
  规则型 → 查模式库，命中即用；未命中 → 带默认方案确认一次 → 进模式库
  执行型 → 自主执行 + 记决策日志

机制（只加机制，不加细节限制）:
  · 确定性关键词表，零 LLM 调用，可复现
  · 关键词分档计分：强=2 分 / 弱=1 分，按类别汇总
  · 分数最高者胜出；平分时按优先级 方向型 > 规则型 > 执行型 裁决
    （上报/确认优先，安全优先——宁可多确认一次，不可漏报方向）
  · 无任何关键词命中 → 保守默认「规则型」（查模式库，未命中带默认方案确认一次，不停摆）

用法:
  python3 decide.py "文本"           # 参数输入
  echo "文本" | python3 decide.py    # stdin 输入
  python3 decide.py --text "文本" --json

作为模块:
  from decide import classify_decision
  result = classify_decision("这个功能的边界在哪里")
"""
import argparse
import json
import sys

DECISION_TYPES = ("方向型", "规则型", "执行型")

# ============================================================
# 关键词表（强=2分 / 弱=1分）—— 确定性规则，零 LLM
# ============================================================

# 方向型 = 做什么 / 边界 / 验收标准
DIRECTION_STRONG = ["验收标准", "验收", "边界", "范围"]
DIRECTION_WEAK = [
    "目标", "方向", "做什么", "做不做", "该不该做", "是否要做", "要不要做", "要不要",
    "算对", "确认", "批准", "场景", "用户旅程", "决策点", "红线", "护栏",
    "试点", "定位", "立项", "准入",
]

# 规则型 = 怎么做 / 偏好 / 取舍标准
RULE_STRONG = [
    "偏好", "怎么选", "如何选", "取舍", "取舍标准", "怎么处理", "如何取舍", "怎么定",
    "怎么做", "如何做", "习惯", "喜欢", "倾向", "风格", "优先级", "怎么命名",
]
RULE_WEAK = [
    "规则", "原则", "默认", "规范", "惯例", "约束", "标准", "阈值", "预算",
    "流程", "通常", "一般", "如何", "怎么",
]

# 执行型 = 细节选择
EXEC_WEAK = [
    "细节", "实现", "选型", "技术", "字段", "命名", "参数", "接口", "配置", "结构",
    "写法", "样式", "变量", "函数", "框架", "数据库", "表", "目录", "文件", "工具",
    "库", "微调", "优化", "重构", "前端", "后端", "组件", "语言", "格式", "按钮",
    "界面", "页面",
]

_KEYWORDS = {
    "方向型": (DIRECTION_STRONG, DIRECTION_WEAK),
    "规则型": (RULE_STRONG, RULE_WEAK),
    "执行型": ([], EXEC_WEAK),
}
_TIE_PRIORITY = ("方向型", "规则型", "执行型")  # 平分裁决优先级（上报/确认优先）
_DEFAULT_DECISION = "规则型"  # 无命中保守默认


def classify_decision(text):
    """确定性三分类。

    返回: {decision, scores, matched, reason}
      decision: 方向型 | 规则型 | 执行型
      scores:   各分类计分
      matched:  各分类命中的关键词
      reason:   判定理由（可留痕）
    """
    text = (text or "").strip()
    scores = {}
    matched = {}
    for cat, (strong, weak) in _KEYWORDS.items():
        hits = []
        for kw in strong:
            if kw in text:
                hits.append((kw, 2))
        for kw in weak:
            if kw in text:
                hits.append((kw, 1))
        scores[cat] = sum(w for _, w in hits)
        matched[cat] = [kw for kw, _ in hits]

    if sum(scores.values()) == 0:
        decision = _DEFAULT_DECISION
        reason = ("无关键词命中 → 保守默认规则型"
                  "（查模式库，未命中带默认方案确认一次，不停摆）")
    else:
        best = max(scores.values())
        top = [c for c in DECISION_TYPES if scores[c] == best]
        if len(top) == 1:
            decision = top[0]
        else:
            decision = next(c for c in _TIE_PRIORITY if c in top)
        detail = "；".join(f"{c}: {scores[c]}" for c in DECISION_TYPES if scores[c] > 0)
        reason = f"关键词计分 {detail} → {decision}"
        if len(top) > 1:
            reason += "（平分按优先级裁决）"

    return {
        "decision": decision,
        "scores": scores,
        "matched": matched,
        "reason": reason,
    }


def main():
    ap = argparse.ArgumentParser(description="决策三分类器（确定性关键词表，零 LLM）")
    ap.add_argument("text", nargs="?", default=None, help="决策描述文本；缺省时读 stdin")
    ap.add_argument("--text", dest="text_opt", default=None, help="决策描述文本（--text 形式）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    text = args.text_opt or args.text
    if not text:
        text = sys.stdin.read().strip()
    if not text:
        print("❌ 缺少输入：传参数或 stdin", file=sys.stderr)
        sys.exit(2)

    result = classify_decision(text)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"分类: {result['decision']}")
        print(f"理由: {result['reason']}")
        print(f"命中: {json.dumps(result['matched'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
