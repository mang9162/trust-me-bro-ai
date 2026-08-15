#!/usr/bin/env python3
"""self-report.py — mechanical half of self-report: write self-learn entry files.

Handles the schema + dedup + file write for `{small,medium,heavy}-learn.js` (kind:
problem | candidate) and `tech-debt.js` (kind: issue), per the self-report SKILL.md.
The classification (tier, which kind, wording) stays with the agent; this script
only emits entries consistently.

Files are JS modules of the form `var <NAME> = [ ...json objects... ];` — the script
extracts the array, appends/updates, and re-emits, preserving unrelated content.

Usage:
  python3 self-report.py add <file.js> --kind issue --title T --problem P [--places a,b] [--reported-by NAME] [--note TEXT]
  python3 self-report.py list <file.js>

Dedup: an existing entry with the same `problem` text gets an appended `occurrences`
entry instead of a duplicate (matching the skill's dedup rule).
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

VAR_RE = re.compile(r"var\s+([A-Z_]+)\s*=\s*(\[[\s\S]*?\])\s*;", re.M)


def read_entries(path: Path):
    """Return (var_name, entries, head, tail) preserving the file around the array."""
    text = path.read_text() if path.exists() else ""
    m = VAR_RE.search(text)
    if not m:
        return None, [], "", text
    var, arr = m.group(1), m.group(2)
    entries = json.loads(arr)
    head = text[:m.start(2)]
    tail = text[m.end(2):]
    return var, entries, head, tail


def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:60]


def cmd_add(path_str, kwargs):
    path = Path(path_str)
    var, entries, head, tail = read_entries(path)
    if var is None:
        sys.exit(f"{path}: no `var NAME = [...]` array found; not a self-learn file")
    kind = kwargs.get("kind")
    if kind not in {"issue", "problem", "candidate"}:
        sys.exit("kind must be issue | problem | candidate")
    title = kwargs.get("title") or ""
    problem = kwargs.get("problem") or ""
    if not title or not problem:
        sys.exit("title and problem are required")
    reported_by = kwargs.get("reported_by") or "self-report"
    today = date.today().isoformat()
    entry = {
        "id": f"{today.replace('-', '')}-{slugify(title)}",
        "kind": kind,
        "status": "pending",
        "firstSeen": today,
        "reportedBy": reported_by,
        "title": title,
        "problem": problem,
    }
    if kind == "issue":
        entry["places"] = [p for p in (kwargs.get("places") or "").split(",") if p.strip()]
    occurrence = {"date": today, "by": reported_by}
    if kwargs.get("note"):
        occurrence["note"] = kwargs["note"]
    for existing in entries:
        if existing.get("problem") == problem:
            existing.setdefault("occurrences", []).append(occurrence)
            print(f"{path}: appended occurrence to existing entry {existing['id']}")
            break
    else:
        entry["occurrences"] = [occurrence]
        entries.append(entry)
        print(f"{path}: added entry {entry['id']}")
    body = "var " + var + " = " + json.dumps(entries, indent=2, ensure_ascii=False) + ";\n"
    path.write_text(head + body + tail)


def cmd_list(path_str):
    var, entries, _, _ = read_entries(Path(path_str))
    if var is None:
        sys.exit(f"{path_str}: no self-learn array found")
    for e in entries:
        print(f"{e.get('id')} [{e.get('kind')}] {e.get('title')} - occurrences: {len(e.get('occurrences', []))}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2 or args[0] not in {"add", "list"}:
        print(__doc__)
        sys.exit(1)
    op, rest = args[0], args[1:]
    if op == "add":
        path = rest[0]
        kv = {}
        i = 1
        while i < len(rest):
            if rest[i].startswith("--"):
                key = rest[i][2:].replace("-", "_")
                kv[key] = rest[i + 1]
                i += 2
            else:
                i += 1
        cmd_add(path, kv)
    else:
        cmd_list(rest[0])
