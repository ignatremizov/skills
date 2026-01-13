---
name: spec-kit-skill
description: Supervisor orchestration for Spec-Kit spec-driven development. Detects the current phase and spawns worker agents with explicit phase skills (UserInput::Skill). Triggered by "spec-kit", "specify flow", "specify phases", or references to .specify/.
---

# Spec-Kit Supervisor: Phase Orchestration

Use this skill as the supervisor (Athena) to coordinate Spec-Kit phases. It does not execute phase work directly. Instead, it selects the next phase, spawns a worker agent, and injects the correct phase skill explicitly.

## Quick Start

1. Ensure `.specify/` exists (`specify init . --ai codex` if missing). Init merges into the repo and may overwrite `.specify/*` and agent prompts; use `--force` only if overwriting `.specify/` is acceptable.
2. Run `.specify/scripts/bash/detect-phase.sh --json` from the repo root.
3. Spawn a worker agent with the matching phase skill and a concise, phase-scoped prompt.
4. Attach the skill explicitly as a `UserInput::Skill` item.

**Init outputs**:
- `.specify/memory/constitution.md`
- `.specify/scripts/<bash|powershell>/` (plus any root scripts)
- `.specify/templates/` (spec/plan/tasks/checklist/agent-file templates)
- `.codex/prompts/speckit.*.md` command prompts (Codex)

**Storage**: `specs/NNN-feature-name/` for feature artifacts and `.specify/memory/` for governance.

## Skill Injection Rule (Non-Interactive)

Skills only activate when sent as explicit inputs.

- TUI: include `$spec-kit-<phase>-skill` in the message.
- Supervisor/app-server: include a `UserInput::Skill { name, path }` entry alongside text.

## Phase Skill Map

- Constitution -> `spec-kit-constitution-skill` -> `.specify/memory/constitution.md`
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
