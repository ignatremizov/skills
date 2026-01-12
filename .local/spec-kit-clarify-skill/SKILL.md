---
name: spec-kit-clarify-skill
description: Generate clarifying questions and update spec.md. Use before planning when requirements are ambiguous.
---

# Spec-Kit Clarify Phase

Resolve ambiguities before planning.

## Prerequisites

- `spec.md` exists for the feature.
- Constitution is available.

## Steps

1. Read `spec.md` and `.specify/memory/constitution.md`.
2. Use `.specify/templates/commands/clarify.md` to craft up to 5 targeted questions.
3. If answers are available in context, update `spec.md` under "## Clarifications".
4. If answers are missing, return the questions and stop.
5. If Linear is the source of truth, mirror decisions back to the Linear issue.

## Output

- Updated `spec.md` with clarifications, or a question list to resolve.

## Example prompts

- "Generate up to five clarifying questions for ZOL-123 and update spec.md with any answers you can infer."
- "Add a Clarifications section for ZOL-456 and list unresolved questions."
