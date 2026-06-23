# Domain Reference

Target: `context/domain-reference.md` — create/update this file from the format below.

## How to use
Read this for the project's domain at a glance: what it is, who acts in it (and what they expect), the vocabulary its requirements use, and how scenarios are named. A project can add its own sections here as its domain needs.

## How to scan (when filling this file)
- **Domain Overview** — read the README / top-level docs / main modules to state what the project is and the problem it solves. List the domain's roles/actors (from auth roles, user types, or the actors named across requirements) with what they do and expect. If you can't tell what the project is for, ask the user — don't guess.
- **Core Terms** — collect the domain words that recur in requirements / module names / docs; define each as it's used here.
- **Scenario Naming** — read existing scenario/test names for the pattern; if none exists, ask the user for the convention.
- Don't guess — leave a cell `TBD` rather than invent a value.

## Domain Overview
- **What it is** — one or two lines: what this project/domain does and the problem it solves.
- **Roles** — the actors in the domain (the people / systems a requirement or scenario acts as or for), what each does, and what a correct outcome looks like for them:

| role | what they do | what they expect |
|---|---|---|
| `<role>` | <their part in the domain> | <what a correct outcome looks like for them> |

## Core Terms
The domain vocabulary — each word a requirement might use and what it means *here* (not its generic dictionary sense). One row per term.

| term | meaning |
|---|---|
| `<Term>` | <what it means in this domain> |

## Scenario Naming
The project's convention for naming a scenario — the `<FULL_SCENARIO_NAME>` that the workflow's `## Layout` wraps as `<NN>-<FULL_SCENARIO_NAME>`. State the pattern and what each part means.
- pattern (default): `<FEATURE>_<SUB_FEATURE>_<RESULT_TYPE>` — or the project's own convention.
- `<FEATURE>` — the feature under test
- `<SUB_FEATURE>` — the area / sub-flow within that feature
- `<RESULT_TYPE>` — the outcome the scenario covers (e.g. a success path vs an alternative / error path)

## Role & Boundary (Read Before Editing)
This file is the project's domain overview — what it is, its roles/actors and their expectations, the Core Terms glossary, and the Scenario Naming convention. Add to it as the domain grows, but only **broad domain content** (new terms, roles, or domain-context sections). Anything that belongs to a sibling file — API request/response payloads (`gateway-contract.md`), DB schema (`database-schema.md`), or test-data values (`data.md`) — goes there, not here.
