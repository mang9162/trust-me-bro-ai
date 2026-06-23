# Error Codes

Target: `context/error-codes.md` — create/update this file from the format below.

## How to use
Read this for how the service replies to inbound API requests: the standard response envelope (**base-response**) and the **registry** of error codes it can return. An error code lets the service say WHAT went wrong beyond HTTP 4xx/5xx. Use it to find the right existing code (or the next one in a group), a code's response/log message, and — via the **Severity** criteria — which level a new error should be. (A specific line's request/`data` shape lives in `gateway-contract.md`; this file holds the shared envelope + the code registry.)

## How to scan (when filling this file)
- **base-response** — read the project's shared response wrapper (a base controller / interceptor / response DTO/type) and record its **actual** shape:
  - matches the recommended standard below → record it.
  - exists but **diverges** from the standard → record the actual shape **and flag the divergence** (surface to the user / `self-report`) — don't overwrite reality with the standard, and don't silently adopt a divergent shape; let the user decide (align to the standard / keep the project's / adjust the standard).
  - no wrapper / no API surface (frontend-only / library) → note that here and skip the rest.
- **registry** — read wherever the project keeps its error codes (enum / CSV / DB / constants) and list each with its severity + messages. If there is no registry yet, this is a bootstrap concern (Initialize Phase 3/4) — propose creating base-response + a registry; don't invent codes.
- **severity** — show the user the default levels below and ask whether the default criteria + actions fit this project or it wants to adjust them; record what's agreed.

Fill per scan mode: light = the base-response shape + code list (ErrorCode only); full = also Severity + messages.
Don't guess — leave a cell `TBD` rather than invent a value.

## base-response
The response envelope every inbound API response uses. The shape below is the **recommended standard**; record the project's real shape and reconcile it against this per *How to scan*. Recommended standard:

`{ request_id, error_code?, message?, data?, paging? }` where `paging` = `{ count, limit, page }`

Fields:
- `request_id` — unique id of this request, for tracing / correlating logs.
- `error_code` — set on failure only; the code from the Registry below.
- `message` — human-readable message (a code's `ResponseMessage` on failure; e.g. `"ok"` on success).
- `data` — the response payload on success (its per-line shape lives in `gateway-contract.md`).
- `paging` — present when the response is a list: `count` (total), `limit` (page size), `page` (current page).

- **success** → `request_id` + `message` + `data` (+ `paging` when listing); no `error_code`.
- **failure** → `request_id` + `error_code` + `message` (the user-facing message for that code).

## Severity levels
How bad an error is, when to use each level, and what it should trigger. The table below is the **default baseline** — use it to recommend the right level for a new error; a project can redefine the criteria or the action for any level.

| level | criteria (when an error is this level) | action (default hint) |
|---|---|---|
| 0 | critical — affects all users; a core business flow can't proceed or a core feature is broken; must hotfix | system should notice before the user does — alert devs (Sentry / Slack / any channel) + log error |
| 1 | high — broken for a group of users (not everyone), often still retryable; fix next release, hotfix if needed | log error for sure; which alerting tool to fire is the project's choice |
| 2 | medium — a non-critical feature, or a main one that has a workaround; annoys users; fix next release | log warn is enough |
| 3 | minor — has a workaround, or cosmetic with the data still correct; fix when convenient | no log (not worth it) |

## Registry
The catalog of error codes — one row per code.
- `ErrorCode` — format `{DOMAIN 3}_{SERVICE 3}{4=bad request/business/validation · 5=system/infra}{NNN}` (e.g. `MCK_SVC4001`), or the project's own scheme. The `4`/`5` mirrors the HTTP family (4xx/5xx).
- `Severity` — `0`–`3` per the levels above.
- `ResponseMessage` — the user-facing message (becomes base-response `message`).
- `LogMessage` — the technical message written to logs.
- To add a code: find its DOMAIN/SERVICE group and take the next free sequence number.

| ErrorCode | Severity | ResponseMessage | LogMessage |
|---|---|---|---|
| `<DOM_SVC4NNN>` | `0–3` | `<user-facing message>` | `<technical log message>` |

## Role & Boundary (Read Before Editing)
This file holds the shared inbound-API response envelope (base-response) and the registry of error codes (code, severity, response/log messages). It is the registry that an `error_code` in `gateway-contract.md` — or one mentioned in a requirement — must match exactly. It does NOT hold per-line request/response payloads (`gateway-contract.md`), DB schema (`database-schema.md`), or test-data variable values (`data.md`). It is read-only to every workflow stage: a new or conflicting code goes to `self-report`, never edited from a stage.
