# Gateway Directory

Target: `context/gateway-directory.md` — create/update this file from the format below.

## How to use
Read this file to find which communication lines this service has and what each is for.
What you get is the WHAT — a catalog of lines; the request/response shapes (success/error)
are not here, they live in gateway-contract.md, reached by the matching `bridge` id.

## How to scan (when filling this file)
Read the repo to discover the lines — every repo differs, so don't assume a stack:
- Inbound  — where this service receives/handles incoming requests (the routes / handlers / listeners it exposes). One table per app/service.
- Outbound — where this service calls other systems (gateway/client code, stub/mock folders, queue publishers). One table per target system.
Fill per scan mode: light = the lines only; full = every cell.

## Inbound Gateway
Lines this service exposes (others call in). One table per app/service (`### <name>`).
One row = one line × one purpose; split variants by a key in `condition`.

Template — fill each cell like this:
| endpoint | condition | purpose | bridge | function | note |
|---|---|---|---|---|---|
| `<METHOD> /<path>` | `<key>=<value>` or `—` | what this line + variant is for | `<your-service>(/<path>)` | receiving controller/handler (or where it will live) | caveat |

## Outbound Gateway
Lines this service calls out to. One table per target system (`### <name>`).
One row = one line × one purpose; split variants by a key in `condition`.

Template — fill each cell like this:
| endpoint | condition | purpose | bridge | function | note |
|---|---|---|---|---|---|
| `<METHOD> /<path>` | `<key>=<value>` or `—` | what this line + variant is for | `<target>(/<path>)` | calling gateway/client (or where it will live) | caveat |

## References
- bridge: tech-stack/gateway-contract.md — the `bridge` id `<service>(<path>)` must match an entry there; gateway-contract.md holds each line's request/response shapes (success/error).

## Role & Boundary (Read Before Editing)
This file catalogs WHAT lines the service has (Inbound + Outbound Gateway) — endpoint, condition,
purpose, the `bridge` id, the `function` it lives at, and notes. It does NOT hold request/response
shapes; those live in gateway-contract.md, matched by `bridge`.
