#!/usr/bin/env python3
"""扫描4个project文件的阻塞/风险项，按天数分级。纯确定性解析。"""
import re, sys
from datetime import date
from pathlib import Path

PROJECT_FILES = {
    "Kitty":    Path("/Users/zhaoyuzhao/.openclaw/workspace/memory/project_main.md"),
    "Xiaofeng": Path("/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/memory/project_xiaofeng.md"),
    "Balance":  Path("/Users/zhaoyuzhao/.openclaw/workspace-balance/memory/project_Balance.md"),
    "Self":     Path("/Users/zhaoyuzhao/.openclaw/workspace-self/memory/project_Self.md"),
}
TODAY = date.today()
RESOLVED = re.compile(r'✅|已修复|已恢复|已从|已重启|已写入|已清理|done|resolved')


def parse_date(s: str):
    """Parse '7/24', '2026-07-24', '7-24' → date or None"""
    s = s.strip()
    if not s:
        return None
    for pat in [r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', r'(\d{1,2})[/\-](\d{1,2})']:
        m = re.search(pat, s)
        if m:
            g = m.groups()
            if len(g) == 3:
                return date(int(g[0]), int(g[1]), int(g[2]))
            return date(TODAY.year, int(g[0]), int(g[1]))
    return None


def classify(days):
    return "🔴" if days >= 7 else "🟠" if days >= 5 else "🟡" if days >= 3 else "🟢"


def find_date_nearby(lines, idx, radius=10):
    """Search nearby lines for a date pattern."""
    for j in range(max(0, idx - radius), min(len(lines), idx + radius)):
        m = re.search(r'(\d{1,2}[/\-]\d{1,2})', lines[j])
        if m:
            d = parse_date(m.group(1))
            if d:
                return d
    return None


def scan_file(filepath, agent):
    """Scan a project file for blockers. Returns list of (agent, days, level, project, desc)."""
    if not filepath.exists():
        return []
    lines = filepath.read_text(encoding="utf-8").split("\n")
    items = []
    current_project = ""
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("### ") and not line.startswith("#### "):
            current_project = line[4:].strip()

        # 1. 风险/问题 table
        if re.match(r'^####\s*(风险|问题|阻塞|Risk|Issue)', line):
            for j in range(i + 1, min(len(lines), i + 30)):
                l = lines[j].strip()
                if l.startswith("#") or (l.startswith("---") and j > i + 1):
                    break
                if not l.startswith("|") or re.match(r'^\|[\s\-:|\-]+\|$', l):
                    continue
                cells = [c.strip() for c in l.strip("|").split("|")]
                if len(cells) < 2 or cells[0].lower() in ("日期", "date", ""):
                    continue
                if cells[1].strip() in ("无", "") or RESOLVED.search(cells[3] if len(cells) > 3 else ""):
                    continue

                d = parse_date(cells[0])
                if not d:
                    m = re.search(r'(\d{1,2}[/\-]\d{1,2})', cells[1])
                    d = parse_date(m.group(1)) if m else find_date_nearby(lines, i, 5)
                if not d:
                    continue

                days = max(0, (TODAY - d).days)
                lvl = classify(days)
                if lvl == "🟢":
                    continue
                desc = cells[1][:60] + ("..." if len(cells[1]) > 60 else "")
                proj = f"·{current_project}" if current_project else ""
                items.append((agent, days, lvl, proj, desc))

        # 2. | 阻塞项 | metadata row with numbered items
        if "### " in line and not line.startswith("#### "):
            for j in range(i + 1, min(len(lines), i + 35)):
                l = lines[j].strip()
                if l.startswith("#") or l.startswith("---"):
                    break
                if not l.startswith("|") or "阻塞项" not in l:
                    continue
                cells = [c.strip() for c in l.strip("|").split("|")]
                for c in cells:
                    if c in ("阻塞项", "无") or c.startswith("无（") or RESOLVED.search(c):
                        continue
                    for part in re.split(r'[①②③④⑤⑥⑦⑧⑨⑩]', c):
                        part = part.strip()
                        if len(part) < 3 or RESOLVED.search(part):
                            continue
                        days = 0
                        m = re.search(r'(\d+)\s*天', part)
                        if m:
                            days = int(m.group(1))
                        else:
                            m2 = re.search(r'(\d{1,2}[/\-]\d{1,2})', part)
                            if m2:
                                d = parse_date(m2.group(1))
                                if d:
                                    days = max(0, (TODAY - d).days)
                        if days == 0:
                            continue
                        lvl = classify(days)
                        if lvl == "🟢":
                            continue
                        desc = part[:60] + ("..." if len(part) > 60 else "")
                        proj = f"·{current_project}" if current_project else ""
                        items.append((agent, days, lvl, proj, desc))
                    break  # only one 阻塞项 row
        i += 1
    return items


def main():
    all_items = []
    for agent, path in PROJECT_FILES.items():
        try:
            all_items.extend(scan_file(path, agent))
        except Exception as e:
            print(f"  ⚠️ 解析 {agent} 文件出错: {e}", file=sys.stderr)

    if not all_items:
        return

    level_order = {"🔴": 0, "🟠": 1, "🟡": 2}
    all_items.sort(key=lambda x: (level_order.get(x[2], 9), -x[1]))

    print("🔍 阻塞扫描")
    stats = {"🔴": 0, "🟠": 0, "🟡": 0, "total": 0}
    for agent, days, lvl, proj, desc in all_items:
        print(f"  {lvl} {agent}{proj} — 阻塞{days}天, {desc}")
        stats[lvl] += 1
        stats["total"] += 1
    print(f"  统计: 总计{stats['total']}项 | 🔴{stats['🔴']} 🟠{stats['🟠']} 🟡{stats['🟡']}")


if __name__ == "__main__":
    main()
