# Tech Stack

Target: `tech-stack/tech-stack.md` — create/update this file from the format below.

## How to use

Read this for THIS project's stack and shape — what it is built with, the architectural pattern its code follows, where source files live, how to run / build / test it, and how its local + test environment comes up. create-task reads the **Architecture Pattern** to shape the functional call tree and the **Project Structure** to place code files.

This file is the overview. The detail of each area lives in its own sibling file — don't restate schema / payloads / code rules / test conventions here.

## How to scan (when filling this file)

Read the repo itself — the package/build manifest (dependencies + scripts), the source tree, config files (container compose, env examples), and the mock/stub config. Don't assume a stack: record only what the repo actually uses.

1. **Primary Stack** — languages, runtime, frameworks, key libraries/tools, grouped by layer.
2. **Architecture Pattern** — the layering / call pattern the code follows (how a call flows through the layers, and what kind of function lives in each layer).
3. **Project Structure** — the source folder tree + what each key directory holds.
4. **Commands** — the run / build / test commands from the manifest scripts (+ any caution).
5. **Infrastructure** — the services the running system needs, plus how the local + test/api-test environment comes up (env vars, containers). The stub/mock mechanism and test-file placement are NOT here — they live in `testing-guide.md` (see References).

Whatever the scan mode, fill as much as you can — a half-filled file breaks the stages that read it.
Don't guess — leave a value `TBD` or ask the user rather than invent one.

## Format

The target file has these sections, in order. Keep each lean — it is an overview that points to siblings, not a copy of them.

## Primary Stack

One row per technology, grouped by layer. `layer` = its role (e.g. language / runtime / framework / datastore / testing / infra).

| layer | technology | version |
| --- | --- | --- |
| `<layer>` | `<technology>` | `<version or —>` |

## Architecture Pattern

- type: <Monolith | Microservices | Serverless | Agent-based | Hybrid>
- pattern: <the call/layering pattern the code follows, e.g. how a request flows through the layers>
- layers: one bullet per layer — `<layer>` — <its responsibility / what kind of function lives here>
- diagram: <pointer to an architecture diagram/doc if one exists, or —>

## Project Structure

```text
<source folder tree — the real top-level + key sub-folders>
```

- `<key directory>` — <what it holds>  (where code/test files live → a code task's `targets.path`)

## Commands

One row per command the project exposes (run / build / test / lint).

| command | does |
| --- | --- |
| `<command>` | <what it runs> |

- caution: <any command that is destructive / slow / needs prior setup, or —>

## Infrastructure

How the running system comes up: the services it runs, plus how to start it locally and for tests. Keep it scannable — short fields and a list, not prose paragraphs.

### Services

The processes/containers that make up the running system — one bullet per service.

- `<service>` — port `<port or —>` — <what it is / what it's for>

### Local run

- bring-up: `<command(s) to start everything — e.g. compose up, then the app start command>`
- env: `<env file + key vars, one NAME=example per line>`

### Test run

- target env: `<the separate test datastore / config the tests point at>`
- lifecycle: `<setup → teardown — e.g. truncate + seed before a run, close the pool after>`

## References

- bridge: `testing-guide.md` — owns the stub/mock mechanism (stub-file template + folder layout) and where test files live. tech-stack only names the services and how to run them; for anything stub- or test-placement-related, go there.

## Role & Boundary (Read Before Editing)

This file is THIS project's stack + shape overview — what it is built with (Primary Stack), the architectural pattern (Architecture Pattern), where source lives (Project Structure), how to run / build / test it (Commands), and the services it runs plus how its local + test environment comes up (Infrastructure). It is what create-task reads to shape the call tree and place files. It does NOT hold DB schema (`database-schema.md`), request/response payloads (`gateway-contract.md`), code conventions / hard rules (`code-standards.md`), test conventions / placement and the stub/mock mechanism (`testing-guide.md`), or which gateway lines exist (`gateway-directory.md`); each of those is its own sibling file. It is read-only to every workflow stage: a missing or conflicting entry goes to `self-report`, never edited from a stage.
