#!/usr/bin/env python3
"""Draw a business swimlane SVG from a .flow text file, lint it against the
drawing rules, and carve one flow.svg per declared scenario.

usage: python3 swimlane.py <dir>/swimlane.flow [--png [OUT_DIR]]

writes  <dir>/swimlane.svg
        <dir>/<Category>/<NN>-<NAME>/flow.svg   (one per `scenario` block)
--png   also renders every written SVG to PNG in OUT_DIR (default: a temp dir)
        with rsvg-convert or headless Chrome, for a visual check.
exit 1  when lint finds an error (the SVGs are still written so they can be inspected).
"""
import html
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

# ====================================================================== parse

NODE_KINDS = {"actor", "task", "cond", "store", "end", "done", "merge", "fork", "join", "note"}
BARS = {"fork", "join"}
ENDS = ("end", "done")                  # red: stopped · green: finished as intended


class Node:
    def __init__(self, nid, kind, lane, text, near, order, line):
        self.id, self.kind, self.lane, self.order, self.line = nid, kind, lane, order, line
        self.lines = [t for t in text.split("|")] if text else []
        self.near = near
        self.col = self.row = None


class Edge:
    def __init__(self, a, b, kind, branch, label, order, line):
        self.a, self.b, self.kind, self.branch, self.order, self.line = a, b, kind, branch, order, line
        self.label = label
        if self.label is None and branch:
            self.label = branch
        self.back = False
        self.tag = f"{a}>{b}"


class Flow:
    def __init__(self):
        self.title, self.subtitles = "", []
        self.lanes, self.groups = [], []          # lanes: (id, role, name-lines)
        self.nodes, self.edges = {}, []
        self.segments, self.scenarios = {}, []
        self.errors, self.warnings = [], []


