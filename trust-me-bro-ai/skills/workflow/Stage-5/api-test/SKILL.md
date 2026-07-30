---
name: api-test
description: Stage-5 of workflow. Author the `03-Api-test/` tasks into the project's api-test files and run them, one task at a time in dependency order — the agent running this skill authors each file itself, no dispatch to an engineer agent. Accepts each task against its own `acceptance`; halts and asks the user on a blocking gap (deadlock, failure, an `assume` that doesn't hold); refreshes the report and pauses for Stage 6 when the queue is drained.
---

# Api Test

## Purpose

Stage 5. Take the api-test tasks create-task authored into `03-Api-test/` and turn each into the project's runnable api-test file, one task at a time in dependency order — running each task's `command` and accepting it against its own `acceptance`.

The agent running this skill authors each file itself; it does not dispatch to a separate engineer agent. Reading `gateway-contract.md` for a line's request/response shape is fine when it helps write the `cases` asserts without guessing fields.

## Procedure

### The loop

Build the queue from the `03-Api-test/` tasks, then repeat:

**1. Pick the next task** — scan top→down by `NN` and take the **first** `pending` task whose `depends_on` are all `done`. Always the topmost runnable one.

- No `pending` left → **DRAINED** (loop done — see Stop & pause).
- `pending` remain but none is runnable (each has an unmet or `failed` `depends_on`) → **DEADLOCK** (see Stop & pause).

**2. Pre-flight** — every task:

- [ ] `depends_on` are all `done`
- [ ] read the task in full (`contract` / `cases` / `targets` / `assume` / `command` / `acceptance`)
- [ ] confirm `assume` holds — the pre-state is really there → if not, **BLOCKED** (see Stop & pause); don't guess it
- [ ] set `status` → `in_progress`; stamp `startedAt` = now (ISO 8601). Don't sync yet — one sync per task, at close-out

**3. Author** — write the request into the project's api-test file at the task's `targets.at`, exactly as its `contract` + `cases` specify. The agent running this skill writes it directly — no dispatch. (Reading `gateway-contract.md` for the line's request/response shape is fine, to write the asserts without guessing fields.)

**4. Run** — if the task carries a `command`, run it.

**5. Accept the result** — check it against the task's **own `acceptance`**.

- matches `acceptance` → pass, continue.
- doesn't → **FAILURE** (see Stop & pause): set `status` → `failed`, stamp `finishedAt`, and **sync** the task (if set up — see *Sync to the board*).

**6. Close-out** — every task:

- [ ] set `status` → `done`; stamp `finishedAt` = now; **sync** the task (if set up — see *Sync to the board*)
- [ ] record the run result (actual vs `acceptance`)
- [ ] update the central task / queue so the next pass (step 1) sees the latest status
- [ ] **every** non-blocking issue found this task → `self-report`

→ back to step 1.

### Sync to the board

Read `scenario-meta.syncTarget`. Unset → skip (sync is opt-in). Set → at each task's **close-out / failure** (steps 6 / 5), run `sync-task-<syncTarget>` on that one task — the single sync carries its final `status`, `startedAt`, `finishedAt`, and actual time:

`sync-task/sync-task-<syncTarget>/sync-task.sh <that task's .json>`

It updates only that card (idempotent). **Don't** sync on pickup (`in_progress`) — one sync per task.

### Stop & pause

Every halt/pause first refreshes the report (`generate-report` → `scenario.html`), then does the row's action. The core rule is *while a runnable task remains, run it* — these rows are where the loop is **done** or **can't proceed**.

| Outcome | When | Action (after `generate-report`) |
| --- | --- | --- |
| **DRAINED** | no api-test task left (step 1) | list the self-learn items recorded this stage (headlines + tier), then pause → Stage 6 (`acceptance-review`). No task-by-task dump. |
| **DEADLOCK** | tasks remain but none runnable — each `pending` has an unmet or `failed` `depends_on` (step 1) | ask the user which task is blocked and why; don't guess |
| **BLOCKED** | an `assume` doesn't hold (step 2) | ask the user to supply / repair the missing pre-state; don't guess it |
| **FAILURE** | result ≠ the task's `acceptance` (step 5) | set the task `failed`; ask the user — the feature isn't verified end-to-end, and downstream may depend on it |

### `self-report` is improve, not fix

`self-report` carries **non-blocking improvement** observations only — e.g. "every api-test re-authors the same login/auth step; promote it?". **Blocking** outcomes (DEADLOCK / BLOCKED / FAILURE) are never silently logged — they halt the loop and ask the user right away.

## References

- bridge: `skills/workflow/SKILL.md` (`## Layout`, `## Stages`) — owns the `03-Api-test/` folder paths and the stage gating; Stage 5 runs after Stage 4 and pauses before Stage 6.
- cross-ref: `tech-stack/gateway-contract.md` — a line's request/response shape, read to author / verify the `cases` asserts without guessing fields.

## Trigger Skill

- generate-report — refresh `scenario.html` at every halt/pause (drained / deadlock / blocked / failure).
- self-report — non-blocking **improvement** observations only; blocking gaps ask the user instead.
- sync-task — at a task's close-out / failure, push that one task to `scenario-meta.syncTarget`'s board. Added to `file-map.html` only when a sync-task skill exists.

## Writes To

- (no file-map edge) the project's real api-test files at each task's `targets.at` — the runnable request files written into the project itself (outside the kit — no node).
- create-task's `03-Api-test/` task files — advances each task's `status` (`pending` → `in_progress` → `done` / `failed`) and stamps `startedAt` (pickup) / `finishedAt` (close-out); touches no other field.

## Role & Boundary (Read Before Editing)

This skill owns Stage 5: the loop over `03-Api-test/` — pick the topmost runnable task, author its request into the project's api-test file at `targets.at` (the agent running this skill writes it, no dispatch), run the task's `command` if it has one, and accept it against its **own `acceptance`**. It may read `gateway-contract.md` for a line's request/response shape to write the asserts. It does NOT author the api-test tasks (`create-task`), does NOT run Setup / Backlog or implement feature code (`execute-tdd`), does NOT stage test data / seeds / stubs (`create-test-data`), does NOT define folder paths or stage gating (`workflow`), and does NOT decide accept / reject the scenario (`acceptance-review`). Task `status` uses create-task's set — `pending` / `in_progress` / `done` / `failed`; it also stamps `startedAt` / `finishedAt` and, when a `sync-task-*` skill exists, pushes each finished task to `scenario-meta.syncTarget`'s board (not owning the sync mechanics — `sync-task`). Blocking gaps (deadlock, failure, an `assume` that doesn't hold) halt the loop and ask the user; only non-blocking improvements go to `self-report`. For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
