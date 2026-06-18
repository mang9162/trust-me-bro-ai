---
name: self-report
description: Sole writer of `{small,medium,heavy}-learn.js`. Triggered by any other skill that notices a self-learn-worthy issue (recurring pattern, missing reference, naming inconsistency, etc.). Dedupes against existing entries (append occurrence vs. new entry), classifies tier (small/medium/heavy), and writes the entry. small/medium are silent; heavy always warns the user. Per-tier "Auto-improve" setting (edit directly) controls whether self-improve is triggered automatically afterwards.
---

# Self Report

## When to invoke
- Any other skill notices something during its own work that should be remembered for later — a recurring pattern, a missing/incorrect reference, a naming inconsistency, a convention that wasn't followed, etc.
- Triggered as part of that skill's own closing steps. Not normally invoked directly by the user.

## Procedure
1. Receive from the caller: `reportedBy` (the calling skill's name), a short `title`, a `problem` description, and an `occurrence` note (what was seen this time, with today's date).
2. Search existing entries across `small-learn.js`, `medium-learn.js`, and `heavy-learn.js` for an entry whose `problem` matches.
   - **Match found** -> append a new item to that entry's `occurrences[]` (date/by/note). Do not change its `tier` or `fixOptions` just because it recurred — re-tiering is `self-improve`'s call if it ever revisits the entry.
   - **No match** -> create a new entry (1 problem = 1 entry = 1 fix). Generate `id` as `<YYYYMMDD>-<short-slug>`, set `status: "pending"`, `firstSeen` = today, and draft 1+ `fixOptions` (each with `label`, `addresses`, `files`, `steps`) describing concrete ways to resolve it.
3. Classify `tier` (small / medium / heavy) — see Tier definitions below.
4. Write the entry (new or updated) into `<tier>-learn.js`.
5. **small / medium** -> silent. Do not interrupt the caller's flow or mention this to the user.
6. **heavy** -> always warn the user (heavy = process-level impact, they need to know now), regardless of the Auto-improve setting.
7. Check **Auto-improve** (below) for this entry's tier:
   - **on** -> immediately trigger `self-improve` for this entry (pass its `id` and `<tier>-learn.js`).
   - **off** (default) -> do not trigger `self-improve`. If the caller or user wants it fixed now, tell them to invoke `self-improve` themselves.

## Tier definitions
- **small** = fixing it touches a single file, and that file is a "soft component" (`context/`, `tech-stack/`, `{small,medium,heavy}-learn.js`, `log.js`).
- **medium** = (a) fixing it touches 1-2 files of a "hard component" (`initialize`, `self-report/SKILL.md`, `self-improve/SKILL.md`, `feed-back.html`, `workflow` including its Stage-1..6 skills, `generate-report` — edited rarely, invoked/read constantly) without affecting many references, or (b) it touches several soft-component files at once.
- **heavy** = process-level change — requires reworking/fixing references across many files, or changes how a structure works.

## Auto-improve (edit this table directly to change behavior)

| Tier | Auto-trigger self-improve? |
|---|---|
| small | off |
| medium | off |
| heavy | off |

Default `off` for every tier — self-report only writes the entry (and warns for heavy); a human (or the user, via `feed-back.html`) decides when to run `self-improve`. Flip any row to `on` to make self-report immediately trigger `self-improve` for new/updated entries of that tier, right after writing them in step 4.

## Entry schema (`small-learn.js` / `medium-learn.js` / `heavy-learn.js` — `var <TIER>_LEARN = [...]`)
```json
{
  "id": "20260612-gwdir-purpose-missing",
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
`reportedBy` is the skill that first hit the issue. Affected files are NOT a top-level field — each `fixOptions[].files` lists the files THAT option would touch, since different options may affect different files.

## References
- cross-ref: `{small,medium,heavy}-learn.js` — search for an existing entry whose `problem` matches before creating or appending, to avoid duplicates.

## Trigger Skill
- self-improve — only when Auto-improve (above) is `on` for the entry's tier; triggered immediately after writing the entry, passing that entry's `id` and `<tier>-learn.js`.

## Writes To
- `{small,medium,heavy}-learn.js` — create a new entry, or append an occurrence to an existing one, per the tier classified above.

## Role & Boundary (Read Before Editing)

This skill is the sole writer of `{small,medium,heavy}-learn.js`. Any skill that notices a self-learn-worthy issue triggers this skill with the problem description instead of writing the JSON itself — this keeps entry format and tiering consistent no matter who reports.

Its responsibility ends at dedup + tier classification + writing the entry, plus checking the Auto-improve table to decide whether to hand off to `self-improve`. It does not choose or execute a fix itself and never writes to `log.js` — that's `self-improve`'s responsibility (see Responsibility map in workflow/SKILL.md).
