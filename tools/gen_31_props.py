"""Level 31, "Roller Rink": the props and set dressing of its halls and rooms (second generator, beside gen_31.py).

It writes only its own files, none of the ones gen_31.py writes:
    blocktypes/31/  l31-carpet (rink, black, grey)  l31-floor (polished, tile, quarry)  l31-brick (plain)
                    l31-sign (trash, outoforder, menu, ad1-3, staffdoorlow/high, door70low/high; the picture on one face)
                    l31-chair  l31-table  l31-bench (orange, green)  l31-condiments  l31-fountain  l31-djdesk (deck, mixer)
                    l31-speaker  l31-gate (we, ns)  l31-star  l31-dispenser  l31-retrocab (shooter, barrels, pyramid)
                    l31-skateshelf  l31-cinemabench  l31-tv (tl tm tr bl bm br)  l31-cctv  l31-monitors
    shapes/block/31/ and textures/block/31/ for them (the textures are procedural; pictures are 64 px, lettering is
    drawn with a 3x5 pixel font of our own).

Every oriented prop is modelled facing NORTH (low z) and has the variant group "side" (north, east, south, west) last:
-east is rotateY 270, -south 180, -west 90, as l3999-chair. Run from the repo root:
    bash tools/locked.sh run python tools/gen_31_props.py
"""
import math
import os
import random

from PIL import Image, ImageDraw

import matlib as M
from modelkit import box, turn, textures, without, DIRS, PX
from texlib import S
from gen_31 import (write_json, shape, save, SIDES, TEX, BLOCKS, STONE, WOOD, GLASS, CLOTH, tex as tex31,
                    cube_block)

METAL = {"walk": "game:walk/stone*", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit",
         "hit": "game:block/heavymetal-hit"}
ROT = {"north": 0, "east": 270, "south": 180, "west": 90}
PIC = 64  # a picture texture is 64 px = 16 units, so 4 px a unit


# ======================================================================== Drawing kit

def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mixc(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(round(v * k)))) for v in c[:3])


def new(w=PIC, h=None, col=(0, 0, 0)):
    return Image.new("RGBA", (w, h or w), tuple(col[:3]) + (255,))


def R(img, x0, y0, x1, y1, col):
    """A filled rectangle, ends inclusive."""
    ImageDraw.Draw(img).rectangle([x0, y0, x1, y1], fill=tuple(col) if len(col) == 4 else tuple(col[:3]) + (255,))


def outline(img, x0, y0, x1, y1, col):
    ImageDraw.Draw(img).rectangle([x0, y0, x1, y1], outline=tuple(col[:3]) + (255,))


def disc(img, cx, cy, r, col):
    ImageDraw.Draw(img).ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(col[:3]) + (255,))


def poly(img, pts, col):
    ImageDraw.Draw(img).polygon(pts, fill=tuple(col[:3]) + (255,))


def line(img, p0, p1, col, w=1):
    ImageDraw.Draw(img).line([p0, p1], fill=tuple(col[:3]) + (255,), width=w)


def noise(img, amount, seed):
    rng = random.Random(seed)
    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            n = rng.uniform(-amount, amount)
            px[x, y] = (M.clamp(r + n), M.clamp(g + n), M.clamp(b + n), a)
    return img


GLYPHS = {
    "A": ".#./#.#/###/#.#/#.#", "B": "##./#.#/##./#.#/##.", "C": ".##/#../#../#../.##", "D": "##./#.#/#.#/#.#/##.",
    "E": "###/#../##./#../###", "F": "###/#../##./#../#..", "G": ".##/#../#.#/#.#/.##", "H": "#.#/#.#/###/#.#/#.#",
    "I": "###/.#./.#./.#./###", "J": "..#/..#/..#/#.#/.#.", "K": "#.#/#.#/##./#.#/#.#", "L": "#../#../#../#../###",
    "M": "#.#/###/###/#.#/#.#", "N": "###/#.#/#.#/#.#/#.#", "O": ".#./#.#/#.#/#.#/.#.", "P": "##./#.#/##./#../#..",
    "Q": ".#./#.#/#.#/##./.##", "R": "##./#.#/##./#.#/#.#", "S": ".##/#../.#./..#/##.", "T": "###/.#./.#./.#./.#.",
    "U": "#.#/#.#/#.#/#.#/###", "V": "#.#/#.#/#.#/#.#/.#.", "W": "#.#/#.#/###/###/#.#", "X": "#.#/#.#/.#./#.#/#.#",
    "Y": "#.#/#.#/.#./.#./.#.", "Z": "###/..#/.#./#../###",
    "0": "###/#.#/#.#/#.#/###", "1": ".#./##./.#./.#./###", "2": "##./..#/.#./#../###", "3": "##./..#/.#./..#/##.",
    "4": "#.#/#.#/###/..#/..#", "5": "###/#../##./..#/##.", "6": ".##/#../###/#.#/###", "7": "###/..#/.#./.#./.#.",
    "8": "###/#.#/###/#.#/###", "9": "###/#.#/###/..#/##.",
    "!": ".#./.#./.#./.../.#.", "'": ".#./.#./.../.../...", "-": ".../.../###/.../...", ".": ".../.../.../.../.#.",
    " ": ".../.../.../.../...", "?": "##./..#/.#./.../.#.",
}


def textw(s, sx=1, bold=False):
    return len(s) * (3 * sx + (1 if bold else 0) + sx) - sx


def text(img, x, y, s, col, sx=1, sy=None, bold=False, jitter=0, seed=0):
    """Pixel lettering from the 3x5 font; sx, sy scale it, bold thickens it by a pixel, jitter wobbles each letter
    (hand lettering). Returns the width."""
    sy = sy or sx
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    col = tuple(col[:3]) + (255,)
    cx = x
    for ch in s:
        rows = GLYPHS[ch].split("/")
        dy = rng.randint(-jitter, jitter) if jitter else 0
        for r, row in enumerate(rows):
            for c, v in enumerate(row):
                if v == "#":
                    x0 = cx + c * sx
                    d.rectangle([x0, y + dy + r * sy, x0 + sx - 1 + (1 if bold else 0), y + dy + r * sy + sy - 1], fill=col)
        cx += 3 * sx + (1 if bold else 0) + sx
    return cx - x - sx


