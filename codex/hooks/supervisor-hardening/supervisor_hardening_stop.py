#!/usr/bin/env python3
"""Stop hook for supervisor-hardening flows."""

from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path


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


def find_repo_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / ".codex").exists():
            return candidate
    return None


def session_key_from_transcript_path(transcript_path: str) -> str:
    return hashlib.sha256(transcript_path.encode("utf-8")).hexdigest()[:24]


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
    return any(token in text for token in COMPLETION_HINTS)


def gather_prompts(state: dict) -> list[str]:
    if state.get("mode") != "supervisor-hardening":
        return []

    prompts: list[str] = []

    pending_reviews = state.get("pending_reviews")
    if isinstance(pending_reviews, list) and pending_reviews:
        prompts.append(
            "Continue the supervisor-hardening workflow. "
            f"The following streams are not reviewer-green yet: {', '.join(map(str, pending_reviews))}. "
            "Finish their reviewer loops before concluding."
        )

    quality_gate = state.get("quality_gate")
    if not isinstance(quality_gate, dict):
        prompts.append(
            "Continue the supervisor-hardening workflow. "
            "Run `quality-gate-hardening` and record its result in the current session flow-state file before concluding."
        )
        return prompts

    status = quality_gate.get("status")
    if status in (None, "", "pending"):
        prompts.append(
            "Continue the supervisor-hardening workflow. "
            "Run `quality-gate-hardening` and record whether the hardening is sufficient before concluding."
        )
    elif status in ("needs_followup", "followup_required", "at_risk"):
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
