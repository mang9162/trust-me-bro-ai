#!/usr/bin/env bash
#
# update-kit.sh — step this installed kit up ONE upstream version at a time.
#
#   status         the installed version + every newer version upstream, in order
#   notes <tag>    what that version fixed / added (release notes, else its commits)
#   plan  <tag>    classify every file the step would touch — writes nothing
#   apply <tag>    write the clean changes; stage each conflict as <path>.incoming
#   finish <tag>   no .incoming left → record the new version
#
# A step compares three trees: the kit AT the installed version (base), the kit at
# the target version (theirs), and what is on disk (ours). A file only counts as a
# conflict when ours differs from base — an untouched file is just updated.
# Files that exist on disk only (knowledge, generated sync-task skills, self-learn
# data) are in no tree and are never touched.
#
# State: <kit>/.kit-version.json  { version, source, path, updatedAt, history[] }
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
STATE="$KIT_DIR/.kit-version.json"

[[ -f "$STATE" ]] || { echo "no $STATE — this kit does not declare its version" >&2; exit 1; }
command -v gh >/dev/null || { echo "gh not found" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq not found" >&2; exit 1; }

CURRENT=$(jq -r '.version' "$STATE")
SOURCE=$(jq -r '.source' "$STATE")
KIT_PATH=$(jq -r '.path // "."' "$STATE")   # where the kit folder sits inside the source repo

# ---------------------------------------------------------------- upstream lookups
tags() {  # every vX.Y.Z tag upstream, oldest first
  gh api "repos/$SOURCE/tags" --paginate --jq '.[].name' \
    | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V
}
newer() {  # the versions above the installed one, in the order they must be applied
  local seen=0 t all
  all=$(tags)
  grep -qx "v$CURRENT" <<<"$all" || { echo "installed version v$CURRENT is not a tag on $SOURCE" >&2; exit 1; }
  while read -r t; do
    if [[ "$t" == "v$CURRENT" ]]; then seen=1; continue; fi
    [[ "$seen" == 1 ]] && printf '%s\n' "$t"
  done <<<"$all"
}
prev_tag() {  # $1=tag -> the tag right before it
  tags | awk -v t="$1" 'p!="" && $0==t {print p; exit} {p=$0}'
}
fetch_tree() {  # $1=tag  $2=dest — extract the kit folder at that tag into $2
  local tmp root; tmp=$(mktemp -d)
  gh api "repos/$SOURCE/tarball/$1" >"$tmp/kit.tgz"
  tar -xzf "$tmp/kit.tgz" -C "$tmp"
  root=$(find "$tmp" -mindepth 1 -maxdepth 1 -type d | head -1)
  [[ -d "$root/$KIT_PATH" ]] || { echo "no '$KIT_PATH' inside $SOURCE at $1" >&2; exit 1; }
  mkdir -p "$2"; cp -R "$root/$KIT_PATH/." "$2/"
  rm -rf "$tmp"
}

# ---------------------------------------------------------------- the three-way compare
classify() {  # $1=base tree  $2=target tree -> "STATUS<TAB>relpath" lines
  local base="$1" theirs="$2" rel b t o
  while read -r rel; do
    [[ "$rel" == ".kit-version.json" ]] && continue
    b="$base/$rel"; t="$theirs/$rel"; o="$KIT_DIR/$rel"
    if [[ -f "$b" && -f "$t" ]] && cmp -s "$b" "$t"; then
      continue                                            # upstream left it alone
    elif [[ -f "$o" ]] && [[ -f "$t" ]] && cmp -s "$o" "$t"; then
      continue                                            # already what the target ships
    elif [[ ! -f "$t" ]]; then                            # upstream deleted it
      if   [[ ! -f "$o" ]];        then continue
      elif cmp -s "$o" "$b";       then printf 'REMOVE\t%s\n' "$rel"
      else                              printf 'CONFLICT-DELETE\t%s\n' "$rel"
      fi
    elif [[ ! -f "$o" ]]; then                            # not on disk → take it
      printf 'ADD\t%s\n' "$rel"
    elif [[ ! -f "$b" ]]; then                            # new upstream, but a file is in the way
      printf 'CONFLICT\t%s\n' "$rel"
    elif cmp -s "$o" "$b"; then                           # untouched locally
      printf 'UPDATE\t%s\n' "$rel"
    else                                                  # edited on both sides
      printf 'CONFLICT\t%s\n' "$rel"
    fi
  done < <({ (cd "$base" && find . -type f); (cd "$theirs" && find . -type f); } | sed 's|^\./||' | sort -u)
}
step_trees() {  # $1=tag — fills BASE_TREE / TARGET_TREE
  BASE_TREE=$(mktemp -d); TARGET_TREE=$(mktemp -d)
  fetch_tree "v$CURRENT" "$BASE_TREE"
  fetch_tree "$1" "$TARGET_TREE"
}
one_step_only() {  # $1=tag — refuse to jump versions
  local next; next=$(newer | head -1)
  [[ -n "$next" ]] || { echo "already at $CURRENT — nothing newer upstream" >&2; exit 1; }
  [[ "$1" == "$next" ]] || { echo "next version is $next, not $1 — one version at a time" >&2; exit 1; }
}

# ---------------------------------------------------------------- subcommands
cmd_status() {
  printf 'installed %s   source %s\n' "$CURRENT" "$SOURCE"
  local n; n=$(newer)
  [[ -n "$n" ]] || { echo "up to date"; return 0; }
  echo "newer versions, apply in this order:"
  printf '%s\n' "$n" | sed 's/^/  /'
}
cmd_notes() {  # $1=tag
  local body prev
  body=$(gh release view "$1" --repo "$SOURCE" --json body --jq '.body' 2>/dev/null || true)
  if [[ -n "$body" && "$body" != "null" ]]; then printf '%s\n' "$body"; return 0; fi
  prev=$(prev_tag "$1")
  [[ -n "$prev" ]] || { echo "(no release notes and no earlier tag to compare against)"; return 0; }
  echo "(no release notes — commits since $prev)"
  gh api "repos/$SOURCE/compare/$prev...$1" --jq '.commits[].commit.message' | grep -v '^$' | sed 's/^/  /'
}
cmd_plan() {  # $1=tag
  one_step_only "$1"
  step_trees "$1"
  classify "$BASE_TREE" "$TARGET_TREE"
  rm -rf "$BASE_TREE" "$TARGET_TREE"
}
cmd_apply() {  # $1=tag
  one_step_only "$1"
  step_trees "$1"
  local st rel
  while IFS=$'\t' read -r st rel; do
    case "$st" in
      ADD|UPDATE)      mkdir -p "$KIT_DIR/$(dirname "$rel")"; cp "$TARGET_TREE/$rel" "$KIT_DIR/$rel" ;;
      REMOVE)          rm -f "$KIT_DIR/$rel" ;;
      CONFLICT)        cp "$TARGET_TREE/$rel" "$KIT_DIR/$rel.incoming" ;;
      CONFLICT-DELETE) : ;;   # nothing to stage — upstream dropped the file, the local edit stays
    esac
    printf '%s\t%s\n' "$st" "$rel"
  done < <(classify "$BASE_TREE" "$TARGET_TREE")
  rm -rf "$BASE_TREE" "$TARGET_TREE"
}
cmd_finish() {  # $1=tag
  one_step_only "$1"
  local left v today
  left=$(find "$KIT_DIR" -name '*.incoming')
  [[ -z "$left" ]] || { echo "unresolved conflicts:" >&2; printf '%s\n' "$left" >&2; exit 1; }
  v="${1#v}"; today=$(date +%F)
  jq --arg v "$v" --arg f "$CURRENT" --arg d "$today" \
     '.history += [{version:$v, from:$f, date:$d}] | .version=$v | .updatedAt=$d' \
     "$STATE" >"$STATE.tmp" && mv "$STATE.tmp" "$STATE"
  echo "kit is now $v"
}

case "${1:-}" in
  status) cmd_status ;;
  notes)  cmd_notes  "${2:?usage: update-kit.sh notes <tag>}" ;;
  plan)   cmd_plan   "${2:?usage: update-kit.sh plan <tag>}" ;;
  apply)  cmd_apply  "${2:?usage: update-kit.sh apply <tag>}" ;;
  finish) cmd_finish "${2:?usage: update-kit.sh finish <tag>}" ;;
  *) echo "usage: update-kit.sh {status | notes <tag> | plan <tag> | apply <tag> | finish <tag>}" >&2; exit 1 ;;
esac
