# Agent Skills

Agent Skills are folders of instructions, scripts, and resources that AI agents can discover and use to perform at specific tasks. Write once, use everywhere.

Codex uses skills to help package capabilities that teams and individuals can use to complete specific tasks in a repeatable way. This repository catalogs skills for use and distribution with Codex.

Learn more:
- [Using skills in Codex](https://developers.openai.com/codex/skills)
- [Create custom skills in Codex](https://developers.openai.com/codex/skills/create-skill)
- [Agent Skills open standard](https://agentskills.io)

## Installing a skill

Skills in [`.system`](skills/.system/) are automatically installed in the latest version of Codex.

To install [curated](skills/.curated/) or [experimental](skills/.experimental/) skills, you can use the `$skill-installer` inside Codex.

Curated skills can be installed by name (defaults to `skills/.curated`):

```
$skill-installer gh-address-comments
```

For experimental skills, specify the skill folder. For example:

```
$skill-installer install the create-plan skill from the .experimental folder
```

Or provide the GitHub directory URL:

```
$skill-installer install https://github.com/openai/skills/tree/main/skills/.experimental/create-plan
```

After installing a skill, restart Codex to pick up new skills.

## Suggested workflows by skill

Local skills in `.local/` are repo-specific. Use them as overrides or add them to `~/.codex/skills` when you want the local behavior to take precedence.

### Local (`.local/`)

- `git-commit-style`: Draft commit messages after staging; summarize intent, behavioral impact, and testing in a repo-aligned format.
- `athena`: Run supervisor-led requirements → design → tasks for new features; writes `.athena/specs/<feature>/`.
- `spec-kit-skill`: Supervisor orchestration for Spec-Kit phases; spawns workers with explicit phase skills.
- `spec-kit-constitution-skill`: Draft or update `.specify/memory/constitution.md`.
- `spec-kit-specify-skill`: Create or update `.specify/specs/<feature>/spec.md`.
- `spec-kit-clarify-skill`: Generate clarifying questions and update `spec.md`.
- `spec-kit-plan-skill`: Produce the plan bundle (`plan.md`, `data-model.md`, `contracts/`, `research.md`, `quickstart.md`).
- `spec-kit-checklist-skill`: Generate requirements-quality checklists in `checklists/`.
- `spec-kit-tasks-skill`: Generate `tasks.md` from the plan bundle.
- `spec-kit-analyze-skill`: Cross-artifact consistency report before implementation.
- `spec-kit-implement-skill`: Execute `tasks.md` and update task checkboxes.
- `claude-skill`: Hand off implementation or review to Claude Code headless mode; requires the `claude` CLI.
- `autonomous-skill`: Execute long-running, multi-session tasks with progress tracking in `.autonomous/`.

### System (`skills/.system/`)

- `skill-creator`: Design or refine a skill with clear triggers, workflows, and helper assets.
- `skill-installer`: Install curated or remote skills into `~/.codex/skills` for repeatable use.

### Curated (`skills/.curated/`)

- `gh-address-comments`: Triage PR review threads, apply fixes, and resolve comments using `gh`.
- `gh-fix-ci`: Pull failing GitHub Actions logs, summarize failures, then propose and implement a fix plan.
- `notion-knowledge-capture`: Turn conversations into structured Notion pages (decisions, FAQs, how-tos).
- `notion-meeting-intelligence`: Prepare meeting agendas and pre-reads from Notion context.
- `notion-research-documentation`: Synthesize Notion research into briefs or comparison docs with citations.
- `notion-spec-to-implementation`: Convert Notion specs into implementation tasks with progress tracking.

### Experimental (`skills/.experimental/`)

- `create-plan`: Provide a concise, single plan when the user explicitly asks for one.
- `linear`: Read and update Linear issues and projects through the Linear MCP workflow.

## License

The license of an individual skill can be found directly inside the skill's directory inside the `LICENSE.txt` file.
