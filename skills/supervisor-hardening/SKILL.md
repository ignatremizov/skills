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

If the user requests, you can pair this loop with the `supervisor-hardening` Codex hook set. Use `$codex-hooks` to manage it, and read [references/hook-setup.md](references/hook-setup.md) before installing or updating supervisor session state. Do not load that reference when hooks are not in use.

## Tool-Assisted Analysis

For Go changes that may contain duplicated logic, dead helpers, interface drift, unclear call ownership, resource leaks, or query-contract drift, read [references/semantic-code-analysis.md](references/semantic-code-analysis.md). Use its checks as scoped review scouts, validate every result against the actual contract, and report which ad-hoc checks ran separately from repository-default lint.

## When to Use

- Main coder work is complete enough that the remaining work is hardening, not feature design.
- The change touches one or more known hardening areas:
  - contract/types/consumer surfaces
  - schema/migrations
  - idempotency/transaction safety
  - query/selectability/runtime parity
  - auth/privacy/recovery
  - async UI lifecycle
  - accessibility/custom controls
  - source-of-truth / duplicated state
  - helper reuse / layer-boundary placement
  - money/currency/ledger semantics
  - operability/logging/provider liveness
  - docs/comments/specs/invariants
  - test proof and harness isolation
- You want narrower post-coder agents instead of one more generalist pass.

## Core Model

Run one or more narrow **hardening coders** and validate each stream with a **fresh reviewer** that receives extra instructions matching the hardening area.

After the selected hardening review waves complete, run one unlensed **blind-spot reviewer** before the quality gate. This reviewer looks for concrete issues not covered by the selected hardening agents and must not use the hardening taxonomy as a checklist.

After the blind-spot reviewer is closed, run a triggered **adversarial reviewer** only when the PR changes an abuse, bypass, concurrency, money, provider, privacy, or cost-amplification surface.

After the blind-spot and any triggered adversarial reviewer are closed, run one **quality-gate agent** to judge whether the selected hardening was sufficient or whether another targeted hardening stream is still warranted.

- Hardening coder owns a single hardening concern.
- Reviewer stays scoped and prioritized, but add area-specific review instructions.
- Blind-spot reviewer is unlensed and first-principles; it may report any concrete issue introduced or made actionable by the PR, including areas the supervisor did not select.
- Adversarial reviewer is threat/abuse oriented; it should assume malicious or concurrent use, replay, malformed payloads, stale state, flaky providers, and cost-amplification attempts, but still report only concrete paths.
- Quality-gate agent is audit-aware and scores the relevant hardening areas from `0-100`.
- Quality-gate recommendations must distinguish `must_close_now` follow-up from `defer_to_followup_spec`.
- Classify reviewer findings into must-close-now versus record-and-defer, with introduced behavioral, security, performance, data-integrity, operational, or documentation-contract gaps as the default inline work.
- Keep waves small and non-overlapping.
- Treat as pre-PR hardening gaps only reviewer findings that are introduced behavioral, security, performance, data-integrity, operational, or documentation-contract defects, or that directly show the selected hardening objective is still unmet.
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
- If a concurrent coder change makes an active review snapshot stale, interrupt the reviewer and ask it to stop and report only findings or investigation conclusions already established against the old snapshot before closing it. Record that output as historical evidence; never use it in place of the required fresh post-change review.
- Run the blind-spot reviewer only after the selected area-specific streams are closed, and before `quality-gate-hardening`.
- Route blind-spot findings into the smallest owning hardening stream or record-and-defer them under the same must-close-now policy used for area-specific reviewer findings.
- If a blind-spot finding causes a patch change, rerun a fresh blind-spot reviewer on the updated patch before quality gate.
- Run an adversarial reviewer after the blind-spot sweep and before quality gate only when the PR touches a trigger surface: auth/recovery/permissions/tenant scope, money/ledger/fees/balances, provider callbacks/webhooks/retries/irreversible side effects, user-controlled uploads/text/URLs/files, costly actions such as quotes/OCR/screening/notifications, state machines with malicious timing, or privacy/PII/anti-enumeration behavior.
- Route adversarial findings into the smallest owning hardening stream (`auth`, `idempotency`, `query`, `money`, `operability`, `contract`, or `source-of-truth`) or record-and-defer them under the same must-close-now policy.
- If an adversarial finding causes a patch change, rerun that owning stream's area reviewer, the blind-spot reviewer, and the adversarial reviewer before quality gate.
- If a later hardening stream changes the patch after the last quality-gate result, treat that gate result as stale and rerun the quality gate on the updated patch before concluding the session.
- Do not conclude the overall session until all review-loop follow-up work is closed and `quality-gate-hardening` has produced a passing or follow-up decision for the latest patch state.
- Only treat a quality-gate follow-up recommendation as blocking when it is classified `must_close_now`; record `defer_to_followup_spec` items for later work instead of recursively expanding the PR.
- Do not defer architectural or maintainability work silently; record the deferred finding or follow-up item before concluding.

