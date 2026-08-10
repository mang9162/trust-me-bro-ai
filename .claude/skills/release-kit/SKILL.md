---
name: release-kit
description: Cut a new version of this repo's kit — pick the version with the user, bump the version marker, tag it, and publish the GitHub release. Runs on master in this repo only, after the release's PRs are merged.
---

# Release Kit

## Purpose

Publish a new version of the `trust-me-bro-ai/` kit so an installed copy can
tell what it is running and step up to it. A release is three things that must
agree: the version marker inside the kit, the tag, and the GitHub release.

## Procedure

### 1. Preflight

On `master`, working tree clean, in sync with `origin`, and `gh auth status`
logged in. Any of these off → say which and stop; do not release from a dirty
or behind tree.

### 2. Read what the release contains

```
gh release list --limit 1
git log v<latest>..master --oneline
```

No commits since the latest tag → say the kit is already released and stop.

### 3. Propose the version, the user picks

Read the merged PR bodies in that range for what actually changed, then
propose one bump with the reason:

| bump | when |
|---|---|
| patch | a fix inside behaviour that already shipped |
| minor | a new skill, a new capability, a new field others can use |
| major | a change that breaks an installed kit — a moved/removed file, a renamed key |

State the proposal and wait for the user's number.

### 4. Bump the marker, then commit

In `trust-me-bro-ai/.kit-version.json` set `version` to the new number and
`updatedAt` to today. Leave `history` as it is — `update-kit` appends to it in
the consumer's repo, not here. Commit that on `master` and push.

This lands before the tag, never after: the marker ships **inside** the kit, so
a consumer installing a tag inherits whatever that tag's tree says.

### 5. Tag the bump commit

Tag `v<version>` at the commit from step 4 and push the tag. Confirm with
`git show v<version>:trust-me-bro-ai/.kit-version.json` that the marker inside
the tag reads the same number — they must match, and this is the only step
that proves it.

### 6. Publish the release

Title `Release <version>`, on the tag from step 5, with notes in exactly these
two sections drawn from the merged PRs:

```
### Problems

- <what was wrong or missing, one fact per bullet>

### Solutions

- <what now holds, answering the problem above it>
```

No other sections, no bullet without a problem it answers.

### 7. Report

Give the user the release URL, the version, and the tag's commit.

## When a step fails

Stop at that step and report what is published so far — a release is not
atomic, and half of one is worse unannounced. A tag already pushed with the
wrong marker inside is the one case with two ways out (move the tag, or cut the
next patch on top); state both and let the user pick.

## References

- cross-ref (no file-map edge): `trust-me-bro-ai/.kit-version.json` — the
  version this kit currently declares (step 2), and the field this skill
  bumps (step 4).

## Writes To

- (no file-map edge) `trust-me-bro-ai/.kit-version.json` — `version` and
  `updatedAt` set to the released version (step 4).

## Role & Boundary (Read Before Editing)

This skill owns cutting a version of this repo's kit: choosing the number with
the user, bumping the version marker inside the commit that gets tagged,
tagging it, and publishing the release with its Problems / Solutions notes. It
lives outside `trust-me-bro-ai/` because only this repo releases the kit — a
repo that installed the kit never runs it.

It does NOT:

- update an installed kit to a newer version — that is `update-kit`, which
  reads the marker this skill writes.
- merge PRs or write their descriptions — that is `create-pr`; this skill runs
  after the merges and only reads what they said.
- edit any skill in the kit — that is `create-skill`; a release publishes what
  is already on `master`.
