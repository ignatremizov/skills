## COMPACTION EVENT ##
Your context will be truncated. Another agent will continue using ONLY your output. You are performing a CONTEXT CHECKPOINT COMPACTION (an "attention update") for a long-running task.

Goal:
- Produce a compact, high-fidelity checkpoint that preserves task intent and execution reality so the next agent can continue correctly without re-reading the whole chat.
- Keep every detail that would change future decisions. Drop conversational debris.

Hard requirements (do not violate):
- Fact safety: Do NOT invent facts (files, commands, outputs, errors, timings). If unknown, write [UNKNOWN].
- Verbatim correctness: anything marked VERBATIM must be exact text (no edits, no paraphrase) inside a code block.
- Preserve tool/command reality: include the most important recent commands/tool calls (exact command lines / file paths) and their outcomes (success/failure + 1-3 key lines).
- Preserve repo state: files changed, tests run, and any errors fixed.
- Be concise and fast: keep only high-signal outputs (final results, error messages, key measurements). Do not write long logs.

"Attention update" heuristic (what to keep vs drop):
- KEEP: objectives, constraints/preferences, decisions+rationale, state of work, what changed (files), what ran (commands/tests) and results, known gotchas, and the next action to take.
- DROP: repeated back-and-forth updates, speculative ideas not acted on, verbose tool output, and intermediate steps that didn't affect outcomes.

Discussion context policy:
- You MAY include a [DISCUSSION] block.
- Prefer a concise paraphrase of the last user requests and assistant responses.
- Only quote verbatim if exact wording is required (commands, file paths, error messages) and keep quotes minimal.
- Deduplicate: if messages are duplicated/redundant, keep only the single most concise version. MUST NOT repeat the same block or message multiple times in the compaction output.

Output format guidance:
- Prefer the standard sections below, but you MAY rename headings, add new sections, or reorder sections if it improves fidelity.

Recommended template (adapt as needed):

(DISCUSSION SHOULD include concise assistant replies, if any, in addition to user messages.)

[DISCUSSION]
```text
<summarized last user/assistant message(s), deduplicated>
```
(note: Terminate the block with [END_OF_DISCUSSION]. MUST NOT write more than 200 lines. If discussion is already under 200 lines, include it all.)

[TASK_OVERVIEW]
- Objective:
- Success criteria:
- Important context (if needed):
- Sub-tasks completed so far (if any):

[CONSTRAINTS_AND_PREFERENCES]
- User preferences:
- Policies/constraints:

[CURRENT_STATUS]
- Git repo state (as relevant): <branch, stash, dirty/clean, staged/unstaged>
- What is complete:
- What is in progress:
- What is pending/blocked:

[KEY_DECISIONS]
- Decision -> rationale -> consequence:
(repeat as needed)

[ASSUMPTIONS]
- Assumption -> basis -> impact:
(repeat as needed)

[REFERENCES]
List only the most important recent actions. Each bullet must include an exact artifact/command and its outcome.
- Command(s): `<command>` -> <result + key output/error line>
- Tool calls: <tool> <args> -> <result>
- Files: <paths + what changed/why>

[OPEN_QUESTIONS_AND_GOTCHAS] (if any - omit if none)
- Unknowns:
- Risks:

[NEXT_STEPS]
1) <next action>
2) <next action>
...
(or, reference an existing plan file if exists and step number)

Rules:
- If there are multiple parallel objectives and tasks, keep them separated inside their own CONTEXT CHECKPOINT COMPACTION groups (label them clearly) instead of mixing details.
- Prefer short, information-dense bullets. You may adjust headings and sections as necessary. The goal is for the next agent to quickly grasp the situation and continue effectively.
