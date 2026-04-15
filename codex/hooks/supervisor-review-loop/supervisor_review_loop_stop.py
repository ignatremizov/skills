#!/usr/bin/env python3
"""Stop hook for supervisor-review-loop flows."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HOOK_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOK_SCRIPT_DIR))
sys.path.insert(0, str(HOOK_SCRIPT_DIR.parent))

from hook_utils import contains_phrase, find_repo_root, session_key_from_transcript_path


COMPLETION_HINTS = (
    "done",
    "completed",
    "complete",
    "finished",
    "all set",
    "ready for review",
    "ready to conclude",
)

NEGATED_COMPLETION_HINTS = (
    "not done",
    "not completed",
    "not complete",
    "isn't done",
    "isn't complete",
    "is not done",
    "is not complete",
    "incomplete",
    "not ready for review",
    "not ready to conclude",
)

def load_flow_state(repo_root: Path, transcript_path: str | None) -> dict | None:
    if not transcript_path:
        return None
    session_key = session_key_from_transcript_path(transcript_path)
    path = repo_root / ".codex" / "flow-state" / "by-session" / f"{session_key}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def looks_like_completion(last_assistant_message: str | None) -> bool:
    if not last_assistant_message:
        return False
    text = last_assistant_message.lower()
    if any(contains_phrase(text, phrase) for phrase in NEGATED_COMPLETION_HINTS):
        return False
    return any(contains_phrase(text, phrase) for phrase in COMPLETION_HINTS)


def gather_prompts(state: dict) -> list[str]:
    if state.get("mode") != "supervisor-review-loop":
        return []

    pending_reviews = state.get("pending_reviews")
    if isinstance(pending_reviews, list) and pending_reviews:
        prompts = [
            "Continue the supervisor-review-loop workflow. "
            f"The following streams still need fresh review-loop closure: {', '.join(map(str, pending_reviews))}. "
            "Finish their reviewer loops and clear the pending review state before concluding."
        ]
    else:
        prompts = []

    must_close_findings = state.get("must_close_findings")
    if isinstance(must_close_findings, list) and must_close_findings:
        sample = "\n".join(f"- {finding}" for finding in must_close_findings[:5])
        prompts.append(
            "Continue the supervisor-review-loop workflow. "
            "There are recorded must-close reviewer findings that have not been cleared. "
            "Fix or explicitly resolve them, rerun a fresh reviewer on the latest patch set, and clear the must-close finding state before concluding."
            f"\n\nRecorded must-close findings:\n{sample}"
        )

    return prompts


def main() -> int:
    payload = json.load(sys.stdin)
    cwd = Path(payload.get("cwd") or ".")
    repo_root = find_repo_root(cwd)
    if repo_root is None:
        return 0

    state = load_flow_state(repo_root, payload.get("transcript_path"))
    if not state:
        return 0

    if not looks_like_completion(payload.get("last_assistant_message")):
        return 0

    prompts = gather_prompts(state)
    if not prompts:
        return 0

    if payload.get("stop_hook_active"):
        print(
            json.dumps(
                {
                    "systemMessage": "Supervisor-review-loop stop hook saw an already-blocked continuation pass and stayed calm to avoid a loop.",
                }
            )
        )
        return 0

    print(
        json.dumps(
            {
                "systemMessage": "Supervisor-review-loop stop hook requesting continuation.",
                "decision": "block",
                "reason": "\n\n".join(prompts),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
