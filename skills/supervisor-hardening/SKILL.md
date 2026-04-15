---
name: supervisor-hardening
description: Supervisor workflow for post-implementation PR hardening. Use after main coding work to analyze the changed area, choose the right coder-hardening agents, run them in dependency-aware waves, and pair each wave with a stricter reviewer pass derived from the hardening area.
---

# Supervisor Hardening

Use this skill after the main implementation pass is done and before opening or finalizing a PR.

It is for turning a mostly-working change into a review-hardened change by:

- classifying the change by risk area
- selecting the minimum useful `coder-hardening-*` agents
- sequencing them to avoid overlap
- pairing each hardening stream with a reviewer pass that uses area-specific additional instructions

## Optional Hooks

You can pair this supervisor loop with the `supervisor-hardening` Codex hook set.

The hook bundle is meant to:

- inject hardening-loop context on session start
- block completion until quality-gate has run
- block completion if a must-close-now follow-up hardening area is still required
- block completion if reviewer-loop closure is still pending for any hardening stream

If you want to manage that hook bundle, use `$codex-hooks` and select the `supervisor-hardening` hook set.

### Hook Setup and Use

Use hooks only for the supervisor session, not for spawned hardening coders or reviewers.

1. Identify the target worktree root for this supervised stream.
   - example: `WORKTREE_ROOT=/path/to/target-worktree`
2. Install the `supervisor-hardening` hook bundle in that worktree before starting or resuming the supervisor session.
   - `~/code/skills/codex/scripts/install-codex-hooks.sh --hook-set supervisor-hardening --root "$WORKTREE_ROOT"`
3. Start or resume the supervisor session in that worktree so the hook registration is loaded.
4. Write session state for that supervisor session with:
   - `python3 ~/code/skills/codex/scripts/write-flow-state.py --root "$WORKTREE_ROOT" --transcript-path "$TRANSCRIPT_PATH" --mode supervisor-hardening ...`
5. Update that state as the loop advances:
   - add and clear pending review-loop-closure streams
   - record must-close reviewer findings while they are still open
   - record deferred reviewer or quality-gate follow-up items for the current defer decision before concluding on `defer_to_followup_spec`
   - record quality-gate results
   - record whether a quality-gate recommendation is `must_close_now` or `defer_to_followup_spec`
   - mark the previous gate stale after later hardening streams change the patch
   - keep the pending review-loop and quality-gate state accurate so the stop gate reflects the latest session status
6. Do not write hardening hook state from child coder, reviewer, or quality-gate sessions. The installed hooks can exist in the same worktree, but only the supervisor session should have matching per-session state.

## When to Use

- Main coder work is complete enough that the remaining work is hardening, not feature design.
- The change touches one or more known hardening areas:
  - contract/docs/types
  - schema/migrations
  - idempotency/transaction safety
  - query/selectability/runtime parity
  - auth/privacy/recovery
  - async UI lifecycle
  - accessibility/custom controls
  - source-of-truth / duplication
  - money/currency/ledger semantics
- You want narrower post-coder agents instead of one more generalist pass.

## Core Model

Run one or more narrow **hardening coders** and validate each stream with a **fresh reviewer** that receives extra instructions matching the hardening area.

After the initial hardening review waves complete, run one **quality-gate agent** to judge whether the selected hardening was sufficient or whether another targeted hardening stream is still warranted.

