#!/usr/bin/env python3
"""generate-feature-dashboard.py — aggregates cross-service feature scenarios into an interactive dashboard.

Scans work/Scenario/ across microservice repositories for matching feature scenarios (e.g. BIZ_AI, BROADCAST, ALL),
extracts metadata, progress tracks, test data, and task graphs, and generates a self-contained,
fully interactive HTML feature dashboard.

Usage:
  python3 generate-feature-dashboard.py --feature BIZ_AI
  python3 generate-feature-dashboard.py --feature BROADCAST --output broadcast-dashboard.html
  python3 generate-feature-dashboard.py --services-dir /path/to/services --feature ALL
  python3 generate-feature-dashboard.py --check
"""

import argparse
import html as html_mod
import json
import os
import re
import sys
from pathlib import Path

esc = html_mod.escape
VOID_TAGS = {"meta", "br", "img", "link", "input", "hr"}

STAGE_LABELS = [
    "Get Requirement",
    "Create Test Data",
    "Create Task",
    "Execute Backlog",
    "Api Test",
    "Acceptance Review",
]

TYPE_TAGS = {
    "unit-test": "t-unit-test",
    "integration-test": "t-integration-test",
    "component-test": "t-component-test",
    "code-task": "t-code-task",
    "api-test": "t-api-test",
    "env-setup": "t-env-setup",
    "interface": "t-interface",
}

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def load_asset(name):
    return (ASSETS_DIR / name).read_text(encoding="utf-8")


CSS = load_asset("feature-dashboard.css")
JS = load_asset("feature-dashboard.js")




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


def calculate_stage_states(meta, base, tasks_by_group):
    backlog = tasks_by_group.get("02-Backlog", [])
    api = tasks_by_group.get("03-Api-test", [])
    all_tasks = tasks_by_group.get("01-Setup", []) + backlog + api

    def all_done(task_list):
        return len(task_list) > 0 and all(
            t.get("status") == "done" for t in task_list
        )

    has_testdata = (base / "01-Testdata" / "Datatest.md").exists()
    return [
        True,  # 1: Requirement defined
        has_testdata,  # 2: Test data
        len(all_tasks) > 0,  # 3: Tasks created
        all_done(backlog),  # 4: Backlog executed
        all_done(api),  # 5: Api test executed
        bool(meta.get("accepted")),  # 6: Acceptance review
    ]


def stage_track_html(states):
    parts = []
    for i, (d, label) in enumerate(zip(states, STAGE_LABELS)):
        if i:
            parts.append(
                f'<div class="stage-connector conn-{"done" if states[i - 1] else "todo"}"></div>'
            )
        cls = (
            "s-done"
            if d
            else ("s-active" if i == 0 or states[i - 1] else "s-todo")
        )
        parts.append(
            f'<div class="stage-wrap {cls}">'
            f'<div class="stage-circle">{i + 1}</div>'
            f'<div class="stage-label">{label}</div>'
            f"</div>"
        )
    return "\n          ".join(parts)


def flow_boxes_html(scenario_id, steps):
    parts = []
    for i, s in enumerate(steps):
        if i:
            parts.append('<div class="flow-arrow">→</div>')
        parts.append(
            f'<div class="flow-step">'
            f'<div class="step-num">{i + 1}</div>'
            f'<div class="flow-box" data-step="{i + 1}" onclick="activateStep(\'{esc(scenario_id)}\', {i + 1})">{esc(s)}</div>'
            f"</div>"
        )
    return "\n            ".join(parts)


def datatest_html(sections):
    if not sections:
        return '<p class="empty-note">Test data not yet created.</p>'
    cols = len(sections[0]["header"])
    parts = []
    for s in sections:
        parts.append(
            f'<tr class="section-row"><td colspan="{cols}">{esc(s["title"])}</td></tr>'
        )
        for row in s["rows"]:
            tds = []
            for c in row:
                if re.fullmatch(r"[0-9_\-]+", c) or c.startswith(
                    ("EAA-", "acct-", "1000")
                ):
                    tds.append(f"<td><code>{esc(c)}</code></td>")
                else:
                    tds.append(f"<td>{esc(c)}</td>")
            parts.append("<tr>" + "".join(tds) + "</tr>")
    header = "".join(f"<th>{esc(h)}</th>" for h in sections[0]["header"])
    return (
        f'<table class="data-table"><thead><tr>{header}</tr></thead><tbody>'
        + "".join(parts)
        + "</tbody></table>"
    )


