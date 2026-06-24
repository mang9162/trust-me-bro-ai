---
name: create-task
description: Stage-3 of workflow. From the agreed scenario.html, design the functional call tree and break the scenario into atomic, self-sufficient TDD tasks (one task = one unit), grouped into Setup / Backlog / Api-test and ordered by dependency with each test paired to its code. Each task carries enough that any agent finishes it without opening another task. Authors the functional-design tree into scenario.html; pauses for review.
---

# Create Task

## Purpose
Turn the agreed scenario — as captured in `scenario.html` by the earlier stages — into the functional design and the ordered, atomic task list that execute-tdd and api-test run against. Every task is one unit of work, detailed enough that any agent finishes it from the task alone.

Everything this skill produces derives from `scenario.html` (its steps, E2E flow) and the reviewed `Datatest.md` (the concrete test-data values from create-test-data). Do not invent work the scenario doesn't call for; if the scenario is unclear or missing something needed to author a task, **ask the user — don't guess**.

This skill PLANS only — it does not implement code, run tests, or stage test data (create-test-data).

## Procedure

### 1. Functional Design
From the scenario steps in `scenario.html` + the codebase, build the function call tree and author it into the `scenario.html` Functional Design card.
- Identify every function the requirement impacts; map parent→child relationships (which function calls which).
- Assign each function a **test level** from what it does (use `tech-stack.md` for the project's structure):
  - `unit` — the function does no I/O; only calls pure helpers.
  - `integration` — the function directly hits DB / Redis / a gateway.
  - `component` — the function orchestrates internal services; mock collaborators (NOT unit-level helpers); NO supertest.
  - **Exactly one level per function — never stack:** a function already covered by `unit` or `integration` does NOT also get a `component` test (e.g. a repository function that hits the DB is `integration` only).
- Order the tree bottom-up — leaf nodes are implemented first by execute-tdd.
- Author the tree into the scenario.html Functional Design card using the card format owned by `generate-report` (its `.fn-tree` node anatomy + test-level tags + `activateFn` task wiring). Don't redefine that markup here — generate-report owns it and preserves your card verbatim on later refreshes.
- Present the updated `scenario.html` for the user to review **before** breaking into tasks.

### 2. Break the scenario into atomic tasks
One task = one unit; **never bundle** ("…and also X" means X is a separate task). Everything comes from `scenario.html`; if the source isn't clear, **ask the user — don't guess**. Put each task in a fixed folder (the folder paths themselves are owned by workflow `## Layout` — this skill only decides the group):

- **01-Setup/** — must be ready before Backlog runs. **One task per unit — never bundle several interfaces or codes into one task:**
  - `00-env-setup` — always first (see step 3).
  - `interface` — **one task per interface**: a brand-new interface is a `create` task; adding to / changing an existing one is a `modify` task (`at` = which field/member). If the feature needs several interfaces (some new, some edited), that is several tasks. Shape from the functional design + `code-standards.md`.
  - `error_code` — **one task per error code** (from `error-codes.md` registry + base-response).
  - `seed` / `stub` / `env-config` — from create-test-data's Datatest / stubs.
- **02-Backlog/** — per node in the functional tree: **one test task per test case** (the success case + each alternative / error case — each its own task with its own running `NN`, never bundled, no letter suffixes) at the node's level (`unit` = no I/O; `integration` = hits DB/Redis/gateway; `component` = orchestrates internal services, mock collaborators, no supertest), **plus** the node's `code` task. The `code` task `depends_on` **all** the node's test-case tasks.
  - Alternative / error cases stay as **test tasks in this scenario's backlog** (mocked / pure tests use no real data) — do NOT spin up a new scenario for an error you aren't deliberately scripting as its own flow. A new scenario is a get-requirement concern: only when the E2E flow genuinely differs and needs its own test data.
- **03-Api-test/** — **one task per request** in the scenario's E2E flow. To author each request, read `gateway-directory.md` **Inbound** for its endpoint (method + path) and `gateway-contract.md` for its request/response shape. **Only the LAST api-test task carries the run `command`** (the project's api-test run command — runs the whole chain once); the rest have no `command`. Running each request separately is too slow — run once at the end.

**While doing 03-Api-test, cross-check the E2E flow against `gateway-directory.md` Inbound.** Every request the flow needs must map to a registered inbound line. If a needed endpoint isn't there, it is one of:
- **incomplete functional design** — the flow needs an endpoint nobody designed (e.g. a "select products then save" scenario needs both a *fetch products* and a *save products* line; if only *save* was designed, the *fetch* is missing),
- **unregistered line** — it exists in code but isn't in gateway-directory,
- **another gateway** — it's outbound → it needs a stub, not an api-test.

Don't guess which — **ask the user** and resolve before continuing.

### 3. Always emit `00-env-setup` first
Every scenario's first task. It turns create-test-data's mocks / seeds / stubs into real, usable test data + a ready test environment, so every later task can `assume` the data already exists. Each scenario is **self-contained** — `00-env-setup` creates this scenario's own state; do NOT reuse state from other scenarios (cross-scenario coupling is hard to maintain).

### 4. Order + TDD pairing
- Number tasks `<NN>` top→down **within each folder**; set `depends_on` (ids) where related. **Every task `depends_on` `00-env-setup`** (env ready first).
- **Pair each node's test case(s) with its code task** — write the node's test-case tasks (each its own `NN`), then its `code` task (which `depends_on` all of them). Never batch all tests across nodes then all code — a missing function is a compile error and the tests can't run.
- **api-test chain:** each api-test task also `depends_on` the previous api-test request in the chain → authoring order = run order (only the last carries the run command, per step 2).
- A compile error because the function isn't written yet IS the expected red; the test task does not stub or fix it — the paired code task does.

### 5. Write each task to the format
Every task is a JSON file that meets the **self-sufficiency bar**: a fresh small agent, given ONLY this task + the project's standing conventions (`testing-guide` / `code-standards`), finishes it — no asking, no opening another task, no guessing. It may rely on (1) its own `targets` files, (2) project conventions, (3) its own `assume` — **everything else is carried in the task. Carry content, not names** (a function/type/value/location comes with its content, not just its name).

**Common fields (every task):**
- `id` — `<NN>-<slug>-<type>`; `NN` runs per folder (the slug keeps the full id unique)
- `type` · `folder` · `status` (`pending` / `in_progress` / `done` / `failed`) · `title` — author tasks as `pending`; execute-tdd advances the rest (`failed` = the task ran but didn't meet its `acceptance`)
- `purpose` — what this task achieves + why, and the scenario it sits under (scope: handle only in-scenario inputs)
- `targets` — `[{ path, mode: create|modify, at }]` — `create` = write new code/test, `modify` = change/refactor existing. For a test task, `at` = its place in the project's test structure (the test path), per `testing-guide`.
- `depends_on` — task ids (ordering only) · `assume` — the pre-state it may rely on, in plain words
- `command` — exact command to run/verify · `acceptance` — done criteria + expected result of `command` (red / green / compiles)
- `effort` (`low`/`med`/`high`, sized below) · `notes`

**Conditional fields (by type):**
- `contract` (interface / code / test / api-test) — full signature/shape **including the shapes of referenced types**, never just their names
- `cases` (test / api-test) — `[{ given, assert: [concrete checks] }]` with real values from `Datatest.md`
- `pseudocode` (test / code) — the step-by-step plan to write it (a test: setup → action → assert; code: the implementation), precise enough to write with no open design decisions
- `uses` (when needed) — `{ testdata: { name: value }, stubs: [...] }` with real values taken from `Datatest.md`

Depth: `contract` carries referenced type shapes (no "see source") · `cases` real `given → assert` · `uses.testdata` name→value · `pseudocode` no open decisions · `targets` path+mode+`at` · `assume` plain pre-state · `command`+`acceptance` exact. **Atomicity:** 1 task = 1 unit.

**Size `effort`:**
- **Backlog tasks** (`unit-test` / `integration-test` / `component-test` / `code-task`) — drivers: LoC, # collaborators to mock, # DB tables touched, novelty.
  - `low` — single function, ≤ ~50 LoC, 0–1 collaborator/mock, follows an existing repo pattern.
  - `medium` — multiple files or coordinated mock setup, < few hundred LoC, cross-module but follows existing patterns.
  - `high` — new pattern, multi-module orchestration, many edge cases, > a few thousand agent tokens.
- **Api-test tasks** (`api-test`) — drivers: sibling pattern availability, # assertions, new mountebank stubs, position in chain.
  - `low` — single request, a sibling scenario to mirror, ≤ ~5 assertions, no new stub.
  - `medium` — 5–15 assertions OR first-in-chain (must bootstrap the chain's shared variables) OR one new stub.
  - `high` — novel scenario (no sibling), long request chain, multiple new downstream stubs, complex body templating.

### 6. Name + place files
Each task file is `<id>.json` (= `<NN>-<slug>-<type>.json`), placed in its group folder. The folder paths are owned by workflow `## Layout`.

### 7. Self-learn
Anything missing to author a task (no contract, a missing/unregistered endpoint, a missing error_code, a conflict) → aggregate to `self-report` (silent).

### 8. Update report
Trigger `generate-report` to refresh `scenario.html`.

### 9. ⏸ PAUSE
Tell the user the updated `scenario.html` is ready (tasks + functional design rendered by generate-report in step 8) and to review it there — don't print a task summary. Do not start execute-tdd until approved.

## References
- bridge: `context/gateway-directory.md` — **Inbound** lines: each E2E request's endpoint (method + path); cross-check the flow against it to catch a missing / unregistered / outbound endpoint.
- bridge: `tech-stack/gateway-contract.md` — request/response shapes an api-test `contract` must match.
- bridge: `tech-stack/database-schema.md` — entity/column shapes for `seed` / `interface` Setup tasks.
- bridge: `context/error-codes.md` — the error_code registry + base-response shape for `error_code` Setup tasks.
- cross-ref: `tech-stack/tech-stack.md` — project structure (drives the functional design + where code / test files live).
- cross-ref: `tech-stack/testing-guide.md` — test conventions + the test structure a test task's `at` path follows.
- cross-ref: `tech-stack/code-standards.md` — code conventions / hard rules embedded into code tasks.
- cross-ref: `https://martinfowler.com/articles/practical-test-pyramid.html` — the test-level (test pyramid) classification (unit / integration / component).
- cross-ref: `skills/generate-report/SKILL.md` — owns the scenario.html Functional Design card format (`.fn-tree` anatomy) this skill authors.
- bridge: `skills/workflow/SKILL.md` (`## Layout`) — owns the Setup / Backlog / Api-test folder paths + task-file placement; this skill groups tasks and defers the paths there.

## Trigger Skill
- generate-report — refresh `scenario.html` after the task list is staged (step 8).
- self-report — when something needed to author a task isn't available (missing contract / endpoint / error_code, or a conflict); silent, aggregated in step 7.

## Role & Boundary (Read Before Editing)
This skill owns Stage 3: the **functional design** (function call tree, authored into `scenario.html`) and breaking the agreed scenario into **atomic, self-sufficient tasks** — grouped into Setup / Backlog / Api-test, ordered with dependencies and TDD test→code pairing, each carrying enough to be done standalone. Everything derives from `scenario.html`; gaps go to `self-report`. It authors api-test tasks (the endpoints are known from gateway-directory) but does NOT run them (that is `api-test`), does NOT execute Setup/Backlog tasks (`execute-tdd`), does NOT stage test data / seeds / stubs (`create-test-data` — it references their shapes), and does NOT define the scenario.html card markup (`generate-report`). For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