- Hardening coder owns a single hardening concern.
- Reviewer stays scoped and prioritized, but add area-specific review instructions.
- Quality-gate agent is audit-aware and scores the relevant hardening areas from `0-100`.
- Quality-gate recommendations must distinguish `must_close_now` follow-up from `defer_to_followup_spec`.
- Classify reviewer findings into must-close-now versus record-and-defer, with introduced behavioral/security/performance/deployability gaps as the default inline work.
- Keep waves small and non-overlapping.
- Treat as pre-PR hardening gaps only reviewer findings that are introduced behavioral, security, performance, or deployability defects, or that directly show the selected hardening objective is still unmet.
- Record lower-priority maintainability or cleanup findings for later follow-up unless they are explicitly part of the current hardening objective.
- Treat non-blocking reviewer findings as record-and-defer by default unless they directly prove the current hardening objective is still unmet.
- Be alert for real drift, duplication, or architecture/refactor concerns surfaced by review; decide explicitly whether they reflect a concrete current risk or should be recorded as deferred follow-up work.
- Persist both must-close and deferred findings in session state so the workflow can prove what pre-PR hardening examined and what was intentionally deferred.
- Fix a must-close finding in the current hardening stream, or immediately route it into the next responsible hardening stream.
- When sending findings back to a hardening coder, preserve the reviewer’s exact file, line, priority, triggering scenario, and unmet hardening objective.
- Prefer forwarding the reviewer finding verbatim or as a tightly structured restatement; do not flatten it into a generic “harden this area” summary.
- Make the handoff explicit about which findings are must-close now, which hardening area owns them, and what focused tests or invariants the coder must check before the next review pass.
- After any fix round triggered by reviewer findings, rerun a fresh reviewer on the updated stream before advancing it.
- Conclude a hardening stream only after its findings are closed for that stream, a fresh post-fix reviewer pass has checked the latest patch set, and the selected hardening objective is met.
- If a later hardening stream changes the patch after the last quality-gate result, treat that gate result as stale and rerun the quality gate on the updated patch before concluding the session.
- Do not conclude the overall session until all review-loop follow-up work is closed and `quality-gate-hardening` has produced a passing or follow-up decision for the latest patch state.
- Only treat a quality-gate follow-up recommendation as blocking when it is classified `must_close_now`; record `defer_to_followup_spec` items for later work instead of recursively expanding the PR.
- Do not defer architectural or maintainability work silently; record the deferred finding or follow-up item before concluding.

## Non-Negotiable Guardrails

- This is post-coder hardening, not a second feature implementation pass.
- Do not reopen deferred product scope.
- Choose the fewest hardening agents that materially reduce PR risk.
- Always spawn delegated agents with `fork_turns="none"`.
- Do not run overlapping hardening agents on the same hot files in parallel unless one is explicitly scoped to a disjoint concern.
- Require evidence-oriented outputs: files changed, tests run, invariants checked.
- Reviewer remains focused on actionable findings; do not let the review loop degrade into style commentary.
- Quality-gate agent may recommend another inline hardening stream only when current PR risk still has a must-close-now gap; otherwise it should defer the idea into follow-up spec work.

## Hardening Areas and Agent Mapping

- `contract`
  - agent: `coder-hardening-contract`
  - use when handlers, DTOs, swagger/docs, generated schemas, UI types, or labels drift
- `schema`
  - agent: `coder-hardening-schema`
  - use when migrations, snapshots, registries, DAO shape, or prod-parity fixtures matter
- `idempotency`
  - agent: `coder-hardening-idempotency`
  - use when keys, conflict targets, transactions, retries, batching, or terminal states matter
- `query`
  - agent: `coder-hardening-query`
  - use when selectors, pagination, filters, workers, or legacy/null row behavior matter
- `auth`
  - agent: `coder-hardening-auth`
  - use when auth, recovery, anti-enumeration, trusted proxies, token lifecycle, or privacy matter
- `async-ui`
  - agent: `coder-hardening-async-ui`
  - use when async state, watchers, timers, route changes, stale responses, or fan-out matter
- `a11y`
  - agent: `coder-hardening-a11y`
  - use when bespoke controls, modals, listboxes, icons, or keyboard behavior matter
- `source-of-truth`
  - agent: `coder-hardening-source-of-truth`
  - use when duplicated helpers or divergent rendered/submitted/search state exists
- `money`
  - agent: `coder-hardening-money`
  - use when ledger side, amount semantics, currency/minor units, account selection, or counterparty direction matter

## Quality-Gate Agent

- agent: `quality-gate-hardening`
- use after the initial hardening waves complete
- purpose:
  - evaluate whether the chosen hardening areas were sufficient
  - score each relevant area `0-100`
  - recommend one additional hardening area if confidence is still too low
  - apply a structured sufficiency checklist covering semantics, retry/concurrency safety, state transitions, bypass flows, test proof quality, persistence parity, payload/identifier contract alignment, data selection processability, auth/privacy boundaries, frontend status/actionability source-of-truth selectors, async UI stale-write safety, custom-control interaction semantics, money/ledger direction, timezone/reference-date contracts, high-risk coverage ownership, and external side-effect safety

