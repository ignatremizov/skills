---
name: supervisor-review-loop
description: Supervisor workflow for dependency-aware Spec-Kit implementation using coder+reviewer loops, staged parallel waves, and fresh prioritized reviewer passes. Use after spec/tasks exist and implementation needs multi-stream supervision rather than a single direct executor.
---

# Supervisor Review Loop

Use this skill when you need to implement a spec with multiple dependent tasks and want high-confidence execution through repeated critical review.

This skill is for the **implementation supervision** stage only.

- Use `spec-kit-skill` for phase detection and phase-to-phase orchestration.
- Pass `spec-kit-implement-skill` when one agent can execute `tasks.md` directly without a supervised multi-stream loop.
- Use `ghc-review-supervisor` skill for `ghc`-driven PR review resolution.
- Use this skill by promoting the current Codex session into the supervisor via `$supervisor-review-loop`.
- Do not spawn a separate `supervisor_review_loop` agent for normal use. That role exists mainly for explicit supervisor-of-supervisors experiments and is still experimental.

## Optional Hooks

You can pair this supervisor loop with the `supervisor-review-loop` Codex hook set.

The hook bundle is meant to:

- inject implementation review-loop context on session start
- block completion while any stream still needs a fresh post-fix reviewer pass

If you want to manage that hook bundle, use `$codex-hooks` and select the `supervisor-review-loop` hook set.

### Hook Setup and Use

Use hooks only for the supervisor session, not for spawned coders or reviewers.

1. Identify the target worktree root for this supervised stream.
   - example: `WORKTREE_ROOT=/path/to/target-worktree`
2. Install the `supervisor-review-loop` hook bundle in that worktree before starting or resuming the supervisor session.
   - `~/code/skills/codex/scripts/install-codex-hooks.sh --hook-set supervisor-review-loop --root "$WORKTREE_ROOT"`
3. Start or resume the supervisor session in that worktree so the hook registration is loaded.
4. Write session state for that supervisor session with:
   - `python3 ~/code/skills/codex/scripts/write-flow-state.py --root "$WORKTREE_ROOT" --transcript-path "$TRANSCRIPT_PATH" --mode supervisor-review-loop ...`
5. Update that state whenever a stream enters or exits review-loop closure:
   - add a `--pending-review <stream-id>` entry when a coder changes a stream after review or when a stream still needs its first fresh reviewer pass
   - persist exact must-close findings, deferred findings, and ignored-finding rationales so resume context preserves the real blocker and triage details
   - clear recorded must-close findings with `--clear-must-close-findings` only after they are fixed or explicitly resolved and a fresh reviewer has checked the latest patch set
   - clear the stored list with `--clear-pending-reviews` only after every pending stream has a fresh reviewer pass and its must-fix-now findings are closed
6. Do not write supervisor-review-loop hook state from child coder or reviewer sessions. The installed hooks can exist in the same worktree, but only the supervisor session should have matching per-session state.

## When to Use

- You have `spec.md` + `tasks.md` and need execution, not planning.
- Work has a clear dependency graph: critical path plus parallelizable streams.
- You need several agents but still want strict quality control.
- You need a fresh reviewer after each coding pass.
- You have an open-agent cap and must recycle reviewers.

## Core Model

Run **coding agents** for implementation and **ephemeral reviewer agents** for scoped `P0`-`P3` validation.

- Coding agent owns one implementation stream.
- Use `reviewer_check` as the routine per-task and per-stream consistency gate before advancing to the next task or dependency wave.
- Reviewer agent is fresh each cycle and reports prioritized findings.
- Close reviewer agent after each review result.
- Triage reviewer findings against the active tasks, spec, contracts, and what the stream changed.
- Classify reviewer findings into `must_close_now` versus recorded/deferred follow-up, with introduced defects as the default reopen signal.
- If a finding is a bug, regression, or contract gap introduced by the stream: send it back to the owning coder, patch, and spawn a new reviewer even when it falls outside the original task slice.
- If a finding is clearly pre-existing, unrelated to the stream's changes, or unsupported by file-level evidence: record the rationale and do not reopen the stream for it.
- Record non-blocking reviewer findings explicitly instead of silently ignoring them, but do not reopen the stream unless they truly must be fixed now.
- Be alert for real drift, duplication, or architecture/refactor concerns surfaced by review; decide explicitly whether they reflect a concrete current risk or should be recorded as deferred follow-up work.
- When sending findings back to a coder, preserve the reviewer’s exact file, line, priority, triggering scenario, and violated invariant.
- Prefer forwarding the reviewer finding verbatim or as a tightly structured restatement; do not merge multiple findings into a vague supervisor summary.
- Make the handoff explicit about which findings are must-fix now, which files are in scope for the fix, and what tests or validation must rerun before the next review pass.
- Reopen the stream whenever a reviewer reports an introduced defect.
- Use supervisor judgment only for non-introduced findings that may or may not need fixing now.
- After any fix round triggered by reviewer findings, require a fresh reviewer pass on the updated stream before concluding it.
- Conclude a stream only after every introduced defect is handled, any other must-fix-now findings are handled, a fresh post-fix reviewer pass has checked the latest patch set, and required validation is complete.
- If a concurrent coder change makes an active review snapshot stale, interrupt the reviewer and ask it to stop and report only findings or investigation conclusions already established against the old snapshot before closing it. Record that output as historical evidence; never use it in place of the required fresh post-change review.
- If you use the hook bundle, keep the pending review-loop state accurate so the stop gate reflects which streams still need fresh reviewer closure.

