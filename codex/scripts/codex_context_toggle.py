#!/usr/bin/env python3
"""Enable or disable Codex skills and agent roles with managed config blocks.

This script uses the native upstream `[[skills.config]] enabled = false` path for
skills, and manages `[agents.<role>]` blocks for user-defined agent roles.

It only mutates blocks marked with its own sentinels inside `~/.codex/config.toml`.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_CONFIG_PATH = Path.home() / ".codex" / "config.toml"
DEFAULT_SKILLS_ROOT = Path.home() / ".codex" / "skills"
DEFAULT_AGENT_SNIPPETS = Path(__file__).resolve().parent.parent / "config" / "agent_roles_config_snippets.toml"

MANAGED_TAG = "codex-context-toggle"


@dataclass(frozen=True)
class SkillEntry:
    key: str
    path: Path


@dataclass(frozen=True)
class AgentEntry:
    name: str
    block: str


def marker(kind: str, name: str, boundary: str) -> str:
    return f"# >>> {MANAGED_TAG} {kind} {name} {boundary}" if boundary == "begin" else f"# <<< {MANAGED_TAG} {kind} {name} {boundary}"


def comment_block(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        if not line:
            out.append("")
        elif line.startswith("# "):
            out.append(line)
        elif line.startswith("#"):
            out.append(f"# {line[1:]}")
        else:
            out.append(f"# {line}")
    return "\n".join(out)


def uncomment_block(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        if line.startswith("# "):
            out.append(line[2:])
        elif line == "#":
            out.append("")
        else:
            out.append(line)
    return "\n".join(out)


def ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def block_regex(kind: str, name: str) -> re.Pattern[str]:
    begin = re.escape(marker(kind, name, "begin"))
    end = re.escape(marker(kind, name, "end"))
    return re.compile(rf"(?ms)^{begin}\n.*?^{end}\n?")


def build_skill_disabled_block(entry: SkillEntry, disabled: bool) -> str:
    inner = (
        "[[skills.config]]\n"
        f'path = "{entry.path}"\n'
        "enabled = false\n"
    )
    if not disabled:
        inner = comment_block(inner)
    return f"{marker('skill', entry.key, 'begin')}\n{inner}{marker('skill', entry.key, 'end')}\n"


def build_agent_block(entry: AgentEntry, enabled: bool) -> str:
    inner = entry.block
    if not enabled:
        inner = comment_block(inner)
    return f"{marker('agent', entry.name, 'begin')}\n{inner}{marker('agent', entry.name, 'end')}\n"


def replace_or_append_block(config_text: str, kind: str, name: str, rendered_block: str) -> str:
    pattern = block_regex(kind, name)
    if pattern.search(config_text):
        return pattern.sub(rendered_block, config_text, count=1)

    config_text = ensure_trailing_newline(config_text)
    if config_text.strip():
        config_text += "\n"
    return config_text + rendered_block


def load_config_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_config(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return {}
    return tomllib.loads(raw)


def discover_skills(skills_root: Path) -> tuple[dict[str, SkillEntry], list[str]]:
    entries: list[SkillEntry] = []
    if skills_root.exists():
        for skill_md in sorted(skills_root.rglob("SKILL.md")):
            rel = skill_md.relative_to(skills_root).parent.as_posix()
            key = skill_md.parent.name
            entries.append(SkillEntry(key=key, path=skill_md.resolve()))
            if rel != key:
                entries.append(SkillEntry(key=rel, path=skill_md.resolve()))

    index: dict[str, SkillEntry] = {}
    collisions: list[str] = []
    seen_paths: dict[str, set[Path]] = {}
    for entry in entries:
        seen_paths.setdefault(entry.key, set()).add(entry.path)
    for key, paths in seen_paths.items():
        if len(paths) > 1 and "/" not in key:
            collisions.append(key)
            continue
        index[key] = SkillEntry(key=key, path=next(iter(paths)))
    return index, collisions


def parse_agent_snippets(snippets_path: Path) -> dict[str, AgentEntry]:
    text = snippets_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    entries: dict[str, AgentEntry] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_name, current_lines
        if current_name is None:
            return
        block = "\n".join(current_lines).rstrip() + "\n"
        entries[current_name] = AgentEntry(name=current_name, block=block)
        current_name = None
        current_lines = []

    for line in lines:
        match = re.match(r"^\[agents\.([A-Za-z0-9_-]+)\]$", line)
        if match:
            flush()
            current_name = match.group(1)
            current_lines = [line]
            continue
        if current_name is not None:
            if re.match(r"^\[.+\]$", line):
                flush()
            else:
                current_lines.append(line)
    flush()
    return entries


def skill_disabled_in_config(config: dict, path: Path) -> bool:
    skills = config.get("skills", {})
    overrides = skills.get("config", []) if isinstance(skills, dict) else []
    for entry in overrides:
        if not isinstance(entry, dict):
            continue
        entry_path = entry.get("path")
        if entry_path == str(path) and entry.get("enabled") is False:
            return True
    return False


def agent_enabled_in_config(config: dict, name: str) -> bool:
    agents = config.get("agents", {})
    return isinstance(agents, dict) and name in agents


def apply_skill_toggle(config_text: str, entry: SkillEntry, enable: bool) -> str:
    return replace_or_append_block(
        config_text,
        "skill",
        entry.key,
        build_skill_disabled_block(entry, disabled=not enable),
    )


def apply_agent_toggle(config_text: str, entry: AgentEntry, enable: bool) -> str:
    return replace_or_append_block(
        config_text,
        "agent",
        entry.name,
        build_agent_block(entry, enabled=enable),
    )


def resolve_targets(index: dict[str, object], names: Iterable[str], kind: str) -> list[object]:
    resolved: list[object] = []
    missing: list[str] = []
    for name in names:
        item = index.get(name)
        if item is None:
            missing.append(name)
        else:
            resolved.append(item)
    if missing:
        raise SystemExit(f"Unknown {kind}: {', '.join(missing)}")
    return resolved


def cmd_list(args: argparse.Namespace) -> int:
    skills_index, collisions = discover_skills(args.skills_root)
    agents_index = parse_agent_snippets(args.agent_snippets)
    config = parse_config(args.config)

    if collisions:
        print("Ambiguous skill names detected; use relative paths for these:")
        for name in sorted(collisions):
            print(f"  {name}")
        print("")

    print("Skills:")
    for key in sorted(skills_index):
        if "/" in key:
            continue
        entry = skills_index[key]
        state = "disabled" if skill_disabled_in_config(config, entry.path) else "enabled"
        print(f"  {key:24} {state:8} {entry.path}")

    print("")
    print("Agents:")
    for name in sorted(agents_index):
        state = "enabled" if agent_enabled_in_config(config, name) else "disabled"
        print(f"  {name:24} {state}")

    return 0


def cmd_toggle(args: argparse.Namespace) -> int:
    config_text = load_config_text(args.config)
    skills_index, collisions = discover_skills(args.skills_root)
    agents_index = parse_agent_snippets(args.agent_snippets)

    if args.kind == "skill":
        if collisions:
            shadowed = [name for name in args.names if name in collisions]
            if shadowed:
                raise SystemExit(
                    "Ambiguous skill name(s): "
                    + ", ".join(shadowed)
                    + ". Use the relative skill path under ~/.codex/skills instead."
                )
        targets = resolve_targets(skills_index, args.names, "skill")
        for entry in targets:
            assert isinstance(entry, SkillEntry)
            config_text = apply_skill_toggle(config_text, entry, enable=(args.action == "enable"))
    else:
        targets = resolve_targets(agents_index, args.names, "agent")
        for entry in targets:
            assert isinstance(entry, AgentEntry)
            config_text = apply_agent_toggle(config_text, entry, enable=(args.action == "enable"))

    args.config.parent.mkdir(parents=True, exist_ok=True)
    args.config.write_text(ensure_trailing_newline(config_text), encoding="utf-8")
    print(f"Updated {args.config}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Enable or disable Codex skills and agent roles with managed config blocks."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--skills-root", type=Path, default=DEFAULT_SKILLS_ROOT)
    parser.add_argument("--agent-snippets", type=Path, default=DEFAULT_AGENT_SNIPPETS)

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List known skills and agent roles.")
    list_parser.set_defaults(func=cmd_list)

    for action in ("enable", "disable"):
        action_parser = subparsers.add_parser(action, help=f"{action.title()} one or more targets.")
        action_parser.add_argument("kind", choices=("skill", "agent"))
        action_parser.add_argument("names", nargs="+")
        action_parser.set_defaults(func=cmd_toggle, action=action)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
