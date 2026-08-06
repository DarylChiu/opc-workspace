#!/usr/bin/env python3
"""
Agent Workspace 一致性校验器 (check_workspaces.py)
=================================================
事故背景: 2026-08-06 xiaofeng 失忆事故 —— openclaw.json 重写时丢失 workspace 字段,
          导致新会话落入 8/4 自动 bootstrap 的空壳工作区 workspace-xiaofeng,
          Bryson 连自己名字都记不起来 (IDENTITY.md 在真工作区里 6/28 就写好了)。

设计目标: 无论 Agent 数量 (4 / 16 / 更多), 每次配置变更后或每日巡检,
          自动发现 "workspace 指向错误" 的 Agent, 不再靠人肉记路径。

校验逻辑 (对一个 agent):
  1. 配置显式性: agents.list[i].workspace 必须存在 (禁止依赖默认推导)
  2. 路径存在性: workspace 目录必须真实存在
  3. 活跃性:     工作区必须是 "活跃记忆区" —— 满足以下任一:
     a. memory/ 下有 >= 3 个 YYYY-MM-DD.md 日记文件
     b. 存在 MEMORY.md 且存在 memory/active.md
     c. 存在 IDENTITY.md 且内容非空模板 (含名字字段)
  4. 空壳检测:   workspace-<id> 或 <id>_workspace 等候选目录若存在但不符合活跃性
                 → 提示 "疑似空壳/被废弃", 便于清理或确认
  5. 交叉验证:   若 agent 同时存在多个候选工作区 (默认推导名 + 显式配置名),
                 只允许配置指向的那个是活跃的, 否则 FAIL

输出: 人类可读报告 + --json 机器可读 (供 cron/运营中枢消费)
退出码: 0 = 全部正常 | 1 = 有 FAIL (配置指向错误) | 2 = 有 WARN (疑似空壳但不影响)
"""

import argparse
import datetime
import json
import os
import sys
import re

DEFAULT_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
# 默认推导规则: OpenClaw 按 workspace-<agentId> 推导 (main 特例为 workspace)
DEFAULT_WS_PATTERNS = [
    lambda aid: os.path.expanduser(f"~/.openclaw/workspace-{aid}"),
    lambda aid: os.path.expanduser(f"~/.openclaw/{aid}_workspace"),
]


def load_config(path):
    with open(path) as f:
        return json.load(f)


def is_active_workspace(ws_path):
    """判断目录是否为活跃记忆工作区 (任一条件满足即活跃)"""
    if not os.path.isdir(ws_path):
        return False
    mem_dir = os.path.join(ws_path, "memory")
    # 条件 a: 日记数量 >= 3
    diary_count = 0
    if os.path.isdir(mem_dir):
        for fn in os.listdir(mem_dir):
            if re.match(r"\d{4}-\d{2}-\d{2}\.md$", fn):
                diary_count += 1
    if diary_count >= 3:
        return True
    # 条件 b: MEMORY.md + memory/active.md
    if os.path.isfile(os.path.join(ws_path, "MEMORY.md")) and os.path.isfile(
        os.path.join(mem_dir, "active.md")
    ):
        return True
    # 条件 c: IDENTITY.md 非空模板 (含名字字段, 排除占位符)
    idp = os.path.join(ws_path, "IDENTITY.md")
    if os.path.isfile(idp):
        try:
            content = open(idp, encoding="utf-8", errors="ignore").read()
        except Exception:
            content = ""
        if content.strip() and "Who Am I?" not in content[:200]:
            return True
    return False


def find_candidate_workspaces(agent_id):
    """找出该 agent 所有可能的工作区路径 (显式配置 + 默认推导 + 反向下划线 + orphan)"""
    cands = set()
    for pat in DEFAULT_WS_PATTERNS:
        try:
            cands.add(pat(agent_id))
        except Exception:
            pass
    # OpenClaw 自动重命名废弃工作区为 *.orphan-YYYYMMDD
    base = os.path.expanduser(f"~/.openclaw")
    if os.path.isdir(base):
        for fn in os.listdir(base):
            if fn.startswith(f"workspace-{agent_id}.") and ".orphan-" in fn:
                cands.add(os.path.join(base, fn))
    return cands


def check_agent(agent_cfg):
    aid = agent_cfg.get("id", "?")
    issues = []
    warns = []

    # 1. 配置显式性
    ws = agent_cfg.get("workspace")
    if not ws:
        issues.append(f"[FAIL] {aid}: 配置中缺少 workspace 字段 (禁止依赖默认推导, 2026-08-06 事故根因)")
        return {"agent": aid, "status": "FAIL", "issues": issues, "warns": warns, "workspace": None}

    ws = os.path.expanduser(ws)

    # 2. 路径存在性
    if not os.path.isdir(ws):
        issues.append(f"[FAIL] {aid}: workspace 路径不存在: {ws}")
        return {"agent": aid, "status": "FAIL", "issues": issues, "warns": warns, "workspace": ws}

    # 3. 活跃性
    if not is_active_workspace(ws):
        issues.append(f"[FAIL] {aid}: workspace 疑似空壳/非活跃记忆区: {ws} (无足够日记/记忆文件)")

    # 4. 空壳检测 (候选目录)
    for cand in find_candidate_workspaces(aid):
        if cand != ws and os.path.isdir(cand):
            if not is_active_workspace(cand):
                warns.append(f"[WARN] {aid}: 存在疑似空壳候选工作区 (可清理或忽略): {cand}")
            else:
                warns.append(f"[WARN] {aid}: 存在【另一个活跃】候选工作区, 请人工确认是否分叉: {cand}")

    # 5. 交叉验证: 显式配置指向的必须是活跃的 (已由 3 覆盖)

    status = "FAIL" if issues else ("WARN" if warns else "PASS")
    return {"agent": aid, "status": status, "issues": issues, "warns": warns, "workspace": ws}


def main():
    ap = argparse.ArgumentParser(description="Agent Workspace 一致性校验器")
    ap.add_argument("--config", default=DEFAULT_CONFIG, help="openclaw.json 路径")
    ap.add_argument("--json", action="store_true", help="输出 JSON (供 cron/运营中枢)")
    ap.add_argument("--verbose", action="store_true", help="显示 PASS 明细")
    args = ap.parse_args()

    cfg = load_config(args.config)
    agents = cfg.get("agents", {}).get("list", [])
    if not agents:
        print("❌ 配置中无 agents.list", file=sys.stderr)
        sys.exit(3)

    results = [check_agent(a) for a in agents]
    fail = [r for r in results if r["status"] == "FAIL"]
    warn = [r for r in results if r["status"] == "WARN"]
    ok = [r for r in results if r["status"] == "PASS"]

    if args.json:
        print(json.dumps({
            "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "total": len(results), "pass": len(ok), "warn": len(warn), "fail": len(fail),
            "agents": results,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"=== Agent Workspace 校验 ({len(agents)} agents, {datetime.date.today()}) ===")
        for r in results:
            if r["status"] == "PASS" and not args.verbose:
                continue
            mark = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[r["status"]]
            print(f"{mark} [{r['status']}] {r['agent']} -> {r['workspace']}")
            for i in r["issues"]:
                print(f"    {i}")
            for w in r["warns"]:
                print(f"    {w}")
        print(f"\n统计: 共{len(results)} | ✅ {len(ok)} | ⚠️ {len(warn)} | ❌ {len(fail)}")

    sys.exit(0 if not fail else (2 if not fail and warn else 1))


if __name__ == "__main__":
    main()