def task_card_html(t, step):
    status = t.get("status", "pending")
    dot = {
        "pending": "dot-pending",
        "in_progress": "dot-in_progress",
        "done": "dot-done",
        "failed": "dot-failed",
    }.get(status, "dot-pending")
    type_cls = TYPE_TAGS.get(t.get("type", ""), "t-env-setup")
    eff = t.get("effort", "low")
    detail = []

    if t.get("contract"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Contract</div><pre class="detail-pre">{esc(t["contract"])}</pre></div>'
        )
    if t.get("pseudocode"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Pseudocode</div><pre class="detail-pre">{esc(t["pseudocode"])}</pre></div>'
        )
    if t.get("cases"):
        items = "".join(
            f'<li>{esc(c.get("given", ""))} → {esc("; ".join(c.get("assert", [])))}</li>'
            for c in t["cases"]
        )
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Cases</div><ul class="assert-list">{items}</ul></div>'
        )
    if t.get("uses"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Test data</div><div class="detail-text">{esc(json.dumps(t["uses"], ensure_ascii=False))}</div></div>'
        )
    if t.get("depends_on"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Depends on</div><div class="dep-tags">'
            + "".join(f'<span class="dep-tag">{esc(d)}</span>' for d in t["depends_on"])
            + "</div></div>"
        )
    if t.get("targets"):
        detail.append(
            '<div class="detail-section"><div class="detail-label">Targets</div>'
            + "".join(
                f'<div class="target-path">{esc(x.get("path", ""))} ({esc(x.get("mode", "modify"))})</div>'
                for x in t["targets"]
            )
            + "</div>"
        )
    if t.get("command"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Command</div><div class="detail-text">{esc(t["command"])}</div></div>'
        )
    if t.get("acceptance"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Acceptance</div><div class="detail-text">{esc(t["acceptance"])}</div></div>'
        )
    if t.get("notes"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Notes</div><div class="detail-text">{esc(t["notes"])}</div></div>'
        )

    detail_html = (
        "".join(detail) if detail else '<div class="detail-text">(no extra detail)</div>'
    )
    sync_tag = ""
    if t.get("sync"):
        sync_tag = f'<a class="tag sync-tag" href="{esc(t["sync"].get("url", "#"))}" target="_blank">↗ #{esc(str(t["sync"].get("id", "")))}</a>'

    return (
        f'<details class="task-card" data-step="{step}">\n'
        f"  <summary>\n"
        f'    <div class="dot {dot}"></div>\n'
        f'    <div class="task-body">\n'
        f'      <div class="task-id">{esc(t["id"])}</div>\n'
        f'      <div class="task-title">{esc(t.get("title", ""))}</div>\n'
        f'      <div class="tags">\n'
        f'        <span class="tag {type_cls}">{esc(t.get("type", ""))}</span>\n'
        f'        <span class="tag e-{eff}">{esc(eff)}</span>\n'
        f'        <span class="tag status-badge">{esc(status)}</span>{sync_tag}\n'
        f"      </div>\n"
        f"    </div>\n"
        f'    <span class="expand-icon">▾</span>\n'
        f"  </summary>\n"
        f'  <div class="task-detail">{detail_html}</div>\n'
        f"</details>"
    )


def tasks_html(tasks_by_group):
    all_empty = all(len(v) == 0 for v in tasks_by_group.values())
    if all_empty:
        return '<p class="empty-note">Tasks not yet created (Stage 3).</p>'

    out = []
    for group_key, label in [
        ("01-Setup", "Setup"),
        ("02-Backlog", "Backlog"),
        ("03-Api-test", "Api Test"),
    ]:
        tasks = tasks_by_group.get(group_key, [])
        out.append(f'<div class="task-group"><div class="group-label">{label}</div>')
        if not tasks:
            out.append('<p class="empty-note">—</p>')
        else:
            for t in tasks:
                step = "all"
                if group_key == "03-Api-test":
                    m = re.match(r"(\d+)-", t["id"])
                    step = m.group(1) if m else "all"
                out.append(task_card_html(t, step))
        out.append("</div>")
    return "\n    ".join(out)


