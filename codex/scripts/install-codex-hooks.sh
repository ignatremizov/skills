#!/usr/bin/env bash

set -euo pipefail

ROOT="."
FORCE="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT="${2:-}"
      shift 2
      ;;
    --force)
      FORCE="true"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: codex/scripts/install-codex-hooks.sh [--root PATH] [--force]

Installs the Spec-Kit Codex hooks bundle from this repo into <root>/.codex/.
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$ROOT" ]]; then
  echo "--root requires a value" >&2
  exit 1
fi

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_ROOT="$(CDPATH="" cd "$SCRIPT_DIR/.." && pwd)"
HOOK_SET_DIR="$CODEX_ROOT/hooks/spec-kit"
TARGET_ROOT="$(CDPATH="" cd "$ROOT" && pwd)"
TARGET_CODEX="$TARGET_ROOT/.codex"
TARGET_HOOKS="$TARGET_CODEX/hooks"

if [[ ! -f "$HOOK_SET_DIR/hooks.json" ]]; then
  echo "Missing hooks.json in hook set: $HOOK_SET_DIR" >&2
  exit 1
fi

mkdir -p "$TARGET_HOOKS"

if [[ -f "$TARGET_CODEX/hooks.json" && "$FORCE" != "true" ]]; then
  echo "ERROR: $TARGET_CODEX/hooks.json already exists. Re-run with --force to overwrite." >&2
  exit 1
fi

cp "$HOOK_SET_DIR/hooks.json" "$TARGET_CODEX/hooks.json"
cp "$HOOK_SET_DIR/spec_kit_session_start.py" "$TARGET_HOOKS/spec_kit_session_start.py"
cp "$HOOK_SET_DIR/spec_kit_stop.py" "$TARGET_HOOKS/spec_kit_stop.py"
chmod +x "$TARGET_HOOKS/spec_kit_session_start.py" "$TARGET_HOOKS/spec_kit_stop.py"

TARGET_CODEX_ENV="$TARGET_CODEX/config.toml"
python3 - "$TARGET_CODEX_ENV" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8") if path.exists() else ""

if re.search(r"(?m)^\s*codex_hooks\s*=", text):
    text = re.sub(r"(?m)^(\s*codex_hooks\s*=\s*).*$", r"\1true", text, count=1)
elif re.search(r"(?m)^\[features\]\s*$", text):
    text = re.sub(r"(?m)^\[features\]\s*$", "[features]\ncodex_hooks = true", text, count=1)
else:
    if text and not text.endswith("\n"):
        text += "\n"
    if text:
        text += "\n"
    text += "[features]\ncodex_hooks = true\n"

path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(text, encoding="utf-8")
PY

echo "Installed Spec-Kit hooks into $TARGET_CODEX"
echo "  - $TARGET_CODEX/hooks.json"
echo "  - $TARGET_HOOKS/spec_kit_session_start.py"
echo "  - $TARGET_HOOKS/spec_kit_stop.py"
echo "  - $TARGET_CODEX_ENV (codex_hooks = true)"
