#!/usr/bin/env node
// Convert active.md to 3-section template
// Strategy: collect ALL content blocks → output grouped by section
const fs = require('fs');
const file = process.argv[2];
if (!file) { console.log('Usage: node convert_active_md.js <path>'); process.exit(1); }

const orig = fs.readFileSync(file, 'utf8');
const lines = orig.split('\n');

// Extract first heading + timestamp
let header = [];
let i = 0;
for (; i < lines.length; i++) {
  if (/^## /.test(lines[i].trim())) break;
  header.push(lines[i]);
}

// Parse blocks: each block starts with ## header, ends before next ##
const blocks = [];
let currentHeader = null;
let currentContent = [];

for (; i < lines.length; i++) {
  const trimmed = lines[i].trim();
  if (/^## /.test(trimmed)) {
    if (currentHeader) blocks.push({ header: currentHeader, content: currentContent });
    currentHeader = trimmed;
    currentContent = [];
  } else {
    currentContent.push(lines[i]);
  }
}
if (currentHeader) blocks.push({ header: currentHeader, content: currentContent });

// Classify each block
const done = [];      // ✅ 已完成
const inprog = [];    // 🟢 进行中
const pending = [];   // 🔵 待办
const other = [];     // preserve as-is

for (const b of blocks) {
  const h = b.header;
  // Map to section
  if (h === '## 📋 近期交付' || h === '## ✅ 已完成' || h === '## ✅ 已完成（历史）' ||
      h === '## ⚠️ 记忆系统漏洞（2026-06-14 修复）' ||
      h === '## 🆕 AI技术知识树·案例归档（2026-06-29）' ||
      h === '## 🔴 合规系统修复（2026-06-25）' ||
      h === '## 🆕 OPC Dashboard 设计系统规范（2026-07-07）' ||
      h === '## 🔧 合规修复 (2026-06-15)') {
    // Convert to ### task title
    let title = h.replace(/^## /, '');
    done.push({ header: '### ' + title, content: b.content });
  } else if (h === '## 🟢 进行中' || h === '## 🆕 OPC看板方法论卡片集成') {
    if (h === '## 🆕 OPC看板方法论卡片集成') {
      inprog.push({ header: '### ' + h.replace(/^## /, '') + ' — 等待Daryl确认方向', content: b.content });
    } else {
      // Section header — don't add as task, just pass through content
      inprog.push({ header: null, content: b.content });
    }
  } else if (h === '## ⏳ 等待 Daryl') {
    // Convert checkbox items under this to ###, merge into pending
    let items = [];
    for (const line of b.content) {
      const t = line.trim();
      if (/^- \[ \]/.test(t)) {
        items.push({ header: '### ' + t.replace(/^- \[ \] /, ''), content: [] });
      }
    }
    if (items.length > 0) {
      pending.push({ header: '### ⏸️ 等待 Daryl 反馈', content: [] });
      for (const item of items) pending.push(item);
    }
  } else if (h === '## 🔵 待办') {
    // Convert - [ ] to ###, keep other content
    for (const line of b.content) {
      const t = line.trim();
      if (/^- \[ \]/.test(t)) {
        pending.push({ header: '### ' + t.replace(/^- \[ \] /, ''), content: [] });
      } else if (t.startsWith('-')) {
        // attach detail to last pending item
        if (pending.length > 0 && pending[pending.length - 1].header) {
          pending[pending.length - 1].content.push(line);
        }
      } else if (t) {
        // other content
        if (pending.length > 0 && pending[pending.length - 1].header) {
          pending[pending.length - 1].content.push(line);
        }
      }
    }
  } else {
    // Unknown headers → keep as-is (parser ignores)
    other.push(b);
  }
}

// OUTPUT
const out = [...header];

// Section 1: ✅ 已完成
out.push('');
out.push('## ✅ 已完成');
for (const b of done) {
  out.push('');
  out.push(b.header);
  for (const l of b.content) out.push(l);
}

// Section 2: 🟢 进行中
out.push('');
out.push('## 🟢 进行中');
for (const b of inprog) {
  if (b.header) {
    out.push('');
    out.push(b.header);
  }
  for (const l of b.content) out.push(l);
}

// Section 3: 🔵 待办
out.push('');
out.push('## 🔵 待办');
for (const b of pending) {
  out.push('');
  out.push(b.header);
  for (const l of b.content) out.push(l);
}

// Other sections (keep as-is after main sections)
for (const b of other) {
  out.push('');
  out.push(b.header);
  for (const l of b.content) out.push(l);
}

// Clean trailing blanks
while (out.length > 0 && out[out.length - 1].trim() === '') out.pop();

fs.writeFileSync(file, out.join('\n') + '\n');

// Verify
const result = fs.readFileSync(file, 'utf8');
const rl = result.split('\n');
console.log('Lines: ' + orig.split('\n').length + ' → ' + rl.length);
console.log('\nStructure:');
rl.forEach((l, idx) => {
  const t = l.trim();
  if (/^## /.test(t)) console.log('  [' + t + ']');
  else if (/^### /.test(t)) console.log('    ' + t.substring(0, 80));
});
