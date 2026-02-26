---
name: supervisor-review-loop
description: Supervisor workflow for dependency-aware implementation with coding-agent + ephemeral-review-agent loops, staged parallel waves, and strict critical-only review gating. Use for multi-task feature delivery from spec/tasks with max-agent constraints.
---

# Supervisor Review Loop

Use this skill when you need to implement a spec with multiple dependent tasks and want high-confidence execution through repeated critical review.

## When to Use

- You have `spec.md` + `tasks.md` from spec-kit and need execution (not just planning).
- Work has a clear dependency graph (critical path + parallelizable tasks).
- You must run several agents but keep strict quality control.
- You have an open-agent cap (for example 6) and must recycle reviewers.

## Core Model

Run **coding agents** for implementation and **ephemeral reviewer agents** for critical-only validation.

- Coding agent owns files/tasks in a stream.
- Reviewer agent is fresh each cycle, reports only blockers.
- Close reviewer agent after each review result.
- If blockers exist: send to coder, patch, spawn new fresh reviewer.
- Stop a stream only when reviewer says exactly: `No critical comments.`

## Non-Negotiable Guardrails

- Keep scope to active spec/tasks; do not pull deferred hardening.
- Demand DRY/KISS and architecture consistency.
- Reviewers must avoid nits/frivolous items.
- Require concrete file-level evidence for blockers.
- If a reviewer overreaches scope, require coder rebuttal with spec/task citations.
- For DAO/repo persistence-shape changes, require matching migration + schema snapshot parity before calling stream done.
- Do not mark a task complete until its stream exits review with `No critical comments.`.

## Execution Protocol

1. **Preflight**
   - Read `spec.md`, `tasks.md`, relevant contracts.
   - Build dependency groups: critical path first, then parallel waves.
   - Reserve one agent slot for reviewer churn.

2. **Critical Path First**
   - Spawn one coding agent for critical sequential tasks.
   - After completion, start review loop (fresh reviewer each pass).
   - Iterate coder<->review until no critical comments.

3. **Parallel Waves**
   - Spawn multiple coding agents for independent streams (respect ownership boundaries).
   - For each stream, run its own ephemeral review loop to green.
   - Do not let overlapping streams edit the same hot files unless intentionally serialized.

4. **Cross-Stream Final Pass**
   - Spawn one final reviewer over all completed streams.
   - If blockers appear, route to smallest responsible stream and rerun review.
   - Explicitly include deployability checks (schema/DAO parity, migration presence, payload contract parity).

5. **Validation**
   - Run focused tests first, then broader touched-package tests.
   - Report unrelated pre-existing failures separately.

## Agent Prompt Templates

### Coding Agent

Include:
- attach `$coder` (or `UserInput::Skill` -> `~/.codex/skills/coder/SKILL.md`)
- task IDs owned
- allowed file paths
- spec/contract paths
- “spec-only, no deferred scope”
- “you are not alone in codebase; ignore unrelated edits”
- required test commands and output

### Reviewer Agent

Include:
- attach `$reviewer` (or `UserInput::Skill` -> `~/.codex/skills/reviewer/SKILL.md`)
- exact scope files
- exact task IDs under review
- instruction: “critical/blocking only, no nits”
- instruction: “ignore deferred tasks/specs”
- success sentinel: `No critical comments.`

## Supervisor State Discipline

- Keep plan statuses current (`in_progress` exactly one step).
- Never exceed agent cap.
- Close reviewers immediately after each verdict.
- Reuse coder only for its stream unless explicit pivot.
- Track completed task IDs in `tasks.md` and verify checkboxes.
- When review reopens a stream, revert task status mentally to in-progress until the fresh reviewer returns `No critical comments.`.

## Recommended Streaming Order

- Stream 0: critical path (API contract + state machine + orchestration glue)
- Stream 1+: independent implementation slices
- Final: integration review + targeted validation

## Output Contract to User

Always report:
- completed task IDs
- files changed by stream
- blocker/fix cycles count
- current unresolved tasks
- tests run + pass/fail summary
- any known unrelated failures
