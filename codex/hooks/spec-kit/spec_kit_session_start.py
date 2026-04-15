#!/usr/bin/env python3
"""Session-start hook for session-scoped Spec-Kit flows."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HOOK_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOK_SCRIPT_DIR))
sys.path.insert(0, str(HOOK_SCRIPT_DIR.parent))

from hook_utils import find_repo_root, session_key_from_transcript_path


MAX_CONTEXT_ITEMS = 5


def read_state(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def load_flow_state(repo_root: Path, transcript_path: str | None) -> tuple[dict | None, Path | None]:
    state_dir = repo_root / ".codex" / "flow-state"
    if transcript_path:
        session_key = session_key_from_transcript_path(transcript_path)
        path = state_dir / "by-session" / f"{session_key}.json"
        data = read_state(path)
        if data:
            return data, path
    return None, None


def persist_session_state(repo_root: Path, transcript_path: str | None, state: dict, source_path: Path | None) -> None:
    if not transcript_path:
        return
    session_key = session_key_from_transcript_path(transcript_path)
    target_path = repo_root / ".codex" / "flow-state" / "by-session" / f"{session_key}.json"
    payload = dict(state)
    payload["session_key"] = session_key
    payload["transcript_path"] = transcript_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if source_path and source_path != target_path and source_path.name == "spec-kit-bootstrap.json":
        try:
            source_path.unlink()
        except Exception:
            pass


def count_unchecked_tasks(tasks_path: Path) -> int:
    if not tasks_path.is_file():
        return 0
    return sum(
        1
        for line in tasks_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("- [ ]")
    )


def build_context(state: dict, source: str) -> str | None:
    if state.get("mode") != "spec-kit":
        return None

    lines = [
        "Spec-Kit hook context:",
        f"- session source: {source}",
    ]
    if state.get("feature_id"):
        lines.append(f"- feature id: {state['feature_id']}")
    if state.get("phase"):
        lines.append(f"- active phase: {state['phase']}")

    required_artifacts = state.get("required_artifacts")
    if isinstance(required_artifacts, list) and required_artifacts:
        lines.append("- required artifacts:")
        for artifact in required_artifacts[:MAX_CONTEXT_ITEMS]:
            lines.append(f"  - {artifact}")
        if len(required_artifacts) > MAX_CONTEXT_ITEMS:
            lines.append(f"  - ... {len(required_artifacts) - MAX_CONTEXT_ITEMS} more")

    task_paths = state.get("task_paths")
    if isinstance(task_paths, list) and task_paths:
        lines.append("- tracked task paths:")
        for task_path_value in task_paths[:MAX_CONTEXT_ITEMS]:
            task_path = Path(str(task_path_value))
            if task_path.is_file():
                lines.append(
                    f"  - {task_path}: {count_unchecked_tasks(task_path)} unchecked task item(s)"
                )
            else:
                lines.append(f"  - {task_path}: missing")
        if len(task_paths) > MAX_CONTEXT_ITEMS:
            lines.append(f"  - ... {len(task_paths) - MAX_CONTEXT_ITEMS} more")

    lines.append(
        "- if you conclude a Spec-Kit phase is complete, the declared required artifacts for this supervisor session must actually exist on disk"
    )
    lines.append(
        "- if any declared task checklist for this supervisor session still has unchecked boxes, do not claim the implementation is complete"
    )
    return "\n".join(lines)


def is_valid_bootstrap_state(state: dict | None) -> bool:
    return state is not None and state.get("mode") == "spec-kit"


def main() -> int:
    payload = json.load(sys.stdin)
    cwd = Path(payload.get("cwd") or ".")
    repo_root = find_repo_root(cwd)
    if repo_root is None:
        return 0

    state, source_path = load_flow_state(repo_root, payload.get("transcript_path"))
    bootstrap_path = repo_root / ".codex" / "flow-state" / "spec-kit-bootstrap.json"
    bootstrap_state = read_state(bootstrap_path)
    bootstrap_can_seed_session = (
        is_valid_bootstrap_state(bootstrap_state)
        and source_path is None
        and bool(payload.get("transcript_path"))
    )
    if bootstrap_can_seed_session:
        state = bootstrap_state
        source_path = bootstrap_path
    if not state:
        return 0
    persist_session_state(repo_root, payload.get("transcript_path"), state, source_path)

    context = build_context(state, payload.get("source", "startup"))
    if not context:
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
