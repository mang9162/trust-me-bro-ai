---
name: execute-issue
description: Runs one issue-fix folder's TDD tasks. Invoked pointed at a `work/Issue/<NN>-<slug>/` that define-task staged; drains its `Backlog/` in dependency order, dispatching each task to an engineer agent (`agent-skill/<task.type>/` handler, else `agent-skill/default-tdd`) and accepting by the task's own acceptance (red / green / all-green). It is the loop / dispatcher — it does not implement code. Halts and asks the user on any blocking gap; there is no report, and when the queue is drained the run simply ends (no next stage).
---

# Execute Issue

## Purpose

Run the TDD tasks `define-task` staged for one issue fix. Invoked pointed at a single `work/Issue/<NN>-<slug>/` folder; drain that folder's `Backlog/` through the red→green loop, one task at a time in dependency order.

This skill is the **loop / dispatcher** for an issue fix — it does NOT implement code itself. It reads each task, hands it (plus an engineer skill) to an **engineer agent** to execute, and accepts the result against the task's own `acceptance`. The engineer skill is a type handler at `agent-skill/<task.type>/` if one exists, otherwise `agent-skill/default-tdd`. The task carries everything the agent needs (define-task's self-sufficiency bar).

## Procedure

### The loop

Build the queue from every task in the pointed-at `work/Issue/<NN>-<slug>/Backlog/` (define-task authored them — `00-check-test` first, a `regression` gate last), then repeat:

**1. Pick the next task** — scan by `NN` and take the **first** `pending` task whose `depends_on` are all `done`. Always the topmost runnable one.

- No `pending` left → **DRAINED** (see Stop & end).
- `pending` remain but none runnable (every one has an unmet or `failed` `depends_on`) → **DEADLOCK** (see Stop & end).

**2. Pre-flight checklist** — every task:

- [ ] `depends_on` are all `done`
- [ ] read the task in full (`contract` / `cases` / `pseudocode` / `targets` / `assume` / `command` / `acceptance`)
- [ ] confirm `assume` holds — the pre-state is really there. If it doesn't → **BLOCKED** (see Stop & end); don't guess the missing pre-state
- [ ] **`00-check-test`** — its `acceptance` is the project's existing suites all green **before any change is made**. A red baseline is a halt: new code on an already-broken baseline makes later failures impossible to attribute
- [ ] set `status` → `in_progress`; stamp `startedAt` = now (ISO 8601). Don't sync yet — one sync per task, at close-out

**3. Dispatch** — pick the engineer skill, then run it:

- [ ] **skill** = the handler at `agent-skill/<task.type>/` if it exists (its type-specific format layers on top of the plain flow), otherwise `agent-skill/default-tdd`
- [ ] one engineer agent, single context, follows that skill on this one task; it writes the artifact, runs the task's `command`, and **self-verifies the result meets the task's `acceptance` before handing back**

**4. Wait** for the engineer agent to finish.

**5. Accept the result** — re-check the agent's result against the task's **own `acceptance`**:

