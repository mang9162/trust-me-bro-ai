#!/usr/bin/env bash
#
# sync-task.sh — push one topic folder to GitHub as a parent issue + sub-issues
# on a Project board. Idempotent: re-running updates instead of duplicating.
#
# Branch auto-detected by the parent doc in the folder:
#   Issue    branch → <topic>/issue.md
#   Scenario branch → <topic>/scenario.html  (parent data in <script id="scenario-meta">)
#
# Remote id is written back so a resync knows update-vs-create:
#   task   → `sync` field inside the task JSON
#   parent → issue.md: trailing HTML-comment marker  |  scenario: scenario-meta.sync
#
# Body FORMAT is owned by editable templates (edit these, not this script):
#   $SYNC_TEMPLATES/task-body.jq        — sub-issue body
#   $SYNC_TEMPLATES/scenario-parent.jq  — scenario parent body
#
# Usage:  sync-task.sh [--parent] <topic-folder | task.json>
#           <folder>        sync the whole topic (parent + every task)
#           <task.json>     update just that one task's card
#           --parent <dir>  sync only the parent (rollup from the tasks, don't touch their cards)
# Config: $SYNC_CONFIG    else <script-dir>/config.json      (see config.example.json)
# Tpls:   $SYNC_TEMPLATES else <script-dir>/templates
#
set -euo pipefail

# ---------------------------------------------------------------- args + deps
PARENT_ONLY=0
if [[ "${1:-}" == "--parent" ]]; then PARENT_ONLY=1; shift; fi
INPUT="${1:?usage: sync-task.sh [--parent] <topic-folder | task.json>}"
INPUT="${INPUT%/}"
# topic root = the folder holding issue.md / scenario.html at or above a path
find_topic_root() {
  local d; d=$(cd "$(dirname "$1")" 2>/dev/null && pwd) || return 1
  while [[ -n "$d" && "$d" != "/" ]]; do
    [[ -f "$d/issue.md" || -f "$d/scenario.html" ]] && { printf '%s' "$d"; return 0; }
    d=$(dirname "$d")
  done
  return 1
}
if [[ -d "$INPUT" ]]; then
  MODE=topic; TOPIC="$INPUT"
elif [[ -f "$INPUT" ]]; then
  MODE=task; TASK_FILE="$INPUT"
  TOPIC=$(find_topic_root "$INPUT") || { echo "no issue.md / scenario.html above $INPUT" >&2; exit 1; }
else
  echo "not a folder or file: $INPUT" >&2; exit 1
fi
[[ "$PARENT_ONLY" == 1 && "$MODE" == task ]] && { echo "--parent needs a topic folder, not a task file" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SYNC_CONFIG:-$SCRIPT_DIR/config.json}"
TPL_DIR="${SYNC_TEMPLATES:-$SCRIPT_DIR/templates}"
[[ -f "$CONFIG" ]] || { echo "missing config: $CONFIG (copy config.example.json)" >&2; exit 1; }
[[ -f "$TPL_DIR/task-body.jq" ]] || { echo "missing template: $TPL_DIR/task-body.jq" >&2; exit 1; }

