---
name: git-commit-style
description: Enforce verbose, PR-summary style commit messages that fully describe changes, rationale, and behavior/impact without requiring code review. Use when writing commits or when a task requires commit message guidance.
---

# Git Commit Style

Write commit messages with enough detail to stand on their own during review or merge.

## Required format

- Follow Conventional Commits: `<type(scope)>: <imperative summary>`
- Include a short body paragraph describing behavior change and impact when relevant.
- Use a blank line between subject and body.
- Prefer bullet points for detailed change lists.
- If there is no ticket, do not include a ticket tag in the subject line.
- Do not hard-wrap body lines; keep paragraphs on single lines.

## Length guidance

- Rule of thumb: fewer than ~5 lines is likely too short; more than ~30 lines is likely too long.

## Content guidance

- Explain what changed and why, not just where.
- Call out user-visible behavior changes, risks, and testing.
- Keep it factual; avoid filler.
- When asked to draft a commit message, always inspect the diff first.
- When asked to amend a commit message, inspect the diff for the commit plus the current changes (typically staged). Update the message to cover the full combined diff while preserving and expanding the original intent.

## Repo style alignment (required)

Before drafting a message, align to the repository’s recent commit style.

Process:
1. Check for explicit guidance in repo docs (AGENTS.md, CONTRIBUTING, README).
2. Inspect at least 5–10 recent commits using full `git log` output (not `--oneline`).
3. Mirror the dominant structure:
   - If commits include a short body paragraph and a `Changes:` list, follow that pattern.
   - If commits are single-line subjects for docs-only changes, keep it short.
   - If commits include “Behavioral effect” or testing notes, include them when relevant.
4. If the user provides an example commit message, treat it as the primary style reference.
5. If you already drafted a message before reviewing repo style, revise it to match.

## Examples

```text
feat(execpolicy): [ZOL-2450] add auto-allow prefixes for execpolicy at startup

Allow configured command prefixes to be auto-approved at startup so routine commands (psql, test cache) no longer require manual execpolicy amendments each session while unlisted commands remain gated.

**Problem:**
Operators lose time re-approving the same safe commands each session because amendments are not persisted into the default policy.

**Approach:**
Introduce an explicit config list that is merged into the effective policy at startup, with deterministic precedence and strict prefix matching.

**Changes:**
- Add `execpolicy.auto_allow_prefixes` to config types and schema with workspace override support.
- Merge configured prefixes into the effective policy at startup while preserving existing manual amendments.
- Define match semantics: prefix match on raw command string, case-sensitive, no shell parsing or quoting expansion.
- Log the merged count at debug level for visibility.

**Tests:**
- Cover prefix match success + non-match behavior.
- Verify merge precedence across global/workspace/execpolicy amendments.

**Behavioral effect:**
Commands starting with configured prefixes are auto-approved without prompting while all other commands continue to require approval.
```

```text
fix(reconcile): recover from stale pagination cursor without data gaps

Rietumu pagination cursors can go stale while stable ref numbers remain valid; recover by retrying without cursor and anchoring lookback to the last known bookmark.

**Problem:**
Ingestion can stall when the upstream cursor expires. The current behavior stops processing without a retry path and risks missing new rows.

**Approach:**
Retry once without the cursor and anchor the date range to a known-good bookmark to avoid both gaps and duplicates.

**Changes:**
- Retry once without trnID when an empty page is returned with cursor set.
- Anchor dateFrom to the bookmark booked_at minus safety margin; clamp dateFrom/dateTo ordering.
- Log a warning when the bookmark cannot be resolved and fall back to latest booked_at.

**Tests:**
- Add cursor fallback tests for single-page and multi-page pagination.
- Cover bookmark-not-found behavior and ensure no duplicate ingestion.

**Behavioral effect:**
Ingestion resumes automatically after cursor invalidation without skipping newer rows or duplicating historical rows.
```

```text
refactor(statement): improve PDF generation robustness without behavior change

Tighten cleanup and edge-case handling in PDF generation and transaction preload helpers to reduce operational noise without changing output behavior.

**Problem:**
Timeout paths left temp files behind and some edge cases emitted noisy logs, making failures harder to triage in production.

**Approach:**
Harden cleanup paths and clarify fallback behavior without changing outputs.

**Changes:**
- Fix temp file cleanup on timeout error path and add defensive UUID shortening.
- Document deep preload chain constraints and maintain existing query behavior.
- Update comments to clarify counterparty fallback order.

**Testing:**
- Existing tests remain green; no new behavior introduced.

No breaking changes; behavior identical aside from improved resilience and documentation.
```

### Repository examples (TKTSTO)

Use these as concrete references for verbosity and structure.

