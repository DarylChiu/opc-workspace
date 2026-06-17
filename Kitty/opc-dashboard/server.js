#!/usr/bin/env node
/**
 * OPC Dashboard Backend — Node.js + Express v2.2 (M2)
 * Agent status · Task CRUD · Artifact scanning · Core projects
 * M2: Workflow editor API · Cost dashboard API · Sandbox/tasks API
 */
const express = require('express');
const { execSync, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8765;
const APP = express();
const BASE = path.resolve(__dirname);
const ARTIFACTS_DIR = path.join(BASE, '..');
const TASKS_FILE = path.join(BASE, 'data', 'tasks.json');
const WORKFLOWS_FILE = path.join(BASE, 'data', 'workflows.json');
const EXCLUDE_DIRS = new Set(['.git', '__pycache__', 'node_modules', 'samples', 'chord-gesture', 'reports', 'opc-dashboard']);

// === Agent Config ===
const AGENTS = {
  kitty:  { name: 'Kitty', role: 'Chief Agent · Execution & Communication', color: '#9999dd', key: 'main' },
  xiaofeng: { name: 'Bryson', role: 'Dev Agent · Full-Stack Engineer', color: '#66ccaa', key: 'xiaofeng' },
  balance: { name: 'Balance', role: 'Cross-Border Financial Analyst · ACCA/CPA/CFA', color: '#50a0ff', key: 'balance' },
  self:  { name: 'Self', role: 'Knowledge Management Expert · CUHK', color: '#ffaa50', key: 'self' },
};

// === Core Projects ===
const CORE_PROJECTS = {
  kitty: [
    { name: 'OPC看板交互系统', phase: 'M2完成，待验收', progress: 95 },
  ],
  xiaofeng: [
    { name: '雅思陪练助手', phase: '深度诊断完成，待确认技术栈', progress: 40 },
    { name: '视频分析MVP', phase: '路演准备中', progress: 60 },
  ],
  balance: [
    { name: '越南税务循环框架', phase: '已完成交付', progress: 100 },
  ],
  self: [
    { name: '知识库体系搭建', phase: '规划中', progress: 20 },
  ],
};

// === Middleware ===
APP.use(express.json({ limit: '2mb' }));
APP.use(express.static(BASE));

fs.mkdirSync(path.join(BASE, 'data'), { recursive: true });
fs.mkdirSync(path.join(BASE, 'data', 'notifications'), { recursive: true });
if (!fs.existsSync(TASKS_FILE)) fs.writeFileSync(TASKS_FILE, JSON.stringify({ tasks: [] }, null, 2));
if (!fs.existsSync(WORKFLOWS_FILE)) fs.writeFileSync(WORKFLOWS_FILE, JSON.stringify({ workflows: [] }, null, 2));

// === API: Agent Status (live via openclaw CLI) ===
APP.get('/api/agents', async (req, res) => {
  try {
    let sessions = [];
    try {
      const sessResult = execSync('openclaw sessions list --json 2>/dev/null || echo "[]"', {
        timeout: 5000, encoding: 'utf8', maxBuffer: 512 * 1024
      });
      sessions = JSON.parse(sessResult);
    } catch(e) {}

    const agents = Object.entries(AGENTS).map(([id, info]) => {
      const agentSessions = sessions.filter(s =>
        (s.agentId || '').includes(info.key) || (s.label || '').toLowerCase().includes(info.key)
      );
      const activeSession = agentSessions.find(s => s.lastActive);
      return {
        id, ...info,
        status: activeSession ? 'active' : 'idle',
        sessionCount: agentSessions.length,
        lastActive: activeSession?.lastActive || null,
        model: activeSession?.model || 'deepseek/deepseek-v4-pro',
      };
    });
    res.json({ ok: true, agents });
  } catch(e) {
    const agents = Object.entries(AGENTS).map(([id, info]) => ({
      id, ...info, status: 'unknown', sessionCount: '?', lastActive: null
    }));
    res.json({ ok: true, agents, _fallback: true });
  }
});

// === API: Core Projects ===
APP.get('/api/projects', (req, res) => {
  res.json({ ok: true, projects: CORE_PROJECTS });
});

// === API: Artifacts ===
APP.get('/api/artifacts', (req, res) => {
  try {
    const artifacts = scanArtifacts(ARTIFACTS_DIR, req.query.type || '');
    res.json({ ok: true, artifacts });
  } catch(e) { res.json({ ok: false, error: e.message }); }
});

function scanArtifacts(dir, typeFilter) {
  const results = [];
  if (!fs.existsSync(dir)) return results;
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.name.startsWith('.') || EXCLUDE_DIRS.has(entry.name)) continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      fs.readdirSync(fullPath, { withFileTypes: true }).forEach(sub => {
        if (!sub.isFile()) return;
        const ext = path.extname(sub.name).toLowerCase();
        const type = getFileType(ext);
        if (type && (!typeFilter || type === typeFilter)) {
          results.push({
            name: `${entry.name}/${sub.name}`,
            path: `/api/preview/${encodeURIComponent(entry.name)}/${encodeURIComponent(sub.name)}`,
            type, ext, project: entry.name,
            size: fs.statSync(path.join(fullPath, sub.name)).size,
          });
        }
      });
    } else {
      const ext = path.extname(entry.name).toLowerCase();
      const type = getFileType(ext);
      if (type && (!typeFilter || type === typeFilter)) {
        results.push({
          name: entry.name,
          path: `/api/preview/${encodeURIComponent(entry.name)}`,
          type, ext, project: '_root',
          size: fs.statSync(fullPath).size,
        });
      }
    }
  }
  return results.sort((a, b) => b.size - a.size);
}

