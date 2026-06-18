#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
SHARED_DIR="$REPO_ROOT/docs/ai/shared"
CODEX_INDEX="$REPO_ROOT/.agents/skills/index"
CLAUDE_INDEX="$REPO_ROOT/.claude/skills/index"

mkdir -p "$CODEX_INDEX" "$CLAUDE_INDEX"

ADDED=() REMOVED=() UNCHANGED=()

# Collect previous skill names from existing index
PREV_SKILLS=()
if [[ -f "$CODEX_INDEX/SKILL.md" ]]; then
  while IFS= read -r line; do
    if [[ "$line" =~ ^\-\ \*\*([a-z0-9-]+)\*\* ]]; then
      PREV_SKILLS+=("${BASH_REMATCH[1]}")
    fi
  done < "$CODEX_INDEX/SKILL.md"
fi

# Scan shared skills recursively (supports nested groupings like workflow/Step-1/) and build index list
SKILL_LIST=""
CURRENT_SKILLS=()
while IFS= read -r skill_md; do
  name=$(grep -m1 '^name:' "$skill_md" | sed 's/name: *//' | tr -d '"')
  desc=$(grep -m1 '^description:' "$skill_md" | sed 's/description: *//' | tr -d '"')
  [[ -z "$name" ]] && continue

  rel_path="${skill_md#$REPO_ROOT/}"
  SKILL_LIST+="- **$name**: $desc\n  path: \`$rel_path\`\n"
  CURRENT_SKILLS+=("$name")

  # Determine added vs unchanged
  if printf '%s\n' "${PREV_SKILLS[@]:-}" | grep -qx "$name"; then
    UNCHANGED+=("$name")
  else
    ADDED+=("$name")
  fi
done < <(find "$SHARED_DIR" -name 'SKILL.md' -type f | sort)

# Determine removed skills
for prev in ${PREV_SKILLS[@]+"${PREV_SKILLS[@]}"}; do
  if ! printf '%s\n' "${CURRENT_SKILLS[@]:-}" | grep -qx "$prev"; then
    REMOVED+=("$prev")
  fi
done

# Generate index content
INDEX_CONTENT="---
name: index
description: Master index of all shared team skills. Use when starting any task — read this first to find the right skill, then follow its path to load the full instructions.
---

# Shared Skills Index

<!-- AUTO-GENERATED — do not edit manually, run \$skill-sync instead -->

$(echo -e "$SKILL_LIST")
## How to use
When a task matches a skill above, read the file at its path and follow the instructions there.
Run \$skill-sync after adding or removing skills in docs/ai/shared/."

echo "$INDEX_CONTENT" > "$CODEX_INDEX/SKILL.md"
echo "$INDEX_CONTENT" > "$CLAUDE_INDEX/SKILL.md"

# Report
echo ""
echo "✓ Skill sync complete"
[[ ${#ADDED[@]}     -gt 0 ]] && echo "  Added:     ${ADDED[*]}"
[[ ${#REMOVED[@]}   -gt 0 ]] && echo "  Removed:   ${REMOVED[*]}"
[[ ${#UNCHANGED[@]} -gt 0 ]] && echo "  Unchanged: ${UNCHANGED[*]}"
echo ""
echo "  Codex index  → ${CODEX_INDEX#$REPO_ROOT/}/SKILL.md"
echo "  Claude index → ${CLAUDE_INDEX#$REPO_ROOT/}/SKILL.md"
