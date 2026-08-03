---
name: create-test-data
description: Stage-2 of workflow. Read the central dictionary + gateway/seeding references, then stage this scenario's test data: Datatest.md (values, with expect + status columns), DB seeds, and stubs. Missing-or-unsure values are asked back; anything not catalogued is reported to self-report (silent) and flagged in Datatest's status. Pause for user review.
---

# Create Test Data

## Purpose
Turn an agreed scenario (its `scenario.html` steps) into the concrete test data the downstream stages run against: the values this scenario uses, the DB rows it needs seeded, and the stubs for the downstream calls it makes. Every value lives in one place — `Datatest.md` — which stubs and seeds embed and the report renders.

This skill only STAGES data inside the scenario folder. It reads the shared reference files but never edits them, never writes assertions, and never moves stubs into the live mock environment.

## Two layers of test data
1. **Central dictionary (names, no values)** — `trust-me-bro-ai/context/data.md`. Catalogues every kind of test-data variable, grouped by context. Read it FIRST so you reuse catalogued names.
2. **Per-scenario Datatest (names + values)** — `Datatest.md`. Picks entries from the dictionary and assigns concrete values for THIS scenario. The single source stubs/seeds embed and the report renders.

## Procedure

1. **Read the references first** (do not draft values before this):
   - `context/data.md` — which catalogued variables this scenario uses.
   - `context/gateway-directory.md` — the downstream gateways this scenario's flow calls (purpose / condition).
   - `tech-stack/gateway-contract.md` — how to shape each stub (predicate key params / response path).
   - `tech-stack/database-schema.md` — the valid tables/columns to seed + each datastore's `seeding` line (how to seed it).
   Also read the scenario's own `scenario.html` steps — they are the source of the `value` / `expect` data.

2. **Write `Datatest.md`** — one `## Section` per context group, each a table with columns `| name | value | expect | status | notes |`:
   - `value` — the input value set up for this scenario (*given*).
   - `expect` — the value verified after the action (*then*). Fill only for variables the scenario checks whose value is known; leave blank for pure inputs or dynamic outputs (e.g. a token). Record the value only — assertions are Stage 5.
   - `status` — `new → self-report` (name not in `data.md`) or `conflict → self-report` (name is in `data.md` but its definition is wrong / contradicts this scenario); blank when the entry already exists and matches.
   - `notes` — any real caveat (e.g. a value reused from another scenario).
   Use values unique to this scenario wherever reuse would collide (fresh `videoId` / `postId` / `pageId`) so stub predicates don't clash with sibling scenarios.
   **If a value is missing, or you are unsure which catalogued entry to use — ask the user. Never invent a name or guess a value.**

3. **Write the DB seeds** — only when an integration path actually looks the entity up. Valid columns/types + the datastore's `seeding` (mechanism/caveat): `database-schema.md`; location: per the workflow `## Layout`. Stage JSON inside the scenario folder only.
   **If the entity or its shape isn't covered there, or you're unsure — ask the user. Don't guess.**

4. **Write the stubs** — one per downstream call, embedding values from `Datatest.md`. Shape each per `gateway-contract.md`; choose which calls from `gateway-directory.md` + the scenario flow; path & filename per the workflow `## Layout`.
   **If a downstream call isn't catalogued, or you're unsure how to match it — ask the user. Don't guess.**

5. **Self-learn** — aggregate every gap found above into a single `self-report` trigger:
   - a `new` variable (not in `data.md`),
   - a `conflict` with `data.md` (its definition is wrong / contradicts this scenario),
   - a missing gateway or entity.
   Silent — do not ask the user whether to report; it is resolved on a separate flow.

6. **Update report** — trigger `generate-report` to refresh `scenario.html`.

7. **⏸ PAUSE** — before presenting, verify your own outputs are internally consistent:
   - every downstream call you know about has a stub,
   - stub predicates use the scenario-unique values from step 2,
   - every value embedded in a stub or seed exists in `Datatest.md`,
   - every row flagged in `status` was actually sent to `self-report`.
   Then present the updated `scenario.html` for review, and list the self-learn items recorded this round (headlines + tier). Do NOT move to Stage 3 until approved.

8. **Sync** — on approval, read `scenario-meta.syncTarget`. Unset → skip. Set → open `sync-task-<syncTarget>` and do a **parent-only** sync (`--parent`); the new test data now shows in the scenario's parent issue.

## References
- cross-ref: `trust-me-bro-ai/context/data.md` — central dictionary; pick catalogued variable names from here (read-only — never write back).
- cross-ref: `trust-me-bro-ai/context/gateway-directory.md` — which downstream gateways the flow calls (purpose / condition).
- cross-ref: `trust-me-bro-ai/tech-stack/gateway-contract.md` — stub predicate key params + response path shape.
- cross-ref: `trust-me-bro-ai/tech-stack/database-schema.md` — valid columns/types for seed rows + each datastore's `seeding` (how to seed).
- bridge: `trust-me-bro-ai/skills/workflow/SKILL.md` (`## Layout`) — owns every `01-Testdata/` path and the stub `<SCENARIO>-<purpose>.json` naming; this skill names files only and defers the paths there.

## Trigger Skill
- self-report — when something needed isn't catalogued or contradicts the dictionary (new variable / conflict / missing gateway or entity); silent, aggregated once in step 5.
- generate-report — refresh `scenario.html` after staging, per step 6.
- sync-task — a parent-only sync to `scenario-meta.syncTarget`'s board (step 8), when set.

## Writes To
- `01-Testdata/` — `Datatest.md`, DB seeds (`db/`), and stubs (`stubs/`) for this scenario.

## Role & Boundary (Read Before Editing)

This skill's responsibility is limited to STAGING this scenario's test data — the concrete values (`Datatest.md`), the DB seeds, and the stubs for the downstream calls the scenario makes (paths owned by the workflow `## Layout`).

It reads the shared reference files (`data.md`, `gateway-directory.md`, `gateway-contract.md`, `database-schema.md`) but never edits them — gaps go to `self-report`. It does not write assertions (api-test), does not move stubs into the live mock environment (execute-tdd / env-setup task), and does not design tasks (create-task), nor own the external-sync mechanics (`sync-task` — step 8 only triggers a parent-only sync to the recorded target). For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
