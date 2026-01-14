---
name: codex-exec
description: Spawn and manage codex exec sub-agent processes from a supervisor script, including capturing session ids, resuming sessions, and injecting skills/context. Use when you need to run ad-hoc questions, reviews, or focused worker tasks in separate exec sessions.
---

# Codex Exec

## Overview

Use `codex-exec` (wrapper for the `codex exec` CLI) to run short-lived sub-agent jobs and keep their session ids so the supervisor can resume or query them later.

## Workflow

1. Decide session strategy:
   - Use a new session for an independent task.
   - Resume an existing session for a follow-up on the same thread.
2. Build a tight prompt:
   - State role, scope, and expected output format.
   - Include relevant context, file paths, or constraints.
   - Include `$skill-name` tokens for CLI skill injection when needed.
3. Launch the sub-agent:
   - New: `codex-exec "prompt..."` (preferred) or `codex exec --json "prompt..."`.
   - Resume: `codex-exec resume <SESSION_ID> "follow-up..."`.
   - Review: `codex-exec review --uncommitted` (or other review flags).
4. Capture outputs and session id:
   - Wrapper: final message on stdout, `session id: ...` on stderr.
   - Raw JSON: parse `thread.started.thread_id` and the last `item.completed` with `type: agent_message`.
   - Direct exec: `codex exec ... 2>/dev/null` to suppress stderr reasoning/tool output when you do not need follow-ups or session ids.
5. Store supervisor state:
   - Map sub-agent name to session id, prompt, last response, and status.
   - Use the stored id for later `resume` calls.

## Skill injection and context

- CLI/TUI: include `$skill-name` in the prompt text so the subprocess loads that skill.
- App-server: include a `UserInput::Skill { name, path }` item alongside `UserInput::Text`.
- Skill content is injected as a separate user message; it does not replace the inline token.

## Working directory and config

- Set cwd: `codex-exec -C /path/to/repo "prompt..."`.
- Add writable roots: `codex-exec --add-dir /path "prompt..."`.
- Select model: `codex-exec -m gpt-5.2-codex "prompt..."` (code) or `codex-exec -m gpt-5-2 "prompt..."` (docs).
- Set reasoning effort: `codex-exec -c model_reasoning_effort=high "prompt..."`.
- Override config: `codex-exec -c key=value "prompt..."`.

## Model reference

- If you run the app server, the `model/list` endpoint returns available models (see `~/code/codex/codex-rs/app-server/README.md`).
- For a static reference, check the built-in presets in `~/code/codex/codex-rs/core/models.json` (may lag behind the service).

## When to spawn vs resume

- Spawn a new session for a new task or different role.
- Resume only when the follow-up depends on the same context/history.
- Avoid mixing unrelated tasks in a single session.

## Example prompts

- "Spawn a developer sub-agent to review changes in src/ and summarize risks. Use $git-commit-style."
- "Spawn a research sub-agent to summarize upstream docs for feature X in 3 bullets."
- "Resume session <ID> and answer: does the previous conclusion still hold after the new diff?"
