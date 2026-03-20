#!/usr/bin/env python3
"""Stop hook for Spec-Kit repos.

Blocks once when the model appears to conclude a Spec-Kit phase but required
artifacts are missing or tasks remain unchecked.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SPEC_KIT_TOPIC_HINTS = (
    "spec-kit",
    ".specify",
    "spec.md",
    "tasks.md",
    "plan.md",
    "clarify",
    "checklist",
    "analyze",
    "specify",
)

COMPLETION_HINTS = (
    "done",
    "completed",
    "complete",
    "finished",
    "all set",
    "ready",
    "unblocked",
)


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


def transcript_mentions_spec_kit(transcript_path: str | None) -> bool:
    if not transcript_path:
        return False
    path = Path(transcript_path)
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        return False
    tail = text[-30000:]
    return any(token in tail for token in SPEC_KIT_TOPIC_HINTS)


def looks_like_completion(last_assistant_message: str | None) -> bool:
    if not last_assistant_message:
        return False
    text = last_assistant_message.lower()
    return any(token in text for token in COMPLETION_HINTS)


def count_unchecked_tasks(tasks_path: Path) -> int:
    if not tasks_path.is_file():
        return 0
    return sum(
        1
        for line in tasks_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("- [ ]")
    )


def gather_reasons(repo_root: Path) -> list[str]:
    prereq_script = repo_root / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
    detect_script = repo_root / ".specify" / "scripts" / "bash" / "detect-phase.sh"
    path_info = (
        run_json(["bash", str(prereq_script), "--json", "--paths-only"], repo_root)
        if prereq_script.is_file()
        else None
    )
    phase_info = (
        run_json(["bash", str(detect_script), "--json"], repo_root)
        if detect_script.is_file()
        else None
    )

    reasons: list[str] = []
    current_phase = None
    if phase_info:
        current_phase = (
            phase_info.get("current_phase")
            or phase_info.get("selected_phase")
            or phase_info.get("latest_phase")
        )

    if path_info:
        feature_spec = path_info.get("FEATURE_SPEC")
        if feature_spec:
            spec_path = Path(feature_spec)
            if current_phase == "specify" and (
                (not spec_path.exists()) or spec_path.stat().st_size == 0
            ):
                reasons.append(
                    "Continue the active Spec-Kit workflow in the `specify` phase. "
                    f"Create or update `{feature_spec}` before concluding."
                )

        tasks = path_info.get("TASKS")
        if tasks:
            tasks_path = Path(tasks)
            if tasks_path.is_file():
                unchecked = count_unchecked_tasks(tasks_path)
                if unchecked > 0:
                    reasons.append(
                        "Continue the active Spec-Kit workflow. "
                        f"`{tasks}` still has {unchecked} unchecked task item(s). "
                        "Complete the remaining tasks, or explicitly state which ones are intentionally still open and why."
                    )
    return reasons


def main() -> int:
    payload = json.load(sys.stdin)
    cwd = Path(payload.get("cwd") or ".")
    repo_root = find_repo_root(cwd)
    if repo_root is None:
        return 0

    if not transcript_mentions_spec_kit(payload.get("transcript_path")):
        return 0
    if not looks_like_completion(payload.get("last_assistant_message")):
        return 0

    reasons = gather_reasons(repo_root)
    if not reasons:
        return 0

    if payload.get("stop_hook_active"):
        print(
            json.dumps(
                {
                    "systemMessage": "Spec-Kit stop hook saw an already-blocked continuation pass and is surfacing warnings without blocking again.",
                }
            )
        )
        return 0

    print(
        json.dumps(
            {
                "systemMessage": "Spec-Kit stop hook requesting continuation.",
                "decision": "block",
                "reason": "\n\n".join(reasons),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
