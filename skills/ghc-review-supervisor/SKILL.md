---
name: ghc-review-supervisor
description: Supervisor workflow for ghc-driven PR review resolution across one or more PRs using coder_pr plus fresh reviewer loops, staged branch-owned streams, and durable thread resolution discipline.
---

# GHC Review Supervisor

Use this skill when one or more open PRs have `ghc` review threads that need fixing across stacked branches or multiple repositories.

This skill is for the **supervised fix-and-resolve workflow**.

- Use `gh-address-comments` when the fixes are already made and the remaining work is mostly fetching, replying, resolving, or re-requesting reviews.
- Use `supervisor-review-loop` for Spec-Kit implementation supervision from `spec.md` and `tasks.md`.

## When to Use

- You have one or more open PRs with unresolved `ghc` review threads.
- Threads map cleanly to repo, branch, or file ownership.
- Work spans multiple PRs, a stacked branch set, or multiple repos.
- You need strict coder-plus-reviewer gating before threads are resolved.
- You must keep a cap on simultaneously open agents.

## Core Model

Run **coding agents** for fixes and **ephemeral reviewer agents** for critical-only validation.

- Coding agent owns a branch-scoped or thread-scoped stream.
- Reviewer agent is fresh each cycle and reports only blockers.
- Close reviewer agent after each verdict.
- If blockers exist: send them back to the owning coder, patch, and spawn a new reviewer.
- Stop a stream only when reviewer says exactly: `No critical comments.`

Pair that loop with `ghc` discipline:

- use `ghc get` or `ghc ids` to refresh unresolved review threads
- group related threads into branch-owned streams
- do not resolve a thread until the owning stream is patched, tested, review-green, and pushed
- reply with one message per thread when resolving

## Non-Negotiable Guardrails

- Refresh `ghc` data before planning and before final unresolved-count verification.
- Always spawn delegated agents with `fork_context=false`.
- Keep each stream branch-owned or otherwise ownership-clean.
- Reviewers must avoid nits and optional refactors.
- Require concrete file-level evidence for blockers.
- Do not resolve a review thread until the fix is durable in the branch the PR points to.
- Do not re-request external reviewers until the updated branch head is pushed and that stream's thread set is fully handled.
- Re-run `ghc ids --refresh --batch-size 100` after resolve batches to verify the unresolved count actually drops.

## Execution Protocol

1. **Preflight**
   - Refresh `ghc` data with `ghc get --refresh --batch-size 100` or `ghc ids --refresh --batch-size 100`.
   - Map unresolved threads to repo, branch, file, and likely owner stream.
   - Build dependency groups: stack base or highest-risk branch first, then independent waves.
   - Reserve one agent slot for reviewer churn.
2. **Critical Stream First**
   - Start with the stack base PR or highest-risk branch.
   - Spawn one coding agent for that stream.
   - Run the review loop until a fresh reviewer returns `No critical comments.`
3. **Parallel Waves**
   - Spawn multiple coding agents for independent PRs or branches with disjoint write sets.
   - Run a separate ephemeral review loop for each stream.
   - Serialize any overlapping hot files or shared stack dependencies.
4. **Resolve and Verify**
   - After a stream is review-green, resolve its owned threads with per-thread messages.
   - Re-request reviewers only after the updated branch is pushed and the stream is fully handled.
   - Re-run `ghc ids --refresh --batch-size 100` to confirm the unresolved set shrinks as expected.
5. **Cross-PR Final Pass**
   - Spawn one final reviewer over the completed streams when thread fixes may interact across PR boundaries.
   - Route any blockers back to the smallest responsible stream and rerun review.

## Agent Prompt Templates

### Coding Agent

Include:

- `agent_type`: `coder_pr`
- `fork_context=false`
- exact review-thread IDs owned
- repo, PR number, and branch
- allowed file paths
- the instruction: `fetch with ghc get --refresh --batch-size 100 before finalizing`
- the instruction: `do not sub-delegate`
- the instruction: `you are not alone in codebase; ignore unrelated edits`
- required test commands and expected output format
- the instruction: `resolve your owned threads yourself only after the fix is tested, review-green, and pushed`

### Reviewer Agent

Include:

- `agent_type`: `reviewer`
- `fork_context=false`
- exact scope files
- exact review-thread IDs under review
- the instruction: `critical/blocking only, no nits`
- the instruction: `review only the active thread scope`
- success sentinel: `No critical comments.`

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
