---
name: handoff
description: Manages context transfer between AI coding sessions. Creates a compact handoff document so a fresh agent can continue work. Use when user says "handoff", "hand off", "resume", "continue later", "pick up where we left off", "transfer context", or when wrapping up a significant session.
argument-hint: "What will the next session be used for?"
---

# Handoff

Transfer context to a fresh session via a compact handoff file. Invoke this skill when the user wants to pause, resume, or pass work to another session.

## Modes

| Invocation | What it does |
|---|---|
| `/handoff` | Full handoff — context, decisions, dead ends, next steps |
| `/handoff quick` | Minimal — one-line goal, suggested skills, 3-5 next steps |
| `/handoff resume` | Continue from an existing handoff file |

If arguments describe the next session's focus, tailor "Next Steps" and "Suggested skills" to it.

## Creating a Handoff

Save to the workspace or a designated handoff location. The SessionStart hook auto-detects handoff files, so keep the `handoff-` prefix.

### Full document

```markdown
<!-- HIGHLY SENSITIVE. Do not share this file. -->
# Handoff — [One-line Goal]

> **Suggested skills**: [skill-1], [skill-2], ...

## What We're Building
[1-3 bullets max. Reference artifacts by path/URL — do not duplicate.]

## Progress
- [x] Done item
- [ ] In-progress item (blocked by X)

## What Worked / Avoid
- ✓ Approach A worked
- ✗ Approach B failed — reason (don't retry)

## Key Decisions
- Chose X over Y because ...

## References
- Docs: `docs/prd.md`, `docs/adr/001-choice.md`
- Commits: `abc1234`, `def5678`

## Next Steps
1. [P0] Critical action item
2. [P1] Important follow-up
3. [P2] Nice to have
```

**Keep it lean** — the next session reads this back, so every line costs tokens twice (to write, then to re-read):
- Bullets only, no prose. Hard cap ~5 bullets per section; delete any section that would be empty.
- Pointers over content: link commits, diffs, PRDs — never paste their contents.

**Quick mode**: keep only the goal, suggested skills, and 3-5 next steps.

## Resume Flow

Triggered when the user confirms a resume — either after the SessionStart hook reports a handoff, or via `/handoff resume`:

1. Read the handoff file.
2. Load any skills listed under "Suggested skills".
3. Summarize state (goal + progress) for the user.
4. Start from the highest-priority "Next Steps" item.
5. Append updates as work progresses (check off items, add new ones) — don't rewrite the whole file.

## Rules

- **Redact** all secrets (API keys, passwords, tokens) and PII before writing.
- Save to the workspace or OS temp dir — use a consistent location.
- First line of every handoff: `<!-- HIGHLY SENSITIVE. Do not share this file. -->`
- Reference existing artifacts (PRDs, ADRs, issues, commits, diffs) by path/URL — never duplicate their content.

## When to Suggest

Proactively offer a handoff when the user says "I need to go" / "let's wrap up", at a milestone, or when the conversation has grown long and context-heavy:

> "Want me to create a handoff so another session can pick this up?"
