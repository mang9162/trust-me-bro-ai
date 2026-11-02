---
name: e2e-swimlane
description: Optional workflow plug-in, run once per feature before Stage-1 get-requirement. Draws the feature's business swimlane (SVG, generated from a text .flow file), lists every scenario the flow can be cut into, and maps each lane to what tests must mock or seed. Stage-1 then picks one scenario from that list.
---

# E2E Swimlane

## Purpose
See the whole feature before writing any one scenario: every business condition,
every way out of it, and which service each step runs in. From that picture the
scenario list is complete (one scenario per route worth testing), and each lane
tells the later stages what has to be mocked or seeded.

## Output
All under the feature folder `work/Scenario/<FEATURE>/` (workflow `## Layout`):

| file | what it is |
|---|---|
| `swimlane.flow` | the source — plain text, edited by hand, see `## .flow format` |
| `swimlane.svg` | the full diagram, generated |
| `e2e-flow.md` | business conditions checklist + lane → mock table + scenario list |
| `<Category>/<NN>-<NAME>/flow.svg` | one per `scenario` block — the full diagram with only that route kept, generated |

## Procedure

1. **Read the requirement** for the whole feature (not one scenario). Ask the user
   about anything unclear: which services take part, what starts the flow, what
   the user finally sees.

2. **Name the lanes** — one lane per real service the flow touches (the system
   under test, each datastore, each downstream service), so a lane name says what
   a test must mock. Take downstream services from `gateway-directory.md`. Mark the
   one that starts the flow `client` and outside parties `3rd`.

3. **List every business condition** as a checklist in `e2e-flow.md` — go through
   every `if` / `continue` / `return` / early exit / `for` / `map` in the functions
   on the path, one row each. Each loop body with more than one step is a loop in
   the diagram. When the code does not exist yet, list them from the requirement
   and write `requirement` as the source.

4. **Write `swimlane.flow`** (`## .flow format`), starting from the shape of
   `examples/comment-bot-reply/`. Pick each box's kind by `## Box kinds` and word
   it by `## Writing the words`, using the vocabulary in `domain-reference.md`.

5. **Generate and lint**:
   `python3 trust-me-bro-ai/skills/workflow/plugins/e2e-swimlane/scripts/swimlane.py work/Scenario/<FEATURE>/swimlane.flow --png`
   Fix every `error:` line and re-run until there are none. Read every `warn:` line
   and fix or accept it.
   - The script cannot run (no Python 3) → stop and tell the user; never draw the SVG by hand.
   - An error still there after two fixes → stop and show the user the error lines.

6. **Look at the picture** — open the PNGs the run printed (or the SVG in a
   browser) and check it reads: labels not sitting on other things, the main route
   easy to follow. Lint cannot judge this.

7. **Tick the checklist** — every row from step 3 names the box id that shows it.
   A row with no box means the diagram is incomplete: add it and go back to step 5.

8. **Cut the scenarios** — add one `scenario` block per route worth testing.
   - Same setup, only the incoming payload differs → one scenario (list each payload in its description).
   - Different setup, or a route through different stores/services → its own scenario.
   Re-run step 5. The `no scenario walks these ways out of a cond` warning must
   end up empty, or every way it lists is written in `e2e-flow.md` with the reason
   it is not tested.

9. **Finish `e2e-flow.md`** — below the checklist from step 3, add the lane → mock
   table, the scenario list and (when needed) Not tested — see `## e2e-flow.md format`.

10. **Self-learn** — if anything noticed is self-learn-worthy (a condition only
    found late, a lane the gateway directory does not list), trigger `self-report`.
    Do not ask the user whether to act on it now.

11. ⏸ **PAUSE** — present `swimlane.svg`, the scenario list and the lane table,
    and list the self-learn items recorded this round. On changes, edit
    `swimlane.flow` and go back to step 5. Do NOT hand off to Stage-1 until
    approved.

## Box kinds

Pick the kind by what the step *is*.

| kind | shape | it is | it is NOT |
|---|---|---|---|
| `actor` | hexagon | who starts the flow — in the `client` lane | a system |
| `task` | box | one thing the system or a person does | a check — a check is a `cond` |
| `cond` | blue diamond | one yes/no question with exactly a `yes` line and a `no` line | "which of several?" — split it into one `cond` per question; things done together — that is a `fork` |
| `store` | rounded box | data at rest, in its datastore's lane, reached by a dashed `..` line | a step — reading/writing is the dashed line, the step is the box it hangs from |
| `end` | red circle | the route stops before the outcome — nothing more happens for this event | "skip this one and go on with the next" inside a loop — that is a `join` leading back to the loop's check |
| `done` | green circle | the route finished as intended — after its last step | a stop part-way — that is an `end` |
| `merge` | white circle | ways meeting again; **required right before a loop starts** — the loop's back line comes into it | a stop |
| `fork` | thick bar | start several things *together* (each may or may not apply); the line out says when it applies | a choice — a choice is a `cond` |
| `join` | thick bar | gather ways back into one; fed only by side `no`/`yes` lines it sits in the gap under them and carries one line on (the "skip this bot" bar) | — |
| `note` | yellow box | an explanation pinned under a box (`near`) | part of the route — no lines go to it |

