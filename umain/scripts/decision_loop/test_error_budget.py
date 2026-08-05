#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_error_budget.py — error_budget.py 周度错误预算回归测试

覆盖（≥5 用例）:
  1. 正常消耗记账
  2. 单个错误不降档（只有周总量超支才刹车）
  3. 超支降档 L3→L2（输出降档信号）
  4. 周重置（跨周自动归零回升 L3）
  5. 磨合期不耗预算（--grace）
  6. P0 拦截（level 10 不进预算）
验收红线: docs/错误预算规则.md「八、验收红线」全部成立

用法: python3 scripts/decision_loop/test_error_budget.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from error_budget import (  # noqa: E402
    record_error, get_status, list_entries, reset_week,
)

BUDGET = 2.0


def setup():
    tmp = tempfile.mkdtemp(prefix="eb_test_")
    return (os.path.join(tmp, "eb.jsonl"),
            os.path.join(tmp, "eb_state.json"))


def test_normal_consumption(ledger, state):
    r = record_error(0.1, "可回滚小错误", "main", "t", ledger=ledger,
                     state_path=state, budget=BUDGET)
    assert r["action"] == "recorded" and r["cost"] == 0.1
    assert r["consumed"] == 0.1 and r["tier"] == "L3" and not r["downgraded"]
    print("  ✅ 1. 正常消耗: 0.1 记账，档位 L3")


def test_single_error_no_downgrade(ledger, state):
    r = record_error(1.0, "发错一条消息", "main", "t", ledger=ledger,
                     state_path=state, budget=BUDGET)
    assert r["consumed"] == 1.1 and r["tier"] == "L3" and not r["downgraded"], r
    print("  ✅ 2. 单个错误不降档: 消耗 1.1 < 预算 2.0，仍 L3")


def test_overspend_downgrade(ledger, state):
    r = record_error(1.0, "不可逆小范围", "main", "t", ledger=ledger,
                     state_path=state, budget=BUDGET)
    assert r["consumed"] >= BUDGET, r
    assert r["tier"] == "L2" and r["downgraded"], r
    assert "降档" in r["message"], r["message"]
    st = get_status(ledger=ledger, state_path=state, budget=BUDGET)
    assert st["exhausted"] and st["downgraded"]
    print("  ✅ 3. 超支降档: 消耗 2.1 ≥ 2.0 → L3→L2，输出降档信号")


def test_weekly_reset(ledger, state):
    # 模拟上周状态 → 自动重置
    st = json.load(open(state))
    st["week_id"] = "2020-01-06"
    json.dump(st, open(state, "w"))
    s = get_status(ledger=ledger, state_path=state, budget=BUDGET)
    assert s["consumed"] == 0 and s["tier"] == "L3" and not s["downgraded"], s
    print("  ✅ 4. 周重置: 跨周自动归零、回升 L3")


def test_grace_period(ledger, state):
    r = record_error(1.0, "磨合期错误", "self", "t", grace="self-personal-km",
                     ledger=ledger, state_path=state, budget=BUDGET)
    assert r["action"] == "grace" and r["cost"] == 0 and r["consumed"] == 0
    assert r["tier"] == "L3"
    rows, _ = list_entries(ledger=ledger)
    assert any(x.get("grace") == "self-personal-km" for x in rows)
    print("  ✅ 5. 磨合期: 错误只记账不耗预算（cost=0）")


def test_p0_block(ledger, state):
    r = record_error(10.0, "删数据/对外承诺", "main", "t", ledger=ledger,
                     state_path=state, budget=BUDGET)
    assert r["action"] == "P0_BLOCK" and r["blocked"] and r["cost"] == 0
    assert r["consumed"] == 0  # 不进预算
    rows, _ = list_entries(ledger=ledger)
    blocked = [x for x in rows if x.get("blocked")]
    assert len(blocked) == 1 and blocked[0]["level"] == 10.0
    print("  ✅ 6. P0 拦截: level 10 不进预算，blocked 留痕")


def main():
    ledger, state = setup()
    reset_week(state_path=state, budget=BUDGET)
    print("== test_error_budget.py ==")
    test_normal_consumption(ledger, state)
    test_single_error_no_downgrade(ledger, state)
    test_overspend_downgrade(ledger, state)
    test_weekly_reset(ledger, state)
    test_grace_period(ledger, state)
    test_p0_block(ledger, state)
    print("✅ test_error_budget.py 全部通过（6 用例）")


if __name__ == "__main__":
    main()
