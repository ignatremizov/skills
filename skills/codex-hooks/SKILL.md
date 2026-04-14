---
name: codex-hooks
description: Manage Codex lifecycle hook bundles from this skills repo. Use when deciding which hook set to install, disable, or uninstall, and when wiring per-session flow-state for spec-kit, supervisor-review-loop, supervisor-hardening, or ghc-review-supervisor loops.
---

# Codex Hooks

Use this skill when you want to manage Codex lifecycle hook bundles from this skills repository.

This skill is for:

- choosing the right hook bundle for a workflow
- installing a hook bundle into a target repo's `.codex/`
- disabling hooks without removing files
- uninstalling a hook bundle cleanly
- wiring per-session flow-state for stateful stop/session-start gates

This skill is not for:

- pretending hooks can run the whole workflow on their own
- installing multiple hook bundles at once
- using hooks as a substitute for agent orchestration

## Current Constraint

Codex currently uses a single active `.codex/hooks.json` per target repo.

That means:

- only one hook bundle should be active per target repo at a time
- installing a different bundle replaces the previous bundle
- stateful hooks should use per-session flow-state files, not one shared repo-global state file

## Available Hook Bundles

### `spec-kit`

Use when you want phase-aware enforcement for the Spec-Kit flow.

What it does:

- injects session-scoped Spec-Kit phase context on session start
- blocks completion when the supervisor session's declared required artifacts are missing
- blocks completion when the supervisor session's declared task files still have unchecked items

### `supervisor-hardening`

Use when you want post-implementation hardening enforcement.

What it does:

- injects hardening loop context on session start
- blocks completion until quality-gate has run
- blocks completion only when a quality-gate follow-up area is marked `must_close_now`
- blocks completion if review-loop closure is still pending for hardening streams

### `supervisor-review-loop`

Use when you want enforcement around implementation-supervision reviewer closure.

What it does:

- injects implementation review-loop context on session start
- blocks completion while any stream still needs a fresh post-fix reviewer pass

### `ghc-review-supervisor`

Use when you want enforcement around a `ghc`-driven PR review resolution loop.

What it does:

- injects review-loop context on session start
- blocks completion if review refresh is still pending
- blocks completion if dedupe/grouping is not finished
- blocks completion if unresolved fix groups remain
- blocks completion if review-loop closure or post-push resolution steps remain

This state is a supervisor completion ledger, not a mirror of the `ghc` cache. Keep remote review-thread contents and resolution truth in `ghc`; record only the checkpoints and obligations needed to stop the supervisor from concluding early.

## Install / Disable / Uninstall

All hook management is driven from the skills repo checkout, not from the target repo.

Use:

```bash
<SKILLS_REPO>/codex/scripts/install-codex-hooks.sh --hook-set <HOOK_SET> --root <TARGET_REPO>
<SKILLS_REPO>/codex/scripts/install-codex-hooks.sh --hook-set <HOOK_SET> --root <TARGET_REPO> --disable
<SKILLS_REPO>/codex/scripts/install-codex-hooks.sh --hook-set <HOOK_SET> --root <TARGET_REPO> --uninstall
```

Examples:

```bash
~/code/skills/codex/scripts/install-codex-hooks.sh --hook-set spec-kit --root /path/to/target-worktree
~/code/skills/codex/scripts/install-codex-hooks.sh --hook-set supervisor-review-loop --root /path/to/target-worktree
~/code/skills/codex/scripts/install-codex-hooks.sh --hook-set supervisor-hardening --root /path/to/target-worktree
~/code/skills/codex/scripts/install-codex-hooks.sh --hook-set ghc-review-supervisor --root /path/to/target-worktree
```

Notes:

- `--disable` flips `codex_hooks = false` in the target repo's `.codex/config.toml`
- `--uninstall` removes the installed hook bundle files when they match the recorded `hooks-state.json`

## Per-Session Flow-State

Stateful hook bundles use per-session flow-state files under:

```text
.codex/flow-state/by-session/<session_key>.json
```

Prefer deriving `session_key` from `transcript_path`.

Use:

```bash
python3 <SKILLS_REPO>/codex/scripts/write-flow-state.py ...
```

For `spec-kit`, prefer:

```bash
python3 <SKILLS_REPO>/codex/scripts/write-spec-kit-state.py ...
```

Record the supervisor session's active phase plus the exact required artifact paths and task-checklist paths for that session. These paths may be absolute and may point into sibling repos or worktrees. Child coder/reviewer sessions in the same worktree will no-op because their transcript-derived session key will not match the supervisor session's flow-state file.

Bootstrap state written without `--transcript-path` can seed a supervisor session that does not yet have transcript-keyed state. Once a supervisor session exists, update it with `--transcript-path "$TRANSCRIPT_PATH"` so another resumed session in the same worktree cannot consume the wrong bootstrap payload.