def parse(path):
    fl = Flow()
    scen = None
    with open(path, encoding="utf-8") as f:
        raw = f.read().splitlines()
    for no, line in enumerate(raw, 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        indented = line[:1] in (" ", "\t")
        try:
            tok = shlex.split(s, comments=True)          # '#' outside quotes starts a comment
        except ValueError as e:
            fl.errors.append(f"line {no}: {e} — put text holding an apostrophe (') in \"double quotes\"")
            continue
        head = tok[0]

        if indented and scen is not None:
            if head == "path":
                scen["paths"].append(_chain(tok[1:]))
            elif head == "use":
                scen["use"] += tok[1:]
            elif head == "note":
                scen["note"] = " ".join(tok[1:])
            else:
                fl.errors.append(f"line {no}: unknown scenario line '{head}' (path / use / note)")
            continue
        scen = None

        if head == "title":
            fl.title = " ".join(tok[1:])
        elif head == "subtitle":
            fl.subtitles.append(" ".join(tok[1:]))
        elif head == "lane":
            if len(tok) < 3:
                fl.errors.append(f"line {no}: lane needs an id and a name")
                continue
            role = tok[2] if tok[2] in ("client", "3rd") else ""
            name = tok[3] if role else tok[2]
            fl.lanes.append((tok[1], role, name.split("|")))
        elif head == "group":
            fl.groups.append((tok[1], tok[2:]))
        elif head in NODE_KINDS:
            if len(tok) < 3:
                fl.errors.append(f"line {no}: {head} needs an id and a lane")
                continue
            near = None
            rest = tok[3:]
            if "near" in rest:
                i = rest.index("near")
                near = rest[i + 1] if i + 1 < len(rest) else None
                rest = rest[:i]
            text = " ".join(rest)
            if tok[1] in fl.nodes:
                fl.errors.append(f"line {no}: duplicate id '{tok[1]}'")
            fl.nodes[tok[1]] = Node(tok[1], head, tok[2], text, near, len(fl.nodes), no)
        elif head == "segment":
            name = tok[1]
            body = [t for t in tok[2:] if t not in ("=", ":")]
            fl.segments.setdefault(name, []).append(_chain(body))
        elif head == "scenario":
            if len(tok) < 4 or tok[1] not in ("Success", "Alternative"):
                fl.errors.append(f"line {no}: scenario <Success|Alternative> <NN> <NAME> \"desc\"")
                continue
            scen = dict(cat=tok[1], nn=tok[2], name=tok[3], desc=" ".join(tok[4:]),
                        note="", paths=[], use=[], line=no)
            fl.scenarios.append(scen)
        elif len(tok) >= 3 and tok[1] in ("->", ".."):
            kind = "flow" if tok[1] == "->" else "data"
            rest = tok[3:]
            branch = None
            if rest and rest[0] in ("yes", "no"):
                branch, rest = rest[0], rest[1:]
            fl.edges.append(Edge(tok[0], tok[2], kind, branch, " ".join(rest) or None, len(fl.edges), no))
        else:
            fl.errors.append(f"line {no}: cannot read '{s}'")
    return fl


def _chain(tokens):
    return [t for t in tokens if t != ">"]

# ====================================================================== checks on the model


def check_model(fl):
    E, W = fl.errors, fl.warnings
    lane_ids = [l[0] for l in fl.lanes]
    for n in fl.nodes.values():
        if n.lane not in lane_ids:
            E.append(f"line {n.line}: {n.id} is in unknown lane '{n.lane}'")
        if n.near and n.near not in fl.nodes:
            E.append(f"line {n.line}: {n.id} is near unknown node '{n.near}'")
        for t in n.lines:
            if re.search(r"[a-z][A-Z]|\w_\w|\(\)|===|!==|\w\.\w+\(", t):
                W.append(f"line {n.line}: {n.id} text '{t}' looks like code — write the business meaning (rule 3)")
    for e in fl.edges:
        for x in (e.a, e.b):
            if x not in fl.nodes:
                E.append(f"line {e.line}: unknown node '{x}'")
        if e.label and "|" in e.label:
            W.append(f"line {e.line}: {e.a} -> {e.b} label has '|' — a line label stays on one line, shorten it instead")
    if E:
        return
    for e in fl.edges:
        if e.kind == "data":
            if "store" not in (fl.nodes[e.a].kind, fl.nodes[e.b].kind):
                E.append(f"line {e.line}: {e.a} .. {e.b} — a data line must touch a store")
        elif fl.nodes[e.b].kind in ("store", "note") or fl.nodes[e.a].kind in ("store", "note"):
            E.append(f"line {e.line}: {e.a} -> {e.b} — stores take data lines (..), notes take no lines")
    for n in fl.nodes.values():
        outs = [e for e in fl.edges if e.a == n.id and e.kind == "flow"]
        if n.kind == "cond":
            if len(outs) != 2:
                E.append(f"line {n.line}: {n.id} has {len(outs)} ways out — a cond asks one yes/no question, exactly 2 ways (rule 2)")
            elif sorted(e.branch or "" for e in outs) != ["no", "yes"]:
                E.append(f"line {n.line}: {n.id} needs one 'yes' and one 'no' line out (rule 4)")
        else:
            for e in outs:
                if e.branch:
                    E.append(f"line {e.line}: {e.a} -> {e.b} — yes/no only belongs on lines out of a cond")
        if n.kind in ENDS and outs:
            E.append(f"line {n.line}: {n.id} is an {n.kind} — nothing goes out of it")
        if n.kind in ("actor", "task", "merge", "fork", "join") and not outs:
            W.append(f"line {n.line}: the route stops at {n.id} — end it at a done (green, finished as intended) or an end (red, stopped)")
        if n.kind in ("task", "actor", "merge") and len(outs) > 1:
            E.append(f"line {n.line}: {n.id} has {len(outs)} ways out — use a cond to choose or a fork to do them together")
    order = [l[0] for l in fl.lanes]
    for gname, glanes in fl.groups:
        for gl in glanes:
            if gl not in order:
                E.append(f"group '{gname}' names unknown lane '{gl}'")

# ====================================================================== layout


def text_w(s, size):
    w = 0.0
    for ch in s:
        o = ord(ch)
        if o == 0x0E31 or 0x0E34 <= o <= 0x0E3A or 0x0E47 <= o <= 0x0E4E:
            continue                                   # Thai marks sit on the letter, no width
        if 0x0E00 <= o <= 0x0E7F or ch.isupper() or ch.isdigit():
            w += 0.62
        elif ch == " ":
            w += 0.3
        else:
            w += 0.53
    return w * size


def end_lab_h(n):
    """room for the text under an end / done circle (one row per '|' line) or an actor"""
    return 22 + 14 * max(0, len(n.lines) - 1) if n.kind in ENDS else 22


def size_nodes(fl):
    for n in fl.nodes.values():
        tw = max([text_w(t, 13) for t in n.lines] or [0])
        k = len(n.lines)
        if n.kind == "task":
            n.w, n.h = max(130, tw + 28), max(48, 15 * k + 22)
        elif n.kind == "cond":
            tw = max([text_w(t, 12) for t in n.lines] or [0])
            n.h = max(80, 13 * k + 56)
            n.w = max(140, (tw + 18) / (1 - 13 * k / n.h))
        elif n.kind == "store":
            n.w, n.h = max(130, tw + 30), max(48, 14 * k + 22)
        elif n.kind == "note":
            tw = max([text_w(t, 11) for t in n.lines] or [0])
            n.w, n.h = max(150, tw + 24), 14 * k + 20
        elif n.kind == "actor":
            n.w, n.h = 46, 52
        elif n.kind in ENDS:
            n.w = n.h = 30
        elif n.kind == "merge":
            n.w = n.h = 26
        else:                                          # fork / join bar; height set later
            n.w, n.h = 10, 40


def layout(fl):
    nodes, edges = fl.nodes, fl.edges
    lane_ix = {l[0]: i for i, l in enumerate(fl.lanes)}
    flow = [e for e in edges if e.kind == "flow"]
    outs = {k: [e for e in flow if e.a == k] for k in nodes}
    ins = {k: [e for e in flow if e.b == k] for k in nodes}

    # loops: an edge back to a node still on the walk
    state = {}
    for start in sorted(nodes.values(), key=lambda n: n.order):
        if start.id in state or ins[start.id] and start.kind not in ("actor",):
            continue
        _dfs(start.id, outs, state)
    for n in sorted(nodes.values(), key=lambda n: n.order):
        if n.id not in state:
            _dfs(n.id, outs, state)

    # columns: longest path over forward lines
    fwd = [e for e in flow if not e.back]
    indeg = {k: 0 for k in nodes}
    for e in fwd:
        indeg[e.b] += 1
    col = {k: 0 for k in nodes}
    queue = sorted([k for k in nodes if indeg[k] == 0], key=lambda k: nodes[k].order)
    seen = 0
    while queue:
        k = queue.pop(0)
        seen += 1
        for e in sorted(outs[k], key=lambda e: e.order):
            if e.back:
                continue
            col[e.b] = max(col[e.b], col[k] + 1)
            indeg[e.b] -= 1
            if indeg[e.b] == 0:
                queue.append(e.b)
    flowing = [k for k in nodes if nodes[k].kind not in ("store", "note")]
    first_out = {k: (sorted(outs[k], key=lambda e: e.order) or [None])[0] for k in nodes}
    for k in flowing:
        n = nodes[k]
        # a join fed only by side ways out (down from conds) lives in the gap under them:
        # it gathers the lines there and carries one line on, without taking a row
        n.gapjoin = (n.kind == "join" and bool(ins[k]) and all(
            nodes[e.a].lane == n.lane and nodes[e.a].kind not in BARS and first_out[e.a] is not e and not e.back
            for e in ins[k]))

    # a bar owns its column inside its lane
    moved = True
    while moved:
        moved = False
        for b in flowing:
            nb = nodes[b]
            if nb.kind not in BARS:
                continue
            mates = [k for k in flowing if k != b and col[k] == col[b] and nodes[k].lane == nb.lane]
            if mates:
                c = col[b]
                if nb.gapjoin:                 # keep the gap join next to its feeders, push the rest
                    for k in flowing:
                        if k != b and col[k] >= c:
                            col[k] += 1
                else:
                    for k in flowing:
                        if col[k] > c:
                            col[k] += 1
                    col[b] = c + 1
                moved = True
                break

    # stores sit under (or over) the node that talks to them, notes beside their anchor
    for k, n in nodes.items():
        if n.kind == "store":
            partners = [e.a if e.b == k else e.b for e in edges if e.kind == "data" and k in (e.a, e.b)]
            col[k] = col[partners[0]] if partners else 0
        elif n.kind == "note":
            col[k] = col[n.near] if n.near else 0
    for k in nodes:
        nodes[k].col = col[k]

    # rows inside each lane
    cells = {}
    straight = {}
    for k in nodes:
        fo = [e for e in sorted(outs[k], key=lambda e: e.order)]
        straight[k] = fo[0] if fo else None

    def place(n, desired):
        r = max(0, desired)
        while (n.lane, r, n.col) in cells:
            r += 1
        n.row = r
        cells[(n.lane, r, n.col)] = n.id

    for c in sorted(set(col[k] for k in flowing)):
        wants = []
        for k in [k for k in flowing if col[k] == c]:
            n = nodes[k]
            if n.gapjoin:
                n.row = max(nodes[e.a].row for e in ins[k]) + 1     # index of the gap it sits in
                continue
            desired, branch = 0, 1
            preds = [e for e in sorted(ins[k], key=lambda e: e.order) if not e.back and nodes[e.a].row is not None]
            same = [e for e in preds if nodes[e.a].lane == n.lane]
            if same:
                st = [e for e in same if straight[e.a] is e]
                p = min(st, key=lambda e: nodes[e.a].row) if st else same[0]
                pr = nodes[p.a].row
                desired, branch = (pr, 0) if straight[p.a] is p else (pr + 1, 1)
            wants.append((branch, desired, n.order, n))
        for branch, desired, _o, n in sorted(wants, key=lambda w: w[:3]):   # straight runs keep their row first
            place(n, desired)
    for k in sorted([k for k in nodes if nodes[k].kind == "store"], key=lambda k: (col[k], nodes[k].order)):
        place(nodes[k], 0)
    fl.place = place
    fl.cells = cells
    fl.lane_ix = lane_ix
    fl.outs, fl.ins, fl.straight = outs, ins, straight
    fl.ncol = max(col.values()) + 1 if col else 1
    fl.nrows = {l[0]: 1 + max([n.row for n in nodes.values() if n.lane == l[0] and n.row is not None
                               and not getattr(n, "gapjoin", False)] or [0]) for l in fl.lanes}


def _dfs(start, outs, state):
    stack = [(start, iter(sorted(outs[start], key=lambda e: e.order)))]
    state[start] = "open"
    while stack:
        k, it = stack[-1]
        e = next(it, None)
        if e is None:
            state[k] = "done"
            stack.pop()
            continue
        if state.get(e.b) == "open":
            e.back = True
        elif e.b not in state:
            state[e.b] = "open"
            stack.append((e.b, iter(sorted(outs[e.b], key=lambda x: x.order))))

# ====================================================================== ports + routes

def assign_ports(fl):
    nodes, E = fl.nodes, fl.errors
    used = {k: set() for k in nodes}
    for e in fl.edges:
        e.pa = e.pb = None
    li = fl.lane_ix

    def above(a, b):            # is node a above node b on the page
        return (li[a.lane], a.row) < (li[b.lane], b.row)

    # out ports
    for k, n in nodes.items():
        outs = sorted(fl.outs[k], key=lambda e: e.order)
        for e in outs:
            if getattr(n, "gapjoin", False):
                e.pa = "G"
                continue
            if n.kind in BARS:
                e.pa = "R"
                continue
            if e is fl.straight[k] and not e.back:
                want = ["R", "B", "T"]
            elif e.back:
                want = ["B", "T"]
            elif above(nodes[e.b], n):
                want = ["T", "B"]
            else:
                want = ["B", "T"]
            e.pa = next((p for p in want if p not in used[k]), None)
            if e.pa is None:
                E.append(f"line {e.line}: {k} has no free side for the line to {e.b}")
                e.pa = "R"
            used[k].add(e.pa)
    # in ports
    for k, n in nodes.items():
        ins = sorted(fl.ins[k], key=lambda e: e.order)
        if n.kind in BARS:
            for e in ins:
                e.pb = "L"
            continue
        prim = None
        for e in ins:
            a = nodes[e.a]
            if not e.back and fl.straight[e.a] is e and a.lane == n.lane and a.row == n.row:
                prim = e
                break
        if prim is None:
            prim = next((e for e in ins if not e.back), None)
        extra_left = 0

        def want_of(e):
            a = nodes[e.a]
            if e is prim:
                return 0, ["L", "T", "B"]
            if e.back:
                return 1, ["B", "T"]
            if (li[a.lane], a.row) != (li[n.lane], n.row):        # clearly above or below: strong
                return 1, (["T", "B"] if above(a, n) else ["B", "T"])
            return 2, (["B", "T"] if e.pa in ("B", "G") else ["T", "B"])
        for e in sorted(ins, key=lambda e: want_of(e)[0]):
            want = want_of(e)[1]
            e.pb = next((p for p in want if p not in used[k]), None)
            if e.pb is None:
                if n.kind == "task" and extra_left < 2:
                    extra_left += 1
                    e.pb = f"L{extra_left}"
                else:
                    E.append(f"line {e.line}: {k} gets more lines than it has sides — put a merge (circle) "
                             f"or join (bar) in front of it")
                    e.pb = "L"
            used[k].add(e.pb)
    # data lines: from the talking node toward the store
    for e in fl.edges:
        if e.kind != "data":
            continue
        s, o = (e.b, e.a) if nodes[e.b].kind == "store" else (e.a, e.b)
        e.src, e.dst = o, s
        down = (li[nodes[s].lane], nodes[s].row) > (li[nodes[o].lane], nodes[o].row)
        e.pa, e.pb = ("D", "T") if down else ("U", "B")
    for e in fl.edges:
        if e.kind == "flow":
            e.src, e.dst = e.a, e.b

    # bar port slots: same-lane partners line up with their own row
    for k, n in nodes.items():
        if n.kind not in BARS:
            continue
        for e in fl.ins[k]:
            a = nodes[e.a]
            e.via_gap = (a.lane == n.lane and a.kind not in BARS and e.pa in ("B", "T") and n.col > a.col)
        for side, lst in (("L", [e for e in fl.ins[k] if not e.via_gap]),
                          ("R", [e for e in fl.outs[k] if e.pa != "G"])):
            byrow = {}
            for e in sorted(lst, key=lambda e: e.order):
                o = nodes[e.a] if side == "L" else nodes[e.b]
                r = o.row if o.lane == n.lane else n.row
                byrow.setdefault(r, []).append(e)
            for r, group in byrow.items():
                group.sort(key=lambda e: 0 if (nodes[e.a if side == "L" else e.b].row == r and
                                               nodes[e.a if side == "L" else e.b].lane == n.lane) else 1)
                for i, e in enumerate(group):
                    sub = (i + 1) // 2 * (1 if i % 2 else -1) if i else 0
                    if side == "L":
                        e.bar_b = (r, sub)
                    else:
                        e.bar_a = (r, sub)
        rows = [n.row]
        for e in fl.ins[k]:
            if not e.via_gap:
                rows.append(e.bar_b[0])
        for e in fl.outs[k]:
            if e.pa != "G":
                rows.append(e.bar_a[0])
        if getattr(n, "gapjoin", False):
            continue
        n.span = (min(rows), max(rows))
        for r in range(n.span[0], n.span[1] + 1):
            fl.cells.setdefault((n.lane, r, n.col), k)
    for n in sorted(nodes.values(), key=lambda n: n.order):
        if n.kind == "note":
            near = nodes.get(n.near)
            fl.place(n, near.row + 1 if near and near.lane == n.lane else 0)
            fl.nrows[n.lane] = max(fl.nrows[n.lane], n.row + 1)


def port_key(fl, n, p, e, end):
    """order-only coordinates of a port, before real geometry exists:
    x key (2c+1, sub) for a column, y key (lane, 2r+1, sub) for a row"""
    li = fl.lane_ix[n.lane]
    if p == "G":
        return (2 * n.col + 1, 0.5), (li, 2 * n.row, 0)
    if n.kind in BARS and p in ("L", "R"):
        if end == "b" and getattr(e, "via_gap", False):
            return (2 * n.col + 1, 0), (li, 2 * n.row + 1, 0)
        r, sub = (e.bar_b if end == "b" else e.bar_a)
        return (2 * n.col + 1, 0), (li, 2 * r + 1, sub)
    sub_y = {"D": 0.5, "U": -0.5}.get(p, 0)
    if p.startswith("L") and len(p) > 1:
        sub_y = 0.3 * int(p[1:])
    sub_x = 0.5 if p in ("D", "U") else 0
    return (2 * n.col + 1, sub_x), (li, 2 * n.row + 1, sub_y)


def clear_row(fl, lane, row, c1, c2):
    return all((lane, row, c) not in fl.cells for c in range(c1 + 1, c2))


def clear_col(fl, a, b):
    """nothing between node a and node b straight down/up their shared column"""
    lanes = [l[0] for l in fl.lanes]
    ia, ib = fl.lane_ix[a.lane], fl.lane_ix[b.lane]
    (top, bot) = (a, b) if (ia, a.row) < (ib, b.row) else (b, a)
    it, ib2 = fl.lane_ix[top.lane], fl.lane_ix[bot.lane]
    for L in range(it, ib2 + 1):
        lane = lanes[L]
        r0 = top.row + 1 if L == it else 0
        r1 = bot.row - 1 if L == ib2 else fl.nrows[lane] - 1
        for r in range(r0, r1 + 1):
            if (lane, r, a.col) in fl.cells:
                return False
    return True


def route(fl, e):
    """abstract route: the fixed coordinate of every straight piece, start to end.
    each item is ('P', ...) for a coordinate taken from a port, ('V', c) a vertical
    channel left of column c, ('G', lane, g) the gap above row g of a lane."""
    A, B = fl.nodes[e.src], fl.nodes[e.dst]
    pa, pb = e.pa, e.pb[0]
    la, lb = A.lane, B.lane
    hstart = pa in ("R",)
    hend = pb == "L"
    if getattr(e, "via_gap", False):
        return [("P", "a"), ("G", la, A.row + (1 if pa == "B" else 0)), ("P", "b")]
    if pa == "G":
        pa = "B"
        A = _GapView(A)
    if pa == "R" and pb == "L" and la == lb:
        ra = e.bar_a[0] if A.kind in BARS else A.row
        rb = e.bar_b[0] if B.kind in BARS else B.row
        sa = e.bar_a[1] if A.kind in BARS else 0
        sb = e.bar_b[1] if B.kind in BARS else 0
        if ra == rb and sa == sb and B.col > A.col and clear_row(fl, la, ra, A.col, B.col) \
                and not (A.kind not in BARS and B.kind not in BARS and e.pb != "L"):
            return [("P", "a")]
    if pa in ("D", "U", "B", "T") and pb in ("T", "B") and A.col == B.col and e.kind == "data" \
            and clear_col(fl, A, B):
        return [("P", "a")]
    if pa in ("B", "T") and pb in ("T", "B") and A.col == B.col and pa != pb and clear_col(fl, A, B) \
            and ((pa == "B") == ((fl.lane_ix[la], A.row) < (fl.lane_ix[lb], B.row))):
        return [("P", "a")]

    # channel each end runs into
    if hstart:
        c1 = ("V", A.col + 1)
    else:
        c1 = ("G", la, A.row + (1 if pa in ("B", "D") else 0))
    if hend:
        c2 = ("V", B.col)
    else:
        c2 = ("G", lb, B.row + (0 if pb == "T" else 1))

    mid = []
    if c1 == c2:
        mid = [c1]
    elif c1[0] == "V" and c2[0] == "V":
        down = (fl.lane_ix[lb], B.row) >= (fl.lane_ix[la], A.row)
        mid = [c1, ("G", la, A.row + (1 if down else 0)), c2]
    elif c1[0] != c2[0]:
        mid = [c1, c2]
    else:
        v = ("V", B.col) if not e.back else ("V", B.col)
        if e.kind == "data" and B.col == A.col:
            v = ("V", B.col + 1)
        mid = [c1, v, c2]
    return [("P", "a")] + mid + [("P", "b")]


def _span(lo, hi):
    return tuple(h - l for h, l in zip(hi, lo))


class _GapView:
    """a gap join seen as a node sitting just above its gap, leaving downward into it"""
    def __init__(self, n):
        self.__dict__.update(n.__dict__)
        self.row = n.row - 1


def build_routes(fl):
    for e in fl.edges:
        e.route = route(fl, e)
    # collect channel pieces for track assignment
    chans = {}
    for e in fl.edges:
        R = e.route
        if len(R) == 1:
            continue
        A, B = fl.nodes[e.src], fl.nodes[e.dst]
        ka = port_key(fl, A, e.pa, e, "a")
        kb = port_key(fl, B, e.pb, e, "b")
        for i in range(1, len(R) - 1):
            ch = R[i]
            prev = R[i - 1]
            nxt = R[i + 1]
            ends = []
            for item, is_prev in ((prev, True), (nxt, False)):
                if item[0] == "P":
                    k = ka if is_prev else kb
                    ends.append(k[1] if ch[0] == "V" else k[0])
                elif item[0] == "V":
                    ends.append((2 * item[1], 0))
                else:
                    ends.append((fl.lane_ix[item[1]], 2 * item[2], 0))
            lo, hi = sorted(ends)
            # a port whose stub crosses this channel: (key, low|high side of the channel)
            att = []
            perp = ("R", "L") if ch[0] == "V" else ("B", "T", "D", "U")
            if i == 1 and e.pa in perp:
                att.append((ka[1] if ch[0] == "V" else ka[0], "low" if e.pa in ("R", "B", "D") else "high"))
            if i == len(R) - 2 and e.pb[0] in perp and not getattr(e, "via_gap", False):
                att.append((kb[1] if ch[0] == "V" else kb[0], "high" if e.pb[0] in ("L", "T") else "low"))
            chans.setdefault(ch, []).append(dict(lo=lo, hi=hi, att=att, e=e, i=i))
    fl.tracks = {}
    for ch, segs in chans.items():
        # shortest pieces take the inner tracks so bundles nest instead of crossing
        segs.sort(key=lambda s: (_span(s["lo"], s["hi"]), s["lo"]))
        # a stub from the low side must sit on a lower track than a stub from the high
        # side at the same spot, or the two stubs would run over each other
        pairs = []
        for a in segs:
            for b in segs:
                if a is not b and any(ka == kb and sa == "low" and sb == "high"
                                      for ka, sa in a["att"] for kb, sb in b["att"]):
                    pairs.append((a, b))
        floor = {id(s): 0 for s in segs}
        for _ in range(len(segs) + 2):
            tracks = []
            for sg in segs:
                t = floor[id(sg)]
                while t < len(tracks) and any(sg["lo"] <= o["hi"] and o["lo"] <= sg["hi"] for o in tracks[t]):
                    t += 1
                while t >= len(tracks):
                    tracks.append([])
                tracks[t].append(sg)
                sg["t"] = t
            bad = [(a, b) for a, b in pairs if a["t"] >= b["t"]]
            if not bad:
                break
            for a, b in bad:
                floor[id(b)] = max(floor[id(b)], a["t"] + 1)
        for sg in segs:
            sg["e"].route[sg["i"]] = ch + (sg["t"],)
        fl.tracks[ch] = len(tracks)

# ====================================================================== geometry

OUT_W, GRP_W, LAB_W = 30, 30, 70
X0 = OUT_W + GRP_W + LAB_W
PAD_R = 30
VT, GT = 14, 22                     # spacing between tracks: vertical channel / gap
BAR_STEP = 18                       # spacing between lines meeting one side of a bar


def geometry(fl, vmin, gmin):
    nodes = fl.nodes
    C = fl.ncol
    NW = [60] * C
    for n in nodes.values():
        NW[n.col] = max(NW[n.col], n.w)
    VW = []
    for c in range(C + 1):
        t = fl.tracks.get(("V", c), 0)
        VW.append(max(44, 20 + t * VT, vmin.get(c, 0)))
    xs, x = [], X0
    for c in range(C):
        x += VW[c]
        xs.append(x)
        x += NW[c]
    fl.W = x + VW[C] + PAD_R
    fl.colx = [xs[c] + NW[c] / 2 for c in range(C)]
    fl.vx = {}
    for c in range(C + 1):
        left = (xs[c - 1] + NW[c - 1]) if c > 0 else X0
        t = fl.tracks.get(("V", c), 0)
        span = (t - 1) * VT
        start = left + (VW[c] - span) / 2
        for k in range(t):
            fl.vx[(c, k)] = start + k * VT

    fl.title_h = 60 + 24 * max(1, len(fl.subtitles))
    y = fl.title_h
    fl.lane_box, fl.rowy, fl.gy, fl.row_h = {}, {}, {}, {}
    for lane, _role, name in fl.lanes:
        R = fl.nrows[lane]
        RH = [40] * R
        for n in nodes.values():
            if n.lane == lane and n.kind not in BARS:
                RH[n.row] = max(RH[n.row], n.h + (end_lab_h(n) if n.kind in ENDS + ("actor",) else 0))
        for e in fl.edges:              # room for stacked bar ports
            for end in ("a", "b"):
                nn = nodes[e.a if end == "a" else e.b]
                slot = getattr(e, "bar_" + end, None)
                if nn.kind in BARS and nn.lane == lane and slot and e.kind == "flow":
                    RH[slot[0]] = max(RH[slot[0]], 2 * BAR_STEP * abs(slot[1]) + 40)
        top = y
        for g in range(R + 1):
            t = fl.tracks.get(("G", lane, g), 0)
            gh = max(26 if 0 < g < R else 22, 14 + t * GT, gmin.get((lane, g), 0))
            ys = y + (gh - (t - 1) * GT) / 2 + 6
            for k in range(t):
                fl.gy[(lane, g, k)] = ys + k * GT
            if g == R:                  # the lane is at least as tall as its rotated name
                need = max(text_w(t, 14) for t in name) + 24 - (y + gh - top)
                if need > 0:
                    gh += need
            y += gh
            if g < R:
                fl.rowy[(lane, g)] = y + RH[g] / 2
                fl.row_h[(lane, g)] = RH[g]
                y += RH[g]
        fl.lane_box[lane] = (top, y - top)
    fl.H = y + 26

    for n in nodes.values():
        n.x = fl.colx[n.col]
        if getattr(n, "gapjoin", False):
            n.y = None
            continue
        n.y = fl.rowy[(n.lane, n.row)]
        if n.kind in ENDS + ("actor",):
            n.y -= 11
    # bars stretch over their ports
    for n in nodes.values():
        if n.kind in BARS:
            ys = [n.y] if n.y is not None else []
            for e in fl.edges:
                if e.a == n.id and e.kind == "flow":
                    if e.pa == "G":
                        g = e.route[1]
                        ys.append(fl.gy[(g[1], g[2], g[3])])
                    else:
                        ys.append(bar_y(fl, n, e.bar_a))
                if e.b == n.id and e.kind == "flow":
                    if getattr(e, "via_gap", False):
                        g = e.route[1]
                        ys.append(fl.gy[(g[1], g[2], g[3])])
                    else:
                        ys.append(bar_y(fl, n, e.bar_b))
            pad = 10 if getattr(n, "gapjoin", False) else 18
            n.top, n.bot = min(ys) - pad, max(ys) + pad
            n.h = n.bot - n.top
            n.y = (n.top + n.bot) / 2


def bar_y(fl, n, slot):
    r, sub = slot
    return fl.rowy[(n.lane, r)] + BAR_STEP * sub


def port_xy(fl, n, p, e, end):
    if n.kind in BARS and p in ("L", "R"):
        y = bar_y(fl, n, e.bar_b if end == "b" else e.bar_a)
        return (n.x - 5 if p == "L" else n.x + 5), y
    w, h = n.w, n.h
    if n.kind in ENDS + ("merge",):
        w = h = n.w
    if p == "R":
        return n.x + w / 2, n.y
    if p.startswith("L"):
        off = 0 if len(p) == 1 else (-12 if p == "L1" else 12)
        return n.x - w / 2, n.y + off
    if p == "T":
        return n.x, n.y - h / 2
    if p == "B":
        return n.x, n.y + h / 2
    if p in ("D", "U"):
        s = 1 if p == "D" else -1
        if n.kind == "cond":
            return n.x + w / 4, n.y + s * h / 4
        if n.kind in ENDS + ("merge", "actor"):
            return n.x + w * 0.35, n.y + s * h * 0.35
        return n.x + w / 4, n.y + s * h / 2
    raise ValueError(p)


def points(fl, e):
    A, B = fl.nodes[e.src], fl.nodes[e.dst]
    if e.pa == "G":
        g = e.route[1]
        P = (A.x + 5, fl.gy[(g[1], g[2], g[3])])
    else:
        P = port_xy(fl, A, e.pa, e, "a")
    if getattr(e, "via_gap", False):
        g = e.route[1]
        gy = fl.gy[(g[1], g[2], g[3])]
        return [P, (P[0], gy), (B.x - 5, gy)]
    Q = port_xy(fl, B, e.pb, e, "b")
    if e.kind == "data" and len(e.route) == 1:
        Q = (P[0], Q[1])                     # straight down onto the store
    R = e.route
    hstart = e.pa == "R" or (e.pa.startswith("L"))
    fixed = []
    fixed.append(P[1] if hstart else P[0])
    for it in R[1:-1]:
        if it[0] == "V":
            fixed.append(fl.vx[(it[1], it[2])])
        else:
            fixed.append(fl.gy[(it[1], it[2], it[3])])
    pts = [P]
    horiz = hstart
    cur = P
    for f in fixed[1:]:
        nxt = (f, cur[1]) if horiz else (cur[0], f)
        pts.append(nxt)
        cur = nxt
        horiz = not horiz
    pts.append((Q[0], cur[1]) if horiz else (cur[0], Q[1]))
    if pts[-1] != Q:
        pts.append(Q)
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) > 0.01 or abs(p[1] - out[-1][1]) > 0.01:
            out.append(p)
    return out