def fn_tree_html(sc_dir, scenario_id):
    hp = sc_dir / "scenario.html"
    if hp.exists():
        content = hp.read_text(encoding="utf-8")
        m = re.search(
            r'<div class="fn-tree">(.*?)</div>\s*<div style="display:flex;align-items:center;gap:10px;margin-top:14px">',
            content,
            re.S,
        )
        if m:
            tree_inner = m.group(1).strip()
            # Rewrite activateFn call signatures to include scenarioId
            tree_inner = re.sub(
                r'activateFn\(this,\s*(\[.*?\])\)',
                rf"activateFn(this, \1, '{scenario_id}')",
                tree_inner,
            )
            return f'<div class="fn-tree">{tree_inner}</div>'
    return '<p class="empty-note">Functional design tree not yet created.</p>'


def acceptance_html(meta):
    rounds = meta.get("acceptanceHistory") or []
    if not rounds:
        return '<p class="empty-note">No acceptance rounds recorded yet.</p>'
    rows = []
    for r in rounds:
        cls = "cat-success" if r.get("result") == "accepted" else "cat-reject"
        rows.append(
            f'<div class="ah-row">'
            f'<span class="category {cls}" style="flex-shrink:0;margin-bottom:0">Round {r.get("round")} · {r.get("result")}</span>'
            f'<p class="desc" style="margin:0;font-size:0.84rem">{esc(r.get("feedback", ""))}</p>'
            f"</div>"
        )
    return "".join(rows)


def scan_feature_scenarios(services_dir, feature_keyword):
    scenarios = []
    svc_dir = Path(services_dir)
    if not svc_dir.exists():
        raise SystemExit(f"Services directory does not exist: {services_dir}")

    is_all = feature_keyword.upper() == "ALL"

    # Scan all service folders
    for service_path in sorted(svc_dir.iterdir()):
        if not service_path.is_dir():
            continue

        scenario_root = service_path / "work" / "Scenario"
        if not scenario_root.exists():
            continue

        for sc_html in sorted(scenario_root.rglob("scenario.html")):
            sc_dir = sc_html.parent
            feature_dir_name = ""
            for part in sc_html.parts:
                if is_all:
                    if part not in ("work", "Scenario", "Success", "Alternative", "scenario.html", service_path.name):
                        feature_dir_name = part
                elif feature_keyword.upper() in part.upper():
                    feature_dir_name = part
                    break

            # Read scenario-meta
            text = sc_html.read_text(encoding="utf-8")
            m = re.search(
                r'<script id="scenario-meta" type="application/json">(.*?)</script>',
                text,
                re.S,
            )
            if not m and not is_all and not feature_dir_name:
                continue

            meta = json.loads(m.group(1)) if m else {}
            sc_name = meta.get("scenario", sc_dir.name)

            # Match on feature name or folder name or scenario name
            if not is_all:
                if not (
                    feature_keyword.upper() in feature_dir_name.upper()
                    or feature_keyword.upper() in sc_dir.name.upper()
                    or feature_keyword.upper() in sc_name.upper()
                ):
                    continue

            # Load tasks
            tdir = sc_dir / "02-Task"
            tasks_by_group = {
                "01-Setup": [],
                "02-Backlog": [],
                "03-Api-test": [],
            }
            if tdir.exists():
                for grp in ["01-Setup", "02-Backlog", "03-Api-test"]:
                    gpath = tdir / grp
                    if gpath.exists():
                        for f in sorted(gpath.glob("*.json")):
                            try:
                                tasks_by_group[grp].append(
                                    json.loads(f.read_text(encoding="utf-8"))
                                )
                            except Exception:
                                pass

            # Load test data
            dt_file = sc_dir / "01-Testdata" / "Datatest.md"
            testdata_sections = (
                parse_datatest(dt_file.read_text(encoding="utf-8"))
                if dt_file.exists()
                else []
            )

            stage_states = calculate_stage_states(meta, sc_dir, tasks_by_group)

            category = meta.get("category") or (
                "Success" if "Success" in str(sc_dir) else "Alternative"
            )

            scenarios.append(
                {
                    "service": service_path.name,
                    "service_path": str(service_path),
                    "feature": feature_dir_name or feature_keyword,
                    "category": category,
                    "id": sc_name,
                    "scenario": sc_name,
                    "dir_path": sc_dir,
                    "meta": meta,
                    "tasks_by_group": tasks_by_group,
                    "testdata_sections": testdata_sections,
                    "stage_states": stage_states,
                    "stages_done": sum(1 for s in stage_states if s),
                    "total_tasks": sum(
                        len(v) for v in tasks_by_group.values()
                    ),
                    "done_tasks": sum(
                        sum(1 for t in v if t.get("status") == "done")
                        for v in tasks_by_group.values()
                    ),
                    "accepted": bool(meta.get("accepted")),
                }
            )

    return scenarios


