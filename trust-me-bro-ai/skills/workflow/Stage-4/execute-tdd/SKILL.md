---
name: execute-tdd
description: Stage-4 of workflow. The central TDD execution loop. Drains the Setup + Backlog tasks authored by create-task in dependency order; for each task it runs a pre-flight / dispatch / close-out checklist, hands the task + a skill (the type handler at `execute-tdd/<task.type>/` if one exists, otherwise `execute-tdd/default-tdd`) to an engineer agent, then accepts the result against the task's own acceptance (red / green / compiles). Does not implement code itself. Halts and asks the user on a blocking gap (deadlock, failure, an assume that doesn't hold); refreshes the report and pauses when the queue is drained, then hands off to Stage 5.
---

# Execute TDD

## Purpose

Stage 4. Take the atomic tasks create-task authored into `01-Setup/` + `02-Backlog/` and run them through the TDD red→green loop, one task at a time in dependency order.

This skill is the **central loop / dispatcher** — it does NOT implement code itself. It reads each task, hands it (plus a skill) to an **engineer agent** to execute, and accepts the result against the task's own `acceptance`. The skill the agent follows is either a type-specific handler (`execute-tdd/<task.type>/`) or, by default, `execute-tdd/default-tdd` (the plain TDD procedure). The task carries everything the agent needs (create-task's self-sufficiency bar).

## Procedure

### The loop

Build the queue from the Setup + Backlog tasks, then repeat:

**1. Pick the next task** — scan top→down (Setup before Backlog, then by `NN`) and take the **first** `pending` task whose `depends_on` are all `done`. Always the topmost runnable one.

- No `pending` left → **DRAINED** (loop done — see Stop & pause).
- `pending` remain but none is runnable (every one has an unmet or `failed` `depends_on`) → **DEADLOCK** (see Stop & pause).

**2. Pre-flight checklist** — every task, regardless of type:

- [ ] `depends_on` are all `done`
- [ ] read the task in full (`contract` / `cases` / `pseudocode` / `targets` / `assume` / `command` / `acceptance`)
- [ ] confirm `assume` holds — the pre-state is really there (e.g. `00-env-setup` seeded the data). If it doesn't → **BLOCKED** (see Stop & pause); don't guess the missing pre-state
- [ ] set `status` → `in_progress`

**3. Dispatch** — pick the skill, then run it in the active mode.

- [ ] **skill** = the handler at `execute-tdd/<task.type>/` if it exists (its type-specific format layers on top of the plain flow), otherwise `execute-tdd/default-tdd`

*Mode — one-context (current; always dispatch this way):*

- [ ] one engineer agent, single context, follows the chosen skill on this one task
- [ ] the agent writes the test/code, runs the task's `command`, and **self-verifies the result meets the task's `acceptance` before handing back** (test task: red-as-expected; code task: green)

*Mode — multi-agent (future option, not active — see `roadmap.html` → "Multi-agent engineer dispatch"):*

- [ ] route the task to an engineer agent by `effort` (e.g. a higher-capability model for high-effort tasks)
- [ ] run independent tasks (no shared `depends_on`) in parallel
- [ ] same contract — each agent self-verifies against `acceptance` before handing back

**4. Wait** for the engineer agent to finish.

**5. Accept the result** — re-check the agent's result against the task's **own `acceptance`** (the expected result it declares: red / green / compiles).

