---
name: initialize-sync-task
description: Router for setting up external task sync — asks which tracker, then hands off to that vendor's installer. Today: GitHub Projects; other trackers fall back to a DIY template. Re-run to add another board / vendor.
---

# Initialize sync-task

## Purpose

Set up sync-task for this repo against an external tracker. Pick the vendor; its installer does the rest, producing a `sync-task-<name>` skill that pushes staged work to one board. Re-run to wire up another board or vendor.

## Procedure

### 1. Pick the tracker

Ask which tracker to sync to:

- **GitHub Projects** → open `github-project/SKILL.md` and follow it.
- **anything else** → not yet supported; point the user to `default/TEMPLATE.md` — the DIY guide for building an installer for that tracker.

### 2. Re-runnable

Invoke again any time to add another board or vendor — each becomes its own `sync-task-<name>` skill, and they coexist.

## Trigger Skill

- initialize-sync-task-github-project — install a GitHub Projects board target (when the user picks GitHub).

## References

- cross-ref (no file-map edge): `default/TEMPLATE.md` — the DIY guide handed to the user when the chosen tracker has no installer yet.

## Role & Boundary (Read Before Editing)

This skill owns only the **vendor choice** for external task sync — routing to the right installer. It does NOT do the setup itself (each `<vendor>/SKILL.md`), run syncs (the generated `sync-task-*` skills), or author / execute tasks. For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
