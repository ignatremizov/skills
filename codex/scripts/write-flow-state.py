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
        default=None,
        help="Completed area name; may be passed multiple times",
    )
    parser.add_argument(
        "--clear-completed-areas",
        action="store_true",
        help="Clear any existing completed area names",
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
        "--quality-gate-status",
        choices=("pending", "passed", "needs_followup"),
        help="Quality-gate status",
    )
    parser.add_argument(
        "--quality-gate-recommended-area",
        help="Recommended follow-up area from quality-gate",
    )
    parser.add_argument(
        "--quality-gate-followup-mode",
        choices=("must_close_now", "defer_to_followup_spec"),
        help="Whether the recommended area must be closed now or deferred into follow-up spec work",
    )
    parser.add_argument(
        "--must-close-finding",
        action="append",
        default=None,
        help="Persisted must-close reviewer finding or follow-up item; may be passed multiple times",
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
        help="Persisted deferred reviewer finding or follow-up item; may be passed multiple times",
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
        "--quality-gate-needs-rerun",
        choices=("true", "false"),
        help="Whether a later hardening stream invalidated the last quality-gate result",
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


def has_list_items(value: object) -> bool:
    return isinstance(value, list) and any(isinstance(item, str) and item for item in value)


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
    payload["mode"] = args.mode
    payload["session_key"] = session_key
    if args.transcript_path:
        payload["transcript_path"] = args.transcript_path
    if args.pr is not None:
        payload["pr"] = args.pr
    if args.branch:
        payload["branch"] = args.branch
    if args.clear_completed_areas:
        payload["completed_areas"] = []
    if args.completed_area is not None:
        payload["completed_areas"] = merge_unique_strings(payload.get("completed_areas"), args.completed_area)
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
    if (
        args.quality_gate_status is not None
        or args.quality_gate_recommended_area is not None
        or args.quality_gate_followup_mode is not None
        or args.quality_gate_needs_rerun is not None
        or args.deferred_finding is not None
        or args.clear_deferred_findings
    ):
        existing_quality_gate = payload.get("quality_gate")
        if isinstance(existing_quality_gate, dict):
            quality_gate = dict(existing_quality_gate)
        else:
            quality_gate = {}
        if (
            args.quality_gate_status is not None
            or args.quality_gate_recommended_area is not None
            or args.quality_gate_followup_mode is not None
        ):
            if args.quality_gate_status is not None:
                quality_gate["status"] = args.quality_gate_status
                if args.quality_gate_status != "needs_followup":
                    quality_gate.pop("recommended_area", None)
                    quality_gate.pop("followup_mode", None)
                    quality_gate.pop("deferred_recorded", None)
            if args.quality_gate_recommended_area is not None:
                quality_gate["recommended_area"] = args.quality_gate_recommended_area
            if args.quality_gate_followup_mode is not None:
                quality_gate["followup_mode"] = args.quality_gate_followup_mode
            if args.quality_gate_followup_mode == "defer_to_followup_spec":
                quality_gate["deferred_recorded"] = has_list_items(payload.get("deferred_findings"))
            elif args.quality_gate_followup_mode is not None:
                quality_gate.pop("deferred_recorded", None)
            quality_gate["needs_rerun"] = False
        if args.quality_gate_needs_rerun is not None:
            quality_gate["needs_rerun"] = args.quality_gate_needs_rerun == "true"
        if (
            quality_gate.get("followup_mode") == "defer_to_followup_spec"
            and (args.deferred_finding is not None or args.clear_deferred_findings)
        ):
            quality_gate["deferred_recorded"] = has_list_items(payload.get("deferred_findings"))
        payload["quality_gate"] = quality_gate

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
