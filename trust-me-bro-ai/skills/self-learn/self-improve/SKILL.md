---
name: self-improve
description: Executes a chosen fix for one self-learn entry — from a feed-back.html copy-prompt, a custom fix typed by the user, or an automatic hand-off from self-report (per-tier Auto-improve setting). Always reviews entries across all three tiers. Confirms understanding before executing if anything is ambiguous, then moves the entry from its tier file into log.js with chosenOption + appliedDate.
---

# Self Improve

## When to invoke
- User pastes a copy-prompt from `feed-back.html`: `self-improve: entry=<id> (<tier>-learn.js), apply fix option <N>`.
- User pastes a custom-fix prompt: `self-improve: entry=<id> (<tier>-learn.js), custom fix: <text>`.
- `self-report` hands off automatically (Auto-improve = `on` for that tier) — gives only the entry `id` and `<tier>-learn.js`, no fix option chosen yet.
- User asks to review/triage pending self-learn entries directly (no specific entry given).

## Procedure
1. Default behavior is to review entries across **all three tiers** (`small-learn.js`, `medium-learn.js`, `heavy-learn.js`) — regardless of whether `self-report` logged silently (small/medium) or warned (heavy).
2. Locate the referenced entry by `id` in its `<tier>-learn.js`.
3. Determine the fix:
   - **Fix option given** (`apply fix option <N>`) -> use `entry.fixOptions[N-1]`.
   - **Custom fix given** (`custom fix: <text>`) -> this becomes a new fix option to append, labeled `"custom"`.
   - **No fix option given** (auto-triggered by self-report, or user asked to triage) -> present `entry.fixOptions` (and the option to write a custom fix) to the user and ask which to apply.
4. **Always confirm understanding before executing** if anything about the chosen fix is ambiguous — whether it came from a numbered option, custom text, or auto-trigger. Do not proceed until the user confirms.
5. Execute the `steps` of the chosen fix option against the files in `fixOptions[].files`.
6. If the fix was custom, append it to the entry's `fixOptions` as `{ "label": "custom", "addresses": ..., "files": [...], "steps": [...] }` before moving the entry.
7. Move the entry from `<tier>-learn.js` to `log.js`:
   - Remove it from `<tier>-learn.js`.
   - Append it to `log.js` with `status: "done"`, `chosenOption` (the applied option's `label`, or `"custom"`), and `appliedDate` = today.

## References
- cross-ref: `{small,medium,heavy}-learn.js` — read the entry being acted on, to execute its fix.

## Writes To
- `log.js` — append the completed entry (with `chosenOption` + `appliedDate`).
- `<tier>-learn.js` — remove the entry once it has been moved to `log.js`.

## Role & Boundary (Read Before Editing)

This skill is the sole writer of `log.js`, and the only skill that executes fixes for self-learn entries. It reviews entries across all three tiers, executes the chosen (or custom, or auto-handed-off) fix, then moves the entry into `log.js` with `chosenOption`/`appliedDate`.

It does not classify new issues or decide which tier an entry belongs to — that's `self-report`'s responsibility (see Responsibility map in workflow/SKILL.md). If the requested fix is ambiguous for any reason, it must confirm understanding with the user before executing anything.
