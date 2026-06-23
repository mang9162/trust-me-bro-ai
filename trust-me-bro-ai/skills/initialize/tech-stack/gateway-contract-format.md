# Gateway Contract

Target: `tech-stack/gateway-contract.md` — create/update this file from the format below.

## How to use
Read this for the request/response shapes of each communication line — what to send and what comes back (success + errors). It pairs with `gateway-directory.md` by the same `bridge` id: gateway-directory says WHICH lines exist and why; this file says what each line's payloads look like. Used to build mocks/stubs (outbound) and to write api-tests (inbound).

## How to scan (when filling this file)
For each line in `gateway-directory.md` (by its `bridge` id), read the code (request/response types/schemas/payloads — whatever the stack uses) and any observed traffic to capture the request shape, the success response, and the possible errors. Light = the `bridge` id + a skeleton (fields `TBD`); full = fill the actual shapes.

## Format
- **One entry per line**, keyed by the same `bridge` id as gateway-directory — NOT per condition. The line has one shape; note where it differs by condition inline. Split a field (`request` / `success` / `errors`) into separate **cases** within the entry only if it differs by condition by more than ~25% (the API is doing several jobs) — never a new entry.
- Two sections mirror gateway-directory: `## Inbound` (we expose — exercised by api-test) and `## Outbound` (we call out — faked by a stub), because `mock` differs.
- **Fields follow the line's protocol** (protocol is in the endpoint in gateway-directory):

  | protocol | fields |
  |---|---|
  | HTTP / gRPC (request→response) | `request` · `success` · `errors` |
  | WS / socket (stream) | `subscribe` · `events` · `errors` |
  | polling | same as HTTP |

- **queue is not a separate shape here:** a queue *consumer* is represented as its **Inbound** HTTP test-consumer entry (the message is the request body, exercised by api-test); a queue *publish* is an **Outbound** line, mocked per the project's setup.
- **Write payloads as JSON:** `request` = the method on one line then the body JSON; `success` = the status on one line then the body JSON.
- **`errors` is a list** (a line may have several). Each: `<status> <NAME> → <error_code>` then the body. Map to the `error_code` in `error-codes.md` when the line is ours (inbound); an external system's code may have no local map.
- **`mock`:**
  - Outbound — HTTP (incl. queue publish): stub. `match` = the request keys the stub predicate matches on; `stub` = the stub file path; `returns` = the `success`/`error` above (chosen per scenario). The stub file's structure (mountebank JSON template) and folder layout live in `tech-stack.md` (Infrastructure) — one place, not repeated here. WS: a mock WS server pushes the `events` above (not a mountebank HTTP stub).
  - Inbound — api-test, no stub: send `request` to the real API and assert `success`/`errors` (WS: connect a real client and assert the `events` stream). If a sibling service in this same repo calls this line, the call is real too — it's just this same Inbound entry, no stub (internal).

## Inbound   (lines we expose — exercised by api-test)
Template — fill each entry like this (swap fields per the line's protocol, see table):
### <bridge id>
- request: <METHOD> + body JSON
- success: <status> + body JSON
- errors:
  - <status> <NAME> → <error_code> — <error body JSON>
- mock: api-test (no stub) — send `request` to the real API, assert status + body

## Outbound   (lines we call out — faked by a stub)
Template — fill each entry like this (swap fields per the line's protocol, see table):
### <bridge id>
- request: <METHOD> + body JSON
- success: <status> + body JSON
- errors:
  - <status> <NAME> → <error_code> — <error body JSON>
- mock:
  - match: <request keys the stub predicate matches on>
  - stub: <stub file path>
  - returns: success / error above (chosen per scenario)

## References
- bridge: `context/gateway-directory.md` — the same `bridge` id must match an entry there (the catalog / WHAT side).
- bridge: `context/error-codes.md` — each inbound error's `error_code` must match an entry in the registry.

## Role & Boundary (Read Before Editing)
This file holds each line's request/response shapes (success + errors) and how it's mocked/tested, paired to `gateway-directory.md` by `bridge` id. It does NOT catalog which lines exist or their purpose (that's `gateway-directory.md`).
