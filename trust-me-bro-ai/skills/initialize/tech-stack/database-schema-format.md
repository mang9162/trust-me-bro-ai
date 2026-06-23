# Database Schema

Target: `tech-stack/database-schema.md` — create/update this file from the format below.

## How to use
Read this for the physical schema of each datastore the project uses — its tables/collections, columns/fields, types, keys, relationships, and indexes — plus what each datastore is for and how it is seeded. You get structure + purpose + how-to-seed — NOT values or value shapes (those live in `data.md` `format`).

## How to scan (when filling this file)
Read the project's schema source per datastore — migrations, ORM models/entities, schema/DDL files, or the running DB. Don't assume a stack: create one `## <database>` section for each datastore the repo actually uses.
1. **Per datastore** — record the engine (`type`), what the datastore is FOR (`description`: which service / domain it belongs to and why it exists — NOT a list of its tables), and how the project seeds it (`seeding`, written once for the whole datastore: which seed file + mechanism + caveat). **If you can't tell what a datastore is for, ask the user — don't guess its purpose.**
2. **Per table/collection** — catalog the columns/fields with their `type`, `key` (PK/FK), and `relationship` (the FK target, as `table.column`), then list the table's indexes below it.

Fill per scan mode: light = datastores + table/collection names only; full = also columns/types/keys/relationships + indexes + `description` + `seeding`.
Don't guess — leave a cell `TBD` rather than invent a value.

## Format
- **One `## <database>` section per datastore** (e.g. one for the relational DB, one for the document DB, one for the cache). Split by engine, not by feature.
- Each section opens with three lines — `type`, `description`, `seeding` — then one `### <table/collection>` block per entity.
- `description` is the datastore's **purpose**: which service / domain it belongs to and why it exists — never a restatement of the tables inside it (those are listed below).
- **One row per column/field.** `key` = `PK` / `FK` / `—`. `relationship` = the FK target as `table.column`, or `—`.
- **`Indexes:` below each table** — one bullet per index: its name + the column(s) it covers + whether unique. `—` if the table has none.
- `seeding` is written **once per `## <database>` section** — how this whole datastore is seeded (its seed file e.g. `postgres.json` + mechanism + any caveat). Never per table. The `01-Testdata/db/` path itself is owned by the workflow `## Layout` — don't repeat it here.

Template — repeat one `## <database>` section per datastore, fill like this:

## <database>
- type: <engine + version>
- description: <which service / domain this datastore belongs to and why it exists — its purpose, not the tables inside>
- seeding: <seed file (e.g. `postgres.json`)> → <mechanism, e.g. ORM hook / init script> · caveat: <e.g. volume is wiped on teardown — reseed each run, or —>

### <table / collection>
| column | type | key | relationship |
|---|---|---|---|
| `<column>` | `<type>` | PK / FK / — | `<table.column>` or — |

Indexes:
- `<index name>` — `(<column(s)>)` <unique / —>

## Role & Boundary (Read Before Editing)
This file holds the physical DB schema per datastore (tables/collections, columns/fields, types, keys, relationships, indexes), what each datastore is for, and how it is seeded. It is what a `data.md` `ref` of `table.column` resolves to. It does NOT hold test-data variable names or value shapes (`data.md`), nor request/response payloads (`gateway-contract.md`). It is read-only to every workflow stage: a missing or conflicting column goes to `self-report`, never edited from a stage.
