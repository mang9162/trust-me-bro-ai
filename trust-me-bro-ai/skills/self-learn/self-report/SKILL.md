---
name: self-report
description: Sole writer of the self-learn entry files — `{small,medium,heavy}-learn.js` (tiered kit issues) and `tech-debt.js` (`kind: issue` — app-code tech debt / bugs / hotfixes). Triggered by any other skill that notices a self-learn-worthy issue. Dedupes against existing entries (append occurrence vs. new entry); tiered entries also classify tier and honor the Auto-improve setting. Silent mid-flow except a heavy tier, which always warns the user.
---

# Self Report

## When to invoke

- Any other skill notices something during its own work that should be remembered for later — a recurring pattern, a missing/incorrect reference, a naming inconsistency, a convention that wasn't followed, etc.
- Triggered as part of that skill's own closing steps. Not normally invoked directly by the user.

## Procedure

1. **Receive from the caller** — read which `kind` it is:

   | field | what it is | problem | candidate | issue |
   |---|---|---|---|---|
   | `reportedBy` | the calling skill's name | ✓ | ✓ | ✓ |
   | `title` | short title (for a candidate, the pattern itself) | ✓ | ✓ | ✓ |
   | `problem` | the bug / gap, or why the pattern should be a rule | ✓ | ✓ | ✓ |
   | `occurrence` | what was seen this time (+ today's date) | ✓ | ✓ | ✓ |
   | `kind` | `problem` (default), `candidate`, or `issue` | ✓ | ✓ | ✓ |
   | `places` | the code location(s) the caller saw it at — appended to the entry's `places` **list** (kept auditable) | — | ✓ | ✓ |

   A `problem` is a bug / gap in the **kit / reference files** to fix; a `candidate` is a recurring code pattern to promote into `code-standards.md`; an `issue` is an **app-code** fix (tech debt / bug / hotfix) parked in `tech-debt.js` for `define-task` to turn into fix tasks later — it carries no `tier` and no `fixOptions` (the fix approach is decided in define-task, not here).
2. **Dedup** — search the entry file this `kind` lives in (`problem` / `candidate` → the three tier files; `issue` → `tech-debt.js`) for a match. `problem` and `issue` match on their `problem` text; `candidate` matches on its `title` / pattern:

   | case | action |
   |---|---|
   | **match found** | append to `occurrences[]` (date/by/note); a `candidate` or `issue` also **adds the new place(s)** to `places` (dedup duplicates); a `candidate` then **recomputes `point`**. Don't change `tier`/`fixOptions` on recurrence — that's `self-improve`'s call. |
   | **no match** | new entry: `id` = `<YYYYMMDD>-<short-slug>`, `status: pending`, `firstSeen` = today, `kind`. A `problem` carries 1+ `fixOptions`; a `candidate` sets `places` + `point` with a "promote as a rule" fix option → `files: ["tech-stack/code-standards.md"]`; an `issue` sets `places` and carries **no `tier` / `fixOptions`**. |

3. Classify `tier` (small / medium / heavy) — see Tier definitions below. **`kind: issue` has no tier** (tier is defined by which kit file a fix touches; an app-code fix doesn't map to it) — skip this step.
4. Write the entry (new or updated) into its file: a tiered entry into `<tier>-learn.js`; an `issue` into `tech-debt.js`.
5. **small / medium / issue** -> **silent** mid-flow — don't interrupt the caller; the calling stage surfaces this round's entries at its pause.
6. **heavy** -> always warn the user (heavy = process-level impact, they need to know now), regardless of the Auto-improve setting.
7. Check **Auto-improve** (below) for this entry's tier — tiered entries only. **`kind: issue` never runs Auto-improve**: its resolver is `define-task` (invoked separately — from `feed-back.html` later, or right after by the reporting stage on a fix-now), not `self-improve`. self-report neither triggers nor performs the fix.
   - **on** -> immediately trigger `self-improve` for this entry (pass its `id` and `<tier>-learn.js`).
   - **off** (default) -> do not trigger `self-improve`. If the caller or user wants it fixed now, tell them to invoke `self-improve` themselves.

## Tier definitions

- **small** = fixing it touches a single file, and that file is a "soft component" (`context/`, `tech-stack/`, `{small,medium,heavy}-learn.js`, `log.js`).
- **medium** = (a) fixing it touches 1-2 files of a "hard component" (`initialize`, `self-report/SKILL.md`, `self-improve/SKILL.md`, `feed-back.html`, `workflow` including its stage skills, `generate-report` — edited rarely, invoked/read constantly) without affecting many references, or (b) it touches several soft-component files at once.
- **heavy** = process-level change — requires reworking/fixing references across many files, or changes how a structure works.

## Auto-improve (edit this table directly to change behavior)

| Tier | Auto-trigger self-improve? |
|---|---|
| small | off |
| medium | off |
| heavy | off |

Default `off` for every tier — self-report only writes the entry (and warns for heavy); a human (or the user, via `feed-back.html`) decides when to run `self-improve`. Flip any row to `on` to make self-report immediately trigger `self-improve` for new/updated entries of that tier, right after writing them in step 4.

## Candidate scoring (edit this table directly)

self-report is the **only** skill that holds this formula and computes the score — the caller reports where it just saw the pattern, never a score; self-report appends the location(s) to the candidate's `places` list (deduped, so the count stays auditable) and derives `point` from `places.length`, recomputing on every new occurrence:

`point = occurrences.length × seenWeight + places.length × placeWeight`

| param | default | meaning |
|---|---|---|
| `seenWeight` | 1 | per occurrence — how many rounds the pattern was reported |
| `placeWeight` | 2 | per place in the code now — weighed heavier (it's ground truth) |

Every candidate is shown in `feed-back.html` (sorted by `point`, highest first); the user reviews / promotes / rejects it there (a rejected candidate is deleted). It is **never auto-promoted**.

## Entry schema (`small-learn.js` / `medium-learn.js` / `heavy-learn.js` — `var <TIER>_LEARN = [...]`)

**`problem`** (the default kind):

```json
{
  "id": "20260612-gwdir-purpose-missing",
  "kind": "problem",
  "tier": "medium",
  "status": "pending",
  "firstSeen": "2026-06-12",
  "reportedBy": "create-test-data",
  "title": "short problem title",
  "problem": "describe the problem...",
  "occurrences": [
    { "date": "2026-06-12", "by": "create-test-data", "note": "what was seen..." }
  ],
  "fixOptions": [
    { "label": 1, "addresses": "what this option fixes", "files": ["context/gateway-directory.md"], "steps": ["step1", "step2"] },
    { "label": 2, "addresses": "...", "files": ["..."], "steps": ["..."] }
  ]
}
```

**`candidate`** — same shape plus a top-level `places` (the list of code locations) and `point` (the score self-report computes from `places.length`); its fix option promotes the pattern into `code-standards.md`:

```json
{
  "id": "20260626-errhandling-trycatch-throw",
  "kind": "candidate",
  "tier": "small",
  "status": "pending",
  "firstSeen": "2026-06-26",
  "reportedBy": "execute-tdd",
  "title": "error handling: try/catch → logger.error → throw AppError",
  "problem": "pattern recurs across the codebase but isn't a rule in code-standards.md yet",
  "places": ["OrderService.createOrder", "PaymentService.charge"],
  "point": 6,
  "occurrences": [
    { "date": "2026-06-26", "by": "execute-tdd", "note": "saw the pattern in OrderService.createOrder" },
    { "date": "2026-06-27", "by": "execute-tdd", "note": "saw it again in PaymentService.charge" }
  ],
  "fixOptions": [
    { "label": 1, "addresses": "promote as a code-standard",
      "files": ["tech-stack/code-standards.md"],
      "steps": ["add to Programming Practices: wrap external calls in try/catch → logger.error → throw AppError"] }
  ]
}
```

Files live per fix option (`fixOptions[].files`), never as a top-level field — different options may touch different files.

**`issue`** (`kind: issue`, lives in `tech-debt.js`) — the app-code fix parked for `define-task`. Same base shape as a `problem` plus a `places` list, but **no `tier` and no `fixOptions`** (define-task decides the fix and authors the tasks):

```json
{
  "id": "20260716-order-total-rounding",
  "kind": "issue",
  "status": "pending",
  "firstSeen": "2026-07-16",
  "reportedBy": "acceptance-review",
  "title": "order grand total rounds half-down",
  "problem": "order grand total rounds half-down but finance expects half-up",
  "places": ["OrderService.calcGrandTotal", "PriceHelper.round"],
  "occurrences": [
    { "date": "2026-07-16", "by": "acceptance-review", "note": "user flagged wrong totals on .5 amounts in the retrospective" }
  ]
}
```

## References

- cross-ref: `{small,medium,heavy}-learn.js` — search for an existing entry that matches (a `problem` by its `problem` text, a `candidate` by its `title` / pattern) before creating or appending, to avoid duplicates.
- cross-ref: `tech-debt.js` — search for an existing `kind: issue` entry (by its `problem` text) before creating or appending, to avoid duplicates.

## Trigger Skill

- self-improve — only when Auto-improve (above) is `on` for the entry's tier; triggered immediately after writing the entry, passing that entry's `id` and `<tier>-learn.js`.

## Writes To

- `{small,medium,heavy}-learn.js` — create a new entry, or append an occurrence to an existing one, per the tier classified above.
- `tech-debt.js` — create a new `kind: issue` entry, or append an occurrence (+ places) to an existing one.

## Script
`scripts/self-report.py` performs the entry write + dedup mechanics (stdlib only):

```bash
python3 skills/self-learn/self-report/scripts/self-report.py add <file.js> --kind issue --title T --problem P [--places a,b] [--reported-by NAME] [--note TEXT]
python3 skills/self-learn/self-report/scripts/self-report.py list <file.js>
```

`<file.js>` is `tech-debt.js` for `kind: issue`, or the tier file (`{small,medium,heavy}-learn.js`) for `problem` / `candidate`. Dedup matches the skill's rule: same `problem` text appends an `occurrences` entry instead of a new entry. The agent still owns classification (kind, tier, wording) — the script only emits consistently.

## Role & Boundary (Read Before Editing)

This skill is the sole writer of `{small,medium,heavy}-learn.js` **and** `tech-debt.js`. Any skill that notices a self-learn-worthy issue triggers this skill instead of writing the JSON itself — this keeps entry format and tiering consistent no matter who reports. All three kinds — `problem`, `candidate`, `issue` — run through the same dedup + write here.

Its responsibility ends at dedup + tier classification + scoring + writing the entry, plus checking the Auto-improve table to decide whether to hand off to `self-improve` (tiered entries only). It does not choose or execute a fix itself and never writes to `log.js`. A tiered fix is `self-improve`'s (including a candidate's promotion into `code-standards.md`); a `kind: issue` fix is `define-task`'s (it reads the entry, authors the fix tasks, and closes the entry) — self-report neither triggers nor performs it. See the Responsibility map in workflow/SKILL.md.
