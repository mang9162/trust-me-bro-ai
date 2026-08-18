---
name: graphify-map
description: Map the whole project into a queryable knowledge graph with Graphify — check whether Graphify is installed, ask the user if they prefer it (default: prefer), and when opted in run it on the project root to produce graphify-out/ (graph.json + GRAPH_REPORT.md + HTML viz) that later questions can query first.
---

# Graphify Map

## Purpose

Build a knowledge graph of the entire project with Graphify (https://github.com/Graphify-Labs/graphify) so later codebase questions (architecture, file relationships, data flow) are answered from the graph instead of re-scanning the repo. Optional by design — it only runs when Graphify is installed AND the user prefers it (default: prefer).

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

On the project root (the repo being mapped, never the kit folder), run the Graphify pipeline:

- Graphify skill present → follow its full pipeline (detect → extract → cluster → report → viz).
- CLI only → `graphify .` (full pipeline; add `--mode deep` for richer INFERRED edges on big repos).

Output lands in `graphify-out/` at the project root: `graph.json` (GraphRAG-ready), `GRAPH_REPORT.md`, and an interactive HTML viz.

### 4. Report + point later questions at the graph

Tell the user where the map lives (`graphify-out/`). From now on, codebase questions should query the graph first (per the Graphify skill's fast path: if `graphify-out/graph.json` exists, run `graphify query "<question>"` before re-reading files).

## References

- cross-ref (no file-map edge): https://github.com/Graphify-Labs/graphify — the external tool this skill drives; install + usage.
- cross-ref (no file-map edge): `~/.claude/skills/graphify/SKILL.md` — the Graphify skill whose pipeline step 3 follows when present.

## Writes To

- (no file-map edge) `graphify-out/` at the project root — graph.json, GRAPH_REPORT.md, HTML viz (step 3).

## Role & Boundary (Read Before Editing)

This skill owns the optional whole-project Graphify map: the install check, the preference ask (default prefer), running the pipeline on the project root, and pointing later questions at the graph. It does NOT own the Graphify pipeline itself (the external skill / CLI does), does NOT query the graph during normal work (any skill may use its fast path), and does NOT install Graphify without asking. For anything outside this boundary, see the Responsibility map in workflow/SKILL.md.
