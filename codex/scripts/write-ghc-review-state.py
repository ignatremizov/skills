#!/usr/bin/env python3
"""Write per-session flow-state for the ghc-review-supervisor hook bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def session_key_from_transcript_path(transcript_path: str) -> str:
    return hashlib.sha256(transcript_path.encode("utf-8")).hexdigest()[:24]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repo root containing .codex/")
    parser.add_argument("--transcript-path", help="Transcript path used to derive the session key")
    parser.add_argument("--session-key", help="Explicit session key override")
    parser.add_argument("--repo", help="Repository slug, e.g. owner/repo")
    parser.add_argument("--pr", type=int, required=True, help="PR number")
    parser.add_argument("--branch", required=True, help="Active branch name")
    parser.add_argument("--review-requested-at", help="ISO-8601 time when review was requested")
    parser.add_argument("--review-ready-after", help="ISO-8601 time before refresh is expected")
    parser.add_argument("--last-refresh-at", help="ISO-8601 time of the latest ghc refresh")
    parser.add_argument("--unresolved-threads", type=int, help="Current unresolved thread count")
    parser.add_argument(
        "--dedupe-complete",
        choices=("true", "false"),
        help="Whether duplicate issues have been grouped into shared fix sets",
    )
    parser.add_argument(
        "--pending-group",
        action="append",
        default=[],
        help="Comma-separated thread-id batch, e.g. t1,t2,t3",
    )
    parser.add_argument(
        "--pending-review",
        action="append",
        default=[],
        help="Pending reviewer-green stream id; may be passed multiple times",
    )
    parser.add_argument(
        "--resolved-after-push",
        choices=("true", "false"),
        help="Whether owned threads were resolved after the latest push",
    )
    parser.add_argument(
        "--rerun-requested",
        choices=("true", "false"),
        help="Whether re-review was requested and a later refresh is expected",
    )
    parser.add_argument(
        "--json-file",
        help="Optional JSON object file merged into the generated state",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete the target session state file instead of writing one",
    )
    return parser.parse_args()


def resolve_session_key(args: argparse.Namespace) -> str:
    if args.session_key:
        return args.session_key
    if args.transcript_path:
        return session_key_from_transcript_path(args.transcript_path)
    raise SystemExit("Either --session-key or --transcript-path is required")


def state_path(root: Path, session_key: str) -> Path:
    return root / ".codex" / "flow-state" / "by-session" / f"{session_key}.json"


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    return value == "true"


def parse_groups(raw_groups: list[str]) -> list[list[str]]:
    groups: list[list[str]] = []
    for raw in raw_groups:
        parts = [part.strip() for part in raw.split(",") if part.strip()]
        if parts:
            groups.append(parts)
    return groups


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    session_key = resolve_session_key(args)
    path = state_path(root, session_key)

    if args.clear:
        if path.exists():
            path.unlink()
        print(path)
        return 0

    payload: dict[str, object] = {
        "mode": "ghc-review-supervisor",
        "session_key": session_key,
        "pr": args.pr,
        "branch": args.branch,
    }
    if args.transcript_path:
        payload["transcript_path"] = args.transcript_path
    if args.repo:
        payload["repo"] = args.repo
    if args.review_requested_at:
        payload["review_requested_at"] = args.review_requested_at
    if args.review_ready_after:
        payload["review_ready_after"] = args.review_ready_after
    if args.last_refresh_at:
        payload["last_refresh_at"] = args.last_refresh_at
    if args.unresolved_threads is not None:
        payload["unresolved_threads"] = args.unresolved_threads

    dedupe_complete = parse_bool(args.dedupe_complete)
    if dedupe_complete is not None:
        payload["dedupe_complete"] = dedupe_complete

    pending_groups = parse_groups(args.pending_group)
    if pending_groups:
        payload["pending_groups"] = pending_groups

    if args.pending_review:
        payload["pending_reviews"] = args.pending_review

    resolved_after_push = parse_bool(args.resolved_after_push)
    if resolved_after_push is not None:
        payload["resolved_after_push"] = resolved_after_push

    rerun_requested = parse_bool(args.rerun_requested)
    if rerun_requested is not None:
        payload["rerun_requested"] = rerun_requested

    if args.json_file:
        extra = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
        if not isinstance(extra, dict):
            raise SystemExit("--json-file must contain a JSON object")
        payload.update(extra)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
