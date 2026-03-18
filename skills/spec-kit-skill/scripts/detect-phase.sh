#!/usr/bin/env bash

# Spec-Kit Phase Detection Script
# Determines the current phase of a spec-kit feature

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOTSTRAP_SCRIPT="$SCRIPT_DIR/bootstrap-assets.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to detect CLI installation
detect_cli() {
  if command -v specify &> /dev/null; then
    return 0
  fi

  if [ -x "$HOME/.local/bin/specify" ]; then
    return 0
  fi

  if command -v uv &> /dev/null; then
    if uv tool list 2>/dev/null | grep -q "specify-cli"; then
      return 0
    fi
  fi

  return 1
}

# Function to check project initialization
has_specify_dir() {
  [ -d ".specify" ] || [ -d "$HOME/.specify" ]
}

has_constitution_repo() {
  [ -f "specs/constitution.md" ]
}

has_constitution_legacy() {
  [ -f ".specify/memory/constitution.md" ]
}

has_constitution() {
  has_constitution_repo || has_constitution_legacy
}

has_phase_scripts() {
  [ -f ".specify/scripts/bash/detect-phase.sh" ] || [ -f "$HOME/.specify/scripts/bash/detect-phase.sh" ]
}

has_templates() {
  [ -d "$HOME/.specify/templates" ] || [ -d ".specify/templates" ]
}

check_initialization() {
  if ! has_specify_dir; then
    return 1
  fi

  if ! has_constitution; then
    return 2
  fi

  if ! has_phase_scripts || ! has_templates; then
    return 2
  fi

  return 0
}

# Function to get latest feature
get_latest_feature() {
  if [ ! -d "specs" ]; then
    return 0
  fi
  ls -d specs/[0-9]* 2>/dev/null | sort -V | tail -1 || true
}

# Function to map current git branch prefix to a feature directory
get_feature_from_branch() {
  if [ ! -d "specs" ]; then
    return 0
  fi

  local branch=""
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)
  if [[ ! "$branch" =~ ^([0-9]{3})- ]]; then
    return 0
  fi

  local prefix="${BASH_REMATCH[1]}"
  local matches=()
  local dir
  for dir in specs/"$prefix"-*; do
    if [ -d "$dir" ]; then
      matches+=("$dir")
    fi
  done

  if [ "${#matches[@]}" -eq 1 ]; then
    echo "${matches[0]}"
  fi
}

resolve_feature_dir() {
  local from_branch=""
  from_branch=$(get_feature_from_branch)
  if [ -n "$from_branch" ]; then
    echo "$from_branch"
    return 0
  fi
  get_latest_feature
}

# Function to detect phase for a feature
detect_phase() {
  local feature_dir="$1"

  # Phase 1: Constitution
  if ! has_constitution; then
    echo "constitution"
    return 0
  fi

  # Phase 2: Specify
  if [ ! -d "$feature_dir" ] || [ ! -f "$feature_dir/spec.md" ]; then
    echo "specify"
    return 0
  fi

  # Phase 3: Clarify
  if ! grep -q "## Clarifications" "$feature_dir/spec.md" 2>/dev/null; then
    echo "clarify"
    return 0
  fi

  # Phase 4: Plan
  if [ ! -f "$feature_dir/plan.md" ]; then
    echo "plan"
    return 0
  fi

  # Phase 5: Tasks
  if [ ! -f "$feature_dir/tasks.md" ]; then
    echo "tasks"
    return 0
  fi

  # Phase 6/7: Analyze or Implement
  if grep -q "\\- \\[ \\]" "$feature_dir/tasks.md" 2>/dev/null; then
    echo "implement"
    return 0
  fi

  echo "complete"
  return 0
}

# Function to count tasks
count_tasks() {
  local feature_dir="$1"
  local pattern="$2"

  if [ ! -f "$feature_dir/tasks.md" ]; then
    echo "0"
    return
  fi

  grep -c "$pattern" "$feature_dir/tasks.md" 2>/dev/null || echo "0"
}