def ctext(img, cx, y, s, col, sx=1, sy=None, bold=False, **kw):
    w = textw(s, sx, bold)
    return text(img, cx - w // 2, y, s, col, sx, sy, bold, **kw)


def pic_uv(w, h, u=0.0, v=0.0):
    """The UV rectangle (units) of a w x h unit picture painted at 4 px a unit in a 64 px texture."""
    return [u, v, u + w, v + h]


def B(name, frm, to, t, faces=DIRS, glow=0, rot=None, origin=None, uv=None, **over):
    """modelkit.box with per-face overrides: north=("key", uv, glow) / "key"."""
    el = box(name, frm, to, t, faces=faces, glow=glow, rot=rot, origin=origin, uv=uv)
    for f, v in over.items():
        if isinstance(v, str):
            v = (v,)
        face = el["faces"][f]
        face["texture"] = "#" + v[0]
        if len(v) > 1 and v[1] is not None:
            face["uv"] = list(v[1])
        if len(v) > 2:
            face["glow"] = v[2]
    return el


def mat(**kw):
    return dict(kw)


def bg_texture(path_or_name):
    """A background wall texture, enlarged 2x to the 64 px of a picture face."""
    p = path_or_name if os.path.isabs(path_or_name) else os.path.join(TEX, path_or_name + ".png")
    return Image.open(p).convert("RGBA").resize((PIC, PIC), Image.NEAREST)


MIDNIGHT = os.path.join(TEX, "..", "3999", "wall-midnight.png")


# ======================================================================== Block type writers

def box_dict(b, side):
    d = {"x1": b[0], "y1": b[1], "z1": b[2], "x2": b[3], "y2": b[4], "z2": b[5]}
    if ROT[side]:
        d["rotateY"] = ROT[side]
    return d


def prop_block(code, comment, shape_for, sel, col, kinds=None, kindgroup="kind", oriented=True, material="Metal",
               sounds=METAL, resistance=3, extra=None, by_kind=None):
    """A JSON-shaped prop. shape_for(kind) -> a shape reference (or a dict base); sel/col are (x1,y1,z1,x2,y2,z2) in block
    units (or callables of the kind; col None for no collision)."""
    groups = []
    if kinds:
        groups.append({"code": kindgroup, "states": kinds})
    if oriented:
        groups.append({"code": "side", "states": SIDES})
    shapes, sels, cols = {}, {}, {}
    for kind in (kinds or [None]):
        for side in (SIDES if oriented else [None]):
            key = "-".join(p for p in (code, kind, side) if p)
            s = shape_for(kind)
            d = {"base": s} if isinstance(s, str) else dict(s)
            if side and ROT[side]:
                d["rotateY"] = ROT[side]
            shapes[key] = d
            sb = sel(kind) if callable(sel) else sel
            sels[key] = box_dict(sb, side or "north")
            cb = col(kind) if callable(col) else col
            if cb:
                cols[key] = box_dict(cb, side or "north")
    data = {"code": code, "variantgroups": groups, "shapeByType": shapes,
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": material, "drawtype": "json",
            "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
            "resistance": resistance, "sounds": sounds, "selectionboxByType": sels, "drops": []}
    if cols:
        data["collisionboxByType"] = cols
    else:
        data["collisionbox"] = None
    data.update(extra or {})
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def full(*a):
    return a


# ======================================================================== Shared material textures

def plastic(base, seed, sheen=0.10):
    img = M.noise_hv(base, 2, seed, S, 3, (8, 4))
    px = img.load()
    for y in range(S):
        for x in range(S):
            k = 1 + sheen * math.exp(-((((x - y) % S) - 10) / 4.0) ** 2)
            r, g, b, a = px[x, y]
            px[x, y] = (M.clamp(r * k), M.clamp(g * k), M.clamp(b * k), a)
    return img


def materials():
    save(M.brushed_metal(seed=3201, base=(206, 212, 222), sheen=18), "mat-chrome")
    save(M.brushed_metal(seed=3202, base=(150, 154, 160)), "mat-steel")
    save(M.brushed_metal(seed=3203, base=(112, 118, 126), direction="v"), "mat-gunmetal")
    save(M.painted_metal(seed=3204, base=(34, 34, 40), panel=False, chips=2), "mat-dark")
    save(M.rubber(seed=3205, base=(24, 24, 28)), "mat-black")
    save(M.painted_metal(seed=3206, base=(200, 202, 204), panel=False, chips=3), "mat-white")


# ======================================================================== Cubes: carpet, floor, brick

def confetti(seed, colours, n):
    """1990s rink-carpet confetti, tiling (everything wraps): small triangles, zigzags, squiggles and dots."""
    pat = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    p = pat.load()
    rng = random.Random(seed)

    def dot(x, y, c):
        p[x % S, y % S] = tuple(c) + (255,)
    for _ in range(n):
        c = rng.choice(colours)
        x, y = rng.randrange(S), rng.randrange(S)
        flip = rng.random() < 0.5
        kind = rng.choice("tzsdd")
        if kind == "d":
            pts = [(0, 0), (1, 0), (0, 1)]
        elif kind == "t":
            pts = [(1, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)]
        elif kind == "z":
            pts = [(k, k % 2 * 2) for k in range(6)]
        else:
            pts = [(k, round(1.4 * math.sin(k * 1.2))) for k in range(8)]
        for (a, b) in pts:
            dot(x + (b if flip else a), y + (a if flip else b), c)
    return pat


def cubes_floor():
    muted = [(190, 58, 150), (58, 168, 188), (208, 186, 72), (48, 158, 138)]
    base = (22, 20, 32)
    save(M.carpet(seed=3210, base=base, pile=8, mottle=3, grain=3, pattern=confetti(3211, muted, 30), pattern_strength=0.9), "carpet-rink")
    save(M.carpet(seed=3212, base=(24, 24, 27), pile=6, mottle=3, grain=5, nap="se"), "carpet-black")
    save(M.carpet(seed=3213, base=(126, 127, 132), tone2=(116, 117, 124), mix2=0.35, pile=5, mottle=3, grain=3, loop=True), "carpet-grey")

    # Polished concrete: a swirl-troweled grey with a broad soft sheen and a bright diagonal reflection (all periodic)
    img = M.concrete(seed=3214, base=(118, 121, 127), mottle=4, aggregate=0.02, pores=0.003, swirl=0.4, grain=2)
    px = img.load()
    for y in range(S):
        for x in range(S):
            k = (1 + 0.05 * math.sin(2 * math.pi * (x + y) / S) + 0.04 * math.sin(2 * math.pi * (2 * x - y) / S + 1.0)
                 + 0.14 * math.exp(-((((x - y) % S) - 8) / 3.5) ** 2) + 0.07 * math.exp(-((((x - y) % S) - 22) / 2.0) ** 2))
            r, g, b, a = px[x, y]
            px[x, y] = (M.clamp(r * k), M.clamp(g * k * 1.005), M.clamp(b * k * 1.02), a)
    save(img, "floor-polished")

    # Vinyl tiles: 2x2 to a block, pale blue and white checker, thin grout
    white = M.tile(seed=3215, base=(232, 234, 236), grout=(168, 174, 184), pitch=16, grout_w=1, jitter=3, glaze=False, speckle=0.1)
    blue = M.tile(seed=3215, base=(142, 186, 232), grout=(168, 174, 184), pitch=16, grout_w=1, jitter=3, glaze=False, speckle=0.1)
    chk = white.copy()
    for (x0, y0) in ((0, 0), (16, 16)):
        chk.paste(blue.crop((x0, y0, x0 + 16, y0 + 16)), (x0, y0))
    save(chk, "floor-tile")
    save(M.tile(seed=3216, base=(150, 72, 52), grout=(112, 104, 96), pitch=16, grout_w=1, jitter=8, uneven=5, glaze=False, speckle=0.35), "floor-quarry")
    save(M.brick(seed=3217), "brick-plain")

    carp = {"rink": "carpet-rink", "black": "carpet-black", "grey": "carpet-grey"}
    cube_block("l31-carpet", [{"code": "kind", "states": list(carp)}], {f"*-{k}": {"all": tex31(v)} for k, v in carp.items()},
               "Level 31: carpet (rink: near-black with muted 1990s confetti for halls and lobbies; black: rough black pile outside the rink; "
               "grey: plain office carpet for the employees' lounge)", material="Cloth", sounds=CLOTH)
    fl = {"polished": "floor-polished", "tile": "floor-tile", "quarry": "floor-quarry"}
    cube_block("l31-floor", [{"code": "kind", "states": list(fl)}], {f"*-{k}": {"all": tex31(v)} for k, v in fl.items()},
               "Level 31: floors (polished: freshly cleaned glossy grey concrete; tile: pale blue and white vinyl for the skate rental; "
               "quarry: red-brown kitchen tiles)")
    cube_block("l31-brick", [{"code": "kind", "states": ["plain"]}], {"*": {"all": tex31("brick-plain")}},
               "Level 31: exposed red-brown brick with mortar")


# ======================================================================== Sign cubes (the picture on one face)

def sheet(img, box_, col=(236, 234, 224), shadow=True, rot=0.0, draw=None):
    """A paper sheet (x0,y0,x1,y1) on img, optionally turned a little; draw(layer) paints its lettering on a 64 px layer."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box_
    if shadow:
        R(layer, x0 + 2, y0 + 2, x1 + 2, y1 + 2, (0, 0, 0, 90))
    R(layer, x0, y0, x1, y1, col)
    R(layer, x0, y0, x1, y0, shade(col, 1.06))
    R(layer, x0, y1, x1, y1, shade(col, 0.86))
    if draw:
        draw(layer)
    if rot:
        layer = layer.rotate(rot, center=((x0 + x1) / 2, (y0 + y1) / 2), resample=Image.NEAREST)
    img.alpha_composite(layer)


def tape(img, cx, cy, ang, length=9, col=(226, 214, 160, 200)):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([cx - length // 2, cy - 2, cx + length // 2, cy + 2], fill=col)
    layer = layer.rotate(ang, center=(cx, cy), resample=Image.NEAREST)
    img.alpha_composite(layer)


def sign_trash():
    img = bg_texture("wall-plain")
    ink = (28, 30, 56)

    def lettering(layer):
        for i, ln in enumerate(("PLEASE THROW", "AWAY TRASH", "AND UNEATEN", "FOOD HERE!")):
            ctext(layer, 32, 8 + i * 13, ln, ink, sx=1, sy=2)
    sheet(img, (6, 4, 57, 59), draw=lettering, rot=1.5)
    for (cx, cy, a) in ((9, 7, 40), (54, 7, -40), (9, 56, -40), (54, 56, 40)):
        tape(img, cx, cy, a)
    return img


def sign_outoforder():
    img = bg_texture(MIDNIGHT)
    ink = (14, 14, 16)

    def lettering(layer):
        ctext(layer, 32, 15, "OUT OF", ink, sx=2, bold=True, jitter=1, seed=7)
        ctext(layer, 32, 31, "ORDER", ink, sx=2, bold=True, jitter=1, seed=8)
        line(layer, (11, 46), (53, 45), ink, 1)
        line(layer, (13, 48), (51, 47), ink, 1)
    sheet(img, (5, 11, 58, 52), col=(238, 234, 214), draw=lettering, rot=-3.5)
    tape(img, 10, 13, 35)
    tape(img, 53, 12, -35)
    return img


def sign_menu():
    img = new(PIC, col=(14, 14, 18))
    R(img, 0, 0, 63, 63, (40, 40, 48))
    R(img, 1, 1, 62, 62, (12, 12, 16))
    outline(img, 2, 2, 61, 61, (90, 40, 150))
    text(img, 6, 5, "PIZZA", (255, 200, 40), sx=2)
    disc(img, 52, 10, 6, (214, 150, 60))
    disc(img, 52, 10, 5, (252, 206, 70))
    for (a, b) in ((49, 8), (54, 11), (50, 13)):
        disc(img, a, b, 1, (210, 50, 40))
    text(img, 6, 18, "CHEESE", (240, 240, 240))
    text(img, 6, 24, "PEPPERONI", (240, 240, 240))
    disc(img, 49, 20, 2, (252, 206, 70))
    disc(img, 49, 26, 2, (210, 50, 40))
    R(img, 5, 30, 58, 30, (90, 40, 150))
    text(img, 6, 33, "WINGS", (255, 110, 50), sx=2)
    disc(img, 52, 36, 4, (196, 104, 40))
    line(img, (54, 39), (58, 43), (232, 226, 210), 2)
    R(img, 5, 45, 58, 45, (90, 40, 150))
    text(img, 6, 48, "FOOT-LONG", (110, 230, 255))
    text(img, 6, 54, "HOT DOGS", (110, 230, 255))
    R(img, 44, 47, 57, 50, (212, 160, 80))
    R(img, 45, 48, 56, 49, (200, 60, 50))
    R(img, 44, 47, 57, 47, (232, 184, 100))
    R(img, 41, 54, 44, 58, (230, 60, 60))
    R(img, 40, 53, 45, 53, (240, 240, 240))
    line(img, (43, 52), (45, 50), (250, 250, 250))
    text(img, 46, 53, "SODA", (255, 120, 220))
    return img


def faded(img, amount=0.28):
    """Age a poster: pull its colours toward a yellowed grey and add a fold crease."""
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            l = (r + g + b) / 3
            c = mixc((r, g, b), (min(255, l + 24), min(255, l + 18), l * 0.86 + 6), amount)
            px[x, y] = c + (255,)
    for y in range(h):
        r, g, b, a = px[w // 2, y]
        px[w // 2, y] = (M.clamp(r * 1.12), M.clamp(g * 1.12), M.clamp(b * 1.1), 255)
    for x in range(w):
        r, g, b, a = px[x, h // 2]
        px[x, h // 2] = (M.clamp(r * 0.88), M.clamp(g * 0.88), M.clamp(b * 0.9), 255)
    return img


def poster(bg_name, top, bottom, draw):
    img = bg_texture(bg_name)
    p = new(PIC, col=top)
    pp = p.load()
    for y in range(PIC):
        c = mixc(top, bottom, y / (PIC - 1))
        for x in range(PIC):
            pp[x, y] = c + (255,)
    draw(p)
    faded(p)
    x0, y0, x1, y1 = 4, 2, 59, 61
    R(img, x0 + 1, y0 + 1, x1 + 1, y1 + 1, (0, 0, 0, 80))
    img.paste(p.crop((x0, y0, x1 + 1, y1 + 1)), (x0, y0))
    outline(img, x0, y0, x1, y1, (226, 224, 214))
    poly(img, [(x1 - 5, y1), (x1, y1), (x1, y1 - 5)], bg_texture(bg_name).getpixel((50, 50))[:3])
    poly(img, [(x1 - 5, y1), (x1, y1 - 5), (x1 - 5, y1 - 5)], (212, 208, 196))
    return img


def ad_skeeter(p):
    ctext(p, 32, 6, "SKEETER", (255, 236, 80), sx=2)
    ctext(p, 32, 18, "WHEELS", (80, 240, 255), sx=2)
    R(p, 14, 36, 34, 47, (246, 246, 250))
    R(p, 28, 28, 38, 40, (246, 246, 250))
    R(p, 28, 28, 38, 30, (220, 60, 170))
    R(p, 14, 44, 44, 47, (226, 226, 232))
    R(p, 30, 36, 46, 45, (246, 246, 250))
    line(p, (16, 40), (36, 40), (220, 60, 170), 2)
    for k in range(5):
        line(p, (30 + k % 2 * 2, 30 + k * 2), (35, 31 + k * 2), (150, 150, 160))
    R(p, 13, 48, 46, 49, (90, 90, 110))
    for cx in (17, 25, 35, 43):
        disc(p, cx, 52, 3, (255, 214, 40))
        disc(p, cx, 52, 1, (200, 120, 20))
    for i, y in enumerate((34, 38, 42, 46)):
        line(p, (2, y), (10 - i % 2 * 2, y), (255, 255, 255))
    ctext(p, 32, 57, "ROLL FAST!", (255, 255, 255))


def ad_fizzbo(p):
    ctext(p, 32, 5, "FIZZBO", (255, 255, 255), sx=2)
    R(p, 20, 20, 43, 54, (232, 236, 240))
    R(p, 20, 20, 43, 23, (200, 204, 210))
    R(p, 20, 51, 43, 54, (200, 204, 210))
    R(p, 20, 28, 43, 46, (240, 240, 245))
    poly(p, [(20, 34), (30, 28), (43, 36), (43, 40), (30, 33), (20, 40)], (250, 220, 40))
    ctext(p, 32, 42, "POP", (220, 30, 40), sx=1)
    for (x, y, r) in ((9, 40, 3), (13, 30, 2), (7, 24, 2), (50, 44, 3), (54, 32, 2), (48, 24, 2), (55, 52, 2), (10, 52, 2)):
        disc(p, x, y, r, (255, 255, 255))
        disc(p, x - 1, y - 1, max(0, r - 2), (255, 140, 150))
    ctext(p, 32, 57, "TRY THE POP!", (255, 240, 120))


def ad_krunch(p):
    ctext(p, 32, 5, "KRUNCH", (255, 244, 90), sx=2)
    ctext(p, 32, 17, "-O'S", (255, 255, 255), sx=2)
    poly(p, [(16, 28), (47, 28), (50, 56), (13, 56)], (230, 70, 40))
    for x in range(16, 48, 3):
        line(p, (x, 28), (x + 1, 32), (250, 130, 90))
    R(p, 15, 36, 48, 47, (255, 214, 60))
    ctext(p, 32, 40, "CRUNCH", (200, 40, 30))
    for (x, y) in ((22, 51), (32, 52), (41, 51)):
        disc(p, x, y, 3, (250, 200, 70))
        disc(p, x, y, 1, (230, 70, 40))
    for (x, y) in ((6, 40), (57, 38), (8, 52), (56, 52)):
        disc(p, x, y, 2, (250, 200, 70))
        disc(p, x, y, 1, (200, 90, 30))


def door_art(low, white):
    """Lower / upper half of a closed door with its frame, on the wall texture it belongs to."""
    img = bg_texture(MIDNIGHT if white else "wall-plain")
    fr = (232, 230, 222) if white else (74, 78, 86)
    leaf = (240, 238, 230) if white else (150, 156, 164)
    hinge = (190, 160, 70) if white else (120, 124, 130)
    R(img, 5, 0, 58, 63, fr)
    R(img, 5, 0, 5, 63, shade(fr, 1.1))
    R(img, 58, 0, 58, 63, shade(fr, 0.8))
    y0 = 0 if low else 4
    if not low:
        R(img, 5, 3, 58, 3, shade(fr, 0.8))
    R(img, 9, y0, 54, 63, leaf)
    px = img.load()
    for y in range(y0, 64):
        for x in range(9, 55):
            r, g, b, a = px[x, y]
            k = 1.0 + (0.05 if x < 14 else 0) - (0.06 if x > 48 else 0) + 0.015 * math.sin(y * 0.9 + x * 0.1)
            px[x, y] = (M.clamp(r * k), M.clamp(g * k), M.clamp(b * k), 255)
    R(img, 8, y0, 8, 63, shade(fr, 0.6))
    R(img, 55, y0, 55, 63, shade(fr, 0.6))
    if not low:
        R(img, 9, 4, 54, 4, shade(leaf, 0.7))
    # raised panels on the wooden door
    if white:
        for (a, b, c, d) in ((14, 6 if low else 10, 49, 28), (14, 34, 49, 58)):
            R(img, a, b, c, d, shade(leaf, 0.95))
            R(img, a, b, c, b, shade(leaf, 0.82))
            R(img, a, b, a, d, shade(leaf, 0.82))
            R(img, a, d, c, d, shade(leaf, 1.06))
            R(img, c, b, c, d, shade(leaf, 1.06))
    if low:
        for hy in (8, 52):
            R(img, 9, hy, 10, hy + 4, hinge)
        if white:
            disc(img, 47, 8, 3, (214, 178, 76))
            disc(img, 46, 7, 1, (250, 232, 150))
            R(img, 44, 17, 50, 21, (214, 178, 76))
            R(img, 46, 19, 47, 20, (60, 50, 20))
        else:
            R(img, 41, 6, 51, 9, (36, 38, 44))
            R(img, 41, 6, 51, 6, (86, 90, 98))
            R(img, 46, 14, 50, 18, (180, 184, 190))
            R(img, 48, 15, 48, 17, (40, 40, 44))
            R(img, 9, 52, 54, 63, (110, 114, 122))
            R(img, 9, 52, 54, 52, (170, 174, 182))
            for sx in (11, 52):
                for sy in (54, 61):
                    img.putpixel((sx, sy), (60, 60, 66, 255))
    else:
        for hy in (8, 48):
            R(img, 9, hy, 10, hy + 4, hinge)
        if white:
            # "70" cut into the leaf: a lit lower edge, a dark groove
            ctext(img, 33, 15, "70", shade(leaf, 1.1), sx=4, sy=5, bold=True)
            ctext(img, 32, 14, "70", (150, 140, 118), sx=4, sy=5, bold=True)
        else:
            R(img, 13, 20, 50, 40, (206, 206, 200))
            outline(img, 13, 20, 50, 40, (110, 112, 116))
            R(img, 14, 21, 49, 21, (240, 240, 236))
            for (sx, sy) in ((15, 22), (48, 22), (15, 38), (48, 38)):
                img.putpixel((sx, sy), (80, 80, 86, 255))
            ctext(img, 32, 25, "EMPLOYEES", (150, 24, 28))
            ctext(img, 32, 32, "ONLY!", (150, 24, 28))
    return img


def signs():
    faces = {
        "trash": sign_trash(),
        "outoforder": sign_outoforder(),
        "menu": sign_menu(),
        "ad1": poster("wall-blue", (140, 50, 190), (230, 70, 150), ad_skeeter),
        "ad2": poster("wall-blue", (200, 30, 50), (250, 120, 60), ad_fizzbo),
        "ad3": poster("wall-blue", (250, 170, 30), (230, 90, 40), ad_krunch),
        "staffdoorlow": door_art(True, False),
        "staffdoorhigh": door_art(False, False),
        "door70low": door_art(True, True),
        "door70high": door_art(False, True),
    }
    back = {"trash": "wall-plain", "menu": "wall-plain", "staffdoorlow": "wall-plain", "staffdoorhigh": "wall-plain",
            "ad1": "wall-blue", "ad2": "wall-blue", "ad3": "wall-blue"}
    textures_ = {}
    for kind, img in faces.items():
        save(img, "sign-" + kind)
        b = tex31(back[kind]) if kind in back else {"base": "block/3999/wall-midnight"}
        for side in SIDES:
            t = {f: b for f in SIDES + ["up", "down"]}
            t[side] = tex31("sign-" + kind)
            textures_[f"*-{kind}-{side}"] = t
    extra = {"vertexFlagsByType": {"*-menu-*": {"glowLevel": 90}}}
    cube_block("l31-sign", [{"code": "kind", "states": list(faces)}, {"code": "side", "states": SIDES}], textures_,
               "Level 31: wall blocks with a picture on one face (the side): a taped trash sign, an out-of-order sheet, a backlit food menu, "
               "three faded posters, a grey steel staff door (low/high halves) and a white wooden door numbered 70 (low/high halves)",
               extra=extra)


# ======================================================================== Furniture: chair, table, bench, condiments

def flat(name, base, seed, sheen=0.0, amount=2):
    img = plastic(base, seed, sheen) if sheen else M.noise_hv(base, amount, seed, S, 3, (8, 4))
    save(img, name)


def chair():
    flat("chair-plastic", (232, 116, 30), 3301, sheen=0.14)
    els = []
    P = "chair-plastic"
    els.append(B("Seat", (3.5, 6.6, 3.5), (12.5, 7.8, 12.0), P))
    els.append(B("SeatLip", (3.8, 7.8, 3.5), (12.2, 8.2, 4.3), P, faces=without(DIRS, "down")))
    els.append(B("BackMid", (4.6, 8.4, 11.6), (11.4, 14.8, 12.8), P))
    els.append(B("BackL", (3.7, 8.4, 11.0), (4.6, 14.2, 12.8), P))
    els.append(B("BackR", (11.4, 8.4, 11.0), (12.3, 14.2, 12.8), P))
    els.append(B("SeatBack", (3.7, 7.8, 11.0), (12.3, 8.4, 12.0), P, faces=without(DIRS, "down")))
    for i, (x, z, top) in enumerate(((4.4, 4.4, 6.6), (11.6, 4.4, 6.6), (4.4, 11.4, 6.6), (11.6, 11.4, 6.6))):
        els.append(B(f"Leg{i}", (x - 0.4, 0, z - 0.4), (x + 0.4, top, z + 0.4), "mat-chrome", faces=without(DIRS, "up")))
    els.append(B("StretchL", (4.0, 2.4, 4.8), (4.8, 3.2, 11.0), "mat-chrome", faces=without(DIRS, "west", "east")))
    els.append(B("StretchR", (11.2, 2.4, 4.8), (12.0, 3.2, 11.0), "mat-chrome", faces=without(DIRS, "west", "east")))
    els.append(B("StretchB", (4.8, 2.4, 11.0), (11.2, 3.2, 11.8), "mat-chrome", faces=without(DIRS, "north", "south")))
    return shape("l31-chair", els)


def table():
    img = M.noise_hv((228, 228, 224), 2, 3311, S, 3, (8, 4))
    px = img.load()
    rng = random.Random(3312)
    for _ in range(40):  # laminate flecks
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = (150, 156, 162, 255) if rng.random() < 0.6 else (250, 250, 250, 255)
    save(img, "table-laminate")
    els = [B("Top", (1, 11, 1), (15, 12, 15), mat(top="table-laminate", side="mat-chrome", bottom="mat-chrome")),
           B("Pole", (7.1, 1, 7.1), (8.9, 11, 8.9), "mat-chrome", faces=without(DIRS, "up", "down")),
           B("Collar", (6.6, 9.6, 6.6), (9.4, 11, 9.4), "mat-chrome", faces=without(DIRS, "up")),
           B("Foot", (3.5, 0, 3.5), (12.5, 0.6, 12.5), "mat-chrome"),
           B("FootTop", (5, 0.6, 5), (11, 1.2, 11), "mat-chrome", faces=without(DIRS, "down")),
           ]
    return shape("l31-table", els)


def bench():
    refs = {}
    for colour, base in (("orange", (226, 108, 28)), ("green", (36, 140, 78))):
        flat("bench-" + colour, base, 3321 + len(colour), sheen=0.06)
        P = "bench-" + colour
        els = []
        for i, z in enumerate((3.0, 5.8, 8.6)):
            els.append(B(f"Seat{i}", (0, 6.3, z), (16, 7.3, z + 2.5), P))
        for i, y in enumerate((8.6, 10.9, 13.2)):
            els.append(B(f"Back{i}", (0, y, 11.2), (16, y + 1.9, 12.1), P))
        for sx, tag in ((1.0, "L"), (13.8, "R")):
            els.append(B("Front" + tag, (sx, 0.4, 3.3), (sx + 1.2, 6.3, 4.5), "mat-dark"))
            els.append(B("Rear" + tag, (sx, 0.4, 12.1), (sx + 1.2, 15.0, 13.3), "mat-dark"))
            els.append(B("Rail" + tag, (sx, 5.3, 4.5), (sx + 1.2, 6.3, 12.1), "mat-dark", faces=without(DIRS, "north", "south")))
            for fz, ftag in ((2.9, "F"), (12.0, "R")):
                els.append(B(f"Foot{tag}{ftag}", (sx - 0.5, 0, fz), (sx + 1.7, 0.4, fz + 2.0), "mat-dark"))
                els.append(B(f"Bolt{tag}{ftag}", (sx + 0.1, 0.4, fz + 1.65), (sx + 1.1, 0.7, fz + 1.95), "mat-steel", faces=without(DIRS, "down")))
        refs[colour] = shape("l31-bench-" + colour, els)
    return refs


def bottle_tex(name, base, seed, label):
    img = M.noise_hv(base, 2, seed, S, 3, (8, 4))
    R(img, 0, 10, 31, 22, label)
    R(img, 0, 10, 31, 10, shade(label, 0.8))
    R(img, 0, 22, 31, 22, shade(label, 0.8))
    for x in (4, 9, 14, 20):
        R(img, x, 14, x + 2, 17, shade(base, 0.7))
    save(img, name)


def condiments():
    for n, b, lab, seed in (("red", (200, 28, 30), (240, 232, 214), 3331), ("yellow", (238, 200, 30), (240, 232, 214), 3332),
                            ("green", (60, 150, 52), (240, 232, 214), 3333)):
        bottle_tex("bottle-" + n, b, seed, lab)
    img = new(PIC, col=(150, 154, 160))
    R(img, 2, 3, 12, 30, (28, 28, 32))      # the dispenser's face: a dark slot full of napkins
    for y in range(5, 29, 3):
        R(img, 3, y, 11, y + 1, (238, 236, 228))
        R(img, 3, y + 2, 11, y + 2, (196, 194, 186))
    R(img, 2, 3, 12, 4, (60, 60, 66))
    save(img, "napkin-front")
    cup = M.noise_hv((200, 40, 44), 2, 3334, S, 3, (8, 4))
    R(cup, 0, 12, 31, 14, (250, 250, 250))
    save(cup, "cup-red")
    st = new(8, 32, (250, 250, 250))
    for y in range(0, 32, 4):
        R(st, 0, y, 7, y + 1, (220, 40, 50))
    save(st, "straw")
    els = [B("Tray", (1.2, 0, 3.5), (14.8, 1.2, 12.5), "mat-steel"),
           B("RimN", (1.2, 1.2, 3.5), (14.8, 1.8, 4.0), "mat-steel", faces=without(DIRS, "down")),
           B("RimS", (1.2, 1.2, 12.0), (14.8, 1.8, 12.5), "mat-steel", faces=without(DIRS, "down")),
           B("RimW", (1.2, 1.2, 4.0), (1.7, 1.8, 12.0), "mat-steel", faces=without(DIRS, "down", "north", "south")),
           B("RimE", (14.3, 1.2, 4.0), (14.8, 1.8, 12.0), "mat-steel", faces=without(DIRS, "down", "north", "south"))]
    for i, (n, cx) in enumerate((("red", 3.2), ("yellow", 6.4), ("green", 9.6))):
        k = "bottle-" + n
        cz = 9.6
        els.append(B(f"Bottle{i}", (cx - 1.4, 1.2, cz - 1.4), (cx + 1.4, 9.6, cz + 1.4), k, north=(k, [0, 0, 16, 16])))
        els.append(B(f"Shoulder{i}", (cx - 0.9, 9.6, cz - 0.9), (cx + 0.9, 10.4, cz + 0.9), k))
        els.append(B(f"Collar{i}", (cx - 0.8, 10.4, cz - 0.8), (cx + 0.8, 11.2, cz + 0.8), "mat-chrome"))
        els.append(B(f"Shaft{i}", (cx - 0.3, 11.2, cz - 0.3), (cx + 0.3, 12.8, cz + 0.3), "mat-chrome", faces=without(DIRS, "up", "down")))
        els.append(B(f"Head{i}", (cx - 0.6, 12.8, cz - 1.9), (cx + 0.6, 13.9, cz + 0.7), k))
    els.append(B("Napkins", (11.0, 1.2, 4.6), (14.4, 10.2, 10.6), "mat-steel", north=("napkin-front", pic_uv(3.4, 8.4)),
                 up="mat-steel"))
    els.append(B("Cup", (2.0, 1.2, 4.6), (5.6, 4.6, 8.0), "cup-red"))
    for i, (sx, sz, top) in enumerate(((2.8, 5.4, 8.6), (3.8, 6.4, 8.0), (4.6, 5.6, 8.8), (3.3, 7.0, 7.6), (4.8, 6.9, 8.3))):
        els.append(B(f"Straw{i}", (sx, 4.4, sz), (sx + 0.5, top, sz + 0.5), "straw", faces=without(DIRS, "down")))
    return shape("l31-condiments", els)


# ======================================================================== Soda fountain

def fountain():
    # counter laminate with door seams and a dark kick plate (rows 0-19 are the 10 units of the front)
    img = M.noise_hv((214, 208, 190), 2, 3341, S, 3, (8, 4))
    R(img, 0, 17, 31, 19, (46, 44, 48))
    for x in (0, 15, 16, 31):
        R(img, x, 0, x, 16, (150, 144, 128))
    R(img, 0, 0, 31, 0, (236, 232, 218))
    for (x0, x1) in ((3, 12), (19, 28)):
        outline(img, x0, 3, x1, 13, (176, 170, 154))
        R(img, x1 - 3, 8, x1 - 2, 9, (96, 96, 102))
    save(img, "counter-front")
    top = M.noise_hv((92, 96, 104), 2, 3342, S, 3, (8, 4))
    save(top, "counter-top")
    # the lit tap panels: four labels, each a coloured field with a dark lettering block
    lit = new(PIC, col=(30, 30, 34))
    for i, c in enumerate(((250, 150, 30), (210, 40, 50), (70, 190, 70), (150, 60, 200))):
        x0 = 1 + i * 10
        R(lit, x0, 1, x0 + 8, 9, c)
        R(lit, x0, 1, x0 + 8, 1, shade(c, 1.2))
        R(lit, x0 + 2, 4, x0 + 6, 6, (250, 250, 240))
        disc(lit, x0 + 4, 8, 1, shade(c, 0.7))
    save(lit, "fountain-lit")
    grille = new(S, col=(40, 40, 46))
    for y in range(0, S, 2):
        R(grille, 0, y, 31, y, (100, 102, 110))
    save(grille, "fountain-grille")
    els = [B("Base", (0, 0, 1), (16, 9, 15), mat(side="counter-front", top="counter-top"),
             north=("counter-front", [0, 0, 16, 10]), south=("counter-front", [0, 0, 16, 10]),
             east=("counter-front", [0, 0, 14, 10]), west=("counter-front", [0, 0, 14, 10])),
           B("Slab", (0, 9, 0.5), (16, 10, 15.5), mat(top="counter-top", side="mat-steel", bottom="mat-steel"),
             north=("mat-steel", [0, 0, 16, 1]), south=("mat-steel", [0, 0, 16, 1])),
           B("Tower", (2.5, 10, 5), (13.5, 16, 12.5), "mat-chrome", north="mat-dark"),
           B("Lit", (3, 13, 4.7), (13, 15.6, 5), "fountain-lit", faces=("north",), glow=170, north=("fountain-lit", pic_uv(10, 2.6), 170)),
           B("Tray", (2.5, 10, 2.4), (13.5, 10.7, 5), "mat-dark", up=("fountain-grille", [0, 0, 11, 3])),
           B("TrayLip", (2.5, 10.7, 2.4), (13.5, 11.3, 2.9), "mat-chrome", faces=without(DIRS, "down")),
           ]
    for i, cx in enumerate((3.9, 6.6, 9.4, 12.1)):
        els.append(B(f"Nozzle{i}", (cx - 0.5, 11.3, 3.3), (cx + 0.5, 12.6, 5), "mat-chrome", faces=without(DIRS, "south", "up")))
        els.append(B(f"NozzleTip{i}", (cx - 0.35, 11.0, 3.45), (cx + 0.35, 11.3, 4.15), "mat-dark", faces=without(DIRS, "up")))
    return shape("l31-fountain", els)


# ======================================================================== DJ desk and speaker

def djdesk():
    front = M.painted_metal(seed=3351, base=(26, 26, 32), panel=False, chips=0)
    R(front, 1, 1, 30, 25, (30, 30, 37))
    outline(front, 1, 1, 30, 25, (14, 14, 18))
    for y in range(4, 24, 2):
        for x in range(4, 28, 3):
            front.putpixel((x, y), (50, 50, 60, 255))
    save(front, "dj-front")
    save(M.painted_metal(seed=3352, base=(22, 22, 26), panel=False, chips=2), "dj-top")
    for n, c in (("magenta", (255, 70, 200)), ("cyan", (70, 235, 255))):
        img = new(S, col=shade(c, 0.7))
        R(img, 0, 2, 31, 3, c)
        R(img, 0, 2, 31, 2, (255, 255, 255))
        save(img, "neon-" + n)
    # the record: 36 px across (9 units) painted in the 64 px texture, grooved, with a coloured label and a spindle hole
    rec = new(PIC, col=(18, 18, 22))
    d = ImageDraw.Draw(rec)
    for r in range(18, 7, -1):
        d.ellipse([18 - r, 18 - r, 18 + r, 18 + r], fill=(20 + (r % 3) * 5, 20 + (r % 3) * 5, 24 + (r % 3) * 5, 255))
    disc(rec, 18, 18, 7, (214, 40, 70))
    disc(rec, 18, 18, 5, (244, 190, 40))
    disc(rec, 18, 18, 1, (10, 10, 10))
    line(rec, (8, 6), (14, 3), (80, 80, 96))
    save(rec, "record")
    mix = new(PIC, col=(26, 26, 30))
    R(mix, 0, 0, 43, 43, (26, 26, 30))
    outline(mix, 0, 0, 43, 43, (70, 70, 80))
    chan_u = [1.4 + 1.65 * i for i in range(6)]
    caps_v = [7.8, 6.5, 8.6, 7.2, 8.2, 6.8]
    for i, u in enumerate(chan_u):
        px_ = int(u * 4)
        R(mix, px_, 24, px_, 38, (8, 8, 10))                     # the fader slot
        for k, c in enumerate(((240, 60, 60), (240, 200, 50), (60, 200, 240))):
            disc(mix, px_, 5 + k * 5, 2, (210, 210, 214))
            disc(mix, px_, 5 + k * 5, 1, c)
        for k in range(4):                                       # level lights
            R(mix, px_ - 1, 21 - k * 2 + 6 - 6, px_ + 1, 21 - k * 2, (60, 230, 90) if k < 3 else (240, 60, 50))
    R(mix, 8, 41, 36, 42, (8, 8, 10))                            # the crossfader slot
    save(mix, "mixer-top")
    save(M.painted_metal(seed=3353, base=(30, 30, 34), panel=False, chips=0), "deck-plinth")
    out = {}
    # --- common desk
    def desk():
        return [B("Body", (0, 0, 2), (16, 13, 14), mat(side="mat-dark", top="mat-dark"), north=("dj-front", [0, 0, 16, 13])),
                B("Top", (0, 13, 1), (16, 14, 15), mat(top="dj-top", side="mat-dark", bottom="mat-dark")),
                B("NeonA", (1, 4.5, 1.5), (15, 5.4, 2), "neon-magenta", faces=("north", "up", "down", "east", "west"), glow=220),
                B("NeonB", (1, 7.2, 1.5), (15, 8.1, 2), "neon-cyan", faces=("north", "up", "down", "east", "west"), glow=220)]
    els = desk()
    els.append(B("Plinth", (1.5, 14, 2.5), (14.5, 14.8, 13.5), mat(top="deck-plinth", side="mat-dark")))
    els.append(B("Platter", (2, 14.8, 3), (12, 15.2, 13), "mat-steel"))
    rv = lambda x0, z0, x1, z1: [x0 - 2.5, z0 - 3.5, x1 - 2.5, z1 - 3.5]
    for tag, (x0, z0, x1, z1) in (("Mid", (2.5, 6.1, 11.5, 9.9)), ("N", (5.1, 3.5, 8.9, 6.1)), ("S", (5.1, 9.9, 8.9, 12.5))):
        els.append(B("Rec" + tag, (x0, 15.2, z0), (x1, 15.6, z1), "mat-black", up=("record", rv(x0, z0, x1, z1))))
    els.append(B("Spindle", (6.8, 15.6, 7.8), (7.2, 16, 8.2), "mat-chrome", faces=without(DIRS, "down")))
    els.append(B("ArmBase", (12.3, 14.8, 3.2), (14.3, 15.8, 5.2), "mat-chrome"))
    els.append(B("Arm", (12.9, 15.3, 4.6), (13.5, 15.7, 11.0), "mat-chrome", rot=(0, -14, 0), origin=(13.2, 15.5, 4.8)))
    els.append(B("Start", (13.0, 14.8, 11.8), (14.0, 15.3, 12.8), "mat-white"))
    out["deck"] = shape("l31-djdesk-deck", els)
    els = desk()
    els.append(B("Mix", (2.5, 14, 2.5), (13.5, 15.2, 13.5), mat(side="mat-dark", bottom="mat-dark"), up=("mixer-top", pic_uv(11, 11))))
    els.append(B("Strip", (3, 14.8, 2.1), (13, 15.2, 2.5), "neon-cyan", faces=("north", "up", "east", "west"), glow=220))
    for i, (u, v) in enumerate(zip(chan_u, caps_v)):
        x, z = 2.5 + u, 2.5 + v
        els.append(B(f"Cap{i}", (x - 0.45, 15.2, z - 0.6), (x + 0.45, 15.7, z + 0.6), "mat-white", faces=without(DIRS, "down")))
    els.append(B("XFade", (7.0, 15.2, 12.5), (8.6, 15.7, 13.1), "mat-white", faces=without(DIRS, "down")))
    out["mixer"] = shape("l31-djdesk-mixer", els)
    return out


def speaker():
    side = M.painted_metal(seed=3361, base=(24, 24, 28), panel=False, chips=2)
    for (x, y) in ((0, 0), (27, 0), (0, 27), (27, 27)):
        R(side, x, y, x + 4, y + 4, (120, 124, 132))
        R(side, x + 1, y + 1, x + 3, y + 3, (160, 164, 172))
    save(side, "speaker-side")
    front = new(PIC, col=(24, 24, 28))
    R(front, 0, 0, 55, 63, (24, 24, 28))
    outline(front, 0, 0, 55, 63, (96, 100, 108))
    outline(front, 1, 1, 54, 62, (50, 52, 58))
    for (x, y) in ((0, 0), (51, 0), (0, 59), (51, 59)):
        R(front, x, y, x + 4, y + 4, (120, 124, 132))
        R(front, x + 1, y + 1, x + 3, y + 3, (166, 170, 178))
    R(front, 18, 58, 37, 60, (6, 6, 8))                          # the bass port
    outline(front, 17, 57, 38, 61, (70, 72, 80))
    save(front, "speaker-front")
    wf = new(PIC, col=(24, 24, 28))
    d = ImageDraw.Draw(wf)
    d.ellipse([0, 0, 23, 23], fill=(70, 72, 80, 255))
    d.ellipse([2, 2, 21, 21], fill=(14, 14, 16, 255))
    d.ellipse([3, 3, 20, 20], fill=(36, 36, 40, 255))
    for r in (9, 7, 5):
        d.ellipse([12 - r, 12 - r, 11 + r, 11 + r], outline=(52, 52, 58, 255))
    d.ellipse([8, 8, 15, 15], fill=(18, 18, 22, 255), outline=(90, 92, 100, 255))
    save(wf, "speaker-woofer")
    horn = new(PIC, col=(8, 8, 10))
    outline(horn, 0, 0, 27, 15, (160, 164, 172))
    outline(horn, 1, 1, 26, 14, (100, 104, 112))
    for x in range(4, 26, 4):
        line(horn, (14, 8), (x, 1), (46, 46, 52))
        line(horn, (14, 8), (x, 14), (46, 46, 52))
    disc(horn, 14, 8, 3, (20, 20, 24))
    save(horn, "speaker-horn")
    els = [B("Cab", (1, 0, 2), (15, 16, 14), mat(side="speaker-side", top="speaker-side", bottom="mat-dark"),
             north=("speaker-front", pic_uv(14, 16))),
           B("Horn", (4.5, 11.2, 1.0), (11.5, 15.2, 2.0), "mat-dark", north=("speaker-horn", pic_uv(7, 4))),
           B("Wf1", (1.7, 3.6, 1.5), (7.7, 9.6, 2.0), "mat-dark", north=("speaker-woofer", pic_uv(6, 6))),
           B("Wf2", (8.3, 3.6, 1.5), (14.3, 9.6, 2.0), "mat-dark", north=("speaker-woofer", pic_uv(6, 6)))]
    return shape("l31-speaker", els)


# ======================================================================== Gate, star light, card dispenser

def gate():
    wood = M.wood_planks(seed=3401, base=(214, 170, 108), planks=2, direction="h", grain=3, flecks=0.6)
    save(wood, "gate-wood")
    save(M.wood_planks(seed=3402, base=(176, 128, 78), planks=1, direction="v", grain=3, flecks=0.6), "gate-post")
    els = []
    for x0, tag in ((0.2, "W"), (14.2, "E")):
        els.append(B("Post" + tag, (x0, 0, 7.2), (x0 + 1.6, 11, 8.8), "gate-post", faces=without(DIRS, "down")))
        els.append(B("Cap" + tag, (x0 - 0.2, 11, 7.0), (x0 + 1.8, 11.6, 9.0), "gate-post"))
    flap = [B("StileW", (1.8, 2.6, 7.6), (3.2, 9.8, 8.4), "gate-wood"),
            B("StileE", (12.8, 2.6, 7.6), (14.2, 9.8, 8.4), "gate-wood"),
            B("RailT", (3.2, 7.8, 7.6), (12.8, 9.8, 8.4), "gate-wood", faces=without(DIRS, "east", "west")),
            B("RailB", (3.2, 2.6, 7.6), (12.8, 4.6, 8.4), "gate-wood", faces=without(DIRS, "east", "west")),
            B("Brace", (3.0, 5.4, 7.7), (13.0, 6.2, 8.3), "gate-wood", rot=(0, 0, 17.3), origin=(8, 5.8, 8)),
            B("Latch", (12.0, 5.8, 7.4), (12.8, 6.8, 8.6), "mat-steel"),
            B("HingeA", (1.6, 3.4, 7.4), (2.4, 4.4, 8.6), "mat-steel"),
            B("HingeB", (1.6, 8.0, 7.4), (2.4, 9.0, 8.6), "mat-steel")]
    return {"we": shape("l31-gate-we", els + flap), "ns": shape("l31-gate-ns", turn(els + flap, 1))}


def star():
    for n, c in (("tube", (255, 240, 205)), ("edge", (255, 120, 190))):
        img = new(S, col=c)
        R(img, 0, 0, 31, 1, shade(c, 1.0))
        save(noise(img, 3, 3411), "star-" + n)
    R_, r_ = 23.0, 23.0 * 0.382
    cx = cz = 8.0
    pts = []
    for k in range(5):
        a = math.radians(72 * k)
        pts.append((cx + R_ * math.sin(a), cz - R_ * math.cos(a)))
        a2 = math.radians(72 * k + 36)
        pts.append((cx + r_ * math.sin(a2), cz - r_ * math.cos(a2)))
    els = []

    def seg(name, p, q, y0, h, w, tex_, glow, grow=0.8, faces=DIRS):
        mx, mz = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        dx, dz = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dz) + grow
        ang = math.degrees(math.atan2(-dz, dx))
        return B(name, (mx - L / 2, y0, mz - w / 2), (mx + L / 2, y0 + h, mz + w / 2), tex_, faces=faces, glow=glow,
                 rot=(0, round(ang, 3), 0), origin=(mx, y0 + h / 2, mz))
    for i in range(10):
        p, q = pts[i], pts[(i + 1) % 10]
        o = 0.03 * (i % 2)
        els.append(seg(f"Core{i}", p, q, 13.0 + o, 0.7, 0.8, "star-tube", 220))
        els.append(seg(f"Edge{i}", p, q, 13.7 + o, 0.5, 2.0, "star-edge", 200, faces=without(DIRS, "up")))
    for i in range(0, 10, 2):
        q = pts[i + 1]
        els.append(seg(f"Spoke{i}", (cx, cz), q, 14.2, 0.4, 0.5, "mat-steel", 0, grow=0.0))
    els.append(B("Hub", (6.5, 14.2, 6.5), (9.5, 14.7, 9.5), "mat-steel"))
    els.append(B("Rod", (7.4, 14.7, 7.4), (8.6, 16, 8.6), "mat-steel", faces=without(DIRS, "up", "down")))
    return shape("l31-star", els)


def dispenser():
    body = M.painted_metal(seed=3421, base=(70, 36, 120), panel=False, chips=3)
    save(body, "disp-body")
    front = new(48, 48, (46, 18, 92))
    R(front, 0, 0, 47, 47, (46, 18, 92))
    outline(front, 0, 0, 47, 47, (230, 60, 200))
    outline(front, 1, 1, 46, 46, (90, 40, 170))
    for i, ln in enumerate(("PLEASE", "PRESS THE", "BUTTON TO", "GET A CARD")):
        ctext(front, 24, 4 + i * 6, ln, (210, 250, 255) if i != 3 else (120, 255, 150))
    disc(front, 24, 35, 8, (20, 12, 40))
    disc(front, 24, 35, 7, (60, 100, 230))
    ring = ImageDraw.Draw(front)
    ring.ellipse([16, 27, 32, 43], outline=(255, 120, 230, 255))
    R(front, 8, 42, 39, 46, (8, 6, 16))
    R(front, 14, 40, 33, 45, (60, 210, 90))
    R(front, 14, 40, 33, 41, (170, 255, 190))
    R(front, 16, 43, 24, 43, (20, 120, 50))
    full_ = new(PIC, col=(46, 18, 92))
    full_.paste(front, (0, 0))
    save(full_, "disp-front")
    btn = new(S, col=(40, 90, 230))
    disc(btn, 16, 16, 12, (70, 130, 255))
    disc(btn, 12, 11, 4, (180, 215, 255))
    save(btn, "disp-btn")
    els = [B("Foot", (5.5, 0, 6), (10.5, 0.8, 10), "mat-steel"),
           B("Post", (7, 0.8, 7), (9, 4, 9), "mat-steel", faces=without(DIRS, "down")),
           B("Box", (2, 4, 5), (14, 16, 11), mat(side="disp-body", top="disp-body", bottom="mat-dark"),
             north=("disp-front", pic_uv(12, 12), 50)),
           B("Btn", (6.5, 5.75, 4.4), (9.5, 8.75, 5), "mat-dark", north=("disp-btn", [0, 0, 16, 16], 90))]
    return shape("l31-dispenser", els)


# ======================================================================== Retro arcade cabinets

SPR = {"a": [".#.#.", "#####", "#.#.#"], "b": ["#####", "##.##", ".#.#."], "c": ["#.#.#", ".###.", "#####"], "d": [".###.", "#####", "#...#"]}


def sprite(img, x, y, rows, col, k=1):
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            if v == "#":
                R(img, x + c * k, y + r * k, x + c * k + k - 1, y + r * k + k - 1, col)


def screen_shooter(img):
    rng = random.Random(3501)
    R(img, 0, 0, 35, 29, (4, 6, 22))
    for _ in range(14):
        img.putpixel((rng.randrange(36), rng.randrange(30)), (110, 120, 170, 255))
    for r, (k, c) in enumerate((("a", (240, 70, 200)), ("b", (70, 230, 90)), ("c", (80, 220, 255)), ("d", (255, 220, 70)))):
        for col in range(5):
            sprite(img, 3 + col * 6, 2 + r * 4, SPR[k], c)
    for x in (4, 15, 26):
        R(img, x, 21, x + 4, 22, (60, 200, 80))
        R(img, x, 22, x, 23, (60, 200, 80))
        R(img, x + 4, 22, x + 4, 23, (60, 200, 80))
    R(img, 15, 27, 21, 28, (230, 230, 240))
    R(img, 17, 25, 19, 26, (230, 230, 240))
    R(img, 18, 23, 18, 24, (250, 250, 250))
    R(img, 18, 18, 18, 19, (255, 255, 120))
    R(img, 9, 15, 9, 16, (255, 120, 120))


def screen_barrels(img):
    R(img, 0, 0, 35, 29, (6, 4, 10))
    gird = (230, 70, 50)
    lows = [(28, 24), (21, 17), (14, 10), (7, 4)]
    for i, (y0, y1) in enumerate(lows):
        a, b = ((0, y1), (35, y0)) if i % 2 == 0 else ((0, y0), (35, y1))
        line(img, a, b, gird, 2)
        line(img, (a[0], a[1] + 2), (b[0], b[1] + 2), (150, 36, 30), 1)
    for (x, y0, y1) in ((26, 4, 9), (9, 11, 17), (24, 18, 23), (7, 25, 28), (16, 6, 9)):
        for y in range(y0, y1 + 1):
            img.putpixel((x, y), (80, 230, 250, 255))
            img.putpixel((x + 2, y), (80, 230, 250, 255))
            if y % 2 == 0:
                R(img, x, y, x + 2, y, (80, 230, 250))
    for (x, y) in ((14, 20), (22, 13), (12, 8), (28, 26)):
        disc(img, x, y, 1, (200, 120, 50))
        img.putpixel((x, y), (250, 220, 120, 255))
    R(img, 2, 0, 8, 4, (140, 80, 40))        # the ape
    R(img, 1, 1, 2, 4, (140, 80, 40))
    R(img, 8, 1, 9, 4, (140, 80, 40))
    R(img, 4, 1, 6, 2, (230, 190, 150))
    img.putpixel((4, 1), (0, 0, 0, 255))
    img.putpixel((6, 1), (0, 0, 0, 255))
    R(img, 5, 26, 6, 28, (60, 90, 240))      # the hero
    img.putpixel((5, 25), (250, 200, 160, 255))
    R(img, 5, 27, 6, 27, (230, 50, 50))


def screen_pyramid(img):
    R(img, 0, 0, 35, 29, (8, 0, 26))
    def cube(cx, y, top, left, right):
        poly(img, [(cx, y), (cx + 4, y + 2), (cx, y + 4), (cx - 4, y + 2)], top)
        poly(img, [(cx - 4, y + 3), (cx, y + 5), (cx, y + 9), (cx - 4, y + 7)], left)
        poly(img, [(cx, y + 5), (cx + 4, y + 3), (cx + 4, y + 7), (cx, y + 9)], right)
    lit = {(0, 0), (1, 0), (2, 1), (3, 3), (3, 0), (2, 0)}
    for r in range(4):
        for c in range(r + 1):
            cx = int(18 + (c - r / 2) * 8)
            y = 2 + r * 6
            on = (r, c) in lit
            cube(cx, y, (250, 220, 60) if on else (70, 90, 240), (40, 60, 180), (30, 40, 130))
    # the hopper: an orange blob with a snout and two white eyes, on the second row
    px_, py_ = 22, 4
    disc(img, px_, py_, 3, (250, 130, 30))
    R(img, px_ - 4, py_ + 1, px_ - 3, py_ + 2, (250, 130, 30))
    img.putpixel((px_ - 1, py_ - 1), (255, 255, 255, 255))
    img.putpixel((px_ + 1, py_ - 1), (255, 255, 255, 255))
    R(img, px_ - 1, py_ + 1, px_ + 1, py_ + 1, (200, 60, 20))
    R(img, px_ - 2, py_ + 3, px_ - 1, py_ + 3, (120, 60, 20))
    R(img, px_ + 1, py_ + 3, px_ + 2, py_ + 3, (120, 60, 20))
    for (x, y) in ((3, 12), (33, 12), (3, 22), (33, 22)):
        ImageDraw.Draw(img).ellipse([x - 2, y - 1, x + 2, y + 1], fill=(230, 70, 220, 255))


GAMES = {
    "shooter": {"body": (28, 36, 78), "accent": (80, 230, 255), "screen": screen_shooter, "t1": "STAR", "t2": "RAIDERS", "bg": (6, 8, 40)},
    "barrels": {"body": (112, 26, 28), "accent": (255, 190, 50), "screen": screen_barrels, "t1": "GIRDER", "t2": "GORILLA", "bg": (30, 6, 8)},
    "pyramid": {"body": (62, 30, 104), "accent": (255, 140, 40), "screen": screen_pyramid, "t1": "CUBE", "t2": "HOPPER", "bg": (24, 6, 52)},
}


def retrocab():
    refs = {}
    save(M.painted_metal(seed=3511, base=(28, 28, 32), panel=False, chips=2), "cab-bezel")
    for n, c in (("red", (226, 38, 40)), ("yellow", (250, 214, 50))):
        flat("cab-" + n, c, 3512 + len(n), sheen=0.15)
    # the coin door and its surround: 12 x 15 units painted at 4 px a unit
    coin = new(PIC, col=(30, 30, 34))
    R(coin, 0, 0, 47, 59, (30, 30, 34))
    R(coin, 14, 24, 33, 45, (150, 154, 160))
    outline(coin, 14, 24, 33, 45, (70, 72, 80))
    for x in (18, 27):
        R(coin, x, 28, x + 2, 34, (30, 10, 10))
        R(coin, x + 1, 29, x + 1, 33, (230, 40, 40))
    R(coin, 17, 38, 30, 42, (20, 20, 24))
    R(coin, 6, 52, 41, 53, (12, 12, 14))
    save(coin, "cab-coin")
    for g, d in GAMES.items():
        body = M.painted_metal(seed=3513 + len(g), base=d["body"], panel=False, chips=2)
        R(body, 0, 0, 31, 1, d["accent"])
        R(body, 0, 0, 1, 31, d["accent"])
        save(body, "cab-side-" + g)
        # control panel top (12 x 2.5 units)
        pan = new(PIC, col=shade(d["body"], 0.5))
        R(pan, 0, 0, 47, 9, shade(d["body"], 0.5))
        R(pan, 0, 0, 47, 1, d["accent"])
        for x in (20, 28, 36, 44):
            disc(pan, x, 6, 2, shade(d["accent"], 0.5))
        save(pan, "cab-panel-" + g)
        scr = new(PIC, col=(0, 0, 0))
        sc = new(36, 30, (0, 0, 0))
        d["screen"](sc)
        for y in range(0, 30, 2):          # faint scanlines
            for x in range(36):
                r, gg, b, a = sc.getpixel((x, y))
                sc.putpixel((x, y), (int(r * 0.82), int(gg * 0.82), int(b * 0.82), 255))
        scr.paste(sc, (0, 0))
        save(scr, "cab-screen-" + g)
        mq = new(PIC, col=d["bg"])
        R(mq, 0, 0, 47, 19, d["bg"])
        for y in range(20):
            R(mq, 0, y, 47, y, mixc(d["bg"], shade(d["accent"], 0.5), y / 19))
        outline(mq, 0, 0, 47, 19, d["accent"])
        w1 = textw(d["t1"], 2)
        ctext(mq, 24, 3, d["t1"], (255, 255, 255), sx=2)
        ctext(mq, 24, 14, d["t2"], d["accent"])
        if w1 <= 32:
            for k in range(4):
                sprite(mq, 38 + k % 2 * 4, 4 + k // 2 * 4, ["#.#", ".#.", "#.#"], shade(d["accent"], 0.9))
        save(mq, "cab-marquee-" + g)
        side = "cab-side-" + g
        els = [
            B("Lower", (2, 0, 4), (14, 15, 15), mat(side=side, top=side, bottom="mat-dark"), north=("cab-coin", pic_uv(12, 15))),
            B("Panel", (2, 13, 1.5), (14, 15, 4), mat(side=side, bottom="mat-dark"), up=("cab-panel-" + g, pic_uv(12, 2.5))),
            B("Mid", (2, 15, 6), (14, 25, 15), side),
            B("BzL", (2, 15, 4.6), (3.5, 25, 6), "cab-bezel"),
            B("BzR", (12.5, 15, 4.6), (14, 25, 6), "cab-bezel"),
            B("BzB", (3.5, 15, 4.6), (12.5, 16.5, 6), "cab-bezel", faces=without(DIRS, "east", "west")),
            B("BzT", (3.5, 24, 4.6), (12.5, 25, 6), "cab-bezel", faces=without(DIRS, "east", "west")),
            B("Screen", (3.5, 16.5, 5.6), (12.5, 24, 6), "mat-black", faces=("north",), north=("cab-screen-" + g, pic_uv(9, 7.5), 150)),
            B("Marquee", (2, 25, 4.6), (14, 30, 6), side, north=("cab-marquee-" + g, pic_uv(12, 5), 210)),
            B("Top", (2, 25, 6), (14, 30, 15), side),
            B("Shaft", (4.95, 15, 2.45), (5.65, 17.4, 3.15), "mat-chrome", faces=without(DIRS, "down", "up")),
            B("Ball", (4.4, 17.4, 1.9), (6.2, 19.2, 3.7), "cab-red"),
            B("BtnA", (8.8, 15, 2.2), (10.4, 15.8, 3.8), "cab-red", faces=without(DIRS, "down")),
            B("BtnB", (11.0, 15, 2.2), (12.6, 15.8, 3.8), "cab-yellow", faces=without(DIRS, "down")),
        ]
        refs[g] = shape("l31-retrocab-" + g, els)
    return refs


# ======================================================================== Skate shelf, cinema bench

def skateshelf():
    save(M.wood_planks(seed=3521, base=(204, 160, 100), planks=2, direction="h", grain=3, flecks=0.5), "shelf-wood")
    save(M.wood_planks(seed=3522, base=(150, 110, 70), planks=1, direction="v", grain=3, flecks=0.5), "shelf-back")
    for n, b in (("white", (238, 238, 242)), ("tan", (200, 160, 112))):
        img = M.noise_hv(b, 2, 3523 + len(n), S, 3, (8, 4))
        R(img, 0, 6, 31, 6, shade(b, 0.8))
        R(img, 0, 20, 31, 20, shade(b, 0.8))
        save(img, "skate-" + n)
    wheels = {"pink": (250, 100, 180), "cyan": (60, 220, 240), "yellow": (250, 220, 50), "orange": (250, 140, 40),
              "green": (90, 220, 90), "purple": (160, 90, 240)}
    for n, c in wheels.items():
        img = new(S, col=c)
        R(img, 0, 0, 31, 31, c)
        disc(img, 16, 16, 6, shade(c, 0.7))
        disc(img, 16, 16, 2, (230, 230, 236))
        save(img, "wheel-" + n)
    rng = random.Random(3524)
    els = [B("WallL", (0, 0, 0), (1, 16, 15), "shelf-wood", faces=without(DIRS, "south")),
           B("WallR", (15, 0, 0), (16, 16, 15), "shelf-wood", faces=without(DIRS, "south")),
           B("Back", (1, 0, 15), (15, 16, 16), "shelf-back")]
    ys = [(0, 1), (5, 6), (10, 11), (15, 16)]
    for i, (a, b) in enumerate(ys):
        els.append(B(f"Shelf{i}", (1, a, 0), (15, b, 15), "shelf-wood", faces=without(DIRS, "south", "east", "west") if i not in (0, 3) else without(DIRS, "south", "east", "west")))
    xs = [(1, 5), (6, 10), (11, 15)]
    cellys = [(1, 5), (6, 10), (11, 15)]
    for r, (ya, yb) in enumerate(cellys):
        for c in (0, 1):
            x = xs[c][1]
            els.append(B(f"Div{r}{c}", (x, ya, 0), (x + 1, yb, 15), "shelf-wood", faces=without(DIRS, "south", "up", "down")))
    wk = list(wheels)
    for r, (ya, yb) in enumerate(cellys):
        for c, (xa, xb) in enumerate(xs):
            boot = rng.choice(("white", "tan"))
            wc = "wheel-" + rng.choice(wk)
            for s in (0, 1):
                bx = xa + 0.35 + s * 1.95
                n_ = f"{r}{c}{s}"
                els.append(B("Frame" + n_, (bx + 0.4, ya + 0.8, 3.0), (bx + 1.0, ya + 1.2, 9.4), "mat-dark"))
                for k, wz in enumerate((3.2, 4.8, 6.6, 8.2)):
                    els.append(B(f"Wh{n_}{k}", (bx + 0.15, ya, wz), (bx + 1.25, ya + 0.9, wz + 0.9), wc, faces=without(DIRS, "up")))
                els.append(B("Boot" + n_, (bx, ya + 1.2, 2.4), (bx + 1.4, ya + 2.4, 9.4), "skate-" + boot))
                els.append(B("Cuff" + n_, (bx, ya + 2.4, 6.2), (bx + 1.4, ya + 3.8, 9.4), "skate-" + boot, faces=without(DIRS, "down")))
    return shape("l31-skateshelf", els)


def cinemabench():
    img = M.brushed_metal(seed=3531, base=(86, 92, 104), direction="h")
    for y in range(4, 32, 6):
        for x in range(3, 32, 6):
            R(img, x, y, x + 1, y, (24, 26, 32))
    save(img, "cinema-top")
    els = [B("Seat", (0, 6, 3), (16, 7, 11), mat(top="cinema-top", side="mat-gunmetal", bottom="mat-gunmetal")),
           B("Back", (0, 7, 11), (16, 11, 12), "mat-gunmetal", faces=without(DIRS, "up") if False else DIRS),
           B("Ped", (5, 0.6, 5), (11, 6, 10), "mat-gunmetal", faces=without(DIRS, "up")),
           B("PedFoot", (4, 0, 4), (12, 0.6, 11), "mat-dark")]
    return shape("l31-cinemabench", els)


# ======================================================================== TV, CCTV, security desk

def tv_scene(w=192, h=128):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    px = img.load()
    stops = [(0, (36, 18, 88)), (30, (140, 40, 120)), (58, (240, 96, 90)), (82, (255, 168, 70)), (104, (255, 226, 140)), (127, (255, 214, 130))]
    for y in range(h):
        for i in range(len(stops) - 1):
            if stops[i][0] <= y <= stops[i + 1][0]:
                t = (y - stops[i][0]) / (stops[i + 1][0] - stops[i][0])
                c = mixc(stops[i][1], stops[i + 1][1], t)
        for x in range(w):
            px[x, y] = c + (255,)
    rng = random.Random(3541)
    for _ in range(26):
        x, y = rng.randrange(w), rng.randrange(0, 30)
        img.putpixel((x, y), (230, 220, 250, 255))
    d = ImageDraw.Draw(img, "RGBA")
    for r, a in ((50, 40), (38, 60), (28, 90)):
        d.ellipse([120 - r, 88 - r, 120 + r, 88 + r], fill=(255, 220, 150, a))
    d.ellipse([98, 66, 142, 110], fill=(255, 246, 190, 255))
    for (x, y, ln, hh) in ((20, 34, 60, 5), (110, 24, 44, 4), (150, 48, 38, 4), (60, 54, 40, 3), (135, 70, 50, 3)):
        d.ellipse([x, y, x + ln, y + hh * 2], fill=(255, 150, 160, 150))
    def hills(base, amp, ph, col, f=1.0):
        pts = [(0, h)]
        for x in range(0, w + 4, 4):
            pts.append((x, base + amp * math.sin(x * 0.034 * f + ph) + amp * 0.4 * math.sin(x * 0.09 * f + ph * 2)))
        pts.append((w, h))
        d.polygon(pts, fill=col)
    hills(96, 9, 0.5, (150, 56, 110, 255))
    hills(104, 10, 2.1, (96, 36, 100, 255))
    hills(112, 8, 4.0, (50, 24, 76, 255), 0.8)
    # the two silhouettes: a tall one and a small one with a big head, hand in hand, on the front hill
    sil = (16, 8, 30, 255)
    gx = 52
    base = 112 + 8 * math.sin(gx * 0.034 * 0.8 + 4.0) + 3.2 * math.sin(gx * 0.09 * 0.8 + 8.0)
    by = int(base) + 2
    d.ellipse([gx - 5, by - 36, gx + 5, by - 26], fill=sil)
    d.polygon([(gx - 6, by - 25), (gx + 6, by - 25), (gx + 8, by - 8), (gx - 8, by - 8)], fill=sil)
    d.rectangle([gx - 6, by - 8, gx - 2, by], fill=sil)
    d.rectangle([gx + 2, by - 8, gx + 6, by], fill=sil)
    sx = gx + 18
    d.ellipse([sx - 5, by - 25, sx + 5, by - 15], fill=sil)
    d.polygon([(sx - 4, by - 14), (sx + 4, by - 14), (sx + 5, by - 5), (sx - 5, by - 5)], fill=sil)
    d.rectangle([sx - 4, by - 5, sx - 1, by], fill=sil)
    d.rectangle([sx + 1, by - 5, sx + 4, by], fill=sil)
    d.line([(gx + 7, by - 20), (sx - 4, by - 14)], fill=sil, width=2)
    d.polygon([(sx - 5, by - 25), (sx - 7, by - 29), (sx - 2, by - 26)], fill=sil)   # ears
    d.polygon([(sx + 5, by - 25), (sx + 7, by - 29), (sx + 2, by - 26)], fill=sil)
    for (x, y) in ((150, 30), (160, 26), (168, 34)):
        d.line([(x - 3, y - 1), (x, y + 1), (x + 3, y - 1)], fill=(30, 14, 40, 255))
    # the bezel: 4 px of black round the whole picture, with a faint edge light inside it
    d.rectangle([0, 0, w - 1, 3], fill=(8, 8, 10, 255))
    d.rectangle([0, h - 4, w - 1, h - 1], fill=(8, 8, 10, 255))
    d.rectangle([0, 0, 3, h - 1], fill=(8, 8, 10, 255))
    d.rectangle([w - 4, 0, w - 1, h - 1], fill=(8, 8, 10, 255))
    d.rectangle([4, 4, w - 5, h - 5], outline=(40, 40, 46, 255))
    return img


def tv():
    scene = tv_scene()
    refs = {}
    for row, rn in enumerate(("t", "b")):
        for col, cn in enumerate(("l", "m", "r")):
            part = rn + cn
            save(scene.crop((col * 64, row * 64, col * 64 + 64, row * 64 + 64)), "tv-" + part)
            # viewed from the north, the picture's left is +x (east): the left block's outer edge is its east face
            faces = ["north"] + (["up"] if rn == "t" else ["down"])
            if cn == "l":
                faces.append("east")
            if cn == "r":
                faces.append("west")
            els = [B("Panel", (0, 0, 14), (16, 16, 16), "mat-black", faces=tuple(faces),
                     north=("tv-" + part, [0, 0, 16, 16], 180))]
            refs[part] = shape("l31-tv-" + part, els)
    return refs


def cctv():
    save(M.painted_metal(seed=3551, base=(150, 152, 156), panel=False, chips=3), "cctv-body")
    lens = new(S, col=(12, 12, 16))
    disc(lens, 16, 16, 13, (60, 62, 70))
    disc(lens, 16, 16, 10, (10, 14, 26))
    disc(lens, 16, 16, 5, (30, 50, 110))
    disc(lens, 13, 13, 2, (170, 200, 255))
    save(lens, "cctv-lens")
    save(new(S, col=(255, 40, 30)), "cctv-led")
    rot = dict(rot=(-10, 0, 0), origin=(8, 13.2, 5.8))
    els = [B("Plate", (6, 15.4, 6.2), (10, 16, 10.2), "mat-dark", faces=without(DIRS, "up")),
           B("Stem", (7.6, 14.4, 7.6), (8.4, 15.4, 8.4), "mat-dark", faces=without(DIRS, "up", "down")),
           B("Arm", (7.6, 14.4, 3.2), (8.4, 15.0, 7.6), "mat-dark", faces=without(DIRS, "south")),
           B("Body", (6.4, 11.9, 2.6), (9.6, 14.4, 9.0), "cctv-body", **rot),
           B("Visor", (6.1, 14.4, 2.2), (9.9, 14.8, 7.2), "cctv-body", faces=without(DIRS, "down"), **rot),
           B("Lens", (6.9, 12.2, 1.8), (9.1, 14.0, 2.6), "mat-dark", north=("cctv-lens", [0, 0, 16, 16]), **rot),
           B("Led", (8.8, 14.0, 2.3), (9.4, 14.4, 2.7), "cctv-led", faces=("north", "east", "up"), glow=255, **rot)]
    return shape("l31-cctv", els)


def cam_views():
    big = new(PIC, col=(0, 0, 0))
    rng = random.Random(3561)
    W_, H_ = 22, 15
    tints = [(120, 140, 160), (110, 130, 150), (120, 128, 136), (90, 110, 130)]
    for k in range(4):
        v = new(W_, H_, (40, 54, 70))
        d = ImageDraw.Draw(v)
        t = tints[k]
        if k == 0:     # a hallway receding to a door
            d.rectangle([0, 0, W_, H_], fill=(34, 44, 58, 255))
            d.polygon([(0, 0), (7, 4), (7, 11), (0, H_)], fill=(52, 66, 84, 255))
            d.polygon([(W_, 0), (15, 4), (15, 11), (W_, H_)], fill=(46, 58, 74, 255))
            d.polygon([(0, H_), (7, 11), (15, 11), (W_, H_)], fill=(70, 80, 92, 255))
            d.rectangle([7, 4, 14, 10], fill=(20, 26, 34, 255))
            d.rectangle([9, 5, 12, 10], fill=(96, 110, 126, 255))
        elif k == 1:   # a room of cabinets in rows
            d.rectangle([0, 0, W_, H_], fill=(30, 40, 52, 255))
            for i in range(6):
                for j in range(2):
                    d.rectangle([1 + i * 3 + j, 3 + j * 5, 2 + i * 3 + j, 6 + j * 5], fill=(90, 110, 130, 255))
                    img_ = (240, 220, 120, 255) if (i + j) % 2 else (120, 220, 240, 255)
                    d.point((1 + i * 3 + j, 4 + j * 5), fill=img_)
        elif k == 2:   # nothing but snow
            for y in range(H_):
                for x in range(W_):
                    n = rng.randint(30, 150)
                    d.point((x, y), fill=(n, n + 6, n + 12, 255))
        else:          # a dim lot under one lamp
            d.rectangle([0, 0, W_, H_], fill=(20, 26, 34, 255))
            d.ellipse([3, 6, 19, 18], fill=(48, 58, 72, 255))
            d.rectangle([14, 2, 15, 6], fill=(140, 150, 160, 255))
            d.rectangle([2, 10, 6, 12], fill=(80, 70, 70, 255))
        for y in range(0, H_, 2):
            for x in range(W_):
                r, g, b, a = v.getpixel((x, y))
                v.putpixel((x, y), (int(r * 0.8), int(g * 0.8), int(b * 0.8), 255))
        text(v, 1, 1, "CAM" + str(k + 1), (200, 214, 228)) if k != 2 else None
        big.paste(v, ((k % 2) * 32, (k // 2) * 32))
    save(big, "cam-views")


def monitors():
    cam_views()
    save(M.noise_hv((176, 172, 160), 2, 3571, S, 3, (8, 4)), "crt-plastic")
    save(M.noise_hv((84, 86, 92), 2, 3572, S, 3, (8, 4)), "crt-back")
    save(M.noise_hv((146, 152, 160), 2, 3573, S, 3, (8, 4)), "desk-grey")
    save(M.noise_hv((64, 68, 76), 2, 3574, S, 3, (8, 4)), "desk-top")
    drw = M.noise_hv((146, 152, 160), 2, 3575, S, 3, (8, 4))
    for y0 in (0, 5):
        outline(drw, 0, y0, 7, y0 + 4, (100, 106, 114))
        R(drw, 3, y0 + 2, 4, y0 + 2, (210, 214, 220))
    save(drw, "desk-front")
    kb = new(PIC, col=(150, 150, 154))
    R(kb, 0, 0, 35, 7, (170, 170, 174))
    for r in range(3):
        for c in range(14):
            R(kb, 1 + c * 2 + (1 if r == 1 else 0), 1 + r * 2, 1 + c * 2 + (1 if r == 1 else 0), 1 + r * 2, (60, 62, 68))
    save(kb, "kbd-top")
    els = [B("PedL", (0, 0, 1), (4, 5, 13), mat(side="desk-grey"), north=("desk-front", pic_uv(4, 5))),
           B("PedR", (12, 0, 1), (16, 5, 13), mat(side="desk-grey"), north=("desk-front", pic_uv(4, 5))),
           B("Modesty", (4, 1, 11), (12, 5, 12.5), "desk-grey", faces=("north", "south")),
           B("Top", (0, 5, 0.5), (16, 6, 13.5), mat(top="desk-top", side="desk-grey", bottom="desk-grey")),
           B("Kbd", (3.5, 6, 0.9), (12.5, 6.7, 2.9), "mat-steel", up=("kbd-top", pic_uv(9, 2)))]
    k = 0
    for row, y in enumerate((6.0, 11.0)):
        for col, x0 in enumerate((1.0, 8.0)):
            u0, v0 = (k % 2) * 8, (k // 2) * 8
            els.append(B(f"Crt{k}", (x0, y, 3), (x0 + 7, y + 5, 5.5), "crt-plastic", faces=without(DIRS, "south")))
            els.append(B(f"Rear{k}", (x0 + 1, y + 0.6, 5.5), (x0 + 6, y + 4.4, 9), "crt-back", faces=without(DIRS, "north")))
            els.append(B(f"Scr{k}", (x0 + 0.75, y + 0.6, 2.8), (x0 + 6.25, y + 4.4, 3.0), "mat-black", faces=("north",),
                         north=("cam-views", [u0, v0, u0 + 5.5, v0 + 3.8], 70)))
            k += 1
    return shape("l31-monitors", els)


# ======================================================================== Block types and main

def blocks():
    ref = chair()
    prop_block("l31-chair", "Level 31: a moulded orange plastic food-court chair on chrome legs; the side is the way a sitter faces",
               lambda k: ref, (0.2, 0, 0.2, 0.8, 0.93, 0.82), (0.2, 0, 0.2, 0.8, 0.45, 0.82), resistance=2)
    ref = table()
    prop_block("l31-table", "Level 31: a square cafe table, white laminate on a chrome pedestal (not oriented)", lambda k: ref,
               (0.0625, 0, 0.0625, 0.9375, 0.75, 0.9375), (0.0625, 0, 0.0625, 0.9375, 0.75, 0.9375), kinds=["plain"], oriented=False, resistance=2)
    refs = bench()
    prop_block("l31-bench", "Level 31: a metal park-style bench with slatted seat and back, full block wide so a row joins; the sitter faces the side",
               lambda k: refs[k], (0, 0, 0.18, 1, 0.95, 0.85), (0, 0, 0.18, 1, 0.45, 0.85), kinds=["orange", "green"], kindgroup="colour")
    ref = condiments()
    prop_block("l31-condiments", "Level 31: a steel condiment stand (ketchup, mustard, relish pumps, napkins, straws); the pumps point to the side",
               lambda k: ref, (0.07, 0, 0.2, 0.93, 0.88, 0.8), (0.07, 0, 0.2, 0.93, 0.88, 0.8), resistance=2)
    ref = fountain()
    prop_block("l31-fountain", "Level 31: a countertop soda fountain on a counter base (a block tall); the taps face the side; dispenses Almond Water",
               lambda k: ref, (0, 0, 0.0625, 1, 1, 0.9375), (0, 0, 0.0625, 1, 1, 0.9375), resistance=4,
               extra={"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser",
                      "attributes": {"dispenses": ["backrooms:almondwater"], "restock": True, "liquidSource": True}})
    refs = djdesk()
    prop_block("l31-djdesk", "Level 31: a black DJ desk, one block, top at 14 units: deck (a turntable) or mixer; the crowd sees the side's front, the DJ stands behind",
               lambda k: refs[k], (0, 0, 0.09, 1, 0.875, 0.9375), (0, 0, 0.09, 1, 0.875, 0.9375), kinds=["deck", "mixer"], kindgroup="part")
    ref = speaker()
    prop_block("l31-speaker", "Level 31: a tall black PA speaker cabinet with two woofers and a horn on the side's face",
               lambda k: ref, (0.0625, 0, 0.0625, 0.9375, 1, 0.875), (0.0625, 0, 0.0625, 0.9375, 1, 0.875), resistance=4)
    refs = gate()
    prop_block("l31-gate", "Level 31: a short wooden gate for the gaps in the rink's barrier, along the axis (we or ns); walk-through",
               lambda k: refs[k], lambda k: (0, 0, 0.42, 1, 0.7, 0.58) if k == "we" else (0.42, 0, 0, 0.58, 0.7, 1), None,
               kinds=["we", "ns"], kindgroup="axis", oriented=False, material="Wood", sounds=WOOD, resistance=2)
    ref = star()
    prop_block("l31-star", "Level 31: the rink's star-shaped ceiling light, a five-pointed neon outline about 3 blocks across, hung under the ceiling (centre block)",
               lambda k: ref, (0.4, 0.85, 0.4, 0.6, 1, 0.6), None, kinds=["plain"], oriented=False, resistance=1,
               extra={"lightHsv": [8, 2, 18]})
    ref = dispenser()
    prop_block("l31-dispenser", "Level 31: the arcade's green-card dispenser: a purple metal box on a short post, a big blue button over a card catcher; faces the side",
               lambda k: ref, (0.125, 0, 0.3, 0.875, 1, 0.7), (0.125, 0, 0.3, 0.875, 1, 0.7))
    refs = retrocab()
    prop_block("l31-retrocab", "Level 31: a 1980s upright arcade cabinet, 30 units tall (it reaches into the block above), lit marquee and screen, by game and facing side",
               lambda k: refs[k], (0.125, 0, 0.09, 0.875, 1, 0.94), (0.125, 0, 0.09, 0.875, 1, 0.94),
               kinds=["shooter", "barrels", "pyramid"], kindgroup="game", resistance=4)
    ref = skateshelf()
    prop_block("l31-skateshelf", "Level 31: a wooden cubby shelf, 3x3 cubbies with a pair of roller skates in each, open on the side",
               lambda k: ref, (0, 0, 0, 1, 1, 1), (0, 0, 0, 1, 1, 1), material="Wood", sounds=WOOD, resistance=3)
    ref = cinemabench()
    prop_block("l31-cinemabench", "Level 31: one segment of a long continuous steel bench (low back on the side opposite the one named), full block wide",
               lambda k: ref, (0, 0, 0.19, 1, 0.69, 0.76), (0, 0, 0.19, 1, 0.44, 0.76))
    refs = tv()
    parts = ["tl", "tm", "tr", "bl", "bm", "br"]
    light = {f"l31-tv-{p}-{s}": [32, 2, 7] for p in ("tm", "bm") for s in SIDES}
    prop_block("l31-tv", "Level 31: a big flat TV, 3 blocks wide and 2 high on a wall (tl tm tr / bl bm br as seen by a viewer in front of it); screen toward the side, wall behind",
               lambda k: refs[k], (0, 0, 0.875, 1, 1, 1), (0, 0, 0.875, 1, 1, 1), kinds=parts, kindgroup="part", resistance=3,
               extra={"lightHsvByType": light})
    ref = cctv()
    prop_block("l31-cctv", "Level 31: a small grey CCTV camera on an L-bracket under the ceiling, lens toward the side and slightly down, with a red LED",
               lambda k: ref, (0.3, 0.55, 0.1, 0.7, 1, 0.6), None, resistance=2)
    ref = monitors()
    prop_block("l31-monitors", "Level 31: a security desk with a 2x2 bank of small CRT monitors showing camera views, screens toward the side, a keyboard in front",
               lambda k: ref, (0, 0, 0.03, 1, 1, 0.85), (0, 0, 0.03, 1, 1, 0.85))


def main():
    materials()
    cubes_floor()
    signs()
    blocks()
    print("Level 31 props: textures in", os.path.relpath(TEX), "; blocktypes in", os.path.relpath(BLOCKS))


if __name__ == "__main__":
    main()
