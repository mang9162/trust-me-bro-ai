---
name: define-task
description: "Task author for recorded issues (tech debt / bug / hotfix / upkeep) — turns a `kind: issue` entry from `tech-debt.js` into TDD fix tasks under `work/Issue/` that execute-issue runs. Also materializes an approved upgrade-lib handoff without re-planning it."
---

# Define Task

## Purpose

Take one recorded issue — a `kind: issue` entry in `tech-debt.js` (a bug, tech debt, hotfix, or upkeep work noted during earlier work) — and turn it into a fix the user agreed to, staged as atomic TDD tasks that `execute-issue` runs from the task files alone.

This skill PLANS the fix only — it does not implement code or run tests. For an approved `upgrade-lib` handoff, it turns the supplied upgrade detail into the same issue/task format without re-deciding the upgrade.

## Layout (owned by this skill — under `work/`, committed)

```
work/Issue/<NN>-<slug>/
├── issue.md                    ← problem / why fix / expected result
└── Backlog/
    ├── 00-check-test.json      ← always first: existing suites still green
    └── 01-<name>-<type>.json   ← TDD tasks; NN = run order
```

The issue folder's `<NN>` runs across `work/Issue/`; task `NN` restarts per issue folder.

## Procedure

### 1. Receive the entry

The entry `id` may arrive from a feed-back.html copy prompt, typed by the user directly, or handed over right after `self-report` recorded it (the fix-now path) — wherever it comes from, read that entry from `tech-debt.js`: its `problem`, `occurrences`, `places`. No matching entry → ask the user, don't guess.

If `source: upgrade-lib`, receive its human-approved upgrade detail instead; do not read `tech-debt.js`. Missing or ambiguous detail → ask the human, don't guess.

### 2. Scope gate — stays active through every later step

The moment the fix starts feeling big — it needs its own E2E flow, new test data (seed / stub / test-data values), or grows beyond refactor + fix — stop, tell the user, and hand the issue to the workflow loop (`get-requirement`). This can fire here or halfway through breaking down tasks; whenever it fires, stop the same way.

### 3. Agree the fix

Investigate the code at the entry's `places`, then propose how to fix — with options when real alternatives exist. **The user agrees the approach before any task is written.**

For an `upgrade-lib` handoff, its supplied approach is already agreed; do not research releases, choose versions, or change its sequencing.

### 4. Create the issue folder

Create `work/Issue/<NN>-<slug>/` and write `issue.md` with exactly three parts:

- **Problem** — what is wrong (from the entry + investigation)
- **Why fix** — why it must change
- **Expected result** — what holds once the tasks are done

Written for a human to read directly.

For an `upgrade-lib` handoff, use the human-selected new or existing issue folder and its supplied issue detail. When reusing a folder, preserve the existing `Problems and Decisions` section.

### 5. Break the fix into TDD tasks

From the agreed approach, list the functions the fix impacts and assign each its test level (`unit` / `integration` / `component`) — using the level `definition` for that function's service in `testing-guide.md` `## Test Levels` (`tech-stack.md` tells which service a function belongs to); exactly one level per function, never stack. Then, bottom-up, into `Backlog/`:

- **`00-check-test` always first** — its `command` runs the project's existing full test suite + api-test suite, `acceptance` = all green **before any change**: new code on an already-broken baseline makes later failures impossible to attribute. Every later task `depends_on` it.
- **one test task per test case** (never bundle) + the node's `code` task; the code task `depends_on` all its test tasks; mid-issue tasks run only their own level's `command`
- **the LAST task is the regression gate** — type `regression`: its `command` runs the full test suite + api-test suite again, `acceptance` = all green; it `depends_on` every code task

For an `upgrade-lib` handoff, use its supplied dependency change, breaking-change, and validation detail to author this pattern; do not add or remove version steps.

### 6. Write each task to the schema

Author every task JSON to the shared schema in `task-schema.md` (this component) — common fields, conditional fields, self-sufficiency bar, and effort sizing are all defined there; read it before authoring. On top of the schema, this pipeline sets:

- `type` ∈ `unit-test` / `integration-test` / `component-test` / `code-task` / `regression` — no Setup or api-test authoring types here
- `cases` values are concrete, from the agreed fix; there is no test data in this pipeline — no `uses` field

