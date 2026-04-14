#!/usr/bin/env python3
"""Write per-session flow-state for the spec-kit hook bundle."""

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
    parser.add_argument("--feature-id", help="Optional feature identifier for this spec-kit session")
    parser.add_argument("--phase", help="Active spec-kit phase name")
    parser.add_argument(
        "--required-artifact",
        action="append",
        default=None,
        help="Required artifact path; may be passed multiple times",
    )
    parser.add_argument(
        "--task-path",
        action="append",
        default=None,
        help="Task checklist path to gate on; may be passed multiple times",
    )
    parser.add_argument(
        "--clear-required-artifacts",
        action="store_true",
        help="Clear any previously recorded required artifact paths",
    )
    parser.add_argument(
        "--clear-task-paths",
        action="store_true",
        help="Clear any previously recorded task checklist paths",
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


def resolve_session_key(args: argparse.Namespace) -> str | None:
    if args.transcript_path:
        return session_key_from_transcript_path(args.transcript_path)
    return None


def state_path(root: Path, session_key: str | None) -> Path:
    if session_key is None:
        return root / ".codex" / "flow-state" / "spec-kit-bootstrap.json"
    return root / ".codex" / "flow-state" / "by-session" / f"{session_key}.json"


def load_existing_state(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def normalize_paths(paths: list[str] | None, root: Path) -> list[str]:
    if not paths:
        return []
    normalized: list[str] = []
    for raw_path in paths:
        stripped_path = raw_path.strip()
        if not stripped_path:
            continue
        path = Path(stripped_path).expanduser()
        if not path.is_absolute():
            path = root / path
        normalized.append(str(path.resolve()))
    return normalized


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
    payload["mode"] = "spec-kit"
    if session_key is not None:
        payload["session_key"] = session_key
    if args.transcript_path:
        payload["transcript_path"] = args.transcript_path
    if args.feature_id:
        payload["feature_id"] = args.feature_id
    if args.phase:
        payload["phase"] = args.phase

    if args.clear_required_artifacts:
        payload["required_artifacts"] = []
    if args.required_artifact is not None:
        payload["required_artifacts"] = merge_unique_strings(
            payload.get("required_artifacts"), normalize_paths(args.required_artifact, root)
        )

    if args.clear_task_paths:
        payload["task_paths"] = []
    if args.task_path is not None:
        payload["task_paths"] = merge_unique_strings(
            payload.get("task_paths"), normalize_paths(args.task_path, root)
        )

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
