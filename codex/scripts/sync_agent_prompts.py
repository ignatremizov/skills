#!/usr/bin/env python3
"""Sync Codex agent developer_instructions from skill source files.

Usage:
  python3 codex/scripts/sync_agent_prompts.py
  python3 codex/scripts/sync_agent_prompts.py --dry-run
  python3 codex/scripts/sync_agent_prompts.py \
    --map codex/agents/awaiter.toml=skills/awaiter/SKILL.md
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable


DEFAULT_MAPPINGS: tuple[tuple[str, str], ...] = (
    # Shared skill-backed prompt sources worth keeping in sync.
    ("codex/agents/audit-supervisor.toml", "skills/audit-supervisor/SKILL.md"),
    ("codex/agents/supervisor-review-loop.toml", "skills/supervisor-review-loop/SKILL.md"),
    ("codex/agents/athena-supervisor.toml", "skills/athena-supervisor/SKILL.md"),
    ("codex/agents/awaiter.toml", "skills/awaiter/SKILL.md"),
    ("codex/agents/reviewer.toml", "skills/reviewer/SKILL.md"),
    # Shared generic coder skill for the default coder role; task-specialized
    # coders keep their own dedicated prompts.
    ("codex/agents/coder.toml", "skills/coder/SKILL.md"),
    ("codex/agents/coder-prototype-spark.toml", "skills/coder/SKILL.md"),
    # xhigh keeps its extra-rigor additions in a dedicated prompt source.
    ("codex/agents/spec-kit-specify.toml", "skills/spec-kit-specify-skill/SKILL.md"),
    ("codex/agents/spec-kit-clarify.toml", "skills/spec-kit-clarify-skill/SKILL.md"),
    ("codex/agents/spec-kit-plan.toml", "skills/spec-kit-plan-skill/SKILL.md"),
    ("codex/agents/spec-kit-tasks.toml", "skills/spec-kit-tasks-skill/SKILL.md"),
    ("codex/agents/spec-kit-checklist.toml", "skills/spec-kit-checklist-skill/SKILL.md"),
    ("codex/agents/spec-kit-analyze.toml", "skills/spec-kit-analyze-skill/SKILL.md"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repo root (defaults to parent of codex/)",
    )
    parser.add_argument(
        "--map",
        action="append",
        default=[],
        metavar="ROLE_TOML=SKILL_MD",
        help="Override/extend default mappings",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write files")
    return parser.parse_args()


def parse_mapping(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise ValueError(f"Invalid mapping '{raw}', expected ROLE_TOML=SKILL_MD")
    role, skill = raw.split("=", 1)
    role = role.strip()
    skill = skill.strip()
    if not role or not skill:
        raise ValueError(f"Invalid mapping '{raw}', both sides are required")
    return role, skill


def strip_frontmatter(content: str) -> str:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return content.strip()

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            body = "\n".join(lines[i + 1 :])
            return body.strip()

    # Malformed frontmatter: keep full content.
    return content.strip()


def build_dev_instructions_block(skill_body: str) -> str:
    escaped = skill_body.replace('"""', '\\"\\"\\"')
    return f'developer_instructions = """\n{escaped}\n"""\n'


def upsert_dev_instructions(agent_toml: str, block: str) -> str:
    pattern = re.compile(r'(?ms)^developer_instructions\s*=\s*"""\n.*?\n"""\s*\n?')
    if pattern.search(agent_toml):
        return pattern.sub(block, agent_toml, count=1)

    if agent_toml and not agent_toml.endswith("\n"):
        agent_toml += "\n"
    if agent_toml and not agent_toml.endswith("\n\n"):
        agent_toml += "\n"
    return agent_toml + block


def resolve_mappings(cli_mappings: Iterable[str]) -> list[tuple[str, str]]:
    if not cli_mappings:
        return list(DEFAULT_MAPPINGS)
    return [parse_mapping(m) for m in cli_mappings]


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    mappings = resolve_mappings(args.map)

    updated = 0
    unchanged = 0

    for role_rel, skill_rel in mappings:
        role_path = (root / role_rel).resolve()
        skill_path = (root / skill_rel).resolve()

        if not skill_path.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_path}")
        if not role_path.exists():
            raise FileNotFoundError(f"Agent toml not found: {role_path}")

        skill_text = skill_path.read_text(encoding="utf-8")
        skill_body = strip_frontmatter(skill_text)
        block = build_dev_instructions_block(skill_body)

        original = role_path.read_text(encoding="utf-8")
        updated_text = upsert_dev_instructions(original, block)

        if updated_text == original:
            unchanged += 1
            print(f"UNCHANGED {role_path}")
            continue

        updated += 1
        if args.dry_run:
            print(f"WOULD UPDATE {role_path} <= {skill_path}")
        else:
            role_path.write_text(updated_text, encoding="utf-8")
            print(f"UPDATED {role_path} <= {skill_path}")

    mode = "DRY-RUN" if args.dry_run else "WRITE"
    print(f"{mode} SUMMARY: updated={updated} unchanged={unchanged} total={len(mappings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