function getFileType(ext) {
  const m = { '.html':'web','.htm':'web','.md':'doc','.txt':'doc','.json':'doc',
    '.py':'code','.js':'code','.ts':'code','.sh':'code',
    '.png':'image','.jpg':'image','.jpeg':'image','.gif':'image','.svg':'image','.webp':'image',
    '.pdf':'other','.csv':'data' };
  return m[ext] || null;
}

// === API: Preview ===
APP.get('/api/preview/*', (req, res) => {
  const fp = decodeURIComponent(req.params[0]);
  const fullPath = path.join(ARTIFACTS_DIR, fp);
  if (!fullPath.startsWith(ARTIFACTS_DIR)) return res.status(403).send('Access denied');
  if (!fs.existsSync(fullPath)) return res.status(404).send('File not found');
  const mime = { '.html':'text/html','.htm':'text/html','.js':'text/javascript',
    '.json':'application/json','.md':'text/plain','.txt':'text/plain',
    '.py':'text/plain','.ts':'text/plain','.sh':'text/plain','.csv':'text/plain' };
  res.type(mime[path.extname(fullPath).toLowerCase()] || 'application/octet-stream');
  res.sendFile(fullPath);
});

// === API: Tasks CRUD ===
function loadTasks() {
  try { return JSON.parse(fs.readFileSync(TASKS_FILE, 'utf8')); } catch { return { tasks: [] }; }
}
function saveTasks(d) { fs.writeFileSync(TASKS_FILE, JSON.stringify(d, null, 2)); }

APP.get('/api/tasks', (req, res) => { res.json(loadTasks()); });

APP.post('/api/tasks', (req, res) => {
  const { agentId, title, description } = req.body;
  if (!agentId || !title) return res.status(400).json({ ok: false, error: 'agentId and title required' });
  const data = loadTasks();
  const task = {
    id: `task_${Date.now()}`, agentId, agentName: AGENTS[agentId]?.name || agentId,
    title, description: description || '', status: 'pending',
    createdAt: new Date().toISOString(), completedAt: null, artifactLink: null,
  };
  data.tasks.push(task);
  saveTasks(data);

  // Write notification file for Agent DM trigger
  const notifyDir = path.join(BASE, 'data', 'notifications');
  fs.mkdirSync(notifyDir, { recursive: true });
  fs.writeFileSync(path.join(notifyDir, `${task.id}.json`), JSON.stringify({
    type: 'new_task', task,
    message: `📋 Daryl assigned「${title}」to ${task.agentName}. Please DM Daryl on Feishu to clarify before starting.\n${description}`,
  }, null, 2));

  res.json({ ok: true, task });
});

APP.patch('/api/tasks/:id', (req, res) => {
  const data = loadTasks();
  const task = data.tasks.find(t => t.id === req.params.id);
  if (!task) return res.status(404).json({ ok: false });
  if (req.body.status) {
    task.status = req.body.status;
    if (req.body.status === 'done') task.completedAt = new Date().toISOString();
  }
  if (req.body.artifactLink !== undefined) task.artifactLink = req.body.artifactLink;
  saveTasks(data);
  res.json({ ok: true, task });
});

APP.delete('/api/tasks/:id', (req, res) => {
  const data = loadTasks();
  data.tasks = data.tasks.filter(t => t.id !== req.params.id);
  saveTasks(data);
  res.json({ ok: true });
});

// === M2 API: Workflows ===
APP.get('/api/workflows', (req, res) => {
  try {
    const data = JSON.parse(fs.readFileSync(WORKFLOWS_FILE, 'utf8'));
    res.json({ ok: true, workflows: data.workflows || [] });
  } catch(e) { res.json({ ok: false, error: e.message, workflows: [] }); }
});

APP.post('/api/workflows', (req, res) => {
  try {
    const { workflows } = req.body;
    if (!Array.isArray(workflows)) return res.status(400).json({ ok: false, error: 'workflows array required' });
    workflows.forEach(w => { w.updatedAt = new Date().toISOString(); });
    fs.writeFileSync(WORKFLOWS_FILE, JSON.stringify({ workflows }, null, 2));

    // Write sync notification
    fs.writeFileSync(path.join(BASE, 'data', 'notifications', `workflow_sync_${Date.now()}.json`), JSON.stringify({
      type: 'workflow_sync',
      timestamp: new Date().toISOString(),
      workflowNames: workflows.map(w => w.name),
    }, null, 2));

    res.json({ ok: true });
  } catch(e) { res.json({ ok: false, error: e.message }); }
});

