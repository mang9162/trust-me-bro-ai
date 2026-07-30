# Build a sync-task installer for a new tracker

Generic guide for wiring `sync-task` to a tracker this kit ships no installer for yet (only **GitHub Projects** exists, under `github-project/`). Copy this shape into a new `initialize-sync-task/<vendor>/` and fill the parts marked *(you supply)* with your tracker's own commands. It says WHAT each step must achieve, not HOW — the how is your tracker's API.

Use `github-project/` as the worked reference: `SKILL.md` (the installer), `skill-format.md` (the generated skill's template), `payload/` (the engine + body templates + config example).

## What you're building

An installer that, each run, produces one self-contained `sync-task/sync-task-<name>/` skill — its own engine, body templates, and config — that pushes staged work (`work/Issue/` / `work/Scenario/`) to ONE board on your tracker, as a parent work item + child work items. Re-run to add more boards.

## What actually differs between trackers

- **The interview** — how you *discover* the targets to offer the user. GitHub has a query API (`gh project list`) to enumerate boards; your tracker exposes its own. The questions you can ask follow from what you can query.
- **The board / field model** — what a "board", a "status", and a "date field" are called, and how they're created.

Everything else stays the same — keep it: the sync mapping, idempotent resync, the editable body format. And the *structure* of how work maps onto the board is the user's choice (captured in the test-loop) — don't hardcode it.

## Installer steps

1. **Preflight** — your tracker's CLI/API is installed and authenticated, with permission to create work items and edit the board. *(you supply: the auth/scope check)*
2. **Name the target** — ask for a short label → `sync-task/sync-task-<name>/`.
3. **Discover + pick the board** — query the tracker for the boards the user can write to; show them; the user picks one. *(you supply: the list query)*
4. **Ensure the board's fields** — it needs a **status** field (the sync maps task status onto it) and, for time tracking, **start / finish date** fields; create them if missing. *(you supply: the field-create calls)*
5. **Collect config** — the per-board settings: which board, the status map (task status → the board's option names), an optional label.
6. **Generate the skill** — into `sync-task/sync-task-<name>/`: copy the engine + body templates, write `config.json`, and write `SKILL.md` from your `skill-format.md`. *(you supply: the engine — see below)*
7. **Test-loop** — sync a throwaway topic, have the user check the board, adjust config/templates, repeat until they accept; then clean up.

## What the engine must do

Given a topic folder (or a single task file), reading `config.json` + templates:

- **Map** — topic → a parent work item (from `issue.md` / `scenario-meta`); each task JSON → a child work item; link each child to its parent; add both to the board; set each item's status from the task's `status` via the status map.
- **Write back the remote id** — into each task's `sync` field and the parent doc — so a re-run is **idempotent**: an already-synced item is updated, never duplicated.
- **Single-task mode** — given one task file, update just that item (for pushing one task's new status/time during execution).
- **Editable body** — render each item's body from templates the user owns.
- **Fail loud** — on any API error, stop and report; never half-write a topic.

## Config shape

Start from `github-project/payload/config.example.json`: the board identifier, `status_map` (task status → board option name), and `label`. Add whatever your tracker needs to identify a board.

## Gotchas (learned on GitHub Projects — check the analogue on yours)

- **ID types** — an API often wants a specific id *type* (numeric db id vs node id) and may fail **silently** on the wrong one — verify links after creating them.
- **Opaque status options** — status option ids often differ per board — look them up by **name** each run, never hardcode.
- **Ordering** — an item usually must be **on the board** before you can set its fields.
