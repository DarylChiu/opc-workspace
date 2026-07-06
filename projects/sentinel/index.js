// Sentinel · P0-P3 合规哨兵
// System-level enforcement of the P0-P3 decision matrix via before_tool_call hook

import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// ─── Constants ───────────────────────────────────────────────
const PLUGIN_ID = "sentinel";
const DANGEROUS_EXEC_PATTERNS = [
  { pattern: /rm\s+-rf\s+\//i, level: "P0", reason: "rm -rf / detected" },
  { pattern: /rm\s+-rf\s+\*/i, level: "P0", reason: "recursive force delete" },
  { pattern: /git\s+push\s+.*--force/i, level: "P0", reason: "force push to remote", approval: true },
  { pattern: /npm\s+publish/i, level: "P0", reason: "npm publish" },
  { pattern: /docker\s+(rm|prune|system\s+prune)/i, level: "P1", reason: "docker cleanup" },
  { pattern: /git\s+push\s+origin\s+(main|master)/i, level: "P0", reason: "push to main/master", approval: true },
  { pattern: />\s*\/dev\/(sd|nvme|disk)/i, level: "P0", reason: "raw disk write" },
  { pattern: /chmod\s+777/i, level: "P1", reason: "overly permissive chmod" },
  { pattern: /DROP\s+(TABLE|DATABASE)/i, level: "P0", reason: "SQL DROP statement" },
];

// ─── Glob matcher ─────────────────────────────────────────────
function globMatch(pattern, str) {
  const regex = new RegExp(
    "^" + pattern
      .replace(/\./g, "\\.")
      .replace(/\*\*/g, "§§DOUBLESTAR§§")
      .replace(/\*/g, "[^/]*")
      .replace(/§§DOUBLESTAR§§/g, ".*")
      + "$"
  );
  return regex.test(str);
}

function matchesAnyPattern(patterns, filePath) {
  for (const p of patterns) {
    if (globMatch(p, filePath)) return true;
  }
  return false;
}

// ─── Path extraction from tool params ─────────────────────────
function extractPaths(toolName, params) {
  const paths = [];
  if (params.path) paths.push(String(params.path));
  if (params.filePath) paths.push(String(params.filePath));
  if (params.file_path) paths.push(String(params.file_path));
  if (params.target) paths.push(String(params.target));
  if (params.dest) paths.push(String(params.dest));
  if (params.destination) paths.push(String(params.destination));
  // For edit tool: params.path is the file being edited
  return paths.filter(p => p && p !== "undefined");
}

// ─── Per-session state ────────────────────────────────────────
const sessionState = new Map(); // sessionKey → { writeCount, execCount, dirs, preopLevel, preopDone }

function getState(sessionKey) {
  if (!sessionState.has(sessionKey)) {
    sessionState.set(sessionKey, {
      writeCount: 0,
      execCount: 0,
      dirs: new Set(),
      preopLevel: null,
      preopDone: false,
      p1Count: 0,
      lastP1Time: 0,
    });
  }
  return sessionState.get(sessionKey);
}

// ─── Level helpers ────────────────────────────────────────────
const LEVEL_ORDER = { P0: 0, P1: 1, P2: 2, P3: 3 };
function isHigherLevel(a, b) {
  return LEVEL_ORDER[a] < LEVEL_ORDER[b];
}

function isNightTime(now, config) {
  const hour = now.getHours();
  const start = config?.nightDowngradeStart ?? 23;
  const end = config?.nightDowngradeEnd ?? 8;
  if (start > end) {
    // e.g. 23:00 - 08:00
    return hour >= start || hour < end;
  }
  return hour >= start && hour < end;
}

// ─── Audit log ────────────────────────────────────────────────
function writeAudit(config, entry) {
  try {
    const dir = config?.auditDir || "memory";
    const fpath = path.resolve(process.env.OPENCLAW_WORKSPACE || ".", dir, "sentinel-audit.jsonl");
    const parent = path.dirname(fpath);
    if (!fs.existsSync(parent)) fs.mkdirSync(parent, { recursive: true });
    fs.appendFileSync(fpath, JSON.stringify(entry) + "\n");
  } catch (e) {
    console.error("[sentinel] audit write failed:", e.message);
  }
}

// ─── Main hook handler ────────────────────────────────────────
async function onBeforeToolCall(event, ctx) {
  const config = ctx.pluginConfig || {};
  if (config.enabled === false) return;

  const agentId = ctx.agentId || "unknown";
  const sessionKey = ctx.sessionKey || "unknown";

  // Skip if targetAgents configured and this agent not in list
  if (config.targetAgents?.length > 0 && !config.targetAgents.includes(agentId)) {
    return;
  }

  const state = getState(sessionKey);
  const toolName = event.toolName;
  const params = event.params || {};

  // ── Track cumulative counts ──────────────────────────────────
  if (toolName === "write" || toolName === "edit") {
    state.writeCount++;
    const paths = extractPaths(toolName, params);
    for (const p of paths) {
      // Extract top-level directory
      const relative = p.replace(/^\/.*?xiaofeng_workspace\//, "").replace(/^\/.*?openclaw\//, "");
      const topDir = relative.split("/")[0];
      if (topDir && topDir !== "." && topDir !== "..") state.dirs.add(topDir);
    }
  }
  if (toolName === "exec") {
    state.execCount++;
  }

  // ── Check for pre-op completion ──────────────────────────────
  // If write/edit count > 3 and no pre-op done, require approval
  if (state.writeCount > 3 && !state.preopDone) {
    const entry = {
      timestamp: new Date().toISOString(),
      agentId,
      sessionKey,
      toolName,
      level: "P1",
      decision: "REQUIRE_APPROVAL",
      reason: "Session has >3 write/edit calls without pre-op classification",
      action: "requireApproval",
    };
    writeAudit(config, entry);

    const result = {
      block: false,
      requireApproval: {
        title: "⚠️ 缺少 pre-op 合规判定",
        description: `本 session 已执行 ${state.writeCount} 次写操作但尚未运行 pre-op.sh 分类。请先完成 P0-P3 分级判定后再继续操作。`,
        severity: "warning",
        timeoutMs: (config.p1TimeoutMinutes || 30) * 60 * 1000,
        timeoutBehavior: isNightTime(new Date(), config) ? "allow" : "deny",
      },
    };
    state.preopLevel = "P1"; // Treat missing pre-op as P1
    return result;
  }

  // ── P0: Check path blacklist ────────────────────────────────
  const p0Paths = config.p0Paths || [".env", ".env.*", "*.secret"];
  if (toolName === "write" || toolName === "edit") {
    const filePaths = extractPaths(toolName, params);
    for (const fp of filePaths) {
      const basename = fp.split("/").pop();
      if (matchesAnyPattern(p0Paths, basename) || matchesAnyPattern(p0Paths, fp)) {
        return handleP0Block("P0 路径匹配: " + fp, config, agentId, sessionKey, toolName);
      }
    }
  }

  // ── P0: Check exec for dangerous patterns ────────────────────
  if (toolName === "exec") {
    const cmd = String(params.command || "");
    for (const dp of DANGEROUS_EXEC_PATTERNS) {
      if (dp.pattern.test(cmd)) {
        if (dp.level === "P0") {
          if (dp.approval) {
            return handleP1Approval("P0 命令: " + dp.reason, cmd.slice(0, 80), config, state);
          }
          return handleP0Block("P0 命令模式: " + dp.reason + " → " + cmd.slice(0, 80), config, agentId, sessionKey, toolName);
        }
        if (dp.level === "P1") {
          state.p1Count++;
          return handleP1Approval("P1 命令模式: " + dp.reason, cmd.slice(0, 80), config, state);
        }
      }
    }
  }

  // ── P1: Check path sensitivity ───────────────────────────────
  const p1Paths = config.p1Paths || [
    "package.json", "requirements.txt", "go.mod",
    "**/types/*", "**/api/*", "**/interface*",
    "**/schema*", "**/migrations/*"
  ];
  if (toolName === "write" || toolName === "edit") {
    const filePaths = extractPaths(toolName, params);
    for (const fp of filePaths) {
      if (matchesAnyPattern(p1Paths, fp) || matchesAnyPattern(p1Paths, fp.split("/").pop())) {
        state.p1Count++;
        return handleP1Approval("P1 敏感路径: " + fp, fp, config, state);
      }
    }
  }

  // ── Cumulative threshold checks ──────────────────────────────
  const writeThreshold = config.writeThreshold || 20;
  const dirThreshold = config.dirThreshold || 3;

  if (state.writeCount >= writeThreshold) {
    state.p1Count++;
    return handleP1Approval(
      `累计写操作 ${state.writeCount} 次 (阈值 ${writeThreshold})`,
      `write 计数: ${state.writeCount}`,
      config, state
    );
  }

  if (state.dirs.size >= dirThreshold) {
    state.p1Count++;
    return handleP1Approval(
      `涉及 ${state.dirs.size} 个目录 (阈值 ${dirThreshold}): ${[...state.dirs].join(", ")}`,
      `目录数: ${state.dirs.size}`,
      config, state
    );
  }

  // ── Exec threshold warning (non-blocking) ────────────────────
  const execThreshold = config.execThreshold || 15;
  if (state.execCount >= execThreshold) {
    writeAudit(config, {
      timestamp: new Date().toISOString(),
      agentId,
      sessionKey,
      toolName,
      level: "P2",
      decision: "WARN",
      reason: `累计 exec ${state.execCount} 次 (阈值 ${execThreshold})`,
    });
  }

  // ── All clear ────────────────────────────────────────────────
  writeAudit(config, {
    timestamp: new Date().toISOString(),
    agentId,
    sessionKey,
    toolName,
    level: state.preopLevel || "P2",
    decision: "PASS",
    writeCount: state.writeCount,
    execCount: state.execCount,
    dirs: [...state.dirs],
  });

  return; // No intervention needed
}

// ── P0 block handler ──────────────────────────────────────────
function handleP0Block(reason, config, agentId, sessionKey, toolName) {
  writeAudit(config, {
    timestamp: new Date().toISOString(),
    agentId,
    sessionKey,
    toolName,
    level: "P0",
    decision: "BLOCK",
    reason,
  });

  return {
    block: true,
    blockReason: `[Sentinel P0 BLOCK] ${reason}`,
  };
}

// ── P1 approval handler ────────────────────────────────────────
function handleP1Approval(title, detail, config, state) {
  const isNight = isNightTime(new Date(), config);
  const timeoutMs = (config.p1TimeoutMinutes || 30) * 60 * 1000;

  if (isNight) {
    // Night mode: auto-downgrade to P2
    writeAudit(config, {
      timestamp: new Date().toISOString(),
      level: "P1",
      decision: "NIGHT_DOWNGRADE_P2",
      reason: title,
    });
    return; // Allow through
  }

  return {
    block: false,
    requireApproval: {
      title: `[Sentinel P1] ${title}`,
      description: `详情: ${detail}\n超时 ${config.p1TimeoutMinutes || 30} 分钟后自动降级为 P2 放行。`,
      severity: "warning",
      timeoutMs,
      timeoutBehavior: "allow",
    },
  };
}

// ── Session cleanup on end ─────────────────────────────────────
function onSessionEnd(event) {
  const sk = event.sessionKey;
  if (sk && sessionState.has(sk)) {
    sessionState.delete(sk);
  }
}

// ── Plugin entry ──────────────────────────────────────────────
export default definePluginEntry({
  id: PLUGIN_ID,
  name: "Sentinel · P0-P3 合规哨兵",
  description: "System-level P0-P3 decision matrix enforcement via before_tool_call hook",
  register(api) {
    api.on("before_tool_call", onBeforeToolCall, { priority: 100 });
    api.on("session_end", onSessionEnd);

    console.log("[sentinel] ✅ P0-P3 compliance sentinel active");
  },
});
