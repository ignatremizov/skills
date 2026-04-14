#!/usr/bin/env bash

set -euo pipefail

ROOT="."
FORCE="false"
HOOK_SET="spec-kit"
MODE="install"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT="${2:-}"
      shift 2
      ;;
    --hook-set)
      HOOK_SET="${2:-}"
      shift 2
      ;;
    --disable)
      MODE="disable"
      shift
      ;;
    --uninstall)
      MODE="uninstall"
      shift
      ;;
    --force)
      FORCE="true"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: codex/scripts/install-codex-hooks.sh [--root PATH] [--hook-set NAME] [--disable|--uninstall] [--force]

Installs, disables, or uninstalls a Codex hooks bundle from this repo in <root>/.codex/.

Available hook sets:
  - spec-kit
  - supervisor-review-loop
  - supervisor-hardening
  - ghc-review-supervisor
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
HOOKS_ROOT="$CODEX_ROOT/hooks"
HOOK_SET_DIR="$CODEX_ROOT/hooks/$HOOK_SET"
TARGET_ROOT="$(CDPATH="" cd "$ROOT" && pwd)"
TARGET_CODEX="$TARGET_ROOT/.codex"
TARGET_HOOKS="$TARGET_CODEX/hooks"
TARGET_CODEX_ENV="$TARGET_CODEX/config.toml"
TARGET_HOOKS_STATE="$TARGET_CODEX/hooks-state.json"

if [[ ! -d "$HOOK_SET_DIR" ]]; then
  echo "Unknown hook set: $HOOK_SET" >&2
  exit 1
fi

if [[ ! -f "$HOOK_SET_DIR/hooks.json" ]]; then
  echo "Missing hooks.json in hook set: $HOOK_SET_DIR" >&2
  exit 1
fi

set_codex_hooks_flag() {
  python3 - "$TARGET_CODEX_ENV" "$1" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
enabled = sys.argv[2].lower() == "true"
text = path.read_text(encoding="utf-8") if path.exists() else ""

if re.search(r"(?m)^\s*codex_hooks\s*=", text):
    text = re.sub(
        r"(?m)^(\s*codex_hooks\s*=\s*).*$",
        rf"\1{'true' if enabled else 'false'}",
        text,
        count=1,
    )
elif re.search(r"(?m)^\[features\]\s*$", text):
    text = re.sub(
        r"(?m)^\[features\]\s*$",
        f"[features]\ncodex_hooks = {'true' if enabled else 'false'}",
        text,
        count=1,
    )
else:
    if text and not text.endswith("\n"):
        text += "\n"
    if text:
        text += "\n"
    text += f"[features]\ncodex_hooks = {'true' if enabled else 'false'}\n"

path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(text, encoding="utf-8")
PY
}

write_hooks_state() {
  python3 - "$TARGET_HOOKS_STATE" "$HOOKS_ROOT" "$HOOK_SET_DIR" "$HOOK_SET" <<'PY'
from pathlib import Path
import json
import sys

state_path = Path(sys.argv[1])
hooks_root = Path(sys.argv[2])
hook_set_dir = Path(sys.argv[3])
hook_set = sys.argv[4]
scripts = sorted({p.name for p in [*hooks_root.glob("*.py"), *hook_set_dir.glob("*.py")]})
payload = {"hook_set": hook_set, "scripts": scripts}
state_path.parent.mkdir(parents=True, exist_ok=True)
state_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
}

read_hooks_state() {
  python3 - "$TARGET_HOOKS_STATE" <<'PY'
from pathlib import Path
import json
import sys

path = Path(sys.argv[1])
if not path.is_file():
    sys.exit(1)
data = json.loads(path.read_text(encoding="utf-8"))
print(json.dumps(data))
PY
}

if [[ "$MODE" == "disable" ]]; then
  set_codex_hooks_flag false
  echo "Disabled codex_hooks in $TARGET_CODEX_ENV"
  exit 0
fi

mkdir -p "$TARGET_HOOKS"

if [[ "$MODE" == "uninstall" ]]; then
  if [[ ! -f "$TARGET_HOOKS_STATE" && "$FORCE" != "true" ]]; then
    echo "ERROR: $TARGET_HOOKS_STATE not found. Re-run with --force to uninstall without metadata." >&2
    exit 1
  fi

  state_json=""
  if state_json="$(read_hooks_state 2>/dev/null)"; then
    installed_hook_set="$(python3 - <<'PY' "$state_json"
import json
import sys
print(json.loads(sys.argv[1]).get("hook_set", ""))
PY
)"
    if [[ "$installed_hook_set" != "$HOOK_SET" && "$FORCE" != "true" ]]; then
      echo "ERROR: Installed hook set is '$installed_hook_set', not '$HOOK_SET'. Re-run with --force to remove anyway." >&2
      exit 1
    fi
    python3 - <<'PY' "$state_json" "$TARGET_HOOKS"
from pathlib import Path
import json
import sys

state = json.loads(sys.argv[1])
hooks_dir = Path(sys.argv[2])
for script in state.get("scripts", []):
    path = hooks_dir / script
    if path.exists():
        path.unlink()
PY
  else
    find "$HOOK_SET_DIR" -maxdepth 1 -type f -name '*.py' -exec basename {} \; | while read -r script; do
      rm -f "$TARGET_HOOKS/$script"
    done
    find "$HOOKS_ROOT" -maxdepth 1 -type f -name '*.py' -exec basename {} \; | while read -r script; do
      rm -f "$TARGET_HOOKS/$script"
    done
  fi

  rm -f "$TARGET_CODEX/hooks.json" "$TARGET_HOOKS_STATE"
  set_codex_hooks_flag false
  echo "Uninstalled $HOOK_SET hooks from $TARGET_CODEX"
  exit 0
fi

if [[ -f "$TARGET_CODEX/hooks.json" && "$FORCE" != "true" ]]; then
  echo "ERROR: $TARGET_CODEX/hooks.json already exists. Re-run with --force to overwrite." >&2
  exit 1
fi

cp "$HOOK_SET_DIR/hooks.json" "$TARGET_CODEX/hooks.json"
find "$HOOKS_ROOT" -maxdepth 1 -type f -name '*.py' -exec cp {} "$TARGET_HOOKS/" \;
find "$HOOK_SET_DIR" -maxdepth 1 -type f -name '*.py' -exec cp {} "$TARGET_HOOKS/" \;
find "$TARGET_HOOKS" -maxdepth 1 -type f -name '*.py' -exec chmod +x {} \;
write_hooks_state
set_codex_hooks_flag true

echo "Installed $HOOK_SET hooks into $TARGET_CODEX"
echo "  - $TARGET_CODEX/hooks.json"
find "$HOOKS_ROOT" -maxdepth 1 -type f -name '*.py' -exec basename {} \; | sort | while read -r script; do
  echo "  - $TARGET_HOOKS/$script"
done
find "$HOOK_SET_DIR" -maxdepth 1 -type f -name '*.py' -exec basename {} \; | sort | while read -r script; do
  echo "  - $TARGET_HOOKS/$script"
done
echo "  - $TARGET_HOOKS_STATE"
echo "  - $TARGET_CODEX_ENV (codex_hooks = true)"
