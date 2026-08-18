#!/usr/bin/env python3
"""export-requests.py — mechanical half of Stage 5 api-test: emit project-side request definitions.

Reads a scenario folder's 03-Api-test/*.json task files and serializes each request
(task id, title, contract, cases, uses) into a machine-consumable definition file —
the artifact a future api-test harness (INITIALIZE_API_TEST_SETUP) runs against.

The semantic part stays with the agent: what the requests ARE comes from create-task;
this script only re-serializes what was already authored, so nothing is re-typed.

Usage:
  python3 export-requests.py <scenario-folder> <out-dir>
  python3 export-requests.py --all <work-root> <out-dir>
"""

import json
import sys
from pathlib import Path


def export(folder: Path, out_dir: Path):
    tdir = folder / "02-Task" / "03-Api-test"
    tasks = sorted(tdir.glob("*.json")) if tdir.exists() else []
    if not tasks:
        print(f"{folder}: no 03-Api-test tasks, skipped")
        return
    requests = []
    for f in tasks:
        t = json.loads(f.read_text())
        requests.append({"task_id": t["id"], "title": t["title"], "contract": t["contract"],
                         "cases": t.get("cases", []), "uses": t.get("uses", {}), "effort": t.get("effort", "low")})
    out = out_dir / f"{folder.name}.requests.json"
    out.write_text(json.dumps({"scenario": folder.name, "requests": requests}, indent=2, ensure_ascii=False))
    print(f"{folder.name}: {len(requests)} request(s) -> {out}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or any(a in ("-h", "--help") for a in args):
        print(__doc__)
        raise SystemExit(0 if args else 1)
    if (args[0] == "--all" and len(args) < 3) or (args[0] != "--all" and len(args) < 2):
        print(__doc__)
        sys.exit(1)
    if args[0] == "--all":
        folders = sorted(p.parent for p in Path(args[1]).rglob("scenario.html"))
        out_dir = Path(args[2])
    else:
        folders = [Path(args[0])]
        out_dir = Path(args[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in folders:
        export(f, out_dir)
