---
name: execute-tdd
description: Stage-4 of workflow. The central TDD execution loop. Drains the Setup + Backlog tasks authored by create-task in dependency order; for each task it runs a pre-flight / dispatch / close-out checklist, hands the task to an engineer (one-context for now) using the handler skill that matches the task's type if one exists, otherwise the default TDD procedure, then accepts the result against the task's own acceptance (red / green / compiles). Does not implement code itself. Halts and asks the user on deadlock or failure; pauses when the queue is drained and hands off to Stage 5.
---

# Execute TDD

## Purpose
Stage 4. Take the atomic tasks create-task authored into `01-Setup/` + `02-Backlog/` and actually run them through the TDD red→green loop, one task at a time in dependency order.

This skill is the **central loop / dispatcher** — it does NOT implement code itself. It reads each task, hands it to an engineer to execute, and verifies the result against the task's own `acceptance`. The engineer writes the test/code from the task; the task carries everything needed (create-task's self-sufficiency bar).

Scope is **Setup + Backlog only**. The api-test suite (`03-Api-test/`) is Stage 5 — a different loop (`api-test`).

## Procedure

### Scope
Drains **01-Setup + 02-Backlog** only. **03-Api-test = Stage 5** (`api-test`) — not this loop.

### The loop
Build the queue from the Setup + Backlog tasks, then repeat:

**1. Pick the next task** — a `pending` task whose `depends_on` are all `done`, in folder order (Setup before Backlog) then `NN`.
- No `pending` left → **DRAINED** → exit the loop → PAUSE → hand off to Stage 5.
- `pending` remain but none is runnable (a `depends_on` is unmet, or a dependency is `failed`) → **DEADLOCK** → stop + **ask the user** (can't proceed, don't guess).

**2. Pre-flight checklist** — every task, regardless of type:
- [ ] `depends_on` are all `done`
- [ ] read the task in full (`contract` / `cases` / `pseudocode` / `targets` / `assume` / `command` / `acceptance`)
- [ ] confirm `assume` holds — the pre-state is really there (e.g. `00-env-setup` seeded the data). **If it doesn't hold → stop + ask the user** (blocking; don't guess the missing pre-state)
- [ ] set `status` → `in_progress`

**3. Dispatch checklist** — who runs it, with which skill:
- [ ] engineer = **one-context** (always, for now — effort-based routing/parallel is deferred; see `roadmap.html` → "Multi-agent engineer dispatch")
- [ ] is there a handler skill that matches `task.type`? (convention: a `SKILL.md` at `execute-tdd/<task.type>/`)
  - **yes** → the engineer uses it (its type-specific format/conventions layer on top of the default TDD flow)
  - **no** → **fallback** = the default TDD procedure below — the engineer writes the test/code straight from the task
- [ ] hand the task (+ the chosen handler skill, if any) to the engineer

**4. Wait** for the engineer to finish.

