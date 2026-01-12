---
name: spec-kit-checklist-skill
description: Generate requirements-quality checklists for a feature using the Spec-Kit checklist template. Use after plan to validate spec clarity and completeness.
---

# Spec-Kit Checklist Phase

Create a requirements-quality checklist for the current feature. This is not an implementation test; it validates the clarity, completeness, and consistency of requirements.

## Prerequisites

- `.specify/` exists.
- `spec.md` exists for the feature.
- `plan.md` and `tasks.md` are recommended if available.

## Steps

1. Run `.specify/scripts/bash/check-prerequisites.sh --json` and capture `FEATURE_DIR` and `AVAILABLE_DOCS`.
2. Read `.specify/templates/commands/checklist.md` for the checklist rules.
3. Read `.specify/templates/checklist-template.md` for format.
4. Load only relevant context from `spec.md` (and `plan.md`/`tasks.md` if present).
5. Create `FEATURE_DIR/checklists/` if missing.
6. Write a domain checklist file (e.g., `ux.md`, `api.md`, `security.md`).
   - Never overwrite existing content.
   - If the file already exists, append new items or choose a new descriptive filename.
7. Ensure each item tests requirements quality (completeness/clarity/consistency/measurability), not implementation behavior.
8. Stop and report the checklist path, item count, focus areas, and any open questions.

## Output

- `FEATURE_DIR/checklists/<domain>.md`

## Example prompts

- "Create a security requirements checklist for ZOL-123."
- "Generate a UX requirements checklist for ZOL-456."
