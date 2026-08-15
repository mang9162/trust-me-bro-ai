#!/usr/bin/env python3
"""init-kit.py — mechanical half of initialize: create the knowledge targets from the format templates.

Implements the initialize SKILL.md Phase-3 mechanics:
- for each *-format.md under skills/initialize/{context,tech-stack}/
- parse its `Target: <path>` line (resolves relative to the kit root, i.e. the folder containing skills/)
- strip the `Target:` line and the `## How to scan (when filling this file)` section
- write the target file if it does NOT exist (existing targets are never overwritten here —
  updates follow the target's own format and are the agent's job)

The semantic scan + filling stays with the agent (per the skill). This script only removes
the ~3KB of per-file boilerplate the agent would otherwise re-emit on first creation.

Usage:
  python3 init-kit.py <kit-root> [--dry-run]

<kit-root> = the folder that contains `skills/` (e.g. `trust-me-bro-ai/`).
Exit code 1 if a template has no Target: line or its target is malformed.
"""

import re
import sys
from pathlib import Path

TEMPLATE_GLOBS = ["skills/initialize/context/*-format.md", "skills/initialize/tech-stack/*-format.md"]
TARGET_RE = re.compile(r"^Target:\s*`([^`]+)`", re.M)


def strip_template(text):
    """Remove the Target: line and the '## How to scan (when filling this file)' section."""
    lines = text.splitlines(keepends=True)
    out, skipping = [], False
    for line in lines:
        if line.startswith("Target: `"):
            continue  # initialize-only marker
        if line.strip() == "## How to scan (when filling this file)":
            skipping = True
            continue
        if skipping and line.startswith("## "):
            skipping = False
        if not skipping:
            out.append(line)
    return "".join(out)


def process(kit_root: Path, dry_run: bool):
    created, skipped, errors = [], [], []
    for glob in TEMPLATE_GLOBS:
        for tmpl in sorted(kit_root.glob(glob)):
            m = TARGET_RE.search(tmpl.read_text())
            if not m:
                errors.append(f"{tmpl.relative_to(kit_root)}: no Target: line")
                continue
            rel = m.group(1)
            target = (kit_root / rel).resolve()
            # target must stay inside the kit root
            if not str(target).startswith(str(kit_root.resolve())):
                errors.append(f"{tmpl.relative_to(kit_root)}: target escapes kit root: {rel}")
                continue
            if target.exists():
                skipped.append(rel)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if not dry_run:
                target.write_text(strip_template(tmpl.read_text()))
            created.append(rel)
    for rel in created:
        print(f"created  {rel}{' (dry-run)' if dry_run else ''}")
    for rel in skipped:
        print(f"exists   {rel} (left untouched)")
    for e in errors:
        print(f"ERROR    {e}")
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or any(a in ("-h", "--help") for a in args):
        print(__doc__)
        raise SystemExit(0 if args else 1)
    dry = "--dry-run" in args
    roots = [a for a in args if not a.startswith("--")]
    if not roots:
        print(__doc__)
        raise SystemExit(1)
    code = 0
    for r in roots:
        code |= process(Path(r), dry)
    raise SystemExit(code)
