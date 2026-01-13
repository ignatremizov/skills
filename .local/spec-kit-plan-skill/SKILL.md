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

1. Run `.specify/scripts/bash/setup-plan.sh --json` and capture the paths it outputs.
2. Read `.codex/prompts/speckit.plan.md` and `.specify/templates/plan-template.md`.
3. Write `plan.md`, filling all sections and documenting tradeoffs.
4. Create supporting artifacts:
   - `research.md` for unknowns and decisions
   - `data-model.md` for entities and relationships
   - `contracts/` for API/interface contracts
   - `quickstart.md` for developer setup and verification
5. Ensure the plan references Linear issue(s) and constitution requirements.
6. Stop and report paths, unresolved questions, and readiness for tasks.

## Output

- `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Example prompts

- "Generate the plan bundle for ZOL-123 from spec.md."
- "Create plan.md, data-model.md, contracts/, research.md, and quickstart.md for ZOL-456."
