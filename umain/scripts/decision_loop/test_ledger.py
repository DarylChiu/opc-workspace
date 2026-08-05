#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_ledger.py — decision_ledger.py 决策账本回归测试

覆盖（≥3 用例）:
  1. 写入（append 创建文件 + 默认值补齐 + 必填校验）
  2. 追加（append-only 完整性，行数只增不减）
  3. 查询（按 agent / 按时间范围 / 损坏行跳过）

用法: python3 scripts/decision_loop/test_ledger.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decision_ledger import append_record, query  # noqa: E402

REC1 = {
    "agent": "main", "task": "M1工具", "decision_type": "执行型",
    "chosen": "关键词权重计分", "alternatives": ["LLM分类"],
    "why": "零LLM确定性", "rejected": "LLM(违规)",
}
REC2 = {
    "agent": "xiaofeng", "task": "剪辑MVP", "decision_type": "规则型",
    "chosen": "用户替身", "why": "减少提问",
}


def test_write(tmp_ledger):
    """写入: 创建文件 + 默认值补齐 + 必填校验"""
    rec = append_record(REC1, ledger=tmp_ledger)
    assert rec["ts"] and rec["is_exception"] is False  # 默认值补齐
    assert rec["alternatives"] == ["LLM分类"] and rec["rejected"] == "LLM(违规)"
    lines = [l for l in open(tmp_ledger) if l.strip()]
    assert len(lines) == 1
    assert json.loads(lines[0])["agent"] == "main"
    # 缺必填字段 → 拒绝
    try:
        append_record({"agent": "main"}, ledger=tmp_ledger)
        assert False, "应拒绝缺必填字段"
    except ValueError:
        pass
    # 非法决策分类 → 拒绝
    try:
        append_record({**REC1, "decision_type": "乱分类"}, ledger=tmp_ledger)
        assert False, "应拒绝非法 decision_type"
    except ValueError:
        pass
    print("  ✅ 1. 写入: 创建/默认值/必填校验/类型白名单")


def test_append(tmp_ledger):
    """追加: append-only 完整性，行数只增不减"""
    append_record(REC1, ledger=tmp_ledger)
    append_record(REC2, ledger=tmp_ledger)
    append_record(REC1, ledger=tmp_ledger)
    lines = [l for l in open(tmp_ledger) if l.strip()]
    assert len(lines) == 3, "追加 3 次应 3 行"
    rows, skipped = query(ledger=tmp_ledger)
    assert len(rows) == 3 and skipped == 0
    assert rows[1]["agent"] == "xiaofeng"  # 顺序保持
    print("  ✅ 2. 追加: append-only 3 行，顺序保持")


def test_query(tmp_ledger):
    """查询: 按 agent / 按时间范围 / 损坏行跳过"""
    append_record(REC1, ledger=tmp_ledger)
    append_record(REC2, ledger=tmp_ledger)
    # 按 agent
    rows, _ = query(agent="main", ledger=tmp_ledger)
    assert len(rows) == 1 and rows[0]["agent"] == "main"
    # 按时间范围（含边界）
    rows, _ = query(since="2026-08-03", until="2026-08-09", ledger=tmp_ledger)
    assert len(rows) == 2
    rows, _ = query(since="2030-01-01", ledger=tmp_ledger)
    assert len(rows) == 0
    # 损坏行跳过不中断
    with open(tmp_ledger, "a") as f:
        f.write("{broken json}\n")
    rows, skipped = query(ledger=tmp_ledger)
    assert len(rows) == 2 and skipped == 1
    print("  ✅ 3. 查询: agent/范围/损坏行跳过")


def main():
    tmp = tempfile.mkdtemp(prefix="ledger_test_")
    print("== test_ledger.py ==")
    test_write(os.path.join(tmp, "dl_write.jsonl"))
    test_append(os.path.join(tmp, "dl_append.jsonl"))
    test_query(os.path.join(tmp, "dl_query.jsonl"))
    print("✅ test_ledger.py 全部通过（3 用例）")


if __name__ == "__main__":
    main()
