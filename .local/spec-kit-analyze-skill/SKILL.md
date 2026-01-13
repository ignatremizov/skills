---
name: spec-kit-analyze-skill
description: Run a cross-artifact consistency check across spec.md, plan.md, and tasks.md before implementation.
---

# Spec-Kit Analyze Phase

Perform a read-only consistency check.

## Prerequisites

- `spec.md`, `plan.md`, and `tasks.md` exist.

## Steps

1. Read `spec.md`, `plan.md`, `tasks.md`, and the constitution.
2. Use `.codex/prompts/speckit.analyze.md` as the rubric.
3. Produce a prioritized report:
   - Critical issues first
   - Warnings second
   - Recommendations last
4. For each issue, propose the artifact to update.

## Output

- Analysis report (returned to supervisor)

## Example prompts

- "Analyze spec/plan/tasks for ZOL-123 and report critical gaps."
- "Check constitution alignment for ZOL-456 before implementation."
