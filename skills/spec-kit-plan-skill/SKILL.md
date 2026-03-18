---
name: spec-kit-plan-skill
description: Generate the Spec-Kit plan bundle (plan.md, data-model.md, contracts, research.md, quickstart.md) from spec.md.
---

# Spec-Kit Plan Phase

Produce the technical plan bundle for the active feature.

## Inputs

- Planning constraints from supervisor/user (`$ARGUMENTS` equivalent)

## Prerequisites

- `spec.md` exists and is sufficiently clear
- Constitution is available
- `{$HOME,.}/.specify/templates/plan-template.md` exists

## Steps

1. Setup plan paths.
   - Run `{$HOME,.}/.specify/scripts/bash/setup-plan.sh --json`.
   - Parse and keep:
     - `FEATURE_SPEC`
     - `IMPL_PLAN`
     - `SPECS_DIR`
     - `BRANCH`
2. Load context.
   - Read `FEATURE_SPEC`.
   - Read `specs/constitution.md` (fallback: `.specify/memory/constitution.md` while migrating).
   - Read plan template and this rubric.
3. Ensure `plan.md` is templated when missing/empty.
   - Run:
     - `../spec-kit-skill/scripts/copy-template.sh --name plan-template.md --to <IMPL_PLAN> --root .`
4. Fill `plan.md` completely.
   - Technical context with explicit unknowns (`NEEDS CLARIFICATION`).
   - Constitution check and design gates.
   - Tradeoffs and constraints.
5. Phase 0: research.
   - Resolve unknowns into `research.md` with:
     - Decision
     - Rationale
     - Alternatives considered
6. Phase 1: design artifacts.
   - Create `data-model.md` (entities, fields, relationships, state transitions).
   - Create `contracts/` for APIs/interfaces.
   - Create `quickstart.md` for setup and verification flow.
7. Re-evaluate constitution alignment after design.
   - Flag unresolved violations as blockers.
8. Stop and report.
   - Branch, `plan.md` path, produced artifacts, unresolved questions.

## Quality rules

- Do not leave unresolved core unknowns in final plan.
- Fail fast on unjustified constitution violations.
- Keep artifacts consistent with spec acceptance criteria and source-of-truth issue links.

## Output

- `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Example prompts

- "Generate the full plan bundle for ZOL-123 from spec.md."
- "Create plan/design artifacts for ZOL-456 and include constitution gates."
