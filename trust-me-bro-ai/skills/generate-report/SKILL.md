---
name: generate-report
description: Regenerate scenario.html inside the scenario folder (under work/) or aggregate cross-service feature scenarios into a unified feature dashboard HTML. Reads the scenario-meta JSON block, Datatest.md, and all task JSON files. Produces an interactive HTML with a 6-stage progress indicator, a scrollable E2E flow, a Functional Design tree, collapsible Test Data and Tasks sections, expandable task cards, and an Acceptance History log. Re-run after any stage to refresh.
---

# Generate Report

## When to invoke
Triggered to (re)render `scenario.html` for a scenario folder — it acts on whatever the folder currently holds, no matter which skill triggered it:
- after a stage has updated the scenario folder, to refresh the human-readable view.
- on demand: "generate report" / "update report".

## Output
`scenario.html` inside the scenario folder (path owned by the workflow `## Layout` — see `## References`) — self-contained, no external dependencies, opens directly in a browser.

## Script
`scripts/generate-report.py` renders single-scenario `scenario.html` files, and `scripts/generate-feature-dashboard.py` aggregates cross-service feature scenarios into a unified multi-tab dashboard (stdlib only, idempotent, structural self-check):

```bash
# Single scenario or all scenarios in repo
python3 skills/generate-report/scripts/generate-report.py <scenario-folder> [...]
python3 skills/generate-report/scripts/generate-report.py --all work/

# Cross-service feature dashboard (static generation)
python3 skills/generate-report/scripts/generate-feature-dashboard.py --feature BIZ_AI

# Cross-service live development with auto-reload (zero-dependencies)
python3 skills/generate-report/scripts/generate-feature-dashboard.py --feature BIZ_AI --serve 8080
python3 skills/generate-report/scripts/generate-feature-dashboard.py --feature BIZ_AI --watch
```

Run `generate-report.py` after any stage instead of hand-rendering: it reads `scenario-meta`, `Datatest.md`, and the task JSONs, detects stage progress from what exists, preserves the Functional Design tree verbatim, and exits non-zero on structural errors.

## Inputs to read
Read the scenario folder per the workflow `## Layout` — it owns the folder structure and file paths (see `## References`). From the files it defines, extract:

| Source | What to extract |
|--------|----------------|
| `scenario.html` → `<script id="scenario-meta">` block | `scenario`, `category`, `description`, `steps[]`, `accepted`, `acceptanceHistory[]`, `sync` (written by sync-task: `{ id, ref, url, itemId, board? }`), `syncTarget` (which `sync-task-*` board, written by get-requirement). **Preserve the tool-written `sync` / `syncTarget` verbatim when re-emitting the block** — never drop them. |
| `scenario.html` → functional-design section (if present) | preserve as-is; do NOT regenerate — it is authored by `create-task` |
| Test-data table file (`Datatest.md`) | all markdown tables → variable name + value + notes |
| Task files (Setup / Backlog / Api-test groups) | each task **by its own `type` field** — render its tag/group from the task data, whatever the type (incl. project-custom ones) |

If a source file does not exist yet, skip that section and add a grey "not yet created" placeholder.

## Stage progress detection

Determine each stage's status by checking what exists:

| Stage | Label | Done when |
|-------|-------|-----------|
| 1 | Get Requirement | `scenario.html` exists (has `<script id="scenario-meta">` block) |
| 2 | Create Test Data | `01-Testdata/Datatest.md` exists |
| 3 | Create Task | `02-Task/` has at least one `.json` file |
| 4 | Execute Backlog | all `02-Backlog/*.json` have `"status": "done"` |
| 5 | Api Test | all `03-Api-test/*.json` have `"status": "done"` |
| 6 | Acceptance Review | `scenario-meta.accepted === true` |

If a stage's files don't exist → `todo`. If files exist but not all done → `active` (a `failed` task counts as not done, so the stage stays `active`). If all done → `done`.  
The first `active` or the first stage after the last `done` is the current stage.

## Progress summary counts

Below the stage track, render a `progress-summary` row showing:
- Setup: X / N done
- Backlog: X / N done
- Api Test: X / N done

Count tasks by their `"status"` field. Colour each task's dot by status — grey `pending`, amber `in_progress`, green `done`, red `failed`; any unrecognized status falls back to grey. Don't hardcode the status set — read whatever the task JSON declares.

