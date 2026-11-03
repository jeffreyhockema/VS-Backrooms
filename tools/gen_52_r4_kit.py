"""Level 52, "The Greenfield Campus": round 4's model kit (2026-11-03), rebuilt shapes for set pieces that were 1-7 plain
boxes in round 3. The builder calls `textures(save)` and then writes each of `shapes()` with gen_52's `shape`, which
overrides the round 3 shape of the same name (the blocktypes, their collision boxes and codes stay as they are).

    l52-stall-{lower,upper}              a restroom stall: a floor-mounted pan with an exposed chrome flushometer, an
                                         open-front seat, the lid raised against the flush pipe, bolt caps; the laminate
                                         partition on a pilaster with a chrome shoe, a gap under it, a headrail on top, a
                                         roll holder and a coat hook
    l52-fumehood-{lower,upper}           a lab fume hood: the base cabinet (doors, pulls, plinth, black worktop) and the
                                         hood (posts, airfoil sill, a framed sash half raised, baffle slots, airflow
                                         monitor with a lit LED, gas tap, gooseneck, top casing, duct stub)
    l52-bleacher                         a row of aluminium bleachers (seat and foot planks as boards, kick plate, steel
                                         understructure with diagonal braces, splice caps)
    l52-goal-{l,m,r}-{lower,upper}       a football goal: round posts and bar, ground frame, back stanchions, a net with
                                         depth (cut-out mesh), pegs
    l52-flagpole-{base,pole,top}         a stepped plinth with a plaque and collar, an octagonal pole with its halyard and
                                         a cleat, the truck, a ball finial and a flag in folds
    l52-post-{kind}-{l,r}-{lower,upper}  a board on two posts: frame, rain hood, bolts, the back panel and its rails,
                                         post caps and foot collars
    l52-sign-{hose,ext,notice-l,notice-r,wallclock,mirror,men,women}
                                         wall fittings: the fire hose cabinet and extinguisher of the shared detail set
                                         (without their wall cube), a cork notice board with pinned sheets, a round wall
                                         clock stopped at 3:52, a restroom mirror with its shelf, the restroom plates

Every shape faces north (-Z) with anything hung on a wall against the wall at z = 16. Textures are r4k-*, drawn from
matlib's materials at 32 px a block (64 px for pictures); cut-outs (the net, the clock face, the hose cabinet's glass)
use alpha 0 or 255 only."""
import json
import math
import os
import random

from PIL import Image, ImageDraw

import matlib as M
from modelkit import box, move

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets", "backrooms")
FULL = (0, 0, 16, 16)
ALL = ("north", "east", "south", "west", "up", "down")


def fs(*drop):
    """All faces but the ones named."""
    return tuple(f for f in ALL if f not in drop)


NOS = fs("south")  # all but the face against the wall


def full_uv(el, *faces):
    for f in faces or el["faces"]:
        if f in el["faces"]:
            el["faces"][f]["uv"] = list(FULL)
    return el


def octo(name, frm, to, tex, axis="y", faces=ALL):
    """A bar of round section stepped from three boxes (wide and flat, narrow and tall, and a square between), whose
    union reads as a rounded profile; each a touch shorter along the axis than the last, so no two end caps share a
    plane."""
    i = "xyz".index(axis)
    lo, hi = list(frm), list(to)
    o = [k for k in range(3) if k != i]
    c = {k: (lo[k] + hi[k]) / 2 for k in o}
    h = {k: (hi[k] - lo[k]) / 2 for k in o}
    out = []
    for n, (fa, fb, e) in enumerate(((1.0, 0.58, 0.0), (0.58, 1.0, 0.012), (0.86, 0.86, 0.024))):
        a, b = list(lo), list(hi)
        a[i], b[i] = lo[i] + e, hi[i] - e
        for k, f in zip(o, (fa, fb)):
            a[k], b[k] = c[k] - h[k] * f, c[k] + h[k] * f
        out.append(box(name + "abc"[n], tuple(a), tuple(b), tex, faces=faces))
    return out


def bar(name, p0, p1, w, tex, faces=ALL, d=None):
    """A bar of section w x d from p0 to p1 (y, z) in the YZ plane at x centre p0[0]: a box along y turned about X."""
    if p1[1] < p0[1]:
        p0, p1 = p1, p0
    x, y0, z0 = p0
    _, y1, z1 = p1
    d = d or w
    L = math.hypot(y1 - y0, z1 - z0)
    cy, cz = (y0 + y1) / 2, (z0 + z1) / 2
    ang = math.degrees(math.atan2(z1 - z0, y1 - y0))
    return box(name, (x - w / 2, cy - L / 2, cz - d / 2), (x + w / 2, cy + L / 2, cz + d / 2), tex, faces=faces,
               rot=(XSIGN * ang, 0, 0), origin=(x, cy, cz))


XSIGN = 1   # the sign of rotationX that tilts a bar's top toward +z (checked in the previews)
ZSIGN = -1  # the sign of rotationZ that turns a hand clockwise as seen from the front (north)
YSIGN = 1   # the sign of rotationY that swings +x toward -z


# ======================================================================== textures

def chrome(seed, base=(206, 210, 214)):
    img = M.brushed_metal(seed, base=base, streak=6, sheen=22)
    px = img.load()
    rng = random.Random(seed)
    for y in range(32):          # a bright specular band and a dark reflected one, as polished chrome shows
        for x in range(32):
            t = (x + y * 0.6) % 32
            if 6 <= t < 9:
                px[x, y] = M.rgba(M.lift(px[x, y], 26))
            elif 18 <= t < 22:
                px[x, y] = M.rgba(M.lift(px[x, y], -34))
    for _ in range(8):
        M.touch(img, rng.randrange(32), rng.randrange(32), 0.25)
    return img


def satin(seed, base=(176, 180, 184), direction="h"):
    img = M.brushed_metal(seed, base=base, streak=8, sheen=10, direction=direction)
    M.grime(img, amount=0.05, seed=seed + 1, cover=0.3)
    return img


def enamel(seed, base, grime=0.06, chips=2, bias=None):
    img = M.painted_metal(seed, base=base, panel=False, chips=chips, under=(120, 116, 110))
    M.grime(img, amount=grime, seed=seed + 1, cover=0.4, bias=bias)
    return img


def plastic(seed, base, amp=2):
    img = M.noise_hv(base, amp, seed, (32, 32), 2, (16, 8))
    M.scratches(img, 3, seed + 1, (2, 5), 0.08)
    return img


def porcelain(seed):
    img = M.noise_hv((236, 236, 232), 1, seed, (32, 32), 2, (16, 8), hue=0.5)
    px = img.load()
    for y in range(32):          # soft glaze highlight bands
        for x in range(32):
            t = (x * 0.5 + y) % 32
            if 4 <= t < 7:
                px[x, y] = M.rgba(M.lift(px[x, y], 9))
            elif 20 <= t < 26:
                px[x, y] = M.rgba(M.lift(px[x, y], -6))
    return img


def bowl_top(seed):
    """The pan seen from above (its rim's top face, whole picture): the glazed rim round an oval bowl, water low in it.
    The picture's top is the face's north edge."""
    n = 64
    img = porcelain(seed).resize((n, n), Image.NEAREST)
    d = ImageDraw.Draw(img)
    d.ellipse((7, 3, 57, 52), fill=(212, 214, 212, 255))
    d.ellipse((10, 6, 54, 49), fill=(194, 198, 198, 255))
    d.ellipse((15, 11, 49, 42), fill=(170, 178, 180, 255))
    d.ellipse((20, 16, 44, 36), fill=(140, 164, 172, 255))   # the water
    d.ellipse((24, 19, 34, 26), fill=(170, 192, 198, 255))
    d.arc((7, 3, 57, 52), 200, 340, fill=(250, 250, 248, 255), width=2)
    M.grime(img, amount=0.04, seed=seed + 2, cover=0.3)
    return img


def laminate(seed, base=(170, 172, 160)):
    img = M.noise_hv(base, 2, seed, (32, 32), 3, (16, 8), hue=0.8)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(60):          # the fine speckle of a high-pressure laminate
        x, y = rng.randrange(32), rng.randrange(32)
        px[x, y] = M.rgba(M.lift(px[x, y], rng.choice((-10, -7, 6))))
    M.scratches(img, 2, seed + 3, (3, 7), 0.07)
    M.grime(img, amount=0.05, seed=seed + 4, cover=0.3)
    return img


def cork(seed):
    img = M.noise_hv((168, 124, 78), 6, seed, (32, 32), 6, (8, 4))
    rng = random.Random(seed)
    px = img.load()
    for _ in range(170):         # granules
        x, y = rng.randrange(32), rng.randrange(32)
        px[x, y] = M.rgba(M.lift(px[x, y], rng.choice((-26, -18, -12, 10, 16))))
    for _ in range(14):          # old pin holes
        x, y = rng.randrange(32), rng.randrange(32)
        px[x, y] = M.rgba((70, 50, 34))
    return img


def sheet(kind, seed):
    """A pinned sheet, drawn at 64 px and squeezed onto its face (the whole picture maps to the face)."""
    rng = random.Random(seed)
    base = {"memo": (234, 232, 222), "grid": (238, 236, 228), "note": (236, 218, 112), "blue": (196, 214, 230),
            "pink": (232, 196, 200), "green": (200, 222, 190)}[kind]
    img = M.noise_hv(base, 2, seed, (64, 64), 3, (16, 8), hue=0.5)
    d = ImageDraw.Draw(img)
    ink = (60, 62, 70, 255)
    grey = (128, 128, 132, 255)
    if kind in ("memo", "blue", "green"):
        d.rectangle((8, 6, 56, 13), fill=ink if kind == "memo" else (40, 70, 120, 255))
        y = 20
        while y < 58:
            d.rectangle((8, y, 8 + rng.randint(30, 48), y + 1), fill=grey)
            y += rng.choice((5, 5, 6, 9))
    elif kind == "grid":
        d.rectangle((6, 6, 58, 12), fill=ink)
        for x in range(6, 60, 13):
            d.line((x, 16, x, 58), fill=grey)
        for y in range(16, 60, 7):
            d.line((6, y, 58, y), fill=grey)
        for _ in range(9):
            cx, cy = 6 + 13 * rng.randrange(4), 16 + 7 * rng.randrange(6)
            d.rectangle((cx + 3, cy + 2, cx + 10, cy + 4), fill=(100, 100, 120, 255))
    elif kind == "note":
        for y in range(14, 54, 9):
            x = 8
            while x < 52:
                n = rng.randint(4, 10)
                d.line((x, y + rng.randint(-1, 1), x + n, y + rng.randint(-1, 1)), fill=(40, 50, 110, 255), width=2)
                x += n + 3
    elif kind == "pink":
        d.rectangle((10, 8, 54, 30), fill=(170, 150, 160, 255))
        d.ellipse((24, 12, 40, 28), fill=(220, 210, 200, 255))
        for y in (36, 42):
            d.rectangle((10, y, 54, y + 2), fill=grey)
        for x in range(8, 58, 8):     # tear-off strips at the foot
            d.line((x, 50, x, 63), fill=(150, 130, 136, 255))
    M.ao_border(img, 2, 0.12)
    M.grime(img, amount=0.05, seed=seed + 1, cover=0.4)
    return img


def clock_face(seed):
    """The wall clock's dial, a cut-out disc (alpha 0 outside): hour bars, minute ticks, digits, no hands (the hands are
    boxes)."""
    n = 256
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = n / 2
    d.ellipse((0, 0, n - 1, n - 1), fill=(244, 242, 236, 255))
    d.ellipse((5, 5, n - 6, n - 6), outline=(210, 208, 200, 255), width=5)
    for k in range(60):
        a = k * math.pi / 30
        r0 = c - 16 if k % 5 else c - 34
        w = 4 if k % 5 else 10
        x0, y0 = c + math.sin(a) * r0, c - math.cos(a) * r0
        x1, y1 = c + math.sin(a) * (c - 9), c - math.cos(a) * (c - 9)
        d.line((x0, y0, x1, y1), fill=(30, 30, 34, 255), width=w)
    from PIL import ImageFont
    font = ImageFont.load_default(size=28)
    for h in range(1, 13):
        a = h * math.pi / 6
        r = c - 58
        x, y = c + math.sin(a) * r, c - math.cos(a) * r
        d.text((x, y), str(h), fill=(30, 30, 34, 255), font=font, anchor="mm", stroke_width=1, stroke_fill=(30, 30, 34, 255))
    small = img.resize((64, 64), Image.LANCZOS)
    px = small.load()
    for y in range(64):
        for x in range(64):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255) if a >= 128 else (0, 0, 0, 0)
    return small


