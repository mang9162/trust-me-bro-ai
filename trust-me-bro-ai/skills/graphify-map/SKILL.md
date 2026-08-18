---
name: graphify-map
description: Map the project — or several repos/folders at once — into one queryable knowledge graph with Graphify — check whether Graphify is installed, ask the user if they prefer it (default: prefer), and when opted in map the project root (optionally plus extra GitHub URLs / sibling folders, merged via merge-graphs) to produce graphify-out/ that later questions can query first.
---

# Graphify Map

## Purpose

Build a knowledge graph of the entire project — or of several repos/folders merged into one cross-repo graph — with Graphify (https://github.com/Graphify-Labs/graphify), so later codebase questions (architecture, file relationships, data flow) are answered from the graph instead of re-scanning the repo. Optional by design — it only runs when Graphify is installed AND the user prefers it (default: prefer).

## Procedure

### 1. Check Graphify is installed

Detect in order: the Graphify skill at `~/.claude/skills/graphify/SKILL.md` (or the host's skills dir), the `graphify` CLI on PATH, or the `graphifyy` Python package importable.

- Installed → step 2.
- Not installed → say so, show https://github.com/Graphify-Labs/graphify, and offer to install (`uv tool install graphifyy`, else `python3 -m pip install graphifyy`). Ask the user — never install silently. If they decline → stop here; the map is skipped.

### 2. Ask preference (default: prefer)

Ask: "Prefer to map this project with Graphify? (default: prefer)". Only a clear no stops — anything else (yes, "sure", silence, "default") counts as prefer.

- Prefer → step 3.
- No → stop cleanly; say it's skipped and can be re-run anytime.

### 3. Run the map

Targets: the project root (the repo being mapped, never the kit folder), plus any extra targets the user named — GitHub URLs or sibling local folders (a multi-repo / multi-service system maps into ONE merged graph).

**Single target (default)**

- Graphify skill present → follow its full pipeline (detect → extract → cluster → report → viz).
- CLI only → `graphify .` (full pipeline; add `--mode deep` for richer INFERRED edges on big repos).

Output lands in `graphify-out/` at the project root: `graph.json` (GraphRAG-ready), `GRAPH_REPORT.md`, and an interactive HTML viz.

**Multiple targets (cross-repo merge)**

Per Graphify's cross-repo flow — per-target runs write into each target's own `graphify-out/`, so they never clobber each other:

1. GitHub URL targets → `graphify clone <url>` each (clones into `~/.graphify/repos/<owner>/<repo>`, reused on repeat runs), then run the full pipeline on each cloned path.
2. Local folder targets → `graphify extract <path>` per folder (the CLI writes `<path>/graphify-out/graph.json` inside the scanned path — do NOT run the skill pipeline per folder; it writes to the CWD's `graphify-out/` and clobbers). Code-only corpora need no API key; pass `--backend` only if the user already has a key set.
3. Merge at the project root — `graphify merge-graphs <t1>/graphify-out/graph.json <t2>/graphify-out/graph.json ... --out graphify-out/graph.json`. Use exactly `graphify-out/graph.json` as the out path: that is the location the query fast path checks.

Merged nodes carry a `repo` attribute, so queries can filter by origin. The merged `graph.json` is the queryable artifact; each target keeps its own `GRAPH_REPORT.md` + HTML viz from its run.

### 4. Report + point later questions at the graph

Tell the user where the map lives (`graphify-out/` — plus, for multi-target runs, each target's own `graphify-out/`). From now on, codebase questions should query the graph first (per the Graphify skill's fast path: if `graphify-out/graph.json` exists, run `graphify query "<question>"` before re-reading files; multi-target graphs answer with `repo`-filtered queries).

## References

- cross-ref (no file-map edge): https://github.com/Graphify-Labs/graphify — the external tool this skill drives; install + usage.
- cross-ref (no file-map edge): `~/.claude/skills/graphify/SKILL.md` — the Graphify skill whose pipeline step 3 follows when present.
- cross-ref (no file-map edge): `~/.claude/skills/graphify/references/github-and-merge.md` — the clone / extract / merge-graphs cross-repo flow step 3 follows for multi-target runs.

## Writes To

- (no file-map edge) `graphify-out/` at the project root — graph.json (the merged cross-repo graph for multi-target runs), GRAPH_REPORT.md, HTML viz (step 3); multi-target runs also write each extra target's own `graphify-out/` inside that target.

## Role & Boundary (Read Before Editing)

This skill owns the optional Graphify map: the install check, the preference ask (default prefer), mapping one or more targets (project root + extra GitHub URLs / sibling folders, merged into one graph), and pointing later questions at the graph. It does NOT own the Graphify pipeline itself (the external skill / CLI does), does NOT query the graph during normal work (any skill may use its fast path), and does NOT install Graphify without asking. For anything outside this boundary, see the Responsibility map in workflow/SKILL.md.