## Step → task linking

- **api-test tasks**: extract NN from the filename prefix (e.g. `03-cfReserveProduct-api-test.json` → step 3). Set `data-step="3"` on the task card.
- **backlog + env-setup tasks**: set `data-step="all"` — they highlight for every step click.
- When a step is activated via JS, also set `target.open = true` so the matching api-test card auto-expands.

## Datatest.md parsing

The file contains multiple `## Section` headings, each followed by one markdown table. The columns are owned by `create-test-data` (currently `name | value | expect | status | notes`) and may change — do NOT assume a fixed set. For each table:
- Read its header row and emit one column per header, in the same order.
- Wrap a cell that looks like an id/number in `<code>`; leave plain text otherwise.
- Skip separator rows (`|---|`).

---

## Collapsible sections

- Each task card MUST be a `<details class="task-card" data-step="...">` element — never a plain `<div>`.
- The `<summary>` contains: dot status indicator + `.task-body` (id, title, tags) + `<span class="expand-icon">▾</span>`.
- If the task has a `sync` field (written by sync-task), append `<a class="tag sync-tag" href="{sync.url}" target="_blank">↗ #{sync.id}</a>` as the last chip inside `.tags` — the link to its synced issue.
- `<summary>` must have `list-style:none` and `::-webkit-details-marker{display:none}` to suppress the browser default triangle.
- The `<div class="task-detail">` after `</summary>` shows full task detail when expanded. Include only fields that are present in the task JSON:
  - `pseudocode` → `<pre class="detail-pre">` (newline-joined array)
  - `context` → `.detail-text`
  - `asserts` → `<ul class="assert-list"><li>` per item
  - `test_path` → `.detail-text`
  - `acceptance` → `.detail-text`
  - `notes` → `.detail-text`
  - `depends_on` → `.dep-tags` with one `.dep-tag` span per id
  - `targets` / `uses.stubs` → `.target-path` per path
- The `expand-icon` rotates 180° when `details[open]` via CSS `transition:transform`.

### Task card HTML skeleton

```html
<details class="task-card" data-step="all">
  <summary>
    <div class="dot dot-pending"></div>
    <div class="task-body">
      <div class="task-id">00-env-setup</div>
      <div class="task-title">...</div>
      <div class="tags">
        <span class="tag t-env-setup">env-setup</span>
        <span class="tag e-low">low</span>
        <span class="tag status-badge">pending</span>
        <!-- only if the task has a `sync` field: --><a class="tag sync-tag" href="{sync.url}" target="_blank">↗ #{sync.id}</a>
      </div>
    </div>
    <span class="expand-icon">▾</span>
  </summary>
  <div class="task-detail">
    <div class="detail-section">
      <div class="detail-label">Pseudocode</div>
      <pre class="detail-pre">step 1: ...
step 2: ...</pre>
    </div>
    <div class="detail-section">
      <div class="detail-label">Asserts</div>
      <ul class="assert-list">
        <li>res.status: eq 200</li>
      </ul>
    </div>
    <div class="detail-section">
      <div class="detail-label">Depends on</div>
      <div class="dep-tags">
        <span class="dep-tag">00-env-setup</span>
      </div>
    </div>
    <div class="detail-section">
      <div class="detail-label">Target</div>
      <div class="target-path">path/to/file.ts</div>
    </div>
    <div class="detail-section">
      <div class="detail-label">Notes</div>
      <div class="detail-text">...</div>
    </div>
  </div>
</details>
```

### Required CSS additions for collapsible cards

Defined once in `assets/scenario-report.css` (`.task-card`, `.expand-icon`, `.task-detail`, `.detail-*`, `.dep-tag`, `.target-path`, `.sync-tag` rules) — the generator inlines them at build time. Do NOT copy CSS rules into this doc; edit the asset instead.

## HTML Template

The full template, stylesheet, and client-side JS are implemented by the generator scripts and their assets — do NOT hand-copy the CSS/JS here:

| Asset | Path | Contents |
|---|---|---|
| Scenario stylesheet | `assets/scenario-report.css` | All CSS for `scenario.html` (collapsible cards, stage track, fn-tree) |
| Scenario JS | `assets/scenario-report.js` | Drag-drop fn-tree, `activateStep` / `activateFn` |
| Dashboard stylesheet | `assets/feature-dashboard.css` | All CSS for the cross-service feature dashboard |
| Dashboard JS | `assets/feature-dashboard.js` | Tab switching, scenario nav, search, live-reload client |

