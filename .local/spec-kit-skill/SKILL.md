---
name: spec-kit-skill
description: Supervisor orchestration for Spec-Kit spec-driven development. Detects the current phase and spawns worker agents with explicit phase skills (UserInput::Skill). Triggered by "spec-kit", "specify flow", "specify phases", or references to .specify/.
---

# Spec-Kit Supervisor: Phase Orchestration

Use this skill as the supervisor (Athena) to coordinate Spec-Kit phases. It does not execute phase work directly. Instead, it selects the next phase, spawns a worker agent, and injects the correct phase skill explicitly.

## Quick Start

1. Ensure `{$HOME,.}/.specify/` exists (`specify init . --ai codex` if missing). Init merges into the repo and may overwrite `.specify/*`; use `--force` only if overwriting repo `.specify/` is acceptable.
2. Run `{$HOME,.}/.specify/scripts/bash/detect-phase.sh --json` from the repo root.
3. Ensure workflow assets exist:
   - Templates in `$HOME/.specify/templates/` (see "Bootstrap Templates")
4. Spawn a worker agent with the matching phase skill and a concise, phase-scoped prompt.
5. Attach the skill explicitly as a `UserInput::Skill` item.

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

**Init outputs**:
- `specs/constitution.md`
- `{$HOME,.}/.specify/scripts/<bash|powershell>/` (plus any root scripts)
- `{$HOME,.}/.specify/templates/` (spec/plan/tasks/checklist/agent-file templates)

**Storage**: `specs/NNN-feature-name/` for feature artifacts and `specs/constitution.md` for governance.

## Skill Injection Rule (Non-Interactive)

Skills only activate when sent as explicit inputs.

- TUI: include `$spec-kit-<phase>-skill` in the message.
- Supervisor/app-server: include a `UserInput::Skill { name, path }` entry alongside text.

## Phase Skill Map

- Constitution -> `spec-kit-constitution-skill` -> `specs/constitution.md`
- Specify -> `spec-kit-specify-skill` -> `specs/NNN-feature-name/spec.md`
- Clarify -> `spec-kit-clarify-skill` -> spec clarifications updated
- Plan -> `spec-kit-plan-skill` -> `plan.md`, `data-model.md`, `contracts/`, `research.md`, `quickstart.md`
- Checklist (optional) -> `spec-kit-checklist-skill` -> `checklists/<domain>.md`
- Tasks -> `spec-kit-tasks-skill` -> `tasks.md`
- Analyze -> `spec-kit-analyze-skill` -> analysis report and fixes
- Implement -> `spec-kit-implement-skill` -> code changes and task updates

## Supervisor Flow

1. Detect phase.
2. If prerequisites are missing, stop and request the missing artifact.
3. Spawn a worker agent and inject the matching phase skill.
4. Optionally run the checklist phase after plan for requirements-quality gating.
5. Review output and proceed or re-run the phase.

## Orchestration Protocol (Required)

1. Keep the supervisor read-only for phase selection and gating.
2. Before spawning workers, ensure templates exist (see "Bootstrap Templates").
3. Spawn exactly one phase worker at a time with explicit `UserInput::Skill` injection.
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

- "Act as the Spec-Kit supervisor: detect the current phase and spawn the right worker for ZOL-123."
- "Coordinate the next Spec-Kit phase and inject the matching skill."
