---
name: create-pr
description: Generate a GitHub PR title and description following the project template (Problems / Solutions / Changes, then Test Result / Reference artifact tables). Outputs copy-paste text only — does not run gh pr create.
---

# create-pr

Generate a PR title and description for the current branch. Output the result as formatted copy-paste text first. If the user then explicitly asks to create the PR, run `gh pr create` and return the URL.

## Base branch

- If the user specifies a base branch (e.g. `/create-pr develop`), use that.
- If no base branch is specified, **ask the user which branch to compare against before doing anything else.** Default suggestion: the repository's primary branch (`main` or `master`, whichever this repo uses — don't assume a fixed name). Wait for confirmation before proceeding.

## Steps

1. Confirm the base branch (see above).

2. Run these commands in parallel to gather context:
   - `git log <base>...HEAD --oneline` — list commits on this branch vs the base
   - `git diff <base>...HEAD --stat` — changed files overview
   - `git diff <base>...HEAD` — full diff for understanding what changed

3. Analyze the diff to identify:
   - **Problems**: what issue, gap, or requirement drove this work. Be specific and lean — one or two sentences max per point. No filler.
   - **Solutions**: what was built or fixed and how it addresses the problem. Match the level of the problem statement.
   - **Changes**: a tight bullet list of concrete code-level changes (files added/modified/deleted, functions changed, config updated, etc.).

4. Collect the files a reviewer opens alongside the diff, into two buckets:
   - **Test Result** — a file holding a test outcome: the api-test html report, a test-level run output, coverage.
   - **Reference** — a file that explains the work: `scenario.html`, `Datatest.md`, and whatever else is read to follow it.

   Link each file that is committed on this branch — `[<name>](<repo-url>/blob/<branch>/<path>)`, paths from step 2. A file that is not committed (a report the runner produced) keeps its name in the cell with `<!-- attach the file here -->` beside it — GitHub takes uploads only through its own UI, and not `.html`, so tell the user to zip it.

   Every `Result` value comes from the actual run output. Never guess one; unknown → leave the cell empty.

5. Draft a PR **title**: imperative mood, ≤72 chars, no period. E.g. `Add recipient ID to order payload`.

6. Output the title and body as plain text the user can copy-paste directly into GitHub. Use this exact template:

```
Title: <title here>

---

### Problems

- <problem 1>
- <problem 2>

### Solutions

- <solution 1, directly addressing problem 1>
- <solution 2, directly addressing problem 2>

### Changes

- <specific change 1>
- <specific change 2>
- <specific change 3>

### Test Result

| File | Level | Result |
|---|---|---|
| <file 1> | <test level> | <result> |

### Reference

| File | What it is |
|---|---|
| <file 1> | <what it is> |
```

## Style rules

- **Problems / Solutions / Changes use bullet points by default** — no prose paragraphs anywhere in the body. Test Result and Reference are always tables.
- **Use a table instead of bullets** when the content has clear columns that aid comparison — e.g. multiple DB migrations with their purpose, before/after values, or a list of endpoints with their methods and paths. Only switch to a table when it genuinely improves readability; don't force it.
- **Clear and lean**: every word earns its place. Cut adjectives and throat-clearing phrases ("In order to", "This PR", "We need to").
- Each bullet or table row is one tight fact. Name the file, function, field, or endpoint when it adds clarity.
- **Drop an empty artifact section** — no test-result file → no `### Test Result` heading at all; same for `### Reference`. Never emit the heading with an empty table or a placeholder row.
- Do not add sections beyond the five in the template.
- Do not include a "Test plan" or checklist unless the user asks.
- Do not explain what you did after outputting the PR — just output the block.

## Role & Boundary (Read Before Editing)
This skill turns the current branch's diff (against a user-confirmed base
branch) into a PR title and a Problems / Solutions / Changes description,
plus the Test Result / Reference tables pointing at the branch's artifacts,
output as copy-paste text — and runs `gh pr create` only if the user
explicitly asks. It owns that PR-text format and the style rules above. It
does NOT pick the base branch on its own (it always asks and waits) and does
NOT create the PR by default.
