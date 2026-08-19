#!/usr/bin/env python3
"""generate-report.py — renders scenario.html for one or more scenario folders.

Implements the generate-report SKILL.md rules:
- reads scenario.html's <script id="scenario-meta"> block (preserves sync/syncTarget verbatim)
- reads 01-Testdata/Datatest.md tables, 02-Task/**/*.json task files
- detects stage progress from what exists (see SKILL.md stage table)
- preserves the Functional Design tree verbatim from the previous scenario.html
- writes scenario.html (self-contained, no external deps)

Usage:
  python3 generate-report.py <scenario-folder> [<scenario-folder> ...]
  python3 generate-report.py --all <work-root>     # every scenario folder under <work-root>
  python3 generate-report.py --check <folder>      # render + verify, exit 1 on structural error

Stdlib only. Idempotent — safe to re-run after any stage.
"""

import html as html_mod
import json
import re
import sys
from pathlib import Path

esc = html_mod.escape
VOID_TAGS = {"meta", "br", "img", "link", "input", "hr"}

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def load_asset(name):
    return (ASSETS_DIR / name).read_text(encoding="utf-8")


CSS = load_asset("scenario-report.css")
JS = load_asset("scenario-report.js")



STAGE_LABELS = ["Get Requirement", "Create Test Data", "Create Task", "Execute Backlog", "Api Test", "Acceptance Review"]
TYPE_TAGS = {"unit-test": "t-unit-test", "integration-test": "t-integration-test", "component-test": "t-component-test",
             "code-task": "t-code-task", "api-test": "t-api-test", "env-setup": "t-env-setup", "interface": "t-interface"}


def parse_datatest(md_text):
    sections, cur = [], None
    for line in md_text.splitlines():
        if line.startswith("## "):
            cur = {"title": line[3:].strip(), "header": None, "rows": []}
            sections.append(cur)
        elif cur is not None and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cur["header"] is None:
                cur["header"] = cells
            elif not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                cur["rows"].append(cells)
    return sections


def stage_states(meta, base):
    backlog = list((base / "02-Task" / "02-Backlog").glob("*.json")) if (base / "02-Task" / "02-Backlog").exists() else []
    api = list((base / "02-Task" / "03-Api-test").glob("*.json")) if (base / "02-Task" / "03-Api-test").exists() else []
    def all_done(files):
        return len(files) > 0 and all(json.loads(f.read_text()).get("status") == "done" for f in files)
    return [
        True,  # 1: scenario.html exists (we are rendering it)
        (base / "01-Testdata" / "Datatest.md").exists(),      # 2
        len(list((base / "02-Task").rglob("*.json"))) > 0,    # 3
        all_done(backlog),                                    # 4
        all_done(api),                                        # 5
        bool(meta.get("accepted")),                           # 6
    ]


def stage_track_html(meta, base):
    states = stage_states(meta, base)
    parts = []
    for i, (d, label) in enumerate(zip(states, STAGE_LABELS)):
        if i:
            parts.append('<div class="stage-connector conn-%s"></div>' % ("done" if states[i - 1] else "todo"))
        cls = "s-done" if d else ("s-active" if i == 0 or states[i - 1] else "s-todo")
        parts.append(f'<div class="stage-wrap {cls}"><div class="stage-circle">{i + 1}</div><div class="stage-label">{label}</div></div>')
    return "\n      ".join(parts)


def flow_boxes_html(steps):
    parts = []
    for i, s in enumerate(steps):
        if i:
            parts.append('<div class="flow-arrow">→</div>')
        parts.append(f'<div class="flow-step"><div class="step-num">{i + 1}</div><div class="flow-box" data-step="{i + 1}" onclick="activateStep({i + 1})">{esc(s)}</div></div>')
    return "\n        ".join(parts)


def datatest_html(sections):
    if not sections:
        return '<p class="empty-note">Test data not yet created.</p>'
    cols = len(sections[0]["header"])
    parts = []
    for s in sections:
        parts.append(f'<tr class="section-row"><td colspan="{cols}">{esc(s["title"])}</td></tr>')
        for row in s["rows"]:
            tds = []
            for c in row:
                if re.fullmatch(r"[0-9_\-]+", c) or c.startswith(("EAA-", "acct-", "1000")):
                    tds.append(f"<td><code>{esc(c)}</code></td>")
                else:
                    tds.append(f"<td>{esc(c)}</td>")
            parts.append("<tr>" + "".join(tds) + "</tr>")
    header = "".join(f"<th>{esc(h)}</th>" for h in sections[0]["header"])
    return f'<table class="data-table"><thead><tr>{header}</tr></thead><tbody>' + "".join(parts) + "</tbody></table>"