## Drawing rules

| # | rule | held by |
|---|---|---|
| 1 | one line = one way out → one way in → one arrowhead; lines never share a piece | generator gives each line its own track and a bridge at crossings; lint `share a piece` |
| 2 | a `cond` asks one yes/no question — exactly 2 ways out | lint |
| 3 | box text is business language, each condition taken from the real code | steps 3–4, `## Writing the words`; lint warns on code-looking text |
| 4 | lines out of a `cond`: green = yes, red = no — the colour of the answer, not good/bad | `yes` / `no` on the line |
| 5 | every loop is drawn as a loop, and every loop is found — a `merge` before it, a `cond` "all done?" that goes back | lint: a line going back must end on a `merge`; step 3 lists every `for` / `map` |
| 6 | shapes never overlap; look at the result every time | generator sizes rows to their shapes; lint `overlap`; step 6 |
| 7 | every route ends at a circle: green `done` = finished as intended, red `end` = stopped | lint `the route stops at` |

## Writing the words

| where | write | wrong → right |
|---|---|---|
| lane | the real service, datastore or outside party (what a test mocks) | a code layer ("handler", "repository") → the service name |
| `task` | one business action: who does what | "skip silently" (ข้ามเงียบ) → "can't reply with an image under a live — let it pass, not a failure" (ตอบรูปใต้ไลฟ์ไม่ได้ ปล่อยผ่าน ไม่ถือว่าล้มเหลว) |
| `cond` | a question answered yes or no, ending in "?" (Thai: ends in ไหม / ใช่ไหม) | `socialNetwork.teamId !== bot.teamId` → "bot belongs to the page's team?" (บอทเป็นของทีมเดียวกับเพจไหม) · "result of this command?" → "this command succeeded?" + "live still running?" + "sent image expired?" |
| line out of a `cond` | the answer first, then why when it helps | "ไม่ใช่ คนละทีม" · "ไม่ได้ เคยตอบแล้ว" · "ใช่ ครบแล้ว" |
| line out of a `fork` | when that branch applies | a diamond "what did the shop set up?" → a fork with "if set to like" (ถ้าตั้งให้กดไลก์) · "if set to reply in chat" (ถ้าตั้งทักแชท) |
| loop check | "all … done?" in the lane that does the looping | "did Facebook finish them all?" in the Facebook lane → "checked every command?" (ตรวจครบทุกคำสั่งแล้วไหม) in our service's lane, looping back to a `merge` |
| `end` / `done` | what happens to the user | "stop, no reply" (จบ ไม่ตอบ) · "done, every bot handled" (จบ ทำครบทุกบอท) |
| `store` | what the data is | a collection/table name → "reply history" (ประวัติการตอบลูกค้า) |
| dashed line | the verb: ask / check / save | "ถาม" · "เช็ก" · "บันทึก" |
| scenario | name per `domain-reference.md`; description = what happens, in user terms | — |

## .flow format

One statement per line; `#` starts a comment (a whole line or the rest of one);
text with spaces or an apostrophe goes in `"quotes"`; `|` inside box or circle
text breaks the line — a line label stays on one line.

| statement | meaning |
|---|---|
| `title <text>` | big title — the feature name |
| `subtitle <text>` | a line under the title (repeatable) |
| `lane <id> [client\|3rd] "<name>"` | a lane, top to bottom in the order written; then sorted: `client` lanes on top, services, datastores (lanes holding only `store`s), `3rd` at the bottom |
| `group "<label>" <lane-id> ...` | a bracket on the left over these lanes (e.g. front / back) |
| `<kind> <id> <lane> "<text>"` | a box (see `## Box kinds`) |
| `note <id> <lane> "<text>" near <id>` | a note under a box |
| `<a> -> <b> [yes\|no] ["label"]` | a flow line; lines out of a `cond` need `yes` / `no` (label defaults to the word yes / no) |
| `<a> .. <b> ["label"]` | a dashed data line between a box and a `store` |
| `segment <NAME> a > b > c` | a named piece of route, reused by scenarios |
| `scenario <Success\|Alternative> <NN> <NAME> "<description>"` | a scenario; indented lines under it: `use <SEGMENT> ...`, `path a > b > c` (each step must be an existing line), `note <text>` |

Layout is automatic: boxes flow left to right in line order, and the **first line
written out of a box runs straight right**; its other lines branch below. To change
which way is the main route, change which line is written first.

## Example

`examples/comment-bot-reply/` is a full, reviewed feature — read it before writing
a new one: `swimlane.flow` (60 boxes, two nested loops, fork/join, the
skip-this-bot join, 15 scenarios), the `swimlane.svg` it generates, and its
filled-in `e2e-flow.md`. Its opening, before the bot loop:

