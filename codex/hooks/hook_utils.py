from __future__ import annotations

import hashlib
import re
from pathlib import Path


def find_repo_root(start: Path) -> Path | None:
    current = start.resolve()
    fallback_git_root: Path | None = None
    for candidate in [current, *current.parents]:
        if (candidate / ".codex").is_dir():
            return candidate
        if fallback_git_root is None and (candidate / ".git").exists():
            fallback_git_root = candidate
    return fallback_git_root


def session_key_from_transcript_path(transcript_path: str) -> str:
    return hashlib.sha256(transcript_path.encode("utf-8")).hexdigest()[:24]


def contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None
