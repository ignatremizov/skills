#!/usr/bin/env python3
"""Stop hook for ghc-review-supervisor flows."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


COMPLETION_HINTS = (
    "done",
    "completed",
    "complete",
    "finished",
    "all set",
    "ready for review",
    "ready to re-request",
    "ready to rerun review",
    "ready to conclude",
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


def parse_dt(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def gather_prompts(state: dict) -> list[str]:
    if state.get("mode") != "ghc-review-supervisor":
        return []

    prompts: list[str] = []

    review_ready_after = parse_dt(state.get("review_ready_after"))
    if review_ready_after and datetime.now(timezone.utc) < review_ready_after:
        prompts.append(
            "Continue the ghc-review-supervisor workflow. "
            f"Wait until after {state['review_ready_after']} for reviews to land, then refresh `ghc` state before concluding."
        )

    if state.get("rerun_requested"):
        review_requested_at = parse_dt(state.get("review_requested_at"))
        last_refresh_at = parse_dt(state.get("last_refresh_at"))
        if last_refresh_at is None or (review_requested_at and last_refresh_at < review_requested_at):
            prompts.append(
                "Continue the ghc-review-supervisor workflow. "
                "A re-review was requested, but `ghc` has not been refreshed since that request. Refresh with `ghc get` or `ghc ids` before concluding."
            )

    unresolved_threads = state.get("unresolved_threads")
    dedupe_complete = state.get("dedupe_complete")
    pending_groups = state.get("pending_groups")
    if isinstance(unresolved_threads, int) and unresolved_threads > 0:
        if not dedupe_complete:
            prompts.append(
                "Continue the ghc-review-supervisor workflow. "
                f"There are still {unresolved_threads} unresolved threads and dedupe/grouping has not been recorded yet. Refresh, dedupe related issues, and shard them into fix groups before concluding."
            )
        elif isinstance(pending_groups, list) and pending_groups:
            prompts.append(
                "Continue the ghc-review-supervisor workflow. "
                f"There are still {len(pending_groups)} unresolved fix group(s) remaining. Spawn the next coder batches and finish them before concluding."
            )

    pending_reviews = state.get("pending_reviews")
    if isinstance(pending_reviews, list) and pending_reviews:
        prompts.append(
            "Continue the ghc-review-supervisor workflow. "
            f"The following streams are not reviewer-green yet: {', '.join(map(str, pending_reviews))}. Finish their reviewer loops before concluding."
        )

    if isinstance(unresolved_threads, int) and unresolved_threads > 0 and not state.get("resolved_after_push"):
        prompts.append(
            "Continue the ghc-review-supervisor workflow. "
            "Thread resolution has not been recorded after the latest push. Resolve the owned threads and refresh `ghc` before concluding."
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
                    "systemMessage": "GHC review supervisor stop hook saw an already-blocked continuation pass and stayed calm to avoid a loop.",
                }
            )
        )
        return 0

    print(
        json.dumps(
            {
                "systemMessage": "GHC review supervisor stop hook requesting continuation.",
                "decision": "block",
                "reason": "\n\n".join(prompts),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