- a **test task** is expected **RED** — a correctly-red test (e.g. a compile/import error because the function isn't written yet) is a **PASS**, not a failure. Don't "fix" it here; its paired code task turns it green.
- a **code task** is expected **GREEN**; a **`regression` / check task** is expected to run its whole suite green.
- matches `acceptance` → pass, continue.
- doesn't match → **FAILURE** (see Stop & end): set `status` → `failed`, stamp `finishedAt`, and **sync** the task (if set up — see *Sync to the board*).
- while accepting, look over the code/test the engineer wrote. If a coding pattern recurs and is **not** already a rule in `code-standards.md`, note the location where it appears; it feeds the `candidate` in step 6.

**6. Close-out checklist** — every task:

- [ ] set `status` → `done`; stamp `finishedAt` = now; **sync** the task (if set up — see *Sync to the board*)
- [ ] **every** non-blocking issue found this task → `self-report`: a recurring pattern that isn't a rule yet goes as a `candidate` (with its `places` list); other issues go as a `problem`

→ back to step 1.

### Sync to the board

Read the `<!-- syncTarget: <name> -->` marker in `issue.md` (define-task records which board it pushed to). Unset → skip (sync is opt-in). Set → push each task to that board **once, at close-out / failure** (steps 6 / 5) — the single sync carries its final `status`, `startedAt`, `finishedAt`, and actual time. Run its engine on the one task:

`sync-task/sync-task-<syncTarget>/sync-task.sh <that task's .json>`

It updates only that card (idempotent). **Don't** sync on pickup (`in_progress`) — one sync per task, not per transition.

### Stop & end

There is **no report** for an issue run — no `scenario.html` exists; status is read straight from the task files. So none of these refreshes anything — each halt just does its row's action and waits for the user. The core rule is *while a runnable task remains, run it* — these are the cases where the run is **done** or **can't proceed**.

| Outcome | When | Action |
| --- | --- | --- |
| **DRAINED** | no task left (step 1) | tell the user the run is done (all tasks green) and list this run's self-learn items (headlines + tier). **The run ends — there is no next stage**: the `regression` task already ran the full suite + api-test as its `command`. |
| **DEADLOCK** | tasks remain but none runnable — every `pending` has an unmet or `failed` `depends_on` (step 1) | tell the user which task is blocked and why; wait — don't guess |
| **BLOCKED** | an `assume` doesn't hold (step 2) | tell the user to supply/repair the missing pre-state; wait — don't guess it |
| **FAILURE** | result ≠ the task's `acceptance` (step 5) | set the task `failed`; tell the user and wait — downstream depends on it, barrelling ahead spreads the break |

### `self-report` is improve, not fix

`self-report` carries **non-blocking improvement** observations only — e.g. "this pattern keeps getting hand-written; promote it to a `code-standard`?" or "this type recurs and needs special handling; add an `agent-skill/<type>/` handler?". **Blocking** outcomes (DEADLOCK / BLOCKED / FAILURE above) are never silently logged — they halt the run and ask the user right away.

## References

- bridge: `maintenance/define-task/SKILL.md` (`## Layout`) — owns the `work/Issue/<NN>-<slug>/Backlog/` folder layout this run drains (`00-check-test` first, `regression` last); execute-issue is pointed at one such folder, it does not author it.
- cross-ref: `tech-stack/code-standards.md` — checked while accepting (step 5) to see whether a recurring pattern is already a rule, before reporting it as a `candidate`.

## Trigger Skill

- `agent-skill/default-tdd` — the engineer skill the agent follows; the always-present default. A project may add a type-specific `agent-skill/<task.type>/` handler that overrides it for that type (step 3) — that handler is added to `file-map.html` only when it actually exists.
- self-report — non-blocking **improvement** observations (step 6): a recurring code pattern as a `candidate`, other issues as a `problem`. Silent, aggregated; blocking gaps ask the user instead.
- sync-task — at a task's close-out / failure, push that one task to the board named by `issue.md`'s `syncTarget` marker (define-task records it) via its `sync-task-*` engine; skipped when no sync-task skill is installed.

## Writes To

- define-task's task files in `work/Issue/<NN>-<slug>/Backlog/` — advances each task's `status` (`pending` → `in_progress` → `done` / `failed`) and stamps `startedAt` (pickup) / `finishedAt` (close-out) as the loop runs; touches no other field.

## Role & Boundary (Read Before Editing)

This skill owns the **issue-fix execution loop**: pointed at one `work/Issue/<NN>-<slug>/`, it drains that folder's `Backlog/` — pick the topmost runnable task, run the pre-flight / dispatch / close-out checklist, dispatch the task + a skill (`agent-skill/<task.type>/` handler, else `agent-skill/default-tdd`) to an engineer agent, and accept each task by its own `acceptance` (red / green / all-green). It does NOT author tasks (`define-task`), does NOT implement code itself (the engineer agent does, guided entirely by the task), does NOT stage test data / seeds / stubs (anything needing them belongs to the workflow loop), and does NOT own the `work/Issue/` layout (`define-task`). It stamps `startedAt` / `finishedAt` and, when `issue.md` names a `syncTarget`, pushes each finished task to that board (`sync-task-*`), but does NOT own the sync mechanics (`sync-task`). There is no report and no stage handoff — a DRAINED run simply ends.

For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
