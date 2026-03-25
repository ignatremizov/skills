---
name: supervisor-review-loop
description: Supervisor workflow for dependency-aware Spec-Kit implementation using coder+reviewer loops, staged parallel waves, and strict critical-only review gating. Use after spec/tasks exist and implementation needs multi-stream supervision rather than a single direct executor.
---

# Supervisor Review Loop

Use this skill when you need to implement a spec with multiple dependent tasks and want high-confidence execution through repeated critical review.

This skill is for the **implementation supervision** stage only.

- Use `spec-kit-skill` for phase detection and phase-to-phase orchestration.
- Pass `spec-kit-implement-skill` when one agent can execute `tasks.md` directly without a supervised multi-stream loop.
- Use `ghc-review-supervisor` skill for `ghc`-driven PR review resolution.
- Do not spawn a separate `supervisor_review_loop` agent. That role exists mainly for explicit supervisor-of-supervisors experiments.

## When to Use

- You have `spec.md` + `tasks.md` and need execution, not planning.
- Work has a clear dependency graph: critical path plus parallelizable streams.
- You need several agents but still want strict quality control.
- You need a fresh reviewer after each coding pass.
- You have an open-agent cap and must recycle reviewers.

## Core Model

Run **coding agents** for implementation and **ephemeral reviewer agents** for critical-only validation.

- Coding agent owns one implementation stream.
- Reviewer agent is fresh each cycle and reports only blockers.
- Close reviewer agent after each review result.
- If blockers exist: send them back to the owning coder, patch, and spawn a new reviewer.
- Stop a stream only when reviewer says exactly: `No critical comments.`

Default worker selection:

- Prefer `coder_spec` for normal task-owned Spec-Kit implementation streams.
- The harness supports per-spawn `model` and `reasoning_effort` overrides, prefer keeping the domain role aligned to the task and overriding those controls directly instead of generic coder presets such as `coder` or `coder_xhigh`, unless explicitly needed where work is not spec-based or out-of-spec.

## Non-Negotiable Guardrails

- Keep scope to active `spec.md`, `tasks.md`, and active contracts only.
- Do not pull deferred hardening or future-phase scope into the stream.
- Demand DRY/KISS and architecture consistency.
- Always spawn delegated agents with `fork_context=false`.
- Reviewers must avoid nits and optional refactors.
- Require concrete file-level evidence for blockers.
- If a reviewer overreaches scope, require rebuttal with task/spec citations.
- For DAO or persistence-shape changes, require matching migration plus schema snapshot parity before calling a stream done.
- Do not mark a task complete until its owning reviewer exits with `No critical comments.`

## Execution Protocol

1. **Preflight**
   - Read `spec.md`, `tasks.md`, `plan.md`, and relevant contracts.
   - Build dependency groups: critical path first, then parallel waves.
   - Reserve one agent slot for reviewer churn.
2. **Critical Path First**
   - Spawn one coding agent for critical sequential tasks.
   - After completion, start the review loop with a fresh reviewer.
   - Iterate coder-to-reviewer until no critical comments remain.
3. **Parallel Waves**
   - Spawn multiple coding agents for independent streams with disjoint ownership.
   - Run a separate ephemeral review loop for each stream.
   - Do not let overlapping streams edit the same hot files unless intentionally serialized.
4. **Cross-Stream Final Pass**
   - Spawn one final reviewer over all completed streams.
   - If blockers appear, route them to the smallest responsible stream and rerun review.
   - Explicitly include deployability checks such as schema/DAO parity, migration presence, and payload contract parity.
5. **Validation**
   - Run focused tests first, then broader touched-package tests.
   - Report unrelated pre-existing failures separately.

## Agent Prompt Templates

### Coding Agent

Include:

- `agent_type`: usually `coder_spec`, with `model` / `reasoning_effort` overrides as needed
- if needed, use `coder` or `coder_xhigh` for non-spec-based work
- `fork_context=false`
- owned task IDs
- allowed file paths
- spec/contract paths
- `plan.md` path when available
- the instruction: `spec-only, no deferred scope`
- the instruction: `you are not alone in codebase; ignore unrelated edits`
- required test commands and expected output format
- optional one-off transient instructions only when the base role prompt is insufficient

### Reviewer Agent

Include:

- `agent_type`: `reviewer`
- `fork_context=false`
- exact scope files
- exact task IDs under review
- the instruction: `critical/blocking only, no nits`
- the instruction: `ignore deferred tasks/specs`
- success sentinel: `No critical comments.`

## Supervisor State Discipline

- Keep plan statuses current with exactly one step `in_progress`.
- Never exceed the active agent cap.
- Close reviewers immediately after each verdict.
- Reuse a coder only for its owned stream unless you intentionally re-scope it.
- Track completed task IDs in `tasks.md` and verify checkboxes.
- When review reopens a stream, treat its tasks as in-progress again until a fresh reviewer returns `No critical comments.`

## Recommended Streaming Order

- Stream 0: critical path, usually API contract, state machine, or orchestration glue
- Stream 1+: independent implementation slices
- Final: integration review plus targeted validation

## Output Contract to User

Always report:

- completed task IDs
- files changed by stream
- blocker/fix cycle count
- current unresolved tasks
- tests run plus pass/fail summary
- any known unrelated failures
