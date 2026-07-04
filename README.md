# Agent Skills

Agent Skills are folders of instructions, scripts, and resources that AI agents can discover and use to perform at specific tasks. Write once, use everywhere.

Codex uses skills to help package capabilities that teams and individuals can use to complete specific tasks in a repeatable way. This repository catalogs skills for use and distribution with Codex.

Learn more:
- [Using skills in Codex](https://developers.openai.com/codex/skills)
- [Create custom skills in Codex](https://developers.openai.com/codex/skills/create-skill)
- [Agent Skills open standard](https://agentskills.io)

## Source layout

This checkout is a source repo, not a mirror of any runtime directory.

- `skills/`: portable skill sources that can be synced into `~/.agents/skills/` and optionally `~/.codex/skills/`
- `codex/agents/`: Codex-only agent manifests referenced directly from `~/.codex/config.toml`
- `codex/hooks/`: Codex-only hook bundles that can be installed into a repo or user `.codex/`
- `codex/config/`: reusable config snippets for Codex agent registration
- `codex/scripts/`: Codex-specific helper/install scripts
- `openai/`: personal OpenAI/Codex prompt profiles, including full base-instruction replacements
- `update-skills.sh`: portable skill sync entrypoint

## Installing a skill

Skills in [`skills/.system`](skills/.system/) are automatically installed in the latest version of Codex.

To install curated skills from [`skills/.curated`](skills/.curated/), you can use the `$skill-installer` inside Codex.

Curated skills can be installed by name (defaults to `skills/.curated`):

```
$skill-installer gh-address-comments
```

You can also provide the GitHub directory URL for a curated skill. For example:

```
$skill-installer install https://github.com/openai/skills/tree/main/skills/.curated/linear
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

## Codex base-instruction profiles

This repo keeps personal Codex base-instruction replacements under `openai/<model>/`.
Use these when you want different Codex operating modes, such as coding, writing, or research,
while sharing the same Codex home, auth, rollouts, skills, and MCP setup.

Example profile files:

- `openai/gpt-5.5/code.md`
- `openai/gpt-5.5/writing.md`
- `openai/gpt-5.5/research.md`
- `openai/gpt-5.5/reporting.md`
- `openai/gpt-5.5/upstream.md` as the upstream baseline snapshot

Create a profile config in `~/.codex/<profile>.config.toml`:

```toml
model = "gpt-5.5"
model_instructions_file = "/Users/iremizov/code/skills/openai/gpt-5.5/code.md"
```

Then launch Codex with that profile:

```sh
codex -p code
```

Repeat the same pattern for other profiles:

```toml
# ~/.codex/writing.config.toml
model = "gpt-5.5"
model_instructions_file = "/Users/iremizov/code/skills/openai/gpt-5.5/writing.md"
```

```sh
codex -p writing
```

Notes:

- `model_instructions_file` replaces the model's built-in base instructions for the session. Keep any base-level Codex operating guidance you rely on in the replacement file.
- Runtime developer blocks, tool schemas, permissions/app/skills instructions, `AGENTS.md`, and selected skills are still injected separately by Codex.
- Normal `spawn_agent` subagents inherit the parent session's resolved base instructions, so a session launched with `codex -p code` spawns agents with the same `code.md` base prompt unless an agent role explicitly overrides instructions.
- Disable domain skills that do not fit a profile. For example, writing profiles should usually disable coding-specific skills so their summaries do not steer writing tasks:

  ```toml
  [[skills.config]]
  name = "frontend-coding"
  enabled = false

  [[skills.config]]
  name = "backend-coding"
  enabled = false
  ```

- Keep global profile prompts broad. For writing projects, put genre, voice, explicitness, taboo/acceptable content, humor level, and taste boundaries in the project's `AGENTS.md` so each project can define its own style.
- Use absolute paths in profile configs for predictable behavior across working directories.

## Codex agent config

For custom agent roles, prefer pointing `~/.codex/config.toml` directly at the source manifests in your checkout rather than generated copies.

Example:

```toml
[agents.reviewer]
description = "Default reviewer preset"
config_file = "<SKILLS_CHECKOUT>/codex/agents/reviewer.toml"

[agents.reviewer_exhaustive]
description = "Optional high-recall reviewer preset for final sweeps"
config_file = "<SKILLS_CHECKOUT>/codex/agents/reviewer-exhaustive.toml"
```

Helpers:

- `codex/config/agent_roles_config_snippets.toml`: copy/pasteable role blocks
- `codex/scripts/install-codex-agents.sh`: installs a managed agent block into a Codex config
- `codex/scripts/codex_context_toggle.py`: enables/disables skills and agents with managed config blocks

## Codex hooks

Hook bundles in this repo are installed from the skills repo checkout, not from an arbitrary target repo.

Use the scripts from your local skills checkout, for example:

```sh
<SKILLS_REPO>/codex/scripts/install-codex-hooks.sh --hook-set spec-kit --root /path/to/target-worktree
<SKILLS_REPO>/codex/scripts/install-codex-hooks.sh --hook-set supervisor-review-loop --root /path/to/target-worktree
<SKILLS_REPO>/codex/scripts/install-codex-hooks.sh --hook-set supervisor-hardening --root /path/to/target-worktree
<SKILLS_REPO>/codex/scripts/install-codex-hooks.sh --hook-set ghc-review-supervisor --root /path/to/target-worktree
```

For per-session hook state, use:

```sh
python3 <SKILLS_REPO>/codex/scripts/write-flow-state.py ...
```

For `spec-kit`, prefer:

```sh
python3 <SKILLS_REPO>/codex/scripts/write-spec-kit-state.py ...
```

Record the supervisor session's active phase plus the exact required artifact and task-checklist paths for that session. Those paths may be absolute and may point into sibling repos or worktrees. Bootstrap state written without `--transcript-path` can seed a supervisor session that does not yet have transcript-keyed state; once a session exists, update it with `--transcript-path "$TRANSCRIPT_PATH"` so another resumed session cannot consume the wrong bootstrap payload.

For `supervisor-review-loop`, use `python3 <SKILLS_REPO>/codex/scripts/write-flow-state.py --mode supervisor-review-loop ...` and keep `pending_reviews` aligned to streams that still need fresh reviewer closure. Persist exact must-close findings, deferred findings, and ignored-finding rationales in the same session state so resumes keep the real blocker context.

For `supervisor-hardening`, if a later hardening stream changes the patch after the last quality-gate result, mark that result stale in flow-state with `--quality-gate-needs-rerun true`. Recording a fresh quality-gate result clears that flag automatically. Record `--quality-gate-followup-mode must_close_now` only when the recommended area must be completed in the active PR; use `defer_to_followup_spec` for architectural or maintainability follow-up that should be recorded for later spec work instead of forced inline. Persist open must-close items with `--must-close-finding ...` and deferred follow-up items with `--deferred-finding ...`, then clear them explicitly when those items are closed or handed off. For a current `defer_to_followup_spec` gate result, record at least one `--deferred-finding ...` in the same or a later write so session state acknowledges that exact defer decision. Use `--clear-pending-reviews` when you need to explicitly clear the stored review-loop-closure list.

For `ghc-review-supervisor`, use `python3 <SKILLS_REPO>/codex/scripts/write-ghc-review-state.py ...` as a supervisor completion ledger, not as a mirror of the `ghc` cache. Keep remote review-thread contents and resolution truth in `ghc`; record only supervisor checkpoints and obligations such as refresh timestamps, unresolved-count snapshots, deduped fix groups, pending reviewer closures, must-close findings, deferred/ignored rationale, and post-push resolution verification.

Here `<SKILLS_REPO>` means your local checkout path, for example `~/code/skills`.

## Suggested workflows by skill

Treat `skills/` as the source of truth for portable skills. Sync them into `~/.agents/skills/` with:

```sh
./update-skills.sh
```

To also refresh `~/.codex/skills/`, use:

```sh
./update-skills.sh --codex
```

For Codex agent prompts whose `developer_instructions` are intentionally derived from skill text, refresh them with:

```sh
python3 codex/scripts/sync_agent_prompts.py
```

### Portable (`skills/`)

- `git-commit-style`: Draft commit messages after staging; summarize intent, behavioral impact, and testing in a repo-aligned format.
- `frontend-coding`: Frontend implementation and review guidance for UI, layout, interaction, accessibility, responsiveness, and visual polish.
- `backend-coding`: Backend implementation and review guidance for APIs, services, persistence, auth, telemetry, security/privacy, performance, and async/distributed flows.
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
- `codex-hooks`: Choose, install, disable, or uninstall Codex hook bundles and wire per-session flow-state for stateful hook enforcement.
- `claude-skill`: Hand off implementation or review to Claude Code headless mode; requires the `claude` CLI.
- `autonomous-skill`: Execute long-running, multi-session tasks with progress tracking in `.autonomous/`.

Recommended local setup:

1. Sync `skills/` into `~/.agents/skills/` with `./update-skills.sh`.
2. Point `~/.codex/config.toml` agent `config_file` entries at `<SKILLS_CHECKOUT>/codex/agents/*.toml`.
3. Use `<SKILLS_REPO>/codex/scripts/install-codex-hooks.sh --root /path/to/target-worktree` and point `--root` at the worktree or repo root where you want the repo-local `.codex/`.
4. Use `~/.codex/skills/` only for Codex runtime skill trees, not as the canonical source repo layout.

#### Hardening Workflow

For non-trivial PRs, prefer a post-coder hardening phase instead of relying on one final general review pass.

Default flow:

1. Main implementation agent completes the feature slice.
2. `supervisor-hardening` classifies the changed area and selects the minimum useful `coder-hardening-*` agents.
3. Each hardening stream is validated by the base `reviewer` with area-specific additional instructions.
4. `quality-gate-hardening` scores the relevant areas (`0-100`) and decides whether one more targeted hardening pass is still warranted.
5. If quality-gate marks another area `must_close_now`, run that one extra hardening stream, then re-run quality-gate. If it marks an area `defer_to_followup_spec`, record it for later work instead of expanding the active PR.
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

## License

The license of an individual skill can be found directly inside the skill's directory inside the `LICENSE.txt` file.