def render_feature_dashboard(scenarios, feature_name, title=None, subtitle=None):
    # Group by service
    services = {}
    for sc in scenarios:
        s_name = sc["service"]
        if s_name not in services:
            services[s_name] = []
        services[s_name].append(sc)

    total_scenarios = len(scenarios)
    total_tasks = sum(sc["total_tasks"] for sc in scenarios)
    total_done_tasks = sum(sc["done_tasks"] for sc in scenarios)
    total_accepted = sum(1 for sc in scenarios if sc["accepted"])
    total_services = len(services)

    service_names_str = ", ".join(sorted(services.keys()))

    if not title:
        f_display = feature_name.replace("_", " ").title() if feature_name != "ALL" else "All Features"
        title = f"{f_display} Cross-Service Dashboard"

    if not subtitle:
        subtitle = (
            f"Cross-service blueprint across {total_services} microservices ({service_names_str}) "
            f"aggregating {total_scenarios} scenarios and {total_tasks} tasks."
        )

    # 1. Topology & Service Cards (Dynamic in Overview)
    topology_cards = []
    for s_idx, (s_name, sc_list) in enumerate(services.items()):
        if s_idx > 0:
            topology_cards.append('<div class="node-conn">➔</div>')
        
        s_tasks = sum(sc["total_tasks"] for sc in sc_list)
        s_done_tasks = sum(sc["done_tasks"] for sc in sc_list)
        s_accepted = sum(1 for sc in sc_list if sc["accepted"])
        s_features = sorted(list(set(sc["feature"] for sc in sc_list)))
        feature_tag = s_features[0] if s_features else "Feature"

        topology_cards.append(
            f'<div class="service-node">'
            f'  <div class="service-node-header">'
            f'    <div class="service-node-title">{esc(s_name)}</div>'
            f'    <span class="service-pill">{len(sc_list)} scenarios</span>'
            f"  </div>"
            f'  <div class="service-node-feature">Feature: {esc(feature_tag)}</div>'
            f'  <div class="service-node-stats">'
            f'    <div class="service-node-stat">'
            f'      <span class="service-node-stat-val">{s_done_tasks} / {s_tasks}</span>'
            f'      <span class="service-node-stat-label">Tasks Done</span>'
            f"    </div>"
            f'    <div class="service-node-stat">'
            f'      <span class="service-node-stat-val">{s_accepted} / {len(sc_list)}</span>'
            f'      <span class="service-node-stat-label">Accepted</span>'
            f"    </div>"
            f"  </div>"
            f'  <button class="service-node-btn" onclick="switchTab(\'{esc(s_name)}\')">Browse Scenarios →</button>'
            f"</div>"
        )

    # 2. Overview Matrix Table
    matrix_rows = []
    for sc in scenarios:
        cat_cls = (
            "cat-success"
            if sc["category"].lower() == "success"
            else "cat-alternative"
        )
        service_key = sc["service"]
        sc_id = sc["id"]

        mini_dots = "".join(
            f'<div class="mini-dot {"mini-done" if s else "mini-todo"}"></div>'
            for s in sc["stage_states"]
        )

        matrix_rows.append(
            f'<tr class="matrix-row">'
            f'<td><span class="service-pill">{esc(sc["service"])}</span></td>'
            f'<td><span class="category {cat_cls}">{esc(sc["category"])}</span></td>'
            f'<td><a class="scenario-link" onclick="selectScenario(\'{esc(service_key)}\', \'{esc(sc_id)}\')">{esc(sc["scenario"])}</a></td>'
            f'<td><div class="mini-stage-bar">{mini_dots} <span style="font-size:0.75rem;margin-left:6px;font-weight:700">{sc["stages_done"]}/6</span></div></td>'
            f'<td><span class="summary-count-badge">{sc["done_tasks"]}/{sc["total_tasks"]} done</span></td>'
            f'<td>{"<span class=\'category cat-success\'>Accepted</span>" if sc["accepted"] else "<span class=\'category cat-alternative\'>In Progress</span>"}</td>'
            f'<td><button class="view-btn" onclick="selectScenario(\'{esc(service_key)}\', \'{esc(sc_id)}\')">View →</button></td>'
            f"</tr>"
        )

    # 3. Service Tab Panels
    service_panels = []
    tab_buttons = [
        '<button class="tab-btn active" data-tab="overview" onclick="switchTab(\'overview\')">'
        '📊 Feature Overview <span class="tab-count">'
        + str(total_scenarios)
        + "</span></button>"
    ]

    for s_name, sc_list in services.items():
        tab_buttons.append(
            f'<button class="tab-btn" data-tab="{esc(s_name)}" onclick="switchTab(\'{esc(s_name)}\')">'
            f'📦 {esc(s_name)} <span class="tab-count">{len(sc_list)}</span>'
            f"</button>"
        )

        nav_items = []
        scenario_views = []

        for idx, sc in enumerate(sc_list):
            is_first = idx == 0
            active_cls = "active" if is_first else ""
            cat_cls = (
                "cat-success"
                if sc["category"].lower() == "success"
                else "cat-alternative"
            )
            sc_id = sc["id"]

            nav_items.append(
                f'<div class="scenario-nav-item {active_cls}" data-scenario="{esc(sc_id)}" onclick="selectScenario(\'{esc(s_name)}\', \'{esc(sc_id)}\')">'
                f'  <div class="nav-item-header">'
                f'    <span class="nav-item-title">{esc(sc["scenario"])}</span>'
                f'    <span class="category {cat_cls}">{esc(sc["category"])}</span>'
                f"  </div>"
                f'  <div class="nav-item-sub">'
                f'    <span>Stage {sc["stages_done"]}/6</span>'
                f'    <span>•</span>'
                f'    <span>{sc["total_tasks"]} tasks</span>'
                f"  </div>"
                f"</div>"
            )

            # Render scenario content
            meta = sc["meta"]
            tasks_by_group = sc["tasks_by_group"]
            setup_c = len(tasks_by_group.get("01-Setup", []))
            setup_d = sum(
                1
                for t in tasks_by_group.get("01-Setup", [])
                if t.get("status") == "done"
            )
            backlog_c = len(tasks_by_group.get("02-Backlog", []))
            backlog_d = sum(
                1
                for t in tasks_by_group.get("02-Backlog", [])
                if t.get("status") == "done"
            )
            api_c = len(tasks_by_group.get("03-Api-test", []))
            api_d = sum(
                1
                for t in tasks_by_group.get("03-Api-test", [])
                if t.get("status") == "done"
            )

            sync_link_html = ""
            if meta.get("sync"):
                sync_link_html = f'<a class="sync-link" href="{esc(meta["sync"].get("url", "#"))}" target="_blank">↗ Issue #{esc(str(meta["sync"].get("id", "")))}</a>'

            scenario_views.append(
                f'<div class="scenario-view {active_cls}" id="view-{esc(sc_id)}">'
                f'  <div class="card scenario-header-card">'
                f'    <div class="scenario-header-top">'
                f'      <div class="scenario-heading">{esc(sc["scenario"])}</div>'
                f'      <div class="badge-group">'
                f'        <span class="service-pill">{esc(s_name)}</span>'
                f'        <span class="category {cat_cls}">{esc(sc["category"])}</span>'
                f"        {sync_link_html}"
                f"      </div>"
                f"    </div>"
                f'    <p class="scenario-desc">{esc(meta.get("description", ""))}</p>'
                f"  </div>"
                f'  <div class="card">'
                f'    <div class="section-title">6-Stage Progress Indicator</div>'
                f'    <div class="stage-track">'
                f"      {stage_track_html(sc['stage_states'])}"
                f"    </div>"
                f'    <div class="progress-summary-row">'
                f'      <div class="progress-summary-item">Setup: <span class="summary-count-badge">{setup_d}/{setup_c} done</span></div>'
                f'      <div class="progress-summary-item">Backlog: <span class="summary-count-badge">{backlog_d}/{backlog_c} done</span></div>'
                f'      <div class="progress-summary-item">Api Test: <span class="summary-count-badge">{api_d}/{api_c} done</span></div>'
                f"    </div>"
                f"  </div>"
                f'  <div class="card">'
                f'    <div class="section-title">E2E Flow</div>'
                f'    <div class="flow-hint">Click a step to highlight matching task cards.</div>'
                f'    <div class="flow-scroll">'
                f'      <div class="flow-row">'
                f"        {flow_boxes_html(sc_id, meta.get('steps', []))}"
                f"      </div>"
                f"    </div>"
                f"  </div>"
                f'  <div class="card">'
                f'    <div class="section-title">Functional Design</div>'
                f"    {fn_tree_html(sc['dir_path'], sc_id)}"
                f"  </div>"
                f'  <div class="card">'
                f'    <div class="section-title">Test Data</div>'
                f"    {datatest_html(sc['testdata_sections'])}"
                f"  </div>"
                f'  <div class="card">'
                f'    <div class="card-header-row">'
                f'      <div class="section-title" style="margin-bottom:0">Tasks ({sc["total_tasks"]})</div>'
                f'      <div class="controls-row">'
                f'        <button class="btn-secondary" onclick="toggleAllTasks(\'{esc(sc_id)}\', true)">Expand All</button>'
                f'        <button class="btn-secondary" onclick="toggleAllTasks(\'{esc(sc_id)}\', false)">Collapse All</button>'
                f"      </div>"
                f"    </div>"
                f"    {tasks_html(tasks_by_group)}"
                f"  </div>"
                f'  <div class="card">'
                f'    <div class="section-title">Acceptance Review History</div>'
                f"    {acceptance_html(meta)}"
                f"  </div>"
                f"</div>"
            )

        service_panels.append(
            f'<div class="tab-panel" id="panel-{esc(s_name)}">'
            f'  <div class="scenario-layout">'
            f'    <div class="scenario-sidebar">'
            f'      <div class="sidebar-title">Scenarios ({len(sc_list)})</div>'
            f"      {''.join(nav_items)}"
            f"    </div>"
            f'    <div class="scenario-content">'
            f"      {''.join(scenario_views)}"
            f"    </div>"
            f"  </div>"
            f"</div>"
        )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
{CSS}
</style>
</head>
<body>

