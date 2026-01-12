---
name: spec-kit-specify-skill
description: Create or update .specify/specs/NNN-feature-name/spec.md using the Spec-Kit spec template. Use when drafting a feature spec or linking to Linear.
---

# Spec-Kit Specify Phase

Produce `spec.md` for the current feature.

## Inputs

- Feature description from the supervisor
- Constitution and `AGENTS.md`
- Linear issue(s) if Linear is the source of truth

## Steps

1. Ensure the feature directory exists at `.specify/specs/NNN-feature-name/`.
   - If missing, ask the supervisor to create it or run `.specify/scripts/bash/create-new-feature.sh --json "<feature description>"`.
2. Read `.specify/templates/spec-template.md` and `.specify/templates/commands/specify.md`.
3. Write `spec.md`:
   - If Linear is the source of truth, keep the spec lightweight and link to the issue(s).
   - Include user stories, acceptance scenarios, requirements, and success criteria.
4. Add or update a "## Clarifications" section placeholder.
5. Stop and report the path and any open questions.

## Output

- `.specify/specs/NNN-feature-name/spec.md`

## Example prompts

- "Create spec.md for 004-user-invite and link ZOL-123 as the source of truth."
- "Draft a tech-agnostic spec for ZOL-456 using the Spec-Kit template."
