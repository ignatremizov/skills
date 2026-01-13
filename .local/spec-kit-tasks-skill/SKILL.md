---
name: spec-kit-tasks-skill
description: Produce tasks.md from the plan bundle. Use after plan.md and supporting artifacts are complete.
---

# Spec-Kit Tasks Phase

Generate a dependency-ordered task list.

## Prerequisites

- `plan.md` and supporting artifacts exist.

## Steps

1. Read `plan.md`, `data-model.md`, `contracts/`, `research.md`, and `quickstart.md`.
2. Use `.codex/prompts/speckit.tasks.md` and `.specify/templates/tasks-template.md`.
3. Create `tasks.md` with small, testable tasks and explicit dependencies.
4. Ensure each task maps back to requirements or Linear acceptance criteria.
5. Stop and report the task file path and any gaps.

## Output

- `tasks.md`

## Example prompts

- "Break the plan into tasks for ZOL-123 and write tasks.md."
- "Generate tasks mapped to ZOL-456 acceptance criteria."
