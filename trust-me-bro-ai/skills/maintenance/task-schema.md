# Task Schema

## How to use

The one schema every task JSON follows, no matter who authors it — `create-task` (scenario work) and `define-task` (issue work) both author to this shape so any task runs the same way. Read it before authoring or editing a task file. Author skills add their own rules on top (task-type list, group folders, ordering); this file defines only what every task shares.

## How to scan

- **Self-sufficiency bar** — the depth every field must reach.
- **Common fields** — present on every task.
- **Conditional fields** — present by task type.
- **Tool-managed fields** — `sync` / `startedAt` / `finishedAt`, written by tooling, not the author.
- **Size `effort`** — how to set `effort`, by task family.

## Format

Every task is one JSON file that meets the **self-sufficiency bar**: a fresh agent, given ONLY this task + the project's standing conventions (`testing-guide` / `code-standards`), finishes it — no asking, no opening another task, no guessing. It may rely on (1) its own `targets` files, (2) project conventions, (3) its own `assume` — **everything else is carried in the task. Carry content, not names** (a function/type/value/location comes with its content, not just its name). **Atomicity: 1 task = 1 unit** — never bundle.

**Common fields (every task):**

- `id` — `<NN>-<slug>-<type>`; `NN` = run order within the task's folder (the slug keeps the full id unique). An always-first task may use a fixed name the author skill defines (e.g. `00-env-setup`, `00-check-test`).
- `type` — from the author skill's type list · `folder` — the group the author skill placed it in
- `status` (`pending` / `in_progress` / `done` / `failed`) · `title` — author tasks as `pending`; execute-tdd advances the rest (`failed` = ran but didn't meet its `acceptance`)
- `purpose` — what this task achieves + why, and the scenario / issue it sits under (scope: handle only in-scope inputs)
- `targets` — `[{ path, mode: create|modify, at }]` — `create` = write new code/test, `modify` = change/refactor existing. For a test task, `at` = its place within the test file's structure — from `testing-guide.md` `## Test Levels`: the owning `### <service>`, then that level's `layout`.
- `depends_on` — task ids (ordering only) · `assume` — the pre-state it may rely on, in plain words
- `command` — exact command to run/verify:
  - verifies **this task's own `targets`** against its `contract` — not behaviour other tasks produce
  - every tool it invokes comes from `assume` or a task in `depends_on`
  - other tasks share the same `targets` path → also pin a literal from this task's `cases`
  - exception: a **gate task** (baseline / dependency install / `regression`) verifies system-wide, and says so in `purpose`
- `acceptance` — done criteria + expected result of `command` (red / green / compiles)
- `effort` (`low` / `med` / `high`, sized below) · `notes`

**Conditional fields (by type):**

- `contract` (interface / code / test / api-test) — full signature/shape **including the shapes of referenced types**, never just their names
- `cases` (test / api-test) — `[{ given, assert: [concrete checks] }]` with real, concrete values — no placeholders
- `pseudocode` (test / code) — the step-by-step plan to write it (a test: setup → action → assert; code: the implementation), precise enough to leave no open design decisions
- `uses` (only when the pipeline stages test data) — `{ testdata: { name: value }, stubs: [...] }` with real values

**Tool-managed fields** *(optional — not authored; written by tooling as the task moves)*:

- `sync` — `sync-task` writes `{ id, ref, url, itemId }` back after the first push: `id` = the tracker handle used to update the item on resync (GitHub = issue number), `ref` = the same item qualified by its repo/project so it stays unique tracker-wide (GitHub = `repo#number`), `url` = human link, `itemId` = the board card's own id. Present → update on resync; absent → create. What each handle is for and when it is written is `sync-task`'s to define.
- `startedAt` / `finishedAt` — ISO 8601 timestamps the runner (`execute-tdd` / `execute-issue`) stamps when the task starts and finishes; `sync-task` maps them onto the board's date fields. Actual duration is derived (`finishedAt` − `startedAt`), not stored.

Author skills (`create-task`, `define-task`) leave all of these absent.

Depth recap: `contract` carries referenced type shapes (no "see source") · `cases` real `given → assert` · `uses.testdata` name→value · `pseudocode` no open decisions · `targets` path+mode+`at` · `assume` plain pre-state · `command`+`acceptance` exact.

**Size `effort`:**

- **Backlog-family tasks** (`unit-test` / `integration-test` / `component-test` / `code-task` and kin) — drivers: LoC, # collaborators to mock, # DB tables touched, novelty.
  - `low` — single function, ≤ ~50 LoC, 0–1 collaborator/mock, follows an existing repo pattern.
  - `medium` — multiple files or coordinated mock setup, < few hundred LoC, cross-module but follows existing patterns.
  - `high` — new pattern, multi-module orchestration, many edge cases, > a few thousand agent tokens.
- **Api-test tasks** (`api-test`) — drivers: sibling pattern availability, # assertions, new mountebank stubs, position in chain.
  - `low` — single request, a sibling scenario to mirror, ≤ ~5 assertions, no new stub.
  - `medium` — 5–15 assertions OR first-in-chain (must bootstrap the chain's shared variables) OR one new stub.
  - `high` — novel scenario (no sibling), long request chain, multiple new downstream stubs, complex body templating.

## Role & Boundary

This file owns the task JSON schema — the self-sufficiency bar, common fields, conditional fields, the tool-managed fields (`sync`, `startedAt`, `finishedAt`), and effort sizing every authored task follows. It does NOT own any author's type list, group folders, or ordering rules (`create-task`, `define-task` — each defines its own on top), how tasks are executed (`execute-tdd` / `execute-issue`), or how the tool-managed fields are written (`sync-task` writes `sync`; the runner stamps the timestamps).