```
lane cust   client "ลูกค้า"
lane pubsub        "Pub/Sub"
lane svc           "live-stream|consumer"
lane mongo         "MongoDB"
lane redis         "Redis"
lane fb     3rd    "3rd|Facebook"

actor n_actor   cust   "ลูกค้า"
task  n_comment cust   "คอมเมนต์ใต้โพสต์|ของร้าน"
task  n_ps      pubsub "แจ้งระบบว่า|มีคอมเมนต์ใหม่"
cond  d_real    svc    "เป็นคอมเมนต์|จริงไหม"
cond  d_page    svc    "เพจเปิดใช้งาน|อยู่ไหม"
end   e_stop    svc    "จบ ไม่ตอบ"
store s_page    mongo  "ข้อมูลเพจที่ผูกไว้"
merge m_bot     svc                                 # the bot loop starts here
task  n_bots    svc    "หยิบบอทของร้าน|มาทีละตัว"

n_actor -> n_comment
n_comment -> n_ps
n_ps -> d_real
d_real -> d_page yes "ใช่"
d_real -> e_stop no  "แค่กดอีโมจิ / แก้คอมเมนต์เดิม"
d_page .. s_page "ถาม"
...
d_bot -> m_bot no "ไม่ ยังดูไม่ครบ หยิบบอทตัวถัดไป"     # back into the merge = a loop
```

## e2e-flow.md format

Fill it like `examples/comment-bot-reply/e2e-flow.md`.

```markdown
# E2E Flow — <FEATURE>

![swimlane](./swimlane.svg)
Generated from `swimlane.flow` — edit it, then re-run swimlane.py.

## Business conditions
| # | question in the diagram | box | from |
|---|---|---|---|
| 4 | บอทเป็นของทีมเดียวกับเพจไหม | `d_team` | `socialNetwork.teamId !== bot.teamId` |

## Lane → what tests mock or seed
| lane | real system | <one column per test level in testing-guide.md> |
|---|---|---|
| MongoDB | `mod_lsm` | mock repository | Mongo จริงใน compose | seed ผ่าน init-db |

## Scenarios
### Success
| NN | scenario | route through the flow | setup to prepare |
|---|---|---|---|
| 03 | `COMMENT_BOT_REPLY_SUCCESS_3` | ทักแชทเป็นรูป ยิงสองรอบด้วย setup เดียว รอบแรกอัปรูปใหม่ รอบสองใช้ของใน Redis | บอท 1 ตัว ตั้งแชทเป็นรูป |
### Alternative
(same columns)

## Not tested
| way out | reason |
|---|---|
| `<cond>><target>` | <why no scenario walks it> |
```

| column | write |
|---|---|
| question in the diagram | the `cond` text exactly as in the diagram |
| box | the box id, so the row can be ticked against the `.flow` |
| from | the code condition as written in the code (or `requirement`) — the only place code words are allowed |
| real system | the concrete thing: database name, what the cache holds, which outside API |
| one cell per test level | what that level does with this lane: real / mock client / real in compose / stub tool |
| route through the flow | which way this scenario takes, in business words — say what is special about it |
| setup to prepare | the data, settings and stub responses that must exist before the scenario runs |

## References
- cross-ref: `trust-me-bro-ai/context/gateway-directory.md` — the downstream services that become lanes.
- cross-ref: `trust-me-bro-ai/context/domain-reference.md` — business vocabulary for box text and scenario naming.
- cross-ref: `trust-me-bro-ai/tech-stack/testing-guide.md` — the test levels that make the columns of the lane → mock table.
- cross-ref (no file-map edge): `examples/comment-bot-reply/` (in this skill's folder) — a full reviewed example of `swimlane.flow`, its SVG and `e2e-flow.md`.
- bridge: `trust-me-bro-ai/skills/workflow/SKILL.md` (`## Layout`) — the feature folder and the `<Category>/<NN>-<NAME>/` scenario folder each `flow.svg` is written to must match it exactly.

## Trigger Skill
- self-report — when something self-learn-worthy is noticed while drawing the flow, per step 10.

## Writes To
- `work/Scenario/<FEATURE>/` — `swimlane.flow`, `swimlane.svg`, `e2e-flow.md`, and each scenario's `flow.svg`.

## Role & Boundary (Read Before Editing)
This plug-in owns the feature-level picture: the `.flow` source, the generated
diagrams (full and per scenario), the business-condition checklist, the lane →
mock table and the scenario list. It runs once per feature, before get-requirement, and
only when the user opts in; without it the workflow runs as before.

It does NOT write `scenario.html` or any scenario's `steps` (get-requirement,
which picks one scenario from this list), stage test data (create-test-data,
which reads the lane table), or render the report (generate-report, which shows a
scenario's `flow.svg` when present). For anything outside this boundary, see the
Responsibility map in `workflow/SKILL.md`.
