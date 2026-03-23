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
- block completion if a follow-up hardening area is still required
- block completion if reviewer-green streams are still pending

If you want to manage that hook bundle, use `$codex-hooks` and select the `supervisor-hardening` hook set.

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

After the initial hardening waves are green, run one **quality-gate agent** to judge whether the selected hardening was sufficient or whether another targeted hardening stream is still warranted.

- Hardening coder owns a single hardening concern.
- Reviewer stays critical-only, but add area-specific review instructions.
- Quality-gate agent is audit-aware and scores the relevant hardening areas from `0-100`.
- Keep waves small and non-overlapping.
- Stop a stream only when reviewer says exactly: `No critical comments.`

## Non-Negotiable Guardrails

- This is post-coder hardening, not a second feature implementation pass.
- Do not reopen deferred product scope.
- Choose the fewest hardening agents that materially reduce PR risk.
- Always spawn delegated agents with `fork_context=false`.
- Do not run overlapping hardening agents on the same hot files in parallel unless one is explicitly scoped to a disjoint concern.
- Require evidence-oriented outputs: files changed, tests run, invariants checked.
- Reviewer remains critical-only; do not let the review loop degrade into style commentary.
- Quality-gate agent is allowed to recommend another hardening stream even when there is no single immediate blocker.

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

Prefer:

- one hardening agent for single-area changes
- two sequential agents for tightly coupled areas
- parallel waves only for disjoint write sets

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
   - If blockers exist, route back to that hardening coder or the smallest responsible follow-up stream.
   - Close reviewer after each verdict.

4. **Quality-Gate Pass**
   - After the initial selected hardening streams are green, spawn `quality-gate-hardening`.
   - Give it:
     - changed files
     - areas already hardened
     - tests/checks already run
     - the PR audit report context when available
   - If it recommends `None`, continue to final pass or stop.
   - If it recommends one additional hardening area with materially low confidence, run that targeted hardening stream next, then re-run the quality gate.

5. **Cross-Area Final Pass**
   - After the quality gate is satisfied, run one final reviewer with combined area instructions if the change spans multiple risk areas.
   - Use this to catch interaction defects between hardening slices.

## Agent Prompt Template

### Hardening Coder

Include:

- exact hardening area owned
- allowed file paths
- changed files or PR diff summary
- instruction: post-coder hardening only, no feature expansion
- required tests/checks
- any repo-specific proof expectation

### Reviewer

Include:

- base `reviewer` profile
- exact scope files
- exact hardening area under review
- area-specific additional instructions from this skill
- instruction: critical/blocking only, no nits
- success sentinel: `No critical comments.`

### Quality Gate Agent

Include:

- changed files or diff summary
- hardening areas already run
- tests/checks already run
- instruction: score relevant areas `0-100`
- instruction: recommend at most one next hardening area
- instruction: use audit-pattern sufficiency, not blocker-only review

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
- streams run and files owned
- reviewer cycles per stream
- quality-gate score summary
- any additional hardening area requested by quality gate
- tests/checks run
- any hardening areas intentionally skipped and why
- any remaining known risks