- A test task is expected to be **RED** — a correctly-red test (e.g. a compile/import error because the function isn't written yet) is a **PASS**, not a failure. Don't "fix" it here; its paired code task turns it green.
- matches `acceptance` → pass, continue.
- doesn't match → **FAILURE** (see Stop & pause): set `status` → `failed`.
- while accepting, look over the code/test the engineer wrote — not just the run result. If a coding pattern recurs and is **not** already a rule in `code-standards.md`, note the location where the pattern appears in this task; it feeds the candidate in step 7 — self-report adds it to the candidate's accumulating `places` list (deduped) and scores from `places.length`. execute-tdd reports the location, never a score.

**6. Per-task review gate** — only when the user asked to review each task: pause here and report `{ task, actual vs acceptance, files / diff touched }`, wait for approval, then resume. If the user didn't ask → don't stop.

**7. Close-out checklist** — every task:

- [ ] set `status` → `done`
- [ ] record the run result (actual vs `acceptance` — green / red-as-expected / compiles)
- [ ] update the central task / queue so the next pass (step 1) sees the latest status
- [ ] **every** non-blocking issue found this task → `self-report`: a recurring pattern from step 5 that isn't a rule yet goes as a `candidate` (with its `places` list); other issues go as a `problem`

→ back to step 1.

### Skills the engineer agent follows — `default-tdd` + type handlers

`execute-tdd` never writes code; an engineer agent does, following one of these skills. Two kinds:

- **`execute-tdd/default-tdd`** — the always-present default. Given only the task, the agent follows the task's `pseudocode`: a **test task** → write the test exactly as `cases` + `contract` specify, run `command`, confirm red per `acceptance`; a **code task** → implement the `contract` so the paired red test goes green; a **Setup task** (interface / error_code / seed / stub / env-setup) → produce the artifact `contract` / `targets` describe and verify with `command`. No design decisions are left open — the task already carries them.
- **`execute-tdd/<task.type>/`** — an optional, type-specific handler (e.g. `execute-tdd/integration-test/`). When present, it layers extra format/conventions for that type on top of the plain flow. Add one only when a type needs special handling (propose it via `self-report`).

### Stop & pause

Every halt/pause first refreshes the report (`generate-report` → `scenario.html`), then does the row's action. The core rule is *while a runnable task remains, run it* — these rows are the cases where the loop is **done** or **can't proceed**, so it never spins or guesses.

| Outcome | When | Action (after `generate-report`) |
| --- | --- | --- |
| **DRAINED** | no Setup/Backlog task left (step 1) | tell the user Stage 4 is done (Setup + Backlog green) and list the self-learn items recorded this stage (headlines + tier); Stage 5 (`api-test`) is next. No task-by-task dump. |
| **DEADLOCK** | tasks remain but none runnable — every `pending` has an unmet or `failed` `depends_on` (step 1) | ask the user which task is blocked and why; don't guess |
| **BLOCKED** | an `assume` doesn't hold (step 2) | ask the user to supply/repair the missing pre-state; don't guess it |
| **FAILURE** | result ≠ the task's `acceptance` (step 5) | set the task `failed`; ask the user — downstream depends on it, barrelling ahead spreads the break |
| **review gate** | user asked to review per task (step 6) | report `{ task, actual vs acceptance, diff }`; resume on approval (a pause, not a stop) |

Report refresh happens only at these points — **not on every task** (too heavy per iteration).

### `self-report` is improve, not fix

`self-report` carries **non-blocking improvement** observations only — e.g. "this pattern keeps getting hand-written across tasks; promote it to a `code-standard`?" or "this type recurs and needs special handling; add an `execute-tdd/<type>/` handler?". **Blocking** outcomes (DEADLOCK / BLOCKED / FAILURE above) are never silently logged — they halt the loop and ask the user right away.

## References

- bridge: `skills/workflow/SKILL.md` (`## Layout`, `## Stages`) — owns the Setup / Backlog / Api-test folder paths and the stage gating; Stage 5 (`api-test`) follows a DRAINED queue.
- cross-ref: `tech-stack/code-standards.md` — checked while accepting (step 5) to see whether a recurring pattern is already a rule, before reporting it as a `candidate`.

## Trigger Skill

- `execute-tdd/default-tdd` — the engineer skill the agent follows; the always-present default. A project may add a type-specific `execute-tdd/<task.type>/` handler that overrides it for that type (step 3) — that handler is added to `file-map.html` only when it actually exists.
- generate-report — refresh `scenario.html` at every halt/pause (drained / deadlock / blocked / failure / review).
- self-report — non-blocking **improvement** observations (step 7): a recurring code pattern as a `candidate`, other issues as a `problem`. Silent, aggregated; blocking gaps ask the user instead.

## Writes To

- create-task's task files in `01-Setup/` / `02-Backlog/` — advances each task's `status` (`pending` → `in_progress` → `done` / `failed`) as the loop runs; doesn't touch any other field.

## Role & Boundary (Read Before Editing)

This skill owns Stage 4: the **central TDD execution loop** over Setup + Backlog — pick the topmost runnable task, run the pre-flight / dispatch / close-out checklist, dispatch the task + a skill (`execute-tdd/<task.type>/` handler, else `execute-tdd/default-tdd`) to an engineer agent, and accept each task by its own `acceptance` (red / green / compiles). It does NOT author tasks (`create-task`), does NOT implement code itself (the engineer agent does, following the dispatched skill, guided entirely by the task), does NOT run api-tests (`03-Api-test/` is `api-test` — a different loop), does NOT stage test data / seeds / stubs (`create-test-data`), and does NOT define folder paths or stage gating (`workflow`). Task `status` uses create-task's set — `pending` / `in_progress` / `done` / `failed`; a task that fails acceptance is set `failed` and halts the loop. Blocking gaps (deadlock, failure, an `assume` that doesn't hold) stop the loop and ask the user; only non-blocking improvements go to `self-report`. For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
