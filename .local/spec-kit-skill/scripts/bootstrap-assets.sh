#!/usr/bin/env bash

# Bootstrap Spec-Kit templates into a target repository.
# - Templates target: <repo>/.specify/templates/
#
# If a repo already has `.specify/templates/`, managed template files are
# overwritten to refresh them. Otherwise, only missing files are created.

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

REPO_ROOT=""
ENSURE="templates"
VERBOSE="false"

usage() {
  cat <<'USAGE'
Usage: bootstrap-assets.sh [--root PATH] [--ensure templates] [--verbose]

Options:
  --root PATH        Target root path (default: $HOME)
  --ensure MODE      What to bootstrap: templates (default: templates)
  --verbose          Print extra details
  --help             Show this help
USAGE
}

log() {
  if [[ "$VERBOSE" == "true" ]]; then
    echo "$@"
  fi
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

resolve_repo_root() {
  if [[ -n "$REPO_ROOT" ]]; then
    return
  fi
  REPO_ROOT="$HOME"
}

find_source_file() {
  local file="$1"
  shift
  local candidates=("$@")
  local path
  for path in "${candidates[@]}"; do
    if [[ -f "$path" ]]; then
      echo "$path"
      return 0
    fi
  done
  return 1
}

copy_if_missing() {
  local target="$1"
  local source="$2"
  if [[ -f "$target" ]]; then
    log "exists: $target"
    return 0
  fi
  mkdir -p "$(dirname "$target")"
  cp "$source" "$target"
  echo "created: $target (from $source)"
}

copy_with_policy() {
  local target="$1"
  local source="$2"
  local overwrite_existing="$3"

  if [[ -f "$target" ]]; then
    if [[ "$overwrite_existing" == "true" ]]; then
      cp "$source" "$target"
      echo "overwrote: $target (from $source)"
    else
      log "exists: $target"
    fi
    return 0
  fi

  copy_if_missing "$target" "$source"
}

write_template_stub() {
  local file="$1"
  local target="$2"
  local overwrite_existing="$3"
  local existed_before="false"

  if [[ -f "$target" ]]; then
    existed_before="true"
  fi

  if [[ "$existed_before" == "true" && "$overwrite_existing" != "true" ]]; then
    log "exists: $target"
    return 0
  fi

  mkdir -p "$(dirname "$target")"

  case "$file" in
    spec-template.md)
      cat >"$target" <<'TEMPLATE'
# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`  
**Created**: [DATE]  
**Status**: Draft  
**Input**: [USER INPUT]

## User Scenarios & Testing *(mandatory)*

## Requirements *(mandatory)*

### Functional Requirements

## Success Criteria *(mandatory)*

## Clarifications
TEMPLATE
      ;;
    plan-template.md)
      cat >"$target" <<'TEMPLATE'
# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [PATH]
**Input**: Feature specification

## Summary
## Technical Context
## Constitution Check
## Project Structure
## Complexity Tracking
TEMPLATE
      ;;
    tasks-template.md)
      cat >"$target" <<'TEMPLATE'
# Tasks: [FEATURE NAME]

**Input**: Design docs from feature folder

## Phase 1: Setup
## Phase 2: Foundational
## Phase 3+: User Stories
## Final Phase: Polish
TEMPLATE
      ;;
    checklist-template.md)
      cat >"$target" <<'TEMPLATE'
# Requirements Checklist: [DOMAIN]

- [ ] Completeness
- [ ] Clarity
- [ ] Consistency
- [ ] Measurability
TEMPLATE
      ;;
    *)
      cat >"$target" <<'TEMPLATE'
# Template
TEMPLATE
      ;;
  esac

  if [[ "$existed_before" == "true" && "$overwrite_existing" == "true" ]]; then
    echo "overwrote: $target (stub)"
  else
    echo "created: $target (stub)"
  fi
}

bootstrap_templates() {
  local target_dir="$REPO_ROOT/.specify/templates"
  local overwrite_existing="false"

  if [[ -d "$target_dir" ]]; then
    overwrite_existing="true"
  fi

  mkdir -p "$target_dir"

  local files=(
    spec-template.md
    plan-template.md
    tasks-template.md
    checklist-template.md
  )

  local source_root="${SPEC_KIT_SOURCE_DIR:-}"
  local file source target
  for file in "${files[@]}"; do
    target="$target_dir/$file"
    if source="$(find_source_file "$file" \
      "$SKILL_DIR/assets/templates/$file" \
      "${source_root:+$source_root/templates/$file}" \
      "$HOME/code/spec-kit/templates/$file")"; then
      copy_with_policy "$target" "$source" "$overwrite_existing"
    else
      write_template_stub "$file" "$target" "$overwrite_existing"
    fi
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      REPO_ROOT="$2"
      shift 2
      ;;
    --ensure)
      ENSURE="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE="true"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

resolve_repo_root
[[ -d "$REPO_ROOT" ]] || die "repo root does not exist: $REPO_ROOT"

if [[ "$ENSURE" != "templates" ]]; then
  die "invalid --ensure value: $ENSURE (only 'templates' is supported)"
fi

bootstrap_templates

echo "done: bootstrapped templates for $REPO_ROOT"
