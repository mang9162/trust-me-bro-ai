#!/usr/bin/env python3
"""taskctl.py — task-file tooling for the shared task schema (skills/maintenance/task-schema.md).

Subcommands:
  scaffold <spec.json> <out-dir>
      Expand a minimal task spec into a full task file: id/status/depends_on/assume/effort
      defaults, folder inferred from type, then validate. Writes <out-dir>/<id>.json.
      Spec fields: id (NN-slug-type), type, title, purpose, targets, and the type's
      conditional fields (contract / cases / pseudocode / uses / command / acceptance /
      notes / effort / depends_on / assume / folder).

  status <task.json> <status>
      Advance one task: pending -> in_progress (stamps startedAt) -> done|failed (stamps
      finishedAt). Rejects invalid transitions. Rewrites the file in place.

  validate <task.json>
      Check a task file against the schema without changing it. Exit 1 on problems.

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
ID_RE = re.compile(r"^(00-(env-setup|check-test)|\d{2}-[a-z0-9-]+-(env-setup|interface|error-code|seed|stub|env-config|unit-test|integration-test|component-test|code-task|api-test|regression))$")


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
    if "id" in t and not ID_RE.match(t["id"]):
        problems.append(f"id does not match NN-slug-type: {t['id']}")
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


def expand(spec):
    t = dict(spec)
    typ = t.get("type", "")
    if "folder" not in t:
        t["folder"] = FOLDER_BY_TYPE.get(typ, "02-Backlog")
    if "status" not in t:
        t["status"] = "pending"
    if "depends_on" not in t:
        t["depends_on"] = [] if t.get("id") == "00-env-setup" else ["00-env-setup"]
    if "assume" not in t:
        t["assume"] = "00-env-setup ran: seeds applied per Datatest.md, env ready" if t.get("depends_on") else "none"
    if "effort" not in t:
        t["effort"] = "low"
    return t


def cmd_scaffold(spec_path, out_dir):
    spec = json.loads(Path(spec_path).read_text())
    if "id" not in spec:
        sys.exit("spec requires id (NN-slug-type)")
    t = expand(spec)
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
    if len(sys.argv) < 2 or sys.argv[1] not in {"scaffold", "status", "validate"}:
        print(__doc__)
        sys.exit(1)
    op, rest = sys.argv[1], sys.argv[2:]
    if op == "scaffold" and len(rest) == 2:
        cmd_scaffold(rest[0], rest[1])
    elif op == "status" and len(rest) == 2:
        cmd_status(rest[0], rest[1])
    elif op == "validate" and len(rest) == 1:
        cmd_validate(rest[0])
    else:
        print(__doc__)
        sys.exit(1)
