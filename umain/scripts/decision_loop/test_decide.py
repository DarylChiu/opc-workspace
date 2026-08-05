#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_decide.py — decide.py 决策三分类器回归测试

覆盖: 三分类各 ≥3 例 + 边界 case（平分裁决 / 优先级 / 无命中保守默认）
验收红线: 分类准确率 ≥ 85%（当前 13/13 = 100%）

用法: python3 scripts/decision_loop/test_decide.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decide import classify_decision  # noqa: E402

# (输入文本, 期望分类)
CASES = [
    # ---- 方向型（做什么/边界/验收标准）----
    ("剪辑MVP的验收标准是什么", "方向型"),
    ("这个功能的边界在哪里", "方向型"),
    ("本次试点范围怎么定", "方向型"),            # 边界: 方向3 vs 规则3 平分 → 优先级
    ("要不要给 Balance 财务任务开预授权区", "方向型"),
    ("新任务要不要走新流程", "方向型"),          # 边界: 要不要 vs 流程 平分 → 优先级
    # ---- 规则型（怎么做/偏好/取舍标准）----
    ("文件命名你偏好怎么处理", "规则型"),
    ("技术选型怎么取舍", "规则型"),
    ("错误预算阈值设为多少", "规则型"),
    ("汇报格式怎么定", "规则型"),
    # ---- 执行型（细节选择）----
    ("这个按钮的交互细节怎么实现", "执行型"),
    ("前端用 Vue 还是 React", "执行型"),
    ("这个字段叫什么名字", "执行型"),
    # ---- 边界: 无关键词命中 → 保守默认规则型 ----
    ("嗯", "规则型"),
]


def main():
    passed = 0
    failed = []
    for text, expected in CASES:
        result = classify_decision(text)
        got = result["decision"]
        if got == expected:
            passed += 1
            print(f"  ✅ {text[:26]:<28} → {got}")
        else:
            failed.append((text, expected, got))
            print(f"  ❌ {text[:26]:<28} expect={expected} got={got}")

    total = len(CASES)
    accuracy = passed / total
    print("-" * 60)
    print(f"通过 {passed}/{total}，准确率 {accuracy:.0%}（红线 ≥ 85%）")
    if failed:
        for text, exp, got in failed:
            print(f"  失败用例: {text} | expect={exp} | got={got}")
        sys.exit(1)
    if accuracy < 0.85:
        print("❌ 准确率未达 85% 红线")
        sys.exit(1)
    print("✅ test_decide.py 全部通过")


if __name__ == "__main__":
    main()
