#!/usr/bin/env python3
"""Stop hook for supervisor-hardening flows."""

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
    "ready for pr",
    "ready to open pr",
    "ready for review",
    "all set",
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
    "not ready for pr",
    "not ready to open pr",
    "not ready for review",
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
    if state.get("mode") != "supervisor-hardening":
        return []

    prompts: list[str] = []

    pending_reviews = state.get("pending_reviews")
    if isinstance(pending_reviews, list) and pending_reviews:
        prompts.append(
            "Continue the supervisor-hardening workflow. "
            f"The following streams still need review-loop closure: {', '.join(map(str, pending_reviews))}. "
            "Finish their reviewer loops and clear the pending review state before concluding."
        )

    must_close_findings = state.get("must_close_findings")
    if isinstance(must_close_findings, list) and must_close_findings:
        sample = "\n".join(f"- {finding}" for finding in must_close_findings[:5])
        prompts.append(
            "Continue the supervisor-hardening workflow. "
            "Recorded must-close findings are still outstanding in session state. Clear them only after the responsible stream has closed its review loop."
            f"\n\nRecorded must-close findings:\n{sample}"
        )

    quality_gate = state.get("quality_gate")
    if not isinstance(quality_gate, dict):
        prompts.append(
            "Continue the supervisor-hardening workflow. "
            "Run `quality-gate-hardening` and record its result in the current session flow-state file before concluding."
        )
        return prompts

    status = quality_gate.get("status")
    followup_mode = quality_gate.get("followup_mode")
    if quality_gate.get("needs_rerun"):
        prompts.append(
            "Continue the supervisor-hardening workflow. "
            "The recorded `quality-gate-hardening` result is stale for the latest patch state. Rerun it and record the updated result before concluding."
        )
        return prompts
    if status in (None, "", "pending"):
        prompts.append(
            "Continue the supervisor-hardening workflow. "
            "Run `quality-gate-hardening` and record whether the hardening is sufficient before concluding."
        )
    elif status in ("needs_followup", "followup_required", "at_risk"):
        if followup_mode == "defer_to_followup_spec":
            if not quality_gate.get("deferred_recorded"):
                prompts.append(
                    "Continue the supervisor-hardening workflow. "
                    "The current quality-gate defer-to-followup-spec decision has not been acknowledged in session state yet. Record the deferred finding or follow-up item for this gate decision before concluding."
                )
            return prompts
        recommended = quality_gate.get("recommended_area")
        if recommended:
            prompts.append(
                "Continue the supervisor-hardening workflow. "
                f"Run the recommended `{recommended}` hardening stream, then rerun or update `quality-gate-hardening` before concluding."
            )
        else:
            prompts.append(
                "Continue the supervisor-hardening workflow. "
                "Quality-gate still requires another hardening pass before concluding."
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
                    "systemMessage": "Supervisor-hardening stop hook saw an already-blocked continuation pass and stayed calm to avoid a loop.",
                }
            )
        )
        return 0

    print(
        json.dumps(
            {
                "systemMessage": "Supervisor-hardening stop hook requesting continuation.",
                "decision": "block",
                "reason": "\n\n".join(prompts),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
