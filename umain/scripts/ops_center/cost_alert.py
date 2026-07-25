#!/usr/bin/env python3
"""
cost_alert.py — 检查cost_daily.json，判断是否需要成本预警。
纯确定性解析，不使用LLM/API。
"""

import json
import sys
from pathlib import Path
from datetime import date

COST_FILE = Path("/Users/zhaoyuzhao/WorkBuddy/Claw/opc-dashboard/data/cost_daily.json")

# 月预算（美元）
BUDGETS = {"Kitty": 15, "Bryson": 20, "Balance": 10, "Self": 10}
TOTAL_BUDGET = 55

# Agent name mapping: JSON key contains → budget key
AGENT_NAME_MAP = {
    "Kitty": "Kitty",
    "Bryson": "Bryson",
    "Balance": "Balance",
    "Self": "Self",
}


def find_agent_cost(by_agent: dict, agent_key: str) -> dict | None:
    """Find agent cost data by partial name matching."""
    for json_key, data in by_agent.items():
        if agent_key in json_key:
            return data
    return None


def main():
    if not COST_FILE.exists():
        print(f"💰 成本预警\n  ⚠️ cost_daily.json 文件不存在: {COST_FILE}", file=sys.stderr)
        return

    try:
        data = json.loads(COST_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError) as e:
        print(f"💰 成本预警\n  ⚠️ 无法解析 cost_daily.json: {e}", file=sys.stderr)
        return

    summary = data.get("summary", {})
    by_agent = data.get("by_agent", {})

    today_cost = summary.get("today_cost", 0)
    month_cost = summary.get("month_cost", 0)
    total_cost = summary.get("total_cost", 0)

    alerts = []

    # Rule 1: Daily cost alerts
    if today_cost > 5:
        alerts.append(f"  🔴 今日${today_cost:.2f} 严重越狱(>$5)")
    elif today_cost > 3:
        alerts.append(f"  ⚠️ 今日${today_cost:.2f} 单日预警(>$3)")

    # Rule 2: Monthly budget alerts
    month_pct = (month_cost / TOTAL_BUDGET * 100) if TOTAL_BUDGET > 0 else 0
    if month_cost > TOTAL_BUDGET:
        alerts.append(f"  🔴 本月${month_cost:.2f}/${TOTAL_BUDGET} ({month_pct:.0f}%) 已超总预算")
    elif month_cost > TOTAL_BUDGET * 0.8:
        alerts.append(f"  ⚠️ 本月${month_cost:.2f}/${TOTAL_BUDGET} ({month_pct:.0f}%) 预算预警(>80%)")

    # Rule 3: Per-agent monthly budget alerts
    for agent_name, budget in BUDGETS.items():
        agent_data = find_agent_cost(by_agent, agent_name)
        if agent_data is None:
            continue
        agent_month = agent_data.get("month_cost", 0)
        agent_pct = (agent_month / budget * 100) if budget > 0 else 0
        if agent_month > budget:
            alerts.append(f"  🔴 {agent_name} 本月${agent_month:.2f}/${budget} ({agent_pct:.0f}%) 超个人预算")
        elif agent_month > budget * 0.8:
            alerts.append(f"  ⚠️ {agent_name} 本月${agent_month:.2f}/${budget} ({agent_pct:.0f}%) 个人预算预警")

    # Rule 4: Cumulative cost alert
    if total_cost > 150:
        alerts.append(f"  ℹ️ 累计${total_cost:.2f} 已超$150")

    if not alerts:
        return  # 正常，无输出

    print("💰 成本预警")
    for alert in alerts:
        print(alert)


if __name__ == "__main__":
    main()
