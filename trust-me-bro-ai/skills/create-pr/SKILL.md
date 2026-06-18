---
name: create-pr
description: Generate a GitHub PR title and description following the project template (Problems / Solutions / Changes). Outputs copy-paste text only — does not run gh pr create.
---

# create-pr

Generate a PR title and description for the current branch. Output the result as formatted copy-paste text first. If the user then explicitly asks to create the PR, run `gh pr create` and return the URL.

## Base branch

- If the user specifies a base branch (e.g. `/create-pr develop`), use that.
- If no base branch is specified, **ask the user which branch to compare against before doing anything else.** Default suggestion: `master`. Wait for confirmation before proceeding.

## Steps

1. Confirm the base branch (see above).

2. Run these commands in parallel to gather context:
   - `git log <base>...HEAD --oneline` — list commits on this branch vs the base
   - `git diff <base>...HEAD --stat` — changed files overview
   - `git diff <base>...HEAD` — full diff for understanding what changed

2. Analyze the diff to identify:
   - **Problems**: what issue, gap, or requirement drove this work. Be specific and lean — one or two sentences max per point. No filler.
   - **Solutions**: what was built or fixed and how it addresses the problem. Match the level of the problem statement.
   - **Changes**: a tight bullet list of concrete code-level changes (files added/modified/deleted, functions changed, config updated, etc.).

3. Draft a PR **title**: imperative mood, ≤72 chars, no period. E.g. `Add recipient ID to order payload`.

4. Output the title and body as plain text the user can copy-paste directly into GitHub. Use this exact template:

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
```

## Style rules

- **All three sections use bullet points by default** — no prose paragraphs anywhere in the body.
- **Use a table instead of bullets** when the content has clear columns that aid comparison — e.g. multiple DB migrations with their purpose, before/after values, or a list of endpoints with their methods and paths. Only switch to a table when it genuinely improves readability; don't force it.
- **Clear and lean**: every word earns its place. Cut adjectives and throat-clearing phrases ("In order to", "This PR", "We need to").
- Each bullet or table row is one tight fact. Name the file, function, field, or endpoint when it adds clarity.
- Do not add sections beyond the three in the template.
- Do not include a "Test plan" or checklist unless the user asks.
- Do not explain what you did after outputting the PR — just output the block.
