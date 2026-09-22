#!/usr/bin/env python3
"""สร้าง swimlane SVG แบบ lane แนวนอนซ้อนบนลงล่าง flow วิ่งซ้าย->ขวา
ตาม format ที่ทีมใช้ (MAINTAIN_EDIT_CART_ADD_ITEM_BY_ADMIN)
"""
import html

# ---------- geometry ----------
OUT_W, GRP_W, LAB_W = 30, 30, 70          # คอลัมน์ซ้าย: bracket รวม / กลุ่ม / ชื่อ lane
X0 = OUT_W + GRP_W + LAB_W                  # ซ้ายสุดของพื้นที่ lane
COLW = 200
NCOL = 28
TITLE_H = 118
PAD_R = 30
W = X0 + NCOL * COLW + PAD_R

LANES = [
    # key,      ชื่อ,                        สูง,  สีพื้น,     กลุ่ม
    ("cust",   ["ลูกค้า"],                   150, "#CFE9D4", "front"),
    ("pubsub", ["Pub/Sub"],                  100, "#C5DCF2", "back"),
    ("svc",    ["live-stream", "consumer"],  700, "#F7DCBE", "back"),
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
LOOP_BACK = ROW_MAIN + 392
SKIP_FWD  = ROW_MAIN + 452
BOT_BACK  = ROW_MAIN + 512
ROW_END = SVC_TOP + 300

FB_TOP = LY["fb"][0]
FB_MAIN = FB_TOP + 74
FB_END = FB_TOP + 156

out = []
A = out.append

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
def task(col, y, lines, w=142, h=54, row=0, cls="n-task"):
    x = cx(col) - w / 2
    A(f'<rect x="{x}" y="{y - h/2}" width="{w}" height="{h}" rx="3" class="{cls}"/>')
    n = len(lines)
    for i, ln in enumerate(lines):
        ty = y - (n - 1) * 7.5 + i * 15 + 4.5
        A(f'<text x="{cx(col)}" y="{ty}" class="t-node">{html.escape(ln)}</text>')
    return (cx(col), y, w, h)

def decision(col, y, lines, w=150, h=84):
    X, hw, hh = cx(col), w / 2, h / 2
    A(f'<polygon points="{X},{y-hh} {X+hw},{y} {X},{y+hh} {X-hw},{y}" class="n-dec"/>')
    n = len(lines)
    for i, ln in enumerate(lines):
        ty = y - (n - 1) * 6.5 + i * 13 + 4
        A(f'<text x="{X}" y="{ty}" class="t-dec">{html.escape(ln)}</text>')
    return (X, y, w, h)

def store(col, y, lines, w=146, h=52):
    X = cx(col)
    A(f'<rect x="{X-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="14" class="n-store"/>')
    n = len(lines)
    for i, ln in enumerate(lines):
        ty = y - (n - 1) * 7 + i * 14 + 4.5
        A(f'<text x="{X}" y="{ty}" class="t-node">{html.escape(ln)}</text>')
    return (X, y, w, h)

def actor(col, y, label):
    X, r = cx(col), 26
    pts = " ".join(f"{X + r*dx},{y + r*dy}" for dx, dy in
                   [(0,-1),(.87,-.5),(.87,.5),(0,1),(-.87,.5),(-.87,-.5)])
    A(f'<polygon points="{pts}" class="n-actor"/>')
    A(f'<text x="{X}" y="{y + r + 17}" class="t-node">{html.escape(label)}</text>')
    return (X, y, r*1.74, r*2)

def forkbar(col, y_top, y_bot, label=None, dx=0):
    """แถบหนา = แยกไปทำพร้อมกัน (fork) หรือรวมกลับ (join) — ไม่ใช่การเลือกทางใดทางหนึ่ง"""
    X = cx(col) + dx
    A(f'<rect x="{X-5}" y="{y_top}" width="10" height="{y_bot-y_top}" rx="2" class="n-fork"/>')
    if label:
        A(f'<text x="{X}" y="{y_bot + 18}" class="t-edge">{html.escape(label)}</text>')
    return (X, (y_top + y_bot)/2, 10, y_bot - y_top)

def note(col, y, lines, w=178, h=46, dx=0):
    X = cx(col) + dx
    A(f'<rect x="{X-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="3" class="n-note"/>')
    n = len(lines)
    for i, ln in enumerate(lines):
        ty = y - (n - 1) * 7 + i * 14 + 4.5
        A(f'<text x="{X}" y="{ty}" class="t-note">{html.escape(ln)}</text>')
    return (X, y, w, h)

def merge(col, y, dx=0):
    """จุดรวมทางเดินก่อนวนกลับ — ไม่ใช่จุดจบ"""
    X, r = cx(col) + dx, 13
    A(f'<circle cx="{X}" cy="{y}" r="{r}" class="n-merge"/>')
    return (X, y, r*2, r*2)

def endpoint(col, y, label, above=False, dx=0):
    X, r = cx(col) + dx, 15
    A(f'<circle cx="{X}" cy="{y}" r="{r}" class="n-end"/>')
    dy = -r - 10 if above else r + 17
    A(f'<text x="{X}" y="{y + dy}" class="t-end">{html.escape(label)}</text>')
    return (X, y, r*2, r*2)

# ---------- arrows ----------
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

def rise(a, b, label=None, branch=None):
    """ออกจากด้านบนแล้วขึ้นไปหาเป้าด้านล่าง"""
    x1, y1 = a[0], a[1] - a[3]/2
    x2, y2 = b[0], b[1] + b[3]/2
    _c, _m = _ink(branch=branch)
    midy = (y1 + y2) / 2
    if abs(x1 - x2) < 1:
        A(f'<path d="M{x1},{y1} L{x2},{y2}" class="{_c}" marker-end="url(#{_m})"/>')
        lx, ly = x1 + 6, midy
    else:
        A(f'<path d="M{x1},{y1} L{x1},{midy} L{x2},{midy} L{x2},{y2}" '
          f'class="{_c}" marker-end="url(#{_m})"/>')
        lx, ly = (x1 + x2)/2, midy - 7
    if label:
        A(f'<text x="{lx}" y="{ly}" class="t-edge">{html.escape(label)}</text>')

def data(a, b, label=None):
    """เส้นประสองทาง: ไปถาม/ไปบันทึกข้อมูล"""
    x1, y1 = a[0], a[1] + a[3]/2
    x2, y2 = b[0], b[1] - b[3]/2
    A(f'<path d="M{x1},{y1} L{x2},{y2}" class="fl-data" marker-end="url(#arD)"/>')
    if label:
        A(f'<text x="{x1 + 7}" y="{(y1 + y2)/2 + 4}" class="t-data">{html.escape(label)}</text>')

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
CUST = lane_mid("cust", -8)
PS = lane_mid("pubsub")
MG = lane_mid("mongo")
RD = lane_mid("redis")

n_actor = actor(0, CUST, "ลูกค้า")
n_comment = task(1, CUST, ["คอมเมนต์ใต้โพสต์", "ของร้าน"])
n_ps = task(2, PS, ["แจ้งระบบว่า", "มีคอมเมนต์ใหม่"])

d_real = decision(3, ROW_MAIN, ["เป็นคอมเมนต์", "จริงไหม"])
d_page = decision(4, ROW_MAIN, ["เพจเปิดใช้งาน", "อยู่ไหม"])
d_who = decision(5, ROW_MAIN, ["คนคอมเมนต์เป็น", "ลูกค้าใช่ไหม"])
n_bots = task(7, ROW_MAIN, ["หยิบบอทของร้าน", "มาทีละตัว"])
d_again = decision(8, ROW_MAIN, ["ตอบคนเดิม", "ซ้ำได้ไหม"])
d_post = decision(9, ROW_MAIN, ["ดูแลโพสต์นี้", "ไหม"])
d_spec = decision(10, ROW_MAIN, ["มีบอทเฉพาะโพสต์", "คุมอยู่ไหม"])
d_kw = decision(11, ROW_MAIN, ["ตรงคำที่ตั้ง", "ให้ตอบไหม"])
d_ban = decision(12, ROW_MAIN, ["มีคำต้องห้าม", "ไหม"])
n_prep = task(13, ROW_MAIN, ["เตรียมคำตอบ", "สุ่มจากชุดที่ตั้งไว้"])

# บอททำได้หลายอย่างพร้อมกัน ไม่ได้เลือกอย่างใดอย่างหนึ่ง -> แถบ fork ไม่ใช่ข้าวหลามตัด
# เงื่อนไขว่าร้านตั้งอะไรไว้บ้าง แปะไว้บนลูกศรแต่ละเส้น
f_split = forkbar(14, ROW_UP - 22, ROW_DOWN + 22, "แยกทำพร้อมกัน", dx=-46)

n_like = task(15, ROW_UP, ["กดไลก์คอมเมนต์"], h=40)
n_reply = task(15, ROW_MAIN, ["ตอบใต้คอมเมนต์", "ข้อความ หรือรูป"], h=48)
n_chat = task(15, ROW_DOWN, ["ทักแชทส่วนตัว"], h=40)

f_join = forkbar(16, ROW_UP - 22, ROW_DOWN + 22, "รวมเป็นชุดเดียว", dx=-52)
n_hint = note(14, ROW_END - 26, ["ตั้งอย่างเดียว หลายอย่าง", "หรือครบทั้งสามก็ได้"], dx=40)

e_stop = endpoint(5, ROW_END, "จบ ไม่ตอบ", dx=40)
m_bot = merge(6, ROW_MAIN, dx=-82)
e_skip = merge(12, ROW_END)
A(f'<text x="{e_skip[0]}" y="{ROW_END + 30}" class="t-edge">ข้ามบอทตัวนี้</text>')

s_page = store(4, MG, ["ข้อมูลเพจที่ผูกไว้"])
s_bots = store(7, MG, ["รายการบอทที่เปิดใช้"])
s_log = store(8, MG, ["ประวัติการตอบลูกค้า"])
s_logw = store(24, MG, ["ประวัติการตอบลูกค้า"])
s_img = store(15, RD, ["รูปที่เคยส่งเข้าแชท"])
s_imgw = store(21, RD, ["รูปที่เคยส่งเข้าแชท"])

n_send = task(17, FB_MAIN, ["รับคำสั่งทั้งหมดในครั้งเดียว", "แล้วส่งผลกลับมาเป็นรายการ"], w=196)

# จุดรวมทางเข้าลูป: เส้นแรกจาก Facebook กับเส้นวนกลับมารวมกันที่นี่
# แล้วค่อยเข้าข้าวหลามตัดเส้นเดียว (ข้าวหลามตัดมี 4 มุม รับได้เข้า 1 ออก 3)
m_in = merge(18, ROW_MAIN)

# ทุกข้าวหลามตัดถามคำถามใช่/ไม่ใช่ข้อเดียว แตกได้ 2 ทางเท่านั้น
# เงื่อนไขมาจากโค้ดจริงใน handleBatchResponse
d_ok   = decision(19, ROW_MAIN,  ["คำสั่งนี้", "สำเร็จไหม"])
d_img  = decision(20, ROW_MAIN,  ["เป็นการส่งรูป", "ทางแชทไหม"])
a_keep = task(21, ROW_UP, ["เก็บรูปไว้ใช้ซ้ำ", "ครั้งหน้า"], w=158, h=48)

d_live = decision(19, ROW_DOWN,  ["ไลฟ์ยังไม่จบ", "อยู่ใช่ไหม"], w=158)
a_pass = task(20, ROW_DOWN, ["ตอบรูปใต้ไลฟ์ไม่ได้", "ปล่อยผ่าน ไม่ถือว่าล้มเหลว"], w=178, h=48)

d_img2 = decision(19, ROW_DOWN2, ["เป็นการส่งรูป", "ทางแชทไหม"])
d_exp  = decision(20, ROW_DOWN2, ["รูปที่เคยส่ง", "หมดอายุไหม"])
a_fail = task(20, ROW_DOWN3, ["บันทึกว่า", "คำสั่งนี้ล้มเหลว"], w=158, h=48)
a_new  = task(21, FB_MAIN, ["ส่งรูปใหม่", "ด้วยลิงก์รูปจริง"], w=158)

n_hint2 = note(23, ROW_DOWN3, ["ถ้าอ่านผลของคำสั่งไม่ออก", "นับเป็นล้มเหลวเหมือนกัน"], w=196)

f_res = forkbar(22, ROW_UP - 22, ROW_DOWN3 + 22, "รวมทาง", dx=-62)
d_more = decision(23, ROW_MAIN, ["ตรวจครบทุก", "คำสั่งแล้วไหม"])
n_note = task(24, ROW_MAIN, ["จดว่าตอบลูกค้า", "คนนี้แล้ว"])
m_end = merge(25, ROW_MAIN)
d_bot = decision(26, ROW_MAIN, ["ดูบอทครบ", "ทุกตัวแล้วไหม"])
n_seen = task(27, CUST, ["เห็นไลก์ คำตอบ", "และข้อความในแชท"])

# ---------- edges ----------
right(n_actor, n_comment)
drop(n_comment, n_ps)
drop(n_ps, d_real)

right(d_real, d_page, "ใช่", branch="true")
right(d_page, d_who, "ใช่ เปิดอยู่", branch="true")
right(d_who, m_bot, "ใช่", branch="true")
right(m_bot, n_bots)
right(n_bots, d_again)
right(d_again, d_post, "ได้", branch="true")
right(d_post, d_spec, "ดูแล", branch="true")
right(d_spec, d_kw, "ไม่มี", branch="false")
right(d_kw, d_ban, "ตรง", branch="true")
right(d_ban, n_prep, "ไม่มี", branch="false")
right(n_prep, f_split)

# ออกจากแถบ fork ไปพร้อมกันทุกเส้นที่ร้านตั้งไว้ เงื่อนไขอยู่บนลูกศร
right(f_split, n_like, "ถ้าตั้งให้กดไลก์", ay=ROW_UP)
right(f_split, n_reply, "ถ้าตั้งค่าตอบใต้คอมเมนต์", ay=ROW_MAIN)
right(f_split, n_chat, "ถ้าตั้งค่าทักแชท", ay=ROW_DOWN)

right(n_like, f_join, by=ROW_UP)
right(n_reply, f_join, by=ROW_MAIN)
right(n_chat, f_join, by=ROW_DOWN)

# แต่ละเส้นได้ช่องเดินของตัวเอง ป้ายวางเหนือช่องนั้น ไม่ทับกัน
LANE_STOP = [ROW_MAIN + 62, ROW_MAIN + 88, ROW_MAIN + 114]
LANE_SKIP = [ROW_MAIN + 62, ROW_MAIN + 88, ROW_MAIN + 114, ROW_MAIN + 140, ROW_MAIN + 166]
drop(d_real, e_stop, "แค่กดอีโมจิ / แก้คอมเมนต์เดิม", branch="false",
     corridor=LANE_STOP[0], lab_x=cx(3) + 96)
drop(d_page, e_stop, "ปิดอยู่ / ไม่เคยผูก", branch="false",
     corridor=LANE_STOP[1], lab_x=cx(4) + 66)
drop(d_who, e_stop, "ร้านเอง", branch="false",
     corridor=LANE_STOP[2], lab_x=cx(5) + 40)

drop(d_again, e_skip, "เคยตอบแล้ว", branch="false",
     corridor=LANE_SKIP[0], lab_x=cx(7) + 58)
drop(d_post, e_skip, "ไม่ใช่โพสต์นี้", branch="false",
     corridor=LANE_SKIP[1], lab_x=cx(8) + 62)
drop(d_spec, e_skip, "มี และตั้งให้หลบ", branch="true",
     corridor=LANE_SKIP[2], lab_x=cx(9) + 70)
drop(d_kw, e_skip, "ไม่ตรง", branch="false",
     corridor=LANE_SKIP[3], lab_x=cx(10) + 38)
drop(d_ban, e_skip, "มี", branch="true",
     corridor=LANE_SKIP[4], lab_x=cx(11) + 26)

data(d_page, s_page, "ถาม")
data(n_bots, s_bots, "ขอรายการ")
data(d_again, s_log, "เช็ก")
data(n_chat, s_img, "หารูปเดิม")

drop(f_join, n_send, enter="left")

# --- ลูปไล่ตรวจผลทีละคำสั่ง ---
rise(n_send, m_in)
right(m_in, d_ok)

right(d_ok, d_img, "ใช่ สำเร็จ", branch="true")
drop(d_ok, d_live, "ไม่สำเร็จ", branch="false")

rise(d_img, a_keep, "ใช่", branch="true")
right(d_img, f_res, "ไม่ใช่ ไม่ต้องทำอะไรต่อ", by=ROW_MAIN, branch="false")
data(a_keep, s_imgw, "เก็บรูป")
right(a_keep, f_res, by=ROW_UP)

right(d_live, a_pass, "ใช่", branch="true")
drop(d_live, d_img2, "ไม่ใช่", branch="false")
right(a_pass, f_res, by=ROW_DOWN)

right(d_img2, d_exp, "ใช่", branch="true")
drop(d_img2, a_fail, "ไม่ใช่", enter="left", branch="false")
right(d_exp, a_new, "ใช่ ส่งใหม่", branch="true")
drop(d_exp, a_fail, "ไม่ใช่", branch="false")
rise(a_new, f_res)
right(a_fail, f_res, by=ROW_DOWN3, hops=[(cx(20) + cx(21))/2 - 2])

right(f_res, d_more)
loopback(d_more, m_in, "ไม่ ยังไม่ครบ ตรวจคำสั่งถัดไป", branch="false", corridor=LOOP_BACK,
         hops=[cx(19), cx(20), cx(21)])
right(d_more, n_note, "ใช่ ครบแล้ว", branch="true")
data(n_note, s_logw, "บันทึก")

# --- ลูปนอก: ร้านตั้งบอทได้หลายตัว ต้องวนดูให้ครบทุกตัว ---
CROSS = [f_join[0], m_in[0], f_res[0], (cx(20) + cx(21))/2 - 2, a_new[0]]
right(n_note, m_end)
forward_under(e_skip, m_end, "ข้ามมารอที่จุดตรวจบอท", corridor=SKIP_FWD, hops=CROSS)
right(m_end, d_bot)
loopback(d_bot, m_bot, "ไม่ ยังดูไม่ครบ หยิบบอทตัวถัดไป", branch="false",
         corridor=BOT_BACK, enter="bottom", hops=CROSS)
rise(d_bot, n_seen, "ใช่ ครบแล้ว", branch="true")

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