def mirror_tex(seed):
    img = M.noise_hv((176, 190, 198), 2, seed, (64, 64), 4, (32, 16), hue=0.5)
    px = img.load()
    for y in range(64):          # soft diagonal reflections and a darker lower band (the room reflected)
        for x in range(64):
            t = (x + y * 0.7) % 64
            v = 16 if 8 <= t < 16 else 9 if 24 <= t < 27 else 0
            if y > 40:
                v -= (y - 40) * 0.6
            px[x, y] = M.rgba(M.lift(px[x, y], v))
    rng = random.Random(seed)
    for _ in range(5):           # wipe streaks
        x0, y0 = rng.randrange(64), rng.randrange(64)
        for k in range(rng.randint(8, 18)):
            M.touch(img, (x0 + k) % 64, (y0 + k // 3) % 64, 0.06)
    M.ao_border(img, 2, 0.15)
    for x in range(64):          # desilvering at the bottom edge
        if rng.random() < 0.4:
            px[x, 63 - rng.randint(0, 1)] = M.rgba((120, 122, 118))
    return img


def plaque(seed):
    img = M.noise_hv((150, 116, 64), 4, seed, (64, 64), 5, (16, 8))
    d = ImageDraw.Draw(img)
    d.rectangle((3, 3, 60, 60), outline=(196, 160, 96, 255), width=2)
    for y, w in ((12, 40), (22, 30), (30, 44), (38, 36)):
        d.rectangle((32 - w // 2, y, 32 + w // 2, y + 2), fill=(96, 72, 40, 255))
    from PIL import ImageFont
    d.text((32, 51), "1952", fill=(90, 66, 36, 255), anchor="mm", font=ImageFont.load_default(size=11))
    M.grime(img, amount=0.2, seed=seed + 1, color=(70, 98, 80), cover=0.5)   # verdigris
    M.ao_border(img, 2, 0.15)
    return img


def monitor_face(seed):
    img = M.noise_hv((214, 210, 198), 2, seed, (64, 64), 2, (16, 8))
    d = ImageDraw.Draw(img)
    from PIL import ImageFont
    d.rectangle((6, 8, 58, 32), fill=(34, 46, 40, 255), outline=(90, 92, 90, 255), width=2)
    d.text((32, 20), "0.50", fill=(150, 230, 140, 255), anchor="mm", font=ImageFont.load_default(size=16))
    d.rectangle((8, 40, 24, 50), fill=(150, 152, 150, 255), outline=(110, 110, 108, 255))
    d.rectangle((28, 40, 44, 50), fill=(150, 152, 150, 255), outline=(110, 110, 108, 255))
    M.ao_border(img, 3, 0.18)
    return img


def net_square(seed, colour=(238, 238, 232), pitch=4, torn=0.0):
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed)
    for y in range(32):
        for x in range(32):
            if x % pitch == 0 or y % pitch == 0:
                if torn and rng.random() < torn:
                    continue
                px[x, y] = M.rgba(M.lift(colour, rng.uniform(-14, 6)))
    return img


# the detail set's hose cabinet and extinguisher textures, copied under this level's keys
L1_TEX = {"r4k-l1-red": "detail/l1red", "r4k-l1-hose": "detail/l1hose", "r4k-l1-glass": "detail/l1cabglass",
          "r4k-l1-greydark": "detail/l1greydark", "r4k-l1-hoselabel": "detail/l1hoselabel", "r4k-l1-steel": "detail/l1steel",
          "r4k-l1-steeldark": "detail/l1steeldark", "r4k-l1-brass": "level5/brass", "r4k-l1-iron": "detail/l1iron",
          "r4k-l1-white": "detail/l1white", "r4k-l1-black": "detail/l1black", "r4k-l1-dial": "detail/l1dial",
          "r4k-l1-extsign": "detail/l1extsign"}
L1_KEY = {v.split("/")[1]: k for k, v in L1_TEX.items()}


def textures(save):
    s = save
    # --- shared metals and plastics
    s(chrome(8001), "r4k-chrome")
    s(satin(8002), "r4k-satin")
    s(satin(8003, (190, 194, 198)), "r4k-alu")
    s(plastic(8004, (34, 34, 36)), "r4k-black")
    s(plastic(8005, (232, 230, 222)), "r4k-white-plastic")
    bolt = M.noise_hv((122, 120, 114), 3, 8006, (32, 32), 3, (16, 8))
    M.rust(bolt, amount=0.3, seed=8007)
    s(bolt, "r4k-bolt")
    # --- the hose cabinet and extinguisher
    for key, src in L1_TEX.items():
        s(Image.open(os.path.join(ASSETS, "textures", "block", src + ".png")).convert("RGBA"), key)
    # --- notice board
    s(cork(8010), "r4k-cork")
    for i, k in enumerate(("memo", "grid", "note", "blue", "pink", "green")):
        s(sheet(k, 8011 + i), f"r4k-sheet-{k}")
    for i, (name, c) in enumerate((("red", (196, 40, 36)), ("blue", (40, 80, 180)), ("yellow", (230, 196, 40)),
                                   ("green", (50, 150, 70)))):
        s(plastic(8020 + i, c, 3), f"r4k-pin-{name}")
    # --- wall clock, mirror
    s(clock_face(8030), "r4k-clockface")
    s(plastic(8031, (42, 42, 46)), "r4k-bezel")
    s(plastic(8032, (178, 34, 30), 3), "r4k-hand-red")
    s(mirror_tex(8040), "r4k-mirror")
    for section in (tex_stall, tex_bleacher, tex_hood, tex_flag, tex_goal, tex_boards):
        section(s)
    textures2(s)
    textures3(s)


def tex_stall(s):
    # --- stall
    s(porcelain(8050), "r4k-porcelain")
    low = porcelain(8051)
    M.grime(low, amount=0.1, seed=8052, cover=0.45)
    s(low, "r4k-porcelain-low")
    s(bowl_top(8053), "r4k-bowltop")
    s(laminate(8054), "r4k-laminate")
    tissue = M.noise_hv((242, 240, 234), 2, 8055, (32, 32), 2, (16, 8))
    M.emboss_lines(tissue, ys=(4, 12, 20, 28), strength=0.05)
    s(tissue, "r4k-tissue")


def tex_bleacher(s):
    # --- bleachers
    plank = M.brushed_metal(8060, base=(184, 188, 190), streak=8, sheen=12)
    M.emboss_lines(plank, ys=(5, 11, 16, 21, 27), strength=0.14)
    M.scratches(plank, 6, 8061, (3, 9), 0.12, angle=0)
    M.grime(plank, amount=0.08, seed=8062, cover=0.4)
    s(plank, "r4k-plank")
    steel = M.painted_metal(8063, base=(78, 80, 84), panel=False, chips=6, under=(120, 116, 110))
    M.rust(steel, amount=0.08, seed=8064)
    M.grime(steel, amount=0.1, seed=8065, cover=0.4)
    s(steel, "r4k-steel")


def tex_hood(s):
    # --- fume hood
    s(enamel(8070, (188, 180, 162), bias="bottom"), "r4k-cab")
    s(enamel(8071, (222, 218, 206), grime=0.04, chips=1), "r4k-hood")
    s(enamel(8072, (204, 204, 198), grime=0.08, chips=0), "r4k-liner")
    ep = M.noise_hv((36, 38, 40), 2, 8073, (32, 32), 2, (16, 8))
    rng = random.Random(8074)
    for _ in range(40):
        ep.putpixel((rng.randrange(32), rng.randrange(32)), M.rgba((52, 54, 56)))
    M.scratches(ep, 5, 8075, (2, 6), 0.1)
    s(ep, "r4k-epoxy")
    vent = M.noise_hv((60, 62, 64), 2, 8076, (32, 32), 2, (16, 8))
    for y in range(0, 32, 4):
        for x in range(32):
            M.touch(vent, x, y, 0.3)
            M.touch(vent, x, y + 1, -0.35)
    s(vent, "r4k-vent")
    s(enamel(8077, (70, 72, 76), grime=0.02, chips=1), "r4k-sashframe")
    s(M.noise_hv((236, 236, 228), 1, 8078, (32, 32), 1, (16, 8)), "r4k-lens")
    s(monitor_face(8079), "r4k-monitor")
    led = Image.new("RGBA", (32, 32), (90, 250, 110, 255))
    s(led, "r4k-led")
    s(M.galvanised(8080, base=(168, 172, 174)), "r4k-duct")


def tex_flag(s):
    # --- flagpole
    s(satin(8090, (200, 202, 204), direction="v"), "r4k-pole")
    con = M.concrete(8091, base=(176, 172, 162), cracks=0, aggregate=0.05)
    M.grime(con, amount=0.12, seed=8092, cover=0.5)
    s(con, "r4k-plinth")
    s(plaque(8093), "r4k-plaque")
    br = M.noise_hv((132, 102, 58), 4, 8094, (32, 32), 4, (16, 8))
    M.grime(br, amount=0.2, seed=8095, color=(70, 98, 80), cover=0.5)
    s(br, "r4k-bronze")
    s(M.brushed_metal(8096, base=(206, 168, 84), streak=8, sheen=18, drift=0.2), "r4k-gold")
    rope = M.noise_hv((226, 222, 210), 3, 8097, (32, 32), 3, (16, 8))
    for y in range(32):
        for x in range(32):
            if (x + y * 2) % 4 == 0:
                M.touch(rope, x, y, -0.12)
    s(rope, "r4k-rope")


def tex_goal(s):
    # --- football goal
    gw = M.noise_hv((238, 238, 234), 2, 8100, (32, 32), 2, (16, 8))
    M.scratches(gw, 4, 8101, (2, 5), -0.12)
    M.grime(gw, amount=0.06, seed=8102, cover=0.35)
    s(gw, "r4k-goal")
    s(net_square(8103), "r4k-gnet")
    for half in ("lower", "upper"):
        for f in ("e", "w"):
            s(side_net(half, "east" if f == "e" else "west", 8104), f"r4k-gnet-side-{half}-{f}")
    peg = M.galvanised(8105, base=(150, 152, 150))
    M.rust(peg, amount=0.2, seed=8106)
    s(peg, "r4k-galv-peg")


def tex_boards(s):
    # --- boards on posts
    bb = M.painted_metal(8110, base=(120, 124, 126), panel=True, chips=4, screws=True)
    M.rust(bb, amount=0.08, seed=8111)
    M.drips(bb, n=3, seed=8112, color=(120, 80, 50), length=(6, 14), strength=0.3)
    s(bb, "r4k-bback-steel")
    ply = M.wood_planks(8113, base=(150, 118, 80), planks=2, direction="h", grain=3)
    M.grime(ply, amount=0.12, seed=8114, cover=0.5)
    s(ply, "r4k-bback-wood")
    fs_ = M.painted_metal(8115, base=(64, 68, 72), panel=False, chips=5, under=(130, 126, 118))
    M.rust(fs_, amount=0.1, seed=8116)
    s(fs_, "r4k-frame-steel")
    fw = M.wood_planks(8117, base=(122, 92, 60), planks=1, direction="h", grain=4)
    M.grime(fw, amount=0.15, seed=8118, cover=0.5)
    s(fw, "r4k-frame-wood")



# ======================================================================== wall fittings

def ring_z(prefix, cx, cy, r, t, z0, z1, tex, n=12, phase=0.0, faces=("north", "up", "down")):
    """A ring of n bars round an axis along z (a hose coil, a bezel): each bar t wide (radially), its outer edge at r."""
    L = 2 * r * math.tan(math.pi / n) + 0.04
    return [box(f"{prefix}{k}", (cx - L / 2, cy + r - t, z0), (cx + L / 2, cy + r, z1), tex, faces=faces,
                rot=(0, 0, k * 360 / n + phase) if (k or phase) else None, origin=(cx, cy, (z0 + z1) / 2)) for k in range(n)]


def hose_cabinet():
    """The detail set's hose cabinet without its wall cube, its reel rebuilt round: a drum, three coils of hose, a hub."""
    els = [e for e in from_detail("l1deco-hosecab") if not e["name"].startswith(("ReelBack", "Coil", "Hub"))]
    cx, cy = 8.0, 7.25
    hose, dark, steel = L1_KEY["l1hose"], L1_KEY["l1steeldark"], L1_KEY["l1steel"]
    els += octo("Drum", (cx - 4.4, cy - 4.4, 14.85), (cx + 4.4, cy + 4.4, 15.5), dark, axis="z", faces=fs("south"))
    for i, (r, ph) in enumerate(((4.1, 0), (3.25, 15), (2.4, 0))):
        els += ring_z(f"Coil{i}_", cx, cy, r, 0.85, 13.75 + 0.05 * i, 14.85, hose, phase=ph)
    els += octo("Hub", (cx - 0.9, cy - 0.9, 13.4), (cx + 0.9, cy + 0.9, 14.85), steel, axis="z", faces=fs("south"))
    return els


def from_detail(name):
    """A shared detail shape hung on its wall cube (at z 0..16, the fitting at negative z) moved onto this level's wall
    at z = 16, without the cube, its textures under this level's keys."""
    d = json.load(open(os.path.join(ASSETS, "shapes", "block", "detail", name + ".json"), encoding="utf-8"))
    els = [e for e in d["elements"] if e["name"] != "Wall"]
    els = move(els, dz=16)
    for e in els:
        for f in e["faces"].values():
            f["texture"] = "#" + L1_KEY[f["texture"][1:]]
    return els


def notice(part):
    """One half of a cork board two blocks wide (l: x 0..15, its seam at x 0; r: x 1..16, its seam at x 16)."""
    fr, ck = "r4k-alu", "r4k-cork"
    seam_face = "west" if part == "l" else "east"
    if part == "l":
        x0, x1, e0, e1 = 0, 15, 14.2, 15
    else:
        x0, x1, e0, e1 = 1, 16, 1, 1.8
    c0, c1 = (0, 14.2) if part == "l" else (1.8, 16)
    els = [box("Cork", (c0, 3.8, 15.2), (c1, 13.2, 16), ck, faces=("north",)),
           box("FrameT", (x0, 13.2, 14.9), (x1, 14, 16), fr, faces=fs("south", seam_face)),
           box("FrameB", (x0, 3, 14.9), (x1, 3.8, 16), fr, faces=fs("south", seam_face)),
           box("FrameE", (e0, 3.8, 14.9), (e1, 13.2, 16), fr, faces=fs("south", "up", "down")),
           # the frame's inner lip, a step down to the cork
           box("LipT", (c0, 12.8, 15.05), (c1, 13.2, 15.2), fr, faces=("north", "down")),
           box("LipB", (c0, 3.8, 15.05), (c1, 4.2, 15.2), fr, faces=("north", "up"))]
    lip_e = (13.8, 14.2) if part == "l" else (1.8, 2.2)
    els.append(box("LipE", (lip_e[0], 4.2, 15.05), (lip_e[1], 12.8, 15.2), fr, faces=("north", "east" if part == "l" else "west")))
    # pinned sheets: (kind, x centre, y centre, w, h, tilt, layer, pin)
    if part == "l":
        sheets = [("memo", 3.2, 8.6, 3.4, 4.6, -3, 0, "red"), ("grid", 7.6, 9.4, 4.6, 3.4, 2, 1, "blue"),
                  ("note", 6.4, 6.0, 2.2, 2.2, 6, 2, "yellow"), ("pink", 11.2, 7.8, 3.2, 4.4, -2, 0, "green")]
    else:
        sheets = [("blue", 4.6, 8.4, 3.4, 4.6, 2.5, 0, "red"), ("green", 9.2, 9.0, 3.4, 4.6, -4, 1, "yellow"),
                  ("memo", 13.0, 7.6, 3.2, 4.4, 1.5, 0, "blue"), ("note", 10.6, 5.6, 2.2, 2.2, -7, 2, "red")]
    for i, (k, cx, cy, w, h, tilt, layer, pin) in enumerate(sheets):
        tilt *= 1.6
        z1 = 15.2 - 0.06 * layer
        el = box(f"Sheet{i}", (cx - w / 2, cy - h / 2, z1 - 0.08), (cx + w / 2, cy + h / 2, z1), f"r4k-sheet-{k}",
                 faces=("north",), rot=(0, 0, tilt * ZSIGN) if tilt else None, origin=(cx, cy + h / 2 - 0.4, z1))
        full_uv(el, "north")
        els.append(el)
        py = cy + h / 2 - 0.5
        els.append(box(f"Pin{i}", (cx - 0.3, py - 0.3, z1 - 0.62), (cx + 0.3, py + 0.3, z1 - 0.08), f"r4k-pin-{pin}",
                       faces=fs("south")))
    return els


def wallclock():
    """A round school clock on the wall: a ring of twelve bezel bars, the dial, the hands at 3:52, the red second hand."""
    cx, cy = 8.0, 6.0
    R, T = 3.7, 0.7           # the bezel's outer radius and its width
    L = 2 * R * math.tan(math.pi / 12) + 0.06
    els = []
    for k in range(12):
        el = box(f"Bezel{k}", (cx - L / 2, cy + R - T, 14.6), (cx + L / 2, cy + R, 16), "r4k-bezel",
                 faces=("north", "up", "down"), rot=(0, 0, k * 30) if k else None, origin=(cx, cy, 15.3))
        els.append(el)
    # an inner step of the bezel, then the dial
    Ri = R - T
    L2 = 2 * Ri * math.tan(math.pi / 12) + 0.04
    for k in range(12):
        els.append(box(f"Step{k}", (cx - L2 / 2, cy + Ri - 0.3, 15.0), (cx + L2 / 2, cy + Ri, 16), "r4k-satin",
                       faces=("north", "down"), rot=(0, 0, k * 30 + 15), origin=(cx, cy, 15.5)))
    r = Ri + 0.05
    # the dial in three stepped boxes (a rounded outline that stays inside the bezel even where the cut-out is not
    # honoured), each showing its own part of the picture (on a north face u runs from +x to -x, v from the top down)
    for n, (fx, fy) in enumerate(((1.0, 0.58), (0.58, 1.0), (0.86, 0.86))):
        x0, x1, y0, y1 = cx - r * fx, cx + r * fx, cy - r * fy, cy + r * fy
        el = box(f"Dial{n}", (x0, y0, 15.4 + 0.01 * n), (x1, y1, 15.6), "r4k-clockface", faces=("north",))
        el["faces"]["north"]["uv"] = [round((cx + r - x1) / (2 * r) * 16, 4), round((cy + r - y1) / (2 * r) * 16, 4),
                                      round((cx + r - x0) / (2 * r) * 16, 4), round((cy + r - y0) / (2 * r) * 16, 4)]
        els.append(el)
    # the hands: hour (3:52 -> 116 degrees clockwise from 12), minute (312), second (200); boxes along +y from the centre
    for name, ang, ln, tail, w, z, tex in (("Hour", 116, 1.8, 0.5, 0.62, 15.25, "r4k-black"),
                                          ("Minute", 312, 2.65, 0.6, 0.42, 15.05, "r4k-black"),
                                          ("Second", 200, 2.75, 0.9, 0.2, 14.85, "r4k-hand-red")):
        els.append(box(name, (cx - w / 2, cy - tail, z - 0.15), (cx + w / 2, cy + ln, z), tex, faces=("north", "east", "west", "up"),
                       rot=(0, 0, -ang * ZSIGN), origin=(cx, cy, z)))
    els.append(box("Cap", (cx - 0.35, cy - 0.35, 14.45), (cx + 0.35, cy + 0.35, 14.7), "r4k-hand-red", faces=fs("south")))
    return els


def mirror():
    """A restroom mirror: the glass in a stainless channel frame, clips at its corners, a stainless shelf under it."""
    st = "r4k-satin"
    g = box("Glass", (1.6, 2.6, 15.55), (14.4, 11.4, 15.8), "r4k-mirror", faces=("north",))
    full_uv(g)
    els = [g,
           box("FrameT", (1.0, 11.4, 15.3), (15.0, 12.0, 16), st, faces=fs("south")),
           box("FrameB", (1.0, 2.0, 15.3), (15.0, 2.6, 16), st, faces=fs("south")),
           box("FrameL", (1.0, 2.6, 15.3), (1.6, 11.4, 16), st, faces=fs("south", "up", "down")),
           box("FrameR", (14.4, 2.6, 15.3), (15.0, 11.4, 16), st, faces=fs("south", "up", "down")),
           box("LipT", (1.6, 11.15, 15.45), (14.4, 11.4, 15.55), st, faces=("north", "down")),
           box("LipB", (1.6, 2.6, 15.45), (14.4, 2.85, 15.55), st, faces=("north", "up")),
           box("Shelf", (2.0, 1.0, 12.8), (14.0, 1.4, 16), st, faces=fs("south")),
           box("ShelfLip", (2.0, 0.6, 12.5), (14.0, 1.4, 12.8), st, faces=fs("south")),
           box("BracketL", (2.6, 0.0, 14.6), (3.0, 1.0, 16), st, faces=fs("south", "up")),
           box("BracketR", (13.0, 0.0, 14.6), (13.4, 1.0, 16), st, faces=fs("south", "up"))]
    for x in (1.15, 14.55):
        for y in (2.15, 11.55):
            els.append(box(f"Clip{x}{y}", (x, y, 15.1), (x + 0.3, y + 0.3, 15.3), "r4k-chrome", faces=fs("south")))
    return els


def plate(face):
    """A restroom pictogram plate: the face on a plate held off the wall, a satin edge, four screw caps."""
    p = box("Plate", (4.8, 3.3, 15.55), (11.2, 9.7, 15.85), {"front": face, "side": "r4k-satin"}, faces=fs("south"))
    full_uv(p, "north")
    els = [p, box("Back", (4.5, 3.0, 15.85), (11.5, 10.0, 16), "r4k-satin", faces=fs("south"))]
    for x in (5.15, 10.35):
        for y in (3.65, 8.85):
            els.append(box(f"Cap{x}{y}", (x, y, 15.3), (x + 0.5, y + 0.5, 15.55), "r4k-chrome", faces=fs("south")))
    return els


def wall_fittings():
    out = {}
    out["l52-sign-mirror"] = mirror()
    out["l52-sign-men"] = plate("sign-men")
    out["l52-sign-women"] = plate("sign-women")
    out["l52-sign-hose"] = hose_cabinet()
    out["l52-sign-ext"] = from_detail("l1deco-extinguisher")
    out["l52-sign-notice-l"] = notice("l")
    out["l52-sign-notice-r"] = notice("r")
    out["l52-sign-wallclock"] = wallclock()
    return out


# ======================================================================== the stall

def stall(part):
    """A restroom stall facing north: the pan against the wall at z 16, the partition along x 15-16 (the stall's left
    seen from in front) on a pilaster at the front, its panel 0.3 block clear of the floor and 1.8 blocks high."""
    lam, ch = "r4k-laminate", "r4k-chrome"
    top = 16 if part == "lower" else 12.0
    els = []
    # the partition: pilaster, panel, the wall channel; the panel shows on both sides (the next stall is at x 16)
    els.append(box("Pilaster", (14.8, 3.6 if part == "lower" else 0, 0), (16, top, 1.4), lam))
    pan_top = 16 if part == "lower" else 12.8
    els.append(box("Panel", (15.1, 4.8 if part == "lower" else 0, 1.4), (15.9, pan_top, 15.4), lam, faces=fs("north")))
    els.append(box("Channel", (14.85, 4.4 if part == "lower" else 0, 15.4), (16, pan_top, 16), ch, faces=fs("south")))
    for y in ((6.4, 13.4) if part == "lower" else (8.6,)):
        els.append(box(f"Clip{y}", (14.85, y, 1.4), (15.1, y + 1.4, 2.6), ch, faces=fs("east")))
        els.append(box(f"ClipE{y}", (15.9, y, 1.4), (16.0, y + 1.4, 2.6), ch, faces=("north", "east", "south", "up", "down")))
    if part == "lower":
        els += [box("Shoe", (14.5, 0, -0.3), (16, 3.4, 1.7), ch, faces=fs("down")),
                box("ShoeLip", (14.4, 3.2, -0.4), (16, 3.6, 1.8), ch, faces=fs("down"))]
        els += toilet(7.5)
        # the roll holder on the partition, at hand height
        els += [box("HolderPlate", (14.6, 8.8, 7.4), (15.1, 11.8, 10.8), ch, faces=fs("east")),
                box("HolderHood", (12.4, 11.2, 7.4), (14.6, 11.6, 10.8), ch),
                box("HolderLip", (12.2, 10.4, 7.4), (12.6, 11.6, 10.8), ch)]
        els += octo("Roll", (12.75, 9.25, 7.8), (14.45, 10.95, 10.4), "r4k-tissue", axis="z")
        els += [box("Sheet", (12.9, 7.2, 8.2), (13.0, 9.6, 10.0), "r4k-tissue", faces=("east", "west", "down")),
                box("Spindle", (13.3, 9.8, 7.5), (13.9, 10.4, 10.7), ch, faces=("north", "south"))]
    else:
        els += [box("PanelCap", (15.0, 12.8, 1.4), (16, 13.1, 15.4), ch, faces=fs("south")),
                box("Headrail", (0, 12.0, 0.1), (16, 13.2, 1.5), "r4k-satin", faces=("north", "south", "up", "down")),
                box("HeadrailLip", (0, 11.6, 0.3), (16, 12.0, 0.7), "r4k-satin", faces=("north", "south", "down")),
                box("RailBracket", (14.6, 11.4, 1.5), (16, 13.2, 2.2), ch, faces=fs("east"))]
        # a coat hook on the partition
        els += [box("HookRose", (14.6, 8.8, 11.9), (15.1, 10.4, 13.1), ch, faces=fs("east")),
                box("HookArm", (13.4, 9.3, 12.25), (14.6, 9.8, 12.75), ch),
                box("HookTip", (13.0, 9.3, 12.25), (13.5, 10.6, 12.75), ch),
                box("HookArm2", (13.9, 10.0, 12.3), (14.6, 10.4, 12.7), ch),
                box("HookTip2", (13.7, 10.0, 12.3), (14.0, 11.2, 12.7), ch)]
    return els


def toilet(cx):
    por, low, ch = "r4k-porcelain", "r4k-porcelain-low", "r4k-chrome"
    seat = "r4k-white-plastic"
    nd = fs("down")
    els = []

    def lay(name, y0, y1, hw, z0, z1, nose_hw, nose_z, tex=por):
        """One course of the pan: the body and a narrower nose in front, for a rounded plan."""
        els.append(box(name, (cx - hw, y0, z0), (cx + hw, y1, z1), tex, faces=nd))
        els.append(box(name + "N", (cx - nose_hw, y0 + 0.01, nose_z), (cx + nose_hw, y1 - 0.01, z0), tex, faces=nd))

    lay("Foot", 0, 0.6, 2.2, 6.6, 14.6, 1.4, 6.1, low)
    lay("Pedestal", 0.6, 3.4, 1.75, 7.0, 14.2, 1.1, 6.6, low)
    lay("Bowl1", 3.4, 4.6, 2.5, 3.8, 13.6, 1.7, 3.1)
    lay("Bowl2", 4.6, 5.8, 3.0, 2.8, 13.8, 2.1, 2.1)
    rim = box("Rim", (cx - 3.3, 5.8, 2.3), (cx + 3.3, 6.6, 13.6), {"top": "r4k-bowltop", "side": por}, faces=nd)
    full_uv(rim, "up")
    els.append(rim)
    els.append(box("RimN", (cx - 2.3, 5.81, 1.8), (cx + 2.3, 6.59, 2.3), por, faces=nd))
    els.append(box("Rear", (cx - 1.9, 3.4, 13.6), (cx + 1.9, 6.6, 15.6), por, faces=fs("down", "north")))
    # the bolt caps either side of the foot
    for x in (cx - 2.6, cx + 1.8):
        els += [box(f"BoltCap{x}", (x, 0, 11.3), (x + 0.8, 0.7, 12.1), por, faces=nd),
                box(f"BoltTop{x}", (x + 0.15, 0.7, 11.45), (x + 0.65, 0.95, 11.95), por, faces=nd)]
    # the open-front seat and its hinges
    els += [box("SeatL", (cx - 3.2, 6.6, 2.6), (cx - 1.8, 7.2, 12.4), seat, faces=nd),
            box("SeatR", (cx + 1.8, 6.6, 2.6), (cx + 3.2, 7.2, 12.4), seat, faces=nd),
            box("SeatB", (cx - 3.0, 6.6, 11.0), (cx + 3.0, 7.19, 12.6), seat, faces=nd),
            box("SeatLN", (cx - 2.9, 6.61, 2.2), (cx - 2.0, 7.19, 2.6), seat, faces=nd),
            box("SeatRN", (cx + 2.0, 6.61, 2.2), (cx + 2.9, 7.19, 2.6), seat, faces=nd)]
    for x in (cx - 2.4, cx + 1.6):
        els.append(box(f"Hinge{x}", (x, 6.6, 12.6), (x + 0.8, 7.6, 13.4), ch, faces=nd))
    # the lid raised and leaning back against the flush tube
    els.append(bar("Lid", (cx, 7.2, 13.0), (cx, 12.6, 13.5), 5.6, seat, d=0.6))
    # the exposed flushometer: valve body, cap, handle, supply with its stop and wall flange, the flush tube, breaker, spud
    els += octo("Valve", (cx - 0.75, 11.4, 14.0), (cx + 0.75, 13.6, 15.5), ch)
    els += octo("ValveCap", (cx - 0.55, 13.6, 14.2), (cx + 0.55, 14.3, 15.3), ch)
    els += [box("Handle", (cx - 3.4, 12.25, 14.45), (cx - 0.75, 12.65, 14.85), ch),
            box("HandleKnob", (cx - 3.8, 12.05, 14.35), (cx - 3.3, 12.85, 14.95), ch),
            box("HandleNut", (cx - 1.3, 12.0, 14.25), (cx - 0.7, 12.9, 15.05), ch)]
    els += octo("Supply", (cx + 0.75, 12.4, 14.35), (cx + 3.4, 13.0, 14.95), ch, axis="x")
    els += octo("Stop", (cx + 3.4, 12.0, 14.0), (cx + 4.6, 13.4, 15.3), ch, axis="x")
    els += [box("StopCap", (cx + 3.75, 13.4, 14.3), (cx + 4.25, 14.0, 15.0), ch),
            box("StopIn", (cx + 3.7, 12.4, 15.3), (cx + 4.3, 13.0, 15.8), ch, faces=fs("north", "south")),
            box("Flange", (cx + 3.2, 11.9, 15.8), (cx + 4.8, 13.5, 16), ch, faces=fs("south"))]
    els += octo("Tube", (cx - 0.4, 7.2, 14.2), (cx + 0.4, 11.4, 15.0), ch)
    els += octo("Breaker", (cx - 0.6, 9.2, 14.0), (cx + 0.6, 10.2, 15.2), ch)
    els += octo("Spud", (cx - 0.7, 6.6, 13.9), (cx + 0.7, 7.3, 15.3), ch)
    return els


# ======================================================================== the bleachers

def zbar(name, p0, p1, w, tex, z0, z1, faces=ALL):
    """A bar of width w from p0 to p1 (x, y) in the plane z0..z1: a box along x turned about Z."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    return box(name, (cx - L / 2, cy - w / 2, z0), (cx + L / 2, cy + w / 2, z1), tex, faces=faces,
               rot=(0, 0, ZROT * ang), origin=(cx, cy, (z0 + z1) / 2))


ZROT = 1   # the sign of rotationZ that turns +x toward +y (counter-clockwise seen from the south)


def bleacher():
    """One row facing north: the toe board and foot plank in front, the seat at the back, the kick plate behind the seat
    up to the block's top (where the next row, a block up and back, carries on with its toe board), the steel under."""
    pl, st, cap, alu = "r4k-plank", "r4k-steel", "r4k-steel", "r4k-alu"
    els = [box("Toe", (0, 0, 0), (16, 4.6, 0.6), alu, faces=fs("down")),
           box("Kick", (0, 10.6, 15.3), (16, 16, 16), alu, faces=fs("down"))]
    for i, (z0, z1) in enumerate(((0.1, 3.6), (3.9, 7.4))):
        els += [box(f"Foot{i}", (0.3, 5.0, z0), (15.7, 6.0, z1), pl),
                box(f"FootCapL{i}", (15.7, 4.9, z0 - 0.05), (16, 6.1, z1 + 0.05), cap, faces=fs("west")),
                box(f"FootCapR{i}", (0, 4.9, z0 - 0.05), (0.3, 6.1, z1 + 0.05), cap, faces=fs("east"))]
    els.append(box("FootNose", (0, 4.6, 0.0), (16, 5.0, 0.7), alu, faces=fs("up", "east", "west")))
    for i, (z0, z1) in enumerate(((9.0, 10.9), (11.1, 13.0), (13.2, 15.1))):
        els += [box(f"Seat{i}", (0.3, 11.9, z0), (15.7, 13.0, z1), pl),
                box(f"SeatCapL{i}", (15.7, 11.8, z0 - 0.05), (16, 13.1, z1 + 0.05), cap, faces=fs("west")),
                box(f"SeatCapR{i}", (0, 11.8, z0 - 0.05), (0.3, 13.1, z1 + 0.05), cap, faces=fs("east"))]
    els.append(box("SeatNose", (0, 11.2, 8.9), (16, 11.9, 9.5), alu, faces=fs("up", "east", "west")))
    # the frames under, at two places across the row
    for k, x in enumerate((1.4, 13.6)):
        els += [box(f"UpF{k}", (x, 0, 3.2), (x + 1.0, 4.4, 4.2), st, faces=fs("down")),
                box(f"UpB{k}", (x, 0, 11.6), (x + 1.0, 11.0, 12.6), st, faces=fs("down")),
                box(f"FootArm{k}", (x - 0.1, 4.4, 0.6), (x + 1.1, 5.0, 7.4), st),
                box(f"SeatArm{k}", (x - 0.1, 11.0, 8.8), (x + 1.1, 11.9, 15.3), st),
                box(f"Sill{k}", (x - 0.2, 0, 2.6), (x + 1.2, 0.5, 13.2), st, faces=fs("down")),
                bar(f"Diag{k}", (x + 0.5, 0.6, 4.4), (x + 0.5, 10.4, 11.4), 0.7, st),
                bar(f"Gusset{k}", (x + 0.5, 9.0, 12.6), (x + 0.5, 11.0, 14.6), 0.6, st)]
    els += [box("BeamF", (0, 3.6, 4.2), (16, 4.4, 5.0), st, faces=fs("east", "west")),
            box("BeamB", (0, 10.2, 12.6), (16, 11.0, 13.4), st, faces=fs("east", "west")),
            box("Tie", (2.4, 0.4, 12.0), (13.6, 1.0, 12.5), st, faces=fs("east", "west")),
            zbar("Cross", (2.4, 1.0), (13.6, 9.8), 0.6, st, 12.7, 13.1)]
    # bolt heads on the frames' faces
    for k, x in enumerate((1.4, 13.6)):
        for (y, z) in ((4.7, 1.0), (4.7, 6.6), (11.5, 10.0), (11.5, 14.6)):
            els.append(box(f"Bolt{k}{y}{z}", (x - 0.35, y - 0.25, z - 0.25), (x - 0.1, y + 0.25, z + 0.25), "r4k-bolt",
                           faces=fs("east")))
    return els


# ======================================================================== the fume hood

def fumehood(part):
    """A lab fume hood, its back to the wall at z 16: the base cabinet and black worktop (lower), the hood (upper)."""
    cab, hood, liner, top, sat = "r4k-cab", "r4k-hood", "r4k-liner", "r4k-epoxy", "r4k-satin"
    els = []
    if part == "lower":
        els += [box("Plinth", (0.8, 0, 4.6), (15.2, 1.2, 16), "r4k-black", faces=("north", "east", "west")),
                box("Carcass", (0.4, 1.2, 3.8), (15.6, 14.2, 16), cab, faces=fs("south", "down")),
                box("Worktop", (0, 14.2, 3.0), (16, 16, 16), top, faces=fs("south")),
                box("Drip", (0, 13.9, 3.3), (16, 14.2, 3.6), top, faces=("north", "down", "east", "west"))]
        for k, (x0, x1) in enumerate(((0.7, 7.85), (8.15, 15.3))):
            els += [box(f"Door{k}", (x0, 1.6, 3.4), (x1, 13.8, 3.8), cab, faces=fs("south")),
                    box(f"DoorPanel{k}", (x0 + 1.0, 2.6, 3.25), (x1 - 1.0, 10.4, 3.4), cab, faces=fs("south")),
                    box(f"Vent{k}", (x0 + 1.4, 11.2, 3.3), (x1 - 1.4, 12.6, 3.4), "r4k-vent", faces=("north",))]
            hx = x1 - 0.9 if k == 0 else x0 + 0.5
            els += [box(f"Pull{k}", (hx, 7.4, 2.6), (hx + 0.4, 10.6, 3.0), sat),
                    box(f"PullA{k}", (hx, 7.6, 3.0), (hx + 0.4, 8.0, 3.4), sat, faces=fs("north", "south")),
                    box(f"PullB{k}", (hx, 10.0, 3.0), (hx + 0.4, 10.4, 3.4), sat, faces=fs("north", "south"))]
        for x in (0.45, 15.3):
            for y in (2.6, 11.8):
                els.append(box(f"Hinge{x}{y}", (x, y, 3.3), (x + 0.25, y + 1.2, 3.9), "r4k-chrome", faces=fs("south")))
        return els
    # the hood: lip, airfoil, posts, sides, casing, back and baffle, sash, monitor, services, duct stub
    els += [box("Lip", (1.6, 0, 3.0), (14.4, 0.45, 3.6), top, faces=fs("down")),
            box("Airfoil", (1.6, 0.45, 2.2), (14.4, 1.05, 3.4), sat, faces=fs("east", "west")),
            box("PostR", (0, 0, 2.4), (1.6, 13.6, 4.2), hood, faces=fs("down")),
            box("PostL", (14.4, 0, 2.4), (16, 13.6, 4.2), hood, faces=fs("down")),
            box("SideR", (0, 0, 4.2), (1.2, 13.6, 16), {"east": liner, "side": hood}, faces=fs("down", "south", "north")),
            box("SideL", (14.8, 0, 4.2), (16, 13.6, 16), {"west": liner, "side": hood}, faces=fs("down", "south", "north")),
            box("Casing", (0, 13.6, 2.0), (16, 15.2, 16), hood, faces=fs("south")),
            box("CasingBand", (0.3, 15.2, 2.6), (15.7, 15.5, 15.7), hood, faces=fs("south", "down")),
            box("Lens", (3.0, 13.4, 5.0), (13.0, 13.6, 12.0), "r4k-lens", faces=("down", "north", "south", "east", "west")),
            box("Back", (1.2, 0, 15.4), (14.8, 13.6, 16), "r4k-black", faces=("north",))]
    for k, (y0, y1) in enumerate(((0.45, 2.0), (2.7, 8.0), (8.7, 13.6))):
        els.append(box(f"Baffle{k}", (1.2, y0, 14.4), (14.8, y1, 14.9), liner, faces=("north", "up", "down")))
    # the sash, raised half way: its frame, the glass, the handle bar
    sash = "r4k-sashframe"
    els += [box("SashL", (1.6, 6.6, 2.7), (2.4, 13.6, 3.5), sash, faces=fs("up")),
            box("SashR", (13.6, 6.6, 2.7), (14.4, 13.6, 3.5), sash, faces=fs("up")),
            box("SashB", (2.4, 6.2, 2.6), (13.6, 7.4, 3.6), sash, faces=fs("east", "west")),
            box("Glass", (2.4, 7.4, 3.0), (13.6, 13.6, 3.2), "hood-glass", faces=("north", "south")),
            box("Handle", (3.0, 6.55, 1.6), (13.0, 7.05, 2.1), sat),
            box("HandleA", (3.2, 6.6, 2.1), (3.7, 7.0, 2.6), sat, faces=fs("north", "south")),
            box("HandleB", (12.3, 6.6, 2.1), (12.8, 7.0, 2.6), sat, faces=fs("north", "south"))]
    # the airflow monitor on the right post, its lit LED
    mon = box("Monitor", (0.1, 8.6, 1.8), (1.5, 11.6, 2.4), {"front": "r4k-monitor", "side": "r4k-cab"}, faces=fs("south"))
    full_uv(mon, "north")
    els += [mon, box("Led", (0.9, 8.9, 1.65), (1.25, 9.25, 1.8), "r4k-led", faces=fs("south"), glow=200)]
    # services: a gas tap on the left side, a gooseneck over a cup sink at the back right
    els += [box("GasBody", (14.0, 2.4, 6.0), (14.8, 3.4, 7.0), "r4k-chrome", faces=fs("east")),
            box("GasNozzle", (13.0, 2.7, 6.3), (14.0, 3.1, 6.7), "r4k-chrome"),
            box("GasLever", (14.1, 3.4, 6.3), (14.5, 4.6, 6.7), "r4k-pin-yellow"),
            box("Sink", (2.0, 0.45, 9.0), (4.6, 0.8, 11.6), {"top": "r4k-black", "side": top}, faces=fs("down"))]
    els += octo("Riser", (2.9, 0.45, 12.5), (3.7, 6.0, 13.3), "r4k-chrome")
    els += [box("Arm", (2.95, 5.4, 9.9), (3.65, 6.1, 12.5), "r4k-chrome"),
            box("Spout", (2.95, 4.3, 9.9), (3.65, 5.4, 10.6), "r4k-chrome"),
            box("Tap", (1.8, 2.6, 12.7), (4.8, 3.0, 13.1), "r4k-chrome"),
            box("TapK1", (1.6, 2.4, 12.6), (2.0, 3.6, 13.2), "r4k-pin-blue"),
            box("TapK2", (4.6, 2.4, 12.6), (5.0, 3.6, 13.2), "r4k-pin-blue")]
    els += octo("Duct", (5.4, 15.2, 7.4), (10.6, 16, 12.6), "r4k-duct")
    els += octo("DuctBand", (5.2, 15.5, 7.2), (10.8, 15.8, 12.8), "r4k-duct", faces=fs("down"))
    return els


# ======================================================================== the flagpole

ROPE_X = (8.95, 9.2)


def halyard(y0, y1):
    """The halyard's two runs down the pole's +x side."""
    return [box(f"Rope{k}{y0}", (ROPE_X[0], y0, z0), (ROPE_X[1], y1, z0 + 0.25), "r4k-rope", faces=fs("up", "down"))
            for k, z0 in enumerate((7.55, 8.2))]


def flagpole(part):
    pole, con = "r4k-pole", "r4k-plinth"
    els = []
    if part == "base":
        els += [box("Step1", (2.5, 0, 2.5), (13.5, 1.6, 13.5), con, faces=fs("down")),
                box("Chamfer1", (2.9, 1.6, 2.9), (13.1, 1.95, 13.1), con, faces=fs("down")),
                box("Step2", (4.2, 1.95, 4.2), (11.8, 4.2, 11.8), con, faces=fs("down")),
                box("Chamfer2", (4.6, 4.2, 4.6), (11.4, 4.55, 11.4), con, faces=fs("down"))]
        pq = box("Plaque", (5.6, 2.3, 3.95), (10.4, 3.9, 4.2), {"front": "r4k-plaque", "side": "r4k-bronze"}, faces=fs("south"))
        full_uv(pq, "north")
        els.append(pq)
        for x in (5.85, 9.85):
            for y in (2.5, 3.4):
                els.append(box(f"Screw{x}{y}", (x, y, 3.8), (x + 0.3, y + 0.3, 3.95), "r4k-bronze", faces=fs("south")))
        els += octo("Collar", (6.5, 4.55, 6.5), (9.5, 5.5, 9.5), "r4k-alu")
        els += octo("CollarTop", (6.85, 5.5, 6.85), (9.15, 6.1, 9.15), "r4k-alu")
        els += octo("Pole", (7.2, 6.1, 7.2), (8.8, 16, 8.8), pole, faces=fs("down"))
        # the cleat at hand height, the halyard made fast on it and its tail
        els += [box("CleatBase", (8.75, 11.0, 7.65), (9.3, 13.4, 8.35), "r4k-alu", faces=fs("west")),
                box("CleatHorn", (9.3, 10.4, 7.7), (9.85, 14.0, 8.3), "r4k-alu"),
                box("Wrap1", (9.25, 11.5, 7.5), (9.95, 11.9, 8.5), "r4k-rope"),
                box("Wrap2", (9.25, 12.5, 7.5), (9.95, 12.9, 8.5), "r4k-rope"),
                box("Tail", (9.6, 8.2, 8.3), (9.85, 11.5, 8.55), "r4k-rope", faces=fs("up")),
                box("TailLoop", (9.45, 7.8, 8.3), (10.0, 8.2, 8.55), "r4k-rope")]
        els += halyard(13.4, 16)
    elif part == "pole":
        els += octo("Pole", (7.3, 0, 7.3), (8.7, 16, 8.7), pole, faces=fs("up", "down"))
        els += halyard(0, 16)
    else:
        els += octo("Pole", (7.4, 0, 7.4), (8.6, 12.6, 8.6), pole, faces=fs("down"))
        els += octo("Truck", (6.8, 12.6, 6.8), (9.2, 13.6, 9.2), "r4k-alu")
        els += [box("Sheave", (9.2, 12.75, 7.5), (9.75, 13.45, 8.5), "r4k-alu", faces=fs("west")),
                box("Spindle", (7.7, 13.6, 7.7), (8.3, 14.1, 8.3), "r4k-gold", faces=fs("down"))]
        els += octo("Ball", (6.9, 14.2, 6.9), (9.1, 15.5, 9.1), "r4k-gold")
        els += octo("BallY", (7.3, 13.95, 7.3), (8.7, 15.75, 8.7), "r4k-gold")
        els += octo("BallT", (7.7, 13.8, 7.7), (8.3, 15.95, 8.3), "r4k-gold")
        els += halyard(0, 12.6)
        # the flag in five panels, folding as it flies toward +x, its leading edge on the halyard
        y0, y1 = 5.4, 12.4
        angles = (10, -16, 14, -12, 8)
        n = len(angles)
        L = 13.3 / n
        x, z = 9.2, 8.05
        for i, a in enumerate(angles):
            el = box(f"Flag{i}", (x, y0, z - 0.05), (x + L + 0.05, y1, z + 0.05), "flag", faces=("north", "south"),
                     rot=(0, a * YSIGN, 0), origin=(x, (y0 + y1) / 2, z))
            el["faces"]["north"]["uv"] = [16 - 16 * (i + 1) / n, 0, 16 - 16 * i / n, 16]
            el["faces"]["south"]["uv"] = [16 * i / n, 0, 16 * (i + 1) / n, 16]
            els.append(el)
            r = math.radians(a)
            x, z = x + L * math.cos(r), z - L * math.sin(r)
        for y in (y0 + 0.3, y1 - 0.8):   # the snap hooks on the halyard
            els.append(box(f"Snap{y}", (8.9, y, 7.75), (9.45, y + 0.5, 8.35), "r4k-alu"))
    return els


# ======================================================================== the football goal

GOAL_TOP = 30.0          # the stanchion's top (on the crossbar's back), in units from the lower block's floor
GOAL_Z0, GOAL_Z1 = 2.8, 14.9   # where the stanchion leaves the bar and where it meets the ground frame (at y 0.9)


def goal_line(Y, off=0.0):
    """z of the stanchion (plus off) at height Y (units from the lower block's floor)."""
    return GOAL_Z0 + off + (GOAL_TOP - Y) / (GOAL_TOP - 0.9) * (GOAL_Z1 - GOAL_Z0)


def side_net(half, face, seed):
    """The side net between the post, the ground bar and the stanchion, cut out to that triangle, for a full-block face
    (uv 0..16) on the plane's `face` side: east (u runs from z 16 to 0) or west (u runs from z 0 to 16)."""
    img = net_square(seed)
    px = img.load()
    for py in range(32):
        for pxx in range(32):
            u = (pxx + 0.5) / 2
            z = 16 - u if face == "east" else u
            Y = (16 if half == "upper" else 0) + 16 - (py + 0.5) / 2
            if not (GOAL_Z0 <= z <= goal_line(Y, -0.3) and 0.9 <= Y <= GOAL_TOP - 1.0):
                px[pxx, py] = (0, 0, 0, 0)
    return img


def goal(part, half):
    """A block of the goal (part l, m, r as seen from the pitch: the l post at x 15, the r post at x 1; half lower or
    upper): round posts and bar, the ground frame back to z 15, the stanchions from the bar's back down to it, the net."""
    gw, net = "r4k-goal", "r4k-gnet"
    els = []
    px = {"l": 15.0, "r": 1.0}.get(part)
    up = half == "upper"
    if px is not None:
        els += octo("Post", (px - 0.8, 0, 1.2), (px + 0.8, 14.8 if up else 16, 2.8), gw, faces=fs("up", "down"))
    if up:
        x0, x1 = {"l": (0, 15.8), "r": (0.2, 16), "m": (0, 16)}[part]
        els += octo("Bar", (x0, 13.2, 1.2), (x1, 14.8, 2.8), gw, axis="x", faces=fs(*(("east", "west") if part == "m" else
                                                                                   ("west",) if part == "l" else ("east",))))
        for k in range(2 if part == "m" else 1, 16, 4):     # net clips on the bar's back
            if x0 + 0.3 < k < x1 - 1:
                els.append(box(f"Clip{k}", (k, 13.5, 2.8), (k + 0.5, 14.5, 3.3), "r4k-white-plastic", faces=fs("north")))
    else:
        bx0, bx1 = {"l": (0, 15.5), "r": (0.5, 16), "m": (0, 16)}[part]
        els.append(box("BackBar", (bx0, 0, 14.4), (bx1, 0.9, 15.4), gw, faces=fs("down", *(("east", "west") if part == "m" else ()))))
        if px is not None:
            els.append(box("SideBar", (px - 0.5, 0, 2.8), (px + 0.5, 0.9, 14.4), gw, faces=fs("down", "north")))
            els.append(box("Corner", (px - 0.7, 0, 13.9), (px + 0.7, 1.2, 15.6), gw, faces=fs("down")))
        for k in ((4, 12) if part == "m" else (6,) if part == "l" else (10,)):   # ground pegs over the back bar
            els += [box(f"Peg{k}", (k, 0, 15.4), (k + 0.4, 1.3, 15.8), "r4k-galv-peg", faces=fs("down")),
                    box(f"PegHook{k}", (k - 0.2, 1.1, 15.0), (k + 0.6, 1.4, 15.8), "r4k-galv-peg")]
    base = 16 if up else 0
    if px is not None:   # the stanchion, its run through this block
        ya, yb = (14.2, 0) if up else (16, 0.9)
        els.append(bar("Stanchion", (px, ya, goal_line(ya + base)), (px, yb, goal_line(yb + base)), 0.8, gw))
        sn = box("SideNet", (px - 0.02, 0, 0), (px + 0.02, 16, 16), f"r4k-gnet-side-{half}-{'w' if part == 'l' else 'e'}",
                 faces=("west",) if part == "l" else ("east",))
        full_uv(sn)
        els.append(sn)
    # the back net, hung a little behind the stanchions' line
    nx0, nx1 = {"l": (0, 15), "r": (1, 16), "m": (0, 16)}[part]
    ya, yb = (14.4, 0) if up else (16, 0.4)
    els.append(bar("Net", (0, ya, goal_line(ya + base, 0.45)), (0, yb, goal_line(yb + base, 0.45)), 1, net, faces=("north",)))
    n = els[-1]
    n["from"][0], n["to"][0] = nx0, nx1
    n["rotationOrigin"][0] = (nx0 + nx1) / 2
    n["from"][2] += 0.475
    n["to"][2] -= 0.475
    n["faces"]["north"]["uv"] = [0, 0, nx1 - nx0, min(16, round(n["to"][1] - n["from"][1], 3))]
    if not up:   # the net's foot lying on the ground behind, pegged
        els.append(box("NetFoot", (nx0, 0.15, 14.0), (nx1, 0.2, 16), net, faces=("up",)))
    return els


# ======================================================================== boards on posts

BOARD_KINDS = ["map", "md", "barry", "turner", "sunfire", "ember", "blackcross"]   # as gen_52_r3.BOARD_KINDS
STEEL_BOARDS = ("map", "md", "barry", "turner")


def board(kind, part, half):
    """A block of a board two blocks wide and two high on two posts (part l: its left seen from in front, at +x; the
    seam between the halves at l's x 0 and r's x 16): the face at z 9..11 spanning the block (the upper half's stopping
    at y 15), a frame round it, a rain hood (upper), bolts, the back panel's rails and brace, the post with its cap and
    foot."""
    steel = kind in STEEL_BOARDS
    post = "post-steel" if steel else "post-wood"
    back = "r4k-bback-steel" if steel else "r4k-bback-wood"
    fr = "r4k-frame-steel" if steel else "r4k-frame-wood"
    up = half == "upper"
    outer, seam = ("east", "west") if part == "l" else ("west", "east")
    px0, px1 = (13, 15) if part == "l" else (1, 3)
    ox0, ox1 = (15.2, 16) if part == "l" else (0, 0.8)
    top = 15 if up else 16
    face = f"board-{kind}-{part}-{half}"
    b = box("Board", (0, 0, 9), (16, top, 11), {"north": face, "south": back, "side": post, "top": post},
            faces=("north", "south") + (("up",) if up else ()))
    full_uv(b, "north")
    els = [b, box("FrameO", (ox0, 0, 8.4), (ox1, top + 0.4 if up else 16, 11.3), fr, faces=fs(seam, *(() if up else ("up", "down"))))]
    if up:
        els += [box("FrameT", (0, 14.6, 8.4), (16, 15.4, 11.3), fr, faces=fs(seam, outer)),
                box("Hood", (0, 15.35, 7.4), (16, 15.85, 12.6), fr, faces=fs(seam), rot=(-XSIGN * 7, 0, 0), origin=(8, 15.6, 12.6)),
                box("HoodLip", (0, 14.9, 7.4), (16, 15.6, 7.9), fr, faces=fs(seam))]
        bolts = [(4, 15.0), (12, 15.0), ((15.6 if part == "l" else 0.4), 12.0)]
        rails = (4.0, 11.0)
    else:
        els.append(box("FrameB", (0, 0, 8.4), (16, 0.8, 11.3), fr, faces=fs(seam, outer, "down")))
        bolts = [(4, 0.4), (12, 0.4), ((15.6 if part == "l" else 0.4), 3.0), ((15.6 if part == "l" else 0.4), 13.0)]
        rails = (2.6, 11.4)
    for i, (bx, by) in enumerate(bolts):
        els.append(box(f"Bolt{i}", (bx - 0.25, by - 0.25, 8.1), (bx + 0.25, by + 0.25, 8.4), "r4k-bolt", faces=fs("south")))
    for i, y in enumerate(rails):
        els.append(box(f"Rail{i}", (0, y, 11.0), (16, y + 1.2, 11.8), fr, faces=fs(seam, "north")))
        els.append(box(f"Clamp{i}", (px0 - 0.3, y - 0.3, 13.0), (px1 + 0.3, y + 1.5, 13.4), "r4k-galv-peg", faces=fs("north")))
    if not up:   # a diagonal brace across the back, between the rails
        a, c = (2.0, 13.0) if part == "l" else (14.0, 3.0)
        els.append(zbar("Brace", (a, 3.8), (c, 11.4), 0.9, fr, 11.05, 11.65))
    # the post, its cap or its foot
    els.append(box("Post", (px0, 0, 11), (px1, 15.2 if up else 16, 13), post, faces=fs("up", "down") if not up else fs("down")))
    if up:
        els += [box("PostCap", (px0 - 0.25, 15.2, 10.75), (px1 + 0.25, 15.9, 13.25), fr, faces=fs("down") if steel else ALL)]
        if not steel:
            els.append(box("PostCapTop", (px0 + 0.2, 15.9, 11.2), (px1 - 0.2, 16.0, 12.8), fr, faces=fs("down")))
    else:
        cx = (px0 + px1) / 2
        if steel:
            els += [box("Footing", (cx - 2.4, 0, 9.6), (cx + 2.4, 0.5, 14.4), "r4k-plinth", faces=fs("down")),
                    box("BasePlate", (cx - 1.7, 0.5, 10.3), (cx + 1.7, 0.85, 13.7), "r4k-steel", faces=fs("down"))]
            for dx in (-1.5, 1.1):
                for dz in (11.2, 12.7):
                    els.append(box(f"Nut{dx}{dz}", (cx + dx, 0.85, dz), (cx + dx + 0.4, 1.25, dz + 0.4), "r4k-bolt",
                                   faces=fs("down")))
        else:
            els += [box("Collar", (cx - 1.9, 0, 10.0), (cx + 1.9, 1.2, 14.0), "r4k-plinth", faces=fs("down")),
                    box("CollarTop", (cx - 1.6, 1.2, 10.4), (cx + 1.6, 1.6, 13.6), "r4k-plinth", faces=fs("down"))]
    return els


def shapes():
    out = {}
    out.update(wall_fittings())
    for k in BOARD_KINDS:
        for p in "lr":
            for h in ("lower", "upper"):
                out[f"l52-post-{k}-{p}-{h}"] = board(k, p, h)
    for p in "lmr":
        for h in ("lower", "upper"):
            out[f"l52-goal-{p}-{h}"] = goal(p, h)
    for p in ("base", "pole", "top"):
        out[f"l52-flagpole-{p}"] = flagpole(p)
    out["l52-fumehood-lower"] = fumehood("lower")
    out["l52-fumehood-upper"] = fumehood("upper")
    out["l52-bleacher"] = bleacher()
    out["l52-stall-lower"] = stall("lower")
    out["l52-stall-upper"] = stall("upper")
    out.update(shapes2())
    out.update(shapes3())
    return out


# ======================================================================== batch 2 (2026-11-03): classroom, restroom, roof
#
#   l52-desk                      a student combo desk: tube frame on glides, laminate top with an edge band and a pencil
#                                 groove, an open book box, a moulded seat at 0.5 with its back on two posts, the runner
#   l52-chalkboard-{lower,upper}-{l,m,r}   a chalkboard 3 x 2 blocks: aluminium frame, slate (its own picture per piece),
#                                 chalk tray with chalk and an eraser (lower m), map rail with cork and clips, a map roller
#                                 case (upper m)
#   l52-fountain                  a wall-hung stainless drinking fountain with a bottle filler above
#   l52-window-{lower,upper}      a two-block window, its glass in the plane x = 8: sill, ledge, window board, jambs,
#                                 mullion, transom, head, beads, a latch on both faces
#   l52-lseat                     a lecture-theatre flip seat (new)
#   l52-projector                 a ceiling-mounted classroom projector, off (new)
#   l52-vent                      a galvanised mushroom vent on a curb (roof)
#
# textures() and shapes() above already include these; textures2(save) and shapes2() are the batch on its own.

def slate_board(seed):
    """The whole slate, 3 blocks wide (l, m, r from the left seen from in front) and 27 units high (the lower piece's
    y 2..16 and the upper's 0..13), at 4 px a unit: 192 x 108. Dark green, eraser swirls, ghosts of old work, chalk dust
    heavier toward the tray."""
    from PIL import ImageFont
    w, h = 192, 112
    img = M.noise_hv((44, 68, 56), 3, seed, (w, h), 4, (32, 16), hue=1.0)
    rng = random.Random(seed)
    ghost = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ghost)
    # eraser swirls: broad faint arcs
    for _ in range(26):
        cx, cy, r = rng.randrange(w), rng.randrange(h), rng.randint(6, 18)
        a0 = rng.randrange(360)
        d.arc((cx - r, cy - r * 0.6, cx + r, cy + r * 0.6), a0, a0 + rng.randint(90, 220), fill=(170, 186, 176, 26),
              width=rng.randint(3, 6))
    # ghosts of old work: lines of maths in faint chalk
    lines = ["x = 2y + 3", "3/4 + 1/8 = 7/8", "a2 + b2 = c2", "12 x 7 = 84", "y = mx + b", "2x - 5 = 11", "x = 8",
             "45 / 9 = 5", "0.25 = 1/4", "1 2 3 4 5"]
    font = ImageFont.load_default(size=9)
    for i in range(9):
        x, y = rng.randrange(4, w - 60), rng.randrange(4, h - 14)
        d.text((x, y), rng.choice(lines), fill=(196, 206, 198, rng.randint(18, 34)), font=font)
    for _ in range(5):   # hand scribble lines
        x, y = rng.randrange(w), rng.randrange(h)
        pts = [(x + k * 4, y + rng.randint(-2, 2)) for k in range(rng.randint(5, 12))]
        d.line(pts, fill=(200, 210, 200, 40), width=1)
    img.alpha_composite(ghost)
    px = img.load()
    for y in range(h):   # dust: heavier toward the bottom (the tray), wiped streaks up from it
        t = min(1.0, max(0.0, (y - 108 * 0.6) / (108 * 0.4)))
        for x in range(w):
            if rng.random() < 0.05 + 0.25 * t:
                px[x, y] = M.rgba(M.lift(px[x, y], rng.uniform(4, 10) + 14 * t))
    for _ in range(14):
        x = rng.randrange(w)
        for y in range(h - rng.randint(6, 22), h):
            px[x, y] = M.rgba(M.lift(px[x, y], 7))
    return img


def desk_top_tex(seed):
    """The desk top seen from above (full picture over the top; the picture's top is the north edge): a pale maple-look
    laminate, scuffs, a pen mark, a ring stain."""
    img = M.noise_hv((206, 180, 140), 2, seed, (64, 64), 4, (32, 16), hue=1.0)
    px = img.load()
    rng = random.Random(seed)
    for y in range(64):   # fine wood-print grain along x
        f = math.sin(y * 0.9 + rng.uniform(-0.2, 0.2)) * 3 + math.sin(y * 0.23) * 4
        for x in range(64):
            px[x, y] = M.rgba(M.lift(px[x, y], f))
    M.scratches(img, 10, seed + 1, (3, 9), 0.1)
    M.stain(img, seed + 2, radius=6, color=(150, 120, 86), strength=0.25, at=(44, 36))
    d = ImageDraw.Draw(img)
    d.line((14, 40, 26, 44), fill=(60, 70, 130, 255), width=1)   # a pen mark
    d.line((15, 45, 22, 47), fill=(60, 70, 130, 255), width=1)
    M.grime(img, amount=0.06, seed=seed + 3, cover=0.4)
    return img


def basin_top(seed):
    """The fountain bowl seen from above (full picture, top = north): the rolled rim, the dished bowl, the drain."""
    n = 64
    img = M.brushed_metal(seed, (n, n), base=(184, 188, 192), streak=6, sheen=12)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((5, 4, 58, 56), radius=14, fill=(160, 164, 168, 255))
    d.rounded_rectangle((8, 7, 55, 53), radius=12, fill=(146, 150, 154, 255))
    d.ellipse((16, 14, 48, 46), fill=(136, 140, 144, 255))
    d.ellipse((27, 25, 37, 35), fill=(96, 98, 100, 255))   # the drain
    for k in range(28, 37, 2):
        d.line((k, 26, k, 34), fill=(60, 62, 64, 255))
    d.arc((5, 4, 58, 56), 190, 350, fill=(222, 224, 226, 255), width=1)
    M.grime(img, amount=0.08, seed=seed + 1, color=(170, 160, 130), cover=0.4)   # a faint scale
    return img


def textures2(save):
    s = save
    # desk
    s(desk_top_tex(8200), "r4k-desktop")
    band = M.noise_hv((70, 56, 42), 2, 8201, (32, 32), 2, (16, 8))
    M.scratches(band, 4, 8202, (2, 5), 0.12)
    s(band, "r4k-edgeband")
    s(enamel(8203, (84, 80, 74), grime=0.08, chips=4), "r4k-tube")
    s(enamel(8204, (96, 88, 78), grime=0.1, chips=3), "r4k-bookbox")
    s(plastic(8205, (140, 104, 70), 3), "r4k-seatshell")
    s(plastic(8206, (230, 120, 150), 3), "r4k-gum")
    # chalkboard
    sb = slate_board(8210)
    for i, part in enumerate("lmr"):
        s(sb.crop((i * 64, 0, i * 64 + 64, 52)).resize((64, 64), Image.LANCZOS), f"r4k-slate-upper-{part}")
        s(sb.crop((i * 64, 52, i * 64 + 64, 108)).resize((64, 64), Image.LANCZOS), f"r4k-slate-lower-{part}")
    tray = satin(8211, (182, 186, 188))
    rng = random.Random(8212)
    for _ in range(140):
        tray.putpixel((rng.randrange(32), rng.randrange(32)), M.rgba((226, 226, 220)))
    s(tray, "r4k-tray")
    s(plastic(8213, (240, 238, 230), 2), "r4k-chalk-white")
    s(plastic(8214, (236, 210, 90), 2), "r4k-chalk-yellow")
    s(M.fabric(8215, base=(70, 70, 72), weave="plain", contrast=4), "r4k-felt")
    s(M.wood_planks(8216, base=(150, 108, 66), planks=1, grain=3), "r4k-woodback")
    s(enamel(8217, (214, 208, 190), grime=0.05, chips=1), "r4k-mapcase")
    # fountain
    s(basin_top(8220), "r4k-basintop")
    s(satin(8221, (178, 182, 186), direction="v"), "r4k-stainless")
    s(plastic(8222, (24, 26, 30), 1), "r4k-sensor")
    # window
    wf = M.noise_hv((232, 232, 226), 1, 8230, (32, 32), 2, (16, 8))
    M.grime(wf, amount=0.05, seed=8231, cover=0.35)
    s(wf, "r4k-wframe")
    wb = M.noise_hv((236, 232, 220), 2, 8232, (32, 32), 2, (16, 8))
    M.scratches(wb, 3, 8233, (2, 5), -0.08)
    M.grime(wb, amount=0.07, seed=8234, cover=0.4)
    s(wb, "r4k-wboard")
    # lecture seat
    s(M.fabric(8240, base=(78, 90, 112), weave="twill", contrast=8), "r4k-upholstery")
    s(plastic(8241, (52, 52, 56), 2), "r4k-shell")
    s(enamel(8242, (66, 68, 72), grime=0.1, chips=4), "r4k-standard")
    s(M.wood_planks(8243, base=(156, 116, 74), planks=1, grain=3), "r4k-armwood")
    s(laminate(8244, (214, 206, 186)), "r4k-tablet")
    rowp = M.noise_hv((176, 150, 96), 3, 8245, (32, 32), 3, (16, 8))
    from PIL import ImageFont
    ImageDraw.Draw(rowp).text((16, 16), "14", fill=(60, 44, 24, 255), anchor="mm", font=ImageFont.load_default(size=16))
    M.ao_border(rowp, 2, 0.2)
    s(rowp, "r4k-rowplate")
    # projector
    pj = M.noise_hv((206, 206, 200), 2, 8250, (32, 32), 2, (16, 8))
    M.scratches(pj, 2, 8251, (2, 4), -0.06)
    M.grime(pj, amount=0.06, seed=8252, cover=0.35)
    s(pj, "r4k-projector")
    lens = M.noise_hv((30, 36, 48), 2, 8253, (32, 32), 2, (16, 8))
    for k in range(6, 12):
        M.touch(lens, k, k - 2, 0.5)
    s(lens, "r4k-lensglass")
    s(plastic(8254, (60, 84, 150), 2), "r4k-vga")
    s(plastic(8255, (28, 28, 30), 1), "r4k-cable")
    s(plastic(8256, (70, 54, 30), 1), "r4k-led-off")
    s(enamel(8257, (230, 228, 222), grime=0.04, chips=0), "r4k-ceilplate")
    # roof vent
    gv = M.galvanised(8260, base=(158, 162, 162), white_rust=0.2)
    M.grime(gv, amount=0.12, seed=8261, cover=0.45)
    M.drips(gv, n=3, seed=8262, color=(110, 100, 86), length=(5, 12), strength=0.25)
    s(gv, "r4k-galv-roof")


# ---------------------------------------------------------------------- desk

def desk():
    """The student combo desk (the student faces north): the desk top in the north half at 0.76 block, the seat in the
    south half at 0.5, joined by the runner along the floor."""
    tube, lam, band, box_ = "r4k-tube", "r4k-desktop", "r4k-edgeband", "r4k-bookbox"
    seat = "r4k-seatshell"
    nd = fs("down")
    top = box("Top", (1.5, 11.4, 2.2), (14.5, 12.2, 8.6), {"top": lam, "side": band, "bottom": box_})
    full_uv(top, "up")
    top["faces"]["up"]["uv"] = [0, 4, 16, 16]
    els = [top,
           box("TopFar", (1.5, 11.4, 0.8), (14.5, 12.2, 1.4), {"top": lam, "side": band, "bottom": box_}),
           box("Groove", (1.5, 11.4, 1.4), (14.5, 11.9, 2.2), {"top": band, "side": band, "bottom": box_}, faces=fs("north", "south"))]
    els[1]["faces"]["up"]["uv"] = [0, 0, 16, 1.2]
    # the open book box under the top, open toward the student
    els += [box("BoxFloor", (2.2, 9.4, 1.4), (13.8, 9.7, 7.8), box_),
            box("BoxL", (2.2, 9.7, 1.4), (2.5, 11.4, 7.8), box_, faces=fs("up")),
            box("BoxR", (13.5, 9.7, 1.4), (13.8, 11.4, 7.8), box_, faces=fs("up")),
            box("BoxFront", (2.5, 9.7, 1.4), (13.5, 11.4, 1.7), box_, faces=fs("up")),
            box("Gum", (10.2, 9.1, 5.0), (10.9, 9.4, 5.7), "r4k-gum", faces=fs("up"))]
    # the frame: front legs up to the book box, a foot bar across with glides, the runner back to the seat's foot bar
    for x in (2.7, 12.5):
        els += [box(f"Leg{x}", (x, 0.8, 3.6), (x + 0.8, 9.4, 4.4), tube, faces=fs("down")),
                box(f"Glide{x}", (x - 0.1, 0, 3.2), (x + 0.9, 0.3, 4.8), "r4k-black", faces=fs("down")),
                box(f"Brace{x}", (x, 8.6, 4.4), (x + 0.8, 9.4, 7.4), tube, faces=fs("up"))]
    els += [box("FootF", (2.7, 0.3, 3.6), (13.3, 1.0, 4.4), tube, faces=fs("east", "west")),
            box("Runner", (7.4, 0.3, 4.4), (8.6, 1.0, 13.4), tube, faces=fs("down")),
            box("FootB", (4.2, 0.3, 13.4), (11.8, 1.0, 14.2), tube, faces=fs()),
            box("Post", (7.5, 1.0, 11.5), (8.5, 6.6, 12.5), tube, faces=fs("down", "up"))]
    for x in (4.2, 11.0):
        els.append(box(f"GlideB{x}", (x - 0.1, 0, 13.2), (x + 0.9, 0.3, 14.4), "r4k-black", faces=fs("down")))
    # the moulded seat (rounded front, raised back edge), its bracket, the back on two posts
    els += [box("SeatBracket", (5.0, 6.6, 10.2), (11.0, 7.1, 13.8), tube, faces=fs("up")),
            box("Seat", (3.6, 7.2, 9.6), (12.4, 7.9, 14.2), seat, faces=nd),
            box("SeatUnder", (4.0, 7.1, 9.8), (12.0, 7.21, 14.0), seat, faces=("down",)),
            box("SeatNose", (4.3, 7.0, 9.1), (11.7, 7.8, 9.6), seat, faces=nd),
            box("SeatRoll", (3.6, 7.9, 13.4), (12.4, 8.3, 14.2), seat, faces=fs("down")),
            box("SeatSideL", (3.6, 7.9, 10.4), (4.2, 8.15, 13.4), seat, faces=fs("down", "south")),
            box("SeatSideR", (11.8, 7.9, 10.4), (12.4, 8.15, 13.4), seat, faces=fs("down", "south"))]
    for x in (4.8, 10.6):
        els.append(box(f"BackPost{x}", (x, 6.6, 14.2), (x + 0.6, 11.2, 14.8), tube))
    els += [box("Back", (3.9, 10.2, 14.8), (12.1, 14.4, 15.5), seat, rot=(XSIGN * 6, 0, 0), origin=(8, 10.2, 14.8)),
            box("BackTop", (4.5, 14.3, 14.85), (11.5, 14.8, 15.45), seat, rot=(XSIGN * 6, 0, 0), origin=(8, 10.2, 14.8)),
            box("BackLow", (4.5, 9.8, 14.85), (11.5, 10.3, 15.45), seat, rot=(XSIGN * 6, 0, 0), origin=(8, 10.2, 14.8))]
    return els


# ---------------------------------------------------------------------- chalkboard

def chalkboard(part, end):
    """A piece of a chalkboard 3 blocks wide and 2 high on the wall to the south (l: its left seen from in front, at +x,
    with the end frame at x 14.8..16; r: the end frame at x 0..1.2): the slate, the aluminium frame proud of it, the
    chalk tray (lower), the map rail (upper), the eraser and chalk (lower m), the map roller case (upper m)."""
    alu = "r4k-alu"
    seam = {"l": ("west",), "m": ("east", "west"), "r": ("east",)}[end]
    lo = part == "lower"
    y0, y1 = (2.0, 16) if lo else (0, 13.0)
    sl = box("Slate", (0, y0, 15.0), (16, y1, 16), f"r4k-slate-{part}-{end}", faces=("north",))
    ix0, ix1 = {"l": (0, 14.8), "m": (0, 16), "r": (1.2, 16)}[end]   # inside the end frame
    full_uv(sl)
    els = [sl]
    if lo:
        els += [box("FrameB", (0, 1.0, 14.3), (16, 2.0, 16), alu, faces=fs("south", *seam)),
                box("LipB", (0, 2.0, 14.7), (16, 2.3, 15.0), alu, faces=("north", "up")),
                box("Tray", (ix0, 0.5, 12.0), (ix1, 1.0, 14.3), "r4k-tray", faces=fs(*seam)),
                box("TrayLip", (ix0, 1.0, 12.0), (ix1, 1.6, 12.4), alu, faces=fs("down", *seam)),
                box("TrayBack", (ix0, 1.0, 14.0), (ix1, 1.2, 14.3), alu, faces=("up",))]
        fy0, fy1 = 1.0, 16
    else:
        els += [box("FrameT", (0, 13.0, 14.3), (16, 14.0, 16), alu, faces=fs("south", *seam)),
                box("LipT", (0, 12.7, 14.7), (16, 13.0, 15.0), alu, faces=("north", "down")),
                box("Rail", (ix0, 14.0, 14.4), (ix1, 15.6, 16), alu, faces=fs("south", *seam)),
                box("Cork", (ix0, 14.3, 14.3), (ix1, 15.3, 14.4), "r4k-cork", faces=("north",))]
        fy0, fy1 = 0, 14.0
    if end in ("l", "r"):
        x0, x1 = (14.8, 16) if end == "l" else (0, 1.2)
        lx0, lx1 = (14.5, 14.8) if end == "l" else (1.2, 1.5)
        els += [box("FrameE", (x0, fy0, 14.3), (x1, fy1 if lo else 15.6, 16), alu, faces=fs("south", *(("up",) if lo else ()))),
                box("LipE", (lx0, y0 if lo else 0, 14.7), (lx1, y1, 15.0), alu, faces=("north", "west" if end == "l" else "east"))]
        if lo:
            els.append(box("TrayEnd", (x0, 0.5, 12.0), (x1, 1.8, 14.3), alu, faces=fs("south")))
    if lo and end == "m":
        els += [box("Felt", (9.6, 1.0, 12.5), (12.4, 1.5, 13.8), "r4k-felt", faces=fs("down")),
                box("EraserBack", (9.7, 1.5, 12.6), (12.3, 2.2, 13.7), "r4k-woodback", faces=fs("down")),
                box("Chalk1", (4.0, 1.0, 12.6), (6.6, 1.6, 13.2), "r4k-chalk-white", faces=fs("down"), rot=(0, YSIGN * 8, 0)),
                box("Chalk2", (7.0, 1.0, 13.2), (8.4, 1.5, 13.7), "r4k-chalk-white", faces=fs("down")),
                box("Chalk3", (5.0, 1.0, 13.4), (6.8, 1.5, 13.9), "r4k-chalk-yellow", faces=fs("down"), rot=(0, -YSIGN * 5, 0))]
    if lo and end == "l":
        els.append(box("Chalk4", (2.0, 1.0, 12.8), (3.0, 1.5, 13.3), "r4k-chalk-white", faces=fs("down")))
    if not lo:
        for i, x in enumerate((4.0, 11.4) if end == "m" else ((5.0,) if end == "l" else (10.4,))):
            els += [box(f"Clip{i}", (x, 14.1, 14.0), (x + 0.6, 15.5, 14.3), alu, faces=fs("south")),
                    box(f"ClipHook{i}", (x + 0.1, 13.2, 13.9), (x + 0.5, 14.1, 14.3), alu, faces=fs("south"))]
    if not lo and end == "m":   # the pull-down map roller case on the rail, its pull tab
        case = "r4k-mapcase"
        els += [box("Case", (1.0, 13.8, 12.6), (15.0, 15.6, 14.3), case, faces=fs("south")),
                box("CaseLo", (1.0, 13.4, 12.9), (15.0, 13.8, 14.0), case, faces=fs("south", "up")),
                box("CaseHi", (1.0, 15.6, 12.9), (15.0, 15.9, 14.0), case, faces=fs("south", "down")),
                box("CapL", (14.6, 13.3, 12.5), (15.4, 16.0, 14.3), "r4k-black", faces=fs("south")),
                box("CapR", (0.6, 13.3, 12.5), (1.4, 16.0, 14.3), "r4k-black", faces=fs("south")),
                box("MapEdge", (1.6, 12.9, 13.2), (14.4, 13.4, 13.5), "r4k-woodback"),
                box("Tab", (7.7, 12.0, 13.25), (8.3, 12.9, 13.45), "r4k-black"),
                box("Ring", (7.5, 11.4, 13.25), (8.5, 12.0, 13.45), "r4k-alu")]
    return els


# ---------------------------------------------------------------------- drinking fountain

def fountain():
    """A wall-hung stainless drinking fountain, facing north, its back splash against the wall at z 16: the bowl at
    0.75 block with a rounded front (stepped courses), the bubbler and its guard, a push bar across the front, the
    tailpiece and trap into the wall under it, the supply stop, and a bottle filler above."""
    st, ch, ss = "r4k-stainless", "r4k-chrome", "r4k-satin"
    nd = fs("down")
    els = [box("Splash", (3.4, 7.4, 15.4), (12.6, 13.6, 16), st, faces=fs("south"))]
    cx = 8.0

    def course(name, y0, y1, hw, z0, nose_hw, nose_z, tex=st, faces=fs("south")):
        els.append(box(name, (cx - hw, y0, z0), (cx + hw, y1, 15.4), tex, faces=faces))
        els.append(box(name + "N", (cx - nose_hw, y0 + 0.01, nose_z), (cx + nose_hw, y1 - 0.01, z0), tex, faces=faces))

    course("Shell1", 8.4, 9.6, 2.6, 11.0, 1.6, 10.2)
    course("Shell2", 9.6, 10.8, 3.4, 9.2, 2.4, 8.4)
    course("Shell3", 10.8, 11.6, 3.9, 8.0, 3.0, 7.2)
    rim = box("Rim", (cx - 4.1, 11.6, 7.4), (cx + 4.1, 12.2, 15.4), {"top": "r4k-basintop", "side": st}, faces=fs("south"))
    full_uv(rim, "up")
    els += [rim, box("RimN", (cx - 3.0, 11.61, 6.8), (cx + 3.0, 12.19, 7.4), st, faces=fs("south"))]
    els.append(box("Bottom", (cx - 2.0, 8.0, 12.0), (cx + 2.0, 8.4, 15.4), st, faces=fs("south")))
    # the bubbler, its guard
    els += octo("Bubbler", (cx - 0.5, 12.2, 12.6), (cx + 0.5, 13.0, 13.6), ch)
    els += [box("BubblerHead", (cx - 0.45, 13.0, 11.8), (cx + 0.45, 13.6, 13.6), ch),
            box("Nozzle", (cx - 0.25, 13.1, 11.5), (cx + 0.25, 13.5, 11.8), "r4k-black", faces=fs("south")),
            box("GuardF", (cx - 1.4, 13.9, 11.0), (cx + 1.4, 14.3, 11.4), ch),
            box("GuardL", (cx - 1.4, 12.2, 11.0), (cx - 1.0, 13.9, 11.4), ch, faces=fs("up")),
            box("GuardR", (cx + 1.0, 12.2, 11.0), (cx + 1.4, 13.9, 11.4), ch, faces=fs("up")),
            box("GuardBL", (cx - 1.4, 13.9, 11.4), (cx - 1.0, 14.3, 13.2), ch, faces=fs("north")),
            box("GuardBR", (cx + 1.0, 13.9, 11.4), (cx + 1.4, 14.3, 13.2), ch, faces=fs("north"))]
    # the push bar across the front, on two arms
    els += [box("PushBar", (cx - 3.2, 10.0, 6.4), (cx + 3.2, 10.9, 6.9), ss),
            box("PushArmL", (cx - 3.0, 10.1, 6.9), (cx - 2.5, 10.8, 8.6), ss, faces=fs("north", "south")),
            box("PushArmR", (cx + 2.5, 10.1, 6.9), (cx + 3.0, 10.8, 8.6), ss, faces=fs("north", "south"))]
    # under: the tailpiece, the trap's bend into the wall with its flange, the supply and its stop
    els += octo("Tail", (cx - 0.5, 5.6, 12.6), (cx + 0.5, 8.0, 13.6), ch, faces=fs("up"))
    els += octo("TrapBend", (cx - 0.55, 4.8, 12.5), (cx + 0.55, 5.8, 13.7), ch)
    els += octo("TrapArm", (cx - 0.5, 4.85, 13.7), (cx + 0.5, 5.75, 15.7), ch, axis="z", faces=fs("south"))
    els += [box("TrapFlange", (cx - 1.0, 4.3, 15.7), (cx + 1.0, 6.3, 16), ch, faces=fs("south"))]
    els += octo("Supply", (10.3, 6.0, 14.2), (10.9, 8.4, 14.8), ch, faces=fs("up"))
    els += [box("Stop", (10.0, 6.0, 13.9), (11.2, 7.0, 15.1), ch),
            box("StopKey", (10.4, 6.2, 13.4), (10.8, 6.8, 13.9), ch, faces=fs("south")),
            box("StopIn", (10.3, 6.2, 15.1), (10.9, 6.8, 16), ch, faces=fs("south", "north"))]
    # the bottle filler above: a housing on the wall, its spout and sensor
    els += [box("FillerBody", (5.0, 13.6, 14.4), (11.0, 16.0, 16), st, faces=fs("south", "up")),
            box("FillerFace", (5.4, 14.0, 14.3), (10.6, 15.6, 14.4), ss, faces=("north",)),
            box("FillerSpout", (cx - 0.5, 14.6, 12.8), (cx + 0.5, 15.2, 14.3), ch, faces=fs("south")),
            box("FillerTip", (cx - 0.4, 14.2, 12.8), (cx + 0.4, 14.6, 13.6), ch, faces=fs("south", "up")),
            box("Sensor", (9.2, 15.0, 14.2), (9.8, 15.4, 14.3), "r4k-sensor", faces=("north",))]
    return els


# ---------------------------------------------------------------------- window

def window(part):
    """A window two blocks high, its glass in the plane x = 8 (axis ns), white aluminium round it: jambs at the block's
    north and south edges, a slim mullion at z 8, beads on both faces round each pane; lower: the sill frame, an outside
    drip ledge (+x) and an inside window board (-x); upper: a transom about a third up and the head. A latch on the
    mullion on both faces. The glass keeps its two faces only."""
    f, g, b = "r4k-wframe", "window-glass", "r4k-wframe"
    lo = part == "lower"
    els = []
    if lo:
        els += [box("Sill", (6.6, 1.2, 0), (9.4, 2.6, 16), f, faces=fs("north", "south", "down")),
                box("Ledge", (9.4, 0.9, 0), (11.6, 1.5, 16), f, faces=fs("north", "south")),
                box("Drip", (11.2, 0.3, 0), (11.6, 0.9, 16), f, faces=fs("north", "south", "up")),
                box("Board", (3.6, 1.6, 0), (6.6, 2.3, 16), "r4k-wboard", faces=fs("north", "south")),
                box("BoardNose", (3.3, 1.5, 0), (3.6, 2.35, 16), "r4k-wboard", faces=fs("north", "south")),
                box("BoardApron", (4.6, 0.6, 0), (6.6, 1.6, 16), "r4k-wboard", faces=fs("north", "south", "up"))]
        spans = [(2.6, 16)]
        ya, yb = 2.6, 16
    else:
        els += [box("Head", (6.6, 13.6, 0), (9.4, 16, 16), f, faces=fs("north", "south", "up")),
                box("Transom", (6.9, 4.6, 1.4), (9.1, 5.8, 14.6), f, faces=fs("north", "south"))]
        spans = [(0, 4.6), (5.8, 13.6)]
        ya, yb = 0, 13.6
    els += [box("JambN", (6.6, ya, 0), (9.4, yb, 1.4), f, faces=fs("up", "down")),
            box("JambS", (6.6, ya, 14.6), (9.4, yb, 16), f, faces=fs("up", "down")),
            box("Mullion", (7.1, ya, 7.5), (8.9, yb, 8.5), f, faces=fs("up", "down"))]
    for i, (s0, s1) in enumerate(spans):
        gl = box(f"Glass{i}", (7.95, s0, 1.4), (8.05, s1, 14.6), g, faces=("east", "west"))
        full_uv(gl)
        els.append(gl)
        for side, (x0, x1) in (("E", (8.05, 8.45)), ("W", (7.55, 7.95))):
            fc = fs("up", "down")
            # beads along the jambs and the mullion, and along the sill / transom / head
            els += [box(f"BeadN{side}{i}", (x0, s0, 1.4), (x1, s1, 1.8), b, faces=("south", "east" if side == "E" else "west")),
                    box(f"BeadS{side}{i}", (x0, s0, 14.2), (x1, s1, 14.6), b, faces=("north", "east" if side == "E" else "west")),
                    box(f"BeadM{side}{i}", (x0, s0, 7.1), (x1, s1, 8.9), b, faces=("north", "south", "east" if side == "E" else "west"))]
            if s0 > 0:
                els.append(box(f"BeadB{side}{i}", (x0, s0, 1.8), (x1, s0 + 0.4, 14.2), b, faces=("up", "east" if side == "E" else "west")))
            if s1 < 16:
                els.append(box(f"BeadT{side}{i}", (x0, s1 - 0.4, 1.8), (x1, s1, 14.2), b, faces=("down", "east" if side == "E" else "west")))
    if lo:   # the latch on the mullion, both faces
        for sgn, x in ((1, 8.9), (-1, 7.1)):
            xa, xb = (x, x + 0.4) if sgn > 0 else (x - 0.4, x)
            la, lb = (x + 0.4, x + 0.9) if sgn > 0 else (x - 0.9, x - 0.4)
            els += [box(f"LatchBase{sgn}", (xa, 10.6, 7.6), (xb, 12.8, 8.4), "r4k-chrome",
                        faces=fs("west" if sgn > 0 else "east")),
                    box(f"LatchLever{sgn}", (la, 11.5, 7.8), (lb, 12.0, 10.2), "r4k-chrome")]
    return els


# ---------------------------------------------------------------------- lecture-theatre seat

def lseat():
    """A lecture-theatre flip seat facing north: steel standards at x 0..1 and 15..16 bolted to the floor (shared look
    in a row), wooden arm rests on them, the upholstered seat folded down at 0.5 block, a padded back on a shell, the
    writing tablet stowed down beside the right arm (+x, the sitter's right), the row plate on the standards' outer
    faces (hidden between neighbours)."""
    up, sh, sd, arm = "r4k-upholstery", "r4k-shell", "r4k-standard", "r4k-armwood"
    els = []
    for k, (x0, x1) in enumerate(((0, 1.0), (15.0, 16))):
        out_face = "west" if k == 0 else "east"
        els += [box(f"Standard{k}", (x0, 0.4, 4.6), (x1, 10.2, 12.0), sd, faces=fs("down")),
                box(f"StdFoot{k}", (x0, 0, 3.6), (x1, 0.4, 13.0), sd, faces=fs("down")),
                box(f"StdNose{k}", (x0 + 0.15, 1.0, 4.2), (x1 - 0.15, 9.8, 4.6), sd, faces=fs("down", "south")),
                box(f"Arm{k}", (x0 - (0.3 if k == 1 else 0), 10.2, 4.0), (x1 + (0.3 if k == 0 else 0), 11.0, 12.6), arm,
                    faces=fs(out_face)),
                box(f"ArmNose{k}", (x0 + 0.1, 10.3, 3.6), (x1 - 0.1, 10.9, 4.0), arm, faces=fs(out_face, "south"))]
        for z in (4.2, 12.2):
            els.append(box(f"Bolt{k}{z}", (x0 + 0.25, 0.4, z), (x0 + 0.75, 0.75, z + 0.5), "r4k-bolt", faces=fs("down")))
        pl = box(f"RowPlate{k}", (-0.1 if k == 0 else 16, 7.0, 5.2), (0 if k == 0 else 16.1, 8.6, 7.4), "r4k-rowplate",
                 faces=(out_face,))
        full_uv(pl)
        els.append(pl)
    # the seat: its pan (shell) under the cushion, the cushion with a rolled front, the pivot brackets
    els += [box("SeatPan", (1.7, 5.8, 4.2), (13.7, 6.6, 11.6), sh, faces=fs("up")),
            box("Cushion", (1.6, 6.6, 3.8), (13.8, 7.8, 11.4), up, faces=fs("down")),
            box("CushionRoll", (1.8, 6.3, 3.3), (13.6, 7.6, 3.8), up, faces=fs("south")),
            box("PivotL", (1.0, 5.6, 9.6), (1.6, 7.2, 11.6), sd),
            box("PivotR", (13.8, 5.6, 10.8), (15.0, 7.2, 11.6), sd)]
    # the back: the padded front and its shell, tilted back
    rot, org = (XSIGN * 10, 0, 0), (8, 7.8, 12.4)
    els += [box("BackPad", (1.7, 8.0, 11.8), (14.3, 15.2, 12.8), up, faces=fs(), rot=rot, origin=org),
            box("BackPadTop", (2.1, 15.2, 11.9), (13.9, 15.6, 12.7), up, faces=fs("down"), rot=rot, origin=org),
            box("BackShell", (1.4, 7.6, 12.8), (14.6, 15.8, 13.6), sh, faces=fs("north"), rot=rot, origin=org),
            box("BackMountL", (1.0, 7.0, 12.0), (1.6, 10.4, 13.2), sd),
            box("BackMountR", (14.4, 7.0, 12.0), (15.0, 10.4, 13.2), sd)]
    # the writing tablet stowed down beside the right arm, its hinge bracket
    els += [box("Tablet", (14.0, 4.0, 4.6), (14.6, 9.8, 10.6), {"side": "r4k-tablet", "top": "r4k-edgeband",
                                                                 "front": "r4k-edgeband", "back": "r4k-edgeband",
                                                                 "bottom": "r4k-edgeband"}),
            box("TabletHinge", (14.6, 8.8, 9.4), (15.0, 10.2, 10.4), sd)]
    return els


# ---------------------------------------------------------------------- projector

def projector():
    """A 2000s classroom projector hung from the ceiling (the block's top face): a ceiling plate, a drop pole with its
    collar, the cradle and its four arms, the light grey body upside down (vents, the lens at the north end with its cap
    off and dangling, a dark status LED; it is off), a VGA cable plugged in at the back looping down and up the pole."""
    pj, blk = "r4k-projector", "r4k-black"
    els = [box("CeilPlate", (5.4, 15.5, 5.4), (10.6, 16, 10.6), "r4k-ceilplate", faces=fs("up"))]
    for x in (5.8, 9.8):
        for z in (5.8, 9.8):
            els.append(box(f"Screw{x}{z}", (x, 15.3, z), (x + 0.4, 15.5, z + 0.4), "r4k-satin", faces=fs("up")))
    els += octo("Pole", (7.45, 11.0, 7.45), (8.55, 15.5, 8.55), blk, faces=fs("up", "down"))
    els += octo("Collar", (7.2, 13.0, 7.2), (8.8, 13.8, 8.8), "r4k-satin")
    els += [box("Spider", (5.2, 10.4, 4.4), (10.8, 11.0, 11.6), blk),
            box("Hub", (6.8, 11.0, 6.8), (9.2, 11.6, 9.2), blk, faces=fs("down"))]
    for x in (4.6, 10.9):
        for z in (4.6, 10.9):
            els.append(box(f"ArmP{x}{z}", (x, 9.4, z), (x + 0.5, 10.4, z + 0.5), blk, faces=fs("up")))
    # the body: a main block with stepped (rounded) edges, upside down so its control panel faces the room below
    els += [box("Body", (4.4, 7.2, 3.4), (11.6, 9.4, 11.6), pj, faces=fs("up")),
            box("BodyX", (4.2, 7.4, 3.6), (11.8, 9.2, 11.4), pj, faces=("east", "west")),
            box("BodyZ", (4.6, 7.4, 3.2), (11.4, 9.2, 11.8), pj, faces=("north", "south")),
            box("BodyLow", (4.6, 7.0, 3.6), (11.4, 7.2, 11.4), pj, faces=("down", "north", "south", "east", "west")),
            box("Top", (4.8, 9.4, 3.8), (11.2, 9.6, 11.2), pj, faces=fs("down"))]
    # vents on both sides and on the front by the lens, a control panel underneath
    els += [box("VentE", (11.8, 7.6, 5.0), (11.9, 9.0, 9.6), "r4k-vent", faces=("east",)),
            box("VentW", (4.1, 7.6, 5.0), (4.2, 9.0, 9.6), "r4k-vent", faces=("west",)),
            box("VentF", (8.8, 7.6, 3.1), (11.0, 9.0, 3.2), "r4k-vent", faces=("north",)),
            box("Panel", (6.0, 6.9, 7.4), (10.0, 7.0, 10.4), "r4k-shell", faces=("down", "north", "south", "east", "west"))]
    for i, x in enumerate((6.4, 7.4, 8.4, 9.2)):
        els.append(box(f"Button{i}", (x, 6.75, 8.4), (x + 0.5, 6.9, 8.9), "r4k-white-plastic", faces=fs("up")))
    els.append(box("Led", (9.4, 6.75, 9.6), (9.8, 6.9, 10.0), "r4k-led-off", faces=fs("up")))
    # the lens: barrel, focus ring, the glass; the cap off, hanging on its cord
    els += octo("Barrel", (5.0, 7.2, 2.2), (7.8, 9.4, 3.3), blk, axis="z", faces=fs("south"))
    els += octo("Focus", (4.9, 7.1, 2.6), (7.9, 9.5, 2.9), "r4k-shell", axis="z", faces=fs("south"))
    els += [box("LensGlass", (5.5, 7.7, 2.1), (7.3, 8.9, 2.2), "r4k-lensglass", faces=("north",)),
            box("CapCord", (6.3, 5.6, 2.4), (6.5, 7.2, 2.6), blk),
            box("Cap", (5.5, 4.2, 2.3), (7.3, 5.6, 2.7), blk),
            box("CapRim", (5.7, 4.0, 2.25), (7.1, 5.8, 2.75), blk)]
    # the VGA cable: the plug at the back, down, a loop, up to the cradle, then up beside the pole
    cab = "r4k-cable"
    els += [box("Plug", (6.2, 7.8, 11.8), (7.8, 8.6, 12.6), "r4k-vga"),
            box("CableDown", (6.8, 4.4, 12.4), (7.2, 7.8, 12.8), cab, faces=fs("up")),
            box("CableLoop", (6.8, 4.0, 12.4), (10.0, 4.4, 12.8), cab),
            box("CableUp", (9.6, 4.4, 12.4), (10.0, 10.4, 12.8), cab, faces=fs("down")),
            box("CableOverZ", (9.6, 10.0, 9.0), (10.0, 10.4, 12.8), cab),
            box("CableOverX", (8.6, 10.0, 8.6), (10.0, 10.4, 9.0), cab),
            box("CablePole", (8.6, 10.4, 8.6), (9.0, 15.5, 9.0), cab, faces=fs("down", "up"))]
    return els


# ---------------------------------------------------------------------- roof vent

def roof_vent():
    """A galvanised mushroom vent about 0.8 block high: a flange and a flashed curb, the stem with its seam bands, a
    dark gap with braces under the cap, the cap in stepped courses."""
    gv = "r4k-galv-roof"
    els = [box("Flange", (2.4, 0, 2.4), (13.6, 0.4, 13.6), gv, faces=fs("down")),
           box("Curb", (3.6, 0.4, 3.6), (12.4, 3.0, 12.4), gv, faces=fs("down")),
           box("CurbLip", (3.3, 3.0, 3.3), (12.7, 3.4, 12.7), gv, faces=fs()),
           box("CurbTop", (4.4, 3.4, 4.4), (11.6, 3.8, 11.6), gv, faces=fs("down"))]
    for x in (2.9, 12.7):
        for z in (2.9, 12.7):
            els.append(box(f"Rivet{x}{z}", (x, 0.4, z), (x + 0.4, 0.65, z + 0.4), "r4k-bolt", faces=fs("down")))
    els += octo("Stem", (5.6, 3.8, 5.6), (10.4, 9.0, 10.4), gv, faces=fs("down", "up"))
    els += octo("Band1", (5.45, 5.4, 5.45), (10.55, 5.8, 10.55), gv, faces=fs("down", "up"))
    els += octo("Band2", (5.45, 7.6, 5.45), (10.55, 8.0, 10.55), gv, faces=fs("down", "up"))
    els += octo("Gap", (5.9, 9.0, 5.9), (10.1, 9.8, 10.1), "r4k-black", faces=fs("down", "up"))
    for i, (x0, z0, x1, z1) in enumerate(((7.7, 4.6, 8.3, 5.9), (7.7, 10.1, 8.3, 11.4), (4.6, 7.7, 5.9, 8.3), (10.1, 7.7, 11.4, 8.3))):
        els.append(box(f"Strap{i}", (x0, 8.4, z0), (x1, 10.0, z1), gv, faces=fs("up")))
    els += octo("Skirt", (3.2, 9.8, 3.2), (12.8, 10.6, 12.8), gv)
    els += octo("Dome", (3.9, 10.6, 3.9), (12.1, 11.6, 12.1), gv, faces=fs("down"))
    els += octo("Crown", (5.2, 11.6, 5.2), (10.8, 12.4, 10.8), gv, faces=fs("down"))
    els += octo("Button", (7.0, 12.4, 7.0), (9.0, 12.8, 9.0), gv, faces=fs("down"))
    return els


def shapes2():
    out = {"l52-desk": desk(), "l52-fountain": fountain(), "l52-lseat": lseat(), "l52-projector": projector(),
           "l52-vent": roof_vent()}
    for part in ("lower", "upper"):
        out[f"l52-window-{part}"] = window(part)
        for end in "lmr":
            out[f"l52-chalkboard-{part}-{end}"] = chalkboard(part, end)
    return out


# ======================================================================== batch 3 (2026-11-03): new set pieces
#
#   l52-trophy-{lower,upper}          a trophy case (laminate base, glass case in an aluminium frame, glass shelves, cups,
#                                     figures, a shield, a ball, medals, a lit header); Transparent pass
#   l52-dugout-{l,m,r}-{lower,upper}  a pitch-side dugout 3 x 2 x 1, open to the north
#   l52-column-{base,shaft,cap}       a round canopy column, 3 blocks
#   l52-ladder-{lower,upper}          a library rolling ladder leaning on the stack to the south
#   l52-planter                       a concrete planter with a clipped shrub
#
# textures() and shapes() above include these; textures3(save) and shapes3() are the batch on its own.

def xslab(name, x0, x1, p0, p1, d, tex, faces=ALL):
    """A slab spanning x0..x1 whose middle runs from p0 to p1 ((y, z) points), d thick: a box along y turned about X."""
    el = bar(name, ((x0 + x1) / 2, p0[0], p0[1]), ((x0 + x1) / 2, p1[0], p1[1]), 1.0, tex, faces=faces, d=d)
    el["from"][0], el["to"][0] = x0, x1
    L = el["to"][1] - el["from"][1]
    for f, face in el["faces"].items():
        w, h = {"north": (x1 - x0, L), "south": (x1 - x0, L), "up": (x1 - x0, d), "down": (x1 - x0, d),
                "east": (d, L), "west": (d, L)}[f]
        face["uv"] = [0, 0, round(min(16, max(w, 0.5)), 4), round(min(16, max(h, 0.5)), 4)]
    return el


def ring_y(prefix, cx, cz, y0, y1, r, t, tex, n=12, faces=("north", "up", "down"), phase=0.0):
    """A ring of n wall segments round a vertical axis (a round column, a flare), each t thick inside radius r."""
    L = 2 * r * math.tan(math.pi / n) + 0.06
    return [box(f"{prefix}{k}", (cx - L / 2, y0, cz - r), (cx + L / 2, y1, cz - r + t), tex, faces=faces,
                rot=(0, k * 360 / n + phase, 0) if (k or phase) else None, origin=(cx, (y0 + y1) / 2, cz)) for k in range(n)]


def textures3(save):
    s = save
    # trophy case
    s(laminate(8300, (150, 112, 74)), "r4k-caselam")
    g = Image.new("RGBA", (32, 32), (214, 228, 232, 52))
    gp = g.load()
    for y in range(32):
        for x in range(32):
            t = (x + y) % 32
            if 4 <= t < 7:
                gp[x, y] = (236, 244, 246, 96)
    s(g, "r4k-caseglass")
    sg = Image.new("RGBA", (32, 32), (200, 222, 220, 90))
    rng = random.Random(8301)
    for _ in range(90):
        sg.putpixel((rng.randrange(32), rng.randrange(32)), (176, 170, 156, 200))   # dust
    s(sg, "r4k-shelfglass")
    s(M.fabric(8302, base=(52, 54, 92), weave="plain", contrast=5), "r4k-casefelt")
    s(M.brushed_metal(8303, base=(214, 176, 84), streak=6, sheen=26, drift=0.25), "r4k-trophy-gold")
    s(chrome(8304, (196, 198, 204)), "r4k-trophy-silver")
    s(M.noise_hv((232, 230, 224), 3, 8305, (32, 32), 5, (8, 4)), "r4k-marble")
    s(M.wood_planks(8306, base=(96, 60, 36), planks=1, grain=3), "r4k-walnut")
    ball = M.noise_hv((200, 100, 44), 3, 8307, (32, 32), 3, (16, 8))
    for k in range(32):
        ball.putpixel((k, 16), M.rgba((40, 30, 24)))
        ball.putpixel((16, k), M.rgba((40, 30, 24)))
    s(ball, "r4k-basketball")
    s(plastic(8308, (170, 40, 40), 2), "r4k-ribbon-red")
    s(plastic(8309, (40, 70, 160), 2), "r4k-ribbon-blue")
    s(Image.new("RGBA", (32, 32), (255, 240, 214, 255)), "r4k-lightstrip")
    # dugout
    sheet_ = M.painted_metal(8310, base=(78, 96, 84), panel=False, chips=6, under=(130, 126, 118))
    M.emboss_lines(sheet_, xs=(0, 8, 16, 24), raised=True, strength=0.18)
    M.grime(sheet_, amount=0.08, seed=8311, cover=0.4)
    s(sheet_, "r4k-dugout")
    low = M.painted_metal(8312, base=(78, 96, 84), panel=False, chips=8, under=(130, 126, 118))
    M.emboss_lines(low, xs=(0, 8, 16, 24), raised=True, strength=0.18)
    M.grime(low, amount=0.28, seed=8313, bias="bottom", cover=0.7)
    M.rust(low, amount=0.06, seed=8314)
    s(low, "r4k-dugout-low")
    roof = M.galvanised(8315, base=(150, 154, 156))
    M.emboss_lines(roof, xs=(2, 6, 10, 14, 18, 22, 26, 30), raised=True, strength=0.2)
    M.drips(roof, n=4, seed=8316, color=(110, 96, 80), length=(6, 14), strength=0.3)
    s(roof, "r4k-corrugated")
    bench = M.wood_planks(8317, base=(146, 112, 74), planks=1, grain=4)
    M.grime(bench, amount=0.14, seed=8318, cover=0.5)
    M.scratches(bench, 5, 8319, (3, 7), 0.1)
    s(bench, "r4k-benchwood")
    # column
    cp = M.painted_metal(8320, base=(226, 224, 216), panel=False, chips=3, under=(150, 140, 120))
    M.grime(cp, amount=0.06, seed=8321, cover=0.35)
    s(cp, "r4k-colpaint")
    cpl = M.painted_metal(8322, base=(226, 224, 216), panel=False, chips=6, under=(150, 140, 120))
    M.grime(cpl, amount=0.2, seed=8323, bias="bottom", cover=0.6)
    M.rust(cpl, amount=0.05, seed=8324)
    s(cpl, "r4k-colpaint-low")
    # ladder
    lw = M.wood_planks(8330, base=(148, 98, 56), planks=1, grain=3, contrast=1.2)
    M.scratches(lw, 3, 8331, (2, 5), 0.08)
    s(lw, "r4k-ladderwood")
    s(M.brushed_metal(8332, base=(190, 150, 72), streak=8, sheen=16, drift=0.25), "r4k-brass")
    s(M.rubber(8333), "r4k-rubber")
    # planter
    pc = M.concrete(8340, base=(168, 164, 154), aggregate=0.08)
    M.grime(pc, amount=0.2, seed=8341, bias="bottom", cover=0.6)
    s(pc, "r4k-planter")
    soil = M.noise_hv((70, 54, 40), 6, 8342, (32, 32), 6, (8, 4))
    rng = random.Random(8343)
    for _ in range(60):
        soil.putpixel((rng.randrange(32), rng.randrange(32)), M.rgba(rng.choice([(110, 96, 80), (46, 36, 26), (130, 120, 104)])))
    s(soil, "r4k-soil")
    leaf = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    lp = leaf.load()
    for y in range(32):
        for x in range(32):
            if rng.random() < 0.86:
                v = rng.uniform(-22, 18)
                lp[x, y] = M.rgba(M.lift((70, 100, 52), v + (8 if (x + 2 * y) % 5 == 0 else 0)))
    s(leaf, "r4k-shrub")
    s(M.noise_hv((40, 60, 32), 6, 8344, (32, 32), 6, (8, 4)), "r4k-shrub-core")
    s(plastic(8345, (214, 160, 90), 2), "r4k-butt")


# ---------------------------------------------------------------------- trophies

def cup(prefix, cx, y0, cz, k, tex, base="r4k-walnut", handles=True):
    """A trophy cup scaled by k: a square plinth, a stem, a cup widening in courses, two handles, a lid knob."""
    def sq(n, hw, ya, yb, t=tex, faces=fs("down")):
        return box(prefix + n, (cx - hw * k, y0 + ya * k, cz - hw * k), (cx + hw * k, y0 + yb * k, cz + hw * k), t, faces=faces)
    els = [sq("Plinth", 1.0, 0, 0.9, base), sq("PlinthTop", 0.8, 0.9, 1.1, base),
           sq("Foot", 0.55, 1.1, 1.4), sq("Stem", 0.22, 1.4, 2.4)]
    for i, (hw, ya, yb) in enumerate(((0.4, 2.4, 2.7), (0.65, 2.7, 3.1), (0.9, 3.9, 4.4))):
        els.append(sq(f"Bowl{i}", hw, ya, yb, faces=ALL if i == 0 else fs("down")))
    els += octo(f"{prefix}Belly", (cx - 0.82 * k, y0 + 3.1 * k, cz - 0.82 * k), (cx + 0.82 * k, y0 + 3.9 * k, cz + 0.82 * k), tex)
    for sgn in ((-1, 1) if handles else ()):   # the handles: a C of three bars either side
        xo = cx + sgn * 0.9 * k
        xa, xb = (xo, xo + 0.55 * k) if sgn > 0 else (xo - 0.55 * k, xo)
        xc = (xb - 0.2 * k, xb) if sgn > 0 else (xa, xa + 0.2 * k)
        els += [box(f"{prefix}HdlT{sgn}", (xa, y0 + 4.0 * k, cz - 0.1 * k), (xb, y0 + 4.2 * k, cz + 0.1 * k), tex),
                box(f"{prefix}HdlB{sgn}", (xa, y0 + 3.0 * k, cz - 0.1 * k), (xb, y0 + 3.2 * k, cz + 0.1 * k), tex),
                box(f"{prefix}HdlS{sgn}", (xc[0], y0 + 3.2 * k, cz - 0.1 * k), (xc[1], y0 + 4.0 * k, cz + 0.1 * k), tex)]
    return els


def figure(prefix, cx, y0, cz, kind, tex="r4k-trophy-gold"):
    """A gold figure on a marble plinth, built in the XY plane (seen from the front): a basketball player shooting, or a
    runner in stride."""
    els = [box(prefix + "Plinth", (cx - 1.0, y0, cz - 0.8), (cx + 1.0, y0 + 1.0, cz + 0.8), "r4k-marble", faces=fs("down")),
           box(prefix + "Base", (cx - 0.7, y0 + 1.0, cz - 0.5), (cx + 0.7, y0 + 1.2, cz + 0.5), tex, faces=fs("down"))]
    b = y0 + 1.2
    z0, z1 = cz - 0.2, cz + 0.2

    def limb(n, x, y, ln, ang, w=0.3):
        els.append(box(prefix + n, (x - w / 2, y, z0), (x + w / 2, y + ln, z1), tex, rot=(0, 0, ang) if ang else None,
                       origin=(x, y, cz)))

    if kind == "shooter":
        limb("LegL", cx - 0.2, b, 1.3, 6)
        limb("LegR", cx + 0.2, b, 1.3, -6)
        els.append(box(prefix + "Body", (cx - 0.3, b + 1.3, z0 - 0.05), (cx + 0.3, b + 2.3, z1 + 0.05), tex))
        els.append(box(prefix + "Head", (cx - 0.2, b + 2.35, z0), (cx + 0.2, b + 2.75, z1), tex))
        limb("ArmL", cx - 0.25, b + 2.2, 1.0, -20, 0.22)
        limb("ArmR", cx + 0.25, b + 2.2, 1.0, 20, 0.22)
        els.append(box(prefix + "Ball", (cx - 0.3, b + 3.1, z0 - 0.05), (cx + 0.3, b + 3.6, z1 + 0.05), tex))
    else:   # runner
        limb("LegF", cx, b, 1.4, -28)
        limb("LegB", cx, b, 1.4, 30)
        els.append(box(prefix + "Body", (cx - 0.28, b + 1.2, z0 - 0.05), (cx + 0.28, b + 2.2, z1 + 0.05), tex,
                       rot=(0, 0, -10), origin=(cx, b + 1.2, cz)))
        els.append(box(prefix + "Head", (cx - 0.38, b + 2.25, z0), (cx + 0.02, b + 2.65, z1), tex))
        limb("ArmF", cx - 0.1, b + 1.6, 0.9, 50, 0.22)
        limb("ArmB", cx + 0.1, b + 1.6, 0.9, -55, 0.22)
    return els


def medal(prefix, x, ytop, z, ribbon, tex):
    return [box(prefix + "Ribbon", (x - 0.3, ytop - 2.2, z - 0.06), (x + 0.3, ytop, z), ribbon, faces=fs("south")),
            box(prefix + "Disc", (x - 0.45, ytop - 3.0, z - 0.16), (x + 0.45, ytop - 2.1, z - 0.06), tex, faces=fs("south"))]


def trophy(part):
    """A trophy case one block wide and two high, its back to the wall at z 16, about 0.6 block deep (front at z 6.2):
    lower, the laminate cabinet base to 0.45 block and the case's felt floor with the first trophies; upper, the glass
    in its aluminium frame, two glass shelves on pins, cups, figures, medals, and a lit header strip."""
    alu, lam, felt, gl = "r4k-alu", "r4k-caselam", "r4k-casefelt", "r4k-caseglass"
    els = []
    lo = part == "lower"
    gy0, gy1 = (7.8, 16) if lo else (0, 14.6)
    # the frame posts at the front corners and back corners, the glass front and sides, the felt back
    for x0, x1 in ((0, 0.8), (15.2, 16)):
        els.append(box(f"PostF{x0}", (x0, gy0, 6.2), (x1, gy1, 7.0), alu, faces=fs("up", "down")))
        els.append(box(f"PostB{x0}", (x0, gy0, 15.2), (x1, gy1, 16), alu, faces=fs("up", "down", "south")))
    els += [box("GlassF", (0.8, gy0 + (0.6 if lo else 0), 6.5), (15.2, gy1, 6.6), gl, faces=("north", "south")),
            box("GlassL", (0.35, gy0, 7.0), (0.45, gy1, 15.2), gl, faces=("east", "west")),
            box("GlassR", (15.55, gy0, 7.0), (15.65, gy1, 15.2), gl, faces=("east", "west")),
            box("Back", (0.8, gy0, 15.6), (15.2, gy1, 16), felt, faces=("north",))]
    for e in els[-4:-1]:
        full_uv(e)
    if lo:
        els += [box("Plinth", (0.6, 0, 7.2), (15.4, 1.0, 16), "r4k-black", faces=("north", "east", "west")),
                box("Carcass", (0.2, 1.0, 6.6), (15.8, 7.2, 16), lam, faces=fs("south", "down")),
                box("Deck", (0, 7.2, 6.2), (16, 7.8, 16), lam, faces=fs("south", "up")),
                box("Felt", (0.8, 7.8, 7.0), (15.2, 8.0, 15.6), felt, faces=("up",)),
                box("SillRail", (0.8, 7.8, 6.2), (15.2, 8.4, 7.0), alu, faces=fs("down"))]
        for k, (x0, x1) in enumerate(((0.5, 7.9), (8.1, 15.5))):
            els.append(box(f"Door{k}", (x0, 1.4, 6.3), (x1, 6.8, 6.6), lam, faces=fs("south")))
            hx = x1 - 1.0 if k == 0 else x0 + 0.6
            els += [box(f"Pull{k}", (hx, 3.4, 5.8), (hx + 0.4, 5.6, 6.1), "r4k-satin"),
                    box(f"PullA{k}", (hx, 3.6, 6.1), (hx + 0.4, 3.9, 6.3), "r4k-satin", faces=fs("north", "south")),
                    box(f"PullB{k}", (hx, 5.1, 6.1), (hx + 0.4, 5.4, 6.3), "r4k-satin", faces=fs("north", "south"))]
        # the first trophies on the felt floor: a big gold cup, a ball on a stand, a shield plaque against the back
        els += cup("Big", 4.2, 8.0, 10.8, 1.3, "r4k-trophy-gold")
        els += [box("StandFoot", (10.4, 8.0, 9.6), (12.6, 8.4, 11.8), "r4k-walnut", faces=fs("down")),
                box("StandPost", (11.3, 8.4, 10.5), (11.7, 9.6, 10.9), "r4k-trophy-gold")]
        for i, (hw, hh) in enumerate(((1.2, 0.55), (1.0, 0.95), (0.6, 1.2))):   # a ball from three stepped rounds
            els += octo(f"Ball{i}", (11.5 - hw, 10.8 - hh, 10.7 - hw), (11.5 + hw, 10.8 + hh, 10.7 + hw), "r4k-basketball")
        els += [box("Shield", (6.4, 8.6, 15.2), (9.6, 13.4, 15.6), "r4k-walnut", faces=fs("south")),
                box("ShieldTip", (7.0, 8.0, 15.25), (9.0, 8.6, 15.6), "r4k-walnut", faces=fs("south")),
                box("ShieldPlate", (6.9, 10.6, 15.1), (9.1, 12.6, 15.2), "r4k-trophy-gold", faces=("north",))]
        els += [box("ShieldFoot", (7.2, 8.0, 14.0), (8.8, 8.4, 15.2), "r4k-walnut", faces=fs("down"))]
    else:
        els += [box("Header", (0, 14.6, 6.2), (16, 16, 16), alu, faces=fs("south")),
                box("Light", (1.0, 14.3, 7.6), (15.0, 14.6, 8.6), "r4k-lightstrip", faces=("down", "north", "south"), glow=180)]
        # two glass shelves on pins
        for i, y in enumerate((4.0, 9.6)):
            els.append(box(f"Shelf{i}", (0.9, y, 7.2), (15.1, y + 0.3, 15.5), "r4k-shelfglass", faces=("up", "down", "north")))
            for x in (0.8, 14.7):
                for z in (8.0, 14.4):
                    els.append(box(f"Pin{i}{x}{z}", (x, y - 0.3, z), (x + 0.5, y, z + 0.4), "r4k-satin", faces=fs("up")))
        els += cup("Silver", 3.6, 4.3, 11.0, 0.95, "r4k-trophy-silver")
        els += figure("Shooter", 8.2, 4.3, 11.0, "shooter")
        els += figure("Runner", 12.4, 4.3, 11.0, "runner")
        els += cup("SmallG", 4.4, 9.9, 11.4, 0.7, "r4k-trophy-gold", handles=False)
        els += cup("SmallS", 11.6, 9.9, 11.4, 0.7, "r4k-trophy-silver", handles=False)
        for i, (x, rib, t) in enumerate(((6.8, "r4k-ribbon-red", "r4k-trophy-gold"), (8.0, "r4k-ribbon-blue", "r4k-trophy-silver"),
                                         (9.2, "r4k-ribbon-red", "r4k-trophy-gold"))):
            els += medal(f"Medal{i}", x, 13.8, 15.6, rib, t)
    return els


# ---------------------------------------------------------------------- dugout

ROOF_F, ROOF_B = (13.6, -1.6), (11.2, 16.0)   # (y, z) of the roof's top at its front edge and at the back (upper block)


def dugout(part, half):
    """A block of a dugout 3 wide (part l, m, r as seen from in front: l at +x), 2 high and 1 deep, open to the north:
    the back panel, the side panels at the ends, front posts, the mono-pitch roof overhanging the front (upper), the
    front's top rail, a long bench at 0.5 on steel legs, a coat-hook rail on the back."""
    st, sheet_ = "r4k-steel", ("r4k-dugout-low" if half == "lower" else "r4k-dugout")
    seam = {"l": ("west",), "m": ("east", "west"), "r": ("east",)}[part]
    lo = half == "lower"
    end = {"l": (15.2, 16), "r": (0, 0.8)}.get(part)
    bx0, bx1 = {"l": (0, 15.2), "m": (0, 16), "r": (0.8, 16)}[part]
    els = [box("Back", (bx0, 0, 15.2), (bx1, 16 if lo else 11.4, 16), sheet_, faces=("north", "up") if not lo else ("north",))]
    if end:
        x0, x1 = end
        outer = "east" if part == "l" else "west"
        px0, px1 = (14.8, 16) if part == "l" else (0, 1.2)
        sx0, sx1 = (x0, x1 - 0.1) if part == "l" else (x0 + 0.1, x1)
        els += [box("Side", (sx0, 0, 1.4), (sx1, 16 if lo else 11.4, 15.0), sheet_, faces=fs("north", "south", "down")),
                box("PostF", (px0, 0, 0.2), (px1, 16 if lo else 13.0, 1.4), st, faces=fs("down", "up") if lo else fs("down")),
                box("PostB", (px0, 0, 15.0), (px1, 16 if lo else 11.4, 16), st, faces=fs("down", "south", "up") if lo else fs("down", "south"))]
        if not lo:   # the side's top stepped up under the sloping roof
            els += [box("SideHi1", (sx0, 11.4, 1.4), (sx1, 12.4, 10.0), sheet_, faces=fs("down", "north")),
                    box("SideHi2", (sx0, 12.4, 1.4), (sx1, 13.0, 4.6), sheet_, faces=fs("down", "north"))]
        for y in ((1.0, 14.0) if lo else (6.0,)):
            els.append(box(f"BoltF{y}", (px0 + 0.35, y, -0.1 + 0.2), (px0 + 0.85, y + 0.5, 0.2), "r4k-bolt", faces=fs("south")))
    if lo:
        # the bench: two boards, a leg frame per block
        for i, (z0, z1) in enumerate(((10.0, 12.1), (12.3, 14.4))):
            els.append(box(f"Seat{i}", (bx0, 7.2, z0), (bx1, 8.0, z1), "r4k-benchwood", faces=fs(*seam)))
        for x in (7.4,):
            els += [box("LegF", (x, 0, 10.6), (x + 1.0, 6.6, 11.4), st, faces=fs("down")),
                    box("LegB", (x, 0, 13.2), (x + 1.0, 6.6, 14.0), st, faces=fs("down")),
                    box("LegArm", (x - 0.1, 6.6, 10.0), (x + 1.1, 7.2, 14.4), st),
                    box("LegFoot", (x - 0.2, 0, 10.2), (x + 1.2, 0.3, 14.4), st, faces=fs("down"))]
        els.append(box("Rail", (bx0, 6.0, 13.4), (bx1, 6.6, 14.2), st, faces=fs(*seam)))
    else:
        # the roof: corrugated sheet sloping back, its front fascia, the front's top rail and the back's top rail
        rx0, rx1 = {"l": (0, 16.25), "m": (0, 16), "r": (-0.25, 16)}[part]   # the roof runs a touch past the ends
        els.append(xslab("Roof", rx0, rx1, ROOF_F, ROOF_B, 0.5, "r4k-corrugated", faces=fs(*seam)))
        els += [box("Fascia", (rx0, 12.6, -1.9), (rx1, 13.6, -1.5), "r4k-corrugated", faces=fs(*seam)),
                box("TopRail", (bx0, 12.2, 0.2), (bx1, 13.0, 1.4), st, faces=fs(*seam)),
                box("BackRail", (bx0, 10.6, 14.4), (bx1, 11.4, 15.2), st, faces=fs(*seam, "up"))]
        # the coat-hook rail on the back, hooks every 4 units
        els.append(box("HookRail", (bx0, 4.0, 14.6), (bx1, 4.8, 15.2), "r4k-benchwood", faces=fs(*seam, "south")))
        for x in (2.0, 6.0, 10.0, 14.0):
            if bx0 + 0.5 < x < bx1 - 0.8:
                els += [box(f"Hook{x}", (x, 4.1, 13.6), (x + 0.4, 4.5, 14.6), st, faces=fs("south")),
                        box(f"HookUp{x}", (x, 4.5, 13.6), (x + 0.4, 5.3, 14.0), st, faces=fs("down"))]
    return els


# ---------------------------------------------------------------------- column

def column(part):
    """A round canopy column 3 blocks high, 0.45 block across: twelve painted steel staves round the axis; the base on a
    chamfered concrete plinth with a bolted base plate and a weld collar; the cap flaring to a plate under the soffit."""
    cx = cz = 8.0
    R = 3.6
    els = []
    if part == "base":
        els += [box("Plinth", (2.6, 0, 2.6), (13.4, 1.0, 13.4), "r4k-plinth", faces=fs("down")),
                box("Chamfer", (3.0, 1.0, 3.0), (13.0, 1.3, 13.0), "r4k-plinth", faces=fs("down")),
                box("Plate", (3.6, 1.3, 3.6), (12.4, 1.7, 12.4), "r4k-steel", faces=fs("down"))]
        for x in (4.0, 11.4):
            for z in (4.0, 11.4):
                els += [box(f"Nut{x}{z}", (x, 1.7, z), (x + 0.6, 2.2, z + 0.6), "r4k-bolt", faces=fs("down")),
                        box(f"Stud{x}{z}", (x + 0.15, 2.2, z + 0.15), (x + 0.45, 2.5, z + 0.45), "r4k-bolt", faces=fs("down"))]
        els += ring_y("Collar", cx, cz, 1.7, 3.0, R + 0.35, 0.6, "r4k-colpaint-low")
        els += ring_y("Shaft", cx, cz, 3.0, 16, R, 0.6, "r4k-colpaint-low", faces=("north",))
    elif part == "shaft":
        els += ring_y("Shaft", cx, cz, 0, 16, R, 0.6, "r4k-colpaint", faces=("north",))
    else:
        els += ring_y("Shaft", cx, cz, 0, 11.0, R, 0.6, "r4k-colpaint", faces=("north",))
        els += ring_y("Band", cx, cz, 11.0, 11.8, R + 0.3, 0.6, "r4k-colpaint")
        els += ring_y("Flare1", cx, cz, 11.8, 13.0, R + 0.8, 1.2, "r4k-colpaint", phase=15)
        els += ring_y("Flare2", cx, cz, 13.0, 14.2, R + 1.6, 2.0, "r4k-colpaint")
        els += [box("CapPlate", (1.6, 14.2, 1.6), (14.4, 15.4, 14.4), "r4k-colpaint", faces=fs("up")),
                box("CapTrim", (1.2, 15.4, 1.2), (14.8, 16, 14.8), "r4k-steel", faces=fs("up"))]
        for x in (2.2, 13.2):
            for z in (2.2, 13.2):
                els.append(box(f"Bolt{x}{z}", (x, 13.9, z), (x + 0.6, 14.2, z + 0.6), "r4k-bolt", faces=fs("up")))
    return els


# ---------------------------------------------------------------------- library ladder

LAD_Z0, LAD_Z1 = 5.6, 14.6   # the rails' middle at the foot (y 0, lower) and at the top (y 32)


def lad_z(Y):
    return LAD_Z0 + (LAD_Z1 - LAD_Z0) * Y / 32.0


def ladder(part):
    """A library rolling ladder leaning on the bookstack (the block to the south, its face at z 16): two oak rails
    leaning back, horizontal treads with nosings and brass brackets, wheels in brass forks at the foot (lower), brass
    hooks over a brass rail on the stack at the top (upper)."""
    wd, br = "r4k-ladderwood", "r4k-brass"
    base = 0 if part == "lower" else 16
    els = []
    for x in (2.6, 13.4):
        ya, yb = (1.2, 16) if part == "lower" else (0, 15.0)
        els.append(bar(f"Rail{x}", (x, ya, lad_z(ya + base)), (x, yb, lad_z(yb + base)), 1.0, wd, d=1.4))
    for y in ((4.0, 8.0, 12.0, 16.0) if part == "lower" else (4.0, 8.0, 12.0)):
        if y >= 16:
            continue
        zc = lad_z(y + base)
        els += [box(f"Tread{y}", (3.1, y - 0.6, zc - 1.6), (12.9, y, zc + 1.0), wd),
                box(f"Nose{y}", (3.1, y - 0.8, zc - 1.8), (12.9, y - 0.1, zc - 1.6), wd, faces=fs("east", "west"))]
        for x in (3.1, 12.4):
            els.append(box(f"Bracket{y}{x}", (x, y - 1.4, zc - 0.3), (x + 0.5, y - 0.6, zc + 0.5), br, faces=fs("up")))
    if part == "lower":
        for x in (2.6, 13.4):
            z = lad_z(0.6)
            els += [box(f"Shoe{x}", (x - 0.6, 1.0, z - 0.8), (x + 0.6, 2.0, z + 0.8), br),
                    box(f"ForkL{x}", (x - 0.6, 0.3, z - 0.6), (x - 0.35, 1.0, z + 0.6), br),
                    box(f"ForkR{x}", (x + 0.35, 0.3, z - 0.6), (x + 0.6, 1.0, z + 0.6), br)]
            els += octo(f"Wheel{x}", (x - 0.35, 0, z - 0.75), (x + 0.35, 1.5, z + 0.75), "r4k-rubber", axis="x")
            els.append(box(f"Axle{x}", (x - 0.7, 0.55, z - 0.15), (x + 0.7, 0.95, z + 0.15), br, faces=("east", "west")))
    else:
        # a top cap on each rail, the hooks over the stack's brass rail, the rail itself on its brackets
        els += octo("StackRail", (0, 14.6, 15.2), (16, 15.6, 16.0), br, axis="x", faces=fs("east", "west", "south"))
        for x in (2.6, 13.4):
            zt = lad_z(31.0)
            els += [box(f"Cap{x}", (x - 0.6, 15.0, zt - 0.8), (x + 0.6, 15.6, zt + 0.8), br),
                    box(f"HookArm{x}", (x - 0.35, 15.6, zt - 0.4), (x + 0.35, 16.0, 16.0), br, faces=fs("south")),
                    box(f"HookDrop{x}", (x - 0.35, 14.2, 15.95), (x + 0.35, 15.6, 16.0), br, faces=("north",)),
                    box(f"Roller{x}", (x - 0.5, 14.9, 14.7), (x + 0.5, 15.5, 15.2), br)]
        for x in (0.6, 15.0):
            els.append(box(f"RailBracket{x}", (x, 14.2, 15.4), (x + 0.4, 15.8, 16.0), br, faces=fs("south")))
    return els


# ---------------------------------------------------------------------- planter

def planter():
    """A square concrete planter (0.66 block high) with a capping lip, its north-east corner chipped, soil, a clipped
    shrub in stepped courses of cut-out leaves round a dark core, cigarette butts in the soil."""
    pc, nd = "r4k-planter", fs("down")
    els = [box("WallN", (1.0, 0, 1.0), (13.6, 9.8, 2.2), pc, faces=nd),
           box("WallChip", (13.6, 0, 1.0), (15.0, 8.6, 2.2), pc, faces=nd),
           box("WallChipStep", (13.6, 8.6, 1.6), (14.4, 9.2, 2.2), pc, faces=nd),
           box("WallS", (1.0, 0, 13.8), (15.0, 9.8, 15.0), pc, faces=nd),
           box("WallW", (1.0, 0, 2.2), (2.2, 9.8, 13.8), pc, faces=nd),
           box("WallE", (13.8, 0, 2.2), (15.0, 9.8, 13.8), pc, faces=nd),
           # the capping lip, overhanging; broken off at the chipped corner
           box("CapN", (0.6, 9.8, 0.6), (13.4, 10.6, 2.4), pc, faces=nd),
           box("CapS", (0.6, 9.8, 13.6), (15.4, 10.6, 15.4), pc, faces=nd),
           box("CapW", (0.6, 9.8, 2.4), (2.4, 10.6, 13.6), pc, faces=nd),
           box("CapE", (13.6, 9.8, 2.4), (15.4, 10.6, 13.6), pc, faces=nd),
           box("Foot", (1.4, -0.01, 1.4), (14.6, 0.3, 14.6), "r4k-black", faces=("north", "east", "south", "west")),
           box("Soil", (2.2, 8.4, 2.2), (13.8, 9.0, 13.8), "r4k-soil", faces=("up",))]
    # the shrub: a dark core, then cut-out leaf courses stepped to a rounded clipped shape
    els += octo("Core", (4.2, 9.0, 4.2), (11.8, 14.4, 11.8), "r4k-shrub-core")
    for i, (hw, y0, y1) in enumerate(((4.8, 9.6, 11.0), (5.4, 11.0, 13.2), (5.0, 13.2, 14.6), (3.8, 14.6, 15.6))):
        els += octo(f"Leaves{i}", (8 - hw, y0, 8 - hw), (8 + hw, y1, 8 + hw), "r4k-shrub")
    # cigarette butts in the soil
    for i, (x, z, a) in enumerate(((3.2, 3.4, 20), (12.0, 12.6, -40), (3.6, 12.2, 70))):
        els.append(box(f"Butt{i}", (x, 9.0, z), (x + 1.2, 9.4, z + 0.4), "r4k-butt", faces=fs("down"), rot=(0, a, 0)))
    return els


def shapes3():
    out = {"l52-planter": planter()}
    for p in ("lower", "upper"):
        out[f"l52-trophy-{p}"] = trophy(p)
        out[f"l52-ladder-{p}"] = ladder(p)
        for e in "lmr":
            out[f"l52-dugout-{e}-{p}"] = dugout(e, p)
    for p in ("base", "shaft", "cap"):
        out[f"l52-column-{p}"] = column(p)
    return out
