# Testing Guide

Target: `tech-stack/testing-guide.md` — create/update this file from the format below.

## How to use

Read this for THIS project's test conventions — the test + stub folder layout, and for each service's test levels: the tool it uses, the command that runs it, where its files live and how they're named, the in-file layout, and the rules it must follow — plus how each service builds its stubs/mocks per technology. create-task reads it to set a test task's `targets.at` (its place in the test structure); default-tdd reads it to write and run the test the project's way. Code conventions for the implementation under test live in `code-standards.md`, not here.

## How to scan (when filling this file)

Read the repo's own tests and stub setup — the test folder(s), a few real test files per level, the test-runner config, and the mock-server / stub config. Don't assume a stack: record only the tools and patterns the repo actually uses.

1. **Test Structure** — map the test + stub folder tree (where test files and stub files live).
2. **Per service, per test level** — for each service (from tech-stack.md), for each level it runs (unit / integration / component / api-test), capture its tool, the command that runs it, file path + naming, in-file layout, and rules.
3. **Stub / Mock** — per service, for each stub/mock technology it uses, how it intercepts, the shape of a stub file, and the filename pattern.

Whatever the scan mode, fill as much as you can — every field of every level; a half-filled file breaks the stages that read it.
Don't guess — leave a value `TBD` or ask the user rather than invent one.

## Format

The target file has these sections, in order.

## Test Structure

The test + stub/mock folder tree — where test files and stub files live across the repo. A tree, then a line per key directory.

```text
<test / stub folder tree — the real top-level test dirs + stub dirs>
```

- `<key test/stub directory>` — <what it holds>

## Test Levels

Grouped by service: one `### <service>` block per service that has its own test suite (the services in tech-stack.md) — always wrap, even a single-service project. Within each, one `#### <level>` block per test level that service runs — omit a level (or a whole service) it doesn't use.

### <service>   (a service from tech-stack.md with its own tests — e.g. front · back)

#### <level>   (unit | integration | component | api-test)

- definition: <what this level covers here — e.g. unit = pure, no I/O · integration = real DB / gateway / cache · component = collaborators mocked, no real I/O · api-test = the real services started, internal calls hit the real services, only outside-project deps mocked>
- tool: `<runner / framework>`   (e.g. jest · vitest · JUnit · api-test: newman / bruno (back) · playwright (front))
- command: `<command that runs this level's tests>`   (e.g. `jest --selectProjects unit`)
- path: `<this level's file location + naming>`   (e.g. beside source as `<name>.unit.spec.ts`)
- layout: <the in-file shape>   (e.g. one `describe` per function, one `it` per case)
- rules: one bullet per hard rule for this level   (e.g. component = mock collaborators only, no supertest · api-test = only outside-project deps are mocked; internal calls hit the real running services)

## Stub / Mock

Grouped by service: one `### <service>` block per service that builds stubs/mocks (the same services as Test Levels) — always wrap, even a single-service project. Within each, one `#### <technology>` block per stub/mock tool that service uses — a service may use several (e.g. an HTTP stub server plus a mock WS server).

### <service>   (a service from tech-stack.md with its own stubs — e.g. front · back)

#### <technology>   (e.g. mountebank · WireMock · nock · a mock WS server)

- used for: <which outbound this fakes — e.g. HTTP outbound / queue publish / WS push>
- approach: <how it intercepts a call — e.g. an HTTP stub server matched by request predicates returning canned responses>
- shape: <the structure of one stub file — e.g. `{ predicates, responses }`>
- filename: `<the stub filename pattern>`

## Role & Boundary (Read Before Editing)

This file holds THIS project's test conventions — the test + stub folder structure, each service's test levels (unit / integration / component / api-test) with their tool, run command, file path + naming, in-file layout, and rules, and how each service's stubs/mocks are built per technology. It is the single home for the project's test conventions: if the project has further test-related structure the sections above don't cover (e.g. e2e / smoke setup, shared fixtures or test-data factories, coverage or CI test-gating rules), add it here under its own heading. Anything that isn't a test convention, don't edit it here — change it in the file that owns it instead: code conventions / hard rules in `code-standards.md`, the stack / services / build-run commands in `tech-stack.md`, request/response payload shapes in `gateway-contract.md`.
