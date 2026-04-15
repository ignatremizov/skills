#!/usr/bin/env python3
"""Stop hook for session-scoped Spec-Kit flows."""

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
    "ready",
    "unblocked",
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
    "not ready",
    "not unblocked",
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


def count_unchecked_tasks(tasks_path: Path) -> int:
    if not tasks_path.is_file():
        return 0
    return sum(
        1
        for line in tasks_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("- [ ]")
    )


def gather_reasons(state: dict) -> list[str]:
    if state.get("mode") != "spec-kit":
        return []

    reasons: list[str] = []
    phase = state.get("phase") or "current"

    required_artifacts = state.get("required_artifacts")
    if isinstance(required_artifacts, list):
        for artifact_value in required_artifacts:
            artifact = Path(str(artifact_value))
            if not artifact.exists():
                reasons.append(
                    "Continue the active Spec-Kit workflow. "
                    f"The required artifact `{artifact}` for phase `{phase}` is missing."
                )
            elif artifact.is_file() and artifact.stat().st_size == 0:
                reasons.append(
                    "Continue the active Spec-Kit workflow. "
                    f"The required artifact `{artifact}` for phase `{phase}` is still empty."
                )

    task_paths = state.get("task_paths")
    if isinstance(task_paths, list):
        for task_path_value in task_paths:
            task_path = Path(str(task_path_value))
            if not task_path.is_file():
                reasons.append(
                    "Continue the active Spec-Kit workflow. "
                    f"The tracked task checklist `{task_path}` is missing."
                )
                continue
            unchecked = count_unchecked_tasks(task_path)
            if unchecked > 0:
                reasons.append(
                    "Continue the active Spec-Kit workflow. "
                    f"`{task_path}` still has {unchecked} unchecked task item(s). "
                    "Complete and check off the remaining tasks, or update session state so this checklist is no longer tracked "
                    "(for example by using `write-spec-kit-state.py --clear-task-paths` or rewriting `--task-path`)."
                )

    return reasons


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

    reasons = gather_reasons(state)
    if not reasons:
        return 0

    if payload.get("stop_hook_active"):
        print(
            json.dumps(
                {
                    "systemMessage": "Spec-Kit stop hook saw an already-blocked continuation pass and is surfacing warnings without blocking again.",
                }
            )
        )
        return 0

    print(
        json.dumps(
            {
                "systemMessage": "Spec-Kit stop hook requesting continuation.",
                "decision": "block",
                "reason": "\n\n".join(reasons),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