Default worker selection:

- Prefer `coder_spec` for normal task-owned Spec-Kit implementation streams.
- The harness supports per-spawn `model` and `reasoning_effort` overrides, prefer keeping the domain role aligned to the task and overriding those controls directly instead of generic coder presets such as `coder` or `coder_xhigh`, unless explicitly needed where work is not spec-based or out-of-spec.
- Prefer `reviewer_check` for routine task and stream gates.
- Use the default `reviewer` for larger gates within the spec-task checklist, including dependency-wave boundaries, milestones spanning several related tasks, high-risk or cross-cutting tasks, ambiguous behavior, and streams that have already needed a non-trivial fix cycle.
- Do not use `reviewer_exhaustive` unless the user explicitly requests an exhaustive review.

## Non-Negotiable Guardrails

- Keep scope to active `spec.md`, `tasks.md`, and active contracts only.
- Do not pull deferred hardening or future-phase scope into the stream.
- Demand DRY/KISS and architecture consistency.
- Spawn delegated agents without parent context: use `fork_context=false` when the active `spawn_agent` schema is multi-agent V1, or `fork_turns="none"` when it is V2.
- Reviewers must avoid nits and optional refactors.
- Require concrete file-level evidence for findings.
- For race/TOCTOU findings, require the reviewer to name the concrete competing writer, prove its mutation is allowed from the relevant state, and map a reachable interleaving where the conflicting operations lack a shared serialization boundary. For TOCTOU, transactions need not overlap: the writer may commit after the check and before the stale result is used. A timing window without this concrete path is not sufficient evidence.
- Reject race findings based only on process-restart environment flags, deployment-owned operationally immutable configuration, backend-forbidden transitions, or hypothetical direct database writes unless the active contract exposes a reachable mutation path.
- Prefer documenting and testing the invariant at the owning mutation/deployment boundary over adding duplicate downstream rereads, locks, snapshots, or fences.
- If a reviewer overreaches scope, require rebuttal with task/spec citations.
- Treat defects introduced by the stream as in-scope for review closure even when they extend beyond the original task slice.
- For DAO or persistence-shape changes, require matching migration plus schema snapshot parity before calling a stream done.
- Do not mark a task complete until its owning reviewer pass has been considered, any must-fix-now findings for that stream are handled, and a fresh reviewer has checked the latest patch set after the last fix round.

## Execution Protocol

1. **Preflight**
   - Read `spec.md`, `tasks.md`, `plan.md`, and relevant contracts.
   - Build dependency groups: critical path first, then parallel waves.
   - Reserve one agent slot for reviewer churn.
2. **Critical Path First**
   - Spawn one coding agent for critical sequential tasks.
   - After completion, start the review loop with a fresh reviewer.
   - Iterate coder-to-reviewer while the latest reviewer pass still surfaces findings the supervisor judges must be fixed now in that stream.
   - When sending review feedback back to the coder, include the exact reviewer finding or a structured restatement with `P` level, `file:line`, scenario, required invariant, and focused validation to rerun.
   - Every time the coder changes the stream to address reviewer findings, rerun a fresh reviewer on the updated patch set before treating the stream as complete.
   - When a concurrent coder invalidates an active review, interrupt that reviewer first and collect only its already-established findings as explicitly historical evidence; then close it and spawn a fresh reviewer on the updated patch.
3. **Parallel Waves**
   - Spawn multiple coding agents for independent streams with disjoint ownership.
   - Run a separate ephemeral review loop for each stream.
   - Do not let overlapping streams edit the same hot files unless intentionally serialized.