## Non-Negotiable Guardrails

- This is post-coder hardening, not a second feature implementation pass.
- Do not reopen deferred product scope.
- Choose the fewest hardening agents that materially reduce PR risk.
- Spawn delegated agents without parent context: use `fork_context=false` when the active `spawn_agent` schema is multi-agent V1, or `fork_turns="none"` when it is V2.
- Do not run overlapping hardening agents on the same hot files in parallel unless one is explicitly scoped to a disjoint concern.
- Require evidence-oriented outputs: files changed, tests run, invariants checked.
- Reviewer remains focused on actionable findings; do not let the review loop degrade into style commentary.
- Blind-spot reviewer must be unlensed: do not pass area-specific instructions, selected hardening areas, or reviewer findings unless needed to avoid duplicate reporting.
- Adversarial reviewer is not mandatory for ordinary refactors, docs-only changes, or low-risk schema cleanup; when skipped, record why no trigger surface was present.
- Quality-gate agent may recommend another inline hardening stream only when current PR risk still has a must-close-now gap; otherwise it should defer the idea into follow-up spec work.
- Before schema, operability, or tests hardening, record the actual deployment context: topology and writer count, traffic/data volume, whether the feature has production data, whether a maintenance stop is allowed, the migration runner, and the rollback/recovery procedure.
- Require every rollout safeguard to name a reachable failure mode and explain why existing Git, migration, stop/start, health, metrics, or provisioning controls do not already cover it.
- For a controlled single-writer deployment with a maintenance window, prefer stop writers, run the normal migration, verify startup, and restart consumers. Do not invent checksum manifests, exact catalog/deparser hashes, cluster/session attestations, bespoke cutover frameworks, duplicated observability contracts, or validator-of-validator suites for speculative future scale.
- Do not use low scale to weaken required money, ledger, authorization, privacy, idempotency, or data-integrity correctness. Proportionality removes ceremonial controls, not domain invariants.

## Hardening Areas and Agent Mapping

- `contract`
  - agent: `coder-hardening-contract`
  - use when handlers, DTOs, Swagger/OpenAPI wire schemas, generated schemas, UI types, extensible enum/literal consumer types, or API-backed labels drift
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
  - use when duplicated helpers, unnecessary downstream normalization, typed status/enum/literal drift, cache-key/input drift, validation-boundary proof, or divergent rendered/submitted/search state exists
- `layer-boundary`
  - agent: `coder-hardening-layer-boundary`
  - use when helper reuse, dead helpers, repo/helper placement, provider/transport persistence ownership, read-time normalization in the wrong layer, shared utility scope, or KISS/DRY layer boundaries matter
- `money`
  - agent: `coder-hardening-money`
  - use when ledger side, amount semantics, currency/minor units, account selection, or counterparty direction matter
