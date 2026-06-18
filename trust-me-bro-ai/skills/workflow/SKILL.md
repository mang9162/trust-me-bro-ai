---
name: workflow
description: Orchestrate a feature from a requirement through TDD tests, implementation, and end-to-end API verification. Six stages with explicit review pauses — (1) get requirement and write scenario.html with user-story steps, (2) create test data + stubs, (3) define tasks, (4) execute the TDD task queue (loop-dispatch per task.type), (5) author the api-test suite then run it once, (6) accept or reject the scenario — reject loops back to Stage 1.
---

# Workflow

## When to invoke
- User provides a requirement and wants tests + implementation + (optionally) API scenario verification.
- Multi-step feature work needing explicit tracking + future agent delegation.

## Role & Boundary (Read Before Editing)

`workflow` is control-only. At any point it answers exactly 3 questions:
1. Which scenario / stage are we in right now?  -> state
2. Which skill runs next?                       -> routing (see Stages table)
3. Do we pause for review now?                  -> gating

It MUST NOT contain:
- "How to" procedure for any stage - lives in that stage's own SKILL.md
- Domain/technical conventions (commands, file-naming, framework/tooling specifics, .env rules, etc.) - tech-stack/code-standards.md
- Self-learn logic/format - each stage skill's own closing step triggers `self-report`; entry schema lives in `skills/self-learn/` (Issue #16)
- Test-level classification criteria - create-task
- Content-file references (data.md, gateway-directory.md, error-codes.md, etc.) - referenced by the stage skill that uses them

If a sentence describes HOW something is done, it does not belong here - move it to the relevant stage skill.

## Layout (under `work/`, committed — push to share with teammates)
```
work/Scenario/<FEATURE>/{Success|Alternative}/<NN>-<FULL_SCENARIO_NAME>/
├── scenario.html                                             ← scenario identity + user-story steps + report
├── 01-Testdata/
│   ├── Datatest.md                                           ← per-scenario concrete values
│   ├── db/{postgres.json,mongo.json}                         ← only when DB seeding is needed
│   └── stubs/<downstream-service>/<SCENARIO>-<purpose>.json
└── 02-Task/
    ├── 01-Setup/                                             ← env-prep tasks
    │   └── 00-env-setup.json
    ├── 02-Backlog/                                           ← code + test tasks (one per function)
    │   ├── 01-<functionName>-unit-test.json
    │   ├── 02-<functionName>-integration-test.json
    │   ├── 03-<functionName>-component-test.json
    │   └── 04-<functionName>-code-task.json
    └── 03-Api-test/                                          ← Bruno scenario, one task per request
        ├── 01-<actionName>-api-test.json
        └── ...
```
Each sibling folder restarts its own `NN` counter.

## Responsibility map

| Skill | Stage | Responsibility |
|---|---|---|
| initialize | (pre) | Bootstrap trust-me-bro-ai/context/ + trust-me-bro-ai/tech-stack/ if missing |
| get-requirement | 1 | Clarify requirement, write scenario.html steps |
| create-test-data | 2 | Datatest.md, DB seeds, stubs |
| create-task | 3 | Functional design + task breakdown + test-level classification |
| unit-test/integration-test/component-test/code-task/env-setup | 4 | TDD execution per task, dispatched by task.type |
| api-test | 5 | Author + run api-test suite |
| acceptance-review | 6 | Accept/reject gate; reject -> back to Stage 1 |

Every skill above ends with its own self-learn step + update-report step. workflow only needs "the skill is done" to gate.

## Preconditions
Before Stage 1: if trust-me-bro-ai/context/ or trust-me-bro-ai/tech-stack/ is missing/empty -> invoke initialize first.

## Stages

| # | Skill | Pauses after? |
|---|---|---|
| 1 | get-requirement | yes |
| 2 | create-test-data | yes |
| 3 | create-task | yes |
| 4 | TDD loop - dispatch per task.type | yes (queue drained or deadlock) |
| 5 | api-test | yes |
| 6 | acceptance-review | yes (gate) |

For each stage:
1. Invoke the skill matching the current stage (Stage 4 = loop-dispatch per task).
2. Wait for the skill to finish (procedure detail lives in that skill's SKILL.md).
3. PAUSE - run generate-report, wait for user review before advancing.

### Stage 6 routing
- Accept -> done for this scenario.
- Reject -> record reason, go back to Stage 1 with the rejection as new/updated requirement input; continue 2->6 again.