# Function to generate status report
generate_report() {
  echo -e "${BLUE}=== Spec-Kit Status ===${NC}"
  echo

  # CLI Check
  if detect_cli; then
    echo -e "${GREEN}✓${NC} CLI installed"
    if command -v specify &> /dev/null; then
      specify --version 2>/dev/null | sed 's/^/  /'
    fi
  else
    echo -e "${RED}✗${NC} CLI not installed"
    echo -e "  ${YELLOW}Install:${NC} uv tool install specify-cli --from git+https://github.com/github/spec-kit.git"
  fi
  echo

  # Initialization Check
  if check_initialization; then
    echo -e "${GREEN}✓${NC} Project initialized"
  else
    local init_status=$?
    if [ "$init_status" -eq 2 ]; then
      echo -e "${YELLOW}⚠${NC} Project partially initialized"
      if ! has_constitution; then
        echo -e "  ${YELLOW}Missing:${NC} constitution (specs/constitution.md)"
      fi
      if ! has_phase_scripts; then
        echo -e "  ${YELLOW}Missing:${NC} detect script ({\$HOME,.}/.specify/scripts/bash/detect-phase.sh)"
      fi
      if ! has_templates; then
        echo -e "  ${YELLOW}Missing:${NC} templates ({\$HOME,.}/.specify/templates)"
      fi
      if [ -x "$BOOTSTRAP_SCRIPT" ]; then
        echo -e "  ${YELLOW}Bootstrap:${NC} $BOOTSTRAP_SCRIPT --ensure templates"
      else
        echo -e "  ${YELLOW}Bootstrap:${NC} create \$HOME/.specify/templates"
      fi
      echo -e "  ${YELLOW}Next:${NC} Re-run init: specify init . --ai codex --force"
    else
      echo -e "${RED}✗${NC} Project not initialized"
      echo -e "  ${YELLOW}Initialize:${NC} specify init . --ai codex"
    fi
    return 1
  fi
  echo

  # Constitution Check
  if has_constitution_repo; then
    echo -e "${GREEN}✓${NC} Constitution present"
  elif has_constitution_legacy; then
    echo -e "${YELLOW}⚠${NC} Constitution present at legacy path .specify/memory/constitution.md"
    echo -e "  ${YELLOW}Recommendation:${NC} migrate to specs/constitution.md"
  else
    echo -e "${YELLOW}⚠${NC} Constitution missing"
    echo -e "  ${YELLOW}Next:${NC} Create constitution (Phase 1)"
    return 0
  fi
  echo

  # Features
  local features
  features=$(ls -d specs/[0-9]* 2>/dev/null | sort -V || echo "")

  if [ -z "$features" ]; then
    echo -e "${YELLOW}No features found${NC}"
    echo -e "  ${YELLOW}Next:${NC} Create first feature"
    echo -e "  ${BLUE}Command:${NC} {\$HOME,.}/.specify/scripts/bash/create-new-feature.sh --json 'feature-name'"
    return 0
  fi

  echo -e "${BLUE}Features:${NC}"
  echo "$features" | while read -r feature; do
    local feature_name
    feature_name=$(basename "$feature" | sed 's/^[0-9]\{3\}-//')
    local feature_num
    feature_num=$(basename "$feature" | grep -o '^[0-9]\{3\}')
    local phase
    phase=$(detect_phase "$feature")

    echo -e "  ${GREEN}[$feature_num]${NC} $feature_name"
    echo -e "      Phase: ${YELLOW}$phase${NC}"

    if [ "$phase" = "implement" ] || [ "$phase" = "complete" ]; then
      local completed
      completed=$(count_tasks "$feature" "\\- \\[x\\]")
      local total
      total=$(count_tasks "$feature" "\\- \\[")
      local percentage=0
      if [ "$total" -gt 0 ]; then
        percentage=$((completed * 100 / total))
      fi
      echo -e "      Tasks: ${GREEN}$completed${NC}/${BLUE}$total${NC} ($percentage%)"
    fi
  done
  echo

  # Next Action
  local selected
  selected=$(resolve_feature_dir)
  if [ -n "$selected" ]; then
    local current_phase
    current_phase=$(detect_phase "$selected")
    local feature_name
    feature_name=$(basename "$selected" | sed 's/^[0-9]\{3\}-//')
    echo -e "${BLUE}Next Action:${NC} Continue with ${YELLOW}$current_phase${NC} phase for feature '${GREEN}$feature_name${NC}'"
  fi
}

# Main execution
main() {
  local json_output=false
  local feature_dir=""

  # Parse arguments
  while [[ $# -gt 0 ]]; do
    case $1 in
      --json)
        json_output=true
        shift
        ;;
      --feature)
        feature_dir="$2"
        shift 2
        ;;
      --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Options:"
        echo "  --json            Output in JSON format"
        echo "  --feature DIR     Check specific feature directory"
        echo "  --help, -h        Show this help message"
        exit 0
        ;;
      *)
        echo "Unknown option: $1"
        exit 1
        ;;
    esac
  done

  # If feature specified, just detect its phase
  if [ -n "$feature_dir" ]; then
    local phase
    phase=$(detect_phase "$feature_dir")

    if [ "$json_output" = true ]; then
      echo "{\"phase\": \"$phase\", \"feature_dir\": \"$feature_dir\"}"
    else
      echo "$phase"
    fi
    exit 0
  fi

  # Otherwise, generate full report
  if [ "$json_output" = true ]; then
    # JSON output
    local cli_installed="false"
    detect_cli && cli_installed="true"

    local project_initialized="false"
    check_initialization && project_initialized="true"
    local templates_available="false"
    has_templates && templates_available="true"

    local selected
    selected=$(resolve_feature_dir)
    local selected_phase="none"
    if [ -n "$selected" ]; then
      selected_phase=$(detect_phase "$selected")
    fi

    local latest
    latest=$(get_latest_feature)
    local latest_phase="none"
    if [ -n "$latest" ]; then
      latest_phase=$(detect_phase "$latest")
    fi

    # Backward-compatible alias for selected feature phase.
    local current_phase="$selected_phase"

    local constitution_path=""
    if has_constitution_repo; then
      constitution_path="specs/constitution.md"
    elif has_constitution_legacy; then
      constitution_path=".specify/memory/constitution.md"
    fi

    echo "{"
    echo "  \"cli_installed\": $cli_installed,"
    echo "  \"project_initialized\": $project_initialized,"
    echo "  \"templates_available\": $templates_available,"
    echo "  \"constitution_path\": \"$constitution_path\","
    echo "  \"latest_feature\": \"$latest\","
    echo "  \"latest_phase\": \"$latest_phase\","
    echo "  \"selected_feature\": \"$selected\","
    echo "  \"selected_phase\": \"$selected_phase\","
    echo "  \"current_phase\": \"$current_phase\""
    echo "}"
  else
    # Human-readable output
    generate_report
  fi
}

# Run main function
main "$@"