- `operability`
  - agent: `coder-hardening-operability`
  - use when logs, metrics, alerts, diagnostics, diagnostic specificity, developer-facing hook/script output, rate limits, provider liveness, manual recovery, or safe-stuck operational visibility matter
- `docs`
  - agent: `coder-hardening-docs`
  - use when comments, specs, README/AGENTS guidance, generated docs, diagrams, examples, runbooks, rollout notes, or invariant explanations matter
- `tests`
  - agent: `coder-hardening-tests`
  - use when changed behavior needs stronger regression proof, DB/test harness isolation, fixture parity, shell/hook parsing proof, or assertion quality

## Quality-Gate Agent

- agent: `quality-gate-hardening`
- use after the initial hardening waves complete
- purpose:
  - evaluate whether the chosen hardening areas were sufficient
  - score each relevant area `0-100`
  - recommend one additional hardening area if confidence is still too low
  - apply a structured sufficiency checklist covering semantics, retry/concurrency safety, state transitions, bypass flows, test proof quality, persistence parity, payload/identifier contract alignment, data selection processability, auth/privacy boundaries, frontend status/actionability source-of-truth selectors, helper reuse and layer-boundary ownership, async UI stale-write safety, custom-control interaction semantics, money/ledger direction, timezone/reference-date contracts, high-risk coverage ownership, and external side-effect safety
  - include operational observability, documentation fidelity, and test-harness proof where relevant

## Change Classification Heuristic

Before spawning agents, classify the change by:

1. **Primary risk**
   - What is most likely to produce a real review finding now?
2. **Execution risk**
   - Could retries, stale state, legacy rows, or deploy order break this?
3. **Contract surface**
   - Did runtime behavior move without adjacent DTOs, types, schemas, or consumers?
   - Do frontend/API enum-like consumer types preserve known literal safety while allowing unknown future strings when the backend contract requires compatibility?
4. **Data correctness**
   - Are keys, money values, filters, or state transitions easy to get subtly wrong?
   - Did the change leave hard-coded status/enum/lifecycle literals, redundant aliases, or unreachable lifecycle branches after introducing a canonical constant or presenter?
5. **Abstraction / optimization expiry**
   - Is the buggy code a duplicate or optimized fork of a more general path?
   - What original constraint justified that fork?
   - Is that constraint still true after later caching, indexing, infra, or library changes?
   - Would deleting or bypassing the special case be safer than repairing it in place?
6. **Helper / layer ownership**
   - Did the change introduce generic helpers before there is stable multi-consumer demand?
   - Did provider, transport, handler, or UI code start owning persistence selection or repository policy?
   - Are helpers placed at the narrowest layer that owns the rule, or did they move into shared utilities too early?
   - Did readers, raw SQL queries/CTEs, or workers add trimming, capitalization, enum repair, or fallback normalization that should instead live at the request/parser/import/migration/write boundary?
7. **Proof and maintainability context**
   - Did the change require tests, generated documentation, comments, specs, diagrams, or examples to keep the invariant understandable?
   - Do tests prove the intended invariant under the repo's actual harness, or are reviewers likely to find missing proof, fake-schema drift, or cleanup/isolation gaps?
8. **Operational behavior**
   - Would logs, metrics, debug endpoints, rate limits, or status transitions let operators distinguish suppressed, failed-closed, retried, or safe-stuck states?
   - Does the change expose raw PII or user-controlled text in operational surfaces without an explicit policy gate?
   - Could adjacent provider calls, DB writes, or branch failures return indistinguishable diagnostics that slow incident triage?
   - Did developer-facing hooks/scripts change verbosity, progress output, or failure behavior without matching docs or PR claims?

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
7. `operability`
8. `docs`
9. `tests`
10. `source-of-truth`
11. `layer-boundary`
12. `async-ui`
13. `a11y`

Rationale:

