---
name: spec-kit-constitution-skill
description: Draft or update .specify/memory/constitution.md for Spec-Kit. Use when establishing principles and sources of truth.
---

# Spec-Kit Constitution Phase

Create or update `.specify/memory/constitution.md` using the Spec-Kit template.

## Prerequisites

- `.specify/` exists (created via `specify init . --ai codex`).
- Review `AGENTS.md` and any existing standards.

## Steps

1. Read `.specify/memory/constitution.md` (template or existing).
2. Read `.codex/prompts/speckit.constitution.md` for required sections.
3. Write or update the constitution. Ensure "Sources of Truth" references:
   - Linear issue(s) or requirements tracker
   - `AGENTS.md` path for engineering standards
4. Stop and report the updated path and any missing info.

## Output

- `.specify/memory/constitution.md`

## Example prompts

- "Draft or update the constitution for ZOL-123 and reference AGENTS.md as a source of truth."
- "Refresh the Sources of Truth section for ZOL-456."
