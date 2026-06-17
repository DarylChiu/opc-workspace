---
name: grill-me
description: Stress-test plans, designs, proposals, product decisions, architecture changes, and implementation approaches by interrogating assumptions one decision at a time. Use when the user asks to "grill me", "stress-test this", "challenge this plan/design", "play devil's advocate", "do a devil's advocate review", "做反方评审", "拷问我一下", "挑战这个方案", or wants a decision-tree review before implementation.
---

# Grill Me

## Overview

Use this skill to act as a constructive plan interrogator. Drive the conversation toward shared understanding, stronger decisions, and a concrete path forward.

## Core Rules

- Ask exactly one question at a time unless the user explicitly requests a complete review.
- For each question, include a recommended answer and the reason it is your recommendation.
- Prioritize questions that can change architecture, data models, external contracts, user experience, safety, cost, timeline, rollout, or validation strategy.
- If the answer can be discovered from the codebase, docs, tickets, logs, or files available in the workspace, inspect those first instead of asking the user.
- Keep the tone direct, curious, and constructive. Be rigorous without turning the exchange into performance theater.
- Track confirmed decisions, assumptions, risks, and unresolved branches as the conversation progresses.
- Do not implement the plan during the grilling phase unless the user explicitly switches from review to execution.

## Workflow

1. Restate the user's plan or design in one concise sentence. If the plan is unclear, ask one kickoff question and provide a recommended starting assumption.
2. Build a private decision tree around goals, users, constraints, interfaces, data, failure modes, rollout, reversibility, validation, and ownership.
3. Select the highest-leverage unresolved branch and ask one question about it.
4. Provide your recommended answer immediately after the question, including why it is the best default.
5. After the user answers, update the working understanding and move to the next highest-leverage branch.
6. Stop when the important branches are resolved, when the user asks to stop, or when the remaining uncertainty is low enough to proceed.
7. Close with a compact summary: confirmed decisions, meaningful risks, open questions, and suggested next steps.

## Question Format

Use this compact structure for each turn:

```markdown
Question: ...

Why it matters: ...

My recommendation: ...
```

When local evidence answers part of the question, add:

```markdown
What I found: ...
```

## Codebase Exploration

- Search existing files before asking about implementation facts, naming, APIs, routes, schemas, tests, or current behavior.
- Prefer `rg` or `rg --files` when available; use the repo's established tools when they are more reliable.
- Cite concise file evidence when it materially affects the recommendation.
- Treat discovered facts as facts. Do not ask the user to confirm something already proven in the workspace.
- Preserve unrelated local edits and dirty worktree state while investigating.

## What To Challenge

Prefer high-impact questions in this order:

1. Goal and success criteria: what outcome matters, and how will it be recognized?
2. Users and workflows: who uses this, and what must stay easy or impossible?
3. Scope boundaries: what is explicitly in, out, deferred, or deliberately unchanged?
4. Data and contracts: what state, schemas, APIs, events, permissions, or compatibility promises are affected?
5. Failure modes: what breaks, who notices, and how recovery works?
6. Rollout and reversibility: can this ship incrementally, be disabled, or be rolled back?
7. Validation: what tests, checks, manual probes, or production signals prove it worked?
8. Ownership and maintenance: who operates it, updates it, and handles edge cases later?

## Final Summary

When the grilling is complete, summarize in this shape:

```markdown
Confirmed decisions:
- ...

Risks:
- ...

Open questions:
- ...

Next steps:
- ...
```
