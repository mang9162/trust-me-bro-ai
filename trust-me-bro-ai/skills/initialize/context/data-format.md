# Data Dictionary

Target: `context/data.md` — create/update this file from the format below.

## How to use
Read this to find the canonical NAME of each test-data variable the project uses: which context it
belongs to (the `## <context>` group it sits under — picture an ER diagram at level 0: the domain
entity the data is about), where its value comes from (`ref`), and the shape to generate a value (`format`). You get names + shapes — NOT actual values. Each scenario fills in its
own values in `<case>/01-Testdata/Datatest.md`, picking the names from here.

## How to scan (when filling this file)
Organise by DOMAIN ENTITY (ER level 0), not by where the data is stored:
1. **Identify the contexts** — read the domain models / aggregates / main resources / any domain or ER docs for the top-level entities the domain is about. These become the `## <context>` sections. Don't make a section per table or datastore — that just duplicates `database-schema.md`.
2. **Catalog the variables** under each context — read whatever the stack exposes: DB columns (schema / migrations / models), request/response payload fields (gateway-contract lines, API types, external / 3rd-party payloads), and ids / tokens / codes handed between systems.
3. **Record the source** of each variable's value as `ref` — the source is only a bridge; it does NOT decide which context the variable belongs to.

Fill per scan mode: light = contexts + variable names only; full = also fill `description`, `ref`, `format`.
If you can't tell which context a variable belongs to, ask the user — don't guess the grouping.
Don't guess — leave a cell `TBD` rather than invent a value.

## Catalog
- **One `## <context>` section per group** — a domain entity (ER level 0): the subject the data is about, not where it comes from. A value's source is never the grouping — it lives only in `ref`, as a bridge.
  Optional `Related to:` list under the heading — the systems / datastores / externals this entity's data touches. Metadata only; it does NOT define the grouping (the entity itself does).
- **One row per variable.** Reuse the same `name` verbatim everywhere (Datatest.md, stubs, seeds) so they all resolve to one entry.
- `ref` — the **BRIDGE** to where the value physically comes from: a DB column → matches a column in `database-schema.md`; a request/response field → matches a line's payload in `gateway-contract.md`. It only points at the source — it does **NOT** say which entity the variable belongs to (the `## <context>` does).
- `format` is the value's *shape* for generating a fresh, non-colliding value — never a concrete value; `TBD` if not yet confirmed.
- `relate data` — the `name` of another entry IN this dictionary that is the same / equivalent datum (one value under different names). Just the name(s) — a direct cross-reference; `—` if none.

Template — repeat one `## <context>` section per group, fill each row like this:

## <context>
Related to:
- <source system / datastore / external>

| name | description | ref | format | relate data |
|---|---|---|---|---|
| `<variableName>` | <what the datum is> | `<source.field>` | <shape — e.g. `UUID v4` / `positive integer` / `one of: A, B` / `decimal, 2dp` / `TBD`> | <name of a related entry here, or —> |

## References
- bridge: `tech-stack/database-schema.md` — a `ref` pointing at a DB column must match a column there; a `format`/type mismatch is a `self-report` conflict.
- bridge: `tech-stack/gateway-contract.md` — a `ref` pointing at a request/response field matches that line's payload shape.

## Role & Boundary (Read Before Editing)
data.md is the central dictionary of test-data variable NAMES — it records which domain entity each piece of
data is about (its `## <context>` group — ER level 0) and where each value comes from (`ref`). It holds only
name + description + source bridge (`ref`) + value `format` + `relate data`; it NEVER holds actual values
(each scenario fills in its own in `Datatest.md`). Grouping is by domain entity, never by datastore — that
would just duplicate `database-schema.md`; `ref` is only a bridge to the source, never a claim of ownership.
It is read-only to every workflow stage: a new variable, or one whose definition conflicts with what is here,
goes to `self-report` — never edited from a stage. General domain knowledge → `domain-reference.md`;
request/response shapes → `gateway-contract.md`; real DB columns/types → `database-schema.md` (linked via `ref`).