command -v gh >/dev/null || { echo "gh not found" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq not found" >&2; exit 1; }

PROJECT_NUMBER=$(jq -r '.project_number' "$CONFIG")
LABEL=$(jq -r '.label // ""' "$CONFIG")
START_FIELD=$(jq -r '.fields.start // ""' "$CONFIG")
END_FIELD=$(jq -r '.fields.end // ""' "$CONFIG")
ACTUAL_FIELD=$(jq -r '.fields.actual // ""' "$CONFIG")
ASSIGN_ON_DONE=$(jq -r '.assign_syncer_on_done // false' "$CONFIG")
SYNCER_LOGIN=""
if [[ "$ASSIGN_ON_DONE" == true ]]; then
  SYNCER_LOGIN=$(gh api user --jq '.login' 2>/dev/null || true)
  [[ -n "$SYNCER_LOGIN" ]] || echo "warn: assign_syncer_on_done is on but the gh account couldn't be resolved — done tasks won't be assigned" >&2
fi

# ---------------------------------------------------------------- repo / owner
REMOTE_URL=$(git -C "$TOPIC" remote get-url origin)
SLUG=$(sed -E 's#(git@[^:]+:|https?://[^/]+/)##; s#\.git$##' <<<"$REMOTE_URL")
OWNER="${SLUG%%/*}"
REPO="${SLUG#*/}"
ROOT=$(git -C "$TOPIC" rev-parse --show-toplevel)

# ---------------------------------------------------------------- one-time lookups
PROJECT_VIEW=$(gh project view "$PROJECT_NUMBER" --owner "$OWNER" --format json)
PROJECT_ID=$(jq -r '.id' <<<"$PROJECT_VIEW")
BOARD_URL=$(jq -r '.url // ""' <<<"$PROJECT_VIEW")
FIELDS_JSON=$(gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json)
STATUS_FIELD_ID=$(jq -r '.fields[] | select(.name=="Status") | .id' <<<"$FIELDS_JSON")
[[ -n "$STATUS_FIELD_ID" ]] || { echo "board has no Status field" >&2; exit 1; }

status_option_id() {  # board option name -> option id (looked up by name, never hardcoded)
  jq -r --arg n "$1" '.fields[] | select(.name=="Status") | .options[] | select(.name==$n) | .id' <<<"$FIELDS_JSON"
}
status_board_name() {  # task status -> board option name via config.status_map
  jq -r --arg s "$1" '.status_map[$s] // .status_map.pending' "$CONFIG"
}
field_id() {  # board field name -> field id ("" if the board has no such field)
  jq -r --arg n "$1" '.fields[] | select(.name==$n) | .id' <<<"$FIELDS_JSON"
}
set_date() {  # $1=item  $2=board_field_name  $3=iso_datetime  (skips if unmapped/absent)
  local fid; [[ -n "$2" && -n "$3" ]] || return 0
  fid=$(field_id "$2"); [[ -n "$fid" ]] || return 0
  gh project item-edit --id "$1" --project-id "$PROJECT_ID" --field-id "$fid" --date "${3%%T*}" >/dev/null
}
set_actual() {  # $1=item  $2=started_iso  $3=finished_iso  -> writes duration in hours
  local fid hours; [[ -n "$ACTUAL_FIELD" && -n "$2" && -n "$3" ]] || return 0
  fid=$(field_id "$ACTUAL_FIELD"); [[ -n "$fid" ]] || return 0
  hours=$(jq -rn --arg s "$2" --arg f "$3" '(($f|fromdateiso8601)-($s|fromdateiso8601))/3600 | (.*100|round)/100' 2>/dev/null) || return 0
  gh project item-edit --id "$1" --project-id "$PROJECT_ID" --field-id "$fid" --number "$hours" >/dev/null
}
type_label() {  # raw task type -> display label used in the issue title  (edit to taste)
  case "$1" in
    unit-test)        echo "Unit Test" ;;
    integration-test) echo "Integration Test" ;;
    component-test)   echo "Component Test" ;;
    code-task)        echo "Code" ;;
    env-setup)        echo "ENV-Setup" ;;
    api-test)         echo "API Test" ;;
    interface)        echo "Interface" ;;
    error_code)       echo "Error Code" ;;
    regression)       echo "Regression" ;;
    *)                echo "$1" ;;
  esac
}

# ---------------------------------------------------------------- gh helpers
issue_num_from_url() { grep -oE '[0-9]+$' <<<"$1"; }
issue_db_id()       { gh api "repos/$OWNER/$REPO/issues/$1" --jq '.id'; }

create_issue() {  # $1=title  $2=body_file  [$3=label] -> prints issue URL
  local args=(--repo "$OWNER/$REPO" --title "$1" --body-file "$2")
  [[ -n "${3:-}" ]] && args+=(--label "$3")
  gh issue create "${args[@]}"
}
edit_issue() {  # $1=number  $2=title  $3=body_file
  gh issue edit "$1" --repo "$OWNER/$REPO" --title "$2" --body-file "$3" >/dev/null
}

link_sub() {  # $1=parent_num  $2=child_num  (sub_issue_id must be the numeric db id, sent as integer)
  local cid; cid=$(issue_db_id "$2")
  gh api --method POST "repos/$OWNER/$REPO/issues/$1/sub_issues" -F "sub_issue_id=$cid" >/dev/null
  # verify — the link API fails SILENTLY on a bad id type, so confirm it took
  gh api "repos/$OWNER/$REPO/issues/$1/sub_issues" --jq '.[].number' | grep -qx "$2" \
    || { echo "sub-issue link failed: #$2 -> #$1" >&2; exit 1; }
}