- `schema` first because persistence-shape drift invalidates downstream reasoning.
- `auth` early because observable security invariants can constrain both backend and frontend hardening.
- `idempotency` before `query` or `money` when replay/state-transition safety is in doubt.
- `query` before `money` when row selection itself may be wrong.
- `money` before UI polish when semantic value mapping is the real risk.
- `contract` after foundational backend semantics unless the change is contract-led.
- `operability` after core semantics because truthful logs/alerts/rate limits depend on the final state machine, but before final test-proof when operational behavior is part of the required proof.
- `docs` after semantics and contract shape are stable; when docs are material, run at least three docs review/correction passes before diminishing returns are assumed.
- `tests` after the behavior shape is stable, unless the only remaining task is to add proof for an already-correct narrow change.
- `source-of-truth` before `async-ui` or `a11y` when duplicated state/control logic is the underlying defect source.
- `layer-boundary` after source-of-truth by default because helper placement should follow canonical ownership, but before UI lifecycle/a11y when misplaced helpers drive control-flow drift.
- `a11y` last by default because it should validate the final control shape, not a moving target.

## Model-Aware Selection Rule

The current hardening coders split into:

- max-reasoning:
  - `coder-hardening-layer-boundary`
- high-reasoning:
  - `coder-hardening-contract`
  - `coder-hardening-schema`
  - `coder-hardening-idempotency`
  - `coder-hardening-query`
  - `coder-hardening-auth`
  - `coder-hardening-async-ui`
  - `coder-hardening-a11y`
  - `coder-hardening-source-of-truth`
  - `coder-hardening-money`
  - `coder-hardening-operability`
  - `coder-hardening-tests`
- medium-reasoning:
  - `coder-hardening-docs`

Selection rule:

- run `coder-hardening-layer-boundary` at its configured max effort when helper placement, provider/transport persistence ownership, dead helper churn, broad shared utility extraction, or misplaced normalization is a material review risk
- select streams by concrete risk and dependency order; the named role carries its tested model, effort, and verbosity configuration
- do not override a role's model or effort unless the user or applicable agent instructions explicitly require it
- once high-risk semantic hardening is green, run dependent documentation or proof streams against the stabilized shape

## Reviewer Additional Instructions by Area

Use the base `reviewer` profile, but add one or more area-specific instructions.

### Contract

- check only contract drift: runtime vs DTO/types/schemas/consumers
- treat stale or invalid generated schema as actionable
- treat API/frontend enum-like types that lose known-literal safety, or become too closed for allowed future backend values, as actionable

### Schema

- check only migration/snapshot/DAO parity and rollout safety
- treat fake-schema tests that hide production behavior as actionable
- calibrate rollout findings to the actual topology, data, maintenance window, and migration runner; reject speculative online/multi-cluster controls
- prefer focused Postgres behavior tests over adjacent checksums, exact catalog hashes, or bespoke post-migration attestations

### Idempotency

- check only transaction, replay, retry, dedupe, and terminal-state risks
- treat non-deterministic ordering/keys as actionable
- for race or TOCTOU findings, require the reviewer to identify the concrete competing writer, prove its mutation is allowed from the relevant source state, and map a reachable interleaving where the conflicting operations lack a shared serialization boundary; for TOCTOU, transactions need not overlap because the writer may commit after the check and before the stale result is used
- reject timing-only race concerns based on process-restart environment flags, deployment-owned operationally immutable configuration, backend-forbidden state transitions, or hypothetical direct database writes unless the active contract exposes a reachable mutation path
- prefer enforcing and testing the invariant at the owning mutation boundary over adding duplicate downstream rereads, locks, snapshots, or fences
- when operational immutability or a forbidden transition is material to the conclusion, require it to be documented at the owning code/spec/technical boundary so later reviewers can validate the assumption

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

- check only duplicated knowledge, canonical write/input boundaries, typed status/enum/literal drift, cache key/input drift, unnecessary downstream normalization in readers/raw SQL/CTEs/workers, and divergent rendered/submitted/search state
- treat multiple active sources for one concept, hard-coded lifecycle/status literals after canonical constants exist, or readers repairing data already canonicalized by writers, as actionable
- before accepting a defensive nil/length/normalization finding, verify the DTO type, route validation, schema constraint, or write contract does not already make that state impossible

