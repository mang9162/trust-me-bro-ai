---
name: index
description: Master index of all shared team skills. Use when starting any task — read this first to find the right skill, then follow its path to load the full instructions.
---

# Shared Skills Index

<!-- AUTO-GENERATED — do not edit manually, run $skill-sync instead -->

- **default-tdd**: The default skill an engineer agent follows when its dispatcher (`execute-tdd` or `execute-issue`) hands it a task and no type-specific handler (`agent-skill/<task.type>/`) applies. It guides the agent to produce exactly that one task's artifact from the task's own fields + the project's standing conventions, run the task's command, and self-verify the result against the task's acceptance (red / green / compiles) before handing back. It is the playbook, not the engineer — the agent is the engineer; this skill is the procedure it follows for one task.
  path: `trust-me-bro-ai/skills/agent-skill/default-tdd/SKILL.md`
- **create-pr**: Generate a GitHub PR title and description following the project template (Problems / Solutions / Changes, then Test Result / Reference artifact tables). Outputs copy-paste text only — does not run gh pr create.
  path: `trust-me-bro-ai/skills/create-pr/SKILL.md`
- **create-skill**: The rules and format for creating or editing any skill in this kit — how to write the body (lean, ordered, condition-driven) and declare cross-file connections (## References / ## Trigger Skill / ## Writes To / ## Role & Boundary). Read before creating or editing a skill. Pairs with file-map.html (in this folder).
  path: `trust-me-bro-ai/skills/create-skill/SKILL.md`
- **generate-report**: Regenerate scenario.html inside the scenario folder (under work/). Reads the scenario-meta JSON block from the existing scenario.html, Datatest.md, and all task JSON files. Produces an interactive HTML with a 6-stage progress indicator, a scrollable E2E flow, a Functional Design tree, collapsible Test Data and Tasks sections, expandable task cards, and an Acceptance History log. Re-run after any stage to refresh.
  path: `trust-me-bro-ai/skills/generate-report/SKILL.md`
- **initialize-sync-task-github-project**: Installs sync-task for one repo against a GitHub Projects board — preflight auth, pick the board, ensure its Status/Date fields, generate a sync-task-<name> skill from skill-format.md, then a test-loop until the user accepts. Re-run to add another board.
  path: `trust-me-bro-ai/skills/initialize/initialize-sync-task/github-project/SKILL.md`
- **initialize-sync-task**: Router for setting up external task sync — asks which tracker, then hands off to that vendor's installer. Today: GitHub Projects; other trackers fall back to a DIY template. Re-run to add another board / vendor.
  path: `trust-me-bro-ai/skills/initialize/initialize-sync-task/SKILL.md`
- **initialize**: First-run bootstrap and re-sync. Scan the repo (light or full), migrate any existing docs, and create/update the context/tech-stack knowledge files from the format templates under initialize/ — using a target's own format when it already exists.
  path: `trust-me-bro-ai/skills/initialize/SKILL.md`
- **define-task**: Task author for recorded issues (tech debt / bug / hotfix / upkeep) — turns a `kind: issue` entry from `tech-debt.js` into TDD fix tasks under `work/Issue/` that execute-issue runs.
  path: `trust-me-bro-ai/skills/maintenance/define-task/SKILL.md`
- **execute-issue**: Runs one issue-fix folder's TDD tasks. Invoked pointed at a `work/Issue/<NN>-<slug>/` that define-task staged; drains its `Backlog/` in dependency order, dispatching each task to an engineer agent (`agent-skill/<task.type>/` handler, else `agent-skill/default-tdd`) and accepting by the task's own acceptance (red / green / all-green). It is the loop / dispatcher — it does not implement code. Halts and asks the user on any blocking gap; there is no report, and when the queue is drained the run simply ends (no next stage).
  path: `trust-me-bro-ai/skills/maintenance/execute-issue/SKILL.md`
- **self-improve**: Executes a chosen fix for one self-learn entry — from a feed-back.html copy-prompt, a custom fix typed by the user, or an automatic hand-off from self-report (per-tier Auto-improve setting). Always reviews entries across all three tiers. Confirms understanding before executing if anything is ambiguous, then moves the entry from its tier file into log.js with chosenOption + appliedDate.
  path: `trust-me-bro-ai/skills/self-learn/self-improve/SKILL.md`
- **self-report**: Sole writer of the self-learn entry files — `{small,medium,heavy}-learn.js` (tiered kit issues) and `tech-debt.js` (`kind: issue` — app-code tech debt / bugs / hotfixes). Triggered by any other skill that notices a self-learn-worthy issue. Dedupes against existing entries (append occurrence vs. new entry); tiered entries also classify tier and honor the Auto-improve setting. Silent mid-flow except a heavy tier, which always warns the user.
  path: `trust-me-bro-ai/skills/self-learn/self-report/SKILL.md`
- **skill-sync**: Sync shared skills index to .agents/skills/index and .claude/skills/index. Use this whenever a new skill is added to or removed from trust-me-bro-ai/skills/.
  path: `trust-me-bro-ai/skills/skill-sync/SKILL.md`
- **update-kit**: Update this installed kit from its upstream repo one version at a time — show what each version fixed and added, let the user pick how far to go, and ask before overwriting anything edited locally.
  path: `trust-me-bro-ai/skills/update-kit/SKILL.md`
- **workflow**: The root orchestrator that drives a feature from requirements through TDD, implementation, and E2E verification. Manages the state transitions across 6 sequential stages.
  path: `trust-me-bro-ai/skills/workflow/SKILL.md`
- **get-requirement**: Stage-1 of workflow. Read the requirement, resolve ambiguities with the user, identify scenarios, and define scenario.html content for each with user-story steps (generate-report writes the file). Pause for user review before any test data or tasks are created.
  path: `trust-me-bro-ai/skills/workflow/Stage-1/get-requirement/SKILL.md`
- **create-test-data**: Stage-2 of workflow. Read the central dictionary + gateway/seeding references, then stage this scenario's test data: Datatest.md (values, with expect + status columns), DB seeds, and stubs. Missing-or-unsure values are asked back; anything not catalogued is reported to self-report (silent) and flagged in Datatest's status. Pause for user review.
  path: `trust-me-bro-ai/skills/workflow/Stage-2/create-test-data/SKILL.md`
- **create-task**: Stage-3 of workflow. From the agreed scenario.html, design the functional call tree and break the scenario into atomic, self-sufficient TDD tasks (one task = one unit), grouped into Setup / Backlog / Api-test and ordered by dependency with each test paired to its code. Each task carries enough that any agent finishes it without opening another task. Authors the functional-design tree into scenario.html; pauses for review.
  path: `trust-me-bro-ai/skills/workflow/Stage-3/create-task/SKILL.md`
- **execute-tdd**: Stage-4 of workflow. The central TDD execution loop. Drains the Setup + Backlog tasks authored by create-task in dependency order; for each task it runs a pre-flight / dispatch / close-out checklist, hands the task + a skill (the type handler at `agent-skill/<task.type>/` if one exists, otherwise `agent-skill/default-tdd`) to an engineer agent, then accepts the result against the task's own acceptance (red / green / compiles). Does not implement code itself. Halts and asks the user on a blocking gap (deadlock, failure, an assume that doesn't hold); refreshes the report and pauses when the queue is drained, then hands off to Stage 5.
  path: `trust-me-bro-ai/skills/workflow/Stage-4/execute-tdd/SKILL.md`
- **api-test**: Stage-5 of workflow. Author the `03-Api-test/` tasks into the project's api-test files and run them, one task at a time in dependency order — the agent running this skill authors each file itself, no dispatch to an engineer agent. Accepts each task against its own `acceptance`; halts and asks the user on a blocking gap (deadlock, failure, an `assume` that doesn't hold); refreshes the report and pauses for Stage 6 when the queue is drained.
  path: `trust-me-bro-ai/skills/workflow/Stage-5/api-test/SKILL.md`
- **acceptance-review**: Stage-6 of workflow. The acceptance gate — summarize the finished scenario, pause, and let the user accept or reject it (the user decides, never the agent). Surfaces anomalies (agent-detected and user-raised), runs a retrospective, and collects closing feedback, then resolve the decision — accept (the scenario is done) or reject (record the round and hand feedback back to Stage 1 for an additive loop-back). Replaces the old agile loop-back-on-failure — the agent never decides a fix on its own.
  path: `trust-me-bro-ai/skills/workflow/Stage-6/acceptance-review/SKILL.md`
## How to use
When a task matches a skill above, read the file at its path and follow the instructions there.
Run $skill-sync after adding or removing skills in trust-me-bro-ai/skills/.