## Change Classification Heuristic

Before spawning agents, classify the change by:

1. **Primary risk**
   - What is most likely to produce a real review finding now?
2. **Execution risk**
   - Could retries, stale state, legacy rows, or deploy order break this?
3. **Contract surface**
   - Did runtime behavior move without adjacent docs/types/schemas?
4. **Data correctness**
   - Are keys, money values, filters, or state transitions easy to get subtly wrong?
5. **Abstraction / optimization expiry**
   - Is the buggy code a duplicate or optimized fork of a more general path?
   - What original constraint justified that fork?
   - Is that constraint still true after later caching, indexing, infra, or library changes?
   - Would deleting or bypassing the special case be safer than repairing it in place?

Prefer:

- one hardening agent for single-area changes
- two sequential agents for tightly coupled areas
- parallel waves only for disjoint write sets

When a change touches a special-case path, force an explicit three-way comparison before choosing the hardening stream:

- repair the local logic
- remove the special case
- route back to the canonical general path

If the code exists for performance reasons, require one sentence on whether the benchmark justification still holds.

## Default Hardening Order

When multiple areas compete, prefer this order unless the diff clearly justifies a narrower sequence:

1. `schema`
2. `auth`
3. `idempotency`
4. `query`
5. `money`
6. `contract`
7. `source-of-truth`
8. `async-ui`
9. `a11y`

Rationale:

- `schema` first because persistence-shape drift invalidates downstream reasoning.
- `auth` early because observable security invariants can constrain both backend and frontend hardening.
- `idempotency` before `query` or `money` when replay/state-transition safety is in doubt.
- `query` before `money` when row selection itself may be wrong.
- `money` before UI polish when semantic value mapping is the real risk.
- `contract` after foundational backend semantics unless the change is contract-led.
- `source-of-truth` before `async-ui` or `a11y` when duplicated state/control logic is the underlying defect source.
- `a11y` last by default because it should validate the final control shape, not a moving target.

## Model-Aware Selection Rule

The current hardening coders split into:

- high-reasoning:
  - `coder-hardening-schema`
  - `coder-hardening-auth`
  - `coder-hardening-idempotency`
  - `coder-hardening-query`
  - `coder-hardening-money`
- medium-reasoning:
  - `coder-hardening-contract`
  - `coder-hardening-source-of-truth`
  - `coder-hardening-async-ui`
  - `coder-hardening-a11y`

Selection rule:

- if both a high-reasoning and medium-reasoning area are triggered, default to the highest-risk high-reasoning stream first
- only skip a triggered high-reasoning area when the diff is clearly bounded away from that concern
- once high-risk semantic hardening is green, run the medium-reasoning hardening streams that depend on the stabilized shape

## Reviewer Additional Instructions by Area

Use the base `reviewer` profile, but add one or more area-specific instructions.

### Contract

- check only contract drift: runtime vs DTO/docs/types/consumers
- treat stale or invalid generated schema/docs as actionable

### Schema

- check only migration/snapshot/DAO parity and rollout safety
- treat fake-schema tests that hide production behavior as actionable

### Idempotency

- check only transaction, replay, retry, dedupe, and terminal-state risks
- treat non-deterministic ordering/keys as actionable

### Query

- check only query/runtime parity, processability of selected rows, and legacy/null row safety
- treat stuck-row or repeat-selection behavior as actionable

### Auth

- check only auth/privacy/recovery invariants
- treat neutral-response asymmetry, token lifecycle drift, and proxy trust issues as actionable

### Async UI

- check only stale-response, unmount, timer/watcher, refetch/error, and restored-state issues
- treat post-unmount mutation and stale fan-out as actionable

### A11y

- check only keyboard, ARIA, focus, dismissal, and semantic HTML issues
- treat mouse-only or mislabeled controls as actionable

### Source of Truth

- check only duplicated knowledge and divergent rendered/submitted/search state
- treat multiple active sources for one concept as actionable

### Money

- check only money, direction, account/currency selection, and minor-unit correctness
- treat wrong semantic side or stale money/account state as actionable

## Execution Protocol

1. **Preflight**
   - Read the user request, changed files, and any available report/checklist inputs.
   - Classify the change into one or more hardening areas.
   - Run an abstraction-review gate for any change that lands in an optimization, cached fast path, duplicate helper, or special-case branch.
   - Build a minimal wave plan.

