#!/usr/bin/env bash
set -euo pipefail

SYSTEM_ROOT="${1:-$HOME/.codex/skills/.system}"

if [[ ! -d "$SYSTEM_ROOT" ]]; then
  echo "system skills root not found: $SYSTEM_ROOT" >&2
  exit 1
fi

shopt -s nullglob
files=("$SYSTEM_ROOT"/*/agents/openai.yaml)

if (( ${#files[@]} == 0 )); then
  echo "no bundled skill openai.yaml files found under: $SYSTEM_ROOT" >&2
  exit 1
fi

for f in "${files[@]}"; do
  tmp="$(mktemp)"
  python3 - "$f" <<'PY' > "$tmp"
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
lines = text.splitlines()

policy_idx = None
for i, line in enumerate(lines):
    if line.strip() == "policy:":
        policy_idx = i
        break

if policy_idx is None:
    if lines and lines[-1].strip() != "":
        lines.append("")
    lines.extend([
        "policy:",
        "  allow_implicit_invocation: false",
    ])
else:
    inserted = False
    j = policy_idx + 1
    while j < len(lines):
        raw = lines[j]
        stripped = raw.strip()
        if stripped and not raw.startswith((" ", "\t")):
            break
        if stripped.startswith("allow_implicit_invocation:"):
            indent = raw[: len(raw) - len(raw.lstrip())]
            lines[j] = f"{indent}allow_implicit_invocation: false"
            inserted = True
            break
        j += 1
    if not inserted:
        lines.insert(policy_idx + 1, "  allow_implicit_invocation: false")

sys.stdout.write("\n".join(lines))
if text.endswith("\n"):
    sys.stdout.write("\n")
PY
  mv "$tmp" "$f"
  echo "patched $f"
done
