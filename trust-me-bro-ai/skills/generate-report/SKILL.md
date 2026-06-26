---
name: generate-report
description: Regenerate scenario.html inside the scenario folder (under work/). Reads the scenario-meta JSON block from the existing scenario.html, Datatest.md, and all task JSON files. Produces an interactive HTML with a 6-stage progress indicator, a scrollable E2E flow, a Functional Design tree, collapsible Test Data and Tasks sections, expandable task cards, and an Acceptance History log. Re-run after any stage to refresh.
---

# Generate Report

## When to invoke
- After any workflow stage pause, to give the team a human-readable view.
- On demand: "generate report" or "update report".
- Automatically after Stage 3 (create-task).

## Output
`work/Scenario/<FEATURE>/{Success|Alternative}/<NN>-<SCENARIO>/scenario.html` — self-contained, no external dependencies, opens directly in a browser.

## Inputs to read

| Source | What to extract |
|--------|----------------|
| `scenario.html` → `<script id="scenario-meta">` block | `scenario`, `category`, `description`, `steps[]`, `accepted`, `acceptanceHistory[]` |
| `scenario.html` → functional-design section (if present) | preserve as-is; do NOT regenerate — it is authored by `create-task` |
| `01-Testdata/Datatest.md` | All markdown tables → variable name + value + notes |
| `02-Task/01-Setup/*.json` | env-setup tasks |
| `02-Task/02-Backlog/*.json` | unit/integration/component/code tasks |
| `02-Task/03-Api-test/*.json` | api-test tasks |

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

If a stage's files don't exist → `todo`. If files exist but not all done → `active`. If all done → `done`.  
The first `active` or the first stage after the last `done` is the current stage.

## Progress summary counts

Below the stage track, render a `progress-summary` row showing:
- Setup: X / N done
- Backlog: X / N done
- Api Test: X / N done

Count tasks by their `"status"` field. Use a grey dot for pending, amber for in_progress, green for done.

## Step → task linking

- **api-test tasks**: extract NN from the filename prefix (e.g. `03-cfReserveProduct-api-test.json` → step 3). Set `data-step="3"` on the task card.
- **backlog + env-setup tasks**: set `data-step="all"` — they highlight for every step click.
- When a step is activated via JS, also set `target.open = true` so the matching api-test card auto-expands.

## Datatest.md parsing

The file contains multiple `## Section` headings, each followed by one markdown table. Parse every table row:
- Column 1 → variable name (wrap in `<code>`)
- Column 2 → value (wrap in `<code>` if it looks like an id/number, plain text otherwise)
- Column 3 → notes (plain text)

Skip separator rows (`|---|`).

---

## Collapsible sections

- Each task card MUST be a `<details class="task-card" data-step="...">` element — never a plain `<div>`.
- The `<summary>` contains: dot status indicator + `.task-body` (id, title, tags) + `<span class="expand-icon">▾</span>`.
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

```css
details.task-card{border:1.5px solid #e2e8f0;border-radius:8px;margin-bottom:6px;transition:border-color .15s,background .15s,box-shadow .15s;background:#fff}
details.task-card>summary{display:flex;gap:12px;padding:11px 14px;cursor:pointer;list-style:none;align-items:flex-start;user-select:none}
details.task-card>summary::-webkit-details-marker{display:none}
details.task-card>summary::marker{display:none}
details.task-card.highlighted{border-color:#6366f1;background:#f0f4ff;box-shadow:0 0 0 2px rgba(99,102,241,.18)}
details.task-card[open]{border-color:#818cf8}
details.task-card[open]>summary{border-bottom:1px solid #e2e8f0}
.expand-icon{margin-left:auto;font-size:0.72rem;color:#94a3b8;transition:transform .18s;flex-shrink:0;margin-top:5px;line-height:1}
details.task-card[open] .expand-icon{transform:rotate(180deg)}
.task-detail{padding:12px 14px 14px 34px;display:flex;flex-direction:column;gap:10px}
.detail-section{display:flex;flex-direction:column;gap:4px}
.detail-label{font-size:0.65rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.07em}
.detail-pre{background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 10px;font-family:'SFMono-Regular',Consolas,monospace;font-size:0.74rem;color:#334155;white-space:pre-wrap;word-break:break-word;line-height:1.55;margin:0}
.assert-list{list-style:none;display:flex;flex-direction:column;gap:3px;padding:0;margin:0}
.assert-list li{font-family:'SFMono-Regular',Consolas,monospace;font-size:0.74rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:4px;padding:3px 8px;color:#334155}
.dep-tags{display:flex;flex-wrap:wrap;gap:4px}
.dep-tag{background:#f1f5f9;color:#475569;font-size:0.67rem;padding:2px 8px;border-radius:10px;font-family:monospace}
.target-path{font-family:'SFMono-Regular',Consolas,monospace;font-size:0.72rem;color:#6366f1;word-break:break-all;line-height:1.7}
.detail-text{font-size:0.8rem;color:#475569;line-height:1.55}
```

