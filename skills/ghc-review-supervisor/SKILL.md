---
name: ghc-review-supervisor
description: Supervisor workflow for ghc-driven PR review resolution across one or more PRs using coder_pr plus fresh reviewer loops, staged branch-owned streams, and durable thread resolution discipline.
---

# GHC Review Supervisor

Use this skill when one or more open PRs have review threads that need fixing across stacked branches or multiple repositories.

This skill is for the **supervised fix-and-resolve workflow** from GitHub remote reviewers.

- Use `ghc` workflow when the fixes are already made and the remaining work is mostly fetching, replying, resolving, or re-requesting reviews.

## Optional Hooks

You can pair this supervisor loop with the `ghc-review-supervisor` Codex hook set.

The hook bundle is meant to:

- inject ghc review-loop context on session start
- block completion until supervisor-owned review refresh checkpoints have happened after re-review requests
- block completion until dedupe/grouping has been recorded
- block completion while grouped fix batches remain
- block completion while pending reviewer-loop closure or post-push thread-resolution steps remain

The hook state is a supervisor completion ledger, not a replacement for the `ghc` cache. Use `ghc` as the source of truth for remote review-thread contents and resolution status. Record only the supervisor obligations needed to prevent premature completion: refresh checkpoints, owned fix groups, pending reviewer closures, must-close findings, deferred/ignored rationale, and post-push resolution verification.

If you want to manage that hook bundle, use `$codex-hooks` and select the `ghc-review-supervisor` hook set.

### Hook Setup and Use

Use hooks only for the supervisor session, not for spawned coder/reviewer streams.

1. Identify the target worktree root for this supervised stream.
   - example: `WORKTREE_ROOT=/path/to/target-worktree`
2. Install the `ghc-review-supervisor` hook bundle in that worktree before starting or resuming the supervisor session.
   - `~/code/skills/codex/scripts/install-codex-hooks.sh --hook-set ghc-review-supervisor --root "$WORKTREE_ROOT"`
3. Start or resume the supervisor session in that worktree so the hook registration is loaded.
4. Write session state for that supervisor session with:
   - `python3 ~/code/skills/codex/scripts/write-ghc-review-state.py --root "$WORKTREE_ROOT" --transcript-path "$TRANSCRIPT_PATH" ...`
5. Update that state after each meaningful coordination boundary:
   - after supervisor-owned refresh checkpoints
   - after dedupe/grouping
   - after spawning or closing fix groups
   - after re-review requests
   - after push/resolve batches
   - keep `ghc` thread details in the `ghc` cache and supervisor handoff messages; do not mirror full thread payloads into hook state
   - persist exact must-close findings, deferred findings, and ignored-finding rationales so resume context preserves the blocking thread details and triage rationale
   - clear recorded must-close findings with `--clear-must-close-findings` only after they are fixed or explicitly resolved and a fresh reviewer has checked the latest patch set
6. Do not write `ghc` hook state from child coder or reviewer sessions. The installed hooks can exist in the same worktree, but only the supervisor session should have matching per-session state.

## When to Use

- You have one or more open PRs with unresolved `ghc` review threads.
- Threads map cleanly to repo, branch, or file ownership.
- Work spans multiple PRs, a stacked branch set, or multiple repos.
- You need strict coder-plus-reviewer gating before threads are resolved.
- You must keep a cap on simultaneously open agents.

## Core Model

Run **coding agents** for fixes and **ephemeral reviewer agents** for scoped `P0`-`P3` validation.

- Coding agent owns a branch-scoped or thread-scoped stream.
- Reviewer agent is fresh each cycle and reports prioritized findings.
- Close reviewer agent after each verdict.
- Triage reviewer findings against the owned thread scope, the actual review request, and what the stream changed.
- Classify reviewer findings into must-fix-before-resolution versus recorded/deferred follow-up, with introduced defects as the default blocker.
- If a finding is a bug or regression introduced by the fix stream: send it back to the owning coder, patch, and spawn a new reviewer even when it falls outside the original thread set.
- If a finding is clearly pre-existing, unrelated to the fix stream's changes, or unsupported by file-level evidence: record the rationale and keep ownership boundaries clean.
- Record non-blocking reviewer findings explicitly instead of silently ignoring them, but do not keep threads open for them unless they truly must be fixed before resolution.
- Be alert for real drift, duplication, or architecture/refactor concerns surfaced by review; decide explicitly whether they reflect a concrete current risk or should be recorded as deferred follow-up work.
- When sending findings back to a coder, preserve the reviewer’s exact file, line, priority, triggering scenario, and violated expectation from the review thread.
- Prefer forwarding the reviewer finding verbatim or as a tightly structured restatement; do not replace it with a generic supervisor paraphrase.
- Make the handoff explicit about which findings block thread resolution now, which files are in scope for the fix, and what tests or refresh steps must run before resolving threads.
- Reopen the stream whenever a reviewer reports an introduced defect.
- Use supervisor judgment only for non-introduced findings that may or may not need fixing before resolution.
- After any fix round triggered by reviewer findings, require a fresh reviewer pass on the updated stream before resolving threads.
- Conclude a stream only after every introduced defect is handled, any other findings that must be fixed before resolution are handled, a fresh post-fix reviewer pass has checked the latest patch set, and required validation is complete.
- Do not conclude the overall session until the review loop for the stream is closed and post-push thread-resolution state has been refreshed.

