# sync-task target skill

Target: `sync-task/sync-task-<name>/SKILL.md` — the installer writes this file (one per board) by copying everything below **except** the `Target:` line and the `## How to scan` section, with the `<…>` placeholders replaced.

## How to scan (when filling this file)
- `<name>` — the short label the user gave this sync target (e.g. `jabz`); becomes the folder (`sync-task-<name>`) and the `name:` frontmatter.
- `<PROJECT_TITLE>` / `<PROJECT_NUMBER>` — the board chosen during setup.
- `<OWNER>` — the board's owner (the repo owner unless the board lives elsewhere).
- Replace every `<…>`; drop this section and the `Target:` line from the written file.

---
name: sync-task-<name>
description: Push staged work (work/Issue, work/Scenario) to the "<PROJECT_TITLE>" GitHub Projects board (#<PROJECT_NUMBER>). Invoke the sync-task-* skill for the board you want.
---

# sync-task-<name>

Push a staged topic folder to **<PROJECT_TITLE>** — GitHub Projects #<PROJECT_NUMBER>, owner `<OWNER>`. Idempotent: re-run to update instead of duplicating. `sync-task.sh`, `templates/`, and `config.json` in this folder are this skill's own copy — a sibling `sync-task-*` skill may target another board or even another vendor. Set up by `initialize-sync-task`; re-run it to reconfigure.

## Procedure

### 1. Preflight

`gh` is logged in (`gh auth status`) with `repo` + `project` scopes — the setup added them; if a `gh` call later fails on auth, re-run `gh auth refresh -s project,read:project --hostname github.com`. `gh` + `jq` on PATH.

### 2. Pick what to sync

Two shapes — the engine auto-detects which:

- **A whole topic** (first sync, or a full resync) — walks the parent + every task:
  - **Issue** (from `define-task`) → `work/Issue/<NN>-<slug>/` — parent `issue.md`, tasks under `Backlog/`.
  - **Scenario** (from the workflow) → `work/Scenario/<…>/<NN>-<NAME>/` — parent `scenario.html` (its `scenario-meta`), tasks under `02-Task/{01-Setup,02-Backlog,03-Api-test}/`.
- **A single task** (one `*.json` task file) — updates just that task's card. For when `execute-tdd` / `execute-issue` finishes a task and pushes its new `status` (+ times) back one at a time, instead of resyncing the whole topic. The task must already be synced (its topic was synced once first).

### 3. Summarize long text (optional)

Long text shows as a short human summary above the raw (kept collapsed). Write summaries into one JSON map, save it to a temp file, and pass it as `SYNC_SUMMARIES` (step 4). It is NOT stored in any file. Two kinds of key:

- **task notes** — for any task whose `notes` are long, key by task `id`: `{ "<task-id>": "1–2 line summary" }`.
- **acceptance history** (parent sync) — key by the scenario name; its value is an object keyed by round, one line per acceptance round: `{ "<scenario-name>": { "1": "…", "2": "…" } }`. The parent issue renders these as a per-round list above the raw history.

A task or round with no entry just shows its raw text.

### 4. Run the engine

From this skill's folder, pass the topic folder **or** a single task file:

```sh
[SYNC_SUMMARIES=<map.json>] ./sync-task.sh <topic-folder>   # whole topic
[SYNC_SUMMARIES=<map.json>] ./sync-task.sh <task.json>      # just that one task
```

It reads `config.json` + `templates/` next to it and `owner/repo` from `git remote`. A topic run creates the parent issue + one sub-issue per task, links them, and puts them on the board; a task run updates only that card.

**Re-running is the sync loop** — every run is idempotent (a synced task is updated in place, never duplicated, via the `sync` id written back into each task / the parent doc). Run it again whenever the state changes: a full topic run to refresh everything, or a single-task run right after `execute-tdd` / `execute-issue` advances one task.

### 5. Verify

The script prints created/updated counts + the parent issue number. Open the board to check. On any error it stops and prints why (it never half-writes a topic) — fix and re-run.

## References
- cross-ref: `maintenance/task-schema.md` — the task fields the body renders (`status`, `startedAt` / `finishedAt`, …).

## Writes To
- (no file-map edge) the GitHub repo + <PROJECT_TITLE> board — creates/updates the parent issue, sub-issues, and their board items.
- (no file-map edge) each synced task JSON + the parent doc (`issue.md` / `scenario-meta`) — writes back the `sync` id so a re-run updates in place.

## Role & Boundary (Read Before Editing)
This skill pushes staged work to the **<PROJECT_TITLE>** board only (vendor: GitHub Projects); sibling `sync-task-*` skills push to other boards / vendors. It does NOT author or execute tasks (`create-task` / `define-task` / `execute-tdd` / `execute-issue`) or set up the board (`initialize-sync-task`). For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