## HTML Template

Save the following as `scenario.html`. Replace every `<!-- FILL: ... -->` comment with real data.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><!-- FILL: scenario name --></title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f1f5f9;color:#1e293b;min-height:100vh}
.container{max-width:980px;margin:0 auto;padding:32px 16px;display:flex;flex-direction:column;gap:16px}
.card{background:#fff;border-radius:12px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,0.07)}

/* Header */
.header{border-left:5px solid #6366f1}
.scenario-name{font-size:1.45rem;font-weight:800;color:#0f172a;margin-bottom:8px}
.category{display:inline-block;padding:3px 12px;border-radius:20px;font-size:0.72rem;font-weight:700;letter-spacing:.05em;margin-bottom:10px}
.cat-success{background:#dcfce7;color:#166534}
.cat-alternative{background:#fef9c3;color:#854d0e}
.desc{color:#475569;font-size:0.88rem;line-height:1.65}

/* Progress */
.section-title{font-size:0.78rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:16px}
.stage-track{display:flex;align-items:flex-start}
.stage-wrap{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;position:relative}
.stage-circle{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:700;position:relative;z-index:1}
.s-done .stage-circle{background:#6366f1;color:#fff}
.s-active .stage-circle{background:#fff;border:2.5px solid #6366f1;color:#6366f1;box-shadow:0 0 0 4px #e0e7ff}
.s-todo .stage-circle{background:#f8fafc;border:2px solid #cbd5e1;color:#94a3b8}
.stage-label{font-size:0.65rem;color:#64748b;text-align:center;max-width:72px;line-height:1.3}
.stage-connector{flex:1;height:2px;margin-top:16px;align-self:flex-start}
.conn-done{background:#6366f1}
.conn-todo{background:#e2e8f0}

/* Flow */
.flow-hint{font-size:0.75rem;color:#94a3b8;margin-bottom:14px}
.flow-scroll{overflow-x:auto;padding-bottom:8px}
.flow-row{display:flex;align-items:flex-start;gap:0;min-width:max-content;padding:4px 2px 12px}
.flow-step{display:flex;flex-direction:column;align-items:center;gap:6px}
.step-num{font-size:0.65rem;font-weight:700;color:#6366f1;background:#e0e7ff;padding:1px 7px;border-radius:10px}
.flow-box{background:#f8fafc;border:2px solid #e2e8f0;border-radius:10px;padding:10px 12px;width:155px;text-align:center;font-size:0.78rem;line-height:1.45;cursor:pointer;transition:border-color .15s,background .15s,transform .15s,box-shadow .15s;color:#334155}
.flow-box:hover{border-color:#818cf8;background:#eef2ff;transform:translateY(-2px);box-shadow:0 4px 12px rgba(99,102,241,.15)}
.flow-box.active{border-color:#6366f1;background:#e0e7ff;box-shadow:0 0 0 3px rgba(99,102,241,.25);color:#1e293b}
.flow-arrow{display:flex;align-items:center;padding:0 6px;margin-top:28px;color:#a5b4fc;font-size:1.1rem;flex-shrink:0}

/* Test Data */
.data-table{width:100%;border-collapse:collapse;font-size:0.82rem}
.data-table th{text-align:left;padding:8px 14px;background:#f8fafc;color:#475569;font-weight:600;border-bottom:2px solid #e2e8f0}
.data-table td{padding:7px 14px;border-bottom:1px solid #f1f5f9;vertical-align:top}
.data-table tr:last-child td{border-bottom:none}
.data-table .section-row td{padding:10px 14px 4px;font-size:0.7rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;background:#f8fafc;border-bottom:1px solid #e2e8f0}
code{background:#f1f5f9;padding:2px 6px;border-radius:5px;font-family:'SFMono-Regular',Consolas,monospace;font-size:0.77rem;color:#0f172a}

/* Functional Design Tree */
.fn-tree{padding:4px 0 8px;display:flex;flex-direction:column;gap:4px}
.fn-tree.drag-over{outline:2px dashed #a5b4fc;outline-offset:4px;border-radius:6px;background:rgba(224,231,255,.2)}
.fn-item{position:relative;display:flex;flex-direction:column;gap:4px}
.fn-item.dragging{opacity:0.35}
.fn-item.drop-before > .fn-node::before{content:'';position:absolute;top:-3px;left:-4px;right:-4px;height:2px;background:#6366f1;border-radius:1px;pointer-events:none}
.fn-item.drop-after > .fn-node::after{content:'';position:absolute;bottom:-3px;left:-4px;right:-4px;height:2px;background:#6366f1;border-radius:1px;pointer-events:none}
.fn-item.drop-inside > .fn-node{background:#e0e7ff !important;outline:2px solid #6366f1}
.fn-node{position:relative;display:inline-flex;align-items:center;gap:6px;padding:6px 10px;background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:8px;font-size:0.82rem;font-weight:500;color:#1e293b;cursor:pointer;transition:border-color .15s,background .15s,box-shadow .15s;user-select:none}
.fn-node:hover{border-color:#818cf8;background:#f0f4ff}
.fn-node.fn-root{background:#eef2ff;border-color:#a5b4fc;font-weight:700}
.fn-node.fn-active{border-color:#6366f1;background:#e0e7ff;box-shadow:0 0 0 3px rgba(99,102,241,.2)}
.fn-children{margin-left:20px;border-left:2px solid #e2e8f0;padding-left:14px;margin-top:4px;display:flex;flex-direction:column;gap:4px;min-height:4px}
.fn-handle{font-size:0.9rem;color:#cbd5e1;cursor:grab;flex-shrink:0;line-height:1}
.fn-handle:hover{color:#94a3b8}
.fn-name{font-family:'SFMono-Regular',Consolas,monospace;font-size:0.78rem}
.fn-delete{margin-left:auto;padding:1px 6px;background:none;border:none;color:#cbd5e1;font-size:0.85rem;line-height:1;cursor:pointer;border-radius:4px;flex-shrink:0;transition:background .1s,color .1s}
.fn-delete:hover{background:#fee2e2;color:#dc2626}
.fn-copy-btn{padding:5px 14px;background:#6366f1;color:#fff;border:none;border-radius:6px;font-size:0.73rem;font-weight:600;cursor:pointer;transition:background .15s}
.fn-copy-btn:hover{background:#4f46e5}

/* Tasks */
.task-group{margin-bottom:20px}
.task-group:last-child{margin-bottom:0}
.group-label{font-size:0.7rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;display:flex;align-items:center;gap:8px}
.group-label::after{content:'';flex:1;height:1px;background:#f1f5f9}
.task-card{display:flex;gap:12px;padding:11px 14px;border:1.5px solid #e2e8f0;border-radius:8px;margin-bottom:6px;transition:border-color .15s,background .15s,box-shadow .15s;background:#fff}
.task-card.highlighted{border-color:#6366f1;background:#f0f4ff;box-shadow:0 0 0 2px rgba(99,102,241,.18)}
.dot{width:8px;height:8px;border-radius:50%;margin-top:6px;flex-shrink:0}
.dot-pending{background:#cbd5e1}
.dot-in_progress{background:#f59e0b}
.dot-done{background:#22c55e}
.task-body{flex:1;min-width:0}
.task-id{font-size:0.67rem;color:#94a3b8;font-family:monospace;margin-bottom:2px}
.task-title{font-size:0.84rem;font-weight:500;color:#1e293b;margin-bottom:6px;line-height:1.4}
.tags{display:flex;flex-wrap:wrap;gap:5px}
.tag{font-size:0.63rem;font-weight:700;padding:1px 7px;border-radius:10px}
.t-unit-test{background:#ede9fe;color:#5b21b6}
.t-integration-test{background:#dbeafe;color:#1e40af}
.t-component-test{background:#fce7f3;color:#9d174d}
.t-code-task{background:#dcfce7;color:#166534}
.t-api-test{background:#ffedd5;color:#9a3412}
.t-env-setup{background:#f1f5f9;color:#475569}
.e-low{background:#dcfce7;color:#166534}
.e-medium{background:#fef9c3;color:#854d0e}
.e-high{background:#fee2e2;color:#991b1b}
.status-badge{background:#f1f5f9;color:#64748b}
.status-done-badge{background:#dcfce7;color:#166534}
.status-progress-badge{background:#fef9c3;color:#854d0e}

.ah-row{display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-top:1px solid #e2e8f0}
.cat-reject{background:#fee2e2;color:#991b1b}
.empty-note{color:#94a3b8;font-size:0.83rem;font-style:italic}
</style>
</head>
<body>
<div class="container">

  <!-- ① NAME + DESCRIPTION — read from <script id="scenario-meta"> block -->
  <div class="card header">
    <div class="scenario-name"><!-- FILL: scenario-meta .scenario --></div>
    <span class="category cat-<!-- FILL: success or alternative (lowercase) -->"><!-- FILL: scenario-meta .category --></span>
    <p class="desc"><!-- FILL: scenario-meta .description --></p>
  </div>

  <!-- ⑥ PROGRESS STAGE -->
  <div class="card">
    <div class="section-title">Progress</div>
    <div class="stage-track">

      <!-- Repeat this block for each of the 6 stages.                         -->
      <!-- Add class s-done / s-active / s-todo to .stage-wrap per detection.  -->
      <!-- Add class conn-done / conn-todo to .stage-connector between stages.  -->

      <div class="stage-wrap s-done">
        <div class="stage-circle">1</div>
        <div class="stage-label">Get Requirement</div>
      </div>
      <div class="stage-connector conn-done"></div>

      <div class="stage-wrap s-done">
        <div class="stage-circle">2</div>
        <div class="stage-label">Create Test Data</div>
      </div>
      <div class="stage-connector conn-done"></div>

      <div class="stage-wrap s-active">
        <div class="stage-circle">3</div>
        <div class="stage-label">Create Task</div>
      </div>
      <div class="stage-connector conn-todo"></div>

      <div class="stage-wrap s-todo">
        <div class="stage-circle">4</div>
        <div class="stage-label">Execute Backlog</div>
      </div>
      <div class="stage-connector conn-todo"></div>

      <div class="stage-wrap s-todo">
        <div class="stage-circle">5</div>
        <div class="stage-label">Api Test</div>
      </div>
      <div class="stage-connector conn-todo"></div>

      <div class="stage-wrap s-todo">
        <div class="stage-circle">6</div>
        <div class="stage-label">Acceptance Review</div>
      </div>

    </div>
  </div>

  <!-- ③ E2E FLOW -->
  <div class="card">
    <div class="section-title" style="margin-bottom:4px">E2E Flow</div>
    <p class="flow-hint">Click a step to highlight related tasks ↓</p>
    <div class="flow-scroll">
      <div class="flow-row">

        <!-- Repeat for each step in scenario-meta .steps[]. N = 1-based index. -->
        <!-- Add flow-arrow div between steps, but NOT after the last step.    -->

        <div class="flow-step">
          <div class="step-num">1</div>
          <div class="flow-box" data-step="1" onclick="activateStep(1)">
            <!-- FILL: steps[0] text -->
          </div>
        </div>

        <div class="flow-arrow">→</div>

        <div class="flow-step">
          <div class="step-num">2</div>
          <div class="flow-box" data-step="2" onclick="activateStep(2)">
            <!-- FILL: steps[1] text -->
          </div>
        </div>

        <!-- ... continue for all steps ... -->

      </div>
    </div>
  </div>

  <!-- ③b FUNCTIONAL DESIGN -->
  <!--
    RULE: authored by create-task (Stage 3), PRESERVED verbatim by generate-report.
    When regenerating, copy the entire .fn-tree div from the previous scenario.html unchanged.
    If Stage < 3 (no tree yet), render the placeholder instead of the fn-tree div.

    Tree anatomy:
    - .fn-tree  → root container
    - .fn-item  → one node at any depth (draggable by JS, delete button added by JS)
      - > .fn-node  → the visible pill: ⠿ handle · fn-name · test-level tag · × delete
      - > .fn-children  → child .fn-item elements (always present, even when empty)

    Each .fn-node has onclick="activateFn(this, ['task-id-1', ...])" wired to backlog task IDs.
    Root nodes additionally carry class fn-root.
    JS (initFnDnD) adds draggable, ×-delete, and before/inside/after drop zones at runtime.
    JS (copyFnTree) copies .fn-tree outerHTML to clipboard so user can paste back to persist.
  -->
  <div class="card">
    <div class="section-title-plain">Functional Design</div>
    <p class="flow-hint" style="margin-bottom:14px">Drag ⠿ to reorder or re-nest · Top/bottom = sibling · Middle = child · Click name to highlight tasks ↓</p>
    <div class="fn-tree">
      <!-- PRESERVE: copy all .fn-item blocks verbatim from previous scenario.html -->
      <!-- Example root item: -->
      <!--
      <div class="fn-item">
        <div class="fn-node fn-root" onclick="activateFn(this,['task-id'])"><span class="fn-handle">⠿</span><span class="fn-name">functionName</span><span class="tag t-component-test">component</span></div>
        <div class="fn-children">
          <div class="fn-item">
            <div class="fn-node" onclick="activateFn(this,['task-id-a','task-id-b'])"><span class="fn-handle">⠿</span><span class="fn-name">childFunction</span><span class="tag t-unit-test">unit</span></div>
            <div class="fn-children"></div>
          </div>
        </div>
      </div>
      -->
      <!-- If Stage < 3: -->
      <!-- <p class="empty-note">Functional design not yet created — will be added during Stage 3 (create-task).</p> -->
    </div>
    <div style="display:flex;align-items:center;gap:10px;margin-top:14px">
      <button class="fn-copy-btn" onclick="copyFnTree()">Copy tree HTML</button>
      <span id="fn-copy-confirm" style="font-size:0.72rem;color:#22c55e;display:none">Copied! Paste to Claude to save.</span>
    </div>
  </div>

  <!-- ④ TEST DATA -->
  <div class="card">
    <div class="section-title" style="margin-bottom:12px">Test Data</div>
    <table class="data-table">
      <thead>
        <tr><th>Variable</th><th>Value</th><th>Notes</th></tr>
      </thead>
      <tbody>

        <!-- For each ## Section in Datatest.md, emit a section-row then data rows. -->

        <tr class="section-row"><td colspan="3"><!-- FILL: section heading --></td></tr>
        <tr>
          <td><code><!-- FILL: variable name --></code></td>
          <td><code><!-- FILL: value --></code></td>
          <td><!-- FILL: notes --></td>
        </tr>

        <!-- Repeat section-row + data rows for every section in Datatest.md -->

      </tbody>
    </table>
  </div>

  <!-- ⑤ TASKS -->
  <div class="card">
    <div class="section-title" style="margin-bottom:16px">Tasks</div>

    <!-- GROUP: Setup (02-Task/01-Setup/) -->
    <div class="task-group">
      <div class="group-label">Setup</div>

      <!-- Repeat for each task in 01-Setup/. Always data-step="all". -->
      <div class="task-card" data-step="all">
        <div class="dot dot-<!-- FILL: pending | in_progress | done -->"></div>
        <div class="task-body">
          <div class="task-id"><!-- FILL: task .id --></div>
          <div class="task-title"><!-- FILL: task .title --></div>
          <div class="tags">
            <span class="tag t-env-setup">env-setup</span>
            <span class="tag e-<!-- FILL: low|medium|high -->"><!-- FILL: effort --></span>
            <span class="tag status-badge"><!-- FILL: status --></span>
          </div>
        </div>
      </div>

    </div>

    <!-- GROUP: Backlog (02-Task/02-Backlog/) -->
    <div class="task-group">
      <div class="group-label">Backlog</div>

      <!-- Repeat for each task in 02-Backlog/. Always data-step="all". -->
      <div class="task-card" data-step="all">
        <div class="dot dot-<!-- FILL: status -->"></div>
        <div class="task-body">
          <div class="task-id"><!-- FILL: task .id --></div>
          <div class="task-title"><!-- FILL: task .title --></div>
          <div class="tags">
            <span class="tag t-<!-- FILL: type e.g. unit-test -->"><!-- FILL: type --></span>
            <span class="tag e-<!-- FILL: effort -->"><!-- FILL: effort --></span>
            <span class="tag status-badge"><!-- FILL: status --></span>
          </div>
        </div>
      </div>

    </div>

    <!-- GROUP: Api Test (02-Task/03-Api-test/) -->
    <div class="task-group">
      <div class="group-label">Api Test</div>

      <!-- Repeat for each task in 03-Api-test/.                                  -->
      <!-- data-step = NN extracted from the filename prefix (e.g. "03-..." → 3). -->
      <div class="task-card" data-step="<!-- FILL: NN as integer -->">
        <div class="dot dot-<!-- FILL: status -->"></div>
        <div class="task-body">
          <div class="task-id"><!-- FILL: task .id --></div>
          <div class="task-title"><!-- FILL: task .title --></div>
          <div class="tags">
            <span class="tag t-api-test">api-test</span>
            <span class="tag e-<!-- FILL: effort -->"><!-- FILL: effort --></span>
            <span class="tag status-badge"><!-- FILL: status --></span>
          </div>
        </div>
      </div>

    </div>

  </div>

  <!-- ⑦ ACCEPTANCE HISTORY — from scenario-meta.acceptanceHistory[] -->
  <div class="card">
    <div class="section-title">Acceptance History</div>

    <!-- If acceptanceHistory[] is empty → render ONLY this note (nothing below). -->
    <p class="empty-note">No acceptance rounds yet — Stage 6 not reached.</p>

    <!-- Otherwise drop the note and repeat one .ah-row per entry, oldest → newest. -->
    <!-- badge: result "accepted" → class cat-success ; "rejected" → class cat-reject -->
    <div class="ah-row">
      <span class="category cat-<!-- FILL: success | reject -->" style="flex-shrink:0;margin-bottom:0">Round <!-- FILL: round --> · <!-- FILL: accepted | rejected --></span>
      <p class="desc" style="margin:0"><!-- FILL: feedback --></p>
    </div>

  </div>

</div><!-- /container -->

<script id="scenario-meta" type="application/json">
{
  "scenario": "<!-- FILL: scenario name -->",
  "category": "<!-- FILL: Success | Alternative -->",
  "description": "<!-- FILL: one-line summary -->",
  "steps": ["<!-- FILL: step 1 -->", "<!-- FILL: step 2 -->"],
  "accepted": <!-- FILL: true once an accepted round exists, else false -->,
  "acceptanceHistory": [<!-- FILL: { "round": N, "result": "accepted | rejected", "feedback": "..." } per round, oldest → newest; [] if none -->]
}
</script>
<script>
var _dragged = null, _dropTarget = null, _dropPos = null;
function _isAnc(anc, el) { var c = el; while(c){ if(c===anc) return true; c=c.parentElement; } return false; }
function _clearDrop() {
  document.querySelectorAll('.fn-item').forEach(function(i){ i.classList.remove('drop-before','drop-inside','drop-after'); });
  var t = document.querySelector('.fn-tree'); if(t) t.classList.remove('drag-over');
}
function _getPos(e, nodeEl) {
  var r = nodeEl.getBoundingClientRect(), y = e.clientY - r.top, h = r.height;
  return y < h*0.3 ? 'before' : y > h*0.7 ? 'after' : 'inside';
}
function initFnDnD() {
  var tree = document.querySelector('.fn-tree');
  if (!tree) return;
  function setupItem(item) {
    item.setAttribute('draggable','true');
    item.addEventListener('dragstart', function(e){
      e.stopPropagation(); _dragged = item;
      e.dataTransfer.effectAllowed = 'move';
      setTimeout(function(){ item.classList.add('dragging'); }, 0);
    });
    item.addEventListener('dragend', function(){
      item.classList.remove('dragging');
      _clearDrop(); _dragged = _dropTarget = _dropPos = null;
    });
    var node = item.querySelector(':scope > .fn-node');
    if (!node) return;
    if (!node.querySelector('.fn-delete')) {
      var del = document.createElement('button');
      del.className = 'fn-delete'; del.textContent = '×'; del.title = 'Remove from tree';
      del.onclick = function(e){ e.stopPropagation(); item.remove(); };
      node.appendChild(del);
    }
    node.addEventListener('dragover', function(e){
      if (!_dragged || _dragged===item || _isAnc(_dragged,item)) return;
      e.preventDefault(); e.stopPropagation();
      _clearDrop(); _dropTarget = item;
      _dropPos = _getPos(e, node);
      item.classList.add('drop-'+_dropPos);
    });
    node.addEventListener('dragleave', function(e){
      if (!node.contains(e.relatedTarget)) item.classList.remove('drop-before','drop-inside','drop-after');
    });
    node.addEventListener('drop', function(e){
      e.preventDefault(); e.stopPropagation(); _clearDrop();
      if (!_dragged || _dragged===item || _isAnc(_dragged,item)) return;
      var pos = _getPos(e, node), parent = item.parentElement;
      if (pos==='before') parent.insertBefore(_dragged, item);
      else if (pos==='after') parent.insertBefore(_dragged, item.nextElementSibling);
      else { var ch = item.querySelector(':scope > .fn-children'); if(ch) ch.appendChild(_dragged); }
    });
  }
  tree.addEventListener('dragover', function(e){
    if (!_dragged || e.target !== tree) return;
    e.preventDefault(); _clearDrop(); tree.classList.add('drag-over');
  });
  tree.addEventListener('drop', function(e){
    if (e.target !== tree) return;
    e.preventDefault(); _clearDrop(); if(_dragged) tree.appendChild(_dragged);
  });
  document.querySelectorAll('.fn-item').forEach(setupItem);
}
function copyFnTree() {
  var tree = document.querySelector('.fn-tree');
  if (!tree) return;
  navigator.clipboard.writeText(tree.outerHTML).then(function() {
    var el = document.getElementById('fn-copy-confirm');
    if (el) { el.style.display='inline'; setTimeout(function(){ el.style.display='none'; }, 2500); }
  });
}
initFnDnD();
function activateFn(el, taskIds) {
  var isAlreadyActive = el.classList.contains('fn-active');
  document.querySelectorAll('.fn-node').forEach(function(n){ n.classList.remove('fn-active'); });
  document.querySelectorAll('details.task-card').forEach(function(c){ c.classList.remove('highlighted'); });
  if (isAlreadyActive) return;
  el.classList.add('fn-active');
  taskIds.forEach(function(id) {
    document.querySelectorAll('.task-id').forEach(function(tid) {
      if (tid.textContent.trim() === id) {
        var card = tid.closest('details.task-card');
        if (card) { card.classList.add('highlighted'); card.open = true; }
      }
    });
  });
  var first = document.querySelector('details.task-card.highlighted');
  if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
}
function activateStep(n) {
  var box = document.querySelector('.flow-box[data-step="' + n + '"]');
  var isAlreadyActive = box && box.classList.contains('active');
  document.querySelectorAll('.flow-box').forEach(function(b){ b.classList.remove('active'); });
  document.querySelectorAll('details.task-card').forEach(function(c){ c.classList.remove('highlighted'); });
  if (isAlreadyActive) return;
  if (box) box.classList.add('active');
  document.querySelectorAll('details.task-card').forEach(function(card){
    var s = card.dataset.step;
    if (s === 'all' || s === String(n)) card.classList.add('highlighted');
  });
  var target = document.querySelector('details.task-card[data-step="' + n + '"]');
  if (target) { target.open = true; target.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
}
</script>
</body>
</html>
```

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
