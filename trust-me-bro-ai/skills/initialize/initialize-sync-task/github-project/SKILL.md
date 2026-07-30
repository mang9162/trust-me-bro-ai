---
name: initialize-sync-task-github-project
description: Installs sync-task for one repo against a GitHub Projects board — preflight auth, pick the board, ensure its Status/Date fields, generate a sync-task-<name> skill from skill-format.md, then a test-loop until the user accepts. Re-run to add another board.
---

# Initialize sync-task — GitHub Projects

## Purpose

Set up sync-task for this repo against a **GitHub Projects (v2)** board. Each run produces one self-contained `sync-task-<name>` skill (its own engine, templates, config) that pushes staged work to that board. Re-run to wire up another board / team.

Provider-specific: leans on `gh` + the Projects API. Reached from the `initialize-sync-task` router (which the main `initialize` Phase 4 offers to trigger).

## Procedure

### 1. Preflight auth + tools

`gh` and `jq` are installed, and `gh auth status` is logged in. Token scopes must include **`repo` + `project` + `read:project`**. If `project` is missing, tell the user to run `gh auth refresh -s project,read:project --hostname github.com` (interactive) and wait — the default `gh` token does NOT carry it. No scopes → stop here; the rest can't run.

### 2. Name this target

Ask the user for a short label (e.g. `jabz`) → the generated skill becomes `sync-task/sync-task-<name>/`. This is what lets several boards coexist in one repo.

### 3. Pick the board

List boards: `gh project list --owner <owner>` (`owner` from `git remote get-url origin`). Show them; the user picks one → its **number** is `project_number`. No board yet → help the user create one (`gh project create --owner <owner> --title <name>`) or point them to the web UI, then re-list.

### 4. Map the board's fields — ask, don't assume the names

Field names differ per board, so **ask the user** which existing field to use for each, or whether to create a new one. List what the board has first: `gh project field-list <number> --owner <owner>`.

The sync fills these fields, so confirm one for each (skip any the user doesn't want — it just won't sync):

- **Status** (single-select) — the task's status. Usually already present; its option names go in `status_map` (step 5).
- **Start** (date) — the task's start date (from `startedAt`).
- **End** (date) — the task's finish date (from `finishedAt`).
- **Actual Time** (number) — hours spent = `finish − start` (e.g. `1.5` = 90 min).

Per field, use an existing one (the user picks which — the names vary) OR create it only if they ask:

- date: `gh project field-create <number> --owner <owner> --name "<name>" --data-type DATE`
- number: `gh project field-create <number> --owner <owner> --name "<name>" --data-type NUMBER`

Record the chosen field names in `config.fields` (step 5).

### 5. Collect config

Assemble the values for `config.json` (shape = `payload/config.example.json`):

- `project_number` — from step 3.
- `status_map` — task status → board Status **option name**. Default `{ pending: Todo, in_progress: "In Progress", done: Done, failed: Todo }`; the left side is fixed by `task-schema.md`, the right must match the board's real option names.
- `fields` — the board field **names** chosen in step 4: `{ start, end, actual }`. Leave any `""` to skip syncing it.
- `label` — optional label put on the parent issue; must already exist in the repo, or `""`.

### 6. Generate the skill

Create `sync-task/sync-task-<name>/` and:

- copy `payload/sync-task.sh` into it (then `chmod +x`) and `payload/templates/` alongside it
- write the collected values as `config.json`
- write `SKILL.md` by instantiating `skill-format.md` — fill `<name>` / `<PROJECT_TITLE>` / `<PROJECT_NUMBER>` / `<OWNER>`, dropping its `Target:` line + `## How to scan` section

### 7. Test-loop — until the user is happy

- Stage a tiny throwaway topic inside the repo (one `issue.md` + a task or two, or a small `scenario.html`).
- Run `sync-task/sync-task-<name>/sync-task.sh <that folder>`.
- Tell the user to open the created issues + the board and check titles, body sections, sub-issue nesting, and Status. **Do not judge it for them.**
- Not to taste → adjust `config.json` (project / status names / label) or the `templates/*.jq` (body format), re-run, look again. Repeat.
- Once the user is satisfied, delete the throwaway issues + board items + the scratch folder.

### 8. Done

`sync-task-<name>` is installed. Point the user at how it is used: run it to sync (`define-task` and the workflow also hand off to it). Re-run this installer to add another board.

## References

- cross-ref (no file-map edge): `skill-format.md` — the `sync-task-<name>/SKILL.md` template instantiated in step 6.
- cross-ref (no file-map edge): `payload/sync-task.sh`, `payload/templates/*.jq`, `payload/config.example.json` — copied verbatim into the generated skill (step 6).
- cross-ref: `maintenance/task-schema.md` — the task `status` values (`status_map` left side) + the `startedAt` / `finishedAt` the Date fields hold.

## Writes To

- (no file-map edge) `sync-task/sync-task-<name>/` — the generated skill: `SKILL.md`, `sync-task.sh`, `templates/`, `config.json` (step 6).
- (no file-map edge) the GitHub Projects board — may create Start / End / Actual-Time fields, only if the user asks for new ones (step 4).

## Role & Boundary (Read Before Editing)

This skill owns the **GitHub-Projects-specific setup** for one board: the auth preflight, discovering + choosing the board, ensuring its Status/Date fields, capturing `config.json`, generating the `sync-task-<name>` skill from `skill-format.md`, and the accept test-loop.

It does NOT:

- run syncs or own their mechanics — the generated `sync-task-*` skill + `payload/sync-task.sh` do.
- choose which provider to install — that is the router `initialize-sync-task`.
- support non-GitHub trackers — each gets its own installer; unsupported ones fall back to `initialize-sync-task/default` (`TEMPLATE.md`).
- author or execute tasks — `create-task` / `define-task` / `execute-tdd` / `execute-issue`.

For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