def segments(pts):
    return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]

# ====================================================================== geometry lint + labels


def node_rect(n, pad=0):
    if n.kind in BARS:
        return (n.x - 5 - pad, n.top - pad, n.x + 5 + pad, n.bot + pad)
    return (n.x - n.w / 2 - pad, n.y - n.h / 2 - pad, n.x + n.w / 2 + pad, n.y + n.h / 2 + pad)


def place_labels(fl, edges, nodes_on):
    boxes = [node_rect(n, 2) for n in nodes_on]
    for n in nodes_on:
        if n.kind in ENDS + ("actor",):
            half = max([60] + [text_w(t, 11.5) / 2 + 4 for t in n.lines]) if n.kind in ENDS else 60
            boxes.append((n.x - half, n.y + n.h / 2, n.x + half, n.y + n.h / 2 + end_lab_h(n)))
        if n.kind in BARS and n.lines:
            tw = max(text_w(t, 11.5) for t in n.lines)
            boxes.append((n.x - tw / 2, n.bot + 4, n.x + tw / 2, n.bot + 22))
    need = {}
    for e in edges:
        e.lab = None
        if not e.label:
            continue
        size = 11 if e.kind == "data" else 11.5
        tw = text_w(e.label, size) + 6
        best = None
        for (p, q) in segments(e.pts):
            if abs(p[1] - q[1]) < 0.01 and abs(q[0] - p[0]) >= tw + 14:
                d = 1 if q[0] > p[0] else -1
                room = abs(q[0] - p[0]) - tw - 16
                found = False
                for step in range(0, int(room) + 1, 24):
                    x0 = p[0] + 8 + step if d > 0 else p[0] - 8 - tw - step
                    box = (x0, p[1] - 15, x0 + tw, p[1] - 2)
                    if not any(_hit(box, b) for b in boxes):
                        best = (x0 + tw / 2, p[1] - 6, box)
                        found = True
                        break
                    if best is None:
                        best = (x0 + tw / 2, p[1] - 6, box, "clash")
                if found:
                    break
            elif abs(p[0] - q[0]) < 0.01 and abs(q[1] - p[1]) >= 24 and (e.kind == "data" or len(e.pts) == 2):
                ym = (p[1] + q[1]) / 2
                box = (p[0] + 6, ym - 9, p[0] + 6 + tw, ym + 5)
                if not any(_hit(box, b) for b in boxes):
                    best = (p[0] + 6, ym + 1, box, "start")
                    break
        if best is None:
            seg = segments(e.pts)[0]
            need[e] = (seg, tw)
            best = (e.pts[0][0] + tw / 2 + 8, e.pts[0][1] - 6, (0, 0, 0, 0), "clash")
        e.lab = best
        boxes.append(best[2])
    return need


