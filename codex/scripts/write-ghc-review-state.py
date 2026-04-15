#!/usr/bin/env python3
"""Write per-session supervisor ledger state for the ghc-review-supervisor hook bundle.

This records workflow checkpoints and blocking obligations. It intentionally
does not mirror the ghc cache or store full review-thread payloads.
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
    parser.add_argument("--repo", help="Repository slug, e.g. owner/repo")
    parser.add_argument("--pr", type=int, required=True, help="PR number")
    parser.add_argument("--branch", required=True, help="Active branch name")
    parser.add_argument("--review-requested-at", help="ISO-8601 time when review was requested")
    parser.add_argument("--review-ready-after", help="ISO-8601 time before refresh is expected")
    parser.add_argument("--last-refresh-at", help="ISO-8601 time of the latest supervisor-owned ghc refresh checkpoint")
    parser.add_argument("--unresolved-threads", type=int, help="Unresolved thread count snapshot from the latest ghc refresh")
    parser.add_argument(
        "--dedupe-complete",
        choices=("true", "false"),
        help="Whether duplicate issues have been grouped into shared fix sets",
    )
    parser.add_argument(
        "--pending-group",
        action="append",
        default=None,
        help="Comma-separated thread-id batch, e.g. t1,t2,t3",
    )
    parser.add_argument(
        "--clear-pending-groups",
        action="store_true",
        help="Clear any existing unresolved fix-group batches",
    )
    parser.add_argument(
        "--pending-review",
        action="append",
        default=None,
        help="Pending review-loop-closure stream id; may be passed multiple times",
    )
    parser.add_argument(
        "--clear-pending-reviews",
        action="store_true",
        help="Clear any existing pending review-loop-closure stream ids",
    )
    parser.add_argument(
        "--must-close-finding",
        action="append",
        default=None,
        help="Persisted must-close reviewer finding; may be passed multiple times",
    )
    parser.add_argument(
        "--clear-must-close-findings",
        action="store_true",
        help="Clear any existing must-close reviewer findings",
    )
    parser.add_argument(
        "--deferred-finding",
        action="append",
        default=None,
        help="Persisted deferred reviewer finding; may be passed multiple times",
    )
    parser.add_argument(
        "--clear-deferred-findings",
        action="store_true",
        help="Clear any existing deferred reviewer findings",
    )
    parser.add_argument(
        "--ignored-finding-rationale",
        action="append",
        default=None,
        help="Persisted rationale for a finding intentionally not reopened; may be passed multiple times",
    )
    parser.add_argument(
        "--clear-ignored-finding-rationales",
        action="store_true",
        help="Clear any existing ignored-finding rationales",
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


def load_existing_state(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def merge_unique_strings(existing: object, new_values: list[str]) -> list[str]:
    merged: list[str] = []
    if isinstance(existing, list):
        for value in existing:
            if isinstance(value, str):
                normalized = value.strip()
                if normalized and normalized not in merged:
                    merged.append(normalized)
    for value in new_values:
        normalized = value.strip()
        if normalized and normalized not in merged:
            merged.append(normalized)
    return merged


def merge_unique_groups(existing: object, new_groups: list[list[str]]) -> list[list[str]]:
    merged: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    if isinstance(existing, list):
        for raw_group in existing:
            if isinstance(raw_group, list):
                group = [part for part in raw_group if isinstance(part, str) and part]
                key = tuple(group)
                if group and key not in seen:
                    seen.add(key)
                    merged.append(group)
    for group in new_groups:
        key = tuple(group)
        if group and key not in seen:
            seen.add(key)
            merged.append(group)
    return merged


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

    payload = load_existing_state(path)
    payload["mode"] = "ghc-review-supervisor"
    payload["session_key"] = session_key
    payload["pr"] = args.pr
    payload["branch"] = args.branch
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

    if args.clear_pending_groups:
        payload["pending_groups"] = []
    if args.pending_group is not None:
        pending_groups = parse_groups(args.pending_group)
        payload["pending_groups"] = merge_unique_groups(payload.get("pending_groups"), pending_groups)

    if args.clear_pending_reviews:
        payload["pending_reviews"] = []
    if args.pending_review is not None:
        payload["pending_reviews"] = merge_unique_strings(payload.get("pending_reviews"), args.pending_review)
    if args.clear_must_close_findings:
        payload["must_close_findings"] = []
    if args.must_close_finding is not None:
        payload["must_close_findings"] = merge_unique_strings(payload.get("must_close_findings"), args.must_close_finding)
    if args.clear_deferred_findings:
        payload["deferred_findings"] = []
    if args.deferred_finding is not None:
        payload["deferred_findings"] = merge_unique_strings(payload.get("deferred_findings"), args.deferred_finding)
    if args.clear_ignored_finding_rationales:
        payload["ignored_finding_rationales"] = []
    if args.ignored_finding_rationale is not None:
        payload["ignored_finding_rationales"] = merge_unique_strings(
            payload.get("ignored_finding_rationales"), args.ignored_finding_rationale
        )

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
