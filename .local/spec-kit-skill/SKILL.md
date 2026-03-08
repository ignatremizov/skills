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
- Implement -> use the existing coding/review loop roles (`coder_spec`, `reviewer_default`, supervisor orchestration), not a separate phase agent from this skill

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