### Layer Boundary

- check only helper reuse, helper placement, dead helpers, misplaced normalization helpers, shared utility scope, and layer ownership
- treat provider/transport code owning persistence selection, repository-policy leakage, one-off generic abstractions, and read-time repair that belongs at a write/input boundary as actionable when they increase current PR risk

### Money

- check only money, direction, account/currency selection, and minor-unit correctness
- treat wrong semantic side or stale money/account state as actionable

### Operability

- check only logging, metrics, diagnostics, PII exposure in operational surfaces, rate limits, provider liveness, and manual recovery visibility
- treat misleading logs, indistinguishable adjacent failure diagnostics, unsafe debug defaults, unbounded costly side effects, and invisible safe-stuck states as actionable
- include developer-facing hook/script output when a PR changes validation progress, silence/verbosity, or failure behavior
- distinguish static file consistency from runtime proof; do not duplicate full dashboard expressions, alert counts, metric lists, or runbook prose into custom validators
- require operational machinery to mitigate a reachable current failure mode and remain simpler than the failure/recovery procedure it protects

### Docs

- check only comments, specs, README/AGENTS guidance, generated docs, diagrams, examples, runbooks, rollout notes, and invariant explanations
- treat stale, missing, misleading, or underspecified docs as actionable when they create concrete future maintenance, integration, audit, or operational risk
- for material docs changes, require a three-pass loop: write/update, review against code and generated output, then correct overstatements/stale examples/missing invariants

### Tests

- check only regression proof, harness parity, fixture isolation, cleanup, and assertion quality
- treat missing invariant coverage, fake-schema/test-harness drift, shell/hook parsing drift, and cleanup/isolation gaps as actionable only when the repo's actual harness does not already cover them
- reject tests of validators that merely restate migrations, platform behavior, provisioned text, or documentation wording
- prefer tests of application-owned trigger semantics, transaction behavior, listener recovery, metric emission, and provisioning load

## Execution Protocol

1. **Preflight**
   - Read the user request, changed files, and any available report/checklist inputs.
   - Classify the change into one or more hardening areas.
   - Run an abstraction-review gate for any change that lands in an optimization, cached fast path, duplicate helper, or special-case branch.
   - When that gate needs tool-assisted semantic or duplication analysis, use the semantic-code-analysis reference and keep heuristic findings non-gating until validated.
   - Build a minimal wave plan.

2. **Wave Planning**
   - Put the highest-risk or foundational hardening area first.
   - Typical order:
     - `schema` before `idempotency` or `query`
     - `auth` before `contract` when neutral observable behavior constrains the flow
     - `query` before `money` when selection correctness is the deeper problem
     - `money` before `contract` when API/UI shape depends on corrected semantic value mapping
     - `contract` before `async-ui` when UI behavior depends on API shape
     - `operability` after core semantics when logs/metrics/rate limits/provider liveness depend on final status behavior
     - `docs` after semantics and contract shape are stable; run the three-pass docs loop when docs are material
     - `tests` after behavior is stable, or earlier when the only task is proof/isolation
     - `source-of-truth` before `async-ui` or `a11y` when duplicated control logic is the root cause
     - `layer-boundary` before `async-ui` or `a11y` when helper placement, misplaced normalization, or layer ownership drives the control shape
     - `a11y` after state/control hardening unless the only remaining risk is semantic HTML or keyboard support

