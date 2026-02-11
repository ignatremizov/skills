#!/usr/bin/env bash

# Copy a Spec-Kit template into a target artifact file.
# Source set: {$HOME,<repo>}/.specify/templates/<template-name>

set -euo pipefail

TEMPLATE_NAME=""
TARGET_FILE=""
ROOT_PATH="."
FORCE="false"

usage() {
  cat <<'USAGE'
Usage: copy-template.sh --name <template-file> --to <target-file> [--root <repo-root>] [--force]

Options:
  --name FILE   Template filename (e.g. spec-template.md)
  --to PATH     Target file path to write
  --root PATH   Repo root to check for optional local override (default: .)
  --force       Overwrite target even if non-empty
  --help        Show this help
USAGE
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      TEMPLATE_NAME="$2"
      shift 2
      ;;
    --to)
      TARGET_FILE="$2"
      shift 2
      ;;
    --root)
      ROOT_PATH="$2"
      shift 2
      ;;
    --force)
      FORCE="true"
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

[[ -n "$TEMPLATE_NAME" ]] || die "--name is required"
[[ -n "$TARGET_FILE" ]] || die "--to is required"

ROOT_PATH="$(cd "$ROOT_PATH" && pwd)"
HOME_SOURCE="$HOME/.specify/templates/$TEMPLATE_NAME"
REPO_SOURCE="$ROOT_PATH/.specify/templates/$TEMPLATE_NAME"

SOURCE=""
if [[ -f "$HOME_SOURCE" ]]; then
  SOURCE="$HOME_SOURCE"
elif [[ -f "$REPO_SOURCE" ]]; then
  SOURCE="$REPO_SOURCE"
else
  die "template not found: $TEMPLATE_NAME (checked $HOME_SOURCE and $REPO_SOURCE). Run bootstrap-assets.sh first."
fi

mkdir -p "$(dirname "$TARGET_FILE")"

if [[ -f "$TARGET_FILE" && "$FORCE" != "true" ]]; then
  if [[ -s "$TARGET_FILE" ]]; then
    echo "skipped: $TARGET_FILE (non-empty; use --force to overwrite)"
    exit 0
  fi
fi

cp "$SOURCE" "$TARGET_FILE"
echo "copied: $SOURCE -> $TARGET_FILE"
