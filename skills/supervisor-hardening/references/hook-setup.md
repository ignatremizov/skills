# Supervisor Hardening Hook Setup

Read this reference only when the supervisor uses the `supervisor-hardening` Codex hook set.

The hook bundle:

- injects hardening-loop context on session start
- blocks completion until quality gate has run
- blocks completion while a `must_close_now` follow-up area remains open
- blocks completion while reviewer-loop closure is pending

Use hooks only for the supervisor session, not spawned coders, reviewers, or quality-gate agents.

1. Identify the target worktree root, for example `WORKTREE_ROOT=/path/to/target-worktree`.
2. Install the bundle before starting or resuming the supervisor session:
   - `~/code/skills/codex/scripts/install-codex-hooks.sh --hook-set supervisor-hardening --root "$WORKTREE_ROOT"`
3. Start or resume the supervisor session in that worktree so the hook registration is loaded.
4. Write state for that supervisor session:
   - `python3 ~/code/skills/codex/scripts/write-flow-state.py --root "$WORKTREE_ROOT" --transcript-path "$TRANSCRIPT_PATH" --mode supervisor-hardening ...`
5. Keep state synchronized as the loop advances:
   - add and clear pending review-loop-closure streams
   - record and clear must-close reviewer findings
   - record deferred reviewer or quality-gate follow-up items before concluding on `defer_to_followup_spec`
   - record quality-gate results and whether the recommendation is `must_close_now` or `defer_to_followup_spec`
   - mark the previous gate stale after later hardening streams change the patch
6. Do not write hardening hook state from child sessions. Only the supervisor session should have matching per-session state.
