#!/usr/bin/env python3
"""Session-start hook for ghc-review-supervisor flows."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HOOK_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOK_SCRIPT_DIR))
sys.path.insert(0, str(HOOK_SCRIPT_DIR.parent))

from hook_utils import find_repo_root, session_key_from_transcript_path


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
    if state.get("mode") != "ghc-review-supervisor":
        return None

    lines = [
        "GHC review supervisor hook context:",
        f"- session source: {source}",
    ]

    for key in ("repo", "pr", "branch", "session_key"):
        if state.get(key):
            lines.append(f"- {key}: {state[key]}")

    if isinstance(state.get("unresolved_threads"), int):
        lines.append(f"- unresolved threads: {state['unresolved_threads']}")

    if state.get("review_ready_after"):
        lines.append(f"- review ready after: {state['review_ready_after']}")
    if state.get("last_refresh_at"):
        lines.append(f"- last refresh at: {state['last_refresh_at']}")

    if state.get("dedupe_complete") is not None:
        lines.append(f"- dedupe complete: {state['dedupe_complete']}")

    pending_groups = state.get("pending_groups")
    if isinstance(pending_groups, list):
        lines.append(f"- pending groups: {len(pending_groups)}")

    pending_reviews = state.get("pending_reviews")
    if isinstance(pending_reviews, list) and pending_reviews:
        lines.append(f"- streams still in review-loop closure: {', '.join(map(str, pending_reviews))}")
    must_close_findings = state.get("must_close_findings")
    if isinstance(must_close_findings, list) and must_close_findings:
        lines.append("- must-close findings still recorded:")
        for finding in must_close_findings[:5]:
            lines.append(f"  - {finding}")
    deferred_findings = state.get("deferred_findings")
    if isinstance(deferred_findings, list) and deferred_findings:
        lines.append("- deferred findings recorded:")
        for finding in deferred_findings[:5]:
            lines.append(f"  - {finding}")
    ignored_rationales = state.get("ignored_finding_rationales")
    if isinstance(ignored_rationales, list) and ignored_rationales:
        lines.append("- ignored-finding rationales recorded:")
        for rationale in ignored_rationales[:5]:
            lines.append(f"  - {rationale}")

    if state.get("rerun_requested") is not None:
        lines.append(f"- re-review requested: {state['rerun_requested']}")

    lines.append(
        "- do not conclude ghc-review-supervisor until review refresh, dedupe/grouping, remaining fix groups, review-loop closure, and thread resolution state are all satisfied"
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
