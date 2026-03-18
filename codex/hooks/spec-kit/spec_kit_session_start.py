#!/usr/bin/env python3
"""Session-start hook for Spec-Kit repos.

Injects compact Spec-Kit workflow context into the model when a session starts
or resumes inside a repo that has `.specify/`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".specify").is_dir():
            return candidate
    return None


def run_json(cmd: list[str], cwd: Path) -> dict | None:
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True,
        )
    except Exception:
        return None
    try:
        return json.loads(result.stdout)
    except Exception:
        return None


def count_unchecked_tasks(tasks_path: Path) -> int:
    if not tasks_path.is_file():
        return 0
    return sum(
        1
        for line in tasks_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("- [ ]")
    )


def build_context(repo_root: Path, payload: dict) -> str | None:
    detect_script = repo_root / ".specify" / "scripts" / "bash" / "detect-phase.sh"
    prereq_script = repo_root / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"

    phase_info = (
        run_json(["bash", str(detect_script), "--json"], repo_root)
        if detect_script.is_file()
        else None
    )
    path_info = (
        run_json(["bash", str(prereq_script), "--json", "--paths-only"], repo_root)
        if prereq_script.is_file()
        else None
    )

    if not phase_info and not path_info:
        return None

    current_phase = None
    if phase_info:
        current_phase = (
            phase_info.get("current_phase")
            or phase_info.get("selected_phase")
            or phase_info.get("latest_phase")
        )

    feature_dir = path_info.get("FEATURE_DIR") if path_info else None
    feature_spec = path_info.get("FEATURE_SPEC") if path_info else None
    tasks_path = Path(path_info["TASKS"]) if path_info and path_info.get("TASKS") else None
    unchecked = count_unchecked_tasks(tasks_path) if tasks_path else 0
    source = payload.get("source", "startup")

    lines = [
        "Spec-Kit hook context:",
        f"- session source: {source}",
    ]
    if current_phase:
        lines.append(f"- detected phase: {current_phase}")
    if feature_dir:
        lines.append(f"- feature dir: {feature_dir}")
    if feature_spec:
        lines.append(f"- spec path: {feature_spec}")
    if tasks_path and tasks_path.is_file():
        lines.append(f"- unchecked tasks: {unchecked}")
    lines.append(
        "- if you conclude a Spec-Kit phase is complete, required artifacts must actually exist on disk"
    )
    lines.append(
        "- if tasks.md exists and still has unchecked boxes, do not claim the implementation is complete"
    )
    return "\n".join(lines)


def main() -> int:
    payload = json.load(sys.stdin)
    cwd = Path(payload.get("cwd") or ".")
    repo_root = find_repo_root(cwd)
    if repo_root is None:
        return 0

    context = build_context(repo_root, payload)
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
