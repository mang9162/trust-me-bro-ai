---
name: update-kit
description: Update this installed kit from its upstream repo one version at a time — show what each version fixed and added, let the user pick how far to go, and ask before overwriting anything edited locally.
---

# update-kit

Bring the `trust-me-bro-ai/` folder in this repo up to a newer upstream version. Each step moves exactly **one** version, so a change set stays small enough to read and accept. The engine is `scripts/update-kit.sh`; this skill drives the choosing and the conflict calls.

## Procedure

### 1. Preflight

`gh` is logged in (`gh auth status`) with read access to the source repo, and `jq` is on PATH. The kit must carry `.kit-version.json` — no file means it was copied in before versioning existed; ask the user which version it came from and write the file before going on.

### 2. Show the gap

```sh
./scripts/update-kit.sh status
```

Prints the installed version and every newer version in the order they must be applied. Already up to date → say so and stop.

### 3. Let the user choose how far to go

Run `notes <tag>` for each newer version and show them together — one block per version, in order, so the user reads what each one fixes and adds before choosing:

```sh
./scripts/update-kit.sh notes v1.2.3
```

The user picks a target version. It can be any of them, not only the newest — a version whose changes they don't want yet is a reason to stop below it.

### 4. Step to the next version

One version per pass, lowest first, even when the target is further up. Preview it before touching anything:

```sh
./scripts/update-kit.sh plan v1.2.3
```

Each line is a status and a path:

| status | meaning |
|---|---|
| `ADD` | new file upstream |
| `UPDATE` | changed upstream, untouched here — safe to take |
| `REMOVE` | dropped upstream, untouched here |
| `CONFLICT` | changed upstream **and** edited here |
| `CONFLICT-DELETE` | dropped upstream but edited here |

Files that exist only in this repo — the `context/` and `tech-stack/` knowledge, generated `sync-task-*` skills, `self-learn` entries — appear in no tree and are never touched.

Show the counts, list the conflicts by name, and get the user's go-ahead for this version.

### 5. Apply and resolve

```sh
./scripts/update-kit.sh apply v1.2.3
```

Clean changes are written. Each conflict leaves the local file untouched and drops the incoming one beside it as `<path>.incoming`. For every conflict, show the user the difference and let them decide — keep the local file, take the incoming one, or merge the two by hand. Delete the `.incoming` file once it's settled. Never resolve one for them.

### 6. Record the version

```sh
./scripts/update-kit.sh finish v1.2.3
```

Refuses while any `.incoming` remains. Otherwise it sets the new version in `.kit-version.json` and appends the step to `history`.

### 7. Continue or stop

Not at the chosen target yet → back to step 4 for the next version. At the target: if any skill folder was added or removed, hand off to `skill-sync` to regenerate the index, then tell the user which versions were applied and what is left unresolved (nothing, if step 6 passed).

## Trigger Skill
- `skill-sync` — regenerate the skills index after a step that added or removed a skill.

## Role & Boundary (Read Before Editing)
This skill updates the installed kit against its upstream source: reading `.kit-version.json`, listing the versions in between, presenting what each one changed, stepping one version at a time, and putting every locally-edited file in front of the user before it is overwritten. It does NOT author or edit skills (`create-skill`), regenerate the skills index (`skill-sync`), or fill the knowledge files (`initialize`) — and it never resolves a conflict on the user's behalf. For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.
