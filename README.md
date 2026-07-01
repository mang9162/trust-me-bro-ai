# trust-me-bro-ai

> When a developer says "it works, trust me bro" — don't.
> This project is named after that line on purpose, because it does the exact opposite: **there is no "trust me bro", only proof by tests.** Write the test red first, then write code until it's green, and let a human review at every gate.

---

## Hey new hire (read this first)

Picture a fresh junior joining the team — just out of an intense TDD bootcamp, can recite "red first, green second, refactor third" in their sleep, but has never touched a real project. They don't know where this team puts its files, which commands to run, how it talks to the database, or how it calls other services.

**That junior is the AI driven by the skills in this project.**

Their strength is *rock-solid TDD discipline* — because we force them to follow the playbook one stage at a time, no shortcuts allowed. Their weakness is *no domain skill yet* — but they get better with every task, because whenever they trip over something (a missed pattern, a broken reference, a naming mismatch), they jot it down in their own notebook (`self-learn`) and apply it next round.

---

## Purpose

`trust-me-bro-ai` is a **skill kit for AI agents** (e.g. Claude Code / Codex) that you drop into any repo to turn "a one-line requirement" into **tested, reviewed code** through a disciplined 6-stage TDD process.

Its core ideas:

- **Real TDD, not TDD in name only** — every function needs a test that fails first, then code to make it pass.
- **A human review gate at every stage** — the AI never accepts its own work; a human is the one who accepts or rejects.
- **Knowledge separated from procedure** — "repo-specific knowledge" (stack, structure, database, downstream services) is extracted into dedicated knowledge files, while the "how-to procedure" stays as generic, reusable skills that work in any repo.
- **Learns from real work** — when it trips on something it writes it down and adapts (`self-learn`), like a junior who steadily levels up.

> Note: this repo is *the kit itself* (it defines the "format/shape" of the skills and knowledge files), not a destination app. To use it for real, you drop the `trust-me-bro-ai/` folder into that app's repo.

---

## Installation

The kit is really just the `trust-me-bro-ai/skills/` folder — nothing to build or compile. They're Markdown files the AI reads and follows. Three steps:

**1. Drop the kit into the target repo**
Copy/add the `trust-me-bro-ai/` folder into the repo you want the junior to work in.

**2. Sync the skill index so the agent can see it**
```bash
bash trust-me-bro-ai/skills/skill-sync/scripts/sync.sh
```
This scans every skill and regenerates the index for both agents:
- `.claude/skills/index/SKILL.md` (for Claude Code)
- `.agents/skills/index/SKILL.md` (for Codex)

Once the index exists, the agent knows which skills exist and where they live.
(Re-run it whenever you add/remove a skill — or just say `$skill-sync`.)

**3. Bootstrap the repo's knowledge (one-time)**
Prompt to `initialize` like `I just drop the kit run initailize.` — it scans the repo (you pick light or full mode) and writes the knowledge files under `trust-me-bro-ai/context/` and `trust-me-bro-ai/tech-stack/` (stack, code standards, schema, etc.), like writing its own onboarding wiki.

After that you're ready to go — invoke `workflow` with a requirement.

## Usage — the 6-stage work loop

Start by handing the junior a requirement and invoking `workflow`. `workflow` is just "the lead who points the way" — it does no stage's work itself. It only answers three questions on repeat: *which stage are we in / which skill runs next / is it time to pause for review* — then routes to that stage's skill.

```
requirement
    |
    v
[Stage 1] get-requirement   -- clarify the requirement, write scenario + user-story steps
    |  (pause for review)
    v
[Stage 2] create-test-data  -- stage test data: values in Datatest.md, DB seeds, stubs for downstream services
    |  (pause for review)
    v
[Stage 3] create-task       -- design the call tree, break it into atomic tasks (1 task = 1 unit), ordered by dependency, test paired with code
    |  (pause for review)
    v
[Stage 4] execute-tdd       -- the real TDD loop: pick one task at a time, red -> green, until the queue is drained
    |  (pause for review)
    v
[Stage 5] api-test          -- author + run the api-test suite end-to-end for real
    |  (pause for review)
    v
[Stage 6] acceptance-review -- summarize the work, then let a HUMAN accept / reject
    |
    +-- accept -> scenario done
    +-- reject -> feed the feedback back to Stage 1 for another round
```

Key points of this loop:

- **Pause at every stage** — the junior doesn't sprint straight to the finish; every gate waits for human review before moving on, so mistakes get caught before they cascade.
- **Hit a wall, stop and ask** — if Stage 4/5 hits a deadlock, a failing test, or an `assume` that doesn't hold, the junior halts and asks a human instead of guessing and barreling on.
- **Reject isn't failure** — it's fresh input. Whether it's "a bug" or "passed but the user wants a change", both go through the same gate and loop back to Stage 1.
- **Work lives in `work/`** — every scenario gets its own folder (scenario.html + test data + task JSON), committed and pushable to share with the team.

Along the way, `generate-report` keeps rendering `scenario.html` into a clean HTML view where you can watch progress across all 6 stages, plus the call tree and task cards.

---

## What each component does

The kit is organized into a handful of groups (the same grouping as `create-skill/file-map.html`, the single source of truth for how everything connects):

| Group | What it does |
|---|---|
| **Control skill** | The rules + format for writing/editing any skill in this kit, plus the `file-map.html` that maps how every file connects. Read before creating or editing a skill. |
| **Workflow control** | The loop itself — the `workflow` lead (state / routing / gating) and its six stage skills (get-requirement -> create-test-data -> create-task -> execute-tdd -> api-test -> acceptance-review), plus the default engineer playbook execute-tdd dispatches. This is the spine that turns a requirement into tested code. |
| **Context (project knowledge)** | Repo-specific facts other skills read: the data dictionary, domain reference, downstream gateway directory, and error codes. |
| **Tech stack** | The technical manual: tech stack, code standards, testing guide, database schema, and gateway contracts. |
| **generate-report** | Renders `scenario.html` into an interactive HTML view (6-stage progress, E2E flow, call tree, task cards). Re-runnable after any stage. |
| **initialize** | Day-one bootstrap — scans the repo and fills the Context + Tech-stack files from the `*-format.md` templates so the junior has this repo's manual. |
| **self-learn** | The notebook that makes the junior better each task: `self-report` writes tiered entries (small/medium/heavy) when a skill trips on something; `self-improve` applies a chosen fix and moves the entry into the log. |
| **Work output** | One folder per scenario under `work/` — `scenario.html`, the test data, and the Setup/Backlog/Api-test task queues. This is what gets committed and shared. |

---