2. **Wave Planning**
   - Put the highest-risk or foundational hardening area first.
   - Typical order:
     - `schema` before `idempotency` or `query`
     - `auth` before `contract` when neutral observable behavior constrains the flow
     - `query` before `money` when selection correctness is the deeper problem
     - `money` before `contract` when API/UI shape depends on corrected semantic value mapping
     - `contract` before `async-ui` when UI behavior depends on API shape
     - `source-of-truth` before `async-ui` or `a11y` when duplicated control logic is the root cause
     - `a11y` after state/control hardening unless the only remaining risk is semantic HTML or keyboard support

3. **Hardening Loop**
   - Spawn one hardening coder per stream.
   - After each stream, spawn a fresh `reviewer` with the corresponding area instructions.
   - If a finding is an introduced behavioral, security, performance, or deployability defect, or it directly shows the selected hardening objective is still unmet, route it back to that hardening coder or into the smallest responsible follow-up hardening stream.
   - If a finding is lower-priority maintainability or cleanup work outside the current hardening objective, record it for later follow-up instead of recursively expanding the hardening loop.
   - When sending review feedback back to a coder, include the exact reviewer finding or a structured restatement with `P` level, `file:line`, scenario, owning hardening area, and focused validation to rerun.
   - Every time a hardening coder changes the stream to address reviewer findings, rerun a fresh reviewer on the updated patch set before advancing that stream.
   - Close reviewer after each verdict.

4. **Quality-Gate Pass**
   - After the full current hardening set is closed, including any reviewer-triggered follow-up streams, spawn `quality-gate-hardening`.
   - Give it:
     - changed files
     - areas already hardened
     - tests/checks already run
     - the PR audit report context when available
   - If it recommends `None`, continue to final pass or stop.
   - If it marks one additional hardening area as `must_close_now`, run that targeted hardening stream next, mark the previous gate result stale, and then re-run the quality gate on the updated patch.
   - If it marks one additional hardening area as `defer_to_followup_spec`, record that area and rationale for later supervisor-authored follow-up work instead of expanding the active PR.
   - If a later hardening stream changes the patch after a gate result, treat the earlier gate result as stale and rerun `quality-gate-hardening` on the updated patch before concluding the session.

5. **Cross-Area Final Pass**
   - After the quality gate is satisfied, run one final reviewer with combined area instructions if the change spans multiple risk areas.
   - When you want extra recall without weakening the normal loop, run the default `reviewer` and `reviewer_exhaustive` in parallel for this final pass.
   - Use this to catch interaction defects between hardening slices.

## Abstraction-Review Gate

Run this gate during preflight whenever the changed area appears in:

- an optimization path
- a duplicate implementation of a general path
- a cached fast path
- a feature flag or special-case branch
- any code whose main purpose is to avoid a previously expensive operation

The gate is short and mandatory:

1. Name the canonical general path, if one exists.
2. State why the special path exists.
3. State whether that reason is still valid.
4. Compare:
   - fix the special path
   - delete the special path
   - route callers back to the canonical path
5. Prefer deletion or reuse of the canonical path when:
   - semantics are duplicated
   - performance justification is stale or unproven
   - the special path has already drifted from the canonical behavior

This is not a request to reopen product scope. It is a narrow review gate intended to catch cases where the safest change is to remove code rather than preserve or extend a risky special case.

## Agent Prompt Template

### Hardening Coder

Include:

- exact hardening area owned
- allowed file paths
- changed files or PR diff summary
- work-specific instructions only when needed beyond the role defaults
- example work-specific instruction: `post-coder hardening only, no feature expansion`
- required tests/checks
- any repo-specific proof expectation

### Reviewer

Include:

- `agent_type`: `reviewer`
- exact scope files
- exact hardening area under review
- area-specific additional instructions from this skill
- work-specific review scope and area-specific constraints only

### Optional Exhaustive Reviewer

Include:

- `agent_type`: `reviewer_exhaustive`
- use it only for optional final or cross-area sweeps where extra recall is worth the cost
- keep the same scope files and hardening-area boundaries as the normal reviewer

### Quality Gate Agent

Include:

