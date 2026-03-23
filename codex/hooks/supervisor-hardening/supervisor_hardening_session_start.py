#!/usr/bin/env python3
"""Session-start hook for supervisor-hardening flows."""

from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path


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


def build_context(state: dict, source: str) -> str | None:
    if state.get("mode") != "supervisor-hardening":
        return None

    lines = [
        "Supervisor-hardening hook context:",
        f"- session source: {source}",
    ]

    if state.get("pr"):
        lines.append(f"- PR: {state['pr']}")
    if state.get("branch"):
        lines.append(f"- branch: {state['branch']}")
    if state.get("session_key"):
        lines.append(f"- session key: {state['session_key']}")

    completed = state.get("completed_areas")
    if isinstance(completed, list) and completed:
        lines.append(f"- completed hardening areas: {', '.join(map(str, completed))}")

    quality_gate = state.get("quality_gate")
    if isinstance(quality_gate, dict):
        status = quality_gate.get("status")
        if status:
            lines.append(f"- quality-gate status: {status}")
        recommended = quality_gate.get("recommended_area")
        if recommended:
            lines.append(f"- quality-gate recommended area: {recommended}")

    pending_reviews = state.get("pending_reviews")
    if isinstance(pending_reviews, list) and pending_reviews:
        lines.append(f"- pending reviewer-green streams: {', '.join(map(str, pending_reviews))}")

    lines.append(
        "- do not conclude supervisor-hardening until quality-gate-hardening has run and any requested follow-up area is addressed"
    )
    return "\n".join(lines)


def main() -> int:
    payload = json.load(sys.stdin)
    cwd = Path(payload.get("cwd") or ".")
    repo_root = find_repo_root(cwd)
    if repo_root is None:
        return 0

    state = load_flow_state(repo_root, payload.get("transcript_path"))
    if not state:
        return 0

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
