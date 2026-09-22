#!/usr/bin/env python3
"""สร้าง swimlane SVG แบบ lane แนวนอนซ้อนบนลงล่าง flow วิ่งซ้าย->ขวา
ตาม format ที่ทีมใช้ (MAINTAIN_EDIT_CART_ADD_ITEM_BY_ADMIN)
"""
import html

# ---------- geometry ----------
OUT_W, GRP_W, LAB_W = 30, 30, 70          # คอลัมน์ซ้าย: bracket รวม / กลุ่ม / ชื่อ lane
X0 = OUT_W + GRP_W + LAB_W                  # ซ้ายสุดของพื้นที่ lane
COLW = 200
NCOL = 40
TITLE_H = 118
PAD_R = 30
W = X0 + NCOL * COLW + PAD_R

LANES = [
    # key,      ชื่อ,                        สูง,  สีพื้น,     กลุ่ม
    ("cust",   ["ลูกค้า"],                   150, "#CFE9D4", "front"),
    ("pubsub", ["Pub/Sub"],                  100, "#C5DCF2", "back"),
    ("svc",    ["live-stream", "consumer"],  800, "#F7DCBE", "back"),
    ("mongo",  ["MongoDB"],                  120, "#FBF1C2", "back"),
    ("redis",  ["Redis"],                    104, "#CFE6E8", "back"),
    ("fb",     ["3rd", "Facebook"],          210, "#D6CFEA", "back"),
]

LY, y = {}, TITLE_H
for key, _n, h, _c, _g in LANES:
    LY[key] = (y, h)
    y += h
H = y + 26

def lane_mid(key, off=0):
    top, h = LY[key]
    return top + h / 2 + off

def cx(col):
    return X0 + col * COLW + COLW / 2

# แถวภายใน lane ของ service
SVC_TOP = LY["svc"][0]
ROW_MAIN = SVC_TOP + 104
ROW_UP = ROW_MAIN - 80
ROW_DOWN = ROW_MAIN + 104
ROW_DOWN2 = ROW_MAIN + 208
ROW_DOWN3 = ROW_MAIN + 312
ROW_DOWN4 = ROW_MAIN + 416
LOOP_BACK = ROW_MAIN + 496
SKIP_FWD  = ROW_MAIN + 556
BOT_BACK  = ROW_MAIN + 616
ROW_END = ROW_MAIN + 348
TYPE_ROW = ROW_MAIN + 430

FB_TOP = LY["fb"][0]
FB_MAIN = FB_TOP + 74
FB_END = FB_TOP + 156

out = []
A = out.append

def tagged(fn):
    """ห่อสิ่งที่ฟังก์ชันวาดไว้ใน <g data-el> เพื่อให้ตัดออกตอนทำ scenario ได้"""
    def wrap(*a, tag=None, **kw):
        i = len(out)
        r = fn(*a, **kw)
        if tag is not None:
            out.insert(i, f'<g data-el="{tag}">')
            out.append("</g>")
        return r
    wrap.__name__ = fn.__name__
    return wrap

# ---------- defs ----------
A(f'<svg class="swim" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
  f'xmlns="http://www.w3.org/2000/svg" role="img" '
  f'aria-label="Swimlane เส้นทางบอทตอบคอมเมนต์">')
