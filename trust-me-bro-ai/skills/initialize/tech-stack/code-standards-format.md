# Code Standards

Target: `tech-stack/code-standards.md` — create/update this file from the format below.

## How to use

Read this for THIS project's code conventions and hard rules — how things are named, how code is formatted, the programming practices / idioms new code must follow, the language style guides it adheres to, the tools + commands that check compliance, and the non-negotiable hard rules.

## How to scan (when filling this file)

Read the repo's own code plus its tooling config — a few representative source files (for naming, formatting, and idioms), the linter / formatter / type-checker config, and any CONTRIBUTING / style doc. Most of this is scannable; the hard prohibitions usually are NOT — ask the user for those.

1. **Naming Conventions** — from the real symbols and filenames across the code: the casing each kind of thing uses.
2. **Formatting** — from the formatter config (prettier / editorconfig / lint style rules); if there's none, read it off the code.
3. **Programming Practices** — the idioms that recur across the code (error handling, transactions, logging, validation, …) — the patterns new code must match.
4. **Style Guides** — any language style guide the project declares (a lint preset it extends, a doc it cites). `—` if none.
5. **Tools & Automation** — the lint / format / type-check tools and the command that checks each.
6. **Hard Rules** — **ask the user**: the must / never rules that scanning the code can't reveal (e.g. never auto-format existing files, never edit `.env`).

Whatever the scan mode, fill as much as you can — a half-filled file breaks default-tdd, which reads it to write code.
Don't guess — leave a value `TBD` or ask the user rather than invent one.

## Format

The target file has these sections, in order. Omit a section the project genuinely has none of (e.g. no language style guide).

## Naming Conventions

One row per kind of thing the project names — the casing/pattern it uses. Add a row per case the project cares about (the user can extend this). Casing vocabulary: `camelCase` · `PascalCase` · `snake_case` · `kebab-case` · `UPPER_SNAKE`.

| applies to | convention | example |
| --- | --- | --- |
| `<kind — e.g. variable · function · class/type · file · constant · inbound API field · outbound API field>` | `<casing/pattern — e.g. camelCase>` | `<a short example, or —>` |

- inbound / outbound API field rows are the **casing rule** for payloads (e.g. inbound = `snake_case`, internal = `camelCase`) — NOT the actual field names or shapes (those live in `gateway-contract.md`).

## Formatting

The mechanical style — usually owned by a formatter. List the source of truth, then the values that matter (or `—` where the formatter owns it).

- source of truth: `<formatter + its config — e.g. prettier (.prettierrc) · .editorconfig>` or `—` (the rules below are the spec)
- indent: `<e.g. 2 spaces · tabs>`
- line length: `<e.g. 100>`
- brace style: `<e.g. 1TBS · Allman>`
- other: `<quotes · semicolons · trailing comma — the project's choices, or —>`

The command that enforces this lives in **Tools & Automation**.

## Programming Practices

One `### <practice>` block per recurring idiom new code must follow — the practices that reading a few files makes obvious. This is the section self-learn promotes a confirmed pattern into.

### <practice>   (e.g. error handling · transactions · logging · validation)

- rule: <what to always / never do — e.g. wrap in try/catch, log `<funcName>: <message>`, rethrow as the project's error type>
- why: <the reason — e.g. one consistent, traceable log line per failure>
- applies to: <where it's required — e.g. every service method that calls a gateway, or —>

## Style Guides

The external, language-level reference the code adheres to. One row per language. `—` for the whole section if the project follows none.

| language | style guide | reference |
| --- | --- | --- |
| `<language>` | `<guide — e.g. PEP 8 · Airbnb · Google Java · —>` | `<url / the lint preset it maps to, or —>` |

## Tools & Automation

The tools that enforce the standards above and the command to check each. These are the standards-check commands default-tdd runs after writing code — general build/run/test commands live in `tech-stack.md`.

| tool | enforces | command to check |
| --- | --- | --- |
| `<tool — e.g. eslint · prettier · tsc>` | `<which section — e.g. Programming Practices · Formatting · types>` | `<e.g. \`npm run lint\` · \`prettier --check .\` · \`tsc --noEmit\`>` |

## Hard Rules

One bullet per non-negotiable rule — what the AI must never / must always do, especially things scanning the code won't reveal. Get these from the **user**.

- `<NEVER | ALWAYS>` <the rule> — <why> (e.g. `NEVER` run a formatter/linter auto-fix across existing files · `NEVER` edit `.env` or commit secrets · `ALWAYS` <project obligation>)

## Role & Boundary (Read Before Editing)

This file holds THIS project's code conventions and hard rules — naming, formatting, programming practices / idioms, language style guides, the tools + check-commands that enforce them, and the non-negotiable hard rules. It is what default-tdd reads to write implementation code the project's way, and the promotion target for self-learn: a repeated pattern enters Programming Practices / Hard Rules only via the out-of-band self-learn review, after the user confirms. Anything that isn't a code convention or hard rule, don't add it here — put it in the file that owns it: the stack / project structure / general build-run-test commands in `tech-stack.md` (code-standards owns only the standards-check commands like lint / format / type-check), test conventions / levels / placement / stub mechanism incl. test-file naming in `testing-guide.md`, request/response field names + shapes in `gateway-contract.md` (Naming here is the casing rule, not the actual fields), DB schema in `database-schema.md`, domain meaning in `domain-reference.md`. It is read-only to every workflow stage: a new or conflicting convention goes to `self-report`, never edited from a stage.
