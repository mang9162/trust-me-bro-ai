---
name: create-skill
description: The rules and format for creating or editing any skill in this kit — how to write the body (lean, ordered, condition-driven) and declare cross-file connections (## References / ## Trigger Skill / ## Writes To / ## Role & Boundary). Read before creating or editing a skill. Pairs with file-map.html (in this folder).
---

# Skill Format Guide

## Purpose
Skill files must not duplicate content owned by another skill or context
file — each piece of reusable content (template, JSON shape, naming
convention, etc.) is defined in exactly ONE place, by its owner. Every other
skill that needs it points to that one place instead of copying it in.

This guide defines the format every skill uses to declare those pointers, so
that:
- nothing is duplicated (avoids drift between copies)
- the *kind* of connection is explicit — a reader (human or agent) knows
  immediately whether to just read a file, validate a key against it, hand
  off to another skill, or expect this skill to write into it.

## Before You Create or Edit a Skill
- **Creating a new skill?** Write its `## Role & Boundary (Read Before
  Editing)` section — every skill declares its own scope, even if
  References / Trigger Skill / Writes To are still empty.
- **Editing an existing skill?** Read its `## Role & Boundary (Read
  Before Editing)` FIRST. If your change doesn't fit that boundary, ALWAYS
  propose updating `## Role & Boundary (Read Before Editing)` itself
  first — to record the new scope decision — before redirecting the change
  elsewhere. Then check the Responsibility map (workflow/SKILL.md) for where
  the change actually belongs.
- **Adding, removing, or changing a `## References` / `## Trigger Skill` /
  `## Writes To` line?** Read `file-map.html` first (its bridge pair), make
  your change, and sync the connection edges immediately so the two never drift.

## Skill File Structure
A skill file's body ends with these sections, in this order (omit any that
are empty):
1. procedure / body content
2. ## References
3. ## Trigger Skill
4. ## Writes To
5. ## Role & Boundary (Read Before Editing)

Position exception: a skill whose entire purpose IS this boundary (e.g. a
control-only orchestrator) opens with `## Role & Boundary (Read Before
Editing)` as its FIRST section instead — same name, only the position
changes.

## Writing the Skill

Keep the body lean and scannable — an agent reads it to act, not to study.
The **Common** rules apply to every skill; then add the **Generic** or
**Specific** rules depending on which kind you're writing.

### Common — every skill
- **Description routes, doesn't sell** — the frontmatter `description` is the
  one line an agent reads to *pick* the skill; say what it IS, not its use
  cases. Push "when" and "how" into the steps.
- **Lean prose** — short, direct sentences; don't restate what a nearby
  table, JSON example, or step already says.
- **Ordered steps, no jumping** — one action per step, in run order; don't
  fold several decisions into one sentence or hop back and forth.
- **Table once it's dense** — when fields / cases / options pile up, switch
  from prose to a table; easier to scan than a paragraph.
- **Conditions sit in their step** — state a condition where it's handled,
  not up front; the reader meets it exactly when it's relevant.
- **Explicit boundaries** — say clearly what the skill IS responsible for,
  in `## Role & Boundary`; if the list grows, break it into separate bullets.
- **Deterministic fallbacks** — every skill *that runs work* defines a path
  for when it fails (halt and ask, a `failed` status, a stop condition);
  never leave failure undefined. A pure reference / format guide (no run
  path) is exempt.

### Generic — a skill many callers share (e.g. self-report, generate-report)
- **Bind to data, not callers** — never name one caller or use case. Key the
  skill on a *condition of the data* it receives (e.g. `kind: candidate`) so
  it reads the same no matter who calls it.

### Specific — a skill that owns one role / stage (e.g. a Stage-N skill)
- **Name its place** — it has one real role, so the `description` states
  which stage / step it is and what it follows or hands off to.
- **Boundary spells the "does NOT"** — `## Role & Boundary` lists what it
  owns *and* what belongs to neighbouring skills, then points to the
  Responsibility map — to stop scope from creeping into another skill.

## Connection Types
- cross-ref — one-way read. Open the target file to use info from it
  (naming conventions, value lists, etc.). No key has to match.
- bridge — read + validate. A key/value in THIS skill's output must match an
  entry in the target file exactly (e.g. a `ref` column). Breaks if either
  side changes without the other.
- trigger — hand-off. Tell another skill to run when done — that skill owns
  its own logic/content; this is NOT a file reference, don't duplicate it
  under References.
- write — this skill writes/updates the target file directly, as part of
  its own procedure (not its main task output).

## Section Formats

### `## References`
One line per file this skill reads (cross-ref / bridge):
- <type>: <file> — <what it's for / which key bridges>

### `## Trigger Skill`
One line per skill this skill hands off to when done:
- <skill> — <what it should do>

### `## Writes To`
One line per file this skill writes/updates directly:
- <file> — <what gets written>

### `## Role & Boundary (Read Before Editing)`
Short positive statement of what this skill IS responsible for, so a future
editor can check "does my change belong here?". Close with a pointer to the
Responsibility map (workflow/SKILL.md) for anything outside this boundary.

Normally the last section. A control-only orchestrator (whose entire content
IS its boundary) may instead open with this section as the first one in the
file — position only, name doesn't change.

## Checklist — Classifying a New Connection
1. Need to open another file for info?
   - no key to validate -> cross-ref
   - a key/value here must match there -> bridge
2. Need another skill to run after this one finishes? -> trigger
3. Does this skill write into another file as part of its own work? -> write

## After You Create or Edit a Skill
Run these in order once the body is written. Each step surfaces what it finds
and lets the user decide — apply only what they choose, and never fix the
skill or its test on your own.

1. **Self-review** — check the skill matches its stated topic and follows
   `## Writing the Skill`. Present the gaps as a table (cause / before /
   after); the user picks which to fix and which to let pass.
2. **Cover the change** — confirm the case you just added or changed has a
   scenario under `skill-evaluation/<skill>/`. If not, propose one drawn from
   this change — the user writes it or asks for a vibe-test — so the run below
   includes it.
3. **Run and report** — run that skill's scenarios with this session as both
   actor and judge. Report the results as a table (eval item / expected /
   actual / pass-fail), then list any failures with their reasons below it.
   All green: done. Any red: the user decides what to change.

## References
- bridge: `file-map.html` — every `## References` / `## Trigger Skill` /
  `## Writes To` line in any skill must correspond to a connection edge in
  this diagram, and every connection edge must correspond to such a line.
  (Execution-flow edges are different — they're mirrored by
  `workflow/SKILL.md`'s Stages / routing steps instead.)

## Role & Boundary (Read Before Editing)
This guide issues the rules / format every skill uses — how to write its
body (lean, ordered, condition-driven), how to declare its cross-file
connections (the `## References` / `## Trigger Skill` / `## Writes To` /
`## Role & Boundary` sections and the connection-type vocabulary), and how to
verify a skill after editing (the `## After You Create or Edit a Skill`
checklist, including running that skill's own eval scenarios under
`skill-evaluation/<skill>/`). Edit this file only to change those shared
rules. It does NOT track which concrete files connect (that is
`file-map.html`, its bridge pair) or which skill does what. The eval here
tests the *skill* itself — whether the produced project's code needs tests is
a separate concern owned by `testing-guide.md` / `tech-stack.md`, not this
guide.
