---
name: index
description: Master index of all shared team skills. Use when starting any task — read this first to find the right skill, then follow its path to load the full instructions.
---

# Shared Skills Index

<!-- AUTO-GENERATED — do not edit manually, run $skill-sync instead -->

- **create-pr**: Generate a GitHub PR title and description following the project template (Problems / Solutions / Changes). Outputs copy-paste text only — does not run gh pr create.
  path: `docs/ai/shared/create-pr/SKILL.md`
- **skill-sync**: Sync shared skills index to .agents/skills/index and ~/.claude/skills/index. Use this whenever a new skill is added to or removed from docs/ai/shared/.
  path: `docs/ai/shared/skill-sync/SKILL.md`
- **workflow**: Orchestrate a feature from a requirement through TDD tests, implementation, and end-to-end API verification. Four stages with explicit review pauses — (1) create test data + stubs, (2) define tasks (env-setup, Backlog code/test tasks with required effort, Api-test tasks one-per-request), (3) execute Setup + Backlog (TDD), (4) author api-test bru files task-by-task then run Bruno once. On Stage-4 failure, create a fix task and loop back through Stage 3.
  path: `docs/ai/shared/workflow/SKILL.md`
- **create-test-data**: Stage-1 of workflow. Pick the data this scenario needs from the central data dictionary, write a per-case Datatest.md spelling the concrete values, then generate DB fixtures (postgres/mongo) and mountebank stubs in 01-Testdata/ using those values. Pause for user review before stubs move to test-env/mountebank/.
  path: `docs/ai/shared/workflow/Step-1/create-test-data/SKILL.md`
- **create-task**: Stage-2 of workflow. After test data is reviewed, write env-setup task into 01-Setup, one Backlog task per impacted function into 02-Backlog, and one Api-test task per Bruno request into 03-Api-test. All tasks require effort (different criteria per stage); api-test tasks additionally require context + asserts. Pause for user review before execution.
  path: `docs/ai/shared/workflow/Step-2/create-task/SKILL.md`
- **api-test**: Stage-4 executor for api-test tasks (one per Bruno request). OPT-IN ONLY. Authors the single bru file at task.target task-by-task using values from Datatest.md and scenario-scoped runtime vars. The LAST api-test task runs `npm run test:brunolocal` once and verifies every task's asserts.
  path: `docs/ai/shared/workflow/Step-3/api-test/SKILL.md`
- **code-task**: Stage-3 executor for code-task. Implements the application/library change so the dependent (already-written, currently red) test tasks pass. Gates on npm run test.
  path: `docs/ai/shared/workflow/Step-3/code-task/SKILL.md`
- **component-test**: Stage-3 executor for component-test tasks (one per orchestration function). Writes a *.component.spec.ts that mocks/spies internal collaborators (NOT pure unit-level helpers and NOT supertest), then runs npm run test:component.
  path: `docs/ai/shared/workflow/Step-3/component-test/SKILL.md`
- **env-setup**: Stage-3 executor for env-setup tasks. Moves staged mountebank stubs from <case>/01-Testdata/stubs/ to test-env/mountebank/, and reports the DB seeds (from 01-Testdata/db/) that integration tests will preinsert. Runs before any Backlog task.
  path: `docs/ai/shared/workflow/Step-3/env-setup/SKILL.md`
- **integration-test**: Stage-3 executor for integration-test tasks (one per function that touches DB / Redis / a gateway). Writes a *.integration.spec.ts that preinserts DB fixtures from 01-Testdata/db, hits real Postgres/Mongo/Redis and gateway adapters against mountebank stubs, then runs npm run test:integration:local.
  path: `docs/ai/shared/workflow/Step-3/integration-test/SKILL.md`
- **unit-test**: Stage-3 executor for unit-test tasks (one per pure function). Writes a focused *.unit.spec.ts that exercises the real function and its pure helpers — no I/O, no mocks of unit-level helpers — runs npm run test:unit, and marks the task done when assertions are in place.
  path: `docs/ai/shared/workflow/Step-3/unit-test/SKILL.md`
## How to use
When a task matches a skill above, read the file at its path and follow the instructions there.
Run $skill-sync after adding or removing skills in docs/ai/shared/.
