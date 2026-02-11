---
name: spec-kit-constitution-skill
description: Draft or update specs/constitution.md for Spec-Kit. Use when establishing principles and sources of truth.
---

# Spec-Kit Constitution Phase

Create or update project governance in `specs/constitution.md`.

## Inputs

- Constitution changes from supervisor/user (`$ARGUMENTS` equivalent)

## Prerequisites

- `specs/` exists
- Constitution template or existing constitution is available

## Steps

1. Load current constitution source.
   - Preferred: `specs/constitution.md`
   - Fallback for migration: `.specify/memory/constitution.md`
2. Identify and resolve placeholders.
   - Replace all unresolved template tokens with concrete values.
   - If unknown, add explicit TODO with rationale.
3. Apply versioning and governance updates.
   - Use semantic version bump rules:
     - MAJOR: breaking governance/principle change
     - MINOR: new/expanded principle
     - PATCH: clarifications/wording
   - Keep dates in `YYYY-MM-DD`.
4. Ensure principle quality.
   - Principles must be declarative, testable, and non-ambiguous.
   - Sources of truth must explicitly reference:
     - requirements tracker (e.g., Linear)
     - `AGENTS.md` for engineering standards
5. Consistency propagation review.
   - Validate alignment with `{$HOME,.}/.specify/templates/spec-template.md`.
   - Validate alignment with `{$HOME,.}/.specify/templates/plan-template.md`.
   - Validate alignment with `{$HOME,.}/.specify/templates/tasks-template.md`.
   - Flag any required follow-up edits.
6. Add sync impact report comment at top.
   - Version old -> new
   - Modified/added/removed sections
   - Template sync status
   - Deferred TODOs
7. Write constitution to `specs/constitution.md`.
8. Stop and report.
   - New version and rationale.
   - Follow-up actions/files.

## Quality rules

- No unexplained bracket placeholders remain.
- Avoid vague language; prefer explicit MUST/SHOULD semantics with rationale.

## Output

- `specs/constitution.md`

## Example prompts

- "Draft or update constitution for ZOL-123 and align sources of truth."
- "Amend governance and bump version with rationale for ZOL-456."
