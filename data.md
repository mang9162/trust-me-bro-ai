# Data Dictionary — central reference

Project-wide catalogue of every kind of test-data variable, grouped by **context** (who owns the data / where it comes from). **No concrete values live here** — only description, source reference, and the value's `format`.

Per-scenario test data files (`<case>/01-Testdata/Datatest.md`) pick entries from this dictionary and assign concrete values for that scenario only.

- `ref` — where the value comes from (source system / field).
- `format` — the *shape* of the value, so a scenario can generate a fresh, non-colliding value when it needs one (e.g. a unique `videoId` per scenario). It is a shape, never a concrete value. `(?)` = shape not yet confirmed — fill it in, don't guess.

Update this file whenever a new variable is discovered (a new field needed by a scenario that isn't already catalogued). Keep entries terse.

---

## External
Related to:
- External API / Hook
- Facebook

| name           | description                                       | ref                                  | format                            |
|----------------|---------------------------------------------------|--------------------------------------|-----------------------------------|
| target         | customer id from a Facebook page (aliased as `recipientId`/`socialUserId` in some downstream payloads — same Facebook user id) | Facebook user id | numeric string (Facebook user id) |
| videoId        | videoId of a live from `live_videos` endpoint     | Facebook `live_videos[].video.id`    | numeric string (Facebook video id) |
| postId         | postId of a live from `live_videos` endpoint      | Facebook `live_videos[].id`          | numeric string (Facebook post id) |
| commentId      | external platform comment id that triggers/links a reserve | `live_crawler_comments.ref_comment_id` | (?)                          |
| commentMessage | raw comment text parsed for CF code + quantity    | webhook payload `value.message`      | free text                         |

## Page Info
Related to:
- SocialNetworks (mongo)
- External API / Hook

| name                | description                                  | ref                            | format                             |
|---------------------|----------------------------------------------|--------------------------------|------------------------------------|
| socialNetworkRefId  | page id on the social network                | SocialNetworks.refId           | numeric string (Facebook page id)  |
| socialToken         | token used to verify against Facebook        | SocialNetworks.token           | opaque token string                |
| pageId              | 3rd-party page id (same value as socialNetworkRefId in most flows) | mirrors socialNetworkRefId | mirrors socialNetworkRefId   |

## User Admin
Related to:
- users (mongo)

| name    | description       | ref            | format |
|---------|-------------------|----------------|--------|
| teamId  | admin team id     | users.teamId   | (?)    |

## Product
Related to:
- External Warehouse
- live_crawler_products (postgres)
- Redis

| name                  | description                              | ref                                       | format                       |
|-----------------------|------------------------------------------|-------------------------------------------|------------------------------|
| productSkuId          | a product SKU id                         | live_crawler_products.product_sku_id      | (?)                          |
| parentProductSkuId    | parent SKU id (when product is a variant)| live_crawler_products.parent_product_sku_id | same shape as productSkuId |
| cfCode                | configured CF code for ordering          | live_crawler_products.cf_code             | (?)                          |
| branchStock           | stock count at the branch                | live_crawler_products.branch_stock        | non-negative integer         |
| currentStock          | current live product stock; equals branchStock after setting live and is updated after checkout, not when reserve is created | live_crawler_products.current_stock | non-negative integer |
| available             | available quantity for a product after active reserves are considered | derived from currentStock minus reserved quantity for that product | non-negative integer (derived) |
| unitPrice             | unit price with VAT in baht                    | live_crawler_products.unit_price    | decimal, 2dp, baht           |
| diffBranchStock       | difference between new and old branchStock (newBranchStock - oldBranchStock); negative = decrease | edit-products flow only | integer (can be negative) |

## Live
Related to:
- live_crawlers (postgres)
- live_crawler_posts (postgres)

| name              | description                                                | ref                                | format                              |
|-------------------|------------------------------------------------------------|------------------------------------|-------------------------------------|
| liveCrawlerId     | unique id of a live crawler record (UUID)                  | live_crawlers.id                   | UUID v4                             |
| liveStatus        | LIVE / END                                                 | live_crawlers.live_status          | one of: LIVE, END                   |
| expireSec         | reserve expiry (seconds)                                   | live_crawlers.expire_sec           | positive integer (seconds)          |
| lastCheckout      | minutes before live ends during which checkout is allowed; -1 = disabled | live_crawlers.last_checkout | integer (minutes; -1 = disabled) |
| cartExpireSec     | cart expiry (seconds)                                      | live_crawlers.cart_expire_sec      | positive integer (seconds)          |
| finishedAt        | when the live was ended on LSM side                        | live_crawler_posts.finished_at     | datetime                            |
| platformFinishedAt| when the live was ended on the platform                    | live_crawler_posts.platform_finished_at | datetime                       |

## Reserve / Order
Related to:
- reservation_products (postgres)
- live_crawler_orders (postgres)
- redis (delay queue)

| name                | description                            | ref                                       | format                          |
|---------------------|----------------------------------------|-------------------------------------------|---------------------------------|
| reserveId           | unique reserve identifier (primary id) | reservation_products.id                   | UUID v4                         |
| reserveReferenceId  | references the owning live             | reservation_products.reserve_reference_id | UUID v4 (references a live)      |
| refOrderId          | references the resulting order         | reservation_products.ref_order_id         | same shape as orderId           |
| quantity            | reserved quantity                      | reservation_products.quantity             | positive integer                |
| orderId             | order id                               | live_crawler_orders.order_id              | (?)                             |
| cartId              | cart id                                | live_crawler_orders.cart_id               | (?)                             |
| billStatus          | PAID / UNPAID / CANCEL                 | live_crawler_orders.bill_status           | one of: PAID, UNPAID, CANCEL    |
| removedQuantity     | quantity removed from cart, returned by cart-edit/cancel response | pinmall `admin-edit-cart` / `remove-reserve` response | non-negative integer |
| removedAmount       | amount removed from cart in baht, returned by cart-edit/cancel response | pinmall `admin-edit-cart` / `remove-reserve` response | decimal, 2dp, baht |
| isCartEmpty         | whether the cart became empty after removal | pinmall `admin-edit-cart` / `remove-reserve` response | boolean             |
| cartItemUnitPrice   | cart item unit price returned by PinMall cart response | pinmall `cart.orderItems[].unitPrice` | decimal, 2dp, baht     |

---

## Role & Boundary (Read Before Editing)

data.md is the central dictionary of test-data variable **names** — it records **who owns each piece of data** (the `## context` group it lives under) and **where each value comes from** (`ref`). It holds only: name + description + source (`ref`) + value `format`. **It never holds concrete values** — those live per-scenario in `Datatest.md`.

- `format` describes only the *shape* used to generate a dynamic, non-colliding value — not a real value.
- **Read-only for every stage.** If a scenario needs a variable that is new, or one whose definition conflicts with what is here → send it to `self-report`. Never edit this file from a stage.
- Scope boundaries: general domain knowledge → `domain-reference.md`; request/response shapes → `gateway-contract.md`; real DB columns/types → `database-schema.md` (linked via `ref`).