3. **Hardening Loop**
   - Spawn one hardening coder per stream.
   - After each stream, spawn a fresh `reviewer` with the corresponding area instructions.
   - If a finding is an introduced behavioral, security, performance, data-integrity, operational, or documentation-contract defect, or it directly shows the selected hardening objective is still unmet, route it back to that hardening coder or into the smallest responsible follow-up hardening stream.
   - If a finding is lower-priority maintainability or cleanup work outside the current hardening objective, record it for later follow-up instead of recursively expanding the hardening loop.
   - When sending review feedback back to a coder, include the exact reviewer finding or a structured restatement with `P` level, `file:line`, scenario, owning hardening area, and focused validation to rerun.
   - Every time a hardening coder changes the stream to address reviewer findings, rerun a fresh reviewer on the updated patch set before advancing that stream.
   - When a concurrent coder invalidates an active review, interrupt that reviewer first and collect only its already-established findings as explicitly historical evidence; then close it and spawn a fresh reviewer on the updated patch.
   - Close reviewer after each verdict.

4. **Blind-Spot Sweep**
   - After the full current hardening set is closed, including any reviewer-triggered follow-up streams, spawn one unlensed blind-spot reviewer.
   - Default to `reviewer_exhaustive` when recall is worth the cost; use `reviewer` only for tiny or low-risk changes.
   - Do not pass area-specific instructions or ask it to validate the supervisor's selected lenses.
   - Prompt it to inspect the changed behavior from first principles and report concrete bugs, regressions, missing tests, contract breaks, or deployability risks that the selected hardening streams may have missed.
   - Route must-close findings back into the smallest owning hardening stream, then rerun that stream's area reviewer and another blind-spot reviewer before quality gate.
   - Record non-blocking blind-spot findings as deferred follow-up with rationale.

5. **Adversarial Sweep**
   - Decide whether adversarial review is triggered.
   - Trigger it when the PR touches auth, recovery, permissions, tenant/account scoping, money movement, ledger posting, fees, balances, provider callbacks, webhooks, retries, irreversible side effects, user-controlled uploads/text/URLs/files, rate-limited or costly actions, state machines with malicious timing, privacy, PII, or anti-enumeration surfaces.
   - If not triggered, record the skip rationale.
   - If triggered, spawn `reviewer_exhaustive` by default; use `reviewer` only for tiny targeted changes.
   - Prompt it as an adversarial abuse/bypass/race/cost sweep, not as another taxonomy review.
   - Require race findings to name the reachable competing writer and allowed transition; reject timing-only scenarios that assume impossible state changes, restart-only configuration drift, or direct database compromise without a concrete trust-boundary failure.
   - Route must-close findings back into the smallest owning hardening stream, then rerun that stream's area reviewer, a blind-spot reviewer, and another adversarial reviewer before quality gate.
   - Record non-blocking adversarial findings as deferred follow-up with rationale.

6. **Quality-Gate Pass**
   - After the full current hardening set, blind-spot sweep, and any triggered adversarial sweep are closed, including any reviewer-triggered follow-up streams, spawn `quality-gate-hardening`.
   - Give it:
     - changed files
     - areas already hardened
     - tests/checks already run
     - blind-spot reviewer result
     - adversarial reviewer result or skip rationale
     - the PR audit report context when available
   - If it recommends `None`, continue to final pass or stop.
   - If it marks one additional hardening area as `must_close_now`, run that targeted hardening stream next, mark the previous gate result stale, and then re-run the quality gate on the updated patch.
   - If it marks one additional hardening area as `defer_to_followup_spec`, record that area and rationale for later supervisor-authored follow-up work instead of expanding the active PR.
   - If a later hardening stream changes the patch after a gate result, treat the earlier gate result as stale and rerun `quality-gate-hardening` on the updated patch before concluding the session.

7. **Cross-Area Final Pass**
   - After the quality gate is satisfied, run one final reviewer with combined area instructions if the change spans multiple risk areas.
   - This is optional and separate from the required blind-spot sweep.
   - When you want extra recall after quality gate, run the default `reviewer` and `reviewer_exhaustive` in parallel for this final pass.
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

### Blind-Spot Reviewer

Include:

- `agent_type`: `reviewer_exhaustive` by default, or `reviewer` only for tiny/low-risk changes
- exact changed files or patch scope
- instruction: `unlensed blind-spot sweep`
- instruction: do not use the selected hardening areas, hardening taxonomy, or prior reviewer findings as a checklist
- instruction: inspect the changed behavior from first principles and report concrete issues the selected hardening streams may have missed
- instruction: keep the normal evidence bar; prefer no finding over weak speculation

### Adversarial Reviewer

Include:

- `agent_type`: `reviewer_exhaustive` by default, or `reviewer` only for tiny/low-risk adversarial scopes
- exact changed files or patch scope
- instruction: `adversarial abuse/bypass/race/cost sweep`
- instruction: assume a motivated user, compromised client, replayed request, concurrent request, malformed payload, stale state, flaky provider, or cost-amplification attempt
- instruction: report only concrete exploit, abuse, corruption, privacy, or operational-cost paths introduced or made actionable by this PR
- instruction: prefer no finding over speculative abuse stories
- routing note: bypass/privacy findings usually route to `auth`; replay/race to `idempotency`; selector abuse to `query`; cost/liveness to `operability`; money loss to `money`; bad contract/input shape to `contract` or `source-of-truth`

### Optional Exhaustive Reviewer

Include:

- `agent_type`: `reviewer_exhaustive`
- use it for the required blind-spot sweep by default, and for optional final or cross-area sweeps where extra recall is worth the cost
- for optional area-specific sweeps, keep the same scope files and hardening-area boundaries as the normal reviewer
- for blind-spot mode, do not pass hardening-area boundaries or area-specific instructions

### Quality Gate Agent

Include:

- changed files or diff summary
- hardening areas already run
- blind-spot reviewer result
- adversarial reviewer result or skip rationale
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
  # Multi-agent V1: use fork_context: false.
  # Multi-agent V2: replace it with fork_turns: "none".
  fork_context: false,
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
  # Multi-agent V1: use fork_context: false.
  # Multi-agent V2: replace it with fork_turns: "none".
  fork_context: false,
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
# Then spawn a fresh reviewer for the updated query slice with the active schema's no-context fork option.

spawn_agent({
  agent_type: "quality_gate_hardening",
  # Multi-agent V1: use fork_context: false.
  # Multi-agent V2: replace it with fork_turns: "none".
  fork_context: false,
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
  - `schema` -> `contract` -> `docs` or `tests` when material -> reviewer
- backend state machine / reconciliation:
  - `idempotency` -> `query` -> `money` -> reviewer
- provider callback, notification, quote, or retry flow:
  - `idempotency` or `money` -> `operability` -> `tests` -> reviewer
- auth or recovery flow:
  - `auth` -> `contract` -> `operability` when logs/diagnostics changed -> reviewer
- docs, generated docs, or template-backed technical documentation change:
  - `docs` -> `contract` when API wire behavior is affected -> reviewer
- frontend data-heavy screen:
  - `source-of-truth` -> `layer-boundary` or `async-ui` -> `tests` when behavior changed -> reviewer
- frontend custom control:
  - `source-of-truth` -> `layer-boundary` or `a11y` -> reviewer
- transfer or balance UI:
  - `money` -> `source-of-truth` -> `async-ui` -> reviewer
- review-thread or external reviewer finding triage:
  - route valid findings to the owning area, and route disputed test-harness/docs/logging findings to `tests`, `docs`, or `operability` before broad semantic streams
- helper/refactor/shared utility change:
  - `layer-boundary` -> reviewer
- backend provider, transport, or handler selecting persistence:
  - `query` -> `layer-boundary` -> reviewer

## Output Contract to User

Always report:

- selected hardening areas and why
- whether the abstraction-review gate was triggered and its conclusion
- streams run and files owned
- reviewer cycles per stream
- blind-spot reviewer result
- adversarial reviewer result or skip rationale
- quality-gate score summary
- any additional hardening area requested by quality gate
- tests/checks run
- any hardening areas intentionally skipped and why
- any remaining known risks