**5. Accept the result** — compare the actual result against the task's **own `acceptance`** (the expected result it declares: red / green / compiles).
- A test task is expected to be **RED** — a correctly-red test (e.g. a compile/import error because the function isn't written yet) is a **PASS**, not a failure. Do not "fix" it here; its paired code task turns it green.
- matches `acceptance` → pass, continue.
- does not match → **FAILURE** → set `status` → `failed`, stop + **ask the user** (downstream tasks depend on it; barrelling ahead just spreads the break).

**6. Per-task review gate** — only when the user asked to review each task: stop here and report `{ task, actual vs acceptance, files / diff touched }`, wait for approval, then resume. If the user did not ask → don't stop.

**7. Close-out checklist** — every task:
- [ ] set `status` → `done`
- [ ] record the run result (actual vs `acceptance` — green / red-as-expected / compiles)
- [ ] update the central task / queue so the next pass (step 1) sees the latest status
- [ ] anything worth **improving** (not blocking) → aggregate to `self-report`

→ back to step 1.

### Default TDD procedure (fallback, when no handler skill matches the type)
The engineer, given only the task, follows the task's `pseudocode`: for a test task, write the test exactly as the `cases` + `contract` specify and confirm it is red per `acceptance`; for a code task, implement the `contract` so the paired red test goes green; for a Setup task (interface / error_code / seed / stub / env-setup), produce the artifact the `contract` / `targets` describe and verify with `command`. No design decisions are left open — the task already carries them.

### Stop conditions
| Condition | When | Action |
|---|---|---|
| **DRAINED** | no Setup/Backlog task left | exit loop → PAUSE → hand to Stage 5 |
| **DEADLOCK** | tasks remain but none runnable (a `depends_on` unmet / a dependency `failed`) | stop + ask the user which task is blocked and why |
| **FAILURE** | step 5: result ≠ the task's `acceptance` | mark `failed`, stop + ask the user |
| **pre-flight fails** | step 2: an `assume` doesn't hold | stop + ask the user |
| per-task review | user asked (step 6) | pause + report, resume on approval (not a terminate) |

The core is "while a runnable task remains, run it." The extra rows are the cases where the loop **can't proceed but isn't done** — those halt with a question, never spin or guess.

### `self-report` is improve, not fix
`self-report` carries **non-blocking improvement** observations only — e.g. "this pattern keeps getting written by hand across tasks; make it a `code-standard`?" or "this type recurs and needs special handling; propose adding an `execute-tdd/<type>/` handler skill". **Blocking** conditions (deadlock, failure, an `assume` that doesn't hold) are NOT silently logged — they **stop the loop and ask the user** right away.

### PAUSE
- On **DRAINED**: trigger `generate-report` to refresh `scenario.html`, tell the user Stage 4 is done (Setup + Backlog green) and Stage 5 (`api-test`) is next. Don't print a task-by-task dump.
- On **DEADLOCK / FAILURE**: trigger `generate-report`, then ask the user to resolve the blocked/failed task before continuing.
- Report refresh happens at these pause points — **not on every task** (too heavy per iteration).

## Examples
Illustration of the standard depth — generic `products/stock` domain, not real data.

**Dispatch decision (step 3)**
```
task 03-findItemsByRestaurant-integration-test  (type: integration-test)
→ look for execute-tdd/integration-test/SKILL.md
   • exists?  → engineer runs with that handler (extra integration-test format on top of TDD)
   • missing? → fallback: default TDD procedure (engineer writes the test from the task's cases + contract)
```

**One node through the loop (a paired test → code, no handler skill present → fallback)**
```
1 pick  01-splitByStockDelta-unit-test  (deps [00-env-setup] done) ✓
2 pre-flight  read task ✓ · assume "env ready, fn not implemented" holds ✓ · status → in_progress
3 dispatch  one-context · no execute-tdd/unit-test/ handler → fallback TDD
4 wait      engineer writes the unit test from `cases`, runs `npm run test:unit`
5 accept    acceptance = RED (import error, fn missing) · actual = RED  → PASS (do NOT fix)
6 review    user didn't ask per-task → no stop
7 close     status → done · record "red-as-expected" · update queue

1 pick  02-splitByStockDelta-code  (deps [01-...unit-test] done) ✓
... 5 accept  acceptance = GREEN · actual = GREEN → PASS
7 close  status → done → back to step 1
```

**Stop — failure (step 5)**
```
5 accept  acceptance = GREEN · actual = test still RED after code task
→ FAILURE: status → failed · stop · ask the user (do not run the dependents)
```

## References
- bridge: create-task's `01-Setup/` + `02-Backlog/` task files — the queue this loop drains (each task carries its own `contract` / `cases` / `pseudocode` / `acceptance`).
- cross-ref: `tech-stack/testing-guide.md` — test conventions the engineer follows when running each task.
- cross-ref: `tech-stack/code-standards.md` — code conventions the engineer follows; also the home for `self-report` improvement suggestions (e.g. a recurring pattern promoted to a standard).
- cross-ref: `roadmap.html` (repo root) — "Multi-agent engineer dispatch": effort-based routing / parallel execution is deferred; one-context for now (step 3).
- bridge: `skills/workflow/SKILL.md` (`## Layout`, `## Stages`) — owns the Setup / Backlog / Api-test folder paths and the stage gating; Stage 5 (`api-test`) follows a DRAINED queue.
- cross-ref: `skills/generate-report/SKILL.md` — refreshes `scenario.html` at the pause points.

## Trigger Skill
- `execute-tdd/<task.type>` handler — the type-matching handler skill, when one exists (step 3); otherwise the default TDD fallback runs.
- generate-report — refresh `scenario.html` at each PAUSE (drained / deadlock / failure / per-task review).
- self-report — non-blocking **improvement** observations only (step 7); silent, aggregated. Blocking gaps ask the user instead.

## Role & Boundary (Read Before Editing)
This skill owns Stage 4: the **central TDD execution loop** over Setup + Backlog — pick the next task by dependency, run the pre-flight / dispatch / close-out checklist, dispatch to an engineer (one-context for now) via the `execute-tdd/<task.type>/` handler skill or the default TDD fallback, and accept each task by its own `acceptance` (red / green / compiles). It does NOT author tasks (`create-task`), does NOT implement code itself (the engineer does, guided entirely by the task), does NOT run api-tests (Stage 5 / `api-test`), does NOT stage test data / seeds / stubs (`create-test-data`), and does NOT define folder paths or stage gating (`workflow`). Blocking gaps (deadlock, failure, an `assume` that doesn't hold) stop the loop and ask the user; only non-blocking improvements go to `self-report`. For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
