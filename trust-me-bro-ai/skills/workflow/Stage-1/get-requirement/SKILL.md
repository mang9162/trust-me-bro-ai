---
name: get-requirement
description: Stage-1 of workflow. Read the requirement, resolve ambiguities with the user, identify scenarios, and define scenario.html content for each with user-story steps (generate-report writes the file). Pause for user review before any test data or tasks are created.
---

# Get Requirement

## Purpose
Establish a shared, unambiguous understanding of what each scenario does — in user/system terms — before any stubs, seeds, or tasks are created. Mistakes here cascade through every downstream stage.

## Procedure

1. **Read the requirement** (user message / or file). Extract:
   - The feature name and affected endpoint(s).
   - Each scenario (Success / Alternative), its trigger, and expected outcome.
   - Any new functions, error codes, or interface changes mentioned.

2. **Identify gaps** — if any of the following are unclear, ask the user before proceeding:
   - Which scenarios to implement (scope).
   - The end-to-end flow: what does the user/system do **before** the feature under test (setup state), **during** (the action), and **after** (verification + cleanup)?
   - Edge cases: what exact condition triggers each Alternative path?
   - Data constraints: what boundary values make validation pass vs. fail? (e.g. minimum quantities, stock limits, threshold diffs)

3. **Define `scenario.html` content** for each scenario (`generate-report` places the file per `workflow/SKILL.md`'s `## Layout` — see `## References`).

   The content for each scenario:

   a. **`scenario-meta`** — machine-readable metadata block:
   ```json
   {
     "scenario": "<SCENARIO_NAME>",
     "category": "Success | Alternative",
     "description": "<one-line human summary>",
     "steps": [
       "<Actor> <does something> — <what state/data is set up or verified>",
       "..."
     ],
     "accepted": false,
     "acceptanceHistory": []
   }
   ```
   `accepted` / `acceptanceHistory` are written back later by `acceptance-review` (Stage 6) — create them here with these defaults. `syncTarget` (which sync board this scenario uses) is written at step 7 when a `sync-task-*` skill exists.

   b. **Header card** — scenario name, category badge, description.

   c. **Progress indicator** — 6-stage track (Stage 1 = done, rest = todo).

   d. **E2E Flow** — one `.flow-box` per step from the `steps` array.

   e. **Test Data** — placeholder section ("not yet created").

   f. **Tasks** — placeholder section ("not yet created").

   > Functional Design is NOT defined at Stage 1. It is added by `create-task` at Stage 3 once the function tree can be fully designed.

   **`steps` rules:**
   - Each step = one meaningful user/system action (not an API call path).
   - Write in plain language: "User creates a live stream with product M001 (branchStock=10)" not "POST /facebook/save-live-config".
   - Cover setup, the feature action, verification, and cleanup.
   - Alternative scenarios: clearly state what condition triggers the failure and what the system returns.

4. **Self-learn** — if anything noticed while gathering this requirement is self-learn-worthy (an ambiguity that needed asking, a recurring domain pattern, a name that doesn't match convention), trigger `self-report` (see `## Trigger Skill`). Do not ask the user whether to act on it now.

5. **Update Report** — trigger `generate-report` to write/update `scenario.html` for each scenario (header-card + progress-indicator(1/6) + E2E-flow + placeholder test-data/tasks, per the `scenario-meta` from step 3).

6. ⏸ **PAUSE** — present each `scenario.html` path and ask the user to review, and list the self-learn items recorded this round (headlines + tier). Do NOT move to Stage 2 until approved.

7. **Sync to the external tracker** — on approval, find the `sync-task-*` skills in `skills/sync-task/`. None → skip. Otherwise select the one for this scenario, record it in `scenario-meta` as `"syncTarget": "<name>"` (later stages read it), and open it for a **parent-only** sync (`--parent`) — the scenario's parent issue on that board (no tasks yet).

## Example steps (correct style)

```json
"steps": [
  "User creates a live stream with product M001 (branchStock=10)",
  "Customer reserves all 10 units of M001",
  "User edits products: increases M001 branchStock from 10 to 12 (+2)",
  "Customer reserves 2 more units of M001 — verifies the +2 increase is available",
  "System confirms reserve record exists and liveCrawler shows branchStock=12",
  "User ends the live stream"
]
```

## What NOT to put in `steps`

`steps` describe **what** happens, in user/system terms -> never **how** it is implemented.
A step is at the wrong level if it names any of:
- a specific API path or HTTP method
- a test-tool variable, binding, or assertion
- a mock/stub identifier for a downstream service
- an implementation detail (class, function, file, library)

If you find yourself naming one of these, it belongs in Stage 3 (create-task) or Stage 5 (api-test) - not here.

## References
- cross-ref: `trust-me-bro-ai/context/domain-reference.md` — scenario naming conventions + Core Terms (domain vocabulary for writing steps).
- bridge: `trust-me-bro-ai/context/error-codes.md` — error codes mentioned in the requirement must match an existing entry exactly (catch duplicate names/spelling drift from the start).
- bridge: `trust-me-bro-ai/skills/workflow/SKILL.md` (`## Layout`) — the scenario folder path `<NN>-<FULL_SCENARIO_NAME>` used in step 3 must match this format exactly.

## Trigger Skill
- generate-report — write/update `scenario.html` (header-card + progress-indicator(1/6) + E2E-flow + placeholder test-data/tasks), per step 5.
- self-report — when something self-learn-worthy is noticed while gathering the requirement, per step 4.
- sync-task — a parent-only sync of the scenario to the selected board (step 7), when a `sync-task-*` skill exists.

## Role & Boundary (Read Before Editing)

This skill's responsibility is limited to one thing per scenario: turn the raw
requirement into a clear, agreed E2E narrative (`steps`) plus the scenario's
name/description — including surfacing ambiguities back to the user when the
requirement is unclear.

It does not extend into test-data design (create-test-data), functional/task
design (create-task), TDD implementation (execute-tdd), verification
(api-test), or the external-sync mechanics (`sync-task` — step 7 only selects the
target and triggers a parent-only sync) — for anything outside this boundary, see the Responsibility map in
workflow/SKILL.md.

The `steps` produced here are the single source later stages trace from —
they are never reshaped to fit downstream (api-test) feasibility.
