#!/usr/bin/env python3
"""Write per-session Codex hook flow-state files.

The state file is stored under:
  .codex/flow-state/by-session/<session_key>.json

Session keys should be derived from `transcript_path` when available so
multiple concurrent supervisor sessions do not clobber each other.
"""

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
    parser.add_argument("--mode", required=True, help="Flow mode, e.g. supervisor-hardening")
    parser.add_argument("--pr", type=int, help="Optional PR number")
    parser.add_argument("--branch", help="Optional branch name")
    parser.add_argument(
        "--completed-area",
        action="append",
        default=[],
        help="Completed area name; may be passed multiple times",
    )
    parser.add_argument(
        "--pending-review",
        action="append",
        default=[],
        help="Pending reviewer-green stream id; may be passed multiple times",
    )
    parser.add_argument(
        "--quality-gate-status",
        choices=("pending", "passed", "needs_followup"),
        help="Quality-gate status",
    )
    parser.add_argument(
        "--quality-gate-recommended-area",
        help="Recommended follow-up area from quality-gate",
    )
    parser.add_argument(
        "--json-file",
        help="Optional JSON file whose object payload will be merged into the generated state",
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

    payload: dict[str, object] = {"mode": args.mode, "session_key": session_key}
    if args.transcript_path:
        payload["transcript_path"] = args.transcript_path
    if args.pr is not None:
        payload["pr"] = args.pr
    if args.branch:
        payload["branch"] = args.branch
    if args.completed_area:
        payload["completed_areas"] = args.completed_area
    if args.pending_review:
        payload["pending_reviews"] = args.pending_review
    if args.quality_gate_status or args.quality_gate_recommended_area:
        payload["quality_gate"] = {
            "status": args.quality_gate_status or "pending",
            "recommended_area": args.quality_gate_recommended_area,
        }

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
