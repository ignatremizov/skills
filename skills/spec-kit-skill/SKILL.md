---
name: spec-kit-skill
description: Supervisor orchestration for Spec-Kit spec-driven development. Detects the current phase and spawns the matching named phase agent role. Triggered by "spec-kit", "specify flow", "specify phases", or references to .specify/.
---

# Spec-Kit Supervisor: Phase Orchestration

Use this skill as the supervisor (Athena) to coordinate Spec-Kit phases. It does not execute phase work directly. Instead, it selects the next phase and spawns the matching phase worker by `agent_type`.

## Quick Start

1. Ensure `{$HOME,.}/.specify/` exists (`specify init . --ai codex` if missing). Init merges into the repo and may overwrite `.specify/*`; use `--force` only if overwriting repo `.specify/` is acceptable.
2. Run `{$HOME,.}/.specify/scripts/bash/detect-phase.sh --json` from the repo root.
3. Ensure workflow assets exist:
   - Templates in `$HOME/.specify/templates/` (see "Bootstrap Templates")
4. Spawn a worker agent with the matching phase `agent_type` and a concise, phase-scoped prompt.

## Bootstrap Templates

Use `scripts/bootstrap-assets.sh` to ensure template availability.

- Default target root is `$HOME` (shared template bootstrap).
- Use `--root .` to bootstrap templates for the current repository.
- The script manages `<root>/.specify/templates/` only.
- If `<root>/.specify/templates/` already exists, managed templates are overwritten.
- If templates are missing, they are created from known sources (or stubs as fallback).
- To copy a template directly into a feature artifact file, use:
  - `scripts/copy-template.sh --name <template-file> --to <target-file> --root .`

Examples:

- Shared templates: `scripts/bootstrap-assets.sh --ensure templates`
- Repo templates: `scripts/bootstrap-assets.sh --root . --ensure templates`

## Scripts

### `scripts/detect-phase.sh`

- Purpose: detect Spec-Kit readiness and current phase.
- Typical usage:
  - `scripts/detect-phase.sh --json`
  - `scripts/detect-phase.sh --feature specs/001-some-feature --json`
- JSON output contract includes:
  - `cli_installed`
  - `project_initialized`
  - `templates_available`
  - `constitution_path`
  - `latest_feature`
  - `latest_phase`
  - `selected_feature`
  - `selected_phase`
  - `current_phase`
  - `current_phase` is an alias for `selected_phase` (backward compatibility).

### `scripts/bootstrap-assets.sh`

- Purpose: ensure required templates exist for phase workers.
- Contract and usage: see "Bootstrap Templates".

### `scripts/copy-template.sh`

- Purpose: copy one template file into a concrete feature artifact file.
- Typical usage:
  - `scripts/copy-template.sh --name spec-template.md --to specs/001-feature/spec.md --root .`
- Behavior contract:
  - source preference: `$HOME/.specify/templates` first, repo `.specify/templates` second
  - skips non-empty targets unless `--force` is provided

## Optional Hooks

The optional Spec-Kit hook bundle provides session-scoped workflow enforcement for the supervisor session:

- `SessionStart` hook:
  - injects the supervisor session's current phase context
  - surfaces the exact required artifact paths and tracked task files recorded for that session
  - warns the model not to claim completion while those declared artifacts are still missing
- `Stop` hook:
  - checks the supervisor session's declared required artifacts
  - checks unchecked boxes in the supervisor session's declared task files
  - blocks one completion pass and feeds a continuation prompt back into the model

This is useful when you want deterministic gating on top of the normal supervisor logic.

If you want to manage the hook bundle, use `$codex-hooks` and select the `spec-kit` hook set.

### Hook Setup and Use

Use hooks only for the supervisor session, not for spawned phase workers.

1. Identify the target worktree root for this supervised stream.
   - example: `WORKTREE_ROOT=/path/to/target-worktree`
2. Install the `spec-kit` hook bundle in that worktree before starting or resuming the supervisor session.
   - `~/code/skills/codex/scripts/install-codex-hooks.sh --hook-set spec-kit --root "$WORKTREE_ROOT"`
3. Start or resume the supervisor session in that worktree so the hook registration is loaded.
4. Write session state for that supervisor session with:
   - bootstrap state without `--transcript-path` can seed a supervisor session that does not yet have transcript-keyed state
   - after the supervisor session exists, write or refresh the session-scoped state with `--transcript-path "$TRANSCRIPT_PATH"`
   - `python3 ~/code/skills/codex/scripts/write-spec-kit-state.py --root "$WORKTREE_ROOT" ...`
5. Record:
   - active `--phase`
   - `--feature-id` when useful
   - every required artifact path with `--required-artifact`
   - every gated task checklist with `--task-path`
6. Update that state after each phase transition.
7. For cross-repo features, pass absolute paths for required artifacts and task files in sibling repos or worktrees.
8. Do not write Spec-Kit hook state from child workers. The installed hooks can exist in the same worktree, but only the supervisor session should have matching per-session state.
9. A supervisor `SessionStart` on `resume` migrates bootstrap state only when the current transcript does not already have session state. For existing supervisor sessions, update state with `--transcript-path "$TRANSCRIPT_PATH"` instead of relying on global bootstrap state.

**Init outputs**:
- `specs/constitution.md`
- `{$HOME,.}/.specify/scripts/<bash|powershell>/` (plus any root scripts)
- `{$HOME,.}/.specify/templates/` (spec/plan/tasks/checklist/agent-file templates)

**Storage**: `specs/NNN-feature-name/` for feature artifacts and `specs/constitution.md` for governance.

## Phase Agent Map

- Constitution -> `spec-kit-constitution-skill` remains a standalone skill, not a named phase agent role
- Specify -> `spec_kit_specify` -> `specs/NNN-feature-name/spec.md`
- Clarify -> `spec_kit_clarify` -> spec clarifications updated
- Plan -> `spec_kit_plan` -> `plan.md`, `data-model.md`, `contracts/`, `research.md`, `quickstart.md`
- Checklist (optional) -> `spec_kit_checklist` -> `checklists/<domain>.md`
- Tasks -> `spec_kit_tasks` -> `tasks.md`
- Analyze -> `spec_kit_analyze` -> analysis report and fixes
- Implement -> hand off to `supervisor-review-loop` for multi-stream coder/reviewer supervision, or `spec-kit-implement-skill` when one agent can execute `tasks.md` directly

## Supervisor Flow

1. Detect phase.
2. If prerequisites are missing, stop and request the missing artifact.
3. Spawn a worker agent with the matching phase `agent_type`.
4. Optionally run the checklist phase after plan for requirements-quality gating.
5. Review output and proceed or re-run the phase.

## Orchestration Protocol (Required)

1. Keep the supervisor read-only for phase selection and gating.
2. Before spawning workers, ensure templates exist (see "Bootstrap Templates").
3. Spawn exactly one phase worker at a time using the matching named `agent_type`.
4. Require worker outputs to include:
   - touched paths
   - unresolved questions
   - next unblocked phase
5. Do not advance phase if required artifacts are missing.

## Sources of Truth

If Linear is the source of truth:

- Link Linear issue(s) in `spec.md`.
- Mirror clarifications and decisions back to Linear.
- Keep `AGENTS.md` as the engineering standards reference in the constitution.

## Stop Conditions

After each phase, stop and report:

- Output paths
- Open questions or missing data
- Whether the next phase is unblocked

## Example prompts

- "Act as the Spec-Kit supervisor: detect the current phase and spawn the right phase agent for ZOL-123."
- "Coordinate the next Spec-Kit phase and use the matching named agent role."