- changed files or diff summary
- hardening areas already run
- tests/checks already run
- result of the abstraction-review gate when one was triggered
- instruction: score relevant areas `0-100`
- instruction: recommend at most one next hardening area
- instruction: classify that recommendation as `must_close_now` or `defer_to_followup_spec`
- instruction: use audit-pattern sufficiency, not blocker-only review

## Example RPC Flow

Example:

```text
spawn_agent({
  agent_type: "coder_hardening_query",
  fork_turns: "none",
  message: "
  Hardening area owned: query
  Allowed files:
  - internal/workflow/repository.go
  - internal/workflow/service.go
  - internal/workflow/repository_test.go
  Changed files / PR summary:
  - request-scoped workflow item selection
  Work-specific instruction:
  - post-coder hardening only, no feature expansion
  Required tests:
  - env GOWORK=off go test ./internal/workflow -run RequestScopedSelection
  "
})

wait_agent({
  targets: [query_stream],
  timeout_ms: 600000
})

spawn_agent({
  agent_type: "reviewer",
  fork_turns: "none",
  message: "
  Scope files:
  - internal/workflow/repository.go
  - internal/workflow/service.go
  - internal/workflow/repository_test.go
  Hardening area under review: query
  Area-specific review constraints:
  - check only query/runtime parity, processability of selected rows, and legacy/null row safety
  - treat stuck-row or repeat-selection behavior as actionable
  "
})

wait_agent({
  targets: [query_review],
  timeout_ms: 600000
})

send_input({
  target: query_stream,
  message: "
  Must-close hardening findings for area=query:
  - [P1] internal/workflow/repository.go:301 Request-scoped miss still falls back to another claimed row for the same account.
    Scenario: legacy drifted data leaves a different request's claimed row active.
    Unmet hardening objective: query/processability must fail closed instead of selecting the wrong row.
    Required fix scope:
    - internal/workflow/repository.go
    Required validation:
    - env GOWORK=off go test ./internal/workflow -run TestRequestScopedClaimedRowDoesNotCrossRequests

  Do not expand into lower-priority cleanup outside the query hardening objective.
  "
})

wait_agent({
  targets: [query_stream],
  timeout_ms: 600000
})
# Then spawn a fresh reviewer for the updated query slice with `fork_turns: "none"`.

spawn_agent({
  agent_type: "quality_gate_hardening",
  fork_turns: "none",
  message: "
  Changed files:
  - internal/workflow/repository.go
  - internal/workflow/service.go
  Hardening areas already run:
  - query
  Tests/checks already run:
  - env GOWORK=off go test ./internal/workflow -run RequestScopedSelection
  Result of abstraction-review gate:
  - special case should route back to the canonical request-scoped path
  Work-specific instructions:
  - score relevant areas 0-100
  - recommend at most one next hardening area
  - use audit-pattern sufficiency, not blocker-only review
  "
})
```

The important part is the handoff payload:
- preserve reviewer `P` level, `file:line`, scenario, and unmet hardening objective
- preserve the supervisor's must-close-now versus deferred classification
- distinguish must-close findings from later follow-up cleanup
- only treat `quality-gate-hardening` follow-up as blocking when it is classified `must_close_now`
- tell the coder which focused invariants and tests to rerun
- if a later stream changes the patch after a gate result, treat the earlier gate result as stale and rerun the gate on the updated patch

## Recommended Area Combinations

- highest-risk backend change:
  - `schema` -> `auth` or `idempotency` -> `query` -> reviewer
- backend API with migration:
  - `schema` -> `contract` -> reviewer
- backend state machine / reconciliation:
  - `idempotency` -> `query` -> `money` -> reviewer
- auth or recovery flow:
  - `auth` -> `contract` -> reviewer
- frontend data-heavy screen:
  - `source-of-truth` -> `async-ui` -> reviewer
- frontend custom control:
  - `source-of-truth` -> `a11y` -> reviewer
- transfer or balance UI:
  - `money` -> `source-of-truth` -> `async-ui` -> reviewer

## Output Contract to User

Always report:

- selected hardening areas and why
- whether the abstraction-review gate was triggered and its conclusion
- streams run and files owned
- reviewer cycles per stream
- quality-gate score summary
- any additional hardening area requested by quality gate
- tests/checks run
- any hardening areas intentionally skipped and why
- any remaining known risks
