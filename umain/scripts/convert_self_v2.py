#!/usr/bin/env python3
"""Convert active.md to 3-section template. Preserves ALL content lines."""
import sys, re
from collections import OrderedDict

filepath = sys.argv[1] if len(sys.argv) > 1 else '/Users/zhaoyuzhao/.openclaw/workspace-self/memory/active.md'

with open(filepath) as f:
    original = f.read()

lines = original.split('\n')

# Extract preamble (everything before first ##)
preamble = []
i = 0
while i < len(lines) and not lines[i].strip().startswith('## '):
    preamble.append(lines[i])
    i += 1

# Parse blocks: header → content lines
blocks = OrderedDict()
current_header = None
current_content = []

while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    if stripped.startswith('## '):
        if current_header:
            blocks[current_header] = current_content
        current_header = stripped
        current_content = []
    else:
        current_content.append(line)
    i += 1
if current_header:
    blocks[current_header] = current_content

# Classification
DONE_PROMOTE = [  # Sections with their own ### items → promote them directly
    '## 📋 近期交付',
    '## 🆕 AI技术知识树·案例归档（2026-06-29）',
]
DONE_WRAP = [  # Sections without ### items → wrap as ### task
    '## ⚠️ 记忆系统漏洞（2026-06-14 修复）',
    '## 🔴 合规系统修复（2026-06-25）',
    '## 🆕 OPC Dashboard 设计系统规范（2026-07-07）',
    '## 🔧 合规修复 (2026-06-15)',
]
INPROG_KEEP = ['## 🟢 进行中']
INPROG_MERGE = ['## 🆕 OPC看板方法论卡片集成']
PENDING_MERGE = ['## ⏳ 等待 Daryl']
PENDING_KEEP = ['## 🔵 待办']
OTHER_KEEP = ['## 📊 F1 知识网络完成状态']

# BUILD OUTPUT
out = list(preamble)

# ── ✅ 已完成 ──
out.append('')
out.append('## ✅ 已完成')

for hdr in DONE_PROMOTE:
    if hdr not in blocks:
        continue
    for l in blocks[hdr]:
        if l.strip().startswith('### '):
            out.append('')
            out.append(l)  # promote directly
        else:
            out.append(l)

for hdr in DONE_WRAP:
    if hdr not in blocks:
        continue
    title = hdr.replace('## ', '### ')
    out.append('')
    out.append(title)
    for l in blocks[hdr]:
        out.append(l)

# ── 🟢 进行中 ──
out.append('')
out.append('## 🟢 进行中')

for hdr in INPROG_KEEP:
    if hdr in blocks:
        for l in blocks[hdr]:
            out.append(l)

for hdr in INPROG_MERGE:
    if hdr not in blocks:
        continue
    out.append('')
    out.append('### ' + hdr.replace('## ', '') + ' — 等待Daryl确认方向')
    for l in blocks[hdr]:
        out.append(l)

# ── 🔵 待办 ──
out.append('')
out.append('## 🔵 待办')

if '## ⏳ 等待 Daryl' in blocks:
    out.append('')
    out.append('### ⏸️ 等待 Daryl 反馈')
    for l in blocks['## ⏳ 等待 Daryl']:
        out.append(l)

if '## 🔵 待办' in blocks:
    for l in blocks['## 🔵 待办']:
        stripped = l.strip()
        m = re.match(r'^- \[ \] (.+)', stripped)
        if m:
            out.append('')
            out.append('### ' + m.group(1))
        else:
            out.append(l)

# ── Reference sections ──
for hdr in OTHER_KEEP:
    if hdr not in blocks:
        continue
    out.append('')
    out.append(hdr)
    for l in blocks[hdr]:
        out.append(l)

# Cleanup trailing blanks
while out and out[-1].strip() == '':
    out.pop()

result = '\n'.join(out) + '\n'

# Verify
print(f"Original: {len(lines)} lines → New: {len(out)} lines")
print("\nStructure:")
for idx, l in enumerate(out):
    t = l.strip()
    if t.startswith('## '):
        print(f"  L{idx+1}: {t}")
    elif t.startswith('### '):
        print(f"    L{idx+1}: {t[:90]}")

# Count ### items per section
sections = {'done': 0, 'in_progress': 0, 'pending': 0}
current = None
for l in out:
    t = l.strip()
    if t == '## ✅ 已完成': current = 'done'
    elif t == '## 🟢 进行中': current = 'in_progress'
    elif t == '## 🔵 待办': current = 'pending'
    elif t.startswith('## '): current = None
    elif t.startswith('### ') and current:
        sections[current] += 1
print(f"\nTask counts: done={sections['done']} in_progress={sections['in_progress']} pending={sections['pending']}")

with open(filepath, 'w') as f:
    f.write(result)
print(f"\n✅ Written to {filepath}")