For `supervisor-review-loop`, use `python3 <SKILLS_REPO>/codex/scripts/write-flow-state.py --mode supervisor-review-loop ...` and keep `pending_reviews` aligned to streams that still need fresh reviewer closure. Persist exact must-close findings, deferred findings, and ignored-finding rationales in the same session state so resume context can reconstruct the real triage, not just the stream IDs. Clear must-close findings explicitly with `--clear-must-close-findings` only after they are fixed or explicitly resolved and a fresh reviewer has checked the latest patch set.

For `supervisor-hardening`, if a later hardening stream changes the patch after the last `quality-gate-hardening` result, mark the recorded gate stale with `--quality-gate-needs-rerun true`. Writing a fresh quality-gate result clears that stale flag automatically. Record `--quality-gate-followup-mode must_close_now` only when the recommended area must be completed in the active PR; use `defer_to_followup_spec` for architectural or maintainability follow-up that should be written down instead of forced inline. Persist open must-close items with `--must-close-finding ...` and deferred follow-up items with `--deferred-finding ...`, then clear them explicitly when the reviewer loop closes or the follow-up is recorded elsewhere. For a current `defer_to_followup_spec` gate result, record at least one `--deferred-finding ...` in the same or a later write so the session state acknowledges that exact defer decision. Use `--clear-pending-reviews` when you need to explicitly clear the stored review-loop-closure list.

For `ghc-review-supervisor`, prefer:

```bash
python3 <SKILLS_REPO>/codex/scripts/write-ghc-review-state.py ...
```

Persist exact must-close findings, deferred findings, and ignored-finding rationales in that `ghc` session state as review loops progress so resumed supervisor sessions can recover the actual blocking thread context and triage rationale. Clear must-close findings explicitly with `--clear-must-close-findings` only after they are fixed or explicitly resolved and a fresh reviewer has checked the latest patch set.

Do not store full `ghc` thread payloads in flow-state. Store supervisor-owned checkpoints only: last refresh timestamp, unresolved-count snapshot, deduped fix groups, pending reviewer closures, must-close findings, deferred/ignored rationale, and whether post-push resolution verification is still pending.

Example (`spec-kit` specific):

```bash
python3 ~/code/skills/codex/scripts/write-spec-kit-state.py \
  --root "$WORKTREE_ROOT" \
  --transcript-path "$TRANSCRIPT_PATH" \
  --feature-id payments-reversal \
  --phase tasks \
  --required-artifact "$PWD/specs/018-payments-reversal/spec.md" \
  --required-artifact "$PWD/specs/018-payments-reversal/plan.md" \
  --required-artifact "$PWD/specs/018-payments-reversal/tasks.md" \
  --task-path "$PWD/specs/018-payments-reversal/tasks.md"
```

Example (`ghc-review-supervisor` specific):

```bash
python3 ~/code/skills/codex/scripts/write-ghc-review-state.py \
  --root "$WORKTREE_ROOT" \
  --transcript-path "$TRANSCRIPT_PATH" \
  --repo owner/repo \
  --pr 123 \
  --branch feature/foo \
  --review-requested-at 2026-03-23T12:00:00Z \
  --review-ready-after 2026-03-23T12:15:00Z \
  --last-refresh-at 2026-03-23T12:16:30Z \
  --unresolved-threads 9 \
  --dedupe-complete true \
  --pending-group t1,t2,t3 \
  --pending-group t4,t5,t6 \
  --resolved-after-push false \
  --rerun-requested true
```

## Decision Rules

Choose the smallest useful hook bundle:

- use `spec-kit` for phase/artifact/task gating
- use `supervisor-review-loop` for implementation-stream reviewer-closure gating
- use `supervisor-hardening` for quality-gate and post-coder hardening gating
- use `ghc-review-supervisor` for `ghc` review-refresh / dedupe / batch / resolve gating

Do not install a bundle unless:

- the workflow is multi-step enough to benefit from lifecycle enforcement
- the target repo can tolerate a single active hook bundle
- the supervisor or workflow can maintain the required flow-state

Prefer disabling over uninstalling when:

- you expect to re-enable the same bundle soon
- you want to keep the installed files in place

Prefer uninstalling when:

- you are switching to a different hook bundle
- the target repo should no longer carry the old hook files

## Workflow Skill Hand-off

When a workflow skill needs lifecycle enforcement:

- `spec-kit-skill` should hand off here for `spec-kit`
- `supervisor-review-loop` should hand off here for `supervisor-review-loop`
- `supervisor-hardening` should hand off here for `supervisor-hardening`
- `ghc-review-supervisor` should hand off here for `ghc-review-supervisor`

The workflow skill should describe what needs gating.
This skill should decide the exact hook command sequence.
