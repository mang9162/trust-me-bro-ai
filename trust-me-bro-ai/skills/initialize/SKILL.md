---
name: initialize
description: First-run bootstrap and re-sync. Scan the repo (light or full), migrate any existing docs, and create/update the context/tech-stack knowledge files from the format templates under initialize/ — using a target's own format when it already exists.
---

# Initialize

## When to invoke
- First time the kit is dropped into a repo (create the `context/`/`tech-stack/` knowledge files), or to re-sync them after the repo has changed.

## Phase 1 — Scan  (ask the user: light or full?)
For each format template under `initialize/context/` and `initialize/tech-stack/` (each `*-format.md` declares a `Target:` path + its format), scan the repo for the data that target needs, then fill it per the chosen mode:
- light — seed a skeleton (names + structure only); leave the rest to self-learn during real workflow runs.
- full — scan thoroughly and fill in every detail as completely and accurately as possible now (heavier on tokens/context); do NOT defer to self-learn.

Stay language/framework-agnostic: read whatever the repo exposes (project metadata, source layout, route/handler/schema/infra definitions, build/test config, …). The specific "where to look" for each target lives in its own `*-format.md`, not hardcoded here — so initialize works on any stack.

Don't invent: if the repo doesn't show a value, leave it blank rather than guess.

When the scan is done, report what was found to the user directly (in the conversation — NOT via self-report); surface only the parts the scan couldn't resolve for Phase 4 to confirm.

## Phase 2 — Detect existing docs & migrate
Find knowledge the repo already has (in other docs, or in the wrong shape) and migrate it into the targets — instead of starting blank or duplicating. Runs before Phase 3 fills the gaps.
1. Enumerate — list existing docs that could hold target knowledge (README, docs folders, AGENTS.md / CLAUDE.md, any prior context notes). Skip the kit's own skill files.
2. Match — map each to a target: direct (1:1) · merge (several → one) · split (one → several) · orphan (no match).
3. Cross-check — for matched files: does the content fit the target's format? do its cross-file links (`bridge` ids / refs) still resolve? any duplication/conflict between sources?
4. Flag list — collect every finding as "what was found + suggestion". Don't auto-apply.
5. ⏸ Review — show the whole flag list to the user once (not one prompt per item); the user decides each.
6. Apply — migrate (write / move / merge / split / delete) per the mapping + the user's decisions, in one pass, writing into each target following its format.
7. Leftover — anything the user didn't decide → hand to self-learn (don't block initialize).

## Phase 3 — Bootstrap (write the targets)
For each format template:
- Target does not exist → create it by copying the whole template into the target — everything **except** the `Target:` line and the `## How to scan (when filling this file)` section (those are initialize-only) — then fill the tables from the Phase 1 scan. The target now carries its own format, so later edits / self-learn follow it without re-reading initialize.
- Target already exists → don't overwrite; extend/update it from the scan, following the format inside the target file itself (not the template — the project may have customized it).
- Don't guess — leave unclear values blank (light); a full scan should already have filled the detail.
- Subject not present in the repo → still create the target (so cross-file bridges keep resolving), but write a clear "not used by this project" marker inside rather than skipping or leaving it empty (e.g. no DB driver → database-schema.md states the project has no database).

Then report what was created/updated (paths).

## Phase 4 — Domain Q&A + Setup Concerns
After Phases 1–3, fill the gaps a scan can't answer. Ask this fixed set (skip any that don't apply), then close with an open question. Each answer is written into its target, following that target's format.

1. Domain — confirm the domain guessed in Phase 1; anything to fix/add?
2. Scenario naming — what naming pattern do this project's scenarios follow? (default `<FEATURE>_<TYPE>_<N>`)
3. Per-line purpose — only for lines the scan left blank (a full scan fills most, so few or none): what it's for / when it's called → gateway directory + its paired contract row.
4. Hard rules — specific actions the AI is forbidden to do in this project (e.g. don't auto-format/lint, don't touch env files, don't edit DB migrations) → code-standards target. (Code style/conventions are separate — inferred from the codebase, not asked here.)
5. Test placement — confirm the test-file (unit / component / integration / api-test) location + naming the scan found; if the scan found none, ask — and suggest a convention that fits the project.
6. Error-code format — only if Phase 3 flagged an error registry is needed and none exists: propose a format and ask which abbreviations to use. (Skip if the project has no API surface.)
7. Local test infra — is local integration/api-test infra already present? If not, PROPOSE scaffolding the kit's default (propose only — don't auto-do).
8. Open-ended — "anything else the AI should know before real work starts?"

### Setup Concerns
Collect everything still needing setup but not done (from Phase 3 + items 6/7). Name each `INITIALIZE_<NameOfWork>` (e.g. `INITIALIZE_BASE_RESPONSE_ERROR_CODE`, `INITIALIZE_API_TEST_SETUP`) and report it to the self-report skill, recording its fix as: start a workflow for it, the way the project recommends. Then advise the user: open `self-learn/feed-back.html`, pick the solution they want, click copy, and paste it back here to start it.

## References
- cross-ref: `initialize/context/*-format.md`, `initialize/tech-stack/*-format.md` — templates read on first create; each gives a `Target:` path + format.

## Trigger Skill
- self-report — record each `INITIALIZE_<NameOfWork>` setup concern (with its fix) so the user can action it via `self-learn/feed-back.html`.

## Writes To
- each template's `Target:` file (e.g. `context/gateway-directory.md`, `tech-stack/database-schema.md`) — created on first run, or updated/extended when it already exists.

## Role & Boundary (Read Before Editing)
initialize bootstraps and re-syncs the `context/`/`tech-stack/` files from the `*-format.md` templates by scanning the repo (light or full) and migrating existing docs. On create it follows the template's format; on update it follows the target file's own (inherited) format. It does NOT own the formats (each `*-format.md` / target file does) and does NOT fill fine detail in light mode — that's self-learn during workflow runs. It also does not continuously keep the files up to date during workflow runs — that ongoing job belongs to self-learn; initialize runs only on explicit first-run / re-sync, so redirect such requests there. For where any other change belongs, see the Responsibility map in workflow/SKILL.md.