board_item_id() {  # $1=issue_number -> project item id ("" if not on board)
  gh project item-list "$PROJECT_NUMBER" --owner "$OWNER" --limit 200 --format json \
    | jq -r --arg n "$1" '.items[] | select(.content.number == ($n|tonumber)) | .id' | head -1
}
ensure_on_board() {  # $1=issue_url  $2=issue_number -> prints item id (adds if missing)
  local id; id=$(board_item_id "$2")
  [[ -n "$id" ]] || id=$(gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" --url "$1" --format json | jq -r '.id')
  printf '%s' "$id"
}
set_status() {  # $1=item_id  $2=board_option_name  (item must already be on board)
  local opt; opt=$(status_option_id "$2")
  [[ -n "$opt" ]] || { echo "no Status option named '$2' on board" >&2; exit 1; }
  gh project item-edit --id "$1" --project-id "$PROJECT_ID" --field-id "$STATUS_FIELD_ID" \
    --single-select-option-id "$opt" >/dev/null
}
assign_syncer() {  # $1=issue_number — assign the syncing gh account (done tasks only, when enabled)
  [[ "$ASSIGN_ON_DONE" == true && -n "$SYNCER_LOGIN" ]] || return 0
  gh issue edit "$1" --repo "$OWNER/$REPO" --add-assignee "$SYNCER_LOGIN" >/dev/null 2>&1 \
    || echo "  warn: could not assign $SYNCER_LOGIN to #$1" >&2
}

# ---------------------------------------------------------------- body (from templates)
# Optional $SYNC_SUMMARIES = path to a JSON map the playbook (AI) writes at sync time; it is
# NOT stored in any file. Two kinds of key: a task `id` → a short `notes` summary string;
# the scenario name → an object keyed by round for the acceptance history
# ({ "<task-id>": "…", "<scenario>": { "1": "…", "2": "…" } }). Missing entry → raw shown, collapsed.
task_body() {  # $1=task_json  $2=rel_path -> stdout
  local sum=""
  if [[ -n "${SYNC_SUMMARIES:-}" && -f "${SYNC_SUMMARIES:-}" ]]; then
    sum=$(jq -r --arg id "$(jq -r '.id // ""' "$1")" '.[$id] // ""' "$SYNC_SUMMARIES")
  fi
  jq -r --arg rel "$2" --arg scenario "$SCENARIO_NAME" --arg summary "$sum" -f "$TPL_DIR/task-body.jq" "$1"
}

process_task() {  # $1=task_json
  local f="$1" rel tp title status status_name sync_id url num bodyfile item started finished
  rel="${f#"$ROOT"/}"
  tp=$(jq -r '.type // "task"' "$f")
  title="[$(type_label "$tp")] $(jq -r '.title // .id // "task"' "$f")"
  status=$(jq -r '.status // "pending"' "$f")
  status_name=$(status_board_name "$status")
  sync_id=$(jq -r '.sync.id // empty' "$f")
  bodyfile=$(mktemp); task_body "$f" "$rel" >"$bodyfile"

  if [[ -n "$sync_id" ]]; then
    edit_issue "$sync_id" "$title" "$bodyfile"; num="$sync_id"
    url="https://github.com/$OWNER/$REPO/issues/$num"
    UPDATED=$((UPDATED+1))
  else
    url=$(create_issue "$title" "$bodyfile")
    num=$(issue_num_from_url "$url")
    link_sub "$PARENT_NUM" "$num"
    jq --argjson s "{\"id\":$num,\"url\":\"$url\"}" '.sync=$s' "$f" >"$f.tmp" && mv "$f.tmp" "$f"
    CREATED=$((CREATED+1))
  fi
  rm -f "$bodyfile"

  item=$(ensure_on_board "$url" "$num")
  set_status "$item" "$status_name"
  if [[ "$status" == done ]]; then assign_syncer "$num"; fi
  started=$(jq -r '.startedAt // empty' "$f"); finished=$(jq -r '.finishedAt // empty' "$f")
  set_date "$item" "$START_FIELD" "$started"
  set_date "$item" "$END_FIELD" "$finished"
  set_actual "$item" "$started" "$finished"
  TASK_STATUSES+=("$status")
  echo "  task #$num  $(basename "$f")"
}

tasks_list() {  # emit task json paths, NN order
  if [[ "$KIND" == scenario ]]; then find "$TOPIC/02-Task" -type f -name '*.json' 2>/dev/null | sort
  else                                find "$TOPIC" -type f -name '*.json' 2>/dev/null | sort; fi
}

rollup_status() {  # parent status derived from child task statuses
  local all_done=1 any=0 s
  [[ ${#TASK_STATUSES[@]} -gt 0 ]] || { echo pending; return; }
  for s in "${TASK_STATUSES[@]}"; do
    [[ "$s" == done ]] || all_done=0
    [[ "$s" == pending ]] || any=1
  done
  if   [[ $all_done -eq 1 ]]; then echo done
  elif [[ $any -eq 1 ]];      then echo in_progress
  else                             echo pending; fi
}

# ---------------------------------------------------------------- parent: Issue branch
parent_issue_md() {
  local doc="$TOPIC/issue.md" title marker bodyfile json url
  title="[Issue] $SCENARIO_NAME"
  marker=$(grep -oE '<!-- sync: \{.*\} -->' "$doc" | head -1 || true)
  bodyfile=$(mktemp)
  # strip both kit-internal markers from the pushed body: the sync id and define-task's syncTarget
  grep -v -E '<!-- sync: \{.*\} -->|<!-- syncTarget: .* -->' "$doc" >"$bodyfile"
  printf '\n---\n_Synced from Trust me bro ai · %s_\n' "$SCENARIO_NAME" >>"$bodyfile"
  if [[ -n "$marker" ]]; then
    PARENT_NUM=$(sed -E 's/^<!-- sync: (.*) -->$/\1/' <<<"$marker" | jq -r '.id')
    edit_issue "$PARENT_NUM" "$title" "$bodyfile"
    url="https://github.com/$OWNER/$REPO/issues/$PARENT_NUM"
  else
    url=$(create_issue "$title" "$bodyfile" "$LABEL"); PARENT_NUM=$(issue_num_from_url "$url")
  fi
  # (re)write the marker so its url/board stay current
  grep -v -E '<!-- sync: \{.*\} -->' "$doc" >"$doc.tmp" && mv "$doc.tmp" "$doc"
  printf '\n<!-- sync: {"id":%s,"url":"%s","board":"%s"} -->\n' "$PARENT_NUM" "$url" "$BOARD_URL" >>"$doc"
  PARENT_URL="https://github.com/$OWNER/$REPO/issues/$PARENT_NUM"
  rm -f "$bodyfile"
}

# ---------------------------------------------------------------- parent: Scenario branch
meta_json() {  # extract the JSON inside <script id="scenario-meta">
  awk '/<script[^>]*id="scenario-meta"/{f=1;next} f&&/<\/script>/{f=0} f' "$TOPIC/scenario.html"
}
write_meta_sync() {  # $1=id  $2=url — add .sync into the scenario-meta block, rebuild scenario.html
  local metaf; metaf=$(mktemp)
  meta_json | jq --argjson s "{\"id\":$1,\"url\":\"$2\",\"board\":\"$BOARD_URL\"}" '.sync=$s' >"$metaf"
  awk -v METAF="$metaf" '
    /<script[^>]*id="scenario-meta"/{print; while((getline l < METAF)>0) print l; close(METAF); skip=1; next}
    skip&&/<\/script>/{skip=0; print; next}
    skip{next}
    {print}' "$TOPIC/scenario.html" >"$TOPIC/scenario.html.tmp" && mv "$TOPIC/scenario.html.tmp" "$TOPIC/scenario.html"
  rm -f "$metaf"
}
parent_scenario() {
  local title sync_id bodyfile url meta cat feature datatest testdata counts fndesign summary
  meta=$(meta_json)
  title="[Scenario] $SCENARIO_NAME"
  sync_id=$(jq -r '.sync.id // empty' <<<"$meta")

  # --- gather the rich body's data (from the scenario folder) ---
  cat=$(jq -r '.category // ""' <<<"$meta")
  feature=""
  if [[ -n "$cat" ]]; then
    feature=$(sed -E "s/_$(printf '%s' "$cat" | tr '[:lower:]' '[:upper:]')_[0-9]+$//" <<<"$SCENARIO_NAME")
    [[ "$feature" == "$SCENARIO_NAME" ]] && feature=""
  fi
  datatest="$TOPIC/01-Testdata/Datatest.md"
  # keep only the section headings + tables (drop the intro prose); nest headings under ## Test Data
  testdata=""; [[ -f "$datatest" ]] && testdata=$(awk '/^## /{sub(/^## /,"### "); print ""; print; print ""; next} /^\|/{print}' "$datatest")
  counts=$(find "$TOPIC/02-Task" -type f -name '*.json' -exec jq -s \
    '{byType:(group_by(.type)|map({key:(.[0].type//"?"),value:length})|from_entries),mocks:([.[].uses.stubs//[]]|add//[]|unique|length)}' {} + 2>/dev/null)
  [[ -n "$counts" ]] || counts='{"byType":{},"mocks":0}'
  fndesign=$(grep -oE 'class="fn-node[^"]*">[^<]+' "$TOPIC/scenario.html" 2>/dev/null | sed -E 's/.*">//' | sed '/^$/d' || true)
  # acceptance-history summary — AI writes it into $SYNC_SUMMARIES keyed by the scenario name;
  # its value is an object keyed by round ({ "<scenario>": { "1": "...", "2": "..." } }); ephemeral
  summary="{}"
  if [[ -n "${SYNC_SUMMARIES:-}" && -f "${SYNC_SUMMARIES:-}" ]]; then
    summary=$(jq -c --arg k "$SCENARIO_NAME" '.[$k] // {}' "$SYNC_SUMMARIES")
  fi

  bodyfile=$(mktemp)
  printf '%s' "$meta" | jq -r \
    --arg scenario "$SCENARIO_NAME" --arg repo "$OWNER/$REPO" --arg feature "$feature" \
    --arg testdata "$testdata" --argjson counts "$counts" --arg fndesign "$fndesign" \
    --argjson summary "$summary" \
    -f "$TPL_DIR/scenario-parent.jq" >"$bodyfile"
  if [[ -n "$sync_id" ]]; then
    PARENT_NUM="$sync_id"; edit_issue "$PARENT_NUM" "$title" "$bodyfile"
    write_meta_sync "$PARENT_NUM" "https://github.com/$OWNER/$REPO/issues/$PARENT_NUM"
  else
    url=$(create_issue "$title" "$bodyfile" "$LABEL"); PARENT_NUM=$(issue_num_from_url "$url")
    write_meta_sync "$PARENT_NUM" "$url"
  fi
  PARENT_URL="https://github.com/$OWNER/$REPO/issues/$PARENT_NUM"
  rm -f "$bodyfile"
}

# ---------------------------------------------------------------- main
if   [[ -f "$TOPIC/issue.md" ]];      then KIND=issue
elif [[ -f "$TOPIC/scenario.html" ]]; then KIND=scenario
else echo "no issue.md or scenario.html in $TOPIC" >&2; exit 1; fi

# full scenario/topic name (used in body footer + parent title)
if [[ "$KIND" == scenario ]]; then
  SCENARIO_NAME=$(meta_json | jq -r '.scenario // "scenario"')
else
  SCENARIO_NAME=$(grep -m1 -E '^# ' "$TOPIC/issue.md" | sed -E 's/^#+ +//')
  [[ -n "$SCENARIO_NAME" ]] || SCENARIO_NAME=$(basename "$TOPIC")
fi

CREATED=0; UPDATED=0; TASK_STATUSES=()

# ---- single task: update just this one (must already be synced with the topic) ----
if [[ "$MODE" == task ]]; then
  if [[ -z "$(jq -r '.sync.id // empty' "$TASK_FILE")" ]]; then
    echo "task not synced yet (no .sync.id) — run a full topic sync first: sync-task.sh $TOPIC" >&2; exit 1
  fi
  echo "sync (single task, $KIND): $TASK_FILE  →  $OWNER/$REPO  project #$PROJECT_NUMBER"
  process_task "$TASK_FILE"
  echo "done: updated 1 task"
  exit 0
fi

# ---- topic: the parent (+ every task, unless --parent) ----
echo "sync ($KIND$([[ $PARENT_ONLY == 1 ]] && echo ', parent-only')): $TOPIC  →  $OWNER/$REPO  project #$PROJECT_NUMBER"
if [[ "$KIND" == issue ]]; then parent_issue_md; else parent_scenario; fi
echo "  parent #$PARENT_NUM"
PARENT_ITEM=$(ensure_on_board "$PARENT_URL" "$PARENT_NUM")

while IFS= read -r taskfile; do
  [[ -n "$taskfile" ]] || continue
  if [[ "$PARENT_ONLY" == 1 ]]; then
    TASK_STATUSES+=("$(jq -r '.status // "pending"' "$taskfile")")   # rollup only — don't touch task cards
  else
    process_task "$taskfile"
  fi
done < <(tasks_list)

set_status "$PARENT_ITEM" "$(status_board_name "$(rollup_status)")"
echo "done: created=$CREATED updated=$UPDATED  parent-status=$(rollup_status)"