def _hit(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def lint_geometry(fl, edges, nodes_on, report=True):
    E = []
    segs = []
    for e in edges:
        for s in segments(e.pts):
            segs.append((e, s))
    # one line = one track: no shared pieces between different lines
    for i in range(len(segs)):
        e1, (p1, q1) = segs[i]
        for j in range(i + 1, len(segs)):
            e2, (p2, q2) = segs[j]
            if e1 is e2:
                continue
            if abs(p1[1] - q1[1]) < .01 and abs(p2[1] - q2[1]) < .01 and abs(p1[1] - p2[1]) < 1:
                lo = max(min(p1[0], q1[0]), min(p2[0], q2[0]))
                hi = min(max(p1[0], q1[0]), max(p2[0], q2[0]))
                if hi - lo > 1:
                    E.append(f"{e1.tag} and {e2.tag} share a piece of line (rule 1)")
            if abs(p1[0] - q1[0]) < .01 and abs(p2[0] - q2[0]) < .01 and abs(p1[0] - p2[0]) < 1:
                lo = max(min(p1[1], q1[1]), min(p2[1], q2[1]))
                hi = min(max(p1[1], q1[1]), max(p2[1], q2[1]))
                if hi - lo > 1:
                    E.append(f"{e1.tag} and {e2.tag} share a piece of line (rule 1)")
    # a line never runs through a shape that is not its own end
    for e, (p, q) in segs:
        for n in nodes_on:
            if n.id in (e.src, e.dst) or n.kind in BARS:
                continue
            r = node_rect(n, -1)
            x1, x2 = sorted((p[0], q[0]))
            y1, y2 = sorted((p[1], q[1]))
            if x1 < r[2] and r[0] < x2 + .01 and y1 < r[3] and r[1] < y2 + .01:
                E.append(f"{e.tag} runs through {n.id}")
    # shapes never overlap
    on = [n for n in nodes_on]
    for i in range(len(on)):
        for j in range(i + 1, len(on)):
            if _hit(node_rect(on[i], 1), node_rect(on[j], 1)):
                E.append(f"{on[i].id} and {on[j].id} overlap (rule 6)")
    for e in edges:
        if e.lab and len(e.lab) > 3 and e.lab[3] == "clash":
            fl.warnings.append(f"label of {e.tag} sits on something — check the picture")
    return sorted(set(E))


def hops_for(edges, nodes_on):
    """an H piece gets a small bridge wherever another line's V piece (or a bar) crosses it"""
    verts = []
    for e in edges:
        for p, q in segments(e.pts):
            if abs(p[0] - q[0]) < .01:
                verts.append((e, p[0], min(p[1], q[1]), max(p[1], q[1])))
    for n in nodes_on:
        if n.kind in BARS:
            verts.append((None, n.x, n.top, n.bot))
    for e in edges:
        e.hops = {}
        for i, (p, q) in enumerate(segments(e.pts)):
            if abs(p[1] - q[1]) > .01:
                continue
            x1, x2 = sorted((p[0], q[0]))
            hs = [vx for (o, vx, y1, y2) in verts
                  if o is not e and x1 + 10 < vx < x2 - 10 and y1 + .5 < p[1] < y2 - .5]
            if hs:
                e.hops[i] = sorted(set(round(h, 2) for h in hs))

# ====================================================================== render

STYLE = """<style>
  .t-title{font-family:Kanit,'IBM Plex Sans Thai',sans-serif;font-size:31px;font-weight:600;fill:#16242A}
  .t-sub{font-family:'IBM Plex Sans Thai',sans-serif;font-size:14px;fill:#54666E}
  .t-lane{font-family:Kanit,'IBM Plex Sans Thai',sans-serif;font-size:14px;font-weight:500;fill:#1D2E35;text-anchor:middle;dominant-baseline:middle}
  .t-grp{font-family:'IBM Plex Sans Thai',sans-serif;font-size:13px;fill:#33474F;text-anchor:middle;dominant-baseline:middle}
  .t-node{font-family:'IBM Plex Sans Thai',sans-serif;font-size:13px;fill:#16242A;text-anchor:middle}
  .t-dec{font-family:'IBM Plex Sans Thai',sans-serif;font-size:12px;fill:#0F2A38;text-anchor:middle}
  .t-edge{font-family:'IBM Plex Sans Thai',sans-serif;font-size:11.5px;fill:#44525C;text-anchor:middle}
  .t-data{font-family:'IBM Plex Sans Thai',sans-serif;font-size:11px;fill:#6C7D85;text-anchor:start}
  .t-end{font-family:'IBM Plex Sans Thai',sans-serif;font-size:11.5px;fill:#8F3A28;text-anchor:middle}
  .t-done{font-family:'IBM Plex Sans Thai',sans-serif;font-size:11.5px;fill:#2F7D4F;text-anchor:middle}
  .n-task{fill:#FFFFFF;stroke:#5C7A8A;stroke-width:1.6}
  .n-dec{fill:#9CC3E0;stroke:#3E6E90;stroke-width:1.6}
  .n-store{fill:#FFFFFF;stroke:#96803A;stroke-width:1.6}
  .n-actor{fill:#D9B8D4;stroke:#7A5675;stroke-width:1.6}
  .n-end{fill:#D9705A;stroke:#8F3A28;stroke-width:1.8}
  .n-done{fill:#6DBB8A;stroke:#2F7D4F;stroke-width:1.8}
  .n-fork{fill:#44525C;stroke:#2B363D;stroke-width:1}
  .n-note{fill:#FBF1C2;stroke:#96803A;stroke-width:1.2}
  .n-merge{fill:#FFFFFF;stroke:#44525C;stroke-width:2}
  .t-note{font-family:'IBM Plex Sans Thai',sans-serif;font-size:11px;fill:#5B4E1E;text-anchor:middle}
  .fl{fill:none;stroke:#44525C;stroke-width:1.7}
  .fl-true{fill:none;stroke:#2F7D4F;stroke-width:1.8}
  .fl-false{fill:none;stroke:#B0402C;stroke-width:1.8}
  .fl-data{fill:none;stroke:#7C8C95;stroke-width:1.4;stroke-dasharray:5 4}
</style>"""

DEFS = """<defs>
<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#44525c"/></marker>
<marker id="arT" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#2F7D4F"/></marker>
<marker id="arF" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#B0402C"/></marker>
<marker id="arD" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#7C8C95"/></marker>
</defs>"""

LANE_FILL = {"client": "#CFE9D4", "3rd": "#D6CFEA"}
LANE_CYCLE = ["#C5DCF2", "#F7DCBE", "#FBF1C2", "#CFE6E8", "#E6DDF2", "#F3D5D5"]


def esc(s):
    return html.escape(s, quote=False)


def render(fl, title, subs, keep_nodes=None, keep_edges=None):
    nodes_on = [n for n in fl.nodes.values() if keep_nodes is None or n.id in keep_nodes]
    edges_on = [e for e in fl.edges if keep_edges is None or e.tag in keep_edges]
    hops_for(edges_on, nodes_on)
    W, H = fl.W, fl.H
    o = [f'<?xml version="1.0" encoding="UTF-8"?>',
         f'<svg class="swim" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" '
         f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(title)}">',
         STYLE, DEFS, f'<rect x="0" y="0" width="{W:.0f}" height="{H:.0f}" fill="#FFFFFF"/>',
         f'<text x="30" y="46" class="t-title">{esc(title)}</text>']
    for i, s in enumerate(subs):
        o.append(f'<text x="32" y="{74 + 22 * i}" class="t-sub">{esc(s)}</text>')
    ci = 0
    for lane, role, name in fl.lanes:
        top, h = fl.lane_box[lane]
        fill = LANE_FILL.get(role)
        if not fill:
            fill = LANE_CYCLE[ci % len(LANE_CYCLE)]
            ci += 1
        o.append(f'<rect x="{X0}" y="{top:.1f}" width="{W - X0 - PAD_R:.0f}" height="{h:.1f}" fill="{fill}" '
                 f'stroke="#7FA8C4" stroke-width="2"/>')
        o.append(f'<rect x="{OUT_W + GRP_W}" y="{top:.1f}" width="{LAB_W}" height="{h:.1f}" fill="#FFFFFF" '
                 f'stroke="#7FA8C4" stroke-width="2"/>')
        lx, ly = OUT_W + GRP_W + LAB_W / 2, top + h / 2
        for i, line in enumerate(name):
            off = (i - (len(name) - 1) / 2) * 15
            o.append(f'<text x="{lx + off:.1f}" y="{ly:.1f}" class="t-lane" '
                     f'transform="rotate(-90 {lx + off:.1f} {ly:.1f})">{esc(line)}</text>')
    top_all = fl.lane_box[fl.lanes[0][0]][0]
    last = fl.lane_box[fl.lanes[-1][0]]
    for gname, glanes in fl.groups:
        ts = [fl.lane_box[g] for g in glanes if g in fl.lane_box]
        if not ts:
            continue
        t1, t2 = min(t for t, _ in ts), max(t + h for t, h in ts)
        o.append(f'<rect x="{OUT_W}" y="{t1:.1f}" width="{GRP_W}" height="{t2 - t1:.1f}" fill="#EEF3F6" '
                 f'stroke="#7FA8C4" stroke-width="2"/>')
        mx, my = OUT_W + GRP_W / 2, (t1 + t2) / 2
        o.append(f'<text x="{mx}" y="{my:.1f}" class="t-grp" transform="rotate(-90 {mx} {my:.1f})">{esc(gname)}</text>')
    t2 = last[0] + last[1]
    o.append(f'<rect x="0" y="{top_all:.1f}" width="{OUT_W}" height="{t2 - top_all:.1f}" fill="#FFFFFF" '
             f'stroke="#7FA8C4" stroke-width="2"/>')
    mx, my = OUT_W / 2, (top_all + t2) / 2
    o.append(f'<text x="{mx}" y="{my:.1f}" class="t-grp" transform="rotate(-90 {mx} {my:.1f})">Business Condition</text>')

    for n in sorted(nodes_on, key=lambda n: n.order):
        o.append(f'<g data-el="{n.id}">')
        o.extend(draw_node(n))
        o.append('</g>')
    for e in sorted(edges_on, key=lambda e: e.order):
        o.append(f'<g data-el="{e.tag}">')
        o.extend(draw_edge(e))
        o.append('</g>')
    o.append('</svg>')
    return "\n".join(o) + "\n"


