---
name: upgrade-lib
description: Plans an upgrade for one explicitly named library. It researches the repository and current official release evidence, asks the human to approve a direct or staged path, then hands the approved detail to define-task. It does not change dependencies or application code.
---

# Upgrade Lib

## Purpose

Plan one library upgrade from the repository's current state to one reviewed target. Research the evidence, design the smallest safe path, get the human's decision, and hand the approved detail to `define-task`.

This skill ends at handoff. It does not edit a manifest, lockfile, source file, `work/Issue/`, or any self-learn file; execution belongs to `execute-issue` after the human reviews the materialized tasks.

## Procedure

### 1. Fix the subject

Require one exact library name. One invocation may cover that library across one or more necessary version boundaries, but never a second library. If several libraries are requested, ask the human which one to plan first.

The target version may be supplied by the human. If it is not, research a stable candidate and present it for review; never silently choose a prerelease or a different package.

### 2. Research the current repository state

Read the live repository rather than a stored dependency profile:

- locate the relevant manifest and current lockfile entry, and establish the declared and resolved versions;
- find the library's real usage in source, tests, scripts, configuration, and startup paths;
- identify current runtime, peer-dependency, package-manager, and test-command constraints from the files that own them;
- identify any install prerequisite. Name only the required environment variable or external prerequisite — never request, print, or store a credential.

Treat missing or conflicting evidence as an open question for the human. Do not write a repository-wide inventory or an upgrade log.

### 3. Research the target and compatibility path

Use current official package metadata, release notes, migration guides, and compatibility documentation. Establish:

- target version and stable/prerelease status;
- changes between the current and target versions that affect the observed usage;
- runtime and peer requirements, install implications, and documented breaking changes;
- exact validation needed to distinguish a safe upgrade from a regression.

Prefer a direct jump to the reviewed target when there is no major-version boundary or documented breaking change that needs isolation. When a major boundary or breaking change does need isolation, propose only the stages and checkpoints that reduce a concrete risk; do not manufacture a hop through every patch or minor release.

### 4. Human decision gate

Present the current version, proposed target, evidence, affected usage, prerequisites, validation gates, and the direct or staged path. Separate confirmed facts from unresolved risks and alternatives.

Stop until the human approves the path and chooses where the work will be materialized:

- `new` — create a new issue folder; or
- an exact existing `work/Issue/<NN>-<slug>/` path — redefine work in that issue.

Do not create tasks, edit dependencies, or invoke `define-task` before this approval.

### 5. Hand off the approved detail

After approval, produce this envelope:

```yaml
source: upgrade-lib
issueTarget: new | work/Issue/<NN>-<slug>/
issue:
  problem: <current dependency problem or need>
  whyFix: <why this upgrade is worth doing now>
  expectedResult: <observable state after every task passes>
upgrade:
  library: <exact name>
  current: <declared and resolved versions>
  target: <approved version and specifier>
  steps:
    - <approved dependency change, affected usage, required adaptation, and validation>
  prerequisites: [<environment variable or external prerequisite names>]
  evidence: [<official release or compatibility facts used in the decision>]
```

Carry the exact manifest/lockfile targets, package-manager change, affected usage, breaking-change behavior/test cases, validation commands, constraints, and evidence that `define-task` needs. Keep approved staged steps in order. Do not turn the detail into task JSON or choose task types, dependencies, or file layout; those belong to `define-task`.

### 6. Hand off and stop

Pass the approved envelope directly to `define-task`. This skill's job is complete when the handoff is accepted for materialization. The human reviews the resulting `issue.md` and task files before separately invoking `execute-issue`.

## Trigger Skill

- `maintenance/define-task` — turn the approved issue/upgrade detail into its issue/task format in the human-selected target (step 6).

## Role & Boundary (Read Before Editing)

This skill owns dependency-specific research, direct-versus-staged upgrade design, the human decision gate, and the approved detail in the `source: upgrade-lib` handoff. It handles exactly one library per invocation and may cross multiple versions only when the reviewed path requires it.

It does NOT modify dependencies or application code; write `work/Issue/`; author task JSON; execute tasks; own the task schema, issue layout, or dispatcher; write an upgrade log; write `tech-debt.js`; or route through `self-report`. `define-task` turns the approved detail into its issue/task format, `execute-issue` dispatches it, and the human decides whether later blocked work is re-planned in a new or existing issue.

For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