// === M2 API: Cost Dashboard ===
// Estimate costs from session data (openclaw status --usage is too slow for dashboard)
let costCache = { data: null, ts: 0, TTL: 120000 }; // 2 min cache

APP.get('/api/costs', async (req, res) => {
  try {
    const now = Date.now();
    if (costCache.data && (now - costCache.ts) < costCache.TTL) {
      return res.json(costCache.data);
    }

    // Collect session stats per agent and model
    let sessions = [];
    const agentSessionPaths = [
      { agent: 'main', path: '/Users/zhaoyuzhao/.openclaw/agents/main/sessions/sessions.json' },
      { agent: 'xiaofeng', path: '/Users/zhaoyuzhao/.openclaw/agents/xiaofeng/sessions/sessions.json' },
      { agent: 'balance', path: '/Users/zhaoyuzhao/.openclaw/agents/balance/sessions/sessions.json' },
      { agent: 'self', path: '/Users/zhaoyuzhao/.openclaw/agents/self/sessions/sessions.json' },
    ];
    const agentSessions = {};
    const modelSessions = {};
    let totalSessions = 0;

    for (const { agent, path: sp } of agentSessionPaths) {
      try {
        if (!fs.existsSync(sp)) continue;
        const raw = fs.readFileSync(sp, 'utf8');
        const data = JSON.parse(raw);
        // sessions.json is a dict keyed by sessionId, each value is a session object
        const sessList = Array.isArray(data) ? data : Object.values(data);
        if (!agentSessions[agent]) agentSessions[agent] = 0;
        agentSessions[agent] += sessList.length;
        totalSessions += sessList.length;
        sessList.forEach(s => {
          if (typeof s !== 'object') return;
          const m = s.model || s.modelProvider || 'unknown';
          modelSessions[m] = (modelSessions[m] || 0) + 1;
        });
      } catch(e) { /* skip */ }
    }

    // Map internal IDs to agent display names
    const idToDisplay = { main: 'kitty', xiaofeng: 'xiaofeng', balance: 'balance', self: 'self' };
    const breakdown = Object.entries(agentSessions).map(([agent, count]) => {
      const displayId = idToDisplay[agent] || agent;
      return {
        agent: displayId,
        name: AGENTS[displayId]?.name || agent,
        sessions: count,
        color: AGENTS[displayId]?.color || '#888',
      };
    }).sort((a, b) => b.sessions - a.sessions);

    const modelBreakdown = Object.entries(modelSessions).map(([model, count]) => ({
      model, sessions: count,
    })).sort((a, b) => b.sessions - a.sessions);

    const costData = {
      ok: true,
      costs: {
        timestamp: new Date().toISOString(),
        source: 'session-files',
        totalSessions,
        agentBreakdown: breakdown,
        modelBreakdown,
        dailyTrend: [],
      }
    };
    costCache = { data: costData, ts: now, TTL: 120000 };
    res.json(costData);
  } catch(e) {
    res.json({ ok: false, error: e.message, costs: null });
  }
});

// === M2 API: Sandbox & Tasks ===
let sbTaskCache = { data: null, ts: 0, TTL: 30000 };

APP.get('/api/sandbox-tasks', async (req, res) => {
  try {
    const now = Date.now();
    if (sbTaskCache.data && (now - sbTaskCache.ts) < sbTaskCache.TTL) {
      return res.json(sbTaskCache.data);
    }

    let sandbox = { containers: [], browsers: [] };
    let tasks = [];
    try {
      const sbRaw = execSync('openclaw sandbox list --json 2>/dev/null', { timeout: 8000, encoding: 'utf8', maxBuffer: 256*1024 });
      sandbox = JSON.parse(sbRaw || '{"containers":[],"browsers":[]}');
    } catch(e) {}
    try {
      const tRaw = execSync('openclaw tasks list --json', { timeout: 8000, encoding: 'utf8', maxBuffer: 512*1024 });
      const tData = JSON.parse(tRaw);
      tasks = (tData.tasks || []).map(t => ({
        taskId: t.taskId, label: t.label, task: t.task, status: t.status, runtime: t.runtime,
        agentId: t.agentId,
        createdAt: t.createdAt, endedAt: t.endedAt,
        summary: (t.terminalSummary || '').substring(0, 80),
      }));
    } catch(e) {}

    const result = { ok: true, sandbox, tasks, timestamp: new Date().toISOString() };
    sbTaskCache = { data: result, ts: now, TTL: 30000 };
    res.json(result);
  } catch(e) {
    res.json({ ok: false, error: e.message });
  }
});

APP.listen(PORT, () => {
  console.log(`🐈‍⬛ OPC Dashboard v2.2 (M2) → http://localhost:${PORT}`);
});
