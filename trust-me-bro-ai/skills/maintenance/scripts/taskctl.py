#!/usr/bin/env python3
"""taskctl.py — task-file tooling for the shared task schema (skills/maintenance/task-schema.md).

Subcommands:
  scaffold <spec.json> <out-dir> [--lane scenario|issue]
      Expand a minimal task spec into a full task file: id/status/depends_on/assume/effort
      defaults (lane-aware: scenario uses 00-env-setup, issue uses 00-check-test), folder
      inferred from type, then validate. Writes <out-dir>/<id>.json.
      Spec fields: id (NN-slug-type, suffix must equal type), type, title, purpose, targets,
      and the type's conditional fields (contract / cases / pseudocode / uses / command /
      acceptance / notes / effort / depends_on / assume / folder).

  status <task.json> <status>
      Advance one task: pending -> in_progress (stamps startedAt) -> done|failed (stamps
      finishedAt). Rejects invalid transitions. Rewrites the file in place.

  validate <task.json>
      Check a task file against the schema without changing it. Exit 1 on problems.

  deps <task-dir>
      Deadlock detector: every pending task's depends_on must exist and be done. Exit 1
      listing {task, dep, why} otherwise (execute-tdd would DEADLOCK).

The schema itself stays the source of truth in task-schema.md; this script only enforces
it mechanically so authoring/close-out stop re-emitting boilerplate and stop shipping
malformed tasks.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TYPES = {"unit-test", "integration-test", "component-test", "code-task", "api-test",
         "env-setup", "interface", "error_code", "seed", "stub", "env-config", "regression"}
FOLDER_BY_TYPE = {"unit-test": "02-Backlog", "integration-test": "02-Backlog", "component-test": "02-Backlog",
                  "code-task": "02-Backlog", "api-test": "03-Api-test", "env-setup": "01-Setup",
                  "interface": "01-Setup", "error_code": "01-Setup", "seed": "01-Setup",
                  "stub": "01-Setup", "env-config": "01-Setup", "regression": "02-Backlog"}
CONDITIONAL = {"contract": {"interface", "code-task", "unit-test", "integration-test", "component-test", "api-test"},
               "cases": {"unit-test", "integration-test", "component-test", "api-test"},
               "pseudocode": {"unit-test", "integration-test", "component-test", "code-task"},
               "uses": {"unit-test", "integration-test", "component-test", "api-test", "seed", "stub"},
               "command": set(TYPES) - {"interface"},
               "acceptance": set(TYPES) - {"interface", "error_code", "seed", "stub", "env-config"}}
REQUIRED = {"id", "type", "status", "title", "purpose", "targets", "depends_on", "assume"}
FIXED_IDS = {"00-env-setup", "00-check-test"}


def id_ok(t):
    tid = t.get("id", "")
    if tid in FIXED_IDS:
        return True
    typ = t.get("type")
    # NN-slug-<type>: the trailing suffix must equal the task's own type field
    return bool(typ) and tid.endswith("-" + typ) and bool(re.fullmatch(r"\d{2}-[a-z0-9_-]+", tid))


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def validate(t):
    problems = []
    for f in REQUIRED:
        if f not in t:
            problems.append(f"missing required field: {f}")
    if "type" in t and t["type"] not in TYPES:
        problems.append(f"unknown type: {t['type']} (known: {sorted(TYPES)})")
    if "status" in t and t["status"] not in {"pending", "in_progress", "done", "failed"}:
        problems.append(f"bad status: {t['status']}")
    if "effort" in t and t["effort"] not in {"low", "med", "high"}:
        problems.append(f"bad effort: {t['effort']}")
    if "id" in t and not id_ok(t):
        problems.append(f"id does not match NN-slug-<type> (suffix must equal the type field): {t.get('id')}")
    if "targets" in t:
        if not isinstance(t["targets"], list) or not t["targets"]:
            problems.append("targets must be a non-empty list")
        for x in (t["targets"] if isinstance(t["targets"], list) else []):
            if not isinstance(x, dict) or not all(k in x for k in ("path", "mode")):
                problems.append(f"target entry missing path/mode: {x}")
            elif x.get("mode") not in {"create", "modify"}:
                problems.append(f"target mode must be create|modify: {x}")
    if "depends_on" in t and not isinstance(t["depends_on"], list):
        problems.append("depends_on must be a list")
    typ = t.get("type")
    for field, types in CONDITIONAL.items():
        if typ in types and field not in t:
            problems.append(f"type {typ} requires field: {field}")
    if t.get("type") in {"unit-test", "integration-test", "component-test", "api-test"} and "cases" in t and not t["cases"]:
        problems.append("cases must be non-empty")
    if "command" in t and t.get("command") == "TBD":
        problems.append("command must not be a literal TBD placeholder")
    return problems


LANES = {
    "scenario": {"dep": "00-env-setup", "assume": "00-env-setup ran: seeds applied per Datatest.md, env ready"},
    "issue": {"dep": "00-check-test", "assume": "00-check-test ran: baseline green, env ready"},
}


def expand(spec, lane="scenario"):
    t = dict(spec)
    typ = t.get("type", "")
    if "folder" not in t:
        t["folder"] = FOLDER_BY_TYPE.get(typ, "02-Backlog")
    if "status" not in t:
        t["status"] = "pending"
    if "depends_on" not in t:
        t["depends_on"] = [] if t.get("id") in FIXED_IDS else [LANES[lane]["dep"]]
    if "assume" not in t:
        t["assume"] = LANES[lane]["assume"] if t.get("depends_on") else "none"
    if "effort" not in t:
        t["effort"] = "low"
    return t


def cmd_scaffold(spec_path, out_dir, lane="scenario"):
    spec = json.loads(Path(spec_path).read_text())
    if "id" not in spec:
        sys.exit("spec requires id (NN-slug-type)")
    t = expand(spec, lane)
    problems = validate(t)
    if problems:
        print("validation failed:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    out = Path(out_dir) / t["folder"]
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{t['id']}.json"
    dest.write_text(json.dumps(t, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {dest}")


def cmd_status(task_path, new_status):
    if new_status not in {"in_progress", "done", "failed"}:
        sys.exit(f"status must be in_progress|done|failed, got {new_status}")
    p = Path(task_path)
    t = json.loads(p.read_text())
    cur = t.get("status", "pending")
    allowed = {"pending": {"in_progress"}, "in_progress": {"done", "failed"}}
    if new_status not in allowed.get(cur, set()):
        sys.exit(f"invalid transition {cur} -> {new_status}")
    t["status"] = new_status
    if new_status == "in_progress":
        t["startedAt"] = t.get("startedAt") or now_iso()
    else:
        t["finishedAt"] = now_iso()
    p.write_text(json.dumps(t, indent=2, ensure_ascii=False) + "\n")
    print(f"{t['id']}: {cur} -> {new_status} ({p})")


def cmd_deps(task_dir):
    """Deadlock detector: every pending task's depends_on must exist and be done."""
    files = sorted(Path(task_dir).rglob("*.json"))
    tasks = {}
    for f in files:
        try:
            t = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(t, dict) and "id" in t:
            tasks[t["id"]] = t
    problems = []
    pending = 0
    for tid, t in sorted(tasks.items()):
        if t.get("status") != "pending":
            continue
        pending += 1
        for d in t.get("depends_on", []):
            if d not in tasks:
                problems.append((tid, d, "missing (typo or not authored)"))
            elif tasks[d].get("status") != "done":
                problems.append((tid, d, f"not done ({tasks[d].get('status')})"))
    if problems:
        for tid, d, why in problems:
            print(f"{tid}: depends_on {d} -> {why}")
        sys.exit(1)
    print(f"queue runnable: {pending} pending task(s), all depends_on done")


def cmd_validate(task_path):
    t = json.loads(Path(task_path).read_text())
    problems = validate(t)
    if problems:
        print(f"{task_path}: INVALID")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print(f"{task_path}: ok")


if __name__ == "__main__":
    if len(sys.argv) < 2 or any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__)
        raise SystemExit(0 if len(sys.argv) > 1 else 1)
    if sys.argv[1] not in {"scaffold", "status", "validate", "deps"}:
        print(__doc__)
        sys.exit(1)
    op, rest = sys.argv[1], sys.argv[2:]
    if op == "scaffold" and len(rest) >= 2:
        lane = "issue" if "--lane" in rest and rest[rest.index("--lane") + 1] == "issue" else "scenario"
        positional = [a for a in rest if not a.startswith("--")]
        cmd_scaffold(positional[0], positional[1], lane)
    elif op == "status" and len(rest) == 2:
        cmd_status(rest[0], rest[1])
    elif op == "validate" and len(rest) == 1:
        cmd_validate(rest[0])
    elif op == "deps" and len(rest) == 1:
        cmd_deps(rest[0])
    else:
        print(__doc__)
        sys.exit(1)
