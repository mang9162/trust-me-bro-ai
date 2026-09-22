#!/usr/bin/env python3
"""สร้าง swimlane SVG แบบ lane แนวนอนซ้อนบนลงล่าง flow วิ่งซ้าย->ขวา
ตาม format ที่ทีมใช้ (MAINTAIN_EDIT_CART_ADD_ITEM_BY_ADMIN)
"""
import html

# ---------- geometry ----------
OUT_W, GRP_W, LAB_W = 30, 30, 70          # คอลัมน์ซ้าย: bracket รวม / กลุ่ม / ชื่อ lane
X0 = OUT_W + GRP_W + LAB_W                  # ซ้ายสุดของพื้นที่ lane
COLW = 170
NCOL = 21
TITLE_H = 118
PAD_R = 30
W = X0 + NCOL * COLW + PAD_R

LANES = [
    # key,      ชื่อ,                        สูง,  สีพื้น,     กลุ่ม
    ("cust",   ["ลูกค้า"],                   150, "#CFE9D4", "front"),
    ("pubsub", ["Pub/Sub"],                  100, "#C5DCF2", "back"),
    ("svc",    ["live-stream", "consumer"],  370, "#F7DCBE", "back"),
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
ROW_UP = ROW_MAIN - 74
ROW_DOWN = ROW_MAIN + 74
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

def endpoint(col, y, label, above=False):
    X, r = cx(col), 15
    A(f'<circle cx="{X}" cy="{y}" r="{r}" class="n-end"/>')
    dy = -r - 10 if above else r + 17
    A(f'<text x="{X}" y="{y + dy}" class="t-end">{html.escape(label)}</text>')
    return (X, y, r*2, r*2)

# ---------- arrows ----------
def right(a, b, label=None, stop=False):
    """ลูกศรตรงแนวนอน หรือหักขึ้น/ลงแบบตั้งฉาก"""
    x1 = a[0] + a[2]/2; y1 = a[1]
    x2 = b[0] - b[2]/2; y2 = b[1]
    m = "arS" if stop else "ar"
    c = "fl-stop" if stop else "fl"
    if abs(y1 - y2) < 1:
        A(f'<path d="M{x1},{y1} L{x2},{y2}" class="{c}" marker-end="url(#{m})"/>')
        lx, ly = (x1 + x2)/2, y1 - 8
    else:
        midx = (x1 + x2) / 2
        A(f'<path d="M{x1},{y1} L{midx},{y1} L{midx},{y2} L{x2},{y2}" '
          f'class="{c}" marker-end="url(#{m})"/>')
        lx, ly = midx + 6, (y1 + y2)/2
    if label:
        A(f'<text x="{lx}" y="{ly}" class="t-edge">{html.escape(label)}</text>')

def drop(a, b, label=None, stop=False, corridor=None, lab_x=None):
    """ออกจากด้านล่างแล้วลงไปหาเป้าด้านบน
    corridor = ระดับ y ที่ให้วิ่งแนวนอน (แยกช่องกันไม่ให้เส้นทับ)
    lab_x    = ตำแหน่ง x ของป้าย (กันป้ายทับกัน)"""
    x1, y1 = a[0], a[1] + a[3]/2
    x2, y2 = b[0], b[1] - b[3]/2
    m = "arS" if stop else "ar"
    c = "fl-stop" if stop else "fl"
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

def rise(a, b, label=None):
    """ออกจากด้านบนแล้วขึ้นไปหาเป้าด้านล่าง"""
    x1, y1 = a[0], a[1] - a[3]/2
    x2, y2 = b[0], b[1] + b[3]/2
    midy = (y1 + y2) / 2
    if abs(x1 - x2) < 1:
        A(f'<path d="M{x1},{y1} L{x2},{y2}" class="fl" marker-end="url(#ar)"/>')
        lx, ly = x1 + 6, midy
    else:
        A(f'<path d="M{x1},{y1} L{x1},{midy} L{x2},{midy} L{x2},{y2}" '
          f'class="fl" marker-end="url(#ar)"/>')
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
d_who = decision(5, ROW_MAIN, ["ลูกค้า หรือ", "ร้านเอง"])
n_bots = task(6, ROW_MAIN, ["ไล่ดูบอทของร้าน", "ทีละตัว"])
d_again = decision(7, ROW_MAIN, ["ตอบคนเดิม", "ซ้ำได้ไหม"])
d_post = decision(8, ROW_MAIN, ["ดูแลโพสต์นี้", "ไหม"])
d_spec = decision(9, ROW_MAIN, ["มีบอทเฉพาะโพสต์", "คุมอยู่ไหม"])
d_kw = decision(10, ROW_MAIN, ["ตรงคำที่ตั้ง", "ให้ตอบไหม"])
d_ban = decision(11, ROW_MAIN, ["มีคำต้องห้าม", "ไหม"])
n_prep = task(12, ROW_MAIN, ["เตรียมคำตอบ", "สุ่มจากชุดที่ตั้งไว้"])

# บอททำได้หลายอย่างพร้อมกัน ไม่ได้เลือกอย่างใดอย่างหนึ่ง -> แถบ fork ไม่ใช่ข้าวหลามตัด
# เงื่อนไขว่าร้านตั้งอะไรไว้บ้าง แปะไว้บนลูกศรแต่ละเส้น
f_split = forkbar(13, ROW_UP - 22, ROW_DOWN + 22, "แยกทำพร้อมกัน", dx=-46)

n_like = task(14, ROW_UP, ["กดไลก์คอมเมนต์"], h=40)
n_reply = task(14, ROW_MAIN, ["ตอบใต้คอมเมนต์", "ข้อความ หรือรูป"], h=48)
n_chat = task(14, ROW_DOWN, ["ทักแชทส่วนตัว"], h=40)

f_join = forkbar(15, ROW_UP - 22, ROW_DOWN + 22, "รวมเป็นชุดเดียว", dx=-52)
n_hint = note(13, ROW_END - 26, ["ตั้งอย่างเดียว หลายอย่าง", "หรือครบทั้งสามก็ได้"], dx=40)

e_stop = endpoint(6, ROW_END, "จบ ไม่ตอบ")
e_skip = endpoint(12, ROW_END, "ข้ามบอทตัวนี้ ไปดูตัวถัดไป")

s_page = store(4, MG, ["ข้อมูลเพจที่ผูกไว้"])
s_bots = store(6, MG, ["รายการบอทที่เปิดใช้"])
s_log = store(7, MG, ["ประวัติการตอบลูกค้า"])
s_logw = store(19, MG, ["ประวัติการตอบลูกค้า"])
s_img = store(14, RD, ["รูปที่เคยส่งเข้าแชท"])

n_send = task(16, FB_MAIN, ["รับคำสั่งทั้งหมด", "ในครั้งเดียว"])
d_ok = decision(17, FB_MAIN, ["ทำให้ครบไหม"])
n_resend = task(18, FB_MAIN, ["ส่งรูปใหม่แทน", "รูปที่หมดอายุ"])
e_quiet = endpoint(17, FB_END, "ข้ามเงียบ ไม่นับว่าพัง")

n_note = task(19, ROW_MAIN, ["จดว่าตอบลูกค้า", "คนนี้แล้ว"])
n_seen = task(20, CUST, ["เห็นไลก์ คำตอบ", "และข้อความในแชท"])

# ---------- edges ----------
right(n_actor, n_comment)
drop(n_comment, n_ps)
drop(n_ps, d_real)

right(d_real, d_page, "ใช่")
right(d_page, d_who, "เปิดอยู่")
right(d_who, n_bots, "ลูกค้า")
right(n_bots, d_again)
right(d_again, d_post, "ได้")
right(d_post, d_spec, "ดูแล")
right(d_spec, d_kw, "ไม่มี")
right(d_kw, d_ban, "ตรง")
right(d_ban, n_prep, "ไม่มี")
right(n_prep, f_split)

# ออกจากแถบ fork ไปพร้อมกันทุกเส้นที่ร้านตั้งไว้ เงื่อนไขอยู่บนลูกศร
right(f_split, n_like, "ถ้าตั้งให้กดไลก์")
right(f_split, n_reply, "ถ้าตั้งค่าตอบใต้คอมเมนต์")
right(f_split, n_chat, "ถ้าตั้งค่าทักแชท")

right(n_like, f_join)
right(n_reply, f_join)
right(n_chat, f_join)

# แต่ละเส้นได้ช่องเดินของตัวเอง ป้ายวางเหนือช่องนั้น ไม่ทับกัน
LANE_STOP = [ROW_MAIN + 62, ROW_MAIN + 88, ROW_MAIN + 114]
LANE_SKIP = [ROW_MAIN + 62, ROW_MAIN + 88, ROW_MAIN + 114, ROW_MAIN + 140, ROW_MAIN + 166]
drop(d_real, e_stop, "แค่กดอีโมจิ / แก้คอมเมนต์เดิม", stop=True,
     corridor=LANE_STOP[0], lab_x=cx(3) + 96)
drop(d_page, e_stop, "ปิดอยู่ / ไม่เคยผูก", stop=True,
     corridor=LANE_STOP[1], lab_x=cx(4) + 66)
drop(d_who, e_stop, "ร้านเอง", stop=True,
     corridor=LANE_STOP[2], lab_x=cx(5) + 40)

LANE_SKIP = [ROW_MAIN + 62, ROW_MAIN + 88, ROW_MAIN + 114, ROW_MAIN + 140, ROW_MAIN + 166]
drop(d_again, e_skip, "เคยตอบแล้ว", stop=True,
     corridor=LANE_SKIP[0], lab_x=cx(7) + 58)
drop(d_post, e_skip, "ไม่ใช่โพสต์นี้", stop=True,
     corridor=LANE_SKIP[1], lab_x=cx(8) + 62)
drop(d_spec, e_skip, "มี และตั้งให้หลบ", stop=True,
     corridor=LANE_SKIP[2], lab_x=cx(9) + 70)
drop(d_kw, e_skip, "ไม่ตรง", stop=True,
     corridor=LANE_SKIP[3], lab_x=cx(10) + 38)
drop(d_ban, e_skip, "มี", stop=True,
     corridor=LANE_SKIP[4], lab_x=cx(11) + 26)

data(d_page, s_page, "ถาม")
data(n_bots, s_bots, "ขอรายการ")
data(d_again, s_log, "เช็ก")
data(n_chat, s_img, "หารูปเดิม")

drop(f_join, n_send)
right(n_send, d_ok)
drop(d_ok, e_quiet, "ตอบรูปใต้ไลฟ์ไม่ได้", stop=True)
right(d_ok, n_resend, "รูปหมดอายุ")
rise(d_ok, n_note, "สำเร็จ")
rise(n_resend, n_note)
data(n_note, s_logw, "บันทึก")
rise(n_note, n_seen)

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
  .n-note{fill:#FBF1C2;stroke:#96803A;stroke-width:1.2}
  .t-note{font-family:'IBM Plex Sans Thai',sans-serif;font-size:11px;fill:#5B4E1E;text-anchor:middle}
  .fl{fill:none;stroke:#44525C;stroke-width:1.7}
  .fl-stop{fill:none;stroke:#B0402C;stroke-width:1.6}
  .fl-data{fill:none;stroke:#7C8C95;stroke-width:1.4;stroke-dasharray:5 4}
</style>"""

standalone = svg.replace("<defs>", STYLE + "\n<defs>", 1)
with open("swimlane.svg", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + standalone)
print("swimlane.svg standalone ok")