`generate-report.py` and `generate-feature-dashboard.py` read these assets at build time and inline them into the generated HTML — a single edit in the asset file regenerates every report consistently, and the output stays self-contained.

### Structural skeleton (what the generated HTML contains)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title><!-- scenario name --></title>
  <style>/* inlined from assets/scenario-report.css */</style>
</head>
<body>
  <div class="container">
    <div class="card header">   <!-- ① scenario name + category + description (from scenario-meta) -->
    <div class="card">          <!-- ⑥ 6-stage progress track -->
    <div class="card">          <!-- E2E flow boxes, click → activateStep highlights matching task cards -->
    <div class="card">          <!-- Functional Design fn-tree (preserved verbatim from prior render) -->
    <div class="card">          <!-- Test Data tables parsed from Datatest.md -->
    <div class="card">          <!-- Tasks: Setup / Backlog / Api-test collapsible cards -->
    <div class="card">          <!-- Acceptance History log from scenario-meta.acceptanceHistory -->
  </div>
  <script id="scenario-meta" type="application/json">{...}</script>  <!-- owned by get-requirement / acceptance-review -->
  <script>/* inlined from assets/scenario-report.js */</script>
</body>
</html>
```

The generator fills every `<!-- FILL: ... -->` slot automatically — see the `## Fill-in checklist` below for what it verifies.

---

## Fill-in checklist

Before saving `scenario.html`, verify:

- [ ] `<title>` = scenario name
- [ ] `.scenario-name` text filled
- [ ] `.category` class suffix is `success` or `alternative` (lowercase)
- [ ] `.desc` filled
- [ ] `<script id="scenario-meta">` block filled with correct JSON
- [ ] All 6 stage circles have correct `s-done / s-active / s-todo` class (Stage 6 = `done` when `scenario-meta.accepted === true`)
- [ ] All connectors have `conn-done / conn-todo` class
- [ ] Acceptance History: one `.ah-row` per `acceptanceHistory[]` entry (badge `cat-success` if accepted / `cat-reject` if rejected), or `empty-note` if none
- [ ] One `.flow-box` per step with correct `data-step` and text
- [ ] No `flow-arrow` after the last step
- [ ] Functional Design section: `.fn-item` blocks copied verbatim from previous HTML (JS adds `draggable`, `×` delete, and drop-zone listeners at runtime); placeholder `<p class="empty-note">` if Stage < 3; each `.fn-node` has `onclick="activateFn(this,[...])"`, a `⠿` handle span, fn-name span, optional test-level tag; root nodes have class `fn-root`; every `.fn-item` has a sibling `.fn-children` div (even when empty)
- [ ] All Datatest.md sections appear as `section-row` + data rows
- [ ] All tasks appear in correct group with correct `data-step`, status dot class, type tag class, effort class
- [ ] File saved as `scenario.html` in the scenario folder (no `case.json` needed)

## Notes
- Generate one `scenario.html` per scenario folder — do NOT share across scenarios.
- If `02-Task/` does not exist yet, render the Tasks section with `<p class="empty-note">Tasks not yet created.</p>`.
- If `01-Testdata/Datatest.md` does not exist, render Test Data section with `<p class="empty-note">Test data not yet created.</p>`.
- After generating, print the file path so the user can open it.

## References
- bridge: `trust-me-bro-ai/skills/workflow/SKILL.md` (`## Layout`) — owns the scenario folder structure and every path this skill reads from and writes `scenario.html` to; the output path and input file locations must match it exactly.

## Writes To
- `scenario.html` — the rendered report for this scenario (its main output).

## Role & Boundary (Read Before Editing)
generate-report owns rendering the per-scenario `scenario.html` from the data already in the scenario folder. It only READS those sources and re-renders the HTML — it never authors or changes their content: the `scenario-meta` block is owned by `get-requirement` / `acceptance-review`, the Functional Design tree by `create-task` (copied verbatim here), task `status` by `execute-tdd` / `api-test`, and test-data values by `create-test-data`. It does not decide where files live (workflow `## Layout`). Being generic, it renders whatever the folder holds regardless of which skill triggered it. For anything outside this boundary, see the Responsibility map in `workflow/SKILL.md`.