<header class="app-header">
  <div class="header-container">
    <div class="header-top">
      <div>
        <div class="feature-title">⚡ {esc(title)}</div>
        <p class="feature-subtitle">{esc(subtitle)}</p>
      </div>
      <div class="badge-group">
        <span class="badge-chip">RAT Workspace</span>
        <span class="badge-chip">Feature: {esc(feature_name)}</span>
        <span class="badge-chip">Live Report</span>
      </div>
    </div>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-val">{total_services}</div>
        <div class="stat-label">Services</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{total_scenarios}</div>
        <div class="stat-label">Total Scenarios</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{total_done_tasks} / {total_tasks}</div>
        <div class="stat-label">Tasks Done</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{total_accepted} / {total_scenarios}</div>
        <div class="stat-label">Accepted Scenarios</div>
      </div>
    </div>
  </div>
</header>

<div class="nav-bar-wrap">
  <div class="nav-bar">
    <ul class="tab-list">
      {''.join(tab_buttons)}
    </ul>
    <div class="search-box">
      <span class="search-icon">🔍</span>
      <input type="text" class="search-input" placeholder="Search scenarios..." oninput="filterScenarios(this.value)">
    </div>
  </div>
</div>

<main class="main-container">

  <!-- Overview Panel -->
  <div class="tab-panel active" id="panel-overview">
    
    <!-- Cross-Service Participating Topology -->
    <div class="topology-box">
      <div class="topology-header">
        <div class="topology-title">Participating Microservices & Architecture Topology</div>
        <span class="badge-chip">{total_services} Active Services</span>
      </div>
      <div class="topology-grid">
        {''.join(topology_cards)}
      </div>
    </div>

    <!-- Scenario Matrix -->
    <div class="card">
      <div class="card-header-row">
        <div>
          <div class="card-title">Cross-Service Scenarios Matrix</div>
          <div class="card-subtitle">Complete scenario ledger across all participating microservices</div>
        </div>
      </div>
      <table class="matrix-table">
        <thead>
          <tr>
            <th>Service</th>
            <th>Category</th>
            <th>Scenario</th>
            <th>6-Stage Progress</th>
            <th>Tasks</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {''.join(matrix_rows)}
        </tbody>
      </table>
    </div>

  </div>

  <!-- Service Specific Panels -->
  {''.join(service_panels)}

