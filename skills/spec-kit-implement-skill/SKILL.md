---
name: spec-kit-implement-skill
description: Execute tasks.md in order and update task checkboxes. Use after analysis is clean or issues are accepted.
---

# Spec-Kit Implement Phase

Execute `tasks.md` end-to-end with progress and validation.

## Inputs

- Implementation scope from supervisor/user (`$ARGUMENTS` equivalent)

## Prerequisites

- `tasks.md` exists for active feature
- Analysis completed or explicitly waived

## Steps

1. Resolve implementation paths.
   - Run `{$HOME,.}/.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`.
   - Parse `FEATURE_DIR` and available docs.
2. Checklist gate (if `FEATURE_DIR/checklists/` exists).
   - Count total/completed/incomplete checkbox items per checklist.
   - If any checklist has incomplete items, stop and ask whether to proceed.
3. Load implementation context.
   - Required: `tasks.md`, `plan.md`
   - Optional: `data-model.md`, `contracts/`, `research.md`, `quickstart.md`
4. Verify project ignore/config hygiene based on detected tech.
   - Ensure required ignore patterns/files are present when relevant.
5. Parse tasks and execution graph.
   - Read IDs, phases, dependencies, `[P]` markers, and file targets.
6. Execute tasks phase-by-phase.
   - Respect sequential dependencies.
   - Execute `[P]` tasks in parallel only when file/dependency-safe.
   - Prefer tests before implementation where the plan/spec requests it.
7. Track progress and update tasks.
   - Mark completed tasks as `[X]` in `tasks.md`.
   - Report failures with next actionable step.
8. Validate completion.
   - Confirm required tasks done.
   - Confirm implementation aligns to spec and plan.
   - Run relevant tests/checks where possible.

## Quality rules

- Do not silently skip failed mandatory tasks.
- Keep implementation aligned with task order unless explicitly reprioritized.
- Preserve atomic progress by updating `tasks.md` as tasks complete.

## Output

- Code changes + updated `tasks.md`
- Progress summary with any blockers

## Example prompts

- "Implement next unchecked tasks for ZOL-123 and update tasks.md."
- "Execute tasks for ZOL-456 phase-by-phase and stop on spec/plan gaps."