def _lines(x, y, lines, cls, step):
    k = len(lines)
    return [f'<text x="{x:.1f}" y="{y - (k - 1) * step / 2 + i * step + 4.5:.1f}" class="{cls}">{esc(t)}</text>'
            for i, t in enumerate(lines)]


def draw_node(n):
    x, y, w, h = n.x, n.y, n.w, n.h
    k = n.kind
    if k == "task":
        return [f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="3" class="n-task"/>'] \
            + _lines(x, y, n.lines, "t-node", 15)
    if k == "cond":
        return [f'<polygon points="{x:.1f},{y - h / 2:.1f} {x + w / 2:.1f},{y:.1f} {x:.1f},{y + h / 2:.1f} '
                f'{x - w / 2:.1f},{y:.1f}" class="n-dec"/>'] + _lines(x, y - 0.5, n.lines, "t-dec", 13)
    if k == "store":
        return [f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="14" class="n-store"/>'] \
            + _lines(x, y, n.lines, "t-node", 14)
    if k == "note":
        return [f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="3" class="n-note"/>'] \
            + _lines(x, y, n.lines, "t-note", 14)
    if k == "actor":
        r = 26
        pts = " ".join(f"{x + r * dx:.1f},{y + r * dy:.1f}" for dx, dy in
                       [(0, -1), (.87, -.5), (.87, .5), (0, 1), (-.87, .5), (-.87, -.5)])
        return [f'<polygon points="{pts}" class="n-actor"/>'] + \
            [f'<text x="{x:.1f}" y="{y + r + 17:.1f}" class="t-node">{esc(" ".join(n.lines))}</text>']
    if k in ENDS:
        return [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" class="n-{k}"/>',
                *[f'<text x="{x:.1f}" y="{y + 32 + 14 * i:.1f}" class="t-{k}">{esc(t)}</text>' for i, t in enumerate(n.lines)]]
    if k == "merge":
        out = [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" class="n-merge"/>']
        if n.lines:
            out.append(f'<text x="{x:.1f}" y="{y + 30:.1f}" class="t-edge">{esc(" ".join(n.lines))}</text>')
        return out
    out = [f'<rect x="{x - 5:.1f}" y="{n.top:.1f}" width="10" height="{n.bot - n.top:.1f}" rx="2" class="n-fork"/>']
    if n.lines:
        out.append(f'<text x="{x:.1f}" y="{n.bot + 18:.1f}" class="t-edge">{esc(" ".join(n.lines))}</text>')
    return out


def draw_edge(e):
    if e.kind == "data":
        cls, mk = "fl-data", "arD"
    elif e.branch == "yes":
        cls, mk = "fl-true", "arT"
    elif e.branch == "no":
        cls, mk = "fl-false", "arF"
    else:
        cls, mk = "fl", "ar"
    pts = e.pts
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i, (p, q) in enumerate(segments(pts)):
        hs = e.hops.get(i, [])
        if hs:
            right = q[0] > p[0]
            for hx in (sorted(hs) if right else sorted(hs, reverse=True)):
                a, b = (hx - 8, hx + 8) if right else (hx + 8, hx - 8)
                d += f" L{a:.1f},{p[1]:.1f} A 8 8 0 0 {1 if right else 0} {b:.1f},{p[1]:.1f}"
        d += f" L{q[0]:.1f},{q[1]:.1f}"
    out = [f'<path d="{d}" class="{cls}" marker-end="url(#{mk})"/>']
    if e.label and e.lab:
        lx, ly = e.lab[0], e.lab[1]
        if e.kind == "data" or (len(e.lab) > 3 and e.lab[3] == "start"):
            out.append(f'<text x="{lx:.1f}" y="{ly:.1f}" class="t-data">{esc(e.label)}</text>')
        else:
            out.append(f'<text x="{lx:.1f}" y="{ly:.1f}" class="t-edge">{esc(e.label)}</text>')
    return out

# ====================================================================== scenarios


def scenario_keep(fl, sc):
    chains = []
    for u in sc["use"]:
        if u not in fl.segments:
            fl.errors.append(f"line {sc['line']}: scenario {sc['name']} uses unknown segment '{u}'")
            continue
        chains += fl.segments[u]
    chains += sc["paths"]
    keep_n, keep_e = set(), set()
    by_pair = {}
    for e in fl.edges:
        if e.kind == "flow":
            by_pair[(e.a, e.b)] = e
    for ch in chains:
        for k in ch:
            if k not in fl.nodes:
                fl.errors.append(f"line {sc['line']}: scenario {sc['name']} names unknown node '{k}'")
            keep_n.add(k)
        for a, b in zip(ch, ch[1:]):
            e = by_pair.get((a, b))
            if e is None:
                fl.errors.append(f"line {sc['line']}: scenario {sc['name']}: no line {a} -> {b}")
            else:
                keep_e.add(e.tag)
    for e in fl.edges:
        if e.kind == "data" and e.src in keep_n:
            keep_n.add(e.dst)
            keep_e.add(e.tag)
    for n in fl.nodes.values():
        if n.kind == "note" and n.near in keep_n:
            keep_n.add(n.id)
    return keep_n, keep_e

# ====================================================================== main


def build(fl):
    """layout, route and settle geometry; returns geometry errors"""
    size_nodes(fl)
    def rank(l):                                       # client · services · datastores · 3rd party
        if l[1] == "client":
            return 0
        if l[1] == "3rd":
            return 3
        kinds = {n.kind for n in fl.nodes.values() if n.lane == l[0] and n.kind != "note"}
        return 2 if kinds == {"store"} else 1           # a lane holding only stores is a datastore
    fl.lanes.sort(key=rank)
    layout(fl)
    for e in fl.edges:
        if e.back and fl.nodes[e.b].kind != "merge":
            fl.errors.append(f"line {e.line}: {e.a} -> {e.b} goes back (a loop) — loop back into a merge "
                             f"placed right before the loop starts (rule 5)")
    assign_ports(fl)
    build_routes(fl)
    vmin, gmin = {}, {}
    for _ in range(6):
        geometry(fl, vmin, gmin)
        for e in fl.edges:
            e.pts = points(fl, e)
        need = place_labels(fl, fl.edges, list(fl.nodes.values()))
        if not need:
            break
        grew = False
        for e, (seg, tw) in need.items():
            p, q = seg
            if abs(p[1] - q[1]) < .01:                    # widen the channel the first piece crosses
                c = channel_at(fl, max(p[0], q[0]))
                if c is not None:
                    cur = vmin.get(c, 0)
                    want = int(tw + 40 + fl.tracks.get(("V", c), 0) * VT)
                    if want > cur:
                        vmin[c] = want
                        grew = True
            else:
                node = fl.nodes[e.src]
                key = (node.lane, node.row + (1 if p[1] < q[1] else 0))
                if gmin.get(key, 0) < 60:
                    gmin[key] = 60
                    grew = True
        if not grew:
            break
    return lint_geometry(fl, fl.edges, list(fl.nodes.values()))


def channel_at(fl, x):
    best, bd = None, 1e9
    for c in range(fl.ncol + 1):
        left = fl.colx[c - 1] if c > 0 else X0
        right = fl.colx[c] if c < fl.ncol else fl.W
        if left <= x <= right + 1:
            d = abs(x - (left + right) / 2)
            if d < bd:
                best, bd = c, d
    return best


def coverage(fl, keeps):
    covered = set()
    for _n, ke in keeps:
        covered |= ke
    miss = [e.tag for e in fl.edges if e.kind == "flow" and fl.nodes[e.a].kind == "cond" and e.tag not in covered]
    if miss and fl.scenarios:
        fl.warnings.append("no scenario walks these ways out of a cond: " + ", ".join(miss))


def to_png(svgs, out_dir):
    tool = shutil.which("rsvg-convert")
    chrome = None
    for c in ("google-chrome", "chromium", "chromium-browser", "chrome",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if shutil.which(c) or os.path.exists(c):
            chrome = shutil.which(c) or c
            break
    if not tool and not chrome:
        print("png: no rsvg-convert or Chrome found — open the SVGs in a browser to check them")
        return
    os.makedirs(out_dir, exist_ok=True)
    for path, w, h in svgs:
        name = os.path.relpath(path).replace(os.sep, "__").replace(".svg", ".png")
        dst = os.path.join(out_dir, name)
        if tool:
            subprocess.run([tool, "-o", dst, path], check=False)
        else:
            subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
                            f"--screenshot={dst}", f"--window-size={int(w)},{int(h)}",
                            "file://" + os.path.abspath(path)], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"png: {dst}")


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0 if len(argv) >= 2 else 2
    src = argv[1]
    png = "--png" in argv
    png_dir = None
    if png:
        i = argv.index("--png")
        png_dir = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else tempfile.mkdtemp(prefix="swimlane-")
    fl = parse(src)
    if not fl.errors:
        check_model(fl)
    if fl.errors:
        for m in fl.errors:
            print("error:", m)
        return 1
    geo = build(fl)
    base = os.path.dirname(os.path.abspath(src))
    written = []
    out = os.path.join(base, "swimlane.svg")
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(fl, fl.title, fl.subtitles))
    written.append((out, fl.W, fl.H))
    keeps = []
    for sc in fl.scenarios:
        kn, ke = scenario_keep(fl, sc)
        keeps.append((sc["name"], ke))
        subs = [f"Scenario: {sc['desc']}"] + ([sc["note"]] if sc["note"] else [])
        folder = os.path.join(base, sc["cat"], f"{sc['nn']}-{sc['name']}")
        os.makedirs(folder, exist_ok=True)
        p = os.path.join(folder, "flow.svg")
        on_nodes = [fl.nodes[k] for k in kn if k in fl.nodes]
        on_edges = [e for e in fl.edges if e.tag in ke]
        place_labels(fl, on_edges, on_nodes)
        with open(p, "w", encoding="utf-8") as f:
            f.write(render(fl, sc["name"], subs, kn, ke))
        written.append((p, fl.W, fl.H))
    place_labels(fl, fl.edges, list(fl.nodes.values()))
    coverage(fl, keeps)
    for p, _w, _h in written:
        print("wrote", os.path.relpath(p))
    for m in fl.warnings:
        print("warn:", m)
    for m in geo + fl.errors:
        print("error:", m)
    if png:
        to_png(written, png_dir)
    return 1 if (geo or fl.errors) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
