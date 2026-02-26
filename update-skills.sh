#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./update-skills.sh [--agents] [skill] [skill] ...

Syncs skill directories from:
  .local/<skill-name>/
to:
  ~/.codex/skills/<skill-name>/

With no skill arguments, syncs all directories that contain SKILL.md.
With skill arguments, syncs only those skills.

Optional:
  --agents   also sync to ~/.agents/skills/<skill-name>/
EOF
}

sync_agents=false
requested_skills=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agents)
      sync_agents=true
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
SOURCE_ROOT="$SCRIPT_DIR/.local"

if [[ ! -d "$SOURCE_ROOT" ]]; then
  echo "Source .local directory not found: $SOURCE_ROOT" >&2
  exit 1
fi

mapfile -t skills < <(
  for dir in "$SOURCE_ROOT"/*/; do
    [[ -d "$dir" ]] || continue
    [[ -f "$dir/SKILL.md" ]] || continue
    basename "$dir"
  done | sort
)

if [[ ${#skills[@]} -eq 0 ]]; then
  echo "No skill directories with SKILL.md found under: $SOURCE_ROOT" >&2
  exit 1
fi

if [[ ${#requested_skills[@]} -gt 0 ]]; then
  selected_skills=()
  for requested in "${requested_skills[@]}"; do
    found=false
    for skill in "${skills[@]}"; do
      if [[ "$skill" == "$requested" ]]; then
        found=true
        selected_skills+=("$skill")
        break
      fi
    done
    if [[ "$found" == "false" ]]; then
      echo "Skill not found in .local: $requested" >&2
      echo "Available skills:" >&2
      printf '  - %s\n' "${skills[@]}" >&2
      exit 1
    fi
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
    mkdir -p "$target_skill_dir"
    rsync -a --delete --exclude '.DS_Store' "$source_dir" "$target_skill_dir/"
    echo "Synced -> $target_skill_dir"
  done
}

sync_target "$HOME/.codex/skills"

if [[ "$sync_agents" == "true" ]]; then
  sync_target "$HOME/.agents/skills"
fi
