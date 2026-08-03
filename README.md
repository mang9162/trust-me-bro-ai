# trust-me-bro-ai

> When a developer says "it works, trust me bro" — don't.
> This project is named after that line on purpose, because it does the exact opposite: **there is no "trust me bro", only proof by tests.** Write the test red first, then write code until it's green, and let a human review at every gate.

---

## Hey new hire (read this first)

Picture a fresh junior joining the team — just out of an intense TDD bootcamp, can recite "red first, green second, refactor third" in their sleep, but has never touched a real project. They don't know where this team puts its files, which commands to run, how it talks to the database, or how it calls other services.

**That junior is the AI driven by the skills in this project.**

Their strength is *rock-solid TDD discipline* — we force them to follow the playbook one stage at a time, no shortcuts. Their weakness is *no domain skill yet* — but they level up every task, because whenever they trip over something (a missed pattern, a broken reference, a naming mismatch) they jot it in their notebook (`self-learn`) and apply it next round.

---

## Purpose

`trust-me-bro-ai` is a **skill kit for AI agents** (e.g. Claude Code / Codex) you drop into any repo to turn a one-line requirement into **tested, reviewed code** through a disciplined TDD process.

- **Real TDD** — every function gets a test that fails first, then code to make it pass.
- **A human gate at every stage** — the AI never accepts its own work; a human accepts or rejects.
- **Knowledge split from procedure** — repo-specific facts (stack, structure, DB, downstream services) live in dedicated knowledge files; the how-to procedure stays generic, reusable skills.
- **Learns from real work** — trips get written down and applied next round (`self-learn`), like a junior who steadily levels up.

> This repo is *the kit itself* — it defines the shape of the skills and knowledge files, not a destination app. To use it, drop the `trust-me-bro-ai/` folder into that app's repo.

---

## What's new

- **v1.0.0** — the foundation: the 6-stage TDD loop, `self-learn`, and a human gate at every stage.
- **v1.1.0** — maintenance lane: turn a logged bug / tech-debt / hotfix into staged TDD fix tasks (`define-task` → `execute-issue`).
- **v1.2.0** — `sync-task`: push staged work to an external tracker (GitHub Projects) as a parent + sub-issues (opt-in).
- **v1.2.1** — `create-task` now self-reviews the design for anomalies before execute.
- **v1.2.2** — on sync, the syncing account is assigned to each task once it's `done`.

---

## Install

The kit is just the `trust-me-bro-ai/skills/` folder — Markdown the AI reads, nothing to build.

1. **Drop it in** — copy the `trust-me-bro-ai/` folder into the target repo.
2. **Build the index** — `bash trust-me-bro-ai/skills/skill-sync/scripts/sync.sh` regenerates `.claude/skills/index/` + `.agents/skills/index/`. Re-run when you add/remove a skill (or say `$skill-sync`).
3. **Bootstrap knowledge (once)** — run `initialize`; it scans the repo (light or full) and writes the knowledge files under `context/` + `tech-stack/`.
4. **(optional) Wire a tracker** — run `initialize-sync-task` to sync work to a board.

Then invoke `workflow` with a requirement.

---

## Usage — the two lanes

**Feature lane** — a new requirement. Invoke `workflow` (the lead that only routes: which stage / which skill next / time to pause). It pauses for human review after **every** stage:

1. `get-requirement` — clarify → scenario + user-story steps
2. `create-test-data` — stage values (`Datatest.md`), DB seeds, stubs for downstream services
3. `create-task` — design the call tree, **self-review it**, break into atomic tasks (1 task = 1 unit), test paired with code
4. `execute-tdd` — the TDD loop: one task at a time, red → green, until the queue drains
5. `api-test` — author + run the api-test suite end-to-end
6. `acceptance-review` — summarize; a **human** accepts (done) or rejects (→ loop back to Stage 1)

**Maintenance lane** — a bug / tech debt / hotfix logged during work:

- `self-report` logs it as an issue in `tech-debt.js` (usually mid-work, automatically)
- `define-task` turns one issue into staged TDD fix tasks under `work/Issue/`
- `execute-issue` runs them (baseline check → red→green → regression gate)

Both lanes: hit a wall (deadlock, failing test, a broken `assume`) → **stop and ask**, never guess. Work lives in `work/` (one folder per scenario/issue), committed and shareable.

---

## Features — what you can do & how

| I want to… | How |
|---|---|
| Build a feature from a requirement | invoke `workflow` → runs the 6-stage loop |
| Fix a logged bug / tech-debt | `define-task` (from `feed-back.html` or an entry id) → `execute-issue` |
| Review & apply the AI's self-learned notes | open `self-learn/feed-back.html`; `self-improve` applies a chosen fix |
| Watch progress visually | `generate-report` → renders `scenario.html` (progress, E2E flow, call tree, task cards) |
| Sync work to a team board | install once with `initialize-sync-task`; the stages then push automatically |
| Draft a PR | `create-pr` → copy-paste title + body |
| Refresh the skill index | `skill-sync` |
| (Re)bootstrap repo knowledge | `initialize` |

---

## Components

Grouped the same as `create-skill/file-map.html` — the single source of truth for how every file connects.

| Group | What it does |
|---|---|
| **Control skill** (C0) | `create-skill` — the rules + format for writing/editing any skill, plus `file-map.html`. Read before editing a skill. |
| **Workflow control** (C1) | the `workflow` lead (state / routing / gating) + the six stage skills. The spine that turns a requirement into tested code. |
| **Context** (C2) | repo knowledge other skills read: data dictionary, domain reference, gateway directory, error codes. |
| **Tech stack** (C3) | the technical manual: tech stack, code standards, testing guide, database schema, gateway contracts. |
| **generate-report** (C4) | renders `scenario.html` into an interactive view; re-runnable after any stage. |
| **initialize** (C5) | day-one bootstrap — fills the Context + Tech-stack files from the `*-format.md` templates. |
| **self-learn** (C6) | the notebook: `self-report` writes entries — `problem` (kit gap), `candidate` (promote a pattern into code standards), `issue` (app-code fix); `self-improve` applies fixes; reviewed in `feed-back.html`. |
| **Work output** (C7) | one folder per scenario/issue under `work/` — `scenario.html` / `issue.md` + test data + task queues. Committed and shared. |
| **maintenance** (C8) | the issue-fix pipeline: `define-task` stages TDD tasks from a logged issue, `execute-issue` runs them. |
| **agent-skill** (C9) | engineer playbooks `execute-tdd` dispatches (e.g. `default-tdd`). |
| **sync-task** (C10) | opt-in external-tracker sync: `initialize-sync-task` installs a per-board `sync-task-<name>` skill that pushes work as a parent + sub-issues. |

Utilities: `create-pr` (PR text) · `skill-sync` (index refresh).