4. **Cross-Stream Final Pass**
   - Spawn the default `reviewer` over all completed streams.
   - Do not add `reviewer_exhaustive` unless the user explicitly requests an exhaustive review.
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
- no-context fork option for the active schema: `fork_context=false` for multi-agent V1 or `fork_turns="none"` for V2
- owned task IDs
- allowed file paths
- spec/contract paths
- `plan.md` path when available
- work-specific instructions only when needed beyond the role defaults
- example work-specific instructions:
- `spec-only, no deferred scope`
- `you are not alone in codebase; ignore unrelated edits`
- required test commands and expected output format
- optional one-off work-specific instructions only when the base role prompt is insufficient

### Reviewer Agent

Include:

- `agent_type`: `reviewer_check` for routine task and stream gates
- use `reviewer` instead for larger checklist gates, dependency-wave or multi-task milestones, high-risk or cross-cutting tasks, ambiguous behavior, or streams that have already needed a non-trivial fix cycle
- no-context fork option for the active schema: `fork_context=false` for multi-agent V1 or `fork_turns="none"` for V2
- exact scope files
- exact task IDs under review
- work-specific review scope and constraints only
- example work-specific instructions:
- `focus on the active task slice, but still report any bug, regression, or contract gap introduced by the stream in the touched scope even when it extends beyond the original task IDs`
- `do not pull in unrelated deferred tasks/specs`

### User-Requested Exhaustive Reviewer Agent

Include:

- `agent_type`: `reviewer_exhaustive`
- use it only when the user explicitly requests an exhaustive review
- keep the same scope files and ownership boundaries as the normal reviewer

## Example RPC Flow

Use the RPC calls as the control plane, not as a license to paraphrase away reviewer context.

Example:

```text
spawn_agent({
  agent_type: "coder_spec",
  # Multi-agent V1: use fork_context: false.
  # Multi-agent V2: replace it with fork_turns: "none".
  fork_context: false,
  message: "
  Owned task IDs: T12, T13
  Allowed files:
  - internal/profile/service.go
  - internal/profile/repository.go
  Spec/contract paths:
  - specs/foo/spec.md
  - specs/foo/tasks.md
  Work-specific instructions for this stream:
  - spec-only, no deferred scope
  Required tests:
  - env GOWORK=off go test ./internal/profile
  "
})

wait_agent({
  targets: [coder_stream],
  timeout_ms: 600000
})

spawn_agent({
  agent_type: "reviewer_check",
  # Multi-agent V1: use fork_context: false.
  # Multi-agent V2: replace it with fork_turns: "none".
  fork_context: false,
  message: "
  Scope files:
  - internal/profile/service.go
  - internal/profile/repository.go
  Task IDs under review: T12, T13
  Work-specific review constraints:
  - focus on the active task slice, but still report any bug, regression, or contract gap introduced by the stream in the touched scope even when it extends beyond the original task IDs
  - do not pull in unrelated deferred tasks/specs
  "
})

wait_agent({
  targets: [reviewer_pass],
  timeout_ms: 600000
})

send_input({
  target: coder_stream,
  message: "
  Must-fix reviewer findings for this stream:
  - [P1] internal/profile/service.go:214 Wrong fallback after missing profile row
    Scenario: resumed request with a legacy null profile reference clears a valid account-scoped row instead of reusing it.
    Violated invariant: account-scoped resume flow must not mutate a different active row.
    Required fix scope:
    - internal/profile/service.go
    Required validation:
    - env GOWORK=off go test ./internal/profile -run TestResumeKeepsActiveRow

  Preserve the scenario and invariant above. Do not broaden into deferred cleanup.
  "
})

wait_agent({
  targets: [coder_stream],
  timeout_ms: 600000
})
# Then spawn a fresh reviewer on the updated patch set with the active schema's no-context fork option.
```

The important part is the handoff payload:
- preserve reviewer `P` level, `file:line`, scenario, and violated invariant
- preserve the supervisor's must-close-now versus deferred classification
- separate must-fix-now findings from recorded/deferred items
- tell the coder exactly which tests or validation to rerun
- avoid summaries like `fix reviewer issues in service.go`

## Supervisor State Discipline

- Keep plan statuses current with exactly one step `in_progress`.
- Never exceed the active agent cap.
- Close reviewers immediately after each verdict.
- Reuse a coder only for its owned stream unless you intentionally re-scope it.
- Track completed task IDs in `tasks.md` and verify checkboxes.
- When review reopens a stream, treat its tasks as in-progress again until the must-fix-now findings are handled or explicitly deferred.

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
