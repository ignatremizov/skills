#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./update-skills.sh [--codex] [skill] [skill] ...

Sync portable skill sources from:
  skills/**/SKILL.md
to:
  ~/.agents/skills/<relative-skill-path>/

With no skill arguments, syncs every skill under `skills/`.
With skill arguments, accepts either:
  - an exact relative path under `skills/` (for example `.curated/gh-address-comments`)
  - a unique basename (for example `coder`)

Optional:
  --codex    also copy the selected skills into ~/.codex/skills/

Notes:
  - Portable skill sources live under `skills/`.
  - Codex-specific role presets live under `codex/agents/` and should be
    referenced directly from `~/.codex/config.toml`.
EOF
}

sync_codex=false
requested_skills=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --codex)
      sync_codex=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      requested_skills+=("$1")
      ;;
  esac
  shift
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
SOURCE_ROOT="$REPO_ROOT/skills"

if [[ ! -d "$SOURCE_ROOT" ]]; then
  echo "Source skills directory not found: $SOURCE_ROOT" >&2
  exit 1
fi

mapfile -t skills < <(
  find "$SOURCE_ROOT" \
    \( -type d \( -name '.venv-*' -o -name '__pycache__' \) -prune \) -o \
    \( -type f -name SKILL.md -print \) \
    | sed "s#^$SOURCE_ROOT/##" \
    | sed 's#/SKILL.md$##' \
    | sort
)

if [[ ${#skills[@]} -eq 0 ]]; then
  echo "No skill directories with SKILL.md found under: $SOURCE_ROOT" >&2
  exit 1
fi

if [[ ${#requested_skills[@]} -gt 0 ]]; then
  selected_skills=()
  for requested in "${requested_skills[@]}"; do
    matches=()
    for skill in "${skills[@]}"; do
      if [[ "$skill" == "$requested" || "$(basename "$skill")" == "$requested" ]]; then
        matches+=("$skill")
      fi
    done

    if [[ ${#matches[@]} -eq 0 ]]; then
      echo "Skill not found under skills/: $requested" >&2
      echo "Available skills:" >&2
      printf '  - %s\n' "${skills[@]}" >&2
      exit 1
    fi

    if [[ ${#matches[@]} -gt 1 ]]; then
      echo "Ambiguous skill selector: $requested" >&2
      echo "Matches:" >&2
      printf '  - %s\n' "${matches[@]}" >&2
      echo "Use the exact relative path under skills/." >&2
      exit 1
    fi

    selected_skills+=("${matches[0]}")
  done
  skills=("${selected_skills[@]}")
fi

sync_target() {
  local target_parent_dir="$1"
  mkdir -p "$target_parent_dir"

  local skill
  for skill in "${skills[@]}"; do
    local source_dir="$SOURCE_ROOT/$skill/"
    local target_skill_dir="$target_parent_dir/$skill"
    mkdir -p "$(dirname "$target_skill_dir")"
    mkdir -p "$target_skill_dir"
    rsync -a --delete --exclude '.DS_Store' "$source_dir" "$target_skill_dir/"
    echo "Synced -> $target_skill_dir"
  done
}

link_target() {
  local target_parent_dir="$1"
  mkdir -p "$target_parent_dir"

  local skill
  for skill in "${skills[@]}"; do
    local source_dir="$SOURCE_ROOT/$skill"
    local target_skill_dir="$target_parent_dir/$skill"
    mkdir -p "$(dirname "$target_skill_dir")"
    rm -rf "$target_skill_dir"
    ln -s "$source_dir" "$target_skill_dir"
    echo "Linked -> $target_skill_dir -> $source_dir"
  done
}

link_target "$HOME/.agents/skills"

if [[ "$sync_codex" == "true" ]]; then
  sync_target "$HOME/.codex/skills"
fi
