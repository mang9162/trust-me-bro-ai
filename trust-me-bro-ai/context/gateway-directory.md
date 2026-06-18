# Gateway Directory

## How to use
Read this file to find which communication lines this service has and what each is for.
What you get is the WHAT — a catalog of lines; the request/response shapes (success/error)
are not here, they live in gateway-contract.md, reached by the matching `bridge` id.

## Inbound Gateway
Lines this service exposes (others call in). One table per app/service (`### <name>`).
One row = one line × one purpose; split variants by a key in `condition`.

Template — fill each cell like this:
| endpoint | condition | purpose | bridge | function | note |
|---|---|---|---|---|---|
| `<METHOD> /<path>` | `<key>=<value>` or `—` | what this line + variant is for | `<your-service>(/<path>)` | receiving controller/handler (or where it will live) | caveat |

### live-service
| endpoint | condition | purpose | bridge | function | note |
|---|---|---|---|---|---|
| POST /lives | — | Create a live | live-service(/lives) | LiveController.create | |
| GET /lives/{id} | — | Get live detail | live-service(/lives/{id}) | LiveController.getById | |
| PATCH /lives/{id} | — | Update a live | live-service(/lives/{id}) | LiveController.update | |
| POST /lives/{id}/end | — | End a live | live-service(/lives/{id}/end) | LiveController.end | |

### live-consumer
| endpoint | condition | purpose | bridge | function | note |
|---|---|---|---|---|---|
| POST /consume/comment | — | Process an incoming live comment | live-consumer(/consume/comment) | CommentConsumer.handle | consumer endpoint (Pub/Sub-driven) |

## Outbound Gateway
Lines this service calls out to. One table per target system (`### <name>`).
One row = one line × one purpose; split variants by a key in `condition`.

Template — fill each cell like this:
| endpoint | condition | purpose | bridge | function | note |
|---|---|---|---|---|---|
| `<METHOD> /<path>` | `<key>=<value>` or `—` | what this line + variant is for | `<target>(/<path>)` | calling gateway/client (or where it will live) | caveat |

### Payment
| endpoint | condition | purpose | bridge | function | note |
|---|---|---|---|---|---|
| POST /payments/charge | — | Charge the customer for an order | Payment(/payments/charge) | PaymentGateway.charge | mocked — confirm in Phase 4 |

### Inventory
| endpoint | condition | purpose | bridge | function | note |
|---|---|---|---|---|---|
| POST /inventory/stock | action=RESERVE | Reserve stock when an order is placed | Inventory(/inventory/stock) | InventoryGateway.reserve | mocked |
| POST /inventory/stock | action=RELEASE | Release reserved stock on cancel | Inventory(/inventory/stock) | InventoryGateway.release | mocked; same shape as RESERVE |

### Notification
| endpoint | condition | purpose | bridge | function | note |
|---|---|---|---|---|---|
| POST /notify/push | — | Push a notification to the customer | Notification(/notify/push) | NotificationGateway.push | mocked |

## References
- bridge: tech-stack/gateway-contract.md — the `bridge` id `<service>(<path>)` must match an entry there; gateway-contract.md holds each line's request/response shapes (success/error).

## Role & Boundary (Read Before Editing)
This file catalogs WHAT lines the service has (Inbound + Outbound Gateway) — endpoint, condition,
purpose, the `bridge` id, the `function` it lives at, and notes. It does NOT hold request/response
shapes; those live in gateway-contract.md, matched by `bridge`.
