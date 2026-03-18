#!/usr/bin/env bash

set -euo pipefail

CONFIG_PATH="$HOME/.codex/config.toml"
SKILLS_CHECKOUT=""

usage() {
  cat <<'EOF'
Usage: codex/scripts/install-codex-agents.sh [--config PATH] [--skills-checkout PATH]

Installs the managed agent role block from codex/config/agent_roles_config_snippets.toml
into the target Codex config file.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG_PATH="${2:-}"
      shift 2
      ;;
    --skills-checkout)
      SKILLS_CHECKOUT="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH="" cd "$SCRIPT_DIR/../.." && pwd)"
SNIPPETS_FILE="$REPO_ROOT/codex/config/agent_roles_config_snippets.toml"

if [[ -z "$SKILLS_CHECKOUT" ]]; then
  SKILLS_CHECKOUT="$REPO_ROOT"
fi

mkdir -p "$(dirname "$CONFIG_PATH")"
touch "$CONFIG_PATH"

rendered="$(mktemp)"
perl -0pe "s#<SKILLS_CHECKOUT>#${SKILLS_CHECKOUT}#g" "$SNIPPETS_FILE" > "$rendered"

cleaned="$(mktemp)"
perl -0pe 's/\n?# >>> codex-agent-install begin\n.*?# <<< codex-agent-install end\n?/\n/s' "$CONFIG_PATH" > "$cleaned"
mv "$cleaned" "$CONFIG_PATH"

if [[ -s "$CONFIG_PATH" ]]; then
  printf '\n' >> "$CONFIG_PATH"
fi

{
  echo "# >>> codex-agent-install begin"
  cat "$rendered"
  echo "# <<< codex-agent-install end"
} >> "$CONFIG_PATH"

rm -f "$rendered"

echo "Installed managed agent role block into $CONFIG_PATH"