Pair that loop with `ghc` discipline:

- use `ghc get` or `ghc ids` as the remote review-thread source of truth
- group related threads into branch-owned streams
- do not resolve a thread until the owning stream is patched, tested, reviewed, and pushed
- reply with one message per thread when resolving

## Non-Negotiable Guardrails

- Refresh `ghc` data before planning and before final unresolved-count verification.
- Do not try to recreate the `ghc` cache in hook state; store only supervisor checkpoint state and blocking workflow decisions.
- Treat remote `ghc` refresh as supervisor-owned coordination work, not default coder work.
- Always spawn delegated agents with `fork_turns="none"`.
- Keep each stream branch-owned or otherwise ownership-clean.
- Reviewers must avoid nits and optional refactors.
- Require concrete file-level evidence for findings.
- Treat defects introduced by the fix stream as in-scope for review closure even when they are outside the original owned thread set.
- Do not resolve a review thread until the fix is durable in the branch the PR points to.
- Do not re-request external reviewers until the updated branch head is pushed and that stream's thread set is fully handled.
- Re-run `ghc ids --refresh --batch-size 100` after resolve batches to verify the unresolved count actually drops.

## Execution Protocol

1. **Preflight**
   - Refresh `ghc` data with `ghc get --refresh --batch-size 100` or `ghc ids --refresh --batch-size 100`.
   - Map unresolved threads to repo, branch, file, and likely owner stream.
   - Record only the resulting supervisor plan/checkpoint state in hook flow-state; leave thread payload lookup to `ghc`.
   - Build dependency groups: stack base or highest-risk branch first, then independent waves.
   - Reserve one agent slot for reviewer churn.
2. **Critical Stream First**
   - Start with the stack base PR or highest-risk branch.
   - Spawn one coding agent for that stream.
   - Run the review loop while the latest reviewer pass still surfaces findings the supervisor judges must be fixed before resolution.
   - When sending review feedback back to the coder, include the exact reviewer finding or a structured restatement with `P` level, `file:line`, scenario, thread expectation, and required test/refresh follow-up.
   - Every time the coder changes the stream to address reviewer findings, rerun a fresh reviewer on the updated patch set before resolving threads.
3. **Parallel Waves**
   - Spawn multiple coding agents for independent PRs or branches with disjoint write sets.
   - Run a separate ephemeral review loop for each stream.
   - Serialize any overlapping hot files or shared stack dependencies.
4. **Resolve and Verify**
   - After a stream has been reviewed, its must-fix-before-resolution findings are handled, and a fresh reviewer has checked the latest patch set, have the owning coder resolve its owned threads with per-thread messages.
   - Re-request reviewers only after the updated branch is pushed and the stream is fully handled.
   - Re-run `ghc ids --refresh --batch-size 100` to confirm the unresolved set shrinks as expected.
5. **Cross-PR Final Pass**
   - Spawn one final reviewer over the completed streams when thread fixes may interact across PR boundaries.
   - When you want extra recall without weakening the normal loop, run the default `reviewer` and `reviewer_exhaustive` in parallel for this final pass.
   - Route any blockers back to the smallest responsible stream and rerun review.

## Agent Prompt Templates

### Coding Agent

Include:

- `agent_type`: `coder_pr`
- `fork_turns="none"`
- exact review-thread IDs owned
- PR reference (`owner/repo #number`) and branch
- allowed file paths
- work-specific instructions only when needed beyond the role defaults
- example work-specific instructions:
- `use the supervisor-provided review-thread IDs and context as your source of truth; do not run a remote ghc refresh unless explicitly instructed`
- required test commands and expected output format
- `resolve your owned threads yourself only after the fix is tested, reviewed, and pushed`

### Reviewer Agent

Include:

- `agent_type`: `reviewer`
- `fork_turns="none"`
- PR reference (`owner/repo #number`) and branch
- exact scope files
- exact review-thread IDs under review
- work-specific review scope and constraints only
- example work-specific instructions:
- `focus on the active thread set, but still report any bug or regression introduced by the fix stream in the touched scope even when it falls outside the original thread IDs`
- `use supervisor-provided thread context first; if exact thread lookup is needed, use cached lookup like ghc get --repo owner/repo --pr 123 PRRT_xxx without --refresh`

### Optional Exhaustive Reviewer Agent

Include:

- `agent_type`: `reviewer_exhaustive`
- use it only for optional final or cross-PR sweeps where extra recall is worth the cost
- keep the same scope files and thread ownership boundaries as the normal reviewer

## Example RPC Flow

Example:

```text
spawn_agent({
  agent_type: "coder_pr",
  fork_turns: "none",
  message: "
  Review-thread IDs owned:
  - PRRT_kwDOL1KxKs6MTE7x
  - PRRT_kwDOL1KxKs6MTE8J
  PR: example-org/example-service #664
  Branch: fix/account-linking-review
  Allowed files:
  - internal/account/linking.go
  - internal/account/linking_copy.go
  Thread context supplied by supervisor:
  - PRRT_kwDOL1KxKs6MTE7x -> account link can be reused during rematerialization
  - PRRT_kwDOL1KxKs6MTE8J -> sibling rows can attach an already-linked token
  Required tests:
  - env GOWORK=off go test ./internal/account -run TestAccountLinkConflict
  Work-specific instructions for this stream:
  - use the supervisor-provided review-thread IDs and context as your source of truth; do not run a remote ghc refresh unless explicitly instructed
  "
})

wait_agent({
  targets: [coder_stream],
  timeout_ms: 600000
})

spawn_agent({
  agent_type: "reviewer",
  fork_turns: "none",
  message: "
  PR: example-org/example-service #664
  Branch: fix/account-linking-review
  Scope files:
  - internal/account/linking.go
  - internal/account/linking_copy.go
  GitHub Review-thread IDs under review:
  - PRRT_kwDOL1KxKs6MTE7x -> account link can be reused during rematerialization
  - PRRT_kwDOL1KxKs6MTE8J -> sibling rows can attach an already-linked token
  Work-specific review constraints:
  - focus on the active thread set, but still report any bug or regression introduced by the fix stream in the touched scope even when it falls outside the original thread IDs
  - use thread context first; if exact thread lookup is needed, use cached lookup like ghc get --repo example-org/example-service --pr 664 PRRT_kwDOL1KxKs6MTE7x without --refresh
  "
})

wait_agent({
  targets: [reviewer_pass],
  timeout_ms: 600000
})

# Preserve the exact reviewer scenario; do not replace it with a generic summary.
send_input({
  target: coder_stream,
  message: "
  Findings that block thread resolution now:
  - [P1] internal/account/linking.go:812 Account link reuse can still attach a token already linked by another request.
    Scenario: sibling account rows sharing a lookup key race during rematerialization.
    Review-thread expectation: the fix must not reintroduce cross-request token assignment.
    Required fix scope:
    - internal/account/linking.go
    Required validation:
    - env GOWORK=off go test ./internal/account -run TestAlreadyLinkedTokenIsUnavailable
  "
})

wait_agent({
  targets: [coder_stream],
  timeout_ms: 600000
})
# Then spawn a fresh reviewer on the updated patch set with `fork_turns: "none"`.
```

The important part is the handoff payload:
- preserve reviewer `P` level, `file:line`, scenario, and thread expectation
- preserve your block-now versus deferred classification
- state the required tests and `ghc` resolve/final-refresh follow-up explicitly
- you own remote refresh and final verification; coders should usually work from handed-off `PRRT_...` IDs and cached context, then resolve their owned threads with implementation-specific messages after reviewer closure
- avoid summaries like `fix remaining PR comments`

## Supervisor State Discipline

- Keep plan statuses current with exactly one step `in_progress`.
- Never exceed the active agent cap.
- Close reviewers immediately after each verdict.
- Reuse a coder only for its owned stream unless you intentionally re-scope it.
- Track unresolved `ghc` thread IDs per stream and re-check them after each resolve batch.
- Treat a stream as reopened if new `ghc` refresh data shows unresolved or newly added owned threads.

## Recommended Streaming Order

- Stream 0: highest-risk branch or the stack base PR
- Stream 1+: independent repo or branch PRs with disjoint write sets
- Final: cross-PR review pass plus unresolved-count verification

## Output Contract to User

Always report:

- resolved thread IDs
- files changed by stream
- blocker/fix cycle count
- current unresolved-thread counts per PR
- tests run plus pass/fail summary
- whether reviews were re-requested
- any known unrelated failures