</main>

<script>
{JS}
</script>

</body>
</html>
"""
    return html_content


def verify_balanced_tags(html_str):
    from html.parser import HTMLParser

    class TagValidator(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.errors = []

        def handle_starttag(self, tag, attrs):
            if tag.lower() not in VOID_TAGS:
                self.stack.append((tag.lower(), self.getpos()))

        def handle_endtag(self, tag):
            tag_l = tag.lower()
            if tag_l in VOID_TAGS:
                return
            if not self.stack:
                self.errors.append(f"unexpected </{tag_l}> at {self.getpos()}")
                return
            top, pos = self.stack.pop()
            if top != tag_l:
                self.errors.append(
                    f"mismatched </{tag_l}> at {self.getpos()} (expected </{top}> opened at {pos})"
                )

    parser = TagValidator()
    parser.feed(html_str)
    parser.close()
    return len(parser.errors) == 0 and len(parser.stack) == 0, parser.errors, parser.stack


def find_default_services_dir():
    """Auto-detect the services root directory from env, cwd, or parent hierarchy."""
    if "SERVICES_DIR" in os.environ:
        return Path(os.environ["SERVICES_DIR"]).resolve()

    cwd = Path.cwd().resolve()
    candidates = [
        cwd / "services",
        cwd.parent / "services",
        cwd.parent.parent / "services",
        cwd.parent.parent.parent / "services",
        cwd.parent.parent.parent.parent / "services",
        Path("/Users/jackmod/Develops/services"),
        cwd,
    ]
    for c in candidates:
        if c.is_dir() and any(
            (c / repo / "work").exists() or (c / repo / "trust-me-bro-ai").exists()
            for repo in os.listdir(c)
            if (c / repo).is_dir()
        ):
            return c
    return cwd


def get_scenarios_fingerprint(services_dir):
    """Compute a timestamp fingerprint of all scenario files under services_dir."""
    svc_dir = Path(services_dir)
    if not svc_dir.exists():
        return 0
    max_mtime = 0
    for sc_root in svc_dir.glob("*/work/Scenario"):
        for p in sc_root.rglob("*"):
            if p.is_file() and p.suffix in (".json", ".md", ".html"):
                try:
                    m = p.stat().st_mtime
                    if m > max_mtime:
                        max_mtime = m
                except OSError:
                    pass
    return max_mtime


def run_serve(args, out_path, port=8080):
    """Run zero-dependency local HTTP server with automatic live-reload on file changes."""
    import time
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    state = {
        "html": "",
        "version": str(time.time()),
    }

    def update_dashboard():
        scenarios = scan_feature_scenarios(args.services_dir, args.feature)
        if not scenarios:
            return
        raw_html = render_feature_dashboard(scenarios, args.feature, title=args.title)
        # Inject live-reload client
        live_reload_script = """