A('''<defs>
<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z" fill="#44525c"/>
</marker>
<marker id="arS" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z" fill="#B0402C"/>
</marker>
<marker id="arT" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z" fill="#2F7D4F"/>
</marker>
<marker id="arF" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z" fill="#B0402C"/>
</marker>
<marker id="arD" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z" fill="#7C8C95"/>
</marker>
</defs>''')
A(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>')

# ---------- title ----------
A('<text x="30" y="46" class="t-title">COMMENT_BOT_REPLY</text>')
A('<text x="32" y="74" class="t-sub">Scenario: ลูกค้าคอมเมนต์ใต้โพสต์ของร้าน '
  'แล้วบอทกดไลก์ ตอบใต้คอมเมนต์ และทักแชทกลับ</text>')
A('<text x="32" y="96" class="t-sub">flow วิ่งซ้ายไปขวา · '
  'ข้ามแถบขึ้นลงตามระบบที่รับผิดชอบ · เส้นประคือไปถามหรือไปบันทึกข้อมูล</text>')

# ---------- lane bands ----------
for key, name, h, color, grp in LANES:
    top, _ = LY[key]
    A(f'<rect x="{X0}" y="{top}" width="{W - X0 - PAD_R}" height="{h}" fill="{color}"/>')
    A(f'<rect x="{X0}" y="{top}" width="{W - X0 - PAD_R}" height="{h}" fill="none" stroke="#7FA8C4" stroke-width="2"/>')
    # ป้ายชื่อ lane (แนวตั้ง)
    lx = OUT_W + GRP_W + LAB_W / 2
    ly = top + h / 2
    A(f'<rect x="{OUT_W + GRP_W}" y="{top}" width="{LAB_W}" height="{h}" fill="#FFFFFF" stroke="#7FA8C4" stroke-width="2"/>')
    n = len(name)
    for i, line in enumerate(name):
        off = (i - (n - 1) / 2) * 15
        A(f'<text x="{lx + off}" y="{ly}" class="t-lane" '
          f'transform="rotate(-90 {lx + off} {ly})">{html.escape(line)}</text>')

# ---------- group brackets ----------
def bracket(x, wdt, key_from, key_to, label, fill):
    t1 = LY[key_from][0]
    t2 = LY[key_to][0] + LY[key_to][1]
    A(f'<rect x="{x}" y="{t1}" width="{wdt}" height="{t2 - t1}" fill="{fill}" stroke="#7FA8C4" stroke-width="2"/>')
    mx, my = x + wdt / 2, (t1 + t2) / 2
    A(f'<text x="{mx}" y="{my}" class="t-grp" transform="rotate(-90 {mx} {my})">{html.escape(label)}</text>')

bracket(OUT_W, GRP_W, "cust", "cust", "หน้าบ้าน", "#EAF4EC")
bracket(OUT_W, GRP_W, "pubsub", "fb", "หลังบ้าน", "#EAF0F5")
bracket(0, OUT_W, "cust", "fb", "Business Condition", "#FFFFFF")

def _ink(stop=False, branch=None):
    """true = เส้นเขียว, false = เส้นแดง, นอกนั้นสีปกติ"""
    if branch == "true":  return "fl-true", "arT"
    if branch == "false": return "fl-false", "arF"
    return ("fl-stop", "arS") if stop else ("fl", "ar")

# ---------- shapes ----------
@tagged
def task(col, y, lines, w=142, h=54, row=0, cls="n-task"):
    x = cx(col) - w / 2
    A(f'<rect x="{x}" y="{y - h/2}" width="{w}" height="{h}" rx="3" class="{cls}"/>')
    n = len(lines)
    for i, ln in enumerate(lines):
        ty = y - (n - 1) * 7.5 + i * 15 + 4.5
        A(f'<text x="{cx(col)}" y="{ty}" class="t-node">{html.escape(ln)}</text>')
    return (cx(col), y, w, h)

@tagged
def decision(col, y, lines, w=150, h=84):
    X, hw, hh = cx(col), w / 2, h / 2
    A(f'<polygon points="{X},{y-hh} {X+hw},{y} {X},{y+hh} {X-hw},{y}" class="n-dec"/>')
    n = len(lines)
    for i, ln in enumerate(lines):
        ty = y - (n - 1) * 6.5 + i * 13 + 4
        A(f'<text x="{X}" y="{ty}" class="t-dec">{html.escape(ln)}</text>')
    return (X, y, w, h)

@tagged
def store(col, y, lines, w=146, h=52):
    X = cx(col)
    A(f'<rect x="{X-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="14" class="n-store"/>')
    n = len(lines)
    for i, ln in enumerate(lines):
        ty = y - (n - 1) * 7 + i * 14 + 4.5
        A(f'<text x="{X}" y="{ty}" class="t-node">{html.escape(ln)}</text>')
    return (X, y, w, h)

@tagged
def actor(col, y, label):
    X, r = cx(col), 26
    pts = " ".join(f"{X + r*dx},{y + r*dy}" for dx, dy in
                   [(0,-1),(.87,-.5),(.87,.5),(0,1),(-.87,.5),(-.87,-.5)])
    A(f'<polygon points="{pts}" class="n-actor"/>')
    A(f'<text x="{X}" y="{y + r + 17}" class="t-node">{html.escape(label)}</text>')
    return (X, y, r*1.74, r*2)

@tagged
def forkbar(col, y_top, y_bot, label=None, dx=0):
    """แถบหนา = แยกไปทำพร้อมกัน (fork) หรือรวมกลับ (join) — ไม่ใช่การเลือกทางใดทางหนึ่ง"""
    X = cx(col) + dx
    A(f'<rect x="{X-5}" y="{y_top}" width="10" height="{y_bot-y_top}" rx="2" class="n-fork"/>')
    if label:
        A(f'<text x="{X}" y="{y_bot + 18}" class="t-edge">{html.escape(label)}</text>')
    return (X, (y_top + y_bot)/2, 10, y_bot - y_top)

@tagged
def note(col, y, lines, w=178, h=46, dx=0):
    X = cx(col) + dx
    A(f'<rect x="{X-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="3" class="n-note"/>')
    n = len(lines)
    for i, ln in enumerate(lines):
        ty = y - (n - 1) * 7 + i * 14 + 4.5
        A(f'<text x="{X}" y="{ty}" class="t-note">{html.escape(ln)}</text>')
    return (X, y, w, h)

@tagged
def merge(col, y, dx=0):
    """จุดรวมทางเดินก่อนวนกลับ — ไม่ใช่จุดจบ"""
    X, r = cx(col) + dx, 13
    A(f'<circle cx="{X}" cy="{y}" r="{r}" class="n-merge"/>')
    return (X, y, r*2, r*2)

@tagged
def endpoint(col, y, label, above=False, dx=0):
    X, r = cx(col) + dx, 15
    A(f'<circle cx="{X}" cy="{y}" r="{r}" class="n-end"/>')
    dy = -r - 10 if above else r + 17
    A(f'<text x="{X}" y="{y + dy}" class="t-end">{html.escape(label)}</text>')
    return (X, y, r*2, r*2)

# ---------- arrows ----------
@tagged
def right(a, b, label=None, stop=False, turn=None, ay=None, by=None, hops=None, branch=None):
    """ลูกศรตรงแนวนอน หรือหักขึ้น/ลงแบบตั้งฉาก
    turn = x ที่จะหักแนวตั้ง (กันหักไปชนกล่องที่ขวางอยู่กลางทาง)"""
    x1 = a[0] + a[2]/2; y1 = ay if ay is not None else a[1]
    x2 = b[0] - b[2]/2; y2 = by if by is not None else b[1]
    c, m = _ink(stop, branch)
    if abs(y1 - y2) < 1:
        seg = f"M{x1},{y1}"
        for hx in sorted([h for h in (hops or []) if x1 < h < x2]):
            seg += f" L{hx - 9},{y1} A 9 9 0 0 1 {hx + 9},{y1}"
        seg += f" L{x2},{y2}"
        A(f'<path d="{seg}" class="{c}" marker-end="url(#{m})"/>')
        lx, ly = (x1 + x2)/2, y1 - 8
    else:
        midx = turn if turn is not None else (x1 + x2) / 2
        A(f'<path d="M{x1},{y1} L{midx},{y1} L{midx},{y2} L{x2},{y2}" '
          f'class="{c}" marker-end="url(#{m})"/>')
        lx, ly = x1 + 44, y1 - 9
    if label:
        A(f'<text x="{lx}" y="{ly}" class="t-edge">{html.escape(label)}</text>')

@tagged
def drop(a, b, label=None, stop=False, corridor=None, lab_x=None, enter=None, branch=None):
    """ออกจากด้านล่างแล้วลงไปหาเป้าด้านบน
    corridor = ระดับ y ที่ให้วิ่งแนวนอน (แยกช่องกันไม่ให้เส้นทับ)
    lab_x    = ตำแหน่ง x ของป้าย (กันป้ายทับกัน)"""
    x1, y1 = a[0], a[1] + a[3]/2
    c, m = _ink(stop, branch)
    if enter == "left":
        # ลงมาถึงระดับเป้าแล้วเลี้ยวเข้าทางซ้าย ไม่ชนเส้นที่ออกจากด้านบนของเป้า
        by = b[1]; bx = b[0] - b[2]/2
        A(f'<path d="M{x1},{y1} L{x1},{by} L{bx},{by}" class="{c}" marker-end="url(#{m})"/>')
        if label:
            # วางป้ายติดต้นทาง จะได้รู้ว่าเป็นทางออกไหนของกล่องต้นทาง
            A(f'<text x="{x1 + 54}" y="{y1 + 32}" class="t-edge">{html.escape(label)}</text>')
        return
    x2, y2 = b[0], b[1] - b[3]/2
    if abs(x1 - x2) < 1 and corridor is None:
        A(f'<path d="M{x1},{y1} L{x2},{y2}" class="{c}" marker-end="url(#{m})"/>')
        lx, ly = x1 + 6, (y1 + y2)/2
    else:
        midy = corridor if corridor is not None else (y1 + y2) / 2
        A(f'<path d="M{x1},{y1} L{x1},{midy} L{x2},{midy} L{x2},{y2}" '
          f'class="{c}" marker-end="url(#{m})"/>')
        lx, ly = (lab_x if lab_x is not None else (x1 + x2)/2), midy - 7
    if label:
        A(f'<text x="{lx}" y="{ly}" class="t-edge">{html.escape(label)}</text>')

@tagged
def rise(a, b, label=None, branch=None, corridor=None):
    """ออกจากด้านบนแล้วขึ้นไปหาเป้าด้านล่าง"""
    x1, y1 = a[0], a[1] - a[3]/2
    x2, y2 = b[0], b[1] + b[3]/2
    _c, _m = _ink(branch=branch)
    midy = corridor if corridor is not None else (y1 + y2) / 2
    if abs(x1 - x2) < 1:
        A(f'<path d="M{x1},{y1} L{x2},{y2}" class="{_c}" marker-end="url(#{_m})"/>')
        lx, ly = x1 + 6, midy
    else:
        A(f'<path d="M{x1},{y1} L{x1},{midy} L{x2},{midy} L{x2},{y2}" '
          f'class="{_c}" marker-end="url(#{_m})"/>')
        lx, ly = (x1 + x2)/2, midy - 7
    if label:
        A(f'<text x="{lx}" y="{ly}" class="t-edge">{html.escape(label)}</text>')

@tagged
def data(a, b, label=None):
    """เส้นประสองทาง: ไปถาม/ไปบันทึกข้อมูล"""
    x1, y1 = a[0], a[1] + a[3]/2
    x2, y2 = b[0], b[1] - b[3]/2
    A(f'<path d="M{x1},{y1} L{x2},{y2}" class="fl-data" marker-end="url(#arD)"/>')
    if label:
        A(f'<text x="{x1 + 7}" y="{(y1 + y2)/2 + 4}" class="t-data">{html.escape(label)}</text>')

@tagged
def loopback(a, b, label=None, corridor=None, hops=None, branch=None, enter=None):
    """วนกลับไปต้นลูป: ออกใต้ a ลงช่องเดิน ย้อนซ้ายไปเลยเป้า แล้วขึ้นเข้าทางซ้ายของเป้า
    เข้าทางซ้ายเพื่อไม่ให้ไปชนเส้นอื่นที่พุ่งเข้าด้านล่างของเป้าอยู่แล้ว"""
    x1, y1 = a[0], a[1] + a[3]/2
    bx, by, bw = b[0], b[1], b[2]
    _c, _m = _ink(branch=branch)
    turn = bx if enter == "bottom" else bx - bw/2 - 46
    seg = f"M{x1},{y1} L{x1},{corridor}"
    for hx in sorted([h for h in (hops or []) if turn < h < x1], reverse=True):
        seg += f" L{hx + 9},{corridor} A 9 9 0 0 1 {hx - 9},{corridor}"   # สะพานข้าม
    seg += (f" L{turn},{corridor} L{turn},{by + b[3]/2}" if enter == "bottom"
            else f" L{turn},{corridor} L{turn},{by} L{bx - bw/2},{by}")
    A(f'<path d="{seg}" class="{_c}" marker-end="url(#{_m})"/>')
    if label:
        A(f'<text x="{(x1 + turn)/2}" y="{corridor - 8}" class="t-edge">{html.escape(label)}</text>')

@tagged
def up_right(a, b, label=None, by=None, branch=None):
    """ออกมุมบน ขึ้นไปถึงระดับ by แล้วเลี้ยวขวาเข้าด้านซ้ายของเป้า"""
    _c, _m = _ink(branch=branch)
    x1, y1 = a[0], a[1] - a[3]/2
    x2 = b[0] - b[2]/2
    A(f'<path d="M{x1},{y1} L{x1},{by} L{x2},{by}" class="{_c}" marker-end="url(#{_m})"/>')
    if label:
        A(f'<text x="{(x1 + x2)/2}" y="{by - 8}" class="t-edge">{html.escape(label)}</text>')

@tagged
def forward_under(a, b, label=None, corridor=None, hops=None, branch=None):
    """ลงใต้ผัง วิ่งไปขวา แล้วขึ้นเข้าทางใต้ของเป้า"""
    _c, _m = _ink(branch=branch)
    x1, y1 = a[0], a[1] + a[3]/2
    x2, y2 = b[0], b[1] + b[3]/2
    seg = f"M{x1},{y1} L{x1},{corridor}"
    for hx in sorted([h for h in (hops or []) if x1 < h < x2]):
        seg += f" L{hx - 9},{corridor} A 9 9 0 0 1 {hx + 9},{corridor}"
    seg += f" L{x2},{corridor} L{x2},{y2}"
    A(f'<path d="{seg}" class="{_c}" marker-end="url(#{_m})"/>')
    if label:
        A(f'<text x="{x1 + 150}" y="{corridor - 8}" class="t-edge">{html.escape(label)}</text>')

# ---------- nodes ----------
CUST = lane_mid("cust", -8); PS = lane_mid("pubsub"); MG = lane_mid("mongo"); RD = lane_mid("redis")

n_actor   = actor(0, CUST, "ลูกค้า", tag="n_actor")
n_comment = task(1, CUST, ["คอมเมนต์ใต้โพสต์", "ของร้าน"], tag="n_comment")
n_ps      = task(2, PS, ["แจ้งระบบว่า", "มีคอมเมนต์ใหม่"], tag="n_ps")

d_real = decision(3, ROW_MAIN, ["เป็นคอมเมนต์", "จริงไหม"], tag="d_real")
d_page = decision(4, ROW_MAIN, ["เพจเปิดใช้งาน", "อยู่ไหม"], tag="d_page")
d_who  = decision(5, ROW_MAIN, ["คนคอมเมนต์เป็น", "ลูกค้าใช่ไหม"], tag="d_who")
e_stop = endpoint(5, ROW_END, "จบ ไม่ตอบ", dx=40, tag="e_stop")
m_bot  = merge(6, ROW_MAIN, dx=-82, tag="m_bot")
n_bots = task(7, ROW_MAIN, ["หยิบบอทของร้าน", "มาทีละตัว"], tag="n_bots")

d_team  = decision(8, ROW_MAIN, ["บอทเป็นของทีม", "เดียวกับเพจไหม"], tag="d_team")
d_again = decision(9, ROW_MAIN, ["ตอบคนเดิม", "ซ้ำได้ไหม"], tag="d_again")
d_post  = decision(10, ROW_MAIN, ["ดูแลโพสต์นี้", "ไหม"], tag="d_post")
d_spec  = decision(11, ROW_MAIN, ["มีบอทเฉพาะโพสต์", "คุมอยู่ไหม"], tag="d_spec")
d_text  = decision(12, ROW_MAIN, ["คอมเมนต์เป็น", "ข้อความไหม"], tag="d_text")
d_kw    = decision(13, ROW_MAIN, ["ตรงคำที่ตั้ง", "ให้ตอบไหม"], tag="d_kw")
d_type  = decision(13, TYPE_ROW, ["บอทตั้งรับคอมเมนต์", "แบบนี้ไหม"], w=176, tag="d_type")
d_ban   = decision(14, ROW_MAIN, ["มีคำต้องห้าม", "ไหม"], tag="d_ban")
n_prep = task(16, ROW_MAIN, ["เตรียมคำตอบ", "สุ่มจากชุดที่ตั้งไว้"], tag="n_prep")
d_has = decision(17, ROW_MAIN, ["มีคำสั่งจะส่ง", "ไหม"], tag="d_has")
e_skip  = merge(15, ROW_END, tag="e_skip")
e_skip_bar = e_skip
out.insert(len(out) - 1,
    f'<text x="{e_skip[0] + 22}" y="{ROW_END + 4}" class="t-edge" '
    f'style="text-anchor:start">ข้ามบอทตัวนี้</text>')

f_split = forkbar(18, ROW_UP - 22, ROW_DOWN2 + 22, "แยกทำพร้อมกัน", dx=-46, tag="f_split")
n_like = task(19, ROW_UP, ["กดไลก์คอมเมนต์"], h=40, tag="n_like")
d_both = decision(19, ROW_MAIN, ["ตอบใต้คอมเมนต์มี", "ทั้งข้อความและรูปไหม"], w=184, tag="d_both")
d_chatimg = decision(19, ROW_DOWN2, ["แชทเป็นรูปไหม"], tag="d_chatimg")
a_chattext = task(20, ROW_DOWN2, ["ส่งข้อความ", "ตามที่ตั้งไว้"], w=150, h=48, tag="a_chattext")
d_cached  = decision(20, ROW_DOWN3, ["เคยส่งรูปนี้", "แล้วไหม"], tag="d_cached")
a_reuse   = task(21, ROW_DOWN3, ["ใช้รูปเดิม", "ที่เก็บไว้"], w=150, h=48, tag="a_reuse")
a_upload  = task(21, ROW_DOWN4, ["แนบลิงก์รูป", "ให้อัปใหม่"], w=150, h=48, tag="a_upload")
m_chat    = forkbar(22, ROW_DOWN2 - 22, ROW_DOWN4 + 22, "รวมข้อความแชท", dx=-40, tag="m_chat")
d_quick   = decision(23, ROW_DOWN3, ["ต้องแนบปุ่ม", "ดูรูปเพิ่มไหม"], tag="d_quick")
a_quick   = task(24, ROW_DOWN4, ["แนบปุ่ม", "ดูรูปเพิ่ม"], w=150, h=48, tag="a_quick")
a_txt = task(20, ROW_MAIN, ["ส่งข้อความ", "ชิ้นเดียว"], w=150, h=48, tag="a_txt")
a_both = task(20, ROW_DOWN, ["ผูกให้รูปขึ้นหลังข้อความ", "แล้วส่งทั้งคู่"], w=190, h=48, tag="a_both")
n_hint = note(17, ROW_DOWN3, ["ตั้งอย่างเดียว หลายอย่าง", "หรือครบทั้งสามก็ได้"], tag="n_hint")
f_join = forkbar(25, ROW_UP - 22, ROW_DOWN4 + 22, "รวมเป็นชุดเดียว", dx=-52, tag="f_join")

s_page = store(4, MG, ["ข้อมูลเพจที่ผูกไว้"], tag="s_page")
s_bots = store(7, MG, ["รายการบอทที่เปิดใช้"], tag="s_bots")
s_log  = store(9, MG, ["ประวัติการตอบลูกค้า"], tag="s_log")
s_img = store(20, RD, ["รูปที่เคยส่งเข้าแชท"], tag="s_img")

n_send = task(26, FB_MAIN, ["รับคำสั่งทั้งหมดในครั้งเดียว", "แล้วส่งผลกลับมาเป็นรายการ"], w=196, tag="n_send")
d_sent = decision(27, ROW_MAIN, ["ยิงคำสั่งออก", "ไปได้ไหม"], tag="d_sent")
m_in = merge(28, ROW_MAIN, tag="m_in")
d_wait = decision(29, ROW_MAIN, ["คำสั่งนี้รอ", "คำสั่งอื่นอยู่ไหม"], w=170, tag="d_wait")
d_ok = decision(30, ROW_MAIN, ["คำสั่งนี้", "สำเร็จไหม"], tag="d_ok")
d_img = decision(31, ROW_MAIN, ["เป็นการส่งรูป", "ทางแชทไหม"], tag="d_img")
a_keep = task(32, ROW_UP, ["เก็บรูปไว้ใช้ซ้ำ", "ครั้งหน้า"], w=158, h=48, tag="a_keep")
d_live = decision(30, ROW_DOWN, ["ไลฟ์ยังไม่จบ", "อยู่ใช่ไหม"], w=158, tag="d_live")
a_pass = task(31, ROW_DOWN, ["ตอบรูปใต้ไลฟ์ไม่ได้", "ปล่อยผ่าน ไม่ถือว่าล้มเหลว"], w=178, h=48, tag="a_pass")
d_img2 = decision(30, ROW_DOWN2, ["เป็นการส่งรูป", "ทางแชทไหม"], tag="d_img2")
d_exp = decision(31, ROW_DOWN2, ["รูปที่เคยส่ง", "หมดอายุไหม"], tag="d_exp")
a_fail = task(31, ROW_DOWN3, ["บันทึกว่า", "คำสั่งนี้ล้มเหลว"], w=158, h=48, tag="a_fail")
a_new = task(32, FB_MAIN, ["ส่งรูปใหม่", "ด้วยลิงก์รูปจริง"], w=158, tag="a_new")
s_imgw = store(32, RD, ["รูปที่เคยส่งเข้าแชท"], tag="s_imgw")
n_hint2 = note(34, ROW_DOWN3, ["ถ้าอ่านผลของคำสั่งไม่ออก", "นับเป็นล้มเหลวเหมือนกัน"], w=196, tag="n_hint2")

f_res = forkbar(33, ROW_UP - 56, ROW_DOWN3 + 22, "รวมทาง", dx=-62, tag="f_res")
d_more = decision(34, ROW_MAIN, ["ตรวจครบทุก", "คำสั่งแล้วไหม"], tag="d_more")
n_note = task(35, ROW_MAIN, ["จดว่าตอบลูกค้า", "คนนี้แล้ว"], tag="n_note")
s_logw = store(35, MG, ["ประวัติการตอบลูกค้า"], tag="s_logw")
m_end = merge(36, ROW_MAIN, tag="m_end")
d_bot = decision(37, ROW_MAIN, ["ดูบอทครบ", "ทุกตัวแล้วไหม"], tag="d_bot")
n_seen = task(38, CUST, ["เห็นไลก์ คำตอบ", "และข้อความในแชท"], tag="n_seen")

# ---------- edges ----------
right(n_actor, n_comment, tag="n_actor>n_comment")
drop(n_comment, n_ps, tag="n_comment>n_ps")
drop(n_ps, d_real, tag="n_ps>d_real")

right(d_real, d_page, "ใช่", branch="true", tag="d_real>d_page")
right(d_page, d_who, "ใช่ เปิดอยู่", branch="true", tag="d_page>d_who")
right(d_who, m_bot, "ใช่", branch="true", tag="d_who>m_bot")
right(m_bot, n_bots, tag="m_bot>n_bots")
right(n_bots, d_team, tag="n_bots>d_team")
right(d_team, d_again, "ใช่", branch="true", tag="d_team>d_again")
right(d_again, d_post, "ได้", branch="true", tag="d_again>d_post")
right(d_post, d_spec, "ดูแล", branch="true", tag="d_post>d_spec")
right(d_spec, d_text, "ไม่มี", branch="false", tag="d_spec>d_text")
right(d_text, d_kw, "ใช่", branch="true", tag="d_text>d_kw")
drop(d_text, d_type, "ไม่ใช่ เป็นรูป/สติกเกอร์", branch="false",
     corridor=TYPE_ROW, enter="left", tag="d_text>d_type")
right(d_kw, d_ban, "ตรง", branch="true", tag="d_kw>d_ban")
right(d_ban, n_prep, "ไม่มี", branch="false", tag="d_ban>n_prep")
rise(d_type, n_prep, "ใช่ รับแบบนี้", branch="true", corridor=TYPE_ROW - 52, tag="d_type>n_prep")
right(n_prep, d_has, tag="n_prep>d_has")
right(d_has, f_split, "ใช่", branch="true", tag="d_has>f_split")

LANE_STOP = [ROW_MAIN + 62, ROW_MAIN + 88, ROW_MAIN + 114]
drop(d_real, e_stop, "แค่กดอีโมจิ / แก้คอมเมนต์เดิม", branch="false",
     corridor=LANE_STOP[0], lab_x=cx(3) + 96, tag="d_real>e_stop")
drop(d_page, e_stop, "ปิดอยู่ / ไม่เคยผูก", branch="false",
     corridor=LANE_STOP[1], lab_x=cx(4) + 66, tag="d_page>e_stop")
drop(d_who, e_stop, "ไม่ใช่ ร้านเอง", branch="false",
     corridor=LANE_STOP[2], lab_x=cx(5) + 52, tag="d_who>e_stop")

SK = [ROW_MAIN + 62 + 34 * k for k in range(8)]
drop(d_team, e_skip, "ไม่ใช่ คนละทีม", branch="false", corridor=SK[0], lab_x=cx(8) + 70, tag="d_team>e_skip")
drop(d_again, e_skip, "ไม่ได้ เคยตอบแล้ว", branch="false", corridor=SK[1], lab_x=cx(9) + 74, tag="d_again>e_skip")
drop(d_post, e_skip, "ไม่ใช่โพสต์นี้", branch="false", corridor=SK[2], lab_x=cx(10) + 62, tag="d_post>e_skip")
drop(d_spec, e_skip, "มี และตั้งให้หลบ", branch="true", corridor=SK[3], lab_x=cx(11) + 70, tag="d_spec>e_skip")
right(d_type, e_skip, "ไม่ใช่ ไม่ได้ตั้งรับ", branch="false", tag="d_type>e_skip")
drop(d_kw, e_skip, "ไม่ตรง", branch="false", corridor=SK[5], lab_x=cx(13) + 40, tag="d_kw>e_skip")
drop(d_ban, e_skip, "มี", branch="true", corridor=SK[6], lab_x=cx(14) + 30, tag="d_ban>e_skip")
drop(d_has, e_skip, "ไม่มีคำสั่งจะส่ง", branch="false", corridor=SK[7], lab_x=cx(16) + 66, tag="d_has>e_skip")

data(d_page, s_page, "ถาม", tag="d_page>s_page")
data(n_bots, s_bots, "ขอรายการ", tag="n_bots>s_bots")
data(d_again, s_log, "เช็ก", tag="d_again>s_log")

right(f_split, n_like, "ถ้าตั้งให้กดไลก์", ay=ROW_UP, tag="f_split>n_like")
right(f_split, d_both, "ถ้าตั้งค่าตอบใต้คอมเมนต์", ay=ROW_MAIN, tag="f_split>d_both")
right(f_split, d_chatimg, "ถ้าตั้งค่าทักแชท", ay=ROW_DOWN2, tag="f_split>n_chat")
right(d_both, a_txt, "ไม่ใช่", branch="false", tag="d_both>a_txt")
drop(d_both, a_both, "ใช่", branch="true", enter="left", tag="d_both>a_both")
right(d_chatimg, a_chattext, "ไม่ใช่", branch="false", tag="d_chatimg>a_chattext")
drop(d_chatimg, d_cached, "ใช่", branch="true", enter="left", tag="d_chatimg>d_cached")
data(d_cached, s_img, "หารูปเดิม", tag="n_chat>s_img")
right(d_cached, a_reuse, "ใช่ ใช้ของเดิม", branch="true", tag="d_cached>a_reuse")
drop(d_cached, a_upload, "ไม่ใช่ ยังไม่เคยส่ง", branch="false", enter="left", tag="d_cached>a_upload")
right(a_chattext, m_chat, by=ROW_DOWN2, tag="a_chattext>m_chat")
right(a_reuse, m_chat, by=ROW_DOWN3, tag="a_reuse>m_chat")
right(a_upload, m_chat, by=ROW_DOWN4, tag="a_upload>m_chat")
right(m_chat, d_quick, tag="m_chat>d_quick")
drop(d_quick, a_quick, "ใช่", branch="true", enter="left", tag="d_quick>a_quick")
right(n_like, f_join, by=ROW_UP, tag="n_like>f_join")
right(a_txt, f_join, by=ROW_MAIN, tag="a_txt>f_join")
right(a_both, f_join, by=ROW_DOWN, tag="a_both>f_join")
right(d_quick, f_join, "ไม่ใช่", by=ROW_DOWN2, branch="false", tag="d_quick>f_join")
right(a_quick, f_join, by=ROW_DOWN4, tag="a_quick>f_join")

drop(f_join, n_send, enter="left", tag="f_join>n_send")
rise(n_send, d_sent, tag="n_send>d_sent")
right(d_sent, m_in, "ได้", branch="true", tag="d_sent>m_in")
right(m_in, d_wait, tag="m_in>d_wait")
right(d_wait, d_ok, "ไม่ใช่", branch="false", tag="d_wait>d_ok")
up_right(d_wait, f_res, "ใช่ ข้ามไปตรวจใบถัดไป", by=ROW_UP - 40, branch="true", tag="d_wait>f_res")
right(d_ok, d_img, "ใช่ สำเร็จ", branch="true", tag="d_ok>d_img")
drop(d_ok, d_live, "ไม่สำเร็จ", branch="false", tag="d_ok>d_live")
rise(d_img, a_keep, "ใช่", branch="true", tag="d_img>a_keep")
right(d_img, f_res, "ไม่ใช่ ไม่ต้องทำอะไรต่อ", by=ROW_MAIN, branch="false", tag="d_img>f_res")
data(a_keep, s_imgw, "เก็บรูป", tag="a_keep>s_imgw")
right(a_keep, f_res, by=ROW_UP, tag="a_keep>f_res")
right(d_live, a_pass, "ใช่", branch="true", tag="d_live>a_pass")
drop(d_live, d_img2, "ไม่ใช่", branch="false", tag="d_live>d_img2")
right(a_pass, f_res, by=ROW_DOWN, tag="a_pass>f_res")
right(d_img2, d_exp, "ใช่", branch="true", tag="d_img2>d_exp")
drop(d_img2, a_fail, "ไม่ใช่", enter="left", branch="false", tag="d_img2>a_fail")
right(d_exp, a_new, "ใช่ ส่งใหม่", branch="true", tag="d_exp>a_new")
drop(d_exp, a_fail, "ไม่ใช่", branch="false", tag="d_exp>a_fail")
rise(a_new, f_res, tag="a_new>f_res")
right(a_fail, f_res, by=ROW_DOWN3, hops=[(cx(31) + cx(32))/2 - 2], tag="a_fail>f_res")

right(f_res, d_more, tag="f_res>d_more")
CROSS = [f_join[0], d_sent[0], m_in[0], f_res[0], (cx(31) + cx(32))/2 - 2, a_new[0]]
loopback(d_more, m_in, "ไม่ ยังไม่ครบ ตรวจคำสั่งถัดไป", branch="false",
         corridor=LOOP_BACK, hops=[cx(30), cx(31), cx(32)], tag="d_more>m_in")
right(d_more, n_note, "ใช่ ครบแล้ว", branch="true", tag="d_more>n_note")
data(n_note, s_logw, "บันทึก", tag="n_note>s_logw")
right(n_note, m_end, tag="n_note>m_end")
forward_under(e_skip, m_end, "ข้ามมารอที่จุดตรวจบอท", corridor=SKIP_FWD, hops=CROSS, tag="e_skip>m_end")
forward_under(d_sent, m_end, "ไม่ได้ ยิงไม่ออก", branch="false", corridor=SKIP_FWD, hops=CROSS, tag="d_sent>m_end")
right(m_end, d_bot, tag="m_end>d_bot")
loopback(d_bot, m_bot, "ไม่ ยังดูไม่ครบ หยิบบอทตัวถัดไป", branch="false",
         corridor=BOT_BACK, enter="bottom", hops=CROSS, tag="d_bot>m_bot")
rise(d_bot, n_seen, "ใช่ ครบแล้ว", branch="true", tag="d_bot>n_seen")

A("</svg>")
svg = "\n".join(out)

with open("swimlane.svg.part", "w", encoding="utf-8") as f:
    f.write(svg)
print(f"svg ok — {W}x{H}, {len(svg)} bytes")

# ---------- standalone .svg (style ฝังในตัว เปิดดูบน GitHub ได้) ----------
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
  .n-task{fill:#FFFFFF;stroke:#5C7A8A;stroke-width:1.6}
  .n-dec{fill:#9CC3E0;stroke:#3E6E90;stroke-width:1.6}
  .n-store{fill:#FFFFFF;stroke:#96803A;stroke-width:1.6}
  .n-actor{fill:#D9B8D4;stroke:#7A5675;stroke-width:1.6}
  .n-end{fill:#D9705A;stroke:#8F3A28;stroke-width:1.8}
  .n-fork{fill:#44525C;stroke:#2B363D;stroke-width:1}
  .n-note{fill:#FBF1C2;stroke:#96803A;stroke-width:1.2}\n  .n-merge{fill:#FFFFFF;stroke:#44525C;stroke-width:2}
  .t-note{font-family:'IBM Plex Sans Thai',sans-serif;font-size:11px;fill:#5B4E1E;text-anchor:middle}
  .fl{fill:none;stroke:#44525C;stroke-width:1.7}
  .fl-stop{fill:none;stroke:#B0402C;stroke-width:1.6}
  .fl-true{fill:none;stroke:#2F7D4F;stroke-width:1.8}
  .fl-false{fill:none;stroke:#B0402C;stroke-width:1.8}
  .fl-data{fill:none;stroke:#7C8C95;stroke-width:1.4;stroke-dasharray:5 4}
</style>"""

standalone = svg.replace("<defs>", STYLE + "\n<defs>", 1)
with open("swimlane.svg", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + standalone)
print("swimlane.svg standalone ok")

# ======================================================================
# ตัด e2e ให้เหลือเส้นทางเดียวต่อ scenario
# ใช้ layout เดิมทุกพิกัด/สี/เส้น แค่ไม่วาดชิ้นที่ไม่อยู่บนเส้นทางนั้น
# ======================================================================

PRE = ["n_actor", "n_comment", "n_ps", "d_real", "d_page", "d_who", "m_bot", "n_bots",
       "s_page", "s_bots", "n_actor>n_comment", "n_comment>n_ps", "n_ps>d_real",
       "d_real>d_page", "d_page>d_who", "d_who>m_bot", "m_bot>n_bots", "d_page>s_page", "n_bots>s_bots"]
GATES = ["d_team", "d_again", "d_post", "d_spec", "d_text", "d_kw", "d_ban", "n_prep", "d_has", "s_log",
         "n_bots>d_team", "d_team>d_again", "d_again>d_post", "d_post>d_spec", "d_spec>d_text",
         "d_text>d_kw", "d_kw>d_ban", "d_ban>n_prep", "n_prep>d_has", "d_has>f_split", "d_again>s_log"]
SEND = ["f_split", "f_join", "n_send", "d_sent", "m_in", "d_wait", "d_ok",
        "f_res", "d_more", "n_note", "s_logw", "m_end", "d_bot", "n_seen",
        "f_join>n_send", "n_send>d_sent", "d_sent>m_in", "m_in>d_wait", "d_wait>d_ok",
        "f_res>d_more", "d_more>n_note", "n_note>s_logw", "n_note>m_end", "m_end>d_bot", "d_bot>n_seen"]
BASE = PRE + GATES + SEND
OK_PLAIN = ["d_img", "d_ok>d_img", "d_img>f_res"]
LIKE = ["n_like", "f_split>n_like", "n_like>f_join"]
CMT_TEXT = ["d_both", "f_split>d_both", "a_txt", "d_both>a_txt", "a_txt>f_join"]
CMT_IMG = ["d_both", "f_split>d_both", "a_both", "d_both>a_both", "a_both>f_join"]
CHAT_TEXT = ["f_split>n_chat", "d_chatimg", "a_chattext", "d_chatimg>a_chattext",
             "m_chat", "a_chattext>m_chat", "d_quick", "m_chat>d_quick", "d_quick>f_join"]
SKIP_OUT = ["e_skip", "e_skip>m_end", "m_end", "d_bot", "n_seen", "m_end>d_bot", "d_bot>n_seen"]

SCENARIOS = {
 "COMMENT_BOT_REPLY_SUCCESS_1": dict(cat="Success", nn="01",
  desc="บอทกดไลก์และตอบใต้คอมเมนต์เป็นข้อความชิ้นเดียว ทั้งสองคำสั่งสำเร็จ",
  note="ร้านมีบอท 1 ตัว · ชุดคำสั่ง 2 ใบ จึงวนตรวจผล 2 รอบ",
  steps=["ทีมงานผูกเพจ Facebook ของร้านเข้ากับระบบ และเปิดสถานะใช้งาน",
         "ทีมงานตั้งบอท 1 ตัวแบบใช้กับทุกโพสต์ ให้กดไลก์และตอบใต้คอมเมนต์เป็นข้อความที่เรียกชื่อจริงลูกค้า",
         "ลูกค้าคอมเมนต์ข้อความใต้โพสต์ของเพจนั้น",
         "ระบบตรวจว่าคอมเมนต์และเพจถูกต้อง แล้วไล่ดูบอทของร้านพบว่าบอทตัวนี้เข้าเงื่อนไข",
         "ระบบส่งคำสั่งกดไลก์และตอบคอมเมนต์ไปยัง Facebook ในการยิงครั้งเดียว",
         "ระบบไล่ตรวจผลทีละคำสั่ง พบว่าสำเร็จทั้งสองใบ",
         "ระบบบันทึกว่าบอทตัวนี้ตอบลูกค้าคนนี้ในโพสต์นี้แล้ว"],
  keep=BASE + OK_PLAIN + LIKE + CMT_TEXT + ["d_more>m_in"]),

 "COMMENT_BOT_REPLY_SUCCESS_2": dict(cat="Success", nn="02",
  desc="บอทตอบใต้คอมเมนต์เป็นข้อความพร้อมรูป โดยรูปต้องขึ้นหลังข้อความ",
  note="ชุดคำสั่ง 2 ใบที่ผูกกัน · ใบข้อความจึงได้ผลกลับมาเป็นค่าว่าง ซึ่งเป็นเรื่องปกติ",
  steps=["ทีมงานผูกเพจและเปิดใช้งาน",
         "ทีมงานตั้งบอทให้ตอบใต้คอมเมนต์เป็นข้อความพร้อมรูป",
         "ลูกค้าคอมเมนต์ข้อความใต้โพสต์",
         "ระบบผูกให้คำสั่งส่งรูปรอคำสั่งส่งข้อความก่อน แล้วส่งทั้งคู่ไป Facebook ในครั้งเดียว",
         "Facebook ไม่ส่งผลของใบข้อความกลับมาเพราะมีใบอื่นรออยู่ ระบบต้องข้ามใบนั้นโดยไม่ถือว่าล้มเหลว",
         "ระบบยืนยันว่าใบรูปสำเร็จ แล้วบันทึกประวัติการตอบ"],
  keep=BASE + OK_PLAIN + CMT_IMG + ["d_more>m_in", "d_wait>f_res"]),

 "COMMENT_BOT_REPLY_SUCCESS_3": dict(cat="Success", nn="03",
  desc="ทักแชทเป็นรูป ยิงสองรอบด้วย setup เดียว รอบแรกอัปรูปใหม่ รอบสองต้องใช้รูปที่เก็บไว้",
  note="สองรอบต่างกันที่ เคยส่งรูปนี้แล้วไหม จึงเก็บทั้งสองทางไว้ในผังเดียว",
  steps=["ทีมงานผูกเพจและตั้งบอทให้ทักแชทส่วนตัวเป็นรูป",
         "ลูกค้าคนแรกคอมเมนต์ ระบบหาไม่พบรูปที่เคยส่ง จึงแนบลิงก์รูปให้ Facebook อัปโหลดใหม่",
         "ส่งสำเร็จ ระบบเก็บรูปนั้นไว้ใช้ซ้ำเป็นเวลา 90 วัน",
         "ลูกค้าคนที่สองคอมเมนต์ด้วยเงื่อนไขเดียวกัน",
         "ระบบหาพบรูปที่เก็บไว้ จึงใช้ของเดิมแทนการอัปโหลดใหม่",
         "ยืนยันว่ารอบที่สองไม่มีการอัปโหลดรูปซ้ำ"],
  keep=BASE + ["f_split>n_chat", "d_chatimg", "d_chatimg>d_cached", "d_cached", "s_img", "n_chat>s_img",
               "a_reuse", "d_cached>a_reuse", "a_upload", "d_cached>a_upload",
               "m_chat", "a_reuse>m_chat", "a_upload>m_chat", "d_quick", "m_chat>d_quick", "d_quick>f_join",
               "d_img", "d_ok>d_img", "a_keep", "d_img>a_keep", "s_imgw", "a_keep>s_imgw", "a_keep>f_res"]),

 "COMMENT_BOT_REPLY_SUCCESS_4": dict(cat="Success", nn="04",
  desc="ทักแชทเป็นข้อความพร้อมแนบปุ่มดูรูปเพิ่ม",
  note="คำตอบแชทมีมากกว่าหนึ่งชิ้นและผูกสินค้าไว้ จึงต้องแนบปุ่มไปด้วย",
  steps=["ทีมงานผูกเพจและตั้งบอทให้ทักแชทด้วยคำตอบสองชิ้นพร้อมผูกสินค้า",
         "ลูกค้าคอมเมนต์ใต้โพสต์",
         "ระบบเตรียมข้อความแชทและตรวจว่าต้องแนบปุ่มดูรูปเพิ่มด้วย",
         "ระบบส่งข้อความพร้อมปุ่มไปยัง Facebook",
         "ยืนยันว่าข้อความที่ส่งมีปุ่มดูรูปเพิ่มแนบไปด้วย"],
  keep=BASE + OK_PLAIN + ["f_split>n_chat", "d_chatimg", "a_chattext", "d_chatimg>a_chattext",
               "m_chat", "a_chattext>m_chat", "d_quick", "m_chat>d_quick",
               "a_quick", "d_quick>a_quick", "a_quick>f_join"]),

 "COMMENT_BOT_REPLY_SUCCESS_5": dict(cat="Success", nn="05",
  desc="ลูกค้าคอมเมนต์เป็นรูปหรือสติกเกอร์ แล้วบอทตั้งรับคอมเมนต์ประเภทนั้นไว้",
  note="คอมเมนต์ที่ไม่ใช่ข้อความจะไม่ถูกเช็คคำที่ตั้งไว้เลย แต่ไปดูว่าบอทติ๊กรับประเภทนั้นไหม",
  steps=["ทีมงานผูกเพจและตั้งบอทโดยติ๊กรับคอมเมนต์ที่เป็นสติกเกอร์",
         "ลูกค้าส่งสติกเกอร์แทนการพิมพ์ข้อความ",
         "ระบบพบว่าไม่ใช่ข้อความ จึงข้ามการเช็คคำที่ตั้งไว้ ไปดูว่าบอทรับประเภทนี้ไหม",
         "บอทติ๊กรับสติกเกอร์ไว้ ระบบจึงตอบใต้คอมเมนต์ตามปกติ",
         "ยืนยันว่าลูกค้าได้รับคำตอบทั้งที่ไม่มีคำที่ตั้งไว้ในคอมเมนต์"],
  keep=PRE + SEND + OK_PLAIN + CMT_TEXT + ["d_more>m_in", "s_log", "d_again>s_log",
        "d_team", "d_again", "d_post", "d_spec", "d_text", "d_type", "n_prep", "d_has",
        "n_bots>d_team", "d_team>d_again", "d_again>d_post", "d_post>d_spec",
        "d_spec>d_text", "d_text>d_type", "d_type>n_prep", "n_prep>d_has", "d_has>f_split"]),

 "COMMENT_BOT_REPLY_SUCCESS_6": dict(cat="Success", nn="06",
  desc="ร้านมีบอทหลายตัวเข้าเงื่อนไขพร้อมกัน ต้องตอบครบทุกตัว",
  note="ตรวจลูปนอกที่วนบอททีละตัว · คอมเมนต์เดียวทำให้ยิง Facebook หลายรอบ",
  steps=["ทีมงานผูกเพจและตั้งบอท 3 ตัวที่เข้าเงื่อนไขพร้อมกัน คือ กดไลก์ ตอบใต้คอมเมนต์ และทักแชท",
         "ลูกค้าคอมเมนต์ข้อความเดียวใต้โพสต์",
         "ระบบไล่ดูบอททีละตัว แต่ละตัวส่งคำสั่งของตัวเองไป Facebook แยกรอบกัน",
         "ระบบบันทึกประวัติแยกรายบอท",
         "ยืนยันว่าลูกค้าได้รับครบทั้งสามอย่างจากคอมเมนต์เดียว"],
  keep=BASE + OK_PLAIN + LIKE + CMT_TEXT + CHAT_TEXT + ["d_more>m_in", "d_bot>m_bot"]),

 "COMMENT_BOT_REPLY_ALTERNATIVE_1": dict(cat="Alternative", nn="01",
  desc="ของที่ส่งเข้ามาแล้วไม่ควรตอบ กดอีโมจิ แก้คอมเมนต์เดิม ร้านคอมเมนต์เอง และบอทคนละทีมกับเพจ",
  note="ใช้ setup เดียว seed บอทปกติและบอทคนละทีมไว้ด้วยกัน แล้วยิงหลาย payload",
  steps=["ทีมงานผูกเพจ ตั้งบอทปกติ 1 ตัว และบอทที่เป็นของทีมอื่นอีก 1 ตัว",
         "ยิงเหตุการณ์กดอีโมจิเข้ามา ระบบต้องไม่ตอบ",
         "ยิงเหตุการณ์แก้ไขคอมเมนต์เดิมเข้ามา ระบบต้องไม่ตอบ",
         "ยิงคอมเมนต์ที่มาจากเพจตัวเอง ระบบต้องไม่ตอบเพื่อกันบอทตอบตัวเอง",
         "ยิงคอมเมนต์ปกติจากลูกค้า บอทที่เป็นของทีมอื่นต้องถูกข้ามไป",
         "ยืนยันว่าไม่มีการยิงคำสั่งไป Facebook เลยในสามเคสแรก"],
  keep=PRE + ["e_stop", "d_real>e_stop", "d_page>e_stop", "d_who>e_stop",
              "d_team", "n_bots>d_team", "d_team>e_skip", "d_bot>m_bot"] + SKIP_OUT),

 "COMMENT_BOT_REPLY_ALTERNATIVE_2": dict(cat="Alternative", nn="02",
  desc="เพจถูกปิดใช้งาน หรือไม่เคยผูกไว้กับระบบ",
  note="จบตั้งแต่ด่านเพจ ไม่ไปถึงการไล่ดูบอทเลย",
  steps=["ทีมงานผูกเพจไว้แต่ปิดสถานะใช้งาน",
         "ลูกค้าคอมเมนต์ใต้โพสต์ของเพจนั้น",
         "ระบบหาข้อมูลเพจแล้วพบว่าปิดใช้งานอยู่",
         "ระบบจบการทำงานโดยไม่ตอบและไม่ไล่ดูบอท"],
  keep=["n_actor", "n_comment", "n_ps", "d_real", "d_page", "s_page",
        "n_actor>n_comment", "n_comment>n_ps", "n_ps>d_real", "d_real>d_page",
        "d_page>s_page", "e_stop", "d_page>e_stop"]),

 "COMMENT_BOT_REPLY_ALTERNATIVE_3": dict(cat="Alternative", nn="03",
  desc="บอทตั้งให้ตอบครั้งเดียว และลูกค้าคนนี้เคยได้รับคำตอบในโพสต์นี้แล้ว",
  note="ต้อง seed ประวัติการตอบไว้ก่อน",
  steps=["ทีมงานตั้งบอทแบบตอบครั้งเดียวต่อคนต่อโพสต์",
         "ระบบมีประวัติอยู่แล้วว่าเคยตอบลูกค้าคนนี้ในโพสต์นี้",
         "ลูกค้าคนเดิมคอมเมนต์ซ้ำในโพสต์เดิม",
         "ระบบเช็กประวัติแล้วข้ามบอทตัวนี้",
         "ยืนยันว่าไม่มีการยิงคำสั่งไป Facebook"],
  keep=PRE + ["d_team", "n_bots>d_team", "d_team>d_again", "d_again", "s_log", "d_again>s_log",
              "d_again>e_skip"] + SKIP_OUT),

 "COMMENT_BOT_REPLY_ALTERNATIVE_4": dict(cat="Alternative", nn="04",
  desc="คอมเมนต์ไม่ผ่านเงื่อนไขคำ ทั้งกรณีไม่ตรงคำที่ตั้งไว้ และกรณีมีคำต้องห้าม",
  note="สอง payload ใช้ setup บอทเดียวกัน จึงควบเป็น scenario เดียว",
  steps=["ทีมงานตั้งบอทโดยกำหนดทั้งคำที่ต้องตรงและคำต้องห้าม",
         "ลูกค้าคอมเมนต์ข้อความที่ไม่มีคำที่ตั้งไว้ ระบบต้องไม่ตอบ",
         "ลูกค้าอีกคนคอมเมนต์ข้อความที่มีคำต้องห้าม ระบบต้องไม่ตอบ",
         "ยืนยันว่าไม่มีการยิงคำสั่งไป Facebook ทั้งสองครั้ง"],
  keep=PRE + ["d_team", "d_again", "d_post", "d_spec", "d_text", "d_kw", "d_ban", "s_log",
              "n_bots>d_team", "d_team>d_again", "d_again>d_post", "d_post>d_spec",
              "d_spec>d_text", "d_text>d_kw", "d_kw>d_ban", "d_again>s_log",
              "d_kw>e_skip", "d_ban>e_skip"] + SKIP_OUT),

 "COMMENT_BOT_REPLY_ALTERNATIVE_5": dict(cat="Alternative", nn="05",
  desc="บอทแบบทุกโพสต์หลบให้บอทเฉพาะโพสต์ ทำให้ตอบตัวเดียวไม่ซ้อนกัน",
  note="ต้องมีบอท 2 ตัวบนโพสต์เดียวกัน",
  steps=["ทีมงานตั้งบอทเฉพาะโพสต์ 1 ตัวบนโพสต์นี้",
         "ทีมงานตั้งบอททุกโพสต์อีก 1 ตัว โดยเปิดตัวเลือกให้หลบเมื่อมีบอทเฉพาะโพสต์",
         "ลูกค้าคอมเมนต์ใต้โพสต์นั้น",
         "ระบบพบว่ามีบอทเฉพาะโพสต์คุมอยู่ จึงข้ามบอททุกโพสต์",
         "ยืนยันว่าลูกค้าได้รับคำตอบจากบอทเฉพาะโพสต์ตัวเดียว ไม่ได้รับซ้ำสองเด้ง"],
  keep=PRE + ["d_team", "d_again", "d_post", "d_spec", "s_log",
              "n_bots>d_team", "d_team>d_again", "d_again>d_post", "d_post>d_spec",
              "d_again>s_log", "d_spec>e_skip", "d_bot>m_bot"] + SKIP_OUT),

 "COMMENT_BOT_REPLY_ALTERNATIVE_6": dict(cat="Alternative", nn="06",
  desc="ไลฟ์ยังไม่จบจึงตอบรูปใต้คอมเมนต์ไม่ได้ ระบบต้องปล่อยผ่านไม่ถือว่าล้มเหลว",
  note="stub Facebook ให้ตอบ error 1705",
  steps=["ทีมงานตั้งบอทให้ตอบใต้คอมเมนต์เป็นข้อความพร้อมรูป",
         "ลูกค้าคอมเมนต์ใต้โพสต์ที่เป็นไลฟ์ซึ่งยังถ่ายอยู่",
         "Facebook ปฏิเสธคำสั่งส่งรูปเพราะไลฟ์ยังไม่จบ",
         "ระบบต้องปล่อยผ่านคำสั่งนั้นโดยไม่นับว่าล้มเหลว และไม่ลองส่งซ้ำ",
         "ระบบยังบันทึกประวัติการตอบตามปกติ"],
  keep=BASE + CMT_IMG + ["d_ok>d_live", "d_live", "a_pass", "d_live>a_pass", "a_pass>f_res", "d_more>m_in"]),

 "COMMENT_BOT_REPLY_ALTERNATIVE_7": dict(cat="Alternative", nn="07",
  desc="รูปที่เคยส่งเข้าแชทหมดอายุ ระบบต้องส่งใหม่ด้วยลิงก์รูปจริงแล้วสำเร็จ",
  note="stub Facebook ให้ตอบ error 100 subcode 2018074 ในครั้งแรก",
  steps=["ระบบมีรูปที่เคยส่งเก็บไว้อยู่แล้ว",
         "ลูกค้าคอมเมนต์ ระบบจึงใช้รูปเดิมที่เก็บไว้ส่งเข้าแชท",
         "Facebook ตอบว่ารูปนั้นหมดอายุแล้ว",
         "ระบบส่งใหม่อีกครั้งโดยแนบลิงก์รูปจริงแทน",
         "ส่งสำเร็จ และระบบเก็บรูปใหม่ไว้ใช้ซ้ำ"],
  keep=BASE + ["f_split>n_chat", "d_chatimg", "d_chatimg>d_cached", "d_cached", "s_img", "n_chat>s_img",
               "a_reuse", "d_cached>a_reuse", "m_chat", "a_reuse>m_chat",
               "d_quick", "m_chat>d_quick", "d_quick>f_join",
               "d_ok>d_live", "d_live", "d_live>d_img2", "d_img2", "d_img2>d_exp",
               "d_exp", "d_exp>a_new", "a_new", "a_new>f_res"]),

 "COMMENT_BOT_REPLY_ALTERNATIVE_8": dict(cat="Alternative", nn="08",
  desc="บอทเปิดใช้งานอยู่แต่ไม่ได้ตั้งคำตอบไว้เลย",
  note="ผ่านทุกด่านเงื่อนไข แต่ไม่มีคำสั่งจะส่ง",
  steps=["ทีมงานเปิดบอทไว้แต่ยังไม่ได้ใส่คำตอบทั้งใต้คอมเมนต์และแชท",
         "ลูกค้าคอมเมนต์ใต้โพสต์",
         "ระบบผ่านทุกด่านเงื่อนไขแล้วพบว่าไม่มีคำสั่งจะส่ง",
         "ระบบข้ามบอทตัวนี้ไปโดยไม่ยิงอะไรไป Facebook",
         "ยืนยันว่าไม่มีการบันทึกประวัติการตอบ"],
  keep=PRE + GATES + ["d_has>e_skip"] + SKIP_OUT),

 "COMMENT_BOT_REPLY_ALTERNATIVE_9": dict(cat="Alternative", nn="09",
  desc="ยิงคำสั่งไป Facebook ไม่ออกเลย เช่น โทเคนหมดอายุหรือปลายทางล่ม",
  note="stub Facebook ให้ล่ม ลูกค้าจะไม่ได้อะไรเลยและไม่ถูกบันทึกว่าตอบแล้ว",
  steps=["ทีมงานตั้งบอทให้ตอบใต้คอมเมนต์ตามปกติ",
         "ลูกค้าคอมเมนต์ใต้โพสต์",
         "ระบบเตรียมคำสั่งครบแล้วยิงไป Facebook แต่ยิงไม่ออก",
         "ระบบข้ามบอทตัวนี้ไปดูตัวถัดไป",
         "ยืนยันว่าไม่มีการบันทึกประวัติ เพื่อให้ลูกค้ายังมีโอกาสได้รับคำตอบในครั้งหน้า"],
  keep=PRE + GATES + ["f_split", "f_join", "n_send", "d_sent",
        "f_join>n_send", "n_send>d_sent", "d_sent>m_end", "m_end", "d_bot", "n_seen",
        "m_end>d_bot", "d_bot>n_seen", "d_bot>m_bot"] + CMT_TEXT),
}

SEED = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{name}</title></head>
<body>
<script id="scenario-meta" type="application/json">
{meta}
</script>
</body>
</html>
"""

def carve(name, spec):
    import os, json
    keep = set(spec["keep"])
    res, skip = [], 0
    for ln in out:
        if ln.startswith('<g data-el="'):
            tag = ln.split('"')[1]
            if tag not in keep: skip += 1
            elif skip == 0: continue
        elif ln == "</g>":
            if skip: skip -= 1
            continue
        elif skip: continue
        else: res.append(ln)
    svg = "\n".join(res)
    svg = svg.replace(">COMMENT_BOT_REPLY<", f">{name}<", 1)
    svg = re.sub(r'(<text x="32" y="74" class="t-sub">)[^<]*',
                 lambda m: m.group(1) + "Scenario: " + spec["desc"], svg, count=1)
    svg = re.sub(r'(<text x="32" y="96" class="t-sub">)[^<]*',
                 lambda m: m.group(1) + spec["note"] + " · ตัดจาก e2e ตัวเต็ม พิกัดและสีเดิมทุกจุด", svg, count=1)
    svg = svg.replace("<defs>", STYLE + "\n<defs>", 1)

    folder = os.path.join(spec["cat"], f'{spec["nn"]}-{name}')
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "flow.svg"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)

    html = os.path.join(folder, "scenario.html")
    if not os.path.exists(html):
        meta = json.dumps({"scenario": name, "category": spec["cat"], "description": spec["desc"],
                           "steps": spec["steps"], "accepted": False, "acceptanceHistory": []},
                          ensure_ascii=False, indent=2)
        with open(html, "w", encoding="utf-8") as f:
            f.write(SEED.format(name=name, meta=meta))
    print(f"{folder}/flow.svg — {len(keep)} ชิ้น")

import re
for _n, _s in SCENARIOS.items():
    carve(_n, _s)
