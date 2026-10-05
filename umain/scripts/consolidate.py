#!/usr/bin/env python3
"""
consolidate.py — 记忆巩固（Dream Engine 精简版）

流程:
  1. 增量触发: 读 state 文件，找上次巩固后修改的记忆文件，无新料则跳过
  2. 输入装配: 收集衍生记忆文件（daily logs / episodes / active / INDEX），oldest→newest
  3. 调 llm_budget 做巩固（flash，80K 输入 / 20K 输出）
  4. 输出写 STAGING，绝不碰真 memory
  5. 打印审阅提示

遗忘边界（Daryl 2026-10-05 拍板）:
  - 只产出"建议"，不直接改任何文件
  - 源记录（日志/git/核心文件）永不删，只归档
  - "新增/去重"可自动，"删除/替换"永远人审阅

用法:
  python3 scripts/consolidate.py [--dry-run] [--since <days>]
"""

import json
import os
import sys
import re
import time
import argparse
import subprocess
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.environ.get("WORKSPACE") or os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MEMORY = os.path.join(WORKSPACE, "memory")
STATE_FILE = os.path.join(MEMORY, "evolution", "consolidation_state.json")
STAGING = os.path.join(MEMORY, "_staging")

# 参与巩固的文件类型（仅衍生记忆）
SCAN_PATTERNS = [
    (r"^\d{4}-\d{2}-\d{2}\.md$", "daily"),   # 每日日志
    (r"^learning_.*\.md$", "episode"),
    (r"^incident_.*\.md$", "episode"),
    (r"^project_.*\.md$", "episode"),
    (r"^active\.md$", "active"),
    (r"^INDEX\.md$", "index"),
]
# 永不参与删除/替换的源记录（只读）
PROTECTED = {"SOUL.md", "USER.md", "IDENTITY.md", "MEMORY.md", "AGENTS.md", "TOOLS.md"}


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_run": 0}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def collect_new_memory(last_run):
    """收集上次巩固后修改的衍生记忆文件，按 mtime 升序（旧→新）。"""
    found = []
    for name in sorted(os.listdir(MEMORY)):
        path = os.path.join(MEMORY, name)
        if not os.path.isfile(path) or name in PROTECTED:
            continue
        for pat, kind in SCAN_PATTERNS:
            if re.match(pat, name):
                mtime = os.path.getmtime(path)
                if mtime > last_run:
                    found.append((mtime, name, kind))
                break
    found.sort()
    return found


def assemble_input(files, cap_chars=80000):
    """装配输入；超出 cap 时从最旧的文件开始丢弃（保留最新）。"""
    chunks = []
    total = 0
    for mtime, name, kind in files:
        try:
            with open(os.path.join(MEMORY, name), "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        block = f"\n\n===== 文件: {name} (类型:{kind}) =====\n" + content
        chunks.append((mtime, block))
        total += len(block)
    dropped = 0
    while chunks and total > cap_chars:
        _, b = chunks.pop(0)
        total -= len(b)
        dropped += 1
    if dropped:
        print(f"⚠️ 输入超上限，丢弃最旧的 {dropped} 个文件")
    return "\n".join(b for _, b in chunks)


SYSTEM_PROMPT = """你是 OPC 的记忆巩固器。请阅读以下近期记忆文件，产出两份东西：

1. **INDEX.md 重建版**（≤200 行）：蒸馏出「当前最要紧的 3 件事 + 活跃项目一句话状态 + 近期关键决策 + Agent 速查 + 红线提醒 + 细节路标」，作为新会话启动必读的精炼索引。不重复 MEMORY.md 的指令，不做日志堆砌。

2. **变更建议清单**：列出建议的 去重/合并/归档 操作（哪些文件内容重复、哪些已过期可归档）。只给建议，不执行。

遗忘边界（必须遵守）：
- 绝不建议删除源记录（每日日志、git、SOUL/USER/MEMORY/IDENTITY/AGENTS/TOOLS 核心文件）
- 只建议对「衍生记忆」做去重/归档
- 每条删除/替换类建议必须写明理由

输出格式（严格按此）：
## 一、INDEX.md 重建版
（直接给出可用的 INDEX.md 完整内容，markdown，≤200 行）

## 二、变更建议
- [去重/归档/替换] 目标 → 理由
"""


def main():
    ap = argparse.ArgumentParser(description="记忆巩固（Dream Engine 精简版）")
    ap.add_argument("--dry-run", action="store_true", help="只装配+打印，不调 LLM")
    ap.add_argument("--since", type=int, default=None, help="覆盖：只看最近 N 天")
    args = ap.parse_args()

    state = load_state()
    last_run = state.get("last_run", 0)
    if args.since:
        last_run = time.time() - args.since * 86400

    files = collect_new_memory(last_run)
    if not files:
        print("ℹ️ 无新增记忆，跳过（增量触发闸）")
        return

    print(f"📥 发现 {len(files)} 个新增/修改的衍生记忆文件:")
    for mtime, name, kind in files:
        print(f"   - {name} ({kind})")

    text = assemble_input(files)
    print(f"📦 装配输入 {len(text)} 字符")

    if args.dry_run:
        print("（dry-run，不调 LLM，不写任何文件）")
        return

    os.makedirs(STAGING, exist_ok=True)
    sys_file = os.path.join(STAGING, "_system_prompt.txt")
    in_file = os.path.join(STAGING, "_consolidation_input.txt")
    out_file = os.path.join(STAGING, f"consolidation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")

    with open(sys_file, "w", encoding="utf-8") as f:
        f.write(SYSTEM_PROMPT)
    with open(in_file, "w", encoding="utf-8") as f:
        f.write(text)

    budget_script = os.path.join(SCRIPT_DIR, "llm_budget.py")
    cmd = [sys.executable, budget_script,
           "--system", sys_file, "--input", in_file, "--output", out_file]
    print(f"🔄 调用巩固（flash，80K/20K 闸）...")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"❌ 巩固调用失败 (exit {r.returncode})")
        return

    save_state({"last_run": time.time()})
    print(f"\n📝 巩固产出已写 STAGING（未动真 memory）:")
    print(f"   {out_file}")
    print("   ⚠️ 请人工审阅后手动应用。")


if __name__ == "__main__":
    main()