### 7. Design self-review

Before closing the entry, run this checklist over the agreed fix + the functions it impacts (step 5). Any item that fails is a flag — surface it at the pause:
- **Intent match** — each function the fix calls is meant to do what the fix needs there, not merely a same-looking name.
- **No orphan / dangling** — every function the fix adds/changes is actually reached, and every call it makes lands on a function that exists.
- **Alternate outcomes have a path** — miss / empty / error outcomes have a branch, not a silent gap.
- **Test level fits** — each impacted function's level matches what it does, exactly one per function (re-affirms step 5).

### 8. Close the entry

Move the entry out of `tech-debt.js` and append it to `log.js` with `status: done` and `issueFolder` — the folder it became (`work/Issue/<NN>-<slug>/`), which is how `feed-back.html` shows a closed issue. This skill does both writes directly.

Skip this step for an `upgrade-lib` handoff; it has no `tech-debt.js` / `log.js` entry.

### 9. ⏸ PAUSE

Tell the user the issue is staged — point to `issue.md` + the `Backlog/` task list and any design self-review flags. Do not run anything. The user reviews; on approval continue to step 10.

### 10. Sync to the external tracker

On approval, find the `sync-task-*` skills in `skills/sync-task/`. None → skip. Otherwise select the one for this issue, record it in `issue.md` as a trailing `<!-- syncTarget: <name> -->` marker (a comment, invisible when rendered — `execute-issue` reads it to hit the same board), then open it for a **full topic** sync: the parent issue + one sub-issue per task on that board (`execute-issue` then keeps each card updated per task). Either way, the folder is now ready for the user to hand to `execute-issue`.

## References

- cross-ref: `self-learn/tech-debt.js` — the entry (`problem` / `occurrences` / `places`) this skill works from (step 1).
- cross-ref: `task-schema.md` — the shared task JSON schema every authored task follows (step 6).
- cross-ref: `tech-stack/testing-guide.md` — test-level definitions per service + the test structure a test task's `at` follows (steps 5–6).
- cross-ref: `tech-stack/tech-stack.md` — which service a function belongs to (step 5).
- cross-ref: `tech-stack/code-standards.md` — code conventions / hard rules embedded into code tasks (step 6).

## Trigger Skill

- sync-task — a full topic sync of the staged issue + tasks to the selected board via its `sync-task-*` skill (step 10), when one exists in `skills/sync-task/`.

## Writes To

- `work/Issue/<NN>-<slug>/` — `issue.md` (+ a trailing `<!-- syncTarget: <name> -->` marker at step 10 when a sync board is selected) + the `Backlog/` TDD task files (the staged fix).
- `self-learn/tech-debt.js` — the defined entry is removed (step 8); an `upgrade-lib` handoff skips this write.
- `self-learn/log.js` — the closed entry is appended with `status: done` + `issueFolder` (step 8); an `upgrade-lib` handoff skips this write.

## Role & Boundary (Read Before Editing)

This skill owns turning one `kind: issue` entry in `tech-debt.js` into a staged, agreed fix: the joint fix decision, the `work/Issue/<NN>-<slug>/` layout (`issue.md` + `Backlog/` task files — this layout is defined here only, nowhere else), and closing the entry into `log.js`. It also owns materializing an approved `upgrade-lib` handoff into that layout without changing the plan.

It does NOT:

- define the task schema — `task-schema.md` (this component) owns it; this skill authors to it (shared with `create-task`).
- execute tasks or advance their `status` — that is `execute-issue`.
- research releases, choose dependency versions, or change an approved upgrade plan — that is `upgrade-lib` responsibility.
- record new entries — `self-report` is the sole writer of new `tech-debt.js` entries; this skill only moves an already-defined entry out.
- improve the kit itself — that is `self-improve`; this skill plans fixes for the project's app code, never kit files.
- author scenario work — anything needing new test data / seeds / stubs or its own E2E flow belongs to the workflow loop (`get-requirement` onward, tasks by `create-task`).
- own the external sync mechanics — that is `sync-task`; this skill only selects the board, records it as `issue.md`'s `syncTarget` marker, and triggers a full topic sync.

For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
