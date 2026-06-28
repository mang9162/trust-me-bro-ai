---
name: default-tdd
description: The default skill an engineer agent follows when execute-tdd (Stage 4) dispatches it a task and no type-specific handler (`execute-tdd/<task.type>/`) applies. It guides the agent to produce exactly that one task's artifact from the task's own fields + the project's standing conventions, run the task's command, and self-verify the result against the task's acceptance (red / green / compiles) before handing back. It is the playbook, not the engineer — the agent is the engineer; this skill is the procedure it follows for one task.
---

# Default TDD

## Purpose

This is the default **playbook an engineer agent follows** when execute-tdd dispatches it a task and no type-specific handler (`execute-tdd/<task.type>/`) applies. execute-tdd hands the engineer agent two things — the task and this skill — and the agent follows the steps here to turn that one task into its artifact, run the task's `command`, and self-verify against the task's `acceptance` before handing the result back.

The agent is the engineer; this skill is only the procedure it follows for one task. execute-tdd owns the loop (picking, ordering, `status`, the report, user interaction); this skill covers a single task's execution.

Work from **only** the task itself + the project's standing conventions (`testing-guide`, `code-standards`) — create-task's self-sufficiency bar guarantees the task carries everything. Don't open another task file, invent missing pieces, or guess; if the task can't be completed from what it carries, report that back — don't patch over it.

## Procedure

The task arrives already picked and pre-flighted by execute-tdd: its `depends_on` are done, its `assume` holds, its `status` is `in_progress`.

### 1. Read the task

Read every field the task carries — `contract`, `cases`, `pseudocode`, `targets`, `uses`, `command`, `acceptance`. These plus the project conventions are the only inputs. No other task files; no inventing.

### 2. Produce exactly this task's artifact (by `type`)

One task = one artifact. Produce only what this task is — nothing of a neighbouring task.

- **test task** (`unit-test` / `integration-test` / `component-test`) — write the test at `targets`, following `cases` (the `given` / `assert` with their real values) + `contract` + `pseudocode`, at the task's level per `testing-guide` `## Test Levels`. **Do NOT implement the function under test** — that is the paired code task.
- **code task** (`code` / `code-task`) — implement the function at `targets` per `contract` + `pseudocode`, to satisfy the paired red test. **Do NOT rewrite the test.**
- **interface** — write the interface / type at `targets` per `contract`.
- **error_code** — add the registry entry per `contract` (error-codes registry + base-response shape).
- **seed / stub / env-config / env-setup** — turn create-test-data's already-staged artifacts (`Datatest.md`, seeds, stubs) into real, usable test data + a ready environment by running the task's bring-up `command`. Apply what create-test-data staged; don't author new test data.

### 3. Run the command

Run the task's `command` exactly as given. Don't substitute a different command.

### 4. Self-verify against `acceptance`

Compare the result of `command` to the task's declared `acceptance` (`red` / `green` / `compiles`):

- **test task** — confirm it is **red in the expected way** (a compile / import error, or an assertion failing, because the unit isn't implemented yet). This red **is** the acceptance — do NOT write code to turn it green.
- **code task** — confirm the paired test is now **green**.
- **interface / error_code / setup** — confirm it **compiles** / the environment is ready.

Reach the acceptance, or determine it genuinely can't be reached from what the task carries — then stop. Don't fiddle indefinitely, and don't massage a non-matching result into looking like a pass.

### 5. Hand the result back to execute-tdd

Report: what was produced (the `targets` touched), the `command` output, and whether it met `acceptance`.

- Met → report success; execute-tdd's close-out sets `status` → `done`.
- Not met / couldn't complete → report the mismatch honestly (what `acceptance` expected vs what happened); execute-tdd decides FAILURE / BLOCKED and owns the halt + user ask.

Anything worth **improving** (a pattern hand-written across tasks, a missing convention) → surface it with the result so execute-tdd's close-out can aggregate it to `self-report`.

Don't set `status`, refresh the report, pick the next task, or ask the user — all of that is execute-tdd's.

## References

- cross-ref: the dispatched task (from create-task's `01-Setup/` / `02-Backlog/`) — the sole work spec; carries `contract` / `cases` / `pseudocode` / `targets` / `command` / `acceptance`.
- cross-ref: `tech-stack/testing-guide.md` — test conventions + the structure a test task's `targets` path follows.
- cross-ref: `tech-stack/code-standards.md` — code conventions / hard rules a code task follows.
- cross-ref (no file-map edge): `https://martinfowler.com/articles/practical-test-pyramid.html` — the unit / integration / component level a test task honours.

## Role & Boundary (Read Before Editing)

This is the **default skill an engineer agent follows** under execute-tdd — the fallback for executing one already-pre-flighted task when no `execute-tdd/<task.type>/` handler matches. It covers: producing that single task's artifact from the task's own fields + project conventions, running the task's `command`, and self-verifying against the task's `acceptance`. It is a playbook, not the engineer — the agent is the engineer. It does NOT pick or order tasks, set `status`, refresh the report, or talk to the user (all execute-tdd's); does NOT author or edit tasks / contracts / cases (`create-task`); does NOT stage new test data, seeds, or stubs (`create-test-data` — it only applies what was staged, via an env-setup task); for a test task does NOT implement the code under test (the paired code task does), and for a code task does NOT rewrite the test. If a task can't be completed from what it carries, report back rather than guessing. For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