def task_card_html(t, step):
    status = t.get("status", "pending")
    dot = {"pending": "dot-pending", "in_progress": "dot-in_progress", "done": "dot-done", "failed": "dot-failed"}.get(status, "dot-pending")
    type_cls = TYPE_TAGS.get(t.get("type", ""), "t-env-setup")
    eff = t.get("effort", "low")
    detail = []
    if t.get("contract"):
        detail.append(f'<div class="detail-section"><div class="detail-label">Contract</div><pre class="detail-pre">{esc(t["contract"])}</pre></div>')
    if t.get("pseudocode"):
        detail.append(f'<div class="detail-section"><div class="detail-label">Pseudocode</div><pre class="detail-pre">{esc(t["pseudocode"])}</pre></div>')
    if t.get("cases"):
        items = "".join(f'<li>{esc(c.get("given", ""))} → {esc("; ".join(c.get("assert", [])))}</li>' for c in t["cases"])
        detail.append(f'<div class="detail-section"><div class="detail-label">Cases</div><ul class="assert-list">{items}</ul></div>')
    if t.get("uses"):
        detail.append(f'<div class="detail-section"><div class="detail-label">Test data</div><div class="detail-text">{esc(json.dumps(t["uses"], ensure_ascii=False))}</div></div>')
    if t.get("depends_on"):
        detail.append(f'<div class="detail-section"><div class="detail-label">Depends on</div><div class="dep-tags">' +
                      "".join(f'<span class="dep-tag">{esc(d)}</span>' for d in t["depends_on"]) + '</div></div>')
    if t.get("targets"):
        detail.append('<div class="detail-section"><div class="detail-label">Targets</div>' +
                      "".join(f'<div class="target-path">{esc(x["path"])} ({esc(x["mode"])})</div>' for x in t["targets"]) + '</div>')
    if t.get("command"):
        detail.append(f'<div class="detail-section"><div class="detail-label">Command</div><div class="detail-text">{esc(t["command"])}</div></div>')
    if t.get("acceptance"):
        detail.append(f'<div class="detail-section"><div class="detail-label">Acceptance</div><div class="detail-text">{esc(t["acceptance"])}</div></div>')
    if t.get("notes"):
        detail.append(f'<div class="detail-section"><div class="detail-label">Notes</div><div class="detail-text">{esc(t["notes"])}</div></div>')
    detail_html = "".join(detail) if detail else '<div class="detail-text">(no extra detail)</div>'
    sync_tag = ""
    if t.get("sync"):
        sync_tag = f'<a class="tag sync-tag" href="{esc(t["sync"].get("url", "#"))}" target="_blank">↗ #{esc(t["sync"].get("id", ""))}</a>'
    return (f'<details class="task-card" data-step="{step}">\n  <summary>\n'
            f'    <div class="dot {dot}"></div>\n    <div class="task-body">\n'
            f'      <div class="task-id">{esc(t["id"])}</div>\n      <div class="task-title">{esc(t["title"])}</div>\n      <div class="tags">\n'
            f'        <span class="tag {type_cls}">{esc(t.get("type", ""))}</span>\n        <span class="tag e-{eff}">{esc(eff)}</span>\n'
            f'        <span class="tag status-badge">{esc(status)}</span>{sync_tag}\n      </div>\n    </div>\n'
            f'    <span class="expand-icon">▾</span>\n  </summary>\n  <div class="task-detail">{detail_html}</div>\n</details>')


def tasks_html(base):
    tdir = base / "02-Task"
    if not tdir.exists():
        return '<p class="empty-note">Tasks not yet created.</p>'
    out = []
    for group, label in [("01-Setup", "Setup"), ("02-Backlog", "Backlog"), ("03-Api-test", "Api Test")]:
        gdir = tdir / group
        out.append(f'<div class="task-group"><div class="group-label">{label}</div>')
        files = sorted(gdir.glob("*.json")) if gdir.exists() else []
        if not files:
            out.append('<p class="empty-note">—</p>')
        for f in files:
            t = json.loads(f.read_text())
            step = "all"
            if group == "03-Api-test":
                m = re.match(r"(\d+)-", t["id"])
                step = m.group(1) if m else "all"
            out.append(task_card_html(t, step))
        out.append("</div>")
    return "\n    ".join(out)


def fn_tree_html(base):
    """Preserve the authored fn-tree verbatim from the previous scenario.html; placeholder if none."""
    hp = base / "scenario.html"
    if hp.exists():
        # capture the authored items but NOT the fn-tree's own closing </div>
        m = re.search(r'<div class="fn-tree">(.*?)</div>\s*<div style="display:flex;align-items:center;gap:10px;margin-top:14px">',
                      hp.read_text(), re.S)
        if m:
            return m.group(1).strip()
    return '<p class="empty-note">Functional design not yet created — will be added during Stage 3 (create-task).</p>'