<script>
(function() {
  let _currentVer = null;
  setInterval(async function() {
    try {
      const res = await fetch('/live-reload-version');
      const ver = await res.text();
      if (_currentVer === null) {
        _currentVer = ver;
      } else if (_currentVer !== ver) {
        _currentVer = ver;
        console.log('[live-reload] Scenario files updated, reloading...');
        window.location.reload();
      }
    } catch(e) {}
  }, 800);
})();
</script>
</body>"""
        state["html"] = raw_html.replace("</body>", live_reload_script)
        state["version"] = str(time.time())
        # Also write to disk if out_path is set
        if out_path:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(raw_html, encoding="utf-8")

    update_dashboard()

    # Watcher thread
    def watch_loop():
        last_fp = get_scenarios_fingerprint(args.services_dir)
        while True:
            time.sleep(0.8)
            curr_fp = get_scenarios_fingerprint(args.services_dir)
            if curr_fp > last_fp:
                last_fp = curr_fp
                print(f"[live-reload] File change detected at {time.strftime('%H:%M:%S')}, regenerating...")
                update_dashboard()

    watcher = threading.Thread(target=watch_loop, daemon=True)
    watcher.start()

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/live-reload-version":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(state["version"].encode("utf-8"))
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(state["html"].encode("utf-8"))

        def log_message(self, format, *log_args):
            pass  # Suppress request spam

    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"\n⚡ Live Dashboard running at: http://localhost:{port}")
    print(f"   Watching: {args.services_dir} for '{args.feature}' scenarios")
    print("   Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server.")
        server.server_close()


def run_watch(args, out_path):
    """Run file watcher loop to regenerate static HTML on disk when files change."""
    import time

    def regenerate():
        scenarios = scan_feature_scenarios(args.services_dir, args.feature)
        if not scenarios:
            return
        html_out = render_feature_dashboard(scenarios, args.feature, title=args.title)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html_out, encoding="utf-8")
        print(f"[watch] Regenerated dashboard ({len(scenarios)} scenarios) -> {out_path} at {time.strftime('%H:%M:%S')}")

    regenerate()
    last_fp = get_scenarios_fingerprint(args.services_dir)
    print(f"\n👀 Watching {args.services_dir} for '{args.feature}' changes (Ctrl+C to stop)...")
    try:
        while True:
            time.sleep(1.0)
            curr_fp = get_scenarios_fingerprint(args.services_dir)
            if curr_fp > last_fp:
                last_fp = curr_fp
                regenerate()
    except KeyboardInterrupt:
        print("\nStopping watcher.")


def main():
    default_services = find_default_services_dir()
    parser = argparse.ArgumentParser(
        description="Generate cross-service feature dashboard for trust-me-bro-ai."
    )
    parser.add_argument(
        "--services-dir",
        default=str(default_services),
        help=f"Root directory containing microservices (default auto-detected: {default_services})",
    )
    parser.add_argument(
        "--feature",
        "-f",
        default="BIZ_AI",
        help="Feature keyword to scan (e.g. BIZ_AI, BROADCAST, or ALL)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output HTML dashboard file path (default: feature-<slug>-dashboard.html)",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Custom dashboard title (default: auto-generated from feature name)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the generated dashboard HTML without writing",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch work/Scenario/ across services and regenerate output on disk on changes",
    )
    parser.add_argument(
        "--serve",
        nargs="?",
        const=8080,
        type=int,
        help="Serve dashboard with zero-dependency auto-reloading dev server (default port: 8080)",
    )

    args = parser.parse_args()

    # Derive default output path
    if args.output:
        out_path = Path(args.output).resolve()
    else:
        slug = args.feature.lower().replace("_", "-")
        base_dir = Path(args.services_dir).parent if Path(args.services_dir).name == "services" else Path.cwd()
        filename = "feature-biz-ai-integration.html" if slug == "biz-ai" else f"feature-{slug}-dashboard.html"
        out_path = (base_dir / filename).resolve()

    if args.serve:
        run_serve(args, out_path, port=args.serve)
        return

    if args.watch:
        run_watch(args, out_path)
        return

    scenarios = scan_feature_scenarios(args.services_dir, args.feature)
    if not scenarios:
        print(f"No scenarios found for feature: {args.feature} in {args.services_dir}")
        sys.exit(1)

    print(
        f"Found {len(scenarios)} scenarios across {len(set(s['service'] for s in scenarios))} services for feature '{args.feature}'."
    )
    for sc in scenarios:
        print(
            f"  [{sc['service']}] {sc['category']} / {sc['scenario']} ({sc['stages_done']}/6 stages, {sc['total_tasks']} tasks)"
        )

    html_out = render_feature_dashboard(
        scenarios, args.feature, title=args.title
    )

    is_valid, errors, unclosed = verify_balanced_tags(html_out)
    if not is_valid:
        print("HTML validation errors:")
        for err in errors:
            print(" ", err)
        for tag, pos in unclosed:
            print(f"  unclosed <{tag}> opened at {pos}")
        sys.exit(1)

    if args.check:
        print("[ok] Dashboard HTML passed structural validation.")
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_out, encoding="utf-8")
    print(f"[ok] Dashboard successfully written to: {out_path}")


if __name__ == "__main__":
    main()
