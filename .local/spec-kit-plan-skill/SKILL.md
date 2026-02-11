---
name: spec-kit-plan-skill
description: Generate the Spec-Kit plan bundle (plan.md, data-model.md, contracts, research.md, quickstart.md) from spec.md.
---

# Spec-Kit Plan Phase

Produce the technical plan bundle.

## Prerequisites

- `spec.md` is complete (or intentionally lightweight with Linear references).
- Constitution is available.

## Steps

1. Run `{$HOME,.}/.specify/scripts/bash/setup-plan.sh --json` and capture the paths it outputs.
2. Read `{$HOME,.}/.specify/templates/plan-template.md` and use this `SKILL.md` as the planning rubric.
3. Ensure `plan.md` is templated if missing/empty:
   - Run `../spec-kit-skill/scripts/copy-template.sh --name plan-template.md --to <IMPL_PLAN from setup-plan output> --root .`
4. Write `plan.md`, filling all sections and documenting tradeoffs.
5. Create supporting artifacts:
   - `research.md` for unknowns and decisions
   - `data-model.md` for entities and relationships
   - `contracts/` for API/interface contracts
   - `quickstart.md` for developer setup and verification
6. Ensure the plan references Linear issue(s) and constitution requirements.
7. Stop and report paths, unresolved questions, and readiness for tasks.

## Output

- `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Example prompts

- "Generate the plan bundle for ZOL-123 from spec.md."
- "Create plan.md, data-model.md, contracts/, research.md, and quickstart.md for ZOL-456."
