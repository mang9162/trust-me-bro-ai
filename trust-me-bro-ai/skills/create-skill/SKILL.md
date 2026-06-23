---
name: create-skill
description: The rules and format for creating or editing any skill in this kit — how to declare cross-file connections (## References / ## Trigger Skill / ## Writes To / ## Role & Boundary) and the connection types (cross-ref / bridge / trigger / write). Read before creating or editing a skill. Pairs with file-map.html (in this folder).
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
  `## Writes To` line?** `file-map.html` is a **bridge** with these three
  sections across every skill — every such line must correspond to a
  *connection* edge (cross-ref / bridge / trigger / write) in that diagram,
  and every connection edge must correspond to a line in some skill's
  References / Trigger Skill / Writes To. (The solid numbered execution-flow
  edges are different: they mirror the workflow orchestrator's dispatch
  order, so their counterpart is the explicit Stages / routing **steps** in
  `workflow/SKILL.md`, not a References / Trigger Skill / Writes To line.)
  Read `file-map.html` first, make your change, then add/remove/relabel the
  matching connection edge there so the two never drift apart.

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

## References
- bridge: `file-map.html` — every `## References` / `## Trigger Skill` /
  `## Writes To` line in any skill must correspond to a connection edge in
  this diagram, and every connection edge must correspond to such a line.
  (Execution-flow edges are mirrored by `workflow/SKILL.md`'s Stages /
  routing steps instead — see "Before You Create or Edit a Skill" above.)

## Role & Boundary (Read Before Editing)
This guide issues the rules / format every skill uses to declare its
cross-file connections — the `## References` / `## Trigger Skill` /
`## Writes To` / `## Role & Boundary` sections and the connection-type
vocabulary (cross-ref / bridge / trigger / write). Edit this file only to
change those shared rules. It does NOT track which concrete files connect
(that is `file-map.html`, its bridge pair) or which skill does what.