```text
feat(options): add configurable reconcile interval and ops backlog warning

Add user-facing settings to control background reconciliation and monitor ops queue health. Users can now disable periodic reconciliation or adjust the interval, and configure when to show backlog warnings.

Changes:
- Add reconcileIntervalMinutes config (default 5min, 0 disables periodic)
- Add opsBacklogWarnThreshold config (default 50, 0 disables warning)
- Add Options UI with debounced inputs for both settings
- Add initBackgroundConfig() to load settings on startup
- Add maybeWarnOpsBacklog() to emit treeview_status warnings
- Update initReconcileAlarm() to disable alarm when interval=0
- Add storage change listeners to update alarm and threshold dynamically
- Add countPendingOps() to OpsQueue and countOpsByState() to IDB
- Add configurable runningStaleMs parameter to processOpsQueue
- Update TreeView to handle broadcast messages (no windowId filter)
- Add treeview_status message handler to display warnings
- Add conflict policy comment in runReconcile
- Update AGENTS.md with new config options
- Add Node test for countPendingOps
- Update version to 0.0.2.10

Startup reconcile always runs regardless of interval setting. Backlog warnings appear at most once per 5 minutes to avoid spam.
```

```text
feat(bkgd): add durable ops queue and reconciliation for MV3 resilience

Add resumable background work infrastructure to handle service worker terminations gracefully in MV3 browsers. Introduce OpsQueue for intent persistence and periodic reconciliation to ensure eventual consistency without requiring open views.

Changes:
- Add OpsQueue (bkgd/ops.js) with IDB-backed intent records (pending, running, done, failed states)
- Add reconcile pass (bkgd/reconcile.js) to merge browser state with tree on startup and periodic alarm
- Bump IDB schema to v2 with new "Ops" object store (state/createdAt indexes)
- Route tree mutations (load, unload, move, delete) through intent queue for resumability
- Add op processor with time budget, retry logic, and stale op recovery
- Implement boring-leaf cleanup to reduce unintended wasLoaded clutter
- Add dirty hint tracking and configurable reconcile interval (5min)
- Update TreeStore/NodeStore to enqueue intents instead of direct mutations for view/browserEvent sources
- Add comprehensive Node-based tests for OpsQueue lifecycle and runReconcile behavior
- Update version to 0.0.2.9

This addresses the root cause of partially-applied tree updates when SW terminates mid-operation, especially "pink tab clutter" from closed tabs persisting as saved tabs.
```

### Multi-area commit guidance (svc repo examples)

Use a multi-area subject or a broad scope when a single cohesive change spans
multiple subsystems that must move together (schema + API + background jobs,
or validation + infra + UX). The commit message should narrate the whole story
so reviewers do not have to correlate multiple commits to understand impact.

```text
refactor(db,s3,pdf): clarify date range strategy and fix resource cleanup ordering

Documentation improvements and a resource cleanup fix for robustness.

Date range strategy:
- Remove specific max/min recommendations from GetAllTransactionsForAccount comments
- Clarify product decision: no hard limit enforced; monitoring and optimization expected for large ranges
- Update 000136 migration safety condition to explicitly handle NULL vs non-NULL ben_name cases for clarity

S3 presigned URL security:
- Clarify that baseEndpoint validation is primarily a guardrail for dev/docker setups (localstack/minio)
- Note that production AWS (no baseEndpoint) skips validation and has no effect

HTML-to-PDF cleanup:
- Move resp.Body.Close() to execute immediately after response received, before status check
- Extract duplicate cleanup deferred calls in ChromePrintToPdf to single location after URL resolution
- Add nil check before calling cleanup to guard against uninitialized function
- Add comment documenting that defer covers all return paths after file creation

Impact: Improved clarity on non-enforced constraints (operators understand they own performance tuning), safer HTTP response handling (body closed even on error status), and more maintainable cleanup pattern (single defer instead of duplicated in two branches).
```

```text
fix(statement): add date validation and improve HTTP server startup diagnostics

Strengthened statement generation with upfront date validation and improved observability for HTML-to-PDF conversion failures.

Date validation:
- Add validateStatementDates to reject end-before-start requests upfront
- Call validation in GenerateAccountStatementPDF before DB queries
- Add unit tests covering valid and invalid date ranges
- Document product decision: no hard timespan limit (monitor and optimize if needed)

HTTP server improvements (htmltopdf.go):
- Add serverErr channel to detect server.Serve() startup failures immediately
- Check serverErr in health check loop to fail fast instead of timing out
- Change health check from GET to HEAD (lighter weight, no response body)
- Add timeout warning log with duration and URL for debugging slow startups
- Clarify godoc: caller must defer cleanup function after successful return

Temp file cleanup:
- Replace silent ignore of os.Remove error with log.Warnf for diagnostics

Behavioral impact: Invalid date ranges now return InvalidRequest immediately instead of proceeding to DB queries. Server startup failures surface within milliseconds instead of timing out after 5 seconds.
```

Other multi-area examples (subjects) from the same history:
- `feat(statement): [ZOL-1679] add counterparty info for incoming transfers and migrate to bank_coordinate`
- `feat(statement): [ZOL-1679] stable statement refs, rietumu metadata, and html->pdf hardening`
