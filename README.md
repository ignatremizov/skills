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


## Codex compaction prompt (autocompact.md)

This repo also includes a Codex compaction prompt file at `autocompact.md`. It controls how Codex writes a high-fidelity checkpoint during `/compact` and auto-compaction.

### Install

1) Symlink the prompt into `~/.codex/docs/` (recommended):

```sh
mkdir -p ~/.codex/docs
ln -sfn ~/code/skills/autocompact.md ~/.codex/docs/autocompact.md
```

2) Point Codex at it via `~/.codex/config.toml`:

```toml
# Use an absolute path if `~` expansion does not work in your build.
experimental_compact_prompt_file = "~/.codex/docs/autocompact.md"

[features]
# Required for Codex to use your local prompt file (remote compaction typically ignores it).
remote_compaction = false
```

3) Restart Codex.

### Notes

- If you keep `remote_compaction = true`, Codex may ignore `experimental_compact_prompt_file`.

## Codex agent config

For custom agent roles, prefer pointing `~/.codex/config.toml` directly at the source manifests in your checkout rather than generated copies.

Example:

```toml
[agents.reviewer]
description = "Default reviewer preset"
config_file = "<SKILLS_CHECKOUT>/.local/reviewer/agent.toml"
```

The repo includes reusable snippets in [`.local/agent_roles_config_snippets.toml`](/home/ignat/code/skills/.local/agent_roles_config_snippets.toml). Replace `<SKILLS_CHECKOUT>` with your local checkout path and paste the needed blocks into `~/.codex/config.toml`.

## Suggested workflows by skill

Local skills in `.local/` are repo-specific. Treat them as the source of truth for custom Codex agent manifests, and expose shared skill folders to tools via `~/.agents/skills`.

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

Recommended local setup:

1. Symlink the skill folders you want to share into `~/.agents/skills/`.
2. Point `~/.codex/config.toml` agent `config_file` entries at `<SKILLS_CHECKOUT>/.local/.../agent.toml`.
3. Use `~/.codex/skills/` only for Codex-specific installed skill trees such as `.system`, `.local`, or other private/non-repo skills.

#### Hardening Workflow

For non-trivial PRs, prefer a post-coder hardening phase instead of relying on one final general review pass.

Default flow:

1. Main implementation agent completes the feature slice.
2. `supervisor-hardening` classifies the changed area and selects the minimum useful `coder-hardening-*` agents.
3. Each hardening stream is validated by the base `reviewer` with area-specific additional instructions.
4. `quality-gate-hardening` scores the relevant areas (`0-100`) and decides whether one more targeted hardening pass is still warranted.
5. If quality-gate requests another area, run that one extra hardening stream, then re-run quality-gate.
6. Run a final combined reviewer pass only when multiple hardening areas interacted or the supervisor wants one last integration check.

Typical hardening order:

- `schema`
- `auth`
- `idempotency`
- `query`
- `money`
- `contract`
- `source-of-truth`
- `async-ui`
- `a11y`

Typical combinations:

- backend API + migration: `schema -> contract`
- backend state machine / reconciliation: `idempotency -> query -> money`
- auth/recovery flow: `auth -> contract`
- frontend data-heavy screen: `source-of-truth -> async-ui`
- frontend custom control: `source-of-truth -> a11y`
- transfer/balance UI: `money -> source-of-truth -> async-ui`

Example invocations:

- Backend PR:
  - "Use `supervisor-hardening` on this `svc` change before PR. The diff touches a migration, a new API response shape, and a state transition. Choose the minimum useful hardening areas, run the streams, then have `quality-gate-hardening` decide whether more hardening is still needed."
- Frontend PR:
  - "Use `supervisor-hardening` on this `emi-frontend` diff before PR. The change adds a custom dropdown and new async data loading. Pick the right hardening agents, validate each stream with reviewer, then run `quality-gate-hardening` and stop only if its confidence is high enough."

Skip the hardening workflow for trivial, tightly bounded diffs where the main coder plus a normal reviewer pass is already proportionate.

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