def acceptance_html(meta):
    rounds = meta.get("acceptanceHistory") or []
    if not rounds:
        return '<p class="empty-note">No acceptance rounds yet — Stage 6 not reached.</p>'
    rows = []
    for r in rounds:
        cls = "cat-success" if r.get("result") == "accepted" else "cat-reject"
        rows.append(f'<div class="ah-row"><span class="category {cls}" style="flex-shrink:0;margin-bottom:0">Round {r.get("round")} · {r.get("result")}</span><p class="desc" style="margin:0">{esc(r.get("feedback", ""))}</p></div>')
    return "".join(rows)


def render(base):
    hp = base / "scenario.html"
    if not hp.exists():
        raise SystemExit(f"no scenario.html at {base}")
    m = re.search(r'<script id="scenario-meta" type="application/json">(.*?)</script>', hp.read_text(), re.S)
    if not m:
        raise SystemExit(f"no scenario-meta block at {base}/scenario.html")
    meta = json.loads(m.group(1))
    sections = parse_datatest((base / "01-Testdata" / "Datatest.md").read_text()) if (base / "01-Testdata" / "Datatest.md").exists() else []
    cat = meta["category"].lower()
    meta_json = json.dumps(meta, indent=2)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(meta['scenario'])}</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="container">

  <div class="card header">
    <div class="scenario-name">{esc(meta['scenario'])}</div>
    <span class="category cat-{cat}">{esc(meta['category'])}</span>
    <p class="desc">{esc(meta['description'])}</p>
  </div>

  <div class="card">
    <div class="section-title">Progress</div>
    <div class="stage-track">
      {stage_track_html(meta, base)}
    </div>
  </div>

  <div class="card">
    <div class="section-title" style="margin-bottom:4px">E2E Flow</div>
    <p class="flow-hint">Click a step to highlight related tasks ↓</p>
    <div class="flow-scroll">
      <div class="flow-row">
        {flow_boxes_html(meta['steps'])}
      </div>
    </div>
  </div>

  <div class="card">
    <div class="section-title">Functional Design</div>
    <p class="flow-hint" style="margin-bottom:14px">Drag ⠿ to reorder or re-nest · Top/bottom = sibling · Middle = child · Click name to highlight tasks ↓</p>
    <div class="fn-tree">
      {fn_tree_html(base)}
    </div>
    <div style="display:flex;align-items:center;gap:10px;margin-top:14px">
      <button class="fn-copy-btn" onclick="copyFnTree()">Copy tree HTML</button>
      <span id="fn-copy-confirm" style="font-size:0.72rem;color:#22c55e;display:none">Copied! Paste to Claude to save.</span>
    </div>
  </div>

  <div class="card">
    <div class="section-title" style="margin-bottom:12px">Test Data</div>
    {datatest_html(sections)}
  </div>

  <div class="card">
    <div class="section-title" style="margin-bottom:16px">Tasks</div>
    {tasks_html(base)}
  </div>

  <div class="card">
    <div class="section-title">Acceptance History</div>
    {acceptance_html(meta)}
  </div>

</div>

<script id="scenario-meta" type="application/json">
{meta_json}
</script>
<script>
{JS}
</script>
</body>
</html>
"""
    hp.write_text(html)
    return hp


def verify(base):
    """Strict structural check: balanced non-void tags."""
    from html.parser import HTMLParser

    class Strict(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack = []
            self.errors = []

        def handle_starttag(self, tag, attrs):
            if tag not in VOID_TAGS:
                self.stack.append(tag)

        def handle_endtag(self, tag):
            if tag in VOID_TAGS:
                return
            if not self.stack:
                self.errors.append(f"extra </{tag}> at {self.getpos()}"); return
            if self.stack[-1] == tag:
                self.stack.pop(); return
            if tag in self.stack:
                while self.stack and self.stack[-1] != tag:
                    self.stack.pop()
                self.stack.pop()
            else:
                self.errors.append(f"mismatch </{tag}> at {self.getpos()}")

    p = Strict()
    p.feed((base / "scenario.html").read_text())
    unclosed = [t for t in p.stack if t not in ("html", "head", "body")]
    return not p.errors and not unclosed, p.errors, unclosed


def find_scenarios(work_root):
    out = []
    for html_path in Path(work_root).rglob("scenario.html"):
        out.append(html_path.parent)
    return sorted(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or any(a in ("-h", "--help") for a in args):
        print(__doc__)
        raise SystemExit(0 if args else 1)
    if args[0] == "--all":
        targets = find_scenarios(args[1] if len(args) > 1 else ".")
    elif args[0] == "--check":
        targets = [Path(args[1])]
    else:
        targets = [Path(a) for a in args]
    fail = 0
    for t in targets:
        try:
            out = render(t)
            ok, errs, unclosed = verify(t)
            state = "ok" if ok else f"STRUCTURE FAIL {errs} {unclosed}"
            print(f"{t} → {out.name} [{state}]")
            if not ok:
                fail += 1
        except SystemExit as e:
            print(f"{t} → {e}")
            fail += 1
    raise SystemExit(1 if fail else 0)
