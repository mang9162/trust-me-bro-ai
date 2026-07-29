---
name: acceptance-review
description: Stage-6 of workflow. The acceptance gate — summarize the finished scenario, pause, and let the user accept or reject it (the user decides, never the agent). Surfaces anomalies (agent-detected and user-raised), runs a retrospective, and collects closing feedback, then resolve the decision — accept (the scenario is done) or reject (record the round and hand feedback back to Stage 1 for an additive loop-back). Replaces the old agile loop-back-on-failure — the agent never decides a fix on its own.
---

# Acceptance Review

## Purpose

Stage 6, the last stage. After Stage 5 (`api-test`) has run, hand the finished scenario to the user and let **the user** decide whether it is accepted — a technical pass (every task `done`, every api-test green) is not the same as user acceptance.

This stage **replaces** the old "agile loop-back on failure": the agent no longer analyses a failure and writes its own fix task. Whether api-test failed (a bug to fix) or passed but the user wants something changed, both go through the one gate here — accept, or reject and loop back to Stage 1.

## Procedure

### 1. Self-review against DoD — *not active yet*

*Placeholder — see `roadmap.html` → "Stage 6 — acceptance-review" → AI self-review against Definition of Done.* The intent: before summarizing, the agent vets the scenario against a DoD checklist and surfaces gaps first. The DoD content is not defined yet — skip this step for now and go straight to Summarize.

### 2. Summarize

Read `scenario.html` and give the user a short recap of the finished scenario:

- task statuses across Setup / Backlog / Api-test (done / failed)
- api-test result per assert (pass / fail)
- a recap of the E2E flow steps

Short and scannable — this orients the user before they decide. Don't dump every task; surface the shape and anything that failed.

### 3. ⏸ PAUSE

Hand over to the user for steps 4–6; ask accept / reject only at step 7.

### 4. Concerns the agent detected

While reviewing the finished scenario, look for anomalies — a likely bug, tech debt, a spot that should be hotfixed — and **raise each to the user as a concern; never decide on your own that something is wrong.** For each, the user confirms (a real problem) or dismisses (false positive / not worth it), then apply the **Anomaly routing** to every confirmed one.

**Anomaly routing** — split a confirmed anomaly by whether it belongs to *this* scenario:

- **Not part of this scenario** (unrelated tech debt / a bug elsewhere / a hotfix) → trigger `self-report` with `kind: issue` (`title` / `problem` / `places`), then ask **fix now, or later?**
  - **fix now** → trigger `define-task` on that entry's `id` — it co-designs and stages the fix (a separate run, not part of resolving this scenario).
  - **later** → leave it in `tech-debt.js`; it surfaces in `feed-back.html` for a later `define-task`.
- **Part of this scenario** (something we just changed, or tied to one of its tasks) → a defect in the current work, not an `issue` — **recommend the user reject**, so workflow loops it back to Stage 1 as a fast feedback loop (the existing additive loop-back, carried out in step 7). Do **not** capture it in `tech-debt.js`.

### 5. Anomalies the user raises

Ask the user: **"Did you spot anything wrong we haven't covered?"** — a **separate question** from the closing feedback in step 6. Apply the same **Anomaly routing** (step 4) to each one the user raises.

### 6. Retrospective — *always, whether accepted or rejected*

A short retrospective runs every round, before the decision is resolved:

- List **what came up along the way** — the improvement observations the earlier stages aggregated to `self-learn` (the pending entries in `{small,medium,heavy}-learn.js`) — **as headlines, by count**, not full detail. This is a retro view, not a promotion step.
- Ask the user: **"Any closing feedback?"** This is process feedback (how the work went), separate from a reject's functional feedback (what to fix) and from the anomalies in steps 4–5. If the user gives any, trigger `self-report` with it as a new `occurrence`.

Reviewing / promoting any of these into `code-standards.md` happens later in the **self-learn review (`feed-back.html`), outside the workflow** — never here; unresolved `self-report` entries stay as they are for a later round.

### 7. Resolve — ask for acceptance

Ask the user whether they accept, then record it **through `generate-report`** (it owns `scenario.html`; this stage only triggers it, see Trigger Skill / Role & Boundary):

- **Accept** → mark the scenario accepted and append an **"Accepted"** round to the Acceptance History. The scenario's workflow is done.
- **Reject** → append a new **"Acceptance Round N"** entry with the user's feedback (what to fix / add), then hand it back to **Stage 1** and reset this stage to pending. workflow routes the loop-back (see `workflow/SKILL.md` → Stage 6 routing); the new requirement is written additively (from → to), continuing the existing scenario folder — never a rewrite.

## References

- cross-ref: `scenario.html` — task statuses, api-test results, and the E2E flow, read to Summarize (step 2).
- cross-ref: `self-learn/{small,medium,heavy}-learn.js` — the pending improvement entries, read for the retrospective headline + count (step 6); not modified here.

## Trigger Skill

- generate-report — owns `scenario.html`; triggered to render the Summarize view and to write the acceptance state (accepted flag + Acceptance History round) on both accept and reject. This stage never writes `scenario.html` itself.
- self-report — an out-of-scenario anomaly (steps 4–5) is handed over as a `kind: issue` entry, and any closing process feedback (step 6) as a new `occurrence`.
- define-task — on a **fix-now**, out-of-scenario anomaly (steps 4–5), triggered on that issue entry's `id` to co-design and stage the fix; skipped when the user parks it for later, or when the anomaly belongs to this scenario (that loops back through workflow instead).

## Role & Boundary (Read Before Editing)

This skill owns Stage 6: the acceptance gate. It Summarizes the finished scenario, PAUSEs for the user, and routes on the user's decision — **the user accepts or rejects, the agent never decides on its own** (this replaces the old agile loop-back-on-failure). It surfaces anomalies (ones it detects and ones the user raises) and, for each the user confirms, applies the Anomaly routing: a defect in *this* scenario is recommended back through workflow's reject loop-back, while anything else is captured via `self-report` as a `kind: issue` (optionally handed to `define-task` to fix now). It always runs a retrospective, then resolves the decision — accept (the scenario is done) or reject (records the round and hands feedback back to Stage 1 for an additive loop-back).

It does NOT:

- write `scenario.html` itself — `generate-report` owns it; this stage only triggers it (accepted flag, Acceptance History, and the Summarize view all go through generate-report).
- analyse a failure or write a fix itself — for a defect in *this* scenario the fix **task** is `create-task`'s (on the loop-back), for an out-of-scenario `kind: issue` it is `define-task`'s; fix **code** is `execute-tdd`'s or `execute-issue`'s. This stage only **surfaces** anomalies (as concerns, or captured `issue` entries) and hands them off — it never designs, authors, or runs a fix, and never decides on its own that something is wrong.
- re-run api-test or any earlier stage — it reviews their output only.
- review self-learn entries in detail — that is the self-learn review in `feed-back.html`, outside the workflow; here they are only listed as a retrospective headline + count.
- own the loop-back routing or the folder / `NN` conventions — that is `workflow`; this stage only supplies the reject feedback.

For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